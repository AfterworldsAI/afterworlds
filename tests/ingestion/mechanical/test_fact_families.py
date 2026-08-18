"""The expanded closed typed-fact union — CRD Issue 5d, Decision 4.

The union grew because full-corpus accounting found substantive authority the
first four families could not carry. Growth is only safe while two properties
hold, so every family is held to both here:

* **closed** — every family round-trips through its canonical payload without
  loss, and an unknown family, a missing field, an extra field, or a mistyped
  value is rejected rather than defaulted; and
* **not an escape hatch** — a second index gets a second typed field, never a
  string with a number in it.

One exemplar per family, each taken from real production-corpus text, so a
family cannot be added here without someone stating what in the SRD justifies it.
"""

from __future__ import annotations

from dataclasses import fields, replace
from enum import StrEnum
from typing import Any

import pytest
from sqlalchemy.orm import Session

from afterworlds.ingestion.mechanical.models import ComponentHandling
from afterworlds.ingestion.mechanical.persistence import (
    persist_draft,
    reconstruct_candidate,
)
from afterworlds.ingestion.mechanical.projection import (
    identify_projection,
)
from afterworlds.ingestion.mechanical.representation import (
    AbilityCheckFact,
    AbilityScore,
    ActionCost,
    ActionEconomyFact,
    ActionRestrictionFact,
    AdvantageFact,
    AdvantageState,
    AttackKind,
    AttackRollFact,
    AutomaticOutcome,
    AutomaticOutcomeFact,
    ComponentDraft,
    ConditionEffectFact,
    ConditionEffectKind,
    ConditionKind,
    CreatureAbilityScoreFact,
    CreatureChallengeFact,
    CreatureDefenseFact,
    CreatureSpeedFact,
    CriticalHitChange,
    CriticalHitRuleFact,
    Currency,
    DamageFact,
    DamageResponseFact,
    DamageResponseKind,
    DamageScope,
    DamageType,
    DcKind,
    DiceExpression,
    DieSize,
    DurationKind,
    EquipmentDescriptorFact,
    FactFamily,
    HealingFact,
    MalformedFactPayloadError,
    Money,
    MovementMode,
    ProgressionEntryFact,
    RangeKind,
    Rational,
    RecordDraft,
    RecordKind,
    RecoveryTrigger,
    RelationshipDraft,
    RelationshipKind,
    RepresentationDraft,
    ResourceRecoveryFact,
    RollActor,
    RollContext,
    RollSpec,
    ScalingBasis,
    ScalingEffect,
    ScalingFact,
    SpeedChange,
    SpeedModificationFact,
    SpellCastingTime,
    SpellComponents,
    SpellDescriptorFact,
    SpellDuration,
    SpellListQualifierFact,
    SpellRange,
    SpellSchool,
    SpellSlotProgressionFact,
    StateEffectFact,
    StateEffectKind,
    TimeUnit,
    UnknownFactFamilyError,
    WeaponProperty,
    WeaponPropertyFact,
    fact_from_payload,
    fact_invariant_violations,
    fact_key,
    fact_payload,
)
from afterworlds.ingestion.mechanical.validation import validate_representation
from tests.ingestion.mechanical.conftest import (
    CREATURE_KEY,
    DESCRIPTOR_KEY,
    NOW,
    RELEASE_BINDING,
    SPELL_KEY,
    bound_corpus,
    build_ledger,
    build_representation,
    candidate_of,
)

