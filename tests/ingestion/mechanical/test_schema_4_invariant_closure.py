"""The schema-4 intrinsic invariant contract, closed and identity-bound — CRD Issue 5d.

Five review rounds found the same shape of defect: a schema-4 value whose fields
were present and individually typed, and whose *intrinsic* rule — a range, a
paired field, a reconciliation with the value that carries it — was never
written. ``Rational(1, 0)`` satisfied a fraction, a negative integer satisfied an
elapsed duration, and a closed choice of rolls was checked without ever being
compared to the fact offering it.

Two things close that class rather than its instances.

**One declaration.** ``invariant_manifest()`` states the intrinsic contract in
serialized terms and is emitted by ``representation_schema_payload()``, so the
schema hash covers it: weakening a rule moves the hash, the destination pin in
``schema_lift`` stops matching, and ``lift_for`` refuses the transition. The
Owner's requirement is that schema identity describe the complete serialized
grammar, and which combinations of fields mean anything is part of a grammar.

**One executable matrix.** Every declared row is exercised here by an object the
shared validator refuses and one it admits. A row nothing demonstrates fails
``test_every_declared_invariant_is_executable``, so the manifest cannot become
decorative prose — which is the only way a declaration like this rots.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from afterworlds.ingestion.mechanical.representation import (
    AbilityCheckFact,
    AbilityScore,
    Applicability,
    ApplicabilityKind,
    Comparison,
    ConditionKind,
    ConditionLevelFact,
    ConditionRemovalRestrictionFact,
    CreatureChallengeFact,
    CreatureSize,
    DamageFact,
    DamageModDirection,
    DamageModificationFact,
    DamageType,
    DcKind,
    DerivedQuantityFact,
    DiceExpression,
    DieSize,
    LevelDirection,
    MeasureUnit,
    Phase,
    Rational,
    Recurrence,
    RecurrenceBoundary,
    RequiredQuantity,
    RollActor,
    RollContext,
    RollSpec,
    ScalingBasis,
    ScalingDirection,
    ScalingEffect,
    ScalingFact,
    SizeKeyedQuantityFact,
    SizeQuantity,
    Skill,
    TimePeriod,
    TimeUnit,
    TrackedQuantity,
    applicability_violations,
    canonical_bytes,
    fact_invariant_violations,
    fact_payload,
    held_structure_violations,
    invariant_manifest,
    recurrence_violations,
    representation_schema_hash,
    representation_schema_payload,
)
from afterworlds.ingestion.mechanical.schema_lift import (
    SCHEMA_3_HASH,
    SCHEMA_3_VERSION,
    SCHEMA_4_HASH,
    SCHEMA_4_VERSION,
    UnknownSchemaLiftError,
    lift_for,
    schema_binding_violations,
)
from afterworlds.services.rules_authority.patches import InvalidPatchError
from afterworlds.services.rules_authority.patches import _build_fact as build_fact_patch

# ---------------------------------------------------------------------------
# The rolls Falling actually prints, and the shapes around them
# ---------------------------------------------------------------------------

DEX_ACROBATICS = RollSpec(
    actor=RollActor.SUBJECT,
    context=RollContext.ABILITY_CHECK,
    ability=AbilityScore.DEXTERITY,
    skill=Skill.ACROBATICS,
)
STR_ATHLETICS = RollSpec(
    actor=RollActor.SUBJECT,
    context=RollContext.ABILITY_CHECK,
    ability=AbilityScore.STRENGTH,
    skill=Skill.ATHLETICS,
)


def _canonical(*rolls: RollSpec) -> tuple[RollSpec, ...]:
    """Canonical order, derived rather than hand-sorted.

    The invariant requires it, so writing the order out here by hand would let a
    test pass by agreeing with itself about what canonical means.
    """
    return tuple(sorted(rolls, key=lambda r: canonical_bytes(_payload_of(r))))


def _payload_of(roll: RollSpec) -> dict[str, object]:
    from afterworlds.ingestion.mechanical.representation import _dataclass_payload

    return _dataclass_payload(roll)


def _falling(**overrides: object) -> AbilityCheckFact:
    """*"a DC 15 Strength (Athletics) or Dexterity (Acrobatics) check"* — real."""
    base: dict[str, object] = {
        "ability": AbilityScore.DEXTERITY,
        "dc_kind": DcKind.FIXED,
        "dc_value": 15,
        "skill": Skill.ACROBATICS,
        "alternatives": _canonical(DEX_ACROBATICS, STR_ATHLETICS),
    }
    return AbilityCheckFact(**{**base, **overrides})  # type: ignore[arg-type]


def _consumption(fraction: Rational) -> Applicability:
    return Applicability(
        kind=ApplicabilityKind.CONSUMPTION_THRESHOLD,
        negated=False,
        comparison=Comparison.REACHES,
        required_quantity=RequiredQuantity.WATER,
        fraction=fraction,
    )


def _elapsed(value: int) -> Applicability:
    return Applicability(
        kind=ApplicabilityKind.ELAPSED_DURATION,
        negated=False,
        value=value,
        unit=TimeUnit.MINUTE,
    )


def _findings(obj: object) -> list[str]:
    """The validator that owns *obj*, chosen by what it is.

    Deliberately a dispatch over three shared validators rather than a per-case
    callable: every row below must be enforced by a validator the production
    paths already call, and routing through anything else would prove a rule
    nothing else runs.
    """
    if isinstance(obj, Applicability):
        return applicability_violations(obj)
    if isinstance(obj, Recurrence):
        return recurrence_violations(obj)
    return list(fact_invariant_violations(obj))


# ---------------------------------------------------------------------------
# The executable matrix: one refused exemplar and one admitted control per row
# ---------------------------------------------------------------------------

CASES: dict[tuple[str, str], tuple[object, object]] = {
    # Shared rational rules — exercised through a fact that does nothing but
    # delegate, so a finding here is the delegation and not a second rule.
    ("shape:denominator+numerator", "numerator"): (
        CreatureChallengeFact(challenge_rating=Rational(-1, 2)),
        CreatureChallengeFact(challenge_rating=Rational(1, 2)),
    ),
    ("shape:denominator+numerator", "denominator"): (
        CreatureChallengeFact(challenge_rating=Rational(1, 0)),
        CreatureChallengeFact(challenge_rating=Rational(1, 4)),
    ),
    # The shared roll shape.
    ("shape:ability+actor+context+skill", "skill"): (
        _falling(
            alternatives=_canonical(
                DEX_ACROBATICS, replace(STR_ATHLETICS, skill=Skill.ARCANA)
            )
        ),
        _falling(),
    ),
    # H-1.
    ("shape:boundary+whose", "whose"): (
        Recurrence(boundary=RecurrenceBoundary.START_OF_TURN, whose=None),
        Recurrence(boundary=RecurrenceBoundary.START_OF_TURN, whose=RollActor.SUBJECT),
    ),
    # H-3.
    ("fact:size_keyed_quantity", "values"): (
        SizeKeyedQuantityFact(
            quantity=RequiredQuantity.FOOD,
            period=TimePeriod.DAY,
            values=(
                SizeQuantity(
                    size=CreatureSize.MEDIUM,
                    amount=Rational(1, 1),
                    unit=MeasureUnit.POUND,
                ),
                SizeQuantity(
                    size=CreatureSize.MEDIUM,
                    amount=Rational(2, 1),
                    unit=MeasureUnit.POUND,
                ),
            ),
        ),
        SizeKeyedQuantityFact(
            quantity=RequiredQuantity.FOOD,
            period=TimePeriod.DAY,
            values=(
                SizeQuantity(
                    size=CreatureSize.MEDIUM,
                    amount=Rational(1, 1),
                    unit=MeasureUnit.POUND,
                ),
            ),
        ),
    ),
    # H-4, and the delegation round 5 corrected.
    ("applicability:consumption_threshold", "fraction"): (
        _consumption(Rational(1, 0)),
        _consumption(Rational(1, 2)),
    ),
    # H-14, and the schema-3 kind whose rule it joined.
    ("applicability:elapsed_duration", "value"): (_elapsed(-5), _elapsed(0)),
    ("applicability:quantity_threshold", "value"): (
        Applicability(
            kind=ApplicabilityKind.QUANTITY_THRESHOLD,
            negated=False,
            quantity=TrackedQuantity.CONDITION_LEVEL,
            comparison=Comparison.REACHES,
            value=-1,
        ),
        Applicability(
            kind=ApplicabilityKind.QUANTITY_THRESHOLD,
            negated=False,
            quantity=TrackedQuantity.CONDITION_LEVEL,
            comparison=Comparison.REACHES,
            value=0,
        ),
    ),
    # H-10 and H-12 joined this one rather than adding rules of their own.
    ("applicability", "kind"): (
        Applicability(
            kind=ApplicabilityKind.PHASE, negated=False, phase=Phase.ON_END, value=3
        ),
        Applicability(kind=ApplicabilityKind.PHASE, negated=False, phase=Phase.ON_END),
    ),
    # H-5.
    ("fact:condition_level", "cumulative"): (
        ConditionLevelFact(
            condition=ConditionKind.EXHAUSTION,
            direction=LevelDirection.REMOVE,
            amount=1,
            cumulative=True,
        ),
        ConditionLevelFact(
            condition=ConditionKind.EXHAUSTION,
            direction=LevelDirection.GAIN,
            amount=1,
            cumulative=True,
        ),
    ),
    # H-6.
    ("fact:condition_removal_restriction", "cause_scoped"): (
        ConditionRemovalRestrictionFact(
            condition=ConditionKind.EXHAUSTION,
            cause_scoped=False,
            until=_consumption(Rational(1, 2)),
        ),
        ConditionRemovalRestrictionFact(
            condition=ConditionKind.EXHAUSTION,
            cause_scoped=True,
            until=_consumption(Rational(1, 2)),
        ),
    ),
    # H-7.
    ("fact:scaling", "threshold"): (
        ScalingFact(
            basis=ScalingBasis.DISTANCE_FALLEN,
            threshold=-10,
            effect=ScalingEffect.DAMAGE,
            direction=ScalingDirection.INCREASE,
            dice_amount=DiceExpression(count=1, die=DieSize.D6),
        ),
        ScalingFact(
            basis=ScalingBasis.DISTANCE_FALLEN,
            threshold=10,
            effect=ScalingEffect.DAMAGE,
            direction=ScalingDirection.INCREASE,
            dice_amount=DiceExpression(count=1, die=DieSize.D6),
        ),
    ),
    # H-9.
    ("fact:damage", "maximum_dice"): (
        DamageFact(
            damage_type=DamageType.BLUDGEONING,
            dice=DiceExpression(count=20, die=DieSize.D6),
            maximum_dice=10,
        ),
        DamageFact(
            damage_type=DamageType.BLUDGEONING,
            dice=DiceExpression(count=1, die=DieSize.D6),
            maximum_dice=20,
        ),
    ),
    # H-11.
    ("fact:ability_check", "alternatives"): (
        _falling(alternatives=_canonical(STR_ATHLETICS, DEX_ACROBATICS)[:1] * 2),
        _falling(),
    ),
    # H-13.
    ("fact:damage_modification", "factor"): (
        DamageModificationFact(
            direction=DamageModDirection.REDUCE, factor=Rational(0, 1)
        ),
        DamageModificationFact(
            direction=DamageModDirection.REDUCE, factor=Rational(1, 2)
        ),
    ),
    # H-15.
    ("fact:derived_quantity", "floor_amount"): (
        DerivedQuantityFact(
            base=1,
            modifier=AbilityScore.CONSTITUTION,
            unit=TimeUnit.MINUTE,
            floor_amount=30,
        ),
        DerivedQuantityFact(
            base=1,
            modifier=AbilityScore.CONSTITUTION,
            unit=TimeUnit.MINUTE,
            floor_amount=30,
            floor_unit=TimeUnit.SECOND,
        ),
    ),
}


def test_every_declared_invariant_is_executable() -> None:
    """The link that stops the manifest from becoming prose.

    A declaration nothing demonstrates is a claim about a rule that may not
    exist. This is the same guard ``introduction_manifest`` carries, for the same
    reason: a schema-5 addition that lands a row without coverage fails here
    rather than being trusted.
    """
    declared = {(row["locus"], row["field"]) for row in invariant_manifest()}
    assert declared == set(CASES), {
        "declared without coverage": sorted(declared - set(CASES)),
        "covered without declaration": sorted(set(CASES) - declared),
    }


@pytest.mark.parametrize("key", sorted(CASES), ids=lambda k: f"{k[0]}/{k[1]}")
def test_each_declared_invariant_refuses_and_admits(key: tuple[str, str]) -> None:
    """Both directions, because a rule that refuses everything is not a rule."""
    bad, good = CASES[key]
    assert _findings(bad), f"{key}: the violating exemplar was admitted"
    assert _findings(good) == [], f"{key}: the control was refused"


def test_the_invariant_contract_is_carried_inside_the_schema_identity() -> None:
    """Declared where it can be checked, and where weakening it costs something."""
    assert representation_schema_payload()["invariants"] == invariant_manifest()


def test_no_python_name_reaches_the_invariant_declaration() -> None:
    """Serialized identifiers only.

    A nested value object carries no type tag on the wire, so it is identified
    by its own sorted field set — the same answer this module already gives for
    a vocabulary, which it identifies by its admitted values.
    """
    for row in invariant_manifest():
        locus = row["locus"]
        assert locus.startswith(("fact:", "applicability", "shape:")), locus
        assert locus == locus.lower(), locus


def test_weakening_an_invariant_declaration_breaks_the_registered_lift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The consequence that makes the declaration load-bearing.

    Dropping a row is what "loosening the contract" looks like from the outside.
    It moves the hash, so the destination pin no longer describes this build, and
    the registered succession refuses to run — the same failure mode that
    protects the introduction manifest.
    """
    from afterworlds.ingestion.mechanical import representation

    kept = representation._INVARIANTS
    monkeypatch.setattr(representation, "_INVARIANTS", kept[1:])
    weakened = representation_schema_hash()

    assert weakened != SCHEMA_4_HASH
    with pytest.raises(UnknownSchemaLiftError):
        lift_for((SCHEMA_3_VERSION, SCHEMA_3_HASH), (SCHEMA_4_VERSION, weakened))


