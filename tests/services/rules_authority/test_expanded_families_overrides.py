"""Expanded fact families flow through the override path — CRD Issue 5d.

Typed patches rebuild facts through the projection's own
:func:`fact_from_payload`, so a family added to the closed union is patchable the
moment it exists and there is no looser runtime door into the same union. That is
a claim about *this* code, though, not a law of nature — these tests hold it for
the families the production-authoring work added, and hold the door shut against
the payloads that would widen it.
"""

from __future__ import annotations

import pytest

from afterworlds.ingestion.mechanical.representation import (
    AbilityScore,
    ActionCost,
    ActionRestrictionFact,
    AdvantageFact,
    AdvantageState,
    AttackKind,
    AttackRollFact,
    AutomaticOutcome,
    AutomaticOutcomeFact,
    CreatureDefenseFact,
    CriticalHitChange,
    CriticalHitRuleFact,
    DamageFact,
    DamageResponseFact,
    DamageResponseKind,
    DamageScope,
    DamageType,
    DiceExpression,
    DieSize,
    RollActor,
    RollContext,
    RollSpec,
    SpeedChange,
    SpeedModificationFact,
    StateEffectFact,
    StateEffectKind,
    fact_key,
    fact_payload,
)
from afterworlds.models.enums import OverrideOperationEnum
from afterworlds.services.rules_authority.outcomes import AuthorityOutcome
from afterworlds.services.rules_authority.service import RulesAuthorityService
from tests.services.rules_authority.conftest import (
    CHECK_COMPONENT_TARGET,
    CHECK_FACT_KEY,
    CHECK_KEY,
    CREATURE_KEY,
    DESCRIPTOR_FACT_TARGET,
    DESCRIPTOR_KEY,
    NOW,
    SPELL_KEY,
    RuntimeFixture,
    append_fact_payload,
    author_override,
    replace_fact_payload,
)
from tests.services.rules_authority.test_typed_overrides import (
    component,
    effective,
    whole_package,
)


def typed_view(runtime: RuntimeFixture):  # type: ignore[no-untyped-def]
    """The raw service result, so a refusal is inspectable rather than asserted away."""
    return RulesAuthorityService(runtime.session, now=NOW).typed_view(
        whole_package(runtime)
    )


#: "Slam. Melee Attack Roll: +4, reach 5 ft." — a family that did not exist
#: when the override path was written.
SLAM = AttackRollFact(AttackKind.MELEE_WEAPON, to_hit_bonus=4, reach_feet=5)

#: "Hit: 10 (2d6 + 3) Bludgeoning damage." — a family carrying a nested value
#: object, which is the part a payload-shaped override could most easily mangle.
SLAM_DAMAGE = DamageFact(
    damage_type=DamageType.BLUDGEONING,
    dice=DiceExpression(2, DieSize.D6, 3),
    stated_average=10,
)

#: "AC 11" / "HP 58 (9d8 + 18)"
DEFENSE = CreatureDefenseFact(
    armor_class=11, hit_points=58, hit_point_dice=DiceExpression(9, DieSize.D8, 18)
)


def test_a_new_family_can_be_appended_by_an_override(runtime: RuntimeFixture) -> None:
    author_override(
        runtime.session,
        override_id="ov-append-attack",
        target=CHECK_COMPONENT_TARGET,
        operation=OverrideOperationEnum.APPEND,
        payload=append_fact_payload(SLAM),
    )
    view = effective(runtime)

    check = component(view, CREATURE_KEY, CHECK_KEY)
    assert check is not None
    added = [f for f in check.facts if f.fact_key == fact_key(SLAM)]
    assert [f.fact for f in added] == [SLAM]
    # Override-supplied authority names its override, never 5c spans.
    assert added[0].supplied_by_override_id == "ov-append-attack"
    assert added[0].span_ids == ()


def test_a_nested_value_object_survives_the_override_path(
    runtime: RuntimeFixture,
) -> None:
    """``2d6 + 3`` comes back as the same typed object, not a look-alike."""
    author_override(
        runtime.session,
        override_id="ov-append-damage",
        target=CHECK_COMPONENT_TARGET,
        operation=OverrideOperationEnum.APPEND,
        payload=append_fact_payload(SLAM_DAMAGE),
    )
    check = component(effective(runtime), CREATURE_KEY, CHECK_KEY)
    assert check is not None
    (added,) = [f for f in check.facts if f.fact_key == fact_key(SLAM_DAMAGE)]
    assert added.fact == SLAM_DAMAGE
    assert isinstance(added.fact.dice, DiceExpression)
    assert added.fact.dice.die is DieSize.D6


def test_a_new_family_can_replace_a_fact_of_another_family(
    runtime: RuntimeFixture,
) -> None:
    """``REPLACE`` supplies a complete replacement, not a merge of two shapes."""
    author_override(
        runtime.session,
        override_id="ov-replace-with-defense",
        target=DESCRIPTOR_FACT_TARGET,
        operation=OverrideOperationEnum.REPLACE,
        payload=replace_fact_payload(DEFENSE),
    )
    descriptor = component(effective(runtime), SPELL_KEY, DESCRIPTOR_KEY)
    assert descriptor is not None
    assert [f.fact for f in descriptor.facts] == [DEFENSE]