#: One honest exemplar per family, each annotated with the production-corpus
#: text it represents. ``EXEMPLARS`` is asserted to cover the whole union below,
#: so adding a family without an exemplar fails rather than going unnoticed.
EXEMPLARS: dict[FactFamily, Any] = {
    # "an Intelligence (Investigation) check against your spell save DC"
    FactFamily.ABILITY_CHECK: AbilityCheckFact(
        AbilityScore.INTELLIGENCE, DcKind.SPELL_SAVE_DC
    ),
    # Mummy's ability grid: "W IS 12" / "+1" / "+3"
    FactFamily.CREATURE_ABILITY_SCORE: CreatureAbilityScoreFact(
        AbilityScore.WISDOM, 12, modifier=1, save_modifier=3
    ),
    # Wish: "Level 9 Conjuration … Casting Time: Action Range: Self
    # Components: V Duration: Instantaneous"
    FactFamily.SPELL_DESCRIPTOR: SpellDescriptorFact(
        level=9,
        school=SpellSchool.CONJURATION,
        ritual=False,
        concentration=False,
        casting_time=SpellCastingTime(cost=ActionCost.ACTION),
        spell_range=SpellRange(kind=RangeKind.SELF),
        components=SpellComponents(verbal=True, somatic=False, material=False),
        duration=SpellDuration(kind=DurationKind.INSTANTANEOUS),
    ),
    # A class table's "Class Features" column
    FactFamily.PROGRESSION_ENTRY: ProgressionEntryFact(
        level=5, entitlement_key="feature:extra-attack"
    ),
    # A class table's numbered slot columns: level 5, third-level slots, 2
    FactFamily.SPELL_SLOT_PROGRESSION: SpellSlotProgressionFact(
        character_level=5, slot_level=3, slots=2
    ),
    # The "Special" column of a "Spell | School | Special" class spell list
    FactFamily.SPELL_LIST_QUALIFIER: SpellListQualifierFact(
        spell_record_key="spell:cure-wounds", always_prepared=True
    ),
    # "Slam. Melee Attack Roll: +4, reach 5 ft."
    FactFamily.ATTACK_ROLL: AttackRollFact(
        AttackKind.MELEE_WEAPON, to_hit_bonus=4, reach_feet=5
    ),
    # "Hit: 10 (2d6 + 3) Bludgeoning damage."
    FactFamily.DAMAGE: DamageFact(
        damage_type=DamageType.BLUDGEONING,
        dice=DiceExpression(2, DieSize.D6, 3),
        stated_average=10,
    ),
    # Wish, Instant Health: "regain all Hit Points"
    FactFamily.HEALING: HealingFact(restores_all_hit_points=True),
    # Mummy: "Vulnerabilities Fire"
    FactFamily.DAMAGE_RESPONSE: DamageResponseFact(
        DamageResponseKind.VULNERABILITY,
        DamageScope.SPECIFIC,
        damage_type=DamageType.FIRE,
    ),
    # Mummy: "Immunities … Charmed"
    FactFamily.CONDITION_EFFECT: ConditionEffectFact(
        ConditionKind.CHARMED, ConditionEffectKind.IMMUNITY
    ),
    # Mummy: "AC 11" … "HP 58 (9d8 + 18)"
    FactFamily.CREATURE_DEFENSE: CreatureDefenseFact(
        armor_class=11, hit_points=58, hit_point_dice=DiceExpression(9, DieSize.D8, 18)
    ),
    # Mummy: "Speed 20 ft."
    FactFamily.CREATURE_SPEED: CreatureSpeedFact(MovementMode.WALK, 20),
    # "CR 1/2 (XP 100; PB +2)"
    FactFamily.CREATURE_CHALLENGE: CreatureChallengeFact(
        challenge_rating=Rational(1, 2), proficiency_bonus=2
    ),
    # "Casting Time: Bonus Action"
    FactFamily.ACTION_ECONOMY: ActionEconomyFact(ActionCost.BONUS_ACTION),
    # "You can use this feature twice, and you regain all expended uses when you
    # finish a Long Rest."
    FactFamily.RESOURCE_RECOVERY: ResourceRecoveryFact(
        resource_key="feature:channel-divinity",
        recovers_on=RecoveryTrigger.LONG_REST,
        uses=2,
    ),
    # Blinded: "your attack rolls have Disadvantage"
    FactFamily.ADVANTAGE: AdvantageFact(
        AdvantageState.DISADVANTAGE,
        RollSpec(RollActor.SUBJECT, RollContext.ATTACK_ROLL),
    ),
    # Paralyzed: "You automatically fail Strength and Dexterity saving throws."
    FactFamily.AUTOMATIC_OUTCOME: AutomaticOutcomeFact(
        RollSpec(RollActor.SUBJECT, RollContext.SAVING_THROW, AbilityScore.STRENGTH),
        AutomaticOutcome.FAILURE,
    ),
    # Grappled: "Your Speed is 0 and can't increase."
    FactFamily.SPEED_MODIFICATION: SpeedModificationFact(
        change=SpeedChange.SET_TO, feet=0, can_increase=False
    ),
    # Incapacitated: "You can't take any action, Bonus Action, or Reaction."
    FactFamily.ACTION_RESTRICTION: ActionRestrictionFact(ActionCost.REACTION),
    # Unconscious: "Any attack roll that hits you is a Critical Hit if the
    # attacker is within 5 feet of you."
    FactFamily.CRITICAL_HIT_RULE: CriticalHitRuleFact(
        CriticalHitChange.AUTOMATIC_ON_HIT
    ),
    # Incapacitated: "Your Concentration is broken."
    FactFamily.STATE_EFFECT: StateEffectFact(StateEffectKind.CONCENTRATION_BROKEN),
    # "The damage increases by 1d10 for each spell slot level above 4."
    FactFamily.SCALING: ScalingFact(
        basis=ScalingBasis.HIGHER_LEVEL_SPELL_SLOT,
        threshold=4,
        effect=ScalingEffect.DAMAGE,
        dice_amount=DiceExpression(1, DieSize.D10),
    ),
    # A weapon table row: "5 GP" / "2 lb."
    FactFamily.EQUIPMENT_DESCRIPTOR: EquipmentDescriptorFact(
        cost=Money(5, Currency.GP), weight_pounds=Rational(2, 1)
    ),
    # "Versatile (1d10)"
    FactFamily.WEAPON_PROPERTY: WeaponPropertyFact(
        WeaponProperty.VERSATILE, versatile_damage=DiceExpression(1, DieSize.D10)
    ),
}