def test_the_registered_lift_still_reaches_the_finalized_destination() -> None:
    """And the other direction: the real pin resolves, and the source is unmoved."""
    lift = lift_for(
        (SCHEMA_3_VERSION, SCHEMA_3_HASH), (SCHEMA_4_VERSION, SCHEMA_4_HASH)
    )
    assert lift.lift_id == "5d-lift-schema-3-to-4"
    assert SCHEMA_3_HASH == (
        "43ed330d3b3630d37ed92122fd87cc2c170863bab4465e53c727f1b8c6b86e05"  # noqa: E501  # pragma: allowlist secret
    )
    assert representation_schema_hash() == SCHEMA_4_HASH


# ---------------------------------------------------------------------------
# R6-1 and R6-2, stated directly rather than only through the matrix
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("value", [-1, -5, -1000])
def test_a_negative_elapsed_duration_is_refused(value: int) -> None:
    """No time has elapsed is a state; negative time is not one."""
    findings = applicability_violations(_elapsed(value))
    assert any("not a count" in f for f in findings), findings


@pytest.mark.parametrize("value", [0, 1, 6, 3600])
def test_zero_and_positive_durations_are_admitted(value: int) -> None:
    """Zero is preserved deliberately.

    Nothing in the governing contract asks for a positive bound, and silently
    turning "not below zero" into "above zero" would refuse a real state — the
    boundary the rule is written on is exactly the one the source states.
    """
    assert applicability_violations(_elapsed(value)) == []


