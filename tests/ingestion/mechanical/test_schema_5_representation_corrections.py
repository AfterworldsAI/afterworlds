"""CRD Issue 5d — representation schema 5, the three corrections and their succession.

The defect family, stated once: **mechanically distinct source meanings collapse
or disappear because their qualifiers or composition are not present in canonical
typed authority.** Schema 4 admitted three instances of it, and each is closed
here by a narrow typed structure rather than by a predicate language:

* a DC source stated no roll context, so a DC 10 Constitution *saving throw* and
  a DC 10 Constitution *ability check* hashed alike;
* a consumption threshold stated one side of a requirement, so *"eats but
  consumes less than half"* and *"eats nothing"* hashed alike; and
* a distance-scaled damage was a :class:`DamageFact` beside a
  :class:`ScalingFact`, which has two readings and therefore two answers.

Every test here is about the *grammar*: what the schema admits, what it refuses,
and what a succession must preserve. Nothing accepts, publishes, or activates.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from afterworlds.ingestion.corpus.hashing import canonical_bytes
from afterworlds.ingestion.mechanical.models import ComponentHandling
from afterworlds.ingestion.mechanical.oracle import (
    AcceptedInputs,
    load_accepted_inputs,
    oracle_identity,
)
from afterworlds.ingestion.mechanical.projection import representation_payload
from afterworlds.ingestion.mechanical.representation import (
    REPRESENTATION_SCHEMA_VERSION,
    AbilityCheckFact,
    AbilityScore,
    Applicability,
    ApplicabilityKind,
    AttackKind,
    AttackRollFact,
    AutomaticOutcome,
    ComponentDraft,
    ComponentOption,
    ConsumptionBand,
    DamageFact,
    DamageInterval,
    DamageModDirection,
    DamageModificationFact,
    DamageType,
    DcKind,
    DiceExpression,
    DieSize,
    DistanceUnit,
    FactQualifier,
    Rational,
    RequiredQuantity,
    RollActor,
    RollContext,
    RollSpec,
    ScalingBasis,
    ScalingDirection,
    ScalingEffect,
    ScalingFact,
    Skill,
    TimePeriod,
    TimeUnit,
    applicability_violations,
    component_damage_composition_violations,
    component_roll_outcome_violations,
    declared_meaning_violations,
    fact_from_payload,
    fact_invariant_violations,
    fact_key,
    fact_payload,
    representation_schema_hash,
)
from afterworlds.ingestion.mechanical.schema_lift import (
    SCHEMA_3_HASH,
    SCHEMA_3_VERSION,
    SCHEMA_4_HASH,
    SCHEMA_4_VERSION,
    SCHEMA_5_HASH,
    SCHEMA_5_VERSION,
    UnknownSchemaLiftError,
    lift_accepted_inputs,
    lift_path,
)

ACCEPTED = (
    Path(__file__).resolve().parents[3]
    / "src/afterworlds/ingestion/mechanical/oracles"
    / "srd-5-2-1-corpus-36b786d8-fa2.json"
)
D6 = DiceExpression(count=1, die=DieSize.D6)


# ---------------------------------------------------------------------------
# Requirement 1 — the roll a DC source states
# ---------------------------------------------------------------------------


def _dc10(context: RollContext) -> AbilityCheckFact:
    """Malnutrition's roll, spelled both ways. Identical but for the context."""
    return AbilityCheckFact(
        ability=AbilityScore.CONSTITUTION,
        dc_kind=DcKind.FIXED,
        dc_value=10,
        context=context,
    )


def test_identical_ability_and_dc_under_check_versus_save_are_distinct() -> None:
    """The collapse schema 5 exists to close, asserted in both currencies.

    Same ability, same DC kind, same DC value. Under schema 4 these were one
    payload and one fact key, so a consumer reading the typed surface could not
    tell a saving throw from an ability check.
    """
    save, check = _dc10(RollContext.SAVING_THROW), _dc10(RollContext.ABILITY_CHECK)
    assert save != check
    assert fact_payload(save) != fact_payload(check)
    assert fact_key(save) != fact_key(check)
    assert fact_payload(save)["context"] == "saving_throw"
    assert fact_payload(check)["context"] == "ability_check"
    assert fact_invariant_violations(save) == ()
    assert fact_invariant_violations(check) == ()


