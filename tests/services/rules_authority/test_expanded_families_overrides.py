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
    AreaDimension,
    AreaDimensionRequirementFact,
    AreaOriginInclusion,
    AreaOriginInclusionFact,
    AttackKind,
    AttackRollFact,
    AutomaticOutcome,
    AutomaticOutcomeFact,
    BenefitOriginSide,
    BlockedLineExclusionFact,
    BlockedLineQuantifier,
    CoverageThreshold,
    CoverBenefitOriginFact,
    CoverDefense,
    CoverDefensiveBonusFact,
    CoverDegree,
    CoverDegreeCombination,
    CoverDegreeSelection,
    CoverDegreeSelectionFact,
    CoveredInteraction,
    CoverOfferor,
    CoverProvisionFact,
    CoverTargetingProhibitionFact,
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
    DistanceUnit,
    MechanicalFact,
    MovementAllowanceBasis,
    MovementAllowanceFact,
    MovementComposition,
    MovementCompositionFact,
    MovementDepletionFact,
    MovementDepletionResolution,
    MovementDepletionTerminator,
    MovementMode,
    MovementPermissionFact,
    MovementWindow,
    RollActor,
    RollContext,
    RollSpec,
    SpecialSpeedFact,
    SpecialSpeedListing,
    SpeedChange,
    SpeedChangePropagationFact,
    SpeedDefinitionFact,
    SpeedModificationFact,
    SpeedPropagationDuration,
    SpeedPropagationMagnitude,
    SpeedPropagationScope,
    SpeedSelection,
    SpeedSelectionFact,
    SpeedSwitchAccounting,
    SpeedSwitchLimitFact,
    SpeedSwitchOutcome,
    StateEffectFact,
    StateEffectKind,
    TargetingProhibition,
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


# -- the areas-of-effect families, through the same path -----------------------
#
# Schema 9 added seven more families for the Area of Effect class. Nothing in
# the override layer was changed for them, which is exactly the claim worth a
# regression: the families reach the seam through the projection's own
# ``fact_from_payload``, and the vocabularies they close stay closed there.

#: Cone, p178: "A Cone's point of origin isn't included in the Cone's area of
#: effect, unless its creator decides otherwise." The creator-controlled
#: exception is inside the member, so an override that dropped it would be
#: stating a different rule rather than reformatting this one.
CONE_INCLUSION = AreaOriginInclusionFact(
    inclusion=AreaOriginInclusion.EXCLUDED_UNLESS_ITS_CREATOR_DECIDES_OTHERWISE
)

#: Area of Effect, p176: all straight lines blocked, Total Cover the threshold.
BLOCKED_LINES = BlockedLineExclusionFact(
    blocked=BlockedLineQuantifier.ALL_STRAIGHT_LINES_FROM_THE_POINT_OF_ORIGIN,
    blocking_cover=CoverDegree.TOTAL,
)

#: Cylinder, p179: two parameters, in the order the sentence prints them.
CYLINDER_DIMENSIONS = AreaDimensionRequirementFact(
    dimensions=(AreaDimension.RADIUS_OF_THE_BASE, AreaDimension.HEIGHT)
)


def test_an_area_of_effect_family_appends_and_reaches_the_typed_view(
    runtime: RuntimeFixture,
) -> None:
    """A schema-9 family through the existing seam, under existing precedence."""
    author_override(
        runtime.session,
        override_id="ov-area-inclusion",
        target=CHECK_COMPONENT_TARGET,
        operation=OverrideOperationEnum.APPEND,
        payload=append_fact_payload(CONE_INCLUSION),
    )
    check = component(effective(runtime), CREATURE_KEY, CHECK_KEY)
    assert check is not None
    (added,) = [f for f in check.facts if f.fact_key == fact_key(CONE_INCLUSION)]
    assert added.fact == CONE_INCLUSION
    assert added.supplied_by_override_id == "ov-area-inclusion"
    assert added.span_ids == ()

    result = typed_view(runtime)
    assert result.outcome is AuthorityOutcome.RESOLVED
    assert result.typed_view is not None
    assert CONE_INCLUSION in [
        f.fact
        for record in result.typed_view.records
        for comp in record.components
        for f in comp.facts
    ]