def test_the_real_falling_shape_is_admitted() -> None:
    """The over-refusal control that matters most: the rule this family exists for."""
    assert fact_invariant_violations(_falling()) == ()


def test_empty_alternatives_stay_an_ordinary_ability_check() -> None:
    """No choice offered, so the fact's own pair is the whole claim."""
    plain = AbilityCheckFact(
        ability=AbilityScore.DEXTERITY,
        dc_kind=DcKind.FIXED,
        dc_value=15,
        skill=Skill.ACROBATICS,
    )
    assert plain.alternatives == ()
    assert fact_invariant_violations(plain) == ()


@pytest.mark.parametrize(
    "context",
    [RollContext.SAVING_THROW, RollContext.ATTACK_ROLL, RollContext.D20_TEST],
    ids=lambda c: c.value,
)
def test_a_member_rolled_in_another_context_is_refused(context: RollContext) -> None:
    """One DC does not govern two kinds of roll."""
    other = RollSpec(
        actor=RollActor.SUBJECT,
        context=context,
        ability=AbilityScore.STRENGTH,
    )
    findings = fact_invariant_violations(
        _falling(alternatives=_canonical(DEX_ACROBATICS, other))
    )
    assert any(context.value in f for f in findings), findings


def test_a_closed_choice_omitting_the_facts_own_pair_is_refused() -> None:
    """The set is the complete choice, so the fact's own roll has to be in it."""
    elsewhere = RollSpec(
        actor=RollActor.SUBJECT,
        context=RollContext.ABILITY_CHECK,
        ability=AbilityScore.WISDOM,
        skill=Skill.PERCEPTION,
    )
    findings = fact_invariant_violations(
        _falling(alternatives=_canonical(STR_ATHLETICS, elsewhere))
    )
    assert any("no member states" in f for f in findings), findings