FAMILY_IDS = [f.value for f in EXEMPLARS]


def test_every_declared_family_has_a_corpus_grounded_exemplar() -> None:
    """A family nobody can name source text for has no business in the union."""
    assert set(EXEMPLARS) == set(FactFamily)


# -- closed: canonical round trip --------------------------------------------


@pytest.mark.parametrize("fact", EXEMPLARS.values(), ids=FAMILY_IDS)
def test_every_family_round_trips_through_its_canonical_payload(fact: Any) -> None:
    payload = fact_payload(fact)
    rebuilt = fact_from_payload(payload)
    assert rebuilt == fact
    assert fact_payload(rebuilt) == payload
    assert fact_key(rebuilt) == fact_key(fact)
    assert fact_invariant_violations(rebuilt) == ()


@pytest.mark.parametrize("fact", EXEMPLARS.values(), ids=FAMILY_IDS)
def test_a_canonical_payload_holds_only_json_primitives(fact: Any) -> None:
    """Nested value objects serialize as plain data, enums as their values.

    A payload holding a live enum member would hash the same as its string but
    compare differently after a round trip, so the stored form and the built
    form would quietly diverge.
    """

    def plain(value: Any) -> bool:
        if isinstance(value, dict):
            return all(isinstance(k, str) and plain(v) for k, v in value.items())
        if isinstance(value, list):
            return all(plain(v) for v in value)
        return value is None or type(value) in (str, int, float, bool)

    assert plain(fact_payload(fact))


@pytest.mark.parametrize("fact", EXEMPLARS.values(), ids=FAMILY_IDS)
def test_a_missing_field_is_rejected_not_defaulted(fact: Any) -> None:
    payload = fact_payload(fact)
    for field in [k for k in payload if k != "family"]:
        without = {k: v for k, v in payload.items() if k != field}
        with pytest.raises(MalformedFactPayloadError, match="missing"):
            fact_from_payload(without)


@pytest.mark.parametrize("fact", EXEMPLARS.values(), ids=FAMILY_IDS)
def test_an_extra_field_is_rejected_not_dropped(fact: Any) -> None:
    with pytest.raises(MalformedFactPayloadError, match="extra"):
        fact_from_payload({**fact_payload(fact), "smuggled": 1})


def test_an_unknown_family_is_rejected() -> None:
    with pytest.raises(UnknownFactFamilyError):
        fact_from_payload({"family": "vibes", "amount": 3})


# -- closed: nested value objects are as strict as families -------------------


@pytest.mark.parametrize(
    ("mutate", "expected"),
    [
        (lambda p: {**p, "dice": {"count": 2, "die": "d6"}}, "missing"),
        (
            lambda p: {**p, "dice": {"count": 2, "die": "d6", "modifier": 3, "x": 1}},
            "extra",
        ),
        (
            lambda p: {**p, "dice": {"count": "2", "die": "d6", "modifier": 3}},
            "integer",
        ),
        (lambda p: {**p, "dice": {"count": 2, "die": "d7", "modifier": 3}}, "DieSize"),
        (lambda p: {**p, "dice": "2d6+3"}, "must be an object"),
    ],
    ids=["missing", "extra", "mistyped", "undeclared-die", "flattened-to-a-string"],
)
def test_a_malformed_nested_value_object_is_rejected(
    mutate: Any, expected: str
) -> None:
    """``2d6 + 3`` is a typed object, never a string somebody parses later."""
    payload = fact_payload(EXEMPLARS[FactFamily.DAMAGE])
    with pytest.raises(MalformedFactPayloadError, match=expected):
        fact_from_payload(mutate(payload))


# -- family contracts, not just field types -----------------------------------


@pytest.mark.parametrize(
    ("fact", "expected"),
    [
        (
            replace(EXEMPLARS[FactFamily.DAMAGE], flat_amount=4),
            "exactly one of a dice expression or a flat amount",
        ),
        (
            replace(EXEMPLARS[FactFamily.HEALING], flat_amount=4),
            "exactly one of a dice expression, a flat amount, or full restoration",
        ),
        (
            replace(EXEMPLARS[FactFamily.CREATURE_SPEED], feet=-5),
            "negative speed",
        ),
        (
            replace(EXEMPLARS[FactFamily.SPELL_SLOT_PROGRESSION], slots=0),
            "grants nothing",
        ),
        (
            replace(EXEMPLARS[FactFamily.WEAPON_PROPERTY], versatile_damage=None),
            "versatile property without its two-handed damage",
        ),
        (
            replace(
                EXEMPLARS[FactFamily.RESOURCE_RECOVERY],
                recharge_die=DieSize.D6,
                recharge_minimum=5,
            ),
            "carries recharge terms",
        ),
        (
            replace(
                EXEMPLARS[FactFamily.CREATURE_CHALLENGE],
                challenge_rating=Rational(1, 0),
            ),
            "denominator 0 is not positive",
        ),
    ],
    ids=[
        "damage-two-amounts",
        "healing-two-amounts",
        "negative-speed",
        "slot-grants-nothing",
        "versatile-without-damage",
        "recharge-terms-on-a-rest",
        "challenge-rating-over-zero",
    ],
)
def test_a_fact_that_contradicts_its_own_contract_is_reported(
    fact: Any, expected: str
) -> None:
    """Union membership is not validity. Such a fact is unusable authority."""
    violations = fact_invariant_violations(fact)
    assert any(expected in v for v in violations), violations