def test_the_context_is_never_omitted_from_the_canonical_payload() -> None:
    """Required, so both spellings cost a key and neither is the free default.

    A defaulted context would omit one of the two under the post-schema-3
    omission rule, and the omitted form would hash exactly as the stated form —
    re-creating the collapse inside the mechanism meant to preserve identity.
    """
    for context in (RollContext.ABILITY_CHECK, RollContext.SAVING_THROW):
        assert "context" in fact_payload(_dc10(context))


def test_the_context_is_keyword_only() -> None:
    """It cannot displace a positional argument, so no call site binds it by luck."""
    with pytest.raises(TypeError):
        AbilityCheckFact(  # type: ignore[misc]
            AbilityScore.CONSTITUTION, DcKind.FIXED, RollContext.SAVING_THROW
        )


@pytest.mark.parametrize(
    "context",
    [RollContext.ATTACK_ROLL, RollContext.INITIATIVE, RollContext.D20_TEST],
)
def test_a_context_that_names_no_dc_bearing_roll_fails_closed(
    context: RollContext,
) -> None:
    """An attack roll has no DC source, and neither Initiative nor the umbrella
    names one roll a difficulty could be stated for."""
    violations = fact_invariant_violations(_dc10(context))
    assert any("ability check or a saving throw" in v for v in violations)


def test_an_undeclared_context_fails_closed() -> None:
    """A string that looks like a member is not one."""
    fact = AbilityCheckFact(
        ability=AbilityScore.CONSTITUTION,
        dc_kind=DcKind.FIXED,
        dc_value=10,
        context="saving_throw",  # type: ignore[arg-type]
    )
    assert any(
        "context must be RollContext" in v for v in fact_invariant_violations(fact)
    )


def _falling_alternatives() -> tuple[RollSpec, ...]:
    """Falling's *"Strength (Athletics) or Dexterity (Acrobatics)"*, canonical."""
    rolls = (
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
    )
    from afterworlds.ingestion.mechanical.representation import _dataclass_payload

    return tuple(sorted(rolls, key=lambda r: canonical_bytes(_dataclass_payload(r))))


def _surface_check(context: RollContext) -> AbilityCheckFact:
    return AbilityCheckFact(
        ability=AbilityScore.STRENGTH,
        dc_kind=DcKind.FIXED,
        dc_value=15,
        skill=Skill.ATHLETICS,
        alternatives=_falling_alternatives(),
        context=context,
    )


def test_fallings_alternatives_stay_an_ability_check() -> None:
    """The brief's own case: the choice Falling offers is a choice of checks."""
    fact = _surface_check(RollContext.ABILITY_CHECK)
    assert fact_invariant_violations(fact) == ()
    assert len(fact.alternatives) == 2
    assert {a.skill for a in fact.alternatives} == {Skill.ATHLETICS, Skill.ACROBATICS}


def test_a_saving_throw_offering_alternative_checks_fails_closed() -> None:
    """Mixed-context alternation, with the halves swapped.

    ``_check_alternatives`` already refuses a *member* rolled as anything but a
    check. This is the same rule for the fact offering them: one DC does not
    govern two kinds of roll.
    """
    violations = fact_invariant_violations(_surface_check(RollContext.SAVING_THROW))
    assert any("does not govern two kinds of roll" in v for v in violations)