def test_the_declared_pair_named_twice_is_refused() -> None:
    """Two distinct RollSpecs, one repeated claim.

    Payload uniqueness cannot see this: the two members differ in ``actor``, so
    they are distinct rolls that name the same ability and skill. Only comparing
    the set against the fact catches it.
    """
    same_pair_other_actor = replace(DEX_ACROBATICS, actor=RollActor.AGAINST_SUBJECT)
    findings = fact_invariant_violations(
        _falling(alternatives=_canonical(DEX_ACROBATICS, same_pair_other_actor))
    )
    assert any("2 members state" in f for f in findings), findings


def test_a_single_alternative_and_a_repeated_roll_are_still_refused() -> None:
    """The rules that were already there, kept while the new ones landed."""
    assert fact_invariant_violations(_falling(alternatives=(DEX_ACROBATICS,)))
    assert fact_invariant_violations(
        _falling(alternatives=(DEX_ACROBATICS, DEX_ACROBATICS))
    )


def test_authoring_order_still_cannot_reach_the_fact_key() -> None:
    """Canonical order, unchanged by the reconciliation rules added beside it."""
    reversed_order = tuple(reversed(_canonical(DEX_ACROBATICS, STR_ATHLETICS)))
    assert fact_invariant_violations(_falling(alternatives=reversed_order))