def test_a_spell_descriptor_disagreeing_with_its_own_duration_is_rejected() -> None:
    """One printed claim, spelled twice, must not say two things."""
    descriptor = EXEMPLARS[FactFamily.SPELL_DESCRIPTOR]
    contradictory = replace(
        descriptor,
        duration=SpellDuration(
            kind=DurationKind.TIMED, amount=1, unit=TimeUnit.MINUTE, concentration=True
        ),
    )
    assert any(
        "disagrees with duration" in v for v in fact_invariant_violations(contradictory)
    )


# -- not an escape hatch ------------------------------------------------------


def test_spell_slot_progression_indexes_the_slot_level_with_a_typed_field() -> None:
    """The class table's second dimension is a typed integer, not a string.

    ``entitlement_key="slots_level_3"`` would satisfy the older family and is
    exactly the stringly escape hatch ADR-005d Decision 4 forbids. It is not
    representable here: the field is an ``int``, and a string is rejected.
    """
    fact = EXEMPLARS[FactFamily.SPELL_SLOT_PROGRESSION]
    assert isinstance(fact.slot_level, int)
    payload = fact_payload(fact)
    assert payload["slot_level"] == 3
    with pytest.raises(MalformedFactPayloadError, match="integer"):
        fact_from_payload({**payload, "slot_level": "3"})


def test_progression_entry_cannot_carry_a_blank_or_absent_entitlement() -> None:
    """The remaining string field is a semantic key, and it must actually name one."""
    assert any(
        "without an entitlement key" in v
        for v in fact_invariant_violations(
            replace(EXEMPLARS[FactFamily.PROGRESSION_ENTRY], entitlement_key="  ")
        )
    )


def test_challenge_rating_stays_an_exact_fraction() -> None:
    """``CR 1/2`` is exact source data; a float would invent precision."""
    payload = fact_payload(EXEMPLARS[FactFamily.CREATURE_CHALLENGE])
    assert payload["challenge_rating"] == {"numerator": 1, "denominator": 2}
    with pytest.raises(MalformedFactPayloadError, match="integer"):
        fact_from_payload(
            {**payload, "challenge_rating": {"numerator": 0.5, "denominator": 1}}
        )


# -- persistence, reconstruction, and the membership relation -----------------


def test_every_family_survives_persistence_and_reconstruction(
    session: Session,
) -> None:
    """A family the store cannot reconstruct is a family the projection cannot keep.

    All twenty at once, on one component, so a family added without a persisted
    round trip fails here rather than the first time a real corpus carries it.
    """
    draft = build_representation(
        components=(
            ComponentDraft(
                record_key=SPELL_KEY,
                semantic_key=DESCRIPTOR_KEY,
                handling=ComponentHandling.STRUCTURED,
                facts=tuple(EXEMPLARS.values()),
            ),
            build_representation().components[1],
        )
    )
    identified = identify_projection(
        candidate_of(RELEASE_BINDING, build_ledger(), draft)
    )
    persist_draft(session, identified, now=NOW)
    session.flush()

    rebuilt = reconstruct_candidate(session, identified.projection_uuid)
    (component,) = [
        c for c in rebuilt.representation.components if c.semantic_key == DESCRIPTOR_KEY
    ]
    assert set(component.facts) == set(EXEMPLARS.values())
    assert identify_projection(rebuilt).projection_uuid == identified.projection_uuid


#: A class record and a spell record, so a spell-list claim can be stated with
#: the endpoints it actually means. The bounded fixture has a spell and a
#: creature but no class, and a spell list belongs to a class.
CLASS_KEY = "class:wizard"
LISTED_SPELL_KEY = "spell:cure-wounds"
SPELL_LIST_KEY = "spell-list"


def _spell_list_draft(
    *,
    qualifier: SpellListQualifierFact | None = None,
    source_key: str = CLASS_KEY,
    source_kind: RecordKind = RecordKind.CLASS,
    target_key: str = LISTED_SPELL_KEY,
    target_kind: RecordKind = RecordKind.SPELL,
    with_edge: bool = True,
    qualifier_on: str | None = None,
) -> RepresentationDraft:
    """The bounded fixture plus one class spell list, perturbable per control."""
    base = build_representation()
    facts = (qualifier,) if qualifier is not None else ()
    owner = qualifier_on or source_key
    return build_representation(
        records=base.records
        + (
            RecordDraft(semantic_key=source_key, kind=source_kind),
            RecordDraft(semantic_key=target_key, kind=target_kind),
        ),
        components=base.components
        + (
            ComponentDraft(
                record_key=owner,
                semantic_key=SPELL_LIST_KEY,
                handling=ComponentHandling.STRUCTURED,
                facts=facts or (EXEMPLARS[FactFamily.PROGRESSION_ENTRY],),
            ),
        ),
        relationships=base.relationships
        + (
            (
                RelationshipDraft(
                    source_record_key=source_key,
                    target_record_key=target_key,
                    kind=RelationshipKind.SPELL_LIST_MEMBER,
                ),
            )
            if with_edge
            else ()
        ),
    )


