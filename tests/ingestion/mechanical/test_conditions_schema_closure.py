"""The conditions batch's schema closure — CRD Issue 5d, #137 contracts 3 and 4.

The first production-content batch (the 15 SRD conditions and the ``Condition``
glossary rule) proposed 33 clauses as ``UNRESOLVED`` because the closed typed
union could not carry them. Four of those were not lossy but *broken*: the union
produced authority that was identical for opposite rules, rejected as a
duplicate, structurally impossible, or simply false.

Every test here fails against the pre-closure union. Each one quotes the
production-corpus clause it exists for, because a family is only admitted with
the source text that forces it.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from afterworlds.ingestion.mechanical.accounting import derive_span_id
from afterworlds.ingestion.mechanical.models import (
    ComponentHandling,
    ReviewState,
    SemanticDisposition,
    SemanticSpan,
)
from afterworlds.ingestion.mechanical.representation import (
    AbilityScore,
    ActionCost,
    ActionRestrictionFact,
    AdvantageFact,
    AdvantageState,
    AutomaticOutcome,
    AutomaticOutcomeFact,
    ComponentDraft,
    CriticalHitChange,
    CriticalHitRuleFact,
    DamageResponseFact,
    DamageResponseKind,
    DamageScope,
    DamageType,
    DiceExpression,
    DieSize,
    MalformedFactPayloadError,
    MovementMode,
    ProvenanceClaim,
    ProvenanceRole,
    ProvenanceTargetKind,
    RecordDraft,
    RecordKind,
    RepresentationDraft,
    RollActor,
    RollContext,
    RollSpec,
    ScalingBasis,
    ScalingDirection,
    ScalingEffect,
    ScalingFact,
    SpeedChange,
    SpeedModificationFact,
    StateEffectFact,
    StateEffectKind,
    fact_from_payload,
    fact_invariant_violations,
    fact_key,
    fact_payload,
    fact_target_key,
)
from afterworlds.ingestion.mechanical.validation import validate_representation
from tests.ingestion.mechanical.conftest import (
    SPELL_LEAF,
    bound_corpus,
    build_ledger,
)

ATTACK = RollContext.ATTACK_ROLL
SAVE = RollContext.SAVING_THROW
CHECK = RollContext.ABILITY_CHECK
MINE, THEIRS = RollActor.SUBJECT, RollActor.AGAINST_SUBJECT
ADV, DIS = AdvantageState.ADVANTAGE, AdvantageState.DISADVANTAGE


def keys(*facts: object) -> set[str]:
    return {fact_key(f) for f in facts}


# ---------------------------------------------------------------------------
# 1. Blinded and Invisible are opposite rules and must not share authority
# ---------------------------------------------------------------------------

#: Blinded, p177: "Attack rolls against you have Advantage, and your attack
#: rolls have Disadvantage."
BLINDED = (
    AdvantageFact(ADV, RollSpec(THEIRS, ATTACK)),
    AdvantageFact(DIS, RollSpec(MINE, ATTACK)),
)

#: Invisible, p184, the exact inverse: "Attack rolls against you have
#: Disadvantage, and your attack rolls have Advantage."
INVISIBLE = (
    AdvantageFact(DIS, RollSpec(THEIRS, ATTACK)),
    AdvantageFact(ADV, RollSpec(MINE, ATTACK)),
)


def test_blinded_and_invisible_do_not_collapse_to_the_same_authority() -> None:
    """The defect that stopped the conditions batch, stated as its inverse.

    Before ``RollSpec``, both conditions reduced to ``{advantage+attack_roll,
    disadvantage+attack_roll}`` — byte-identical fact keys for opposite rules,
    so a deterministic consumer reading the typed surface could not tell being
    Blinded from being Invisible.
    """
    assert keys(*BLINDED) != keys(*INVISIBLE)
    # Not merely different in aggregate: no single fact is shared.
    assert keys(*BLINDED).isdisjoint(keys(*INVISIBLE))


def test_the_polarity_survives_canonical_serialization() -> None:
    """Distinctness must hold in the persisted form, not only in memory."""
    for mine, theirs in ((BLINDED[1], BLINDED[0]), (INVISIBLE[1], INVISIBLE[0])):
        assert fact_payload(mine)["roll"] != fact_payload(theirs)["roll"]
        assert fact_from_payload(fact_payload(mine)) == mine
        assert fact_from_payload(fact_payload(theirs)) == theirs


# ---------------------------------------------------------------------------
# 2. Prone states three attack-roll rules in one clause
# ---------------------------------------------------------------------------

#: Prone, p186: "You have Disadvantage on attack rolls. An attack roll against
#: you has Advantage if the attacker is within 5 feet of you. Otherwise, that
#: attack roll has Disadvantage."
PRONE_SELF = AdvantageFact(DIS, RollSpec(MINE, ATTACK))
PRONE_AGAINST_NEAR = AdvantageFact(ADV, RollSpec(THEIRS, ATTACK))
PRONE_AGAINST_OTHERWISE = AdvantageFact(DIS, RollSpec(THEIRS, ATTACK))


def test_prones_three_attack_claims_are_three_distinct_facts() -> None:
    """Before ``RollSpec`` the self-attack and 'otherwise' claims were one key.

    ``validate_representation`` rejected the component as carrying a duplicate
    typed fact, so the clause could not be represented at all.
    """
    facts = (PRONE_SELF, PRONE_AGAINST_NEAR, PRONE_AGAINST_OTHERWISE)
    assert len(keys(*facts)) == 3


def test_prones_component_validates_without_a_duplicate_fact() -> None:
    """The whole clause, as one component, through the production validator."""
    findings = _validate((PRONE_SELF, PRONE_AGAINST_NEAR, PRONE_AGAINST_OTHERWISE))
    assert not findings, findings


def test_the_proximity_and_otherwise_branches_stay_distinguishable() -> None:
    """The two rolls *against* the subject differ by advantage state.

    The circumstance that selects between them — "if the attacker is within 5
    feet of you" — remains governing prose on a ``MIXED`` component, which is
    this module's existing contract for a stated qualifier. What the schema owes
    is that the two outcomes are not the same claim, and they are not.
    """
    assert fact_key(PRONE_AGAINST_NEAR) != fact_key(PRONE_AGAINST_OTHERWISE)
    assert fact_key(PRONE_AGAINST_OTHERWISE) != fact_key(PRONE_SELF)


# ---------------------------------------------------------------------------
# 3. An ability-qualified saving throw cannot widen into every saving throw
# ---------------------------------------------------------------------------

#: Restrained, p187: "You have Disadvantage on Dexterity saving throws."
RESTRAINED_SAVE = AdvantageFact(DIS, RollSpec(MINE, SAVE, AbilityScore.DEXTERITY))


def test_a_dexterity_save_is_not_the_same_claim_as_every_save() -> None:
    """The pre-closure form asserted disadvantage on *all* saving throws.

    That is not a lossy representation of the source; it is a false one, and it
    is the reason the clause was proposed unresolved rather than typed.
    """
    unqualified = AdvantageFact(DIS, RollSpec(MINE, SAVE))
    assert fact_key(RESTRAINED_SAVE) != fact_key(unqualified)
    assert fact_payload(RESTRAINED_SAVE)["roll"]["ability"] == "dexterity"
    assert fact_payload(unqualified)["roll"]["ability"] is None


def test_the_ability_qualifier_survives_reconstruction() -> None:
    """A round trip that dropped ``ability`` would silently widen the claim."""
    rebuilt = fact_from_payload(fact_payload(RESTRAINED_SAVE))
    assert rebuilt == RESTRAINED_SAVE
    assert rebuilt.roll.ability is AbilityScore.DEXTERITY  # type: ignore[union-attr]


def test_a_payload_missing_the_ability_key_is_rejected_not_defaulted() -> None:
    """Absent is not "no ability": a dropped key must fail, not widen."""
    payload = fact_payload(RESTRAINED_SAVE)
    del payload["roll"]["ability"]  # type: ignore[index]
    with pytest.raises(MalformedFactPayloadError):
        fact_from_payload(payload)


def test_paralyzeds_two_automatic_failures_are_two_facts() -> None:
    """Paralyzed, p186: "You automatically fail Strength and Dexterity saving
    throws." — two named rolls, so two claims, distinguished by ability."""
    strength = AutomaticOutcomeFact(
        RollSpec(MINE, SAVE, AbilityScore.STRENGTH), AutomaticOutcome.FAILURE
    )
    dexterity = AutomaticOutcomeFact(
        RollSpec(MINE, SAVE, AbilityScore.DEXTERITY), AutomaticOutcome.FAILURE
    )
    assert fact_key(strength) != fact_key(dexterity)
    # An automatic failure is not an extreme disadvantage, and the two families
    # must not be interchangeable.
    assert fact_key(strength) != fact_key(
        AdvantageFact(DIS, RollSpec(MINE, SAVE, AbilityScore.STRENGTH))
    )