# ---------------------------------------------------------------------------
# The paths a bad fact travels, each returning what its own callers handle
# ---------------------------------------------------------------------------


def _bad_alternatives() -> AbilityCheckFact:
    """A closed choice that omits the pair the fact itself declares."""
    elsewhere = RollSpec(
        actor=RollActor.SUBJECT,
        context=RollContext.ABILITY_CHECK,
        ability=AbilityScore.WISDOM,
        skill=Skill.PERCEPTION,
    )
    return _falling(alternatives=_canonical(STR_ATHLETICS, elsewhere))


def test_the_shared_draft_validator_carries_it_to_every_authority_seam() -> None:
    """Loader, acceptance, verified lift and publication share one reader.

    ``held_structure_violations`` walks every fact and applicability a draft
    holds and reports what each family's own validator says. Round 4 wired it
    into ``schema_binding_violations``, so a fact whose intrinsic invariant fails
    is refused at committed-artifact loading, at acceptance for both halves,
    inside ``verify_lift``, and at publication — from this one call.
    """
    from tests.ingestion.mechanical.conftest import build_representation

    draft = build_representation()
    tampered = replace(
        draft,
        components=(
            replace(draft.components[0], facts=(_bad_alternatives(),)),
            *draft.components[1:],
        ),
    )
    assert held_structure_violations(draft) == []
    findings = held_structure_violations(tampered)
    assert any("alternatives is the complete choice" in f for f in findings), findings
    assert schema_binding_violations(
        tampered, (SCHEMA_4_VERSION, SCHEMA_4_HASH)
    ), "the binding invariant must carry the family finding"


def test_the_override_patch_builder_refuses_it_in_its_own_words() -> None:
    """The fifth path, which has its own typed failure and its own caller."""
    with pytest.raises(InvalidPatchError):
        build_fact_patch(fact_payload(_bad_alternatives()), "what")


def test_the_override_patch_builder_still_admits_the_real_shape() -> None:
    """The over-refusal control on that path."""
    assert build_fact_patch(fact_payload(_falling()), "what") == _falling()