def test_an_alternative_rolled_as_a_save_still_fails_closed() -> None:
    """The pre-existing half of the rule is not weakened by the new one."""
    fact = AbilityCheckFact(
        ability=AbilityScore.STRENGTH,
        dc_kind=DcKind.FIXED,
        dc_value=15,
        skill=Skill.ATHLETICS,
        context=RollContext.ABILITY_CHECK,
        alternatives=(
            RollSpec(
                actor=RollActor.SUBJECT,
                context=RollContext.ABILITY_CHECK,
                ability=AbilityScore.STRENGTH,
                skill=Skill.ATHLETICS,
            ),
            RollSpec(
                actor=RollActor.SUBJECT,
                context=RollContext.SAVING_THROW,
                ability=AbilityScore.DEXTERITY,
            ),
        ),
    )
    assert any("rolled as saving_throw" in v for v in fact_invariant_violations(fact))


def test_both_contexts_round_trip_through_the_wire() -> None:
    """Persistence, committed loading and override targeting all use this seam."""
    for context in (RollContext.ABILITY_CHECK, RollContext.SAVING_THROW):
        fact = _dc10(context)
        assert fact_from_payload(fact_payload(fact)) == fact


def test_a_payload_missing_the_context_is_refused_rather_than_defaulted() -> None:
    """A truncated payload is not silently completed at the new axis."""
    payload = dict(fact_payload(_dc10(RollContext.SAVING_THROW)))
    del payload["context"]
    with pytest.raises(Exception, match="missing"):
        fact_from_payload(payload)


# ---------------------------------------------------------------------------
# Requirement 2 — Malnutrition's consumption semantics
# ---------------------------------------------------------------------------


def _band(**kw: object) -> Applicability:
    return Applicability(
        kind=ApplicabilityKind.CONSUMPTION_THRESHOLD,
        band=ConsumptionBand(
            quantity=RequiredQuantity.FOOD, period=TimePeriod.DAY, **kw  # type: ignore[arg-type]
        ),
    )


#: The four distinctions the brief requires, plus the two neighbours they must
#: not collapse into: Dehydration's unbounded-below threshold, and the full
#: amount a removal restriction waits for.
BANDS: dict[str, Applicability] = {
    "partial: 0 < x < 1/2": _band(lower=Rational(0, 1), upper=Rational(1, 2)),
    "none: x == 0": _band(
        lower=Rational(0, 1),
        lower_inclusive=True,
        upper=Rational(0, 1),
        upper_inclusive=True,
    ),
    "none, sustained 5 days": _band(
        lower=Rational(0, 1),
        lower_inclusive=True,
        upper=Rational(0, 1),
        upper_inclusive=True,
        sustained_at_least=5,
        sustained_unit=TimeUnit.DAY,
    ),
    "none, sustained 6 days": _band(
        lower=Rational(0, 1),
        lower_inclusive=True,
        upper=Rational(0, 1),
        upper_inclusive=True,
        sustained_at_least=6,
        sustained_unit=TimeUnit.DAY,
    ),
    "dehydration: x < 1/2, no lower": _band(upper=Rational(1, 2)),
    "full amount: x >= 1": _band(lower=Rational(1, 1), lower_inclusive=True),
}


@pytest.mark.parametrize("name", sorted(BANDS))
def test_each_stated_consumption_form_is_admitted(name: str) -> None:
    assert applicability_violations(BANDS[name]) == []


def test_every_consumption_form_has_its_own_canonical_payload() -> None:
    """The distinctions are real on the wire, not only in the constructor.

    ``partial`` versus ``none`` is the pair schema 4 collapsed: both reduced to
    ``< 1/2`` because a single comparison could state only one side. ``none``
    versus ``none, sustained`` is the pair the brief forbids
    ``ELAPSED_DURATION(5, DAY)`` from standing in for, and the two sustained
    durations must not collapse into each other either.
    """
    from afterworlds.ingestion.mechanical.representation import _dataclass_payload

    seen: dict[bytes, str] = {}
    for name, applicability in BANDS.items():
        key = canonical_bytes(_dataclass_payload(applicability))
        assert key not in seen, f"{name} collides with {seen[key]}"
        seen[key] = name
    assert len(seen) == len(BANDS)