# ---------------------------------------------------------------------------
# 4. "Resistance to all damage" is one claim with one provenance
# ---------------------------------------------------------------------------

#: Petrified, p186: "You have Resistance to all damage."
ALL_DAMAGE = DamageResponseFact(DamageResponseKind.RESISTANCE, DamageScope.ALL)


def test_resistance_to_all_damage_is_a_single_typed_claim() -> None:
    assert not fact_invariant_violations(ALL_DAMAGE)
    assert fact_from_payload(fact_payload(ALL_DAMAGE)) == ALL_DAMAGE


def test_all_damage_needs_exactly_one_primary_provenance_claim() -> None:
    """The reason enumeration was not an option.

    Thirteen enumerated facts would each need a ``PRIMARY`` claim on the one
    span that says "all damage", and validation rejects that as conflicting
    primary claims. One fact needs one claim, and validates.
    """
    assert not _validate((ALL_DAMAGE,))


def test_enumerating_every_damage_type_is_structurally_rejected() -> None:
    """The workaround the schema exists to make impossible, exercised."""
    enumerated = tuple(
        DamageResponseFact(
            DamageResponseKind.RESISTANCE, DamageScope.SPECIFIC, damage_type=t
        )
        for t in DamageType
    )
    findings = _validate(enumerated, all_facts_claim_one_span=True)
    assert [f for f in findings if "conflicting primary claims" in f], findings