def test_the_typed_view_reports_the_new_family_to_deterministic_consumers(
    runtime: RuntimeFixture,
) -> None:
    author_override(
        runtime.session,
        override_id="ov-append-attack-view",
        target=CHECK_COMPONENT_TARGET,
        operation=OverrideOperationEnum.APPEND,
        payload=append_fact_payload(SLAM),
    )
    result = typed_view(runtime)
    assert result.outcome is AuthorityOutcome.RESOLVED
    assert result.typed_view is not None
    facts = [
        f.fact
        for record in result.typed_view.records
        for comp in record.components
        for f in comp.facts
    ]
    assert SLAM in facts


# -- and the door stays shut --------------------------------------------------


@pytest.mark.parametrize(
    ("payload", "why"),
    [
        (
            {"patch": "append_fact", "fact": {"family": "vibes", "amount": 3}},
            "a family outside the closed union",
        ),
        (
            {
                "patch": "append_fact",
                "fact": {**fact_payload(SLAM), "smuggled": {"dc": 15}},
            },
            "an extra field the union does not declare",
        ),
        (
            {
                "patch": "append_fact",
                "fact": {
                    k: v for k, v in fact_payload(SLAM).items() if k != "to_hit_bonus"
                },
            },
            "a missing field that would otherwise default",
        ),
        (
            {
                "patch": "append_fact",
                "fact": {**fact_payload(SLAM_DAMAGE), "dice": "2d6+3"},
            },
            "a nested value object flattened into a string",
        ),
    ],
    ids=["unknown-family", "extra-field", "missing-field", "stringly-dice"],
)
def test_an_override_cannot_widen_the_closed_union(
    runtime: RuntimeFixture, payload: dict[str, object], why: str
) -> None:
    """Every one of these is ``INVALID_OVERRIDE`` — never a skipped override.

    A runtime path that accepted what persistence rejects would be a second,
    looser definition of the union, and the looser one would win.
    """
    author_override(
        runtime.session,
        override_id=f"ov-bad-{abs(hash(why))}",
        target=CHECK_COMPONENT_TARGET,
        operation=OverrideOperationEnum.APPEND,
        payload=payload,
    )
    result = typed_view(runtime)
    assert result.outcome is AuthorityOutcome.INVALID_OVERRIDE, why


def test_base_authority_is_unchanged_by_any_of_this(runtime: RuntimeFixture) -> None:
    """Overrides never mutate the immutable base projection."""
    author_override(
        runtime.session,
        override_id="ov-append-attack-base",
        target=CHECK_COMPONENT_TARGET,
        operation=OverrideOperationEnum.APPEND,
        payload=append_fact_payload(SLAM),
    )
    effective(runtime)

    from afterworlds.ingestion.mechanical.persistence import reconstruct_candidate

    rebuilt = reconstruct_candidate(runtime.session, str(runtime.projection_uuid))
    keys = {fact_key(f) for c in rebuilt.representation.components for f in c.facts}
    assert fact_key(SLAM) not in keys
    assert CHECK_FACT_KEY in keys


# -- the conditions-batch families, through the same path ---------------------
#
# The schema-closure work added five families and reshaped three. The override
# layer rebuilds facts through the projection's own ``fact_from_payload``, so it
# should carry them with no change here — but "should" is what a regression is
# for, and the reshaped families are the ones a stale payload could quietly
# survive in.

#: Blinded, p177: "your attack rolls have Disadvantage."
BLINDED_SELF = AdvantageFact(
    AdvantageState.DISADVANTAGE,
    RollSpec(RollActor.SUBJECT, RollContext.ATTACK_ROLL),
)

#: Blinded's other half, and Invisible's inverse: "Attack rolls against you
#: have Advantage." Identical to ``BLINDED_SELF`` before ``RollSpec`` existed.
BLINDED_AGAINST = AdvantageFact(
    AdvantageState.ADVANTAGE,
    RollSpec(RollActor.AGAINST_SUBJECT, RollContext.ATTACK_ROLL),
)

#: Petrified, p186: "You have Resistance to all damage."
ALL_DAMAGE = DamageResponseFact(DamageResponseKind.RESISTANCE, DamageScope.ALL)

#: Paralyzed, p186: "You automatically fail … Dexterity saving throws."
AUTO_FAIL = AutomaticOutcomeFact(
    RollSpec(RollActor.SUBJECT, RollContext.SAVING_THROW, AbilityScore.DEXTERITY),
    AutomaticOutcome.FAILURE,
)

#: Grappled, p182: "Your Speed is 0 and can't increase."
SPEED_ZERO = SpeedModificationFact(
    change=SpeedChange.SET_TO, feet=0, can_increase=False
)