def test_partial_consumption_is_not_merely_less_than_half() -> None:
    """*"eats **but** consumes less than half"* excludes eating nothing.

    The source gives the two a different consequence — a saving throw against
    one, an automatic level against the other — so a representation that cannot
    tell them apart states the wrong rule for a creature that ate nothing.
    """
    partial = BANDS["partial: 0 < x < 1/2"]
    assert partial.band is not None
    assert partial.band.lower == Rational(0, 1)
    assert partial.band.lower_inclusive is False
    assert partial != BANDS["none: x == 0"]
    assert partial != BANDS["dehydration: x < 1/2, no lower"]


def test_a_sustained_duration_belongs_to_the_band_it_measures() -> None:
    """*"eats nothing **for 5 days**"* is one state with a duration.

    Stated as an elapsed clock beside a zero-food test it would say "five days
    have passed", which is true of every creature alive on day five.
    """
    sustained = BANDS["none, sustained 5 days"]
    assert sustained.band is not None
    assert sustained.band.sustained_at_least == 5
    assert sustained.band.sustained_unit is TimeUnit.DAY
    elapsed = Applicability(
        kind=ApplicabilityKind.ELAPSED_DURATION, value=5, unit=TimeUnit.DAY
    )
    assert applicability_violations(elapsed) == []
    assert elapsed != sustained
    assert elapsed.band is None


@pytest.mark.parametrize(
    ("name", "kw", "expected"),
    [
        ("no bound at all", {}, "states no bound"),
        (
            "crossed bounds",
            {"lower": Rational(1, 1), "upper": Rational(1, 2)},
            "above its upper bound",
        ),
        (
            "a point that excludes itself",
            {"lower": Rational(0, 1), "upper": Rational(0, 1)},
            "names one share but excludes it",
        ),
        (
            "an inclusivity for an absent bound",
            {"upper": Rational(1, 2), "lower_inclusive": True},
            "states an absent lower bound",
        ),
        (
            "half a sustained duration",
            {"upper": Rational(1, 2), "sustained_at_least": 5},
            "both an amount and a unit, or neither",
        ),
        (
            "a sustained duration of nothing",
            {
                "upper": Rational(1, 2),
                "sustained_at_least": 0,
                "sustained_unit": TimeUnit.DAY,
            },
            "is not a duration",
        ),
        (
            "a negative share",
            {"upper": Rational(-1, 2)},
            "numerator -1 is negative",
        ),
        (
            "a share over zero",
            {"upper": Rational(1, 0)},
            "denominator 0 is not positive",
        ),
    ],
)
def test_a_band_that_names_no_real_share_set_fails_closed(
    name: str, kw: dict[str, object], expected: str
) -> None:
    violations = applicability_violations(_band(**kw))
    assert any(expected in v for v in violations), (name, violations)


def test_a_consumption_kind_carrying_the_old_operands_has_nowhere_to_put_them() -> None:
    """Schema 4's ``required_quantity``/``fraction`` triple is gone, not dormant.

    A field no kind ranges over is unreachable by construction, which is why it
    was removed rather than left in place: an unreachable field is exactly the
    ambiguity this succession closes.
    """
    with pytest.raises(TypeError):
        Applicability(  # type: ignore[call-arg]
            kind=ApplicabilityKind.CONSUMPTION_THRESHOLD,
            required_quantity=RequiredQuantity.FOOD,
            fraction=Rational(1, 2),
        )


def test_a_consumption_kind_states_its_band_and_nothing_else() -> None:
    """The closed field matrix still decides the populated set exactly."""
    assert any(
        "states no band" in v
        for v in applicability_violations(
            Applicability(kind=ApplicabilityKind.CONSUMPTION_THRESHOLD)
        )
    )
    assert any(
        "does not range over" in v
        for v in applicability_violations(
            Applicability(
                kind=ApplicabilityKind.ROLL_OUTCOME,
                outcome=AutomaticOutcome.SUCCESS,
                band=BANDS["none: x == 0"].band,
            )
        )
    )


