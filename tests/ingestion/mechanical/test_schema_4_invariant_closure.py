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

from afterworlds.ingestion.mechanical.models import ComponentHandling
from afterworlds.ingestion.mechanical.representation import (
    AbilityCheckFact,
    AbilityScore,
    Applicability,
    ApplicabilityKind,
    AutomaticOutcome,
    Comparison,
    ComponentDraft,
    ConditionKind,
    ConditionLevelFact,
    ConditionRemovalRestrictionFact,
    ConsumptionBand,
    CreatureChallengeFact,
    CreatureSize,
    DamageFact,
    DamageInterval,
    DamageModDirection,
    DamageModificationFact,
    DamageType,
    DcKind,
    DerivedQuantityFact,
    DiceExpression,
    DieSize,
    DistanceUnit,
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
    _dataclass_payload,
    applicability_violations,
    canonical_bytes,
    component_damage_composition_violations,
    component_roll_outcome_violations,
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
    SCHEMA_5_HASH,
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
    return AbilityCheckFact(**{**base, **overrides}, context=RollContext.ABILITY_CHECK)  # type: ignore[arg-type]


_FALL_INTERVAL = DamageInterval(
    basis=ScalingBasis.DISTANCE_FALLEN, amount=10, unit=DistanceUnit.FOOT
)
#: Falling's closed choice, in canonical order — the alternatives contract
#: refuses an unordered one, which is a different rule's witness.
_FALLING_ALTERNATIVES = tuple(
    sorted(
        (
            RollSpec(
                actor=RollActor.SUBJECT,
                context=RollContext.ABILITY_CHECK,
                ability=AbilityScore.STRENGTH,
                skill=Skill.ATHLETICS,
            ),
            RollSpec(
                actor=RollActor.SUBJECT,
                context=RollContext.ABILITY_CHECK,
                ability=AbilityScore.DEXTERITY,
                skill=Skill.ACROBATICS,
            ),
        ),
        key=lambda r: canonical_bytes(_dataclass_payload(r)),
    )
)


def _component(**kw: object) -> ComponentDraft:
    """A minimal component carrying whatever the row under test is about."""
    return ComponentDraft(
        record_key="hazard.falling",
        semantic_key="probe",
        handling=ComponentHandling.STRUCTURED,
        **kw,  # type: ignore[arg-type]
    )


def _consumption(fraction: Rational) -> Applicability:
    return Applicability(
        kind=ApplicabilityKind.CONSUMPTION_THRESHOLD,
        negated=False,
        band=ConsumptionBand(
            quantity=RequiredQuantity.WATER,
            period=TimePeriod.DAY,
            lower=fraction,
            lower_inclusive=True,
        ),
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
    if isinstance(obj, ComponentDraft):
        # Two component-scoped rules, asked exactly as ``_validate_components``
        # asks them.
        return [
            *component_damage_composition_violations(obj.facts, obj.options, "probe"),
            *component_roll_outcome_violations(
                obj.facts, obj.options, obj.applies_when, "probe", obj.fact_qualifiers
            ),
        ]
    if isinstance(obj, Applicability):
        return applicability_violations(obj)
    if isinstance(obj, Recurrence):
        return recurrence_violations(obj)
    return list(fact_invariant_violations(obj))


# ---------------------------------------------------------------------------
# The executable matrix: one refused exemplar and one admitted control per row
# ---------------------------------------------------------------------------

#: Keyed by the manifest's own invariant **id**, not by ``(locus, field)``: two
#: independent rules can constrain the same field — a scaling threshold's range
#: and a scaling increment's exclusivity both live on ``fact:scaling`` — so a
#: field-keyed table would let one rule's witness stand in for the other's.
CASES: dict[str, tuple[object, object]] = {
    # Shared rational rules — exercised through a fact that does nothing but
    # delegate, so a finding here is the delegation and not a second rule.
    "rational.numerator.not-below-zero": (
        CreatureChallengeFact(challenge_rating=Rational(-1, 2)),
        CreatureChallengeFact(challenge_rating=Rational(1, 2)),
    ),
    "rational.denominator.at-least-one": (
        CreatureChallengeFact(challenge_rating=Rational(1, 0)),
        CreatureChallengeFact(challenge_rating=Rational(1, 4)),
    ),
    # The shared roll shape.
    "roll.skill.governing-ability-agrees": (
        _falling(
            alternatives=_canonical(
                DEX_ACROBATICS, replace(STR_ATHLETICS, skill=Skill.ARCANA)
            )
        ),
        _falling(),
    ),
    # H-1.
    "recurrence.whose.turn-boundary-only": (
        Recurrence(boundary=RecurrenceBoundary.START_OF_TURN, whose=None),
        Recurrence(boundary=RecurrenceBoundary.START_OF_TURN, whose=RollActor.SUBJECT),
    ),
    # H-3.
    "size_keyed_quantity.values.one-row-per-size-in-order": (
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
    # Schema 5, the two component-scoped rules. A component is the smallest
    # thing that can state either, because neither is a property of one fact.
    "component.damage.interval-excludes-damage-scaling": (
        _component(
            facts=(
                DamageFact(
                    damage_type=DamageType.BLUDGEONING,
                    dice=DiceExpression(count=1, die=DieSize.D6),
                    per=_FALL_INTERVAL,
                ),
                ScalingFact(
                    basis=ScalingBasis.CHARACTER_LEVEL,
                    threshold=5,
                    effect=ScalingEffect.DAMAGE,
                    dice_amount=DiceExpression(count=1, die=DieSize.D6),
                ),
            )
        ),
        _component(
            facts=(
                DamageFact(
                    damage_type=DamageType.BLUDGEONING,
                    dice=DiceExpression(count=1, die=DieSize.D6),
                    per=_FALL_INTERVAL,
                ),
            )
        ),
    ),
    "component.roll_outcome.one-established-roll-in-scope": (
        _component(
            facts=(
                DamageModificationFact(
                    direction=DamageModDirection.REDUCE, factor=Rational(1, 2)
                ),
            ),
            applies_when=Applicability(
                kind=ApplicabilityKind.ROLL_OUTCOME,
                outcome=AutomaticOutcome.SUCCESS,
            ),
        ),
        _component(
            facts=(
                AbilityCheckFact(
                    ability=AbilityScore.STRENGTH,
                    dc_kind=DcKind.FIXED,
                    dc_value=15,
                    context=RollContext.ABILITY_CHECK,
                ),
                DamageModificationFact(
                    direction=DamageModDirection.REDUCE, factor=Rational(1, 2)
                ),
            ),
            applies_when=Applicability(
                kind=ApplicabilityKind.ROLL_OUTCOME,
                outcome=AutomaticOutcome.SUCCESS,
            ),
        ),
    ),
    # H-14, and the schema-3 kind whose rule it joined.
    "elapsed_duration.value.not-below-zero": (_elapsed(-5), _elapsed(0)),
    "quantity_threshold.value.not-below-zero": (
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
    "applicability.kind.closed-field-matrix": (
        Applicability(
            kind=ApplicabilityKind.PHASE, negated=False, phase=Phase.ON_END, value=3
        ),
        Applicability(kind=ApplicabilityKind.PHASE, negated=False, phase=Phase.ON_END),
    ),
    # H-5.
    "condition_level.cumulative.accrual-only": (
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
    "condition_removal_restriction.cause_scoped.always": (
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
    # Schema 5. The band's own contract, replacing schema 4's single-sided
    # fraction row: each witness names one share set the band must refuse and
    # one it must admit.
    "consumption_band.bounds.names-a-real-share-set": (
        Applicability(
            kind=ApplicabilityKind.CONSUMPTION_THRESHOLD,
            negated=False,
            band=ConsumptionBand(quantity=RequiredQuantity.FOOD, period=TimePeriod.DAY),
        ),
        Applicability(
            kind=ApplicabilityKind.CONSUMPTION_THRESHOLD,
            negated=False,
            band=ConsumptionBand(
                quantity=RequiredQuantity.FOOD,
                period=TimePeriod.DAY,
                upper=Rational(1, 2),
            ),
        ),
    ),
    "consumption_band.bounds.shared-rational-rules": (
        _consumption(Rational(1, 0)),
        _consumption(Rational(1, 2)),
    ),
    "consumption_band.sustained.amount-and-unit-together": (
        Applicability(
            kind=ApplicabilityKind.CONSUMPTION_THRESHOLD,
            negated=False,
            band=ConsumptionBand(
                quantity=RequiredQuantity.FOOD,
                period=TimePeriod.DAY,
                upper=Rational(1, 2),
                sustained_at_least=5,
            ),
        ),
        Applicability(
            kind=ApplicabilityKind.CONSUMPTION_THRESHOLD,
            negated=False,
            band=ConsumptionBand(
                quantity=RequiredQuantity.FOOD,
                period=TimePeriod.DAY,
                upper=Rational(1, 2),
                sustained_at_least=5,
                sustained_unit=TimeUnit.DAY,
            ),
        ),
    ),
    # Schema 5, requirement 1.
    "ability_check.context.dc-bearing-roll-only": (
        AbilityCheckFact(
            ability=AbilityScore.CONSTITUTION,
            dc_kind=DcKind.FIXED,
            dc_value=10,
            context=RollContext.INITIATIVE,
        ),
        AbilityCheckFact(
            ability=AbilityScore.CONSTITUTION,
            dc_kind=DcKind.FIXED,
            dc_value=10,
            context=RollContext.SAVING_THROW,
        ),
    ),
    "ability_check.context.alternatives-are-checks": (
        AbilityCheckFact(
            ability=AbilityScore.STRENGTH,
            dc_kind=DcKind.FIXED,
            dc_value=15,
            skill=Skill.ATHLETICS,
            context=RollContext.SAVING_THROW,
            alternatives=_FALLING_ALTERNATIVES,
        ),
        AbilityCheckFact(
            ability=AbilityScore.STRENGTH,
            dc_kind=DcKind.FIXED,
            dc_value=15,
            skill=Skill.ATHLETICS,
            context=RollContext.ABILITY_CHECK,
            alternatives=_FALLING_ALTERNATIVES,
        ),
    ),
    # Schema 5, requirement 3.
    "damage.per.repeats-a-dice-expression": (
        DamageFact(
            damage_type=DamageType.BLUDGEONING, flat_amount=3, per=_FALL_INTERVAL
        ),
        DamageFact(
            damage_type=DamageType.BLUDGEONING,
            dice=DiceExpression(count=1, die=DieSize.D6),
            per=_FALL_INTERVAL,
        ),
    ),
    "damage_interval.basis.distance-only": (
        DamageFact(
            damage_type=DamageType.BLUDGEONING,
            dice=DiceExpression(count=1, die=DieSize.D6),
            per=DamageInterval(
                basis=ScalingBasis.CHARACTER_LEVEL, amount=10, unit=DistanceUnit.FOOT
            ),
        ),
        DamageFact(
            damage_type=DamageType.BLUDGEONING,
            dice=DiceExpression(count=1, die=DieSize.D6),
            per=_FALL_INTERVAL,
        ),
    ),
    "scaling.basis.no-distance-fallen": (
        ScalingFact(
            basis=ScalingBasis.DISTANCE_FALLEN,
            threshold=10,
            effect=ScalingEffect.DAMAGE,
            direction=ScalingDirection.INCREASE,
            dice_amount=DiceExpression(count=1, die=DieSize.D6),
        ),
        ScalingFact(
            basis=ScalingBasis.CHARACTER_LEVEL,
            threshold=10,
            effect=ScalingEffect.DAMAGE,
            direction=ScalingDirection.INCREASE,
            dice_amount=DiceExpression(count=1, die=DieSize.D6),
        ),
    ),
    # H-7.
    "scaling.threshold.not-below-zero": (
        ScalingFact(
            basis=ScalingBasis.CHARACTER_LEVEL,
            threshold=-10,
            effect=ScalingEffect.DAMAGE,
            direction=ScalingDirection.INCREASE,
            dice_amount=DiceExpression(count=1, die=DieSize.D6),
        ),
        ScalingFact(
            basis=ScalingBasis.CHARACTER_LEVEL,
            threshold=10,
            effect=ScalingEffect.DAMAGE,
            direction=ScalingDirection.INCREASE,
            dice_amount=DiceExpression(count=1, die=DieSize.D6),
        ),
    ),
    # H-7 again: the rule that makes Falling's "1d6 for every 10 feet" an
    # increment at all. Its own witness rather than the threshold rule's,
    # because two independent rules live on this family.
    "scaling.increment.exactly-one": (
        ScalingFact(
            basis=ScalingBasis.CHARACTER_LEVEL,
            threshold=10,
            effect=ScalingEffect.DAMAGE,
            direction=ScalingDirection.INCREASE,
            dice_amount=DiceExpression(count=1, die=DieSize.D6),
            amount=2,
        ),
        ScalingFact(
            basis=ScalingBasis.CHARACTER_LEVEL,
            threshold=10,
            effect=ScalingEffect.DAMAGE,
            direction=ScalingDirection.INCREASE,
            dice_amount=DiceExpression(count=1, die=DieSize.D6),
        ),
    ),
    # H-9.
    "damage.maximum_dice.caps-a-stated-expression": (
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
    "ability_check.alternatives.complete-closed-choice": (
        _falling(alternatives=_canonical(STR_ATHLETICS, DEX_ACROBATICS)[:1] * 2),
        _falling(),
    ),
    # H-13.
    "damage_modification.factor.positive-and-not-one": (
        DamageModificationFact(
            direction=DamageModDirection.REDUCE, factor=Rational(0, 1)
        ),
        DamageModificationFact(
            direction=DamageModDirection.REDUCE, factor=Rational(1, 2)
        ),
    ),
    # H-15.
    "derived_quantity.floor.amount-and-unit-together": (
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
    """What this proves, and — precisely — what it does not.

    It proves every declared row is exercised in both directions, and that no
    witness exists for a row nobody declared. That is a real property: a
    declaration nothing demonstrates fails here rather than standing as prose,
    and it is the same guard ``introduction_manifest`` carries.

    It **cannot** prove no declaration was omitted. Nothing inside a set equality
    between a manifest and a table written against it could: both halves are
    written by the same hand, and an invariant left out of both is invisible to
    it. Round 7 is the demonstration — the scaling increment rule was enforced,
    settled, and absent from both, and this test passed.

    Completeness comes from the bounded authority-to-manifest reconciliation
    recorded in ``.claude/review-notes/pr-159-issue-5d-remediation-log.md``:
    every schema-4 addition's settled invariants read off the hazards-1 closure
    authority, and for an addition that joined an existing validator, that
    validator's branches enumerated one at a time and each classified. This test
    holds the result honest; it does not derive it.
    """
    declared = {row["id"] for row in invariant_manifest()}
    assert declared == set(CASES), {
        "declared without coverage": sorted(declared - set(CASES)),
        "covered without declaration": sorted(set(CASES) - declared),
    }


@pytest.mark.parametrize("invariant_id", sorted(CASES))
def test_each_declared_invariant_refuses_and_admits(invariant_id: str) -> None:
    """Both directions, because a rule that refuses everything is not a rule."""
    bad, good = CASES[invariant_id]
    assert _findings(bad), f"{invariant_id}: the violating exemplar was admitted"
    assert _findings(good) == [], f"{invariant_id}: the control was refused"


def test_the_invariant_contract_is_carried_inside_the_schema_identity() -> None:
    """Declared where it can be checked, and where weakening it costs something."""
    assert representation_schema_payload()["invariants"] == invariant_manifest()


def test_no_python_name_reaches_the_invariant_declaration() -> None:
    """Serialized identifiers only.

    A nested value object carries no type tag on the wire, so it is identified
    by its own sorted field set — the same answer this module already gives for
    a vocabulary, which it identifies by its admitted values.

    ``component`` joins the prefixes at schema 5. It is a serialized identifier
    like the others: ``components`` is a collection the payload carries, and the
    two rules declared against it are properties of a whole component rather
    than of any one fact in it. No Python name appears in it either.
    """
    for row in invariant_manifest():
        locus = row["locus"]
        assert locus.startswith(
            ("fact:", "applicability", "shape:", "component")
        ), locus
        assert locus == locus.lower(), locus
        assert row["id"] == row["id"].lower(), row["id"]


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
    assert representation_schema_hash() == SCHEMA_5_HASH


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
        context=RollContext.ABILITY_CHECK,
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