@pytest.mark.parametrize(
    ("payload", "why"),
    [
        (
            {
                "patch": "append_fact",
                "fact": {**fact_payload(CONE_INCLUSION), "inclusion": "excluded"},
            },
            "an inclusion member that drops the creator-controlled exception",
        ),
        (
            {
                "patch": "append_fact",
                "fact": {
                    **fact_payload(BLOCKED_LINES),
                    "blocked": "a_straight_line_from_the_point_of_origin",
                },
            },
            "a quantifier that would invert the blocked-line rule",
        ),
        (
            {
                "patch": "append_fact",
                "fact": {**fact_payload(CYLINDER_DIMENSIONS), "dimensions": "radius"},
            },
            "an ordered parameter list flattened into a string",
        ),
    ],
    ids=["weakened-inclusion", "weakened-quantifier", "stringly-dimensions"],
)
def test_an_area_of_effect_override_cannot_widen_the_union(
    runtime: RuntimeFixture, payload: dict[str, object], why: str
) -> None:
    """The same door, held shut against the schema-9 vocabularies.

    The first two state a *different rule* from the one the source prints; the
    third is a malformed encoding of the right one. Admitting either kind at
    the runtime seam would put a second definition of the class in front of a
    consumer, so the seam refuses both without having to tell them apart.
    """
    author_override(
        runtime.session,
        override_id=f"ov-area-bad-{abs(hash(why))}",
        target=CHECK_COMPONENT_TARGET,
        operation=OverrideOperationEnum.APPEND,
        payload=payload,
    )
    assert typed_view(runtime).outcome is AuthorityOutcome.INVALID_OVERRIDE, why


# -- the cover families, through the same path --------------------------------
#
# Schema 10 added five more families for the Cover entry, and one member --
# ``CoverDegree.HALF`` -- to a vocabulary the override layer could already
# carry. That widening is why this block is written out rather than assumed
# from the two above: the seam has been able to accept a degree of cover since
# schema 6, so the question is whether it now accepts the third member and the
# rules that say what a degree *is*, without the door opening any wider.

#: Cover table, p15: "Half" / "+2 bonus to AC and Dexterity saving throws". One
#: printed benefit that is two modifications at once, both keyed to one degree
#: -- and the specimen that carries the member schema 10 added.
HALF_BENEFIT = CoverDefensiveBonusFact(
    degree=CoverDegree.HALF,
    bonus=2,
    to_defense=CoverDefense.ARMOR_CLASS,
    to_saving_throw=AbilityScore.DEXTERITY,
)

#: Cover table, p15: "Total" / "Can't be targeted directly". Not a bonus, and
#: not a prohibition on everything: "directly" is printed.
TOTAL_PROHIBITION = CoverTargetingProhibitionFact(
    degree=CoverDegree.TOTAL,
    prohibits=TargetingProhibition.DIRECT_TARGETING,
)

#: Cover table, p15: "Another creature or an object that covers at least half of
#: the target". Half is the only degree a creature can offer.
HALF_PROVISION = CoverProvisionFact(
    degree=CoverDegree.HALF,
    offered_by=CoverOfferor.ANOTHER_CREATURE_OR_AN_OBJECT,
    coverage=CoverageThreshold.AT_LEAST_HALF,
)

#: Cover, p15: the benefit applies only against something originating on the far
#: side. Printed at one site only, and it qualifies every degree.
BENEFIT_ORIGIN = CoverBenefitOriginFact(
    interaction=CoveredInteraction.AN_ATTACK_OR_OTHER_EFFECT,
    requires_origin=BenefitOriginSide.OPPOSITE_SIDE_OF_THE_COVER,
)

#: Cover, p15 and p179: the most protective degree applies, and the degrees are
#: not added together. One rule with two printed halves.
DEGREE_SELECTION = CoverDegreeSelectionFact(
    selects=CoverDegreeSelection.MOST_PROTECTIVE,
    combination=CoverDegreeCombination.NOT_ADDED_TOGETHER,
)

COVER_FACTS = (
    HALF_BENEFIT,
    TOTAL_PROHIBITION,
    HALF_PROVISION,
    BENEFIT_ORIGIN,
    DEGREE_SELECTION,
)