def _spell_list_findings(**kwargs: Any) -> list[str]:
    """Only the spell-list judgements.

    The perturbed draft adds records and a component with no provenance edges,
    which the provenance validator reports for reasons unrelated to spell lists.
    Narrowing to the two message families under test stops a positive control
    from failing — or a negative one from passing — for the wrong reason.
    """
    findings = validate_representation(
        _spell_list_draft(**kwargs), build_ledger(), bound_corpus()
    )
    return [
        f
        for f in findings
        if f.startswith("spell-list membership") or f.startswith("spell-list qualifier")
    ]


QUALIFIER = SpellListQualifierFact(
    spell_record_key=LISTED_SPELL_KEY, always_prepared=True
)


def test_a_class_to_spell_membership_with_a_qualifier_is_accepted() -> None:
    """The shape the 73 ``Spell | School | Special`` tables actually state."""
    assert _spell_list_findings(qualifier=QUALIFIER) == []


def test_membership_without_a_qualifier_remains_valid() -> None:
    """Most rows say nothing in the Special column, and must not have to.

    Requiring a qualifier per edge would force one to be invented for every
    ordinary spell on every class list.
    """
    assert _spell_list_findings() == []


def test_a_membership_edge_from_a_non_class_record_is_rejected() -> None:
    """A spell list belongs to a class; any other source states something else."""
    findings = _spell_list_findings(
        qualifier=QUALIFIER, source_key=CREATURE_KEY, source_kind=RecordKind.CREATURE
    )
    assert any("a spell list belongs to a class" in f for f in findings), findings


def test_a_membership_edge_to_a_non_spell_record_is_rejected() -> None:
    """The case the previous revision accepted: a spell-to-creature edge.

    A consumer reading these edges as spell-list eligibility would have received
    an arbitrary record as a member.
    """
    findings = _spell_list_findings(
        target_key=CREATURE_KEY, target_kind=RecordKind.CREATURE
    )
    assert any("only a spell can be on a spell list" in f for f in findings), findings


def test_a_qualifier_naming_a_non_spell_record_is_rejected() -> None:
    findings = _spell_list_findings(
        qualifier=SpellListQualifierFact(
            spell_record_key=CREATURE_KEY, always_prepared=True
        ),
        target_key=CREATURE_KEY,
        target_kind=RecordKind.CREATURE,
    )
    assert any("a spell-list qualifier names a spell" in f for f in findings), findings


def test_a_qualifier_on_a_non_class_record_is_rejected() -> None:
    """The Special column is a column of the class's own table."""
    findings = _spell_list_findings(qualifier=QUALIFIER, qualifier_on=SPELL_KEY)
    assert any("belongs to the class stating the list" in f for f in findings), findings


def test_a_spell_list_qualifier_needs_its_membership_edge() -> None:
    """The fact and the relationship are one claim, split by what each can say.

    The edge is the membership classification; the fact is what the ``Special``
    column says about it. A qualifier alone would describe a membership the
    projection never declares, and would vanish from any consumer reading the
    relationship graph.
    """
    findings = _spell_list_findings(qualifier=QUALIFIER, with_edge=False)
    assert any("does not declare as a spell_list_member" in f for f in findings)


def test_a_spell_list_qualifier_naming_no_record_is_rejected() -> None:
    findings = _spell_list_findings(
        qualifier=SpellListQualifierFact(
            spell_record_key="spell:not-in-this-projection", always_prepared=True
        )
    )
    assert any("unknown spell record" in f for f in findings)


# -- the invariant checkers themselves ----------------------------------------
#
# Membership of the closed union is not validity: a fact can be a declared
# family and still contradict its own contract, and such a fact would persist as
# mechanically unusable authority. The checkers are that safety net, so they are
# exercised across every family and every field here, rather than only at the
# handful of contradictions somebody thought to write down.


def _wrong_typed(value: Any) -> Any:
    """A value of the wrong type for the field *value* came from.

    Chosen to be the mistakes that actually slip through: a string where a
    Boolean belongs (``"false"`` is truthy), a Boolean where an integer belongs
    (``bool`` is an ``int`` subclass), and a plain string where an enum member
    belongs (``StrEnum`` members *are* strings).
    """
    if isinstance(value, bool):
        return "false"
    if isinstance(value, StrEnum):
        return str(value.value)
    if isinstance(value, int):
        return True
    if isinstance(value, str):
        return 42
    return "not-a-value-object"