@pytest.mark.parametrize(
    "fact",
    [
        # Barbarian: "Resistance to all damage except Force damage."
        DamageResponseFact(
            DamageResponseKind.RESISTANCE,
            DamageScope.ALL,
            except_types=(DamageType.FORCE,),
        ),
        # Boon of Truesight: "Resistance to all damage except Psychic and Radiant."
        DamageResponseFact(
            DamageResponseKind.RESISTANCE,
            DamageScope.ALL,
            except_types=(DamageType.PSYCHIC, DamageType.RADIANT),
        ),
        # The mummy lord's heart: "Immunity to all damage except Fire."
        DamageResponseFact(
            DamageResponseKind.IMMUNITY,
            DamageScope.ALL,
            except_types=(DamageType.FIRE,),
        ),
    ],
)
def test_all_damage_except_siblings_are_expressible(fact: DamageResponseFact) -> None:
    """The three corpus-wide "all except" forms, none of them a condition."""
    assert not fact_invariant_violations(fact)
    assert fact_from_payload(fact_payload(fact)) == fact


def test_exception_order_cannot_mint_a_second_fact_key() -> None:
    """One claim, one canonical payload.

    Tuple order reaches the payload and therefore the fact key, so an unsorted
    exception list would make "Psychic and Radiant" and "Radiant and Psychic"
    two different facts about the same rule.
    """
    unsorted = DamageResponseFact(
        DamageResponseKind.RESISTANCE,
        DamageScope.ALL,
        except_types=(DamageType.RADIANT, DamageType.PSYCHIC),
    )
    assert any("not sorted" in v for v in fact_invariant_violations(unsorted))