@pytest.mark.parametrize(
    "fact", COVER_FACTS, ids=[fact.FAMILY.value for fact in COVER_FACTS]
)
def test_a_cover_family_appends_and_reaches_the_typed_view(
    runtime: RuntimeFixture, fact: MechanicalFact
) -> None:
    """Each schema-10 family through the existing seam, under existing precedence.

    All five rather than one representative, because they are not variations on
    a single shape: a numeric bonus, a prohibition, a provision keyed to the new
    member, a precondition on the benefit and a selection rule are five
    different payloads arriving at the same door.
    """
    override_id = f"ov-cover-{fact.FAMILY.value}"
    author_override(
        runtime.session,
        override_id=override_id,
        target=CHECK_COMPONENT_TARGET,
        operation=OverrideOperationEnum.APPEND,
        payload=append_fact_payload(fact),
    )
    check = component(effective(runtime), CREATURE_KEY, CHECK_KEY)
    assert check is not None
    (added,) = [f for f in check.facts if f.fact_key == fact_key(fact)]
    assert added.fact == fact
    assert added.supplied_by_override_id == override_id
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


@pytest.mark.parametrize(
    ("payload", "why"),
    [
        (
            {
                "patch": "append_fact",
                "fact": {**fact_payload(HALF_PROVISION), "degree": "quarter"},
            },
            "a fourth degree of cover",
        ),
        (
            {
                "patch": "append_fact",
                "fact": {**fact_payload(HALF_BENEFIT), "to_defense": "armour_class"},
            },
            "a defense the entry never names",
        ),
        (
            {
                "patch": "append_fact",
                "fact": {**fact_payload(HALF_BENEFIT), "bonus": "+2"},
            },
            "a bonus encoded as the string the page prints",
        ),
        (
            {
                "patch": "append_fact",
                "fact": {**fact_payload(TOTAL_PROHIBITION), "prohibits": "targeting"},
            },
            "a prohibition broadened past direct targeting",
        ),
        (
            {
                "patch": "append_fact",
                "fact": {
                    **fact_payload(HALF_PROVISION),
                    "coverage": "at_least_some_of_the_target",
                },
            },
            "a coverage threshold the table does not print",
        ),
        (
            {
                "patch": "append_fact",
                "fact": {**fact_payload(BENEFIT_ORIGIN), "interaction": "an_attack"},
            },
            "an interaction that drops the other effects",
        ),
        (
            {
                "patch": "append_fact",
                "fact": {
                    **fact_payload(DEGREE_SELECTION),
                    "combination": "added_together",
                },
            },
            "a combination rule that inverts the printed one",
        ),
    ],
    ids=[
        "fourth-degree",
        "unknown-defense",
        "stringly-bonus",
        "broadened-prohibition",
        "unprinted-threshold",
        "narrowed-interaction",
        "inverted-combination",
    ],
)
def test_a_cover_override_cannot_widen_the_union(
    runtime: RuntimeFixture, payload: dict[str, object], why: str
) -> None:
    """The same door, held shut against the schema-10 vocabularies.

    Five of these state a *different rule* from the one the source prints and
    two are malformed encodings of the right one, and the seam refuses both
    kinds without having to tell them apart. ``fourth-degree`` is the one worth
    naming separately: ``CoverDegree`` is the vocabulary this schema widened,
    and widening it once is not the same as leaving it open.
    """
    author_override(
        runtime.session,
        override_id=f"ov-cover-bad-{abs(hash(why))}",
        target=CHECK_COMPONENT_TARGET,
        operation=OverrideOperationEnum.APPEND,
        payload=payload,
    )
    assert typed_view(runtime).outcome is AuthorityOutcome.INVALID_OVERRIDE, why


# -- the speed families, through the same path --------------------------------
#
# Schema 11 mints seven families and widens ``MovementMode`` by one member, but
# it also does something the three blocks above never did: it adds an optional
# field to a family the override layer has carried since schema 6. So this
# block asks two questions rather than one. Do the seven new payloads reach a
# deterministic consumer intact -- and does ``MovementAllowanceFact``, whose
# wire shape changed under an override author who may still be writing the old
# one, still arrive as the fact it now is?