@pytest.mark.parametrize("fact", EXEMPLARS.values(), ids=FAMILY_IDS)
def test_every_field_of_every_family_is_type_checked(fact: Any) -> None:
    """Mistyping any declared field is reported, for every family.

    Generic rather than per-family on purpose: a family added with a checker
    that forgets one of its fields fails here, without anyone having to remember
    to hand-write that family's negative control.
    """
    for spec in fields(type(fact)):
        original = getattr(fact, spec.name)
        if original is None:
            continue  # An unset optional field has no type to get wrong.
        broken = replace(fact, **{spec.name: _wrong_typed(original)})
        violations = fact_invariant_violations(broken)
        assert violations, f"{type(fact).__name__}.{spec.name} accepted a wrong type"
        assert any(spec.name in v for v in violations), (
            f"{type(fact).__name__}.{spec.name} was rejected, but no violation "
            f"named it: {violations}"
        )


#: Which family each shared value object hangs off, so a value-object control
#: can be written once and checked through a real fact.
_HOLDERS: dict[type, tuple[FactFamily, str]] = {
    DiceExpression: (FactFamily.DAMAGE, "dice"),
    Rational: (FactFamily.CREATURE_CHALLENGE, "challenge_rating"),
    Money: (FactFamily.EQUIPMENT_DESCRIPTOR, "cost"),
    SpellCastingTime: (FactFamily.SPELL_DESCRIPTOR, "casting_time"),
    SpellRange: (FactFamily.SPELL_DESCRIPTOR, "spell_range"),
    SpellComponents: (FactFamily.SPELL_DESCRIPTOR, "components"),
    SpellDuration: (FactFamily.SPELL_DESCRIPTOR, "duration"),
}


def _holding(value: Any, value_type: type) -> Any:
    family, field = _HOLDERS[value_type]
    return replace(EXEMPLARS[family], **{field: value})


@pytest.mark.parametrize(
    "value_object",
    [
        DiceExpression(2, DieSize.D6, 3),
        Rational(1, 2),
        Money(5, Currency.GP),
        SpellCastingTime(cost=ActionCost.ACTION),
        SpellRange(kind=RangeKind.RANGED, feet=60),
        SpellComponents(verbal=True, somatic=True, material=False),
        SpellDuration(kind=DurationKind.TIMED, amount=1, unit=TimeUnit.MINUTE),
    ],
    ids=[
        "dice",
        "rational",
        "money",
        "casting-time",
        "range",
        "components",
        "duration",
    ],
)
def test_a_value_object_replaced_by_a_look_alike_dict_is_rejected(
    value_object: Any,
) -> None:
    """A nested value object is as closed as a family.

    A dict with exactly the right keys is not a :class:`DiceExpression`, and
    accepting one would reopen the untyped escape hatch through the back door.
    """
    as_dict = {
        f.name: getattr(value_object, f.name) for f in fields(type(value_object))
    }
    violations = fact_invariant_violations(_holding(as_dict, type(value_object)))
    assert any("must be" in v for v in violations), violations


@pytest.mark.parametrize(
    ("value_object", "expected"),
    [
        (DiceExpression(0, DieSize.D6), "rolls no dice"),
        (Rational(-1, 2), "is negative"),
        (Rational(1, 0), "is not positive"),
        (Money(-5, Currency.GP), "is negative"),
        (SpellCastingTime(), "exactly one of an action cost or an elapsed time"),
        (
            SpellCastingTime(cost=ActionCost.ACTION, amount=1, unit=TimeUnit.MINUTE),
            "exactly one of an action cost or an elapsed time",
        ),
        (SpellCastingTime(amount=1), "needs both amount and unit"),
        (SpellRange(kind=RangeKind.RANGED), "a ranged spell states a distance"),
        (SpellRange(kind=RangeKind.RANGED, feet=0), "is not a distance"),
        (
            SpellRange(kind=RangeKind.SELF, feet=30),
            "the distance comes from the named kind",
        ),
        (
            SpellComponents(
                verbal=True, somatic=False, material=False, material_consumed=True
            ),
            "consumes a material component it does not have",
        ),
        (SpellDuration(kind=DurationKind.TIMED), "needs both amount and unit"),
        (
            SpellDuration(
                kind=DurationKind.INSTANTANEOUS, amount=1, unit=TimeUnit.MINUTE
            ),
            "the length comes from the named kind",
        ),
    ],
)
def test_a_value_object_that_contradicts_its_own_contract_is_reported(
    value_object: Any, expected: str
) -> None:
    """ "The value comes from the named kind, not from the fact", held.

    Each of these would otherwise persist as authority stating two incompatible
    things about one printed value.
    """
    violations = fact_invariant_violations(_holding(value_object, type(value_object)))
    assert any(expected in v for v in violations), violations