# ---------------------------------------------------------------------------
# 5. Widening, contradiction, and invalid combinations fail closed
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("fact", "expected"),
    [
        # An attack roll has no ability qualifier in the source's phrasing;
        # allowing one would let a fact invent a restriction.
        (
            AdvantageFact(DIS, RollSpec(MINE, ATTACK, AbilityScore.STRENGTH)),
            "names an ability only for ability checks and saving throws",
        ),
        # Initiative is rolled by the creature whose turn order it sets.
        (
            AdvantageFact(ADV, RollSpec(THEIRS, RollContext.INITIATIVE)),
            "Initiative rolled against the subject",
        ),
        # "all damage" and a named type are two different claims.
        (
            DamageResponseFact(
                DamageResponseKind.RESISTANCE,
                DamageScope.ALL,
                damage_type=DamageType.FIRE,
            ),
            "also names a damage type",
        ),
        # A specific response has nothing to except.
        (
            DamageResponseFact(
                DamageResponseKind.RESISTANCE,
                DamageScope.SPECIFIC,
                damage_type=DamageType.FIRE,
                except_types=(DamageType.COLD,),
            ),
            "specific damage response carries exceptions",
        ),
        (
            DamageResponseFact(DamageResponseKind.RESISTANCE, DamageScope.SPECIFIC),
            "names no damage type",
        ),
        (
            DamageResponseFact(
                DamageResponseKind.IMMUNITY,
                DamageScope.ALL,
                except_types=(DamageType.FIRE, DamageType.FIRE),
            ),
            "repeats a damage type",
        ),
        # "You can't take any none" states nothing.
        (
            ActionRestrictionFact(ActionCost.NONE),
            "is not an action-economy slot to restrict",
        ),
        # Any hit is a Critical Hit; a threshold would be a second rule.
        (
            CriticalHitRuleFact(CriticalHitChange.AUTOMATIC_ON_HIT, threshold=19),
            "carries a threshold",
        ),
        (
            CriticalHitRuleFact(CriticalHitChange.THRESHOLD_LOWERED),
            "states no threshold",
        ),
        (
            CriticalHitRuleFact(CriticalHitChange.THRESHOLD_LOWERED, threshold=21),
            "is not a lowered d20 threshold",
        ),
        # "Speed is halved" states no distance.
        (
            SpeedModificationFact(change=SpeedChange.HALVED, feet=10),
            "halved speed carries a distance",
        ),
        (
            SpeedModificationFact(change=SpeedChange.SET_TO),
            "states no distance",
        ),
        (
            SpeedModificationFact(change=SpeedChange.REDUCED_BY, feet=-5),
            "negative speed distance",
        ),
        # A decreasing damage die is not a form the source states, and admitting
        # it would let an upcasting fact silently invert.
        (
            ScalingFact(
                basis=ScalingBasis.HIGHER_LEVEL_SPELL_SLOT,
                threshold=4,
                effect=ScalingEffect.DAMAGE,
                direction=ScalingDirection.DECREASE,
                dice_amount=DiceExpression(1, DieSize.D10),
            ),
            "decreasing damage scaling is not a form the source states",
        ),
        (
            ScalingFact(
                basis=ScalingBasis.HIGHER_LEVEL_SPELL_SLOT,
                threshold=0,
                effect=ScalingEffect.EFFECTIVE_SPELL_LEVEL,
                direction=ScalingDirection.DECREASE,
            ),
            "effective_spell_level scaling states a direction",
        ),
    ],
)
def test_a_contradictory_or_widening_fact_is_reported(
    fact: object, expected: str
) -> None:
    violations = fact_invariant_violations(fact)
    assert any(expected in v for v in violations), violations


@pytest.mark.parametrize(
    "unknown",
    [
        {"actor": "bystander", "context": "attack_roll", "ability": None},
        {"actor": "subject", "context": "morale_check", "ability": None},
        {"actor": "subject", "context": "saving_throw", "ability": "luck"},
    ],
)
def test_an_unknown_rollspec_member_is_rejected(unknown: dict[str, object]) -> None:
    """A qualifier outside the closed vocabulary is not forward compatibility."""
    payload = fact_payload(RESTRAINED_SAVE) | {"roll": unknown}
    with pytest.raises(MalformedFactPayloadError):
        fact_from_payload(payload)


def test_a_rollspec_replaced_by_a_look_alike_dict_is_rejected() -> None:
    """A dict with the right keys is not a closed value object."""
    fake = replace(
        RESTRAINED_SAVE,
        roll={"actor": "subject", "context": "saving_throw", "ability": "dexterity"},  # type: ignore[arg-type]
    )
    # Reported by the shared value-object seam every sibling uses, so the
    # message is the same one a look-alike DiceExpression or Money would get.
    assert any("must be RollSpec" in v for v in fact_invariant_violations(fake))


def test_an_extra_rollspec_key_is_rejected_not_dropped() -> None:
    payload = fact_payload(RESTRAINED_SAVE)
    payload["roll"]["skill"] = "acrobatics"  # type: ignore[index]
    with pytest.raises(MalformedFactPayloadError):
        fact_from_payload(payload)