#: Speed, p14: "A creature's Speed is the distance in feet the creature can
#: cover when it moves on its turn." The unit and the window, and no number:
#: the entry defines the quantity without printing one.
SPEED_DEFINITION = SpeedDefinitionFact(
    unit=DistanceUnit.FOOT,
    window=MovementWindow.OWN_TURN,
)

#: Movement and Position, p14: "you can move a distance up to your Speed" on
#: your turn. The family is schema 6's; ``window`` is the field schema 11 added
#: to it, and this specimen is the reason the optional field is exercised here.
OWN_SPEED_ALLOWANCE = MovementAllowanceFact(
    basis=MovementAllowanceBasis.OWN_SPEED,
    window=MovementWindow.OWN_TURN,
)

#: Movement and Position, p14: "until it is used up or until you are done
#: moving, whichever comes first". Both terminators in one fact, because the
#: resolution is a statement about the pair.
DEPLETION = MovementDepletionFact(
    depletes=MovementAllowanceBasis.OWN_SPEED,
    until=(
        MovementDepletionTerminator.ALLOWANCE_USED_UP,
        MovementDepletionTerminator.DONE_MOVING,
    ),
    resolution=MovementDepletionResolution.WHICHEVER_COMES_FIRST,
)

#: Speed, p14: a creature with more than one speed chooses which to use before
#: moving.
SELECTION = SpeedSelectionFact(permits=SpeedSelection.CHOOSE_BEFORE_MOVING)

#: Speed, p14: switching costs the distance already moved, and a nonpositive
#: remainder forbids the new speed. The prohibition, not an arithmetic rule.
SWITCH_LIMIT = SpeedSwitchLimitFact(
    accounting=SpeedSwitchAccounting.SUBTRACT_DISTANCE_ALREADY_MOVED,
    when_nonpositive=SpeedSwitchOutcome.FORBIDS_USING_THE_NEW_SPEED,
)

#: Speed, p14: a change to Speed changes every special speed by the same amount
#: for the same duration. The worked examples are evidence, not a calculator.
PROPAGATION = SpeedChangePropagationFact(
    to=SpeedPropagationScope.EVERY_SPECIAL_SPEED,
    magnitude=SpeedPropagationMagnitude.EQUAL_AMOUNT,
    duration=SpeedPropagationDuration.SAME_DURATION,
)

#: Speed, p14: "such as a Burrow Speed, Climb Speed, Fly Speed, or Swim Speed".
#: The listing member is what keeps "such as" open at the consumer.
SPECIAL_FLY = SpecialSpeedFact(
    mode=MovementMode.FLY,
    listing=SpecialSpeedListing.NAMED_IN_A_NON_EXHAUSTIVE_LIST,
)

#: Movement and Position, p14: you can jump as part of your move. ``jump`` is
#: the member schema 11 adds to a vocabulary this seam already accepted, so
#: this specimen is the widening arriving through the override door.
JUMP_PERMISSION = MovementPermissionFact(mode=MovementMode.JUMP)

#: Movement and Position, p14: such movement is part of the entire move.
COMPOSITION = MovementCompositionFact(composes=MovementComposition.ENTIRE_MOVE)

SPEED_FACTS = (
    SPEED_DEFINITION,
    OWN_SPEED_ALLOWANCE,
    DEPLETION,
    SELECTION,
    SWITCH_LIMIT,
    PROPAGATION,
    SPECIAL_FLY,
    JUMP_PERMISSION,
    COMPOSITION,
)


@pytest.mark.parametrize(
    "fact", SPEED_FACTS, ids=[fact.FAMILY.value for fact in SPEED_FACTS]
)
def test_a_speed_family_appends_and_reaches_the_typed_view(
    runtime: RuntimeFixture, fact: MechanicalFact
) -> None:
    """Nine specimens for seven new families, and the two extra are the point.

    ``movement_allowance`` and ``movement_permission`` are not new, so a block
    that covered only the mint would skip exactly the two payloads whose shape
    changed under an unchanged family name.
    """
    override_id = f"ov-speed-{fact.FAMILY.value}"
    author_override(
        runtime.session,
        override_id=override_id,
        target=CHECK_COMPONENT_TARGET,
        operation=OverrideOperationEnum.APPEND,
        payload=append_fact_payload(fact),
    )
    check = component(effective(runtime), CREATURE_KEY, CHECK_KEY)
    assert check is not None
    (added,) = [f for f in check.facts if f.fact_key == fact_key(fact)]
    assert added.fact == fact
    assert added.supplied_by_override_id == override_id
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