# ---------------------------------------------------------------------------
# Requirement 3 — one reading for Falling's damage
# ---------------------------------------------------------------------------

FALL_INTERVAL = DamageInterval(
    basis=ScalingBasis.DISTANCE_FALLEN, amount=10, unit=DistanceUnit.FOOT
)
FALLING = DamageFact(
    damage_type=DamageType.BLUDGEONING, dice=D6, maximum_dice=20, per=FALL_INTERVAL
)


def test_falling_states_its_whole_damage_in_one_fact() -> None:
    """1d6 per 10 feet fallen, capped at 20d6, with no base beside it."""
    assert fact_invariant_violations(FALLING) == ()
    payload = fact_payload(FALLING)
    assert payload["per"] == {"basis": "distance_fallen", "amount": 10, "unit": "foot"}
    assert payload["maximum_dice"] == 20
    assert fact_from_payload(payload) == FALLING


def test_falling_cannot_be_stated_as_base_damage_plus_scaling() -> None:
    """The schema-4 shape, refused at the fact that made it ambiguous."""
    violations = fact_invariant_violations(
        ScalingFact(
            basis=ScalingBasis.DISTANCE_FALLEN,
            threshold=10,
            effect=ScalingEffect.DAMAGE,
            direction=ScalingDirection.INCREASE,
            dice_amount=D6,
        )
    )
    assert any("stated as DamageFact.per" in v for v in violations)


def test_a_component_states_one_damage_composition() -> None:
    """The component-level half, for a scaling whose basis is not a distance.

    ``ScalingFact`` refuses ``DISTANCE_FALLEN`` outright, so this catches the
    composition that is legal fact by fact and unreadable together.
    """
    level_scaled = ScalingFact(
        basis=ScalingBasis.CHARACTER_LEVEL,
        threshold=5,
        effect=ScalingEffect.DAMAGE,
        dice_amount=D6,
    )
    assert component_damage_composition_violations((FALLING,), (), "t") == []
    assert (
        component_damage_composition_violations(
            (DamageFact(damage_type=DamageType.FIRE, dice=D6), level_scaled), (), "t"
        )
        == []
    )
    violations = component_damage_composition_violations(
        (FALLING, level_scaled), (), "component hazard.falling/fall_damage"
    )
    assert any("one component states one damage composition" in v for v in violations)


def test_the_rule_reaches_inside_an_option_arm() -> None:
    """An actor choice is not a way around a component-scoped rule."""
    option = ComponentOption(
        semantic_key="arm",
        facts=(
            FALLING,
            ScalingFact(
                basis=ScalingBasis.CHARACTER_LEVEL,
                threshold=5,
                effect=ScalingEffect.DAMAGE,
                amount=2,
            ),
        ),
    )
    assert component_damage_composition_violations((), (option,), "t")


@pytest.mark.parametrize(
    ("name", "interval", "expected"),
    [
        (
            "a basis that is not a distance",
            DamageInterval(
                basis=ScalingBasis.CHARACTER_LEVEL, amount=10, unit=DistanceUnit.FOOT
            ),
            "not a distance",
        ),
        (
            "an interval of nothing",
            DamageInterval(
                basis=ScalingBasis.DISTANCE_FALLEN, amount=0, unit=DistanceUnit.FOOT
            ),
            "is not an interval",
        ),
    ],
)
def test_a_malformed_interval_fails_closed(
    name: str, interval: DamageInterval, expected: str
) -> None:
    violations = fact_invariant_violations(
        DamageFact(damage_type=DamageType.BLUDGEONING, dice=D6, per=interval)
    )
    assert any(expected in v for v in violations), (name, violations)


def test_an_interval_repeats_dice_rather_than_a_flat_amount() -> None:
    violations = fact_invariant_violations(
        DamageFact(damage_type=DamageType.FIRE, flat_amount=3, per=FALL_INTERVAL)
    )
    assert any("an interval repeats a dice expression" in v for v in violations)