#: Incapacitated, p184: "You can't take any … Reaction."
NO_REACTION = ActionRestrictionFact(ActionCost.REACTION)

#: Unconscious, p191: "Any attack roll that hits you is a Critical Hit …"
AUTO_CRIT = CriticalHitRuleFact(CriticalHitChange.AUTOMATIC_ON_HIT)

#: Incapacitated, p184: "Your Concentration is broken."
CONCENTRATION = StateEffectFact(StateEffectKind.CONCENTRATION_BROKEN)


@pytest.mark.parametrize(
    "fact",
    [
        BLINDED_AGAINST,
        ALL_DAMAGE,
        AUTO_FAIL,
        SPEED_ZERO,
        NO_REACTION,
        AUTO_CRIT,
        CONCENTRATION,
    ],
    ids=[
        "advantage-polarity",
        "all-damage",
        "automatic-outcome",
        "speed-modification",
        "action-restriction",
        "critical-hit",
        "state-effect",
    ],
)
def test_a_conditions_family_appends_and_reaches_the_typed_view(
    runtime: RuntimeFixture, fact: object
) -> None:
    """Each new or reshaped family survives the override path intact."""
    author_override(
        runtime.session,
        override_id=f"ov-cond-{fact_key(fact)}",
        target=CHECK_COMPONENT_TARGET,
        operation=OverrideOperationEnum.APPEND,
        payload=append_fact_payload(fact),
    )
    check = component(effective(runtime), CREATURE_KEY, CHECK_KEY)
    assert check is not None
    (added,) = [f for f in check.facts if f.fact_key == fact_key(fact)]
    assert added.fact == fact
    assert added.span_ids == ()

    result = typed_view(runtime)
    assert result.outcome is AuthorityOutcome.RESOLVED
    assert result.typed_view is not None
    assert fact in [
        f.fact
        for record in result.typed_view.records
        for comp in record.components
        for f in comp.facts
    ]


def test_roll_polarity_survives_the_override_path(runtime: RuntimeFixture) -> None:
    """Two opposite claims stay two facts after a runtime round trip.

    This is the Blinded/Invisible defect at the override seam: if the runtime
    rebuild dropped ``actor``, the two would collapse back into one key and one
    of them would silently disappear from the effective view.
    """
    for i, fact in enumerate((BLINDED_SELF, BLINDED_AGAINST)):
        author_override(
            runtime.session,
            override_id=f"ov-polarity-{i}",
            target=CHECK_COMPONENT_TARGET,
            operation=OverrideOperationEnum.APPEND,
            payload=append_fact_payload(fact),
        )
    check = component(effective(runtime), CREATURE_KEY, CHECK_KEY)
    assert check is not None
    rebuilt = [f.fact for f in check.facts if f.fact in (BLINDED_SELF, BLINDED_AGAINST)]
    assert len(rebuilt) == 2
    assert {f.roll.actor for f in rebuilt} == {  # type: ignore[union-attr]
        RollActor.SUBJECT,
        RollActor.AGAINST_SUBJECT,
    }


@pytest.mark.parametrize(
    ("payload", "why"),
    [
        (
            {
                "patch": "append_fact",
                "fact": {
                    **fact_payload(BLINDED_SELF),
                    "roll": {
                        "actor": "bystander",
                        "context": "attack_roll",
                        "ability": None,
                    },
                },
            },
            "an actor outside the closed vocabulary",
        ),
        (
            {
                "patch": "append_fact",
                "fact": {
                    **fact_payload(BLINDED_SELF),
                    "roll": {"actor": "subject", "context": "attack_roll"},
                },
            },
            "a roll specification missing its ability key",
        ),
        (
            {
                "patch": "append_fact",
                "fact": {**fact_payload(BLINDED_SELF), "roll": "subject attack roll"},
            },
            "a value object flattened into a string",
        ),
        (
            {
                "patch": "append_fact",
                "fact": {
                    **fact_payload(ALL_DAMAGE),
                    "damage_type": "fire",
                },
            },
            "an all-damage response that also names a type",
        ),
        (
            {
                "patch": "append_fact",
                "fact": {
                    **fact_payload(CONCENTRATION),
                    "effect": "cannot_smell",
                },
            },
            "a state effect outside the closed vocabulary",
        ),
    ],
    ids=[
        "unknown-actor",
        "missing-ability",
        "stringly-rollspec",
        "contradictory-scope",
        "unknown-state-effect",
    ],
)
def test_a_conditions_family_override_cannot_widen_the_union(
    runtime: RuntimeFixture, payload: dict[str, object], why: str
) -> None:
    """The same door, held shut against the new vocabularies."""
    author_override(
        runtime.session,
        override_id=f"ov-cond-bad-{abs(hash(why))}",
        target=CHECK_COMPONENT_TARGET,
        operation=OverrideOperationEnum.APPEND,
        payload=payload,
    )
    assert typed_view(runtime).outcome is AuthorityOutcome.INVALID_OVERRIDE, why