def test_exhaustion_scaling_records_its_direction_not_a_sign() -> None:
    """Exhaustion, p181: "the roll is reduced by 2 times your Exhaustion level."

    Recorded declaratively, exactly as ``ScalingFact`` already records the
    upcasting clause. Nothing evaluates it, and no adjustment parameter is
    defined — that contract remains the ADR-015b Known Unknown.
    """
    fact = ScalingFact(
        basis=ScalingBasis.CONDITION_LEVEL,
        threshold=0,
        effect=ScalingEffect.D20_TEST,
        direction=ScalingDirection.DECREASE,
        amount=2,
    )
    assert not fact_invariant_violations(fact)
    assert fact_payload(fact)["direction"] == "decrease"
    # The magnitude stays positive; the direction is not smuggled into a sign.
    assert fact_payload(fact)["amount"] == 2
    assert fact_from_payload(fact_payload(fact)) == fact


def test_the_state_effect_vocabulary_stays_closed() -> None:
    """A state a batch cannot type is unresolved, never a new member."""
    payload = fact_payload(StateEffectFact(StateEffectKind.CONCENTRATION_BROKEN))
    with pytest.raises(MalformedFactPayloadError):
        fact_from_payload(payload | {"effect": "cannot_smell"})


def test_a_speed_modification_is_not_a_creature_speed() -> None:
    """Two different claims that a single family would have conflated.

    ``CreatureSpeedFact`` states what a stat block prints; this states what a
    rule does to whatever Speed the subject has. Using the former for Grappled
    would assert the creature's printed Speed is 0.
    """
    grappled = SpeedModificationFact(
        change=SpeedChange.SET_TO, feet=0, can_increase=False
    )
    assert fact_payload(grappled)["family"] == "speed_modification"
    assert not fact_invariant_violations(grappled)
    # The mode-qualified sibling: "your Fly Speed is reduced to 0".
    flying = replace(grappled, mode=MovementMode.FLY)
    assert fact_key(flying) != fact_key(grappled)


# ---------------------------------------------------------------------------
# Local draft helpers — the smallest valid representation carrying given facts
# ---------------------------------------------------------------------------

RECORD = "condition:under-test"
COMPONENT = "effect"


def _spans(count: int) -> tuple[SemanticSpan, ...]:
    """Exactly *count* substantive spans, all on the same bound leaf.

    Exactly, not generously: a spare substantive span nothing claims is itself a
    validation finding, so an over-supplied ledger would mask the finding each
    test is actually about.
    """
    return tuple(
        SemanticSpan(
            span_id=_span_id(i),
            leaf_id=SPELL_LEAF,
            char_start=i * 2,
            char_end=i * 2 + 2,
            disposition=SemanticDisposition.SUBSTANTIVE,
            review_state=ReviewState.ACCEPTED,
        )
        for i in range(count)
    )


def _span_id(index: int) -> str:
    return derive_span_id(SPELL_LEAF, index * 2, index * 2 + 2)


def _validate(
    facts: tuple[object, ...], *, all_facts_claim_one_span: bool = False
) -> tuple[str, ...]:
    """Validate one record, one component, one primary claim per fact.

    ``all_facts_claim_one_span`` points every fact at the *same* span, which is
    what enumerating a whole vocabulary onto one clause would have to do.
    """
    provenance = tuple(
        ProvenanceClaim(
            ProvenanceTargetKind.FACT,
            fact_target_key(RECORD, COMPONENT, fact),
            _span_id(0 if all_facts_claim_one_span else i),
            ProvenanceRole.PRIMARY,
        )
        for i, fact in enumerate(facts)
    )
    draft = RepresentationDraft(
        records=(RecordDraft(semantic_key=RECORD, kind=RecordKind.CONDITION),),
        components=(
            ComponentDraft(
                record_key=RECORD,
                semantic_key=COMPONENT,
                handling=ComponentHandling.STRUCTURED,
                facts=tuple(facts),  # type: ignore[arg-type]
            ),
        ),
        prose_bindings=(),
        relationships=(),
        references=(),
        provenance=provenance,
    )
    spans = _spans(1 if all_facts_claim_one_span else len(facts))
    return validate_representation(draft, build_ledger(spans), bound_corpus())