# ---------------------------------------------------------------------------
# A roll outcome answers to exactly one roll in its own scope
# ---------------------------------------------------------------------------

ON_SUCCESS = Applicability(
    kind=ApplicabilityKind.ROLL_OUTCOME, outcome=AutomaticOutcome.SUCCESS
)
HALVED = DamageModificationFact(
    direction=DamageModDirection.REDUCE, factor=Rational(1, 2)
)


def test_a_roll_outcome_with_no_roll_in_scope_fails_closed() -> None:
    """The rejected proposal's shape: a halving component that calls for no roll.

    *"On a successful check"* names the check the same rule already called for.
    In a component of its own it names the outcome of nothing.
    """
    violations = component_roll_outcome_violations(
        (HALVED,), (), ON_SUCCESS, "component hazard.falling/fall_halving"
    )
    assert any("outcome of nothing" in v for v in violations)


def test_a_roll_outcome_with_two_rolls_in_scope_fails_closed() -> None:
    """Ambiguous is worse than absent: a consumer picks one."""
    violations = component_roll_outcome_violations(
        (
            _surface_check(RollContext.ABILITY_CHECK),
            AttackRollFact(attack_kind=AttackKind.MELEE_WEAPON, to_hit_bonus=5),
            HALVED,
        ),
        (),
        ON_SUCCESS,
        "component x/y",
    )
    assert any("which one the outcome is about is unstated" in v for v in violations)


def test_the_halving_belongs_to_the_component_that_holds_the_check() -> None:
    """The honest authoring the rule forces, and the one the source states.

    The modifier sits beside the check, and only that fact carries the outcome —
    the Reaction the same component states is not conditioned on succeeding.
    """
    check = _surface_check(RollContext.ABILITY_CHECK)
    assert (
        component_roll_outcome_violations(
            (check, HALVED),
            (),
            None,
            "component hazard.falling/surface_check",
            (FactQualifier(fact_key=fact_key(HALVED), applies_when=ON_SUCCESS),),
        )
        == []
    )


def test_an_option_arm_establishes_its_own_roll_but_not_its_siblings() -> None:
    """Arms are mutually exclusive, so a roll in one has not happened in another."""
    check = _surface_check(RollContext.ABILITY_CHECK)
    rolling = ComponentOption(
        semantic_key="rolls", facts=(check,), applies_when=ON_SUCCESS
    )
    silent = ComponentOption(
        semantic_key="silent", facts=(HALVED,), applies_when=ON_SUCCESS
    )
    findings = component_roll_outcome_violations((), (rolling, silent), None, "t")
    assert not any("rolls" in f for f in findings)
    assert any("silent" in f and "outcome of nothing" in f for f in findings)


def test_a_component_wide_outcome_is_not_established_by_one_arm() -> None:
    """A component-wide condition holds whichever arm is taken, so an arm's roll
    cannot establish it."""
    check = _surface_check(RollContext.ABILITY_CHECK)
    findings = component_roll_outcome_violations(
        (HALVED,),
        (
            ComponentOption(semantic_key="a", facts=(check,)),
            ComponentOption(semantic_key="b", facts=(check,)),
        ),
        ON_SUCCESS,
        "t",
    )
    assert any("outcome of nothing" in f for f in findings)


# ---------------------------------------------------------------------------
# Requirement 4 — the schema-4 → schema-5 succession
# ---------------------------------------------------------------------------


def test_this_build_declares_schema_5_and_the_registry_pins_its_hash() -> None:
    assert REPRESENTATION_SCHEMA_VERSION == SCHEMA_5_VERSION
    assert representation_schema_hash() == SCHEMA_5_HASH