@pytest.mark.parametrize(
    ("fact", "expected"),
    [
        (
            replace(EXEMPLARS[FactFamily.ABILITY_CHECK], dc_kind=DcKind.FIXED),
            "fixed DC without a dc_value",
        ),
        (
            replace(EXEMPLARS[FactFamily.ABILITY_CHECK], dc_value=15),
            "the value comes from the named source",
        ),
        (
            replace(EXEMPLARS[FactFamily.CREATURE_ABILITY_SCORE], score=-1),
            "negative ability score",
        ),
        (
            replace(EXEMPLARS[FactFamily.SPELL_DESCRIPTOR], level=-1),
            "negative spell level",
        ),
        (
            replace(EXEMPLARS[FactFamily.PROGRESSION_ENTRY], level=-1),
            "negative progression level",
        ),
        (
            replace(EXEMPLARS[FactFamily.PROGRESSION_ENTRY], quantity=0),
            "grants nothing",
        ),
        (
            replace(EXEMPLARS[FactFamily.SPELL_SLOT_PROGRESSION], character_level=0),
            "is not a level",
        ),
        (
            replace(EXEMPLARS[FactFamily.SPELL_SLOT_PROGRESSION], slot_level=0),
            "is not a slot level",
        ),
        (
            replace(EXEMPLARS[FactFamily.SPELL_LIST_QUALIFIER], spell_record_key="  "),
            "without a spell record key",
        ),
        (
            replace(
                EXEMPLARS[FactFamily.SPELL_LIST_QUALIFIER],
                always_prepared=False,
                minimum_class_level=None,
            ),
            "states no qualifier",
        ),
        (
            replace(EXEMPLARS[FactFamily.SPELL_LIST_QUALIFIER], minimum_class_level=0),
            "is not a level",
        ),
        (
            replace(EXEMPLARS[FactFamily.ATTACK_ROLL], reach_feet=0),
            "reach_feet 0 is not a distance",
        ),
        (
            replace(
                EXEMPLARS[FactFamily.ATTACK_ROLL],
                reach_feet=None,
                range_normal_feet=100,
                range_long_feet=20,
            ),
            "is shorter than",
        ),
        (
            replace(
                EXEMPLARS[FactFamily.ATTACK_ROLL], reach_feet=None, range_long_feet=100
            ),
            "range_long_feet without a normal range",
        ),
        (
            replace(EXEMPLARS[FactFamily.DAMAGE], dice=None, flat_amount=0),
            "deals no damage",
        ),
        (
            replace(EXEMPLARS[FactFamily.DAMAGE], stated_average=0),
            "stated_average 0 deals no damage",
        ),
        (
            replace(
                EXEMPLARS[FactFamily.HEALING],
                restores_all_hit_points=False,
                flat_amount=0,
            ),
            "restores nothing",
        ),
        (
            replace(EXEMPLARS[FactFamily.CREATURE_DEFENSE], hit_points=0),
            "is not a living creature",
        ),
        (
            replace(EXEMPLARS[FactFamily.CREATURE_DEFENSE], armor_class=-1),
            "negative armor_class",
        ),
        (
            replace(EXEMPLARS[FactFamily.CREATURE_SPEED], feet=-5),
            "negative speed",
        ),
        (
            replace(EXEMPLARS[FactFamily.RESOURCE_RECOVERY], resource_key=" "),
            "without a resource key",
        ),
        (
            replace(EXEMPLARS[FactFamily.RESOURCE_RECOVERY], uses=0),
            "grants nothing",
        ),
        (
            replace(
                EXEMPLARS[FactFamily.RESOURCE_RECOVERY],
                recovers_on=RecoveryTrigger.RECHARGE_ROLL,
            ),
            "needs both a die and a minimum roll",
        ),
        (
            replace(
                EXEMPLARS[FactFamily.RESOURCE_RECOVERY],
                recovers_on=RecoveryTrigger.RECHARGE_ROLL,
                recharge_die=DieSize.D6,
                recharge_minimum=0,
            ),
            "always succeeds",
        ),
        (
            replace(EXEMPLARS[FactFamily.SCALING], threshold=-1),
            "negative scaling threshold",
        ),
        (
            replace(EXEMPLARS[FactFamily.SCALING], dice_amount=None),
            "exactly one of a dice amount or an amount",
        ),
        (
            replace(
                EXEMPLARS[FactFamily.SCALING],
                effect=ScalingEffect.EFFECTIVE_SPELL_LEVEL,
            ),
            "the value comes from the slot level itself",
        ),
        (
            replace(EXEMPLARS[FactFamily.SCALING], dice_amount=None, amount=0),
            "changes nothing",
        ),
        (EquipmentDescriptorFact(), "states neither a cost nor a weight"),
        (
            replace(
                EXEMPLARS[FactFamily.WEAPON_PROPERTY],
                weapon_property=WeaponProperty.HEAVY,
            ),
            "carries versatile damage",
        ),
        (
            replace(
                EXEMPLARS[FactFamily.WEAPON_PROPERTY],
                weapon_property=WeaponProperty.THROWN,
                versatile_damage=None,
            ),
            "thrown property without a normal range",
        ),
        (
            replace(
                EXEMPLARS[FactFamily.WEAPON_PROPERTY],
                versatile_damage=DiceExpression(1, DieSize.D10),
                thrown_range_normal_feet=20,
            ),
            "carries a thrown range",
        ),
        (
            replace(
                EXEMPLARS[FactFamily.WEAPON_PROPERTY],
                weapon_property=WeaponProperty.THROWN,
                versatile_damage=None,
                thrown_range_normal_feet=20,
                thrown_range_long_feet=0,
            ),
            "thrown_range_long_feet 0 is not a distance",
        ),
    ],
)
def test_each_family_reports_its_own_contract_violation(
    fact: Any, expected: str
) -> None:
    """One control per contract clause, so no clause goes unexercised."""
    violations = fact_invariant_violations(fact)
    assert any(expected in v for v in violations), violations