def test_the_depletion_terminators_survive_the_override_path_in_order(
    runtime: RuntimeFixture,
) -> None:
    """The one new field that is a sequence, checked as a sequence.

    ``until`` is the only schema-11 field whose payload is a list. A path that
    round-tripped it as a set, or kept only its last member, would still produce
    a ``MovementDepletionFact`` and still resolve -- so the arrival is checked
    against the printed order rather than against membership.
    """
    author_override(
        runtime.session,
        override_id="ov-speed-until-order",
        target=CHECK_COMPONENT_TARGET,
        operation=OverrideOperationEnum.APPEND,
        payload=append_fact_payload(DEPLETION),
    )
    check = component(effective(runtime), CREATURE_KEY, CHECK_KEY)
    assert check is not None
    (added,) = [f for f in check.facts if f.fact_key == fact_key(DEPLETION)]
    arrived = added.fact
    assert isinstance(arrived, MovementDepletionFact)
    assert arrived.until == (
        MovementDepletionTerminator.ALLOWANCE_USED_UP,
        MovementDepletionTerminator.DONE_MOVING,
    )


@pytest.mark.parametrize(
    ("payload", "why"),
    [
        (
            {
                "patch": "append_fact",
                "fact": {**fact_payload(DEPLETION), "until": "allowance_used_up"},
            },
            "one terminator where the sentence prints a list of them",
        ),
        (
            {
                "patch": "append_fact",
                "fact": {**fact_payload(DEPLETION), "until": ["out_of_movement"]},
            },
            "a terminator the sentence never names",
        ),
        (
            {
                "patch": "append_fact",
                "fact": {**fact_payload(OWN_SPEED_ALLOWANCE), "window": "next_turn"},
            },
            "a window on the field schema 11 added to an older family",
        ),
        (
            {
                "patch": "append_fact",
                "fact": {**fact_payload(JUMP_PERMISSION), "mode": "teleport"},
            },
            "a mode outside the closure jump was added to",
        ),
        (
            {
                "patch": "append_fact",
                "fact": {**fact_payload(SPEED_DEFINITION), "unit": "feet"},
            },
            "the unit spelled the way the page prints it in a sentence",
        ),
        (
            {
                "patch": "append_fact",
                "fact": {
                    **fact_payload(SWITCH_LIMIT),
                    "when_nonpositive": "allows_using_the_new_speed",
                },
            },
            "the nonpositive prohibition inverted into a permission",
        ),
        (
            {
                "patch": "append_fact",
                "fact": {**fact_payload(PROPAGATION), "to": "every_speed"},
            },
            "propagation broadened past the special speeds",
        ),
        (
            {
                "patch": "append_fact",
                "fact": {**fact_payload(SPECIAL_FLY), "listing": "exhaustive_list"},
            },
            "a listing that closes what the entry prints as open",
        ),
        (
            {
                "patch": "append_fact",
                "fact": {**fact_payload(COMPOSITION), "composes": "partial_move"},
            },
            "a composition the entry does not state",
        ),
    ],
    ids=[
        "scalar-until",
        "unnamed-terminator",
        "unknown-window",
        "mode-past-the-closure",
        "stringly-unit",
        "inverted-prohibition",
        "broadened-propagation",
        "closed-listing",
        "unprinted-composition",
    ],
)
def test_a_speed_override_cannot_widen_the_union(
    runtime: RuntimeFixture, payload: dict[str, object], why: str
) -> None:
    """The same door, held shut against the schema-11 vocabularies.

    ``scalar-until`` and ``mode-past-the-closure`` are the two worth naming.
    The first is the only shape check in this schema that is about a field
    being a list at all; the second asks whether widening ``MovementMode`` once
    left it open, and the answer is that it did not.
    """
    author_override(
        runtime.session,
        override_id=f"ov-speed-bad-{abs(hash(why))}",
        target=CHECK_COMPONENT_TARGET,
        operation=OverrideOperationEnum.APPEND,
        payload=payload,
    )
    assert typed_view(runtime).outcome is AuthorityOutcome.INVALID_OVERRIDE, why