def test_schema_4_rejects_schema_5_only_meaning() -> None:
    """Each of the three corrections, refused under the contract that lacks it."""
    for holder, expected in (
        (_dc10(RollContext.SAVING_THROW), "'context' key"),
        (
            Applicability(
                kind=ApplicabilityKind.CONSUMPTION_THRESHOLD,
                band=BANDS["none: x == 0"].band,
            ),
            "'band' key",
        ),
        (FALLING, "'per' key"),
        (FALL_INTERVAL, "does not admit 'foot'"),
    ):
        from afterworlds.ingestion.mechanical.representation import (
            post_schema_3_violations,
        )

        findings = post_schema_3_violations(holder, SCHEMA_4_VERSION)
        assert any(expected in f for f in findings), (holder, findings)
        assert post_schema_3_violations(holder, SCHEMA_5_VERSION) == []


def test_schema_5_still_states_every_schema_4_introduction() -> None:
    """A later contract states its predecessor's admissions as well as its own."""
    from afterworlds.ingestion.mechanical.representation import _VERSION_STATES

    assert _VERSION_STATES[SCHEMA_5_VERSION] >= _VERSION_STATES[SCHEMA_4_VERSION]
    assert SCHEMA_5_VERSION in _VERSION_STATES[SCHEMA_5_VERSION]


def test_the_registered_path_from_schema_3_crosses_schema_4() -> None:
    """The committed artifact's chain is preserved, not shortened.

    A direct 3 → 5 row would reach the same declaration while asserting the
    artifact never crossed schema 4, which its own evidence rules refuse.
    """
    steps = lift_path(
        (SCHEMA_3_VERSION, SCHEMA_3_HASH), (SCHEMA_5_VERSION, SCHEMA_5_HASH)
    )
    assert [s.lift_id for s in steps] == [
        "5d-lift-schema-3-to-4",
        "5d-lift-schema-4-to-5",
    ]
    assert (steps[0].to_version, steps[0].to_hash) == (SCHEMA_4_VERSION, SCHEMA_4_HASH)


@pytest.mark.parametrize(
    ("name", "source", "target"),
    [
        (
            "reversed",
            (SCHEMA_5_VERSION, SCHEMA_5_HASH),
            (SCHEMA_4_VERSION, SCHEMA_4_HASH),
        ),
        (
            "unregistered source",
            ("5d-representation-schema-9", "0" * 64),
            (SCHEMA_5_VERSION, SCHEMA_5_HASH),
        ),
        (
            "hash mismatch",
            (SCHEMA_4_VERSION, "0" * 64),
            (SCHEMA_5_VERSION, SCHEMA_5_HASH),
        ),
        (
            "skipped destination",
            (SCHEMA_3_VERSION, SCHEMA_3_HASH),
            ("5d-representation-schema-9", "0" * 64),
        ),
        (
            "no-op is not a path",
            (SCHEMA_5_VERSION, SCHEMA_5_HASH),
            (SCHEMA_5_VERSION, SCHEMA_5_HASH),
        ),
    ],
)
def test_an_unauthorized_succession_fails_closed(
    name: str, source: tuple[str, str], target: tuple[str, str]
) -> None:
    with pytest.raises(UnknownSchemaLiftError):
        lift_path(source, target)


@pytest.fixture(scope="module")
def accepted() -> AcceptedInputs:
    return load_accepted_inputs(ACCEPTED)


def test_the_accepted_artifact_holds_no_ability_check_fact(
    accepted: AcceptedInputs,
) -> None:
    """Why a *required* axis moves no accepted identity.

    Adding a required field to a family changes every payload of that family.
    Nothing accepted is affected because nothing accepted is that family — which
    is a fact about the artifact, so it is asserted against the artifact rather
    than assumed.
    """
    families = [
        f.FAMILY.value
        for component in accepted.oracle.representation.components
        for f in component.all_facts()
    ]
    assert families
    assert "ability_check" not in families