def test_a_structure_outside_the_union_has_no_contract_to_check() -> None:
    """Reported as non-membership, rather than crashing on a missing checker."""
    violations = fact_invariant_violations(DiceExpression(1, DieSize.D6))
    assert violations == (
        "DiceExpression is not a member of the closed typed-fact union",
    )


# -- recharge thresholds the die can actually reach ---------------------------


@pytest.mark.parametrize("die", list(DieSize), ids=[d.value for d in DieSize])
def test_a_recharge_minimum_equal_to_the_die_maximum_is_attainable(
    die: DieSize,
) -> None:
    """``Recharge 6`` on a d6 is a real stat-block line, so the bound is inclusive."""
    fact = replace(
        EXEMPLARS[FactFamily.RESOURCE_RECOVERY],
        recovers_on=RecoveryTrigger.RECHARGE_ROLL,
        recharge_die=die,
        recharge_minimum=die.faces,
    )
    assert fact_invariant_violations(fact) == ()


@pytest.mark.parametrize("die", list(DieSize), ids=[d.value for d in DieSize])
def test_a_recharge_minimum_above_the_die_maximum_is_rejected(die: DieSize) -> None:
    """One past the top of the die is a resource that can never come back.

    It would otherwise validate, persist, and publish as typed authority for a
    feature that never recharges.
    """
    fact = replace(
        EXEMPLARS[FactFamily.RESOURCE_RECOVERY],
        recovers_on=RecoveryTrigger.RECHARGE_ROLL,
        recharge_die=die,
        recharge_minimum=die.faces + 1,
    )
    violations = fact_invariant_violations(fact)
    assert any("is unreachable on" in v for v in violations), violations


def test_the_die_range_comes_from_the_die_itself() -> None:
    """No parallel table to fall out of step with the union."""
    assert [d.faces for d in DieSize] == [4, 6, 8, 10, 12, 20, 100]


def test_the_existing_recharge_controls_remain_green() -> None:
    """The new upper bound did not displace the checks already there."""
    base = replace(
        EXEMPLARS[FactFamily.RESOURCE_RECOVERY],
        recovers_on=RecoveryTrigger.RECHARGE_ROLL,
        recharge_die=DieSize.D6,
        recharge_minimum=5,
    )
    assert fact_invariant_violations(base) == ()
    assert any(
        "always succeeds" in v
        for v in fact_invariant_violations(replace(base, recharge_minimum=0))
    )
    assert any(
        "needs both a die and a minimum roll" in v
        for v in fact_invariant_violations(replace(base, recharge_minimum=None))
    )
    assert any(
        "carries recharge terms" in v
        for v in fact_invariant_violations(
            replace(base, recovers_on=RecoveryTrigger.LONG_REST)
        )
    )


def test_an_unreachable_recharge_still_fails_after_reconstruction(
    session: Session,
) -> None:
    """The publication path exercises this over reconstructed state, not memory.

    A fact that only failed in-memory validation could be persisted by an
    authoring path and then published from the database.
    """
    unreachable = replace(
        EXEMPLARS[FactFamily.RESOURCE_RECOVERY],
        recovers_on=RecoveryTrigger.RECHARGE_ROLL,
        recharge_die=DieSize.D6,
        recharge_minimum=7,
    )
    draft = build_representation(
        components=(
            ComponentDraft(
                record_key=SPELL_KEY,
                semantic_key=DESCRIPTOR_KEY,
                handling=ComponentHandling.STRUCTURED,
                facts=(unreachable,),
            ),
            build_representation().components[1],
        )
    )
    identified = identify_projection(
        candidate_of(RELEASE_BINDING, build_ledger(), draft)
    )
    persist_draft(session, identified, now=NOW)
    session.flush()

    rebuilt = reconstruct_candidate(session, identified.projection_uuid)
    findings = validate_representation(
        rebuilt.representation, rebuilt.classification, bound_corpus()
    )
    assert any("is unreachable on" in f for f in findings), findings