# ---------------------------------------------------------------------------
# Semantic vacuity — a variant that claims a change it does not make
# ---------------------------------------------------------------------------
#
# Review round 2 (Codex P2). A fact can satisfy every structural rule its family
# declares and still assert nothing: the discriminator names an operation, and
# the value supplied makes that operation a no-op. Such a fact passes
# representation validation, reaches persisted state, and *satisfies a typed
# family obligation* while carrying authority that changes nothing — which is
# the closed-typed-authority contract failing quietly rather than loudly.
#
# The three below are the concrete holes found by a sweep bounded to the
# families this branch adds or reshapes. ``ScalingFact`` already guarded the
# same shape ("amount 0 changes nothing"), which is what made the class legible.


@pytest.mark.parametrize("threshold", [20, 1, 0, -1, 21])
def test_a_critical_hit_threshold_that_lowers_nothing_is_rejected(
    threshold: int,
) -> None:
    """20 is the ordinary threshold, so lowering *to* 20 lowers nothing.

    The pre-fix bound was the die's face range, which admitted 20 and let the
    fact claim a change it does not make.
    """
    fact = CriticalHitRuleFact(CriticalHitChange.THRESHOLD_LOWERED, threshold=threshold)
    assert fact_invariant_violations(fact)


@pytest.mark.parametrize("threshold", [19, 18, 2])
def test_a_genuinely_lowered_critical_hit_threshold_is_accepted(
    threshold: int,
) -> None:
    """The Champion's "on a roll of 19 or 20" is the boundary case, and passes."""
    fact = CriticalHitRuleFact(CriticalHitChange.THRESHOLD_LOWERED, threshold=threshold)
    assert not fact_invariant_violations(fact)


def test_the_critical_hit_boundary_is_exactly_nineteen_twenty() -> None:
    """Stated as one assertion so the boundary cannot drift unnoticed."""
    lowered = CriticalHitRuleFact(CriticalHitChange.THRESHOLD_LOWERED, threshold=19)
    unchanged = CriticalHitRuleFact(CriticalHitChange.THRESHOLD_LOWERED, threshold=20)
    assert not fact_invariant_violations(lowered)
    assert fact_invariant_violations(unchanged)


def test_a_speed_reduction_of_zero_feet_is_rejected() -> None:
    """A stated reduction of nothing is not a small reduction; it is no rule."""
    assert fact_invariant_violations(
        SpeedModificationFact(change=SpeedChange.REDUCED_BY, feet=0)
    )


def test_setting_speed_to_zero_stays_valid() -> None:
    """The exempt case, and the reason the guard is scoped to REDUCED_BY.

    "Your Speed is 0 and can't increase" is exactly what five conditions state,
    so a zero here is the rule rather than the absence of one.
    """
    assert not fact_invariant_violations(
        SpeedModificationFact(change=SpeedChange.SET_TO, feet=0, can_increase=False)
    )
    assert not fact_invariant_violations(
        SpeedModificationFact(change=SpeedChange.SET_TO, feet=0)
    )


def test_an_all_damage_response_excepting_every_type_is_rejected() -> None:
    """Resistance to all damage except every damage type responds to nothing."""
    every = tuple(sorted(DamageType, key=lambda d: d.value))
    assert fact_invariant_violations(
        DamageResponseFact(
            DamageResponseKind.RESISTANCE, DamageScope.ALL, except_types=every
        )
    )


def test_an_all_damage_response_excepting_all_but_one_stays_valid() -> None:
    """The guard is exhaustion, not "many exceptions"."""
    every = tuple(sorted(DamageType, key=lambda d: d.value))
    assert not fact_invariant_violations(
        DamageResponseFact(
            DamageResponseKind.RESISTANCE, DamageScope.ALL, except_types=every[:-1]
        )
    )


def test_the_exhaustion_guard_is_derived_from_the_closed_vocabulary() -> None:
    """A damage type added later must not leave the guard stale.

    Asserted against ``len(DamageType)`` rather than a written 13, which is what
    the checker itself does.
    """
    every = tuple(sorted(DamageType, key=lambda d: d.value))
    assert len(every) == len(DamageType)
    assert fact_invariant_violations(
        DamageResponseFact(
            DamageResponseKind.IMMUNITY, DamageScope.ALL, except_types=every
        )
    )


def test_scalings_existing_guard_already_closed_this_class() -> None:
    """The sibling that was already safe, kept as the pattern's reference case."""
    assert fact_invariant_violations(
        ScalingFact(
            basis=ScalingBasis.CONDITION_LEVEL,
            threshold=0,
            effect=ScalingEffect.D20_TEST,
            direction=ScalingDirection.DECREASE,
            amount=0,
        )
    )