def test_lifting_the_accepted_artifact_to_schema_5_moves_nothing(
    accepted: AcceptedInputs,
) -> None:
    """Byte identity across every inherited collection, and two recorded steps."""
    before_identity = oracle_identity(accepted.oracle)
    lifted, records = lift_accepted_inputs(accepted, (SCHEMA_5_VERSION, SCHEMA_5_HASH))

    assert [r.lift_id for r in records] == [
        "5d-lift-schema-3-to-4",
        "5d-lift-schema-4-to-5",
    ]
    before = representation_payload(
        accepted.oracle.representation, schema_version=SCHEMA_3_VERSION
    )
    after = representation_payload(
        lifted.oracle.representation, schema_version=SCHEMA_5_VERSION
    )
    assert set(before) == set(after)
    for collection in sorted(before):
        assert canonical_bytes(before[collection]) == canonical_bytes(after[collection])
    for record in records:
        assert set(record.verified_collections) == set(before)

    # Carried by identity, never by transformation.
    assert lifted.oracle.representation is accepted.oracle.representation
    assert lifted.oracle.spans == accepted.oracle.spans
    assert lifted.oracle.obligations == accepted.oracle.obligations
    assert lifted.batches == accepted.batches
    assert lifted.acceptances == accepted.acceptances
    # The committed artifact predates anchors, so the lift synthesizes them in
    # their one possible reading — each retained batch reviewed under the schema
    # the artifact declared — rather than at the destination, which would be the
    # restamp the evidence rules refuse.
    assert accepted.schema_anchors == ()
    assert [
        (a.batch_id, a.proposal_identity, a.schema_version, a.schema_hash)
        for a in lifted.schema_anchors
    ] == [
        (b.batch_id, b.proposal_identity, SCHEMA_3_VERSION, SCHEMA_3_HASH)
        for b in accepted.batches
    ]
    assert lifted.oracle.schema_version == SCHEMA_5_VERSION

    # The oracle identity moves *only* because its declared schema did, which is
    # Decision 8 behaving correctly, and the payload it covers is unchanged.
    assert oracle_identity(lifted.oracle) != before_identity


def test_the_committed_artifact_is_never_written(accepted: AcceptedInputs) -> None:
    """A succession is proved against the file, never applied to it."""
    before = ACCEPTED.read_bytes()
    lift_accepted_inputs(accepted, (SCHEMA_5_VERSION, SCHEMA_5_HASH))
    assert ACCEPTED.read_bytes() == before
    assert json.loads(before.decode("utf-8"))["representation_schema"] == {
        "version": SCHEMA_3_VERSION,
        "hash": SCHEMA_3_HASH,
    }


def test_a_schema_4_declaration_still_loads_under_a_schema_5_build() -> None:
    """The predecessor contract stays recognized, so nothing already merged is
    stranded by this succession."""
    from afterworlds.ingestion.mechanical.schema_lift import accepted_schema_contracts

    contracts = accepted_schema_contracts()
    assert (SCHEMA_3_VERSION, SCHEMA_3_HASH) in contracts
    assert (SCHEMA_4_VERSION, SCHEMA_4_HASH) in contracts
    assert (SCHEMA_5_VERSION, SCHEMA_5_HASH) in contracts


def test_a_schema_5_draft_declaring_schema_4_is_refused() -> None:
    """The whole-draft seam, not only the walker."""
    from afterworlds.ingestion.mechanical.representation import (
        RecordDraft,
        RecordKind,
        RepresentationDraft,
    )

    draft = RepresentationDraft(
        records=(
            RecordDraft(semantic_key="hazard.falling", kind=RecordKind.GLOSSARY_RULE),
        ),
        components=(
            ComponentDraft(
                record_key="hazard.falling",
                semantic_key="fall_damage",
                handling=ComponentHandling.STRUCTURED,
                facts=(FALLING,),
            ),
        ),
        prose_bindings=(),
        relationships=(),
        references=(),
        provenance=(),
    )
    assert declared_meaning_violations(draft, SCHEMA_5_VERSION) == []
    assert any(
        "'per' key" in f for f in declared_meaning_violations(draft, SCHEMA_4_VERSION)
    )
