"""CRD Issue 5d — what a fresh `hazards-1` regeneration may author under schema 5.

**These are fixtures, not an acceptance.** Proposal
``6277ff735e0e47b3337f2c3736ca7922864b1cde9a3c286b3aee48ee461ba259`` was rejected
and is not reused, edited, or blessed here; nothing in this module constructs it,
imports it, or asserts anything about its identity. What is proved is narrower and
is the only thing a schema PR can prove: **the shapes a later regeneration will
need are authorable under schema 5, and the shapes it must not use are refused.**
The regeneration itself happens after this succession is Owner-merged, from the
bound 5c source, and receives a new identity and a fresh semantic review.

Each fixture below is one correction the rejection called for. They are written
against the representation contract alone — no corpus, no spans, no provenance,
no ledger — because the question each answers is "can the schema state this?",
not "does this record say it".
"""

from __future__ import annotations

import pytest

from afterworlds.ingestion.mechanical.models import ComponentHandling
from afterworlds.ingestion.mechanical.representation import (
    AbilityCheckFact,
    AbilityScore,
    ActionCost,
    ActionEconomyFact,
    Applicability,
    ApplicabilityKind,
    AutomaticOutcome,
    ComponentDraft,
    ConditionEffectFact,
    ConditionEffectKind,
    ConditionKind,
    ConditionLevelFact,
    ConsumptionBand,
    DamageFact,
    DamageInterval,
    DamageModDirection,
    DamageModificationFact,
    DamageOutcome,
    DamageType,
    DcKind,
    DiceExpression,
    DieSize,
    DistanceUnit,
    EffectTerminationFact,
    FactQualifier,
    LevelDirection,
    Rational,
    Recurrence,
    RecurrenceBoundary,
    RequiredQuantity,
    RollActor,
    RollContext,
    RollSpec,
    ScalingBasis,
    Skill,
    TimePeriod,
    TimeUnit,
    applicability_violations,
    component_damage_composition_violations,
    component_roll_outcome_violations,
    fact_invariant_violations,
    fact_key,
    fact_qualifier_violations,
)

D6 = DiceExpression(count=1, die=DieSize.D6)


def _authorable(component: ComponentDraft) -> list[str]:
    """Every component-scoped rule schema 5 applies, asked at once.

    The same functions ``validation._validate_components`` calls, so a fixture
    that passes here is authorable for real rather than passing a weaker local
    check. Provenance and prose-binding closure are deliberately outside this:
    those are relational rules about a corpus this module does not bind.
    """
    findings: list[str] = []
    for fact in component.all_facts():
        findings.extend(fact_invariant_violations(fact))
    if component.applies_when is not None:
        findings.extend(applicability_violations(component.applies_when))
    for qualifier in component.fact_qualifiers:
        findings.extend(applicability_violations(qualifier.applies_when))
    findings.extend(
        fact_qualifier_violations(
            component.facts, component.options, component.fact_qualifiers, "fixture"
        )
    )
    findings.extend(
        component_damage_composition_violations(
            component.facts, component.options, "fixture"
        )
    )
    findings.extend(
        component_roll_outcome_violations(
            component.facts,
            component.options,
            component.applies_when,
            "fixture",
            component.fact_qualifiers,
        )
    )
    return findings


# ---------------------------------------------------------------------------
# 1. `self_extinguish` is MIXED, and "and rolling on the ground" is substantive
#    governing prose rather than a supporting aside
# ---------------------------------------------------------------------------


def test_self_extinguish_can_be_mixed_with_governing_prose() -> None:
    """Burning's self-extinguish states an act the union cannot enumerate.

    *"by giving yourself the Prone condition **and rolling on the ground**"* — the
    Prone cost is typed, the action cost is typed, the termination is typed, and
    the rolling is an act with no family. Schema 4 authored this ``STRUCTURED``
    and carried the rolling as supporting authority owned by the component, which
    says the clause merely *frames* the mechanic. It does not: without it the
    component states that going Prone alone extinguishes the fire.

    ``MIXED`` is what says the component's meaning is partly typed and partly
    governing prose, and it needs no schema addition — only a prose binding,
    which the regeneration supplies from the bound release.
    """
    component = ComponentDraft(
        record_key="hazard.burning",
        semantic_key="self_extinguish",
        handling=ComponentHandling.MIXED,
        irreducibility_reason_code="open_ended_effect",
        facts=(
            ActionEconomyFact(cost=ActionCost.ACTION),
            ConditionEffectFact(
                condition=ConditionKind.PRONE, effect=ConditionEffectKind.APPLIES
            ),
            EffectTerminationFact(),
        ),
    )
    assert _authorable(component) == []
    assert component.handling is ComponentHandling.MIXED
    assert component.irreducibility_reason_code is not None


def test_a_mixed_component_still_has_to_say_why() -> None:
    """MIXED is not a way to avoid naming a closed reason."""
    from afterworlds.ingestion.mechanical.policy import irreducibility_reason_for

    assert irreducibility_reason_for("open_ended_effect") is not None
    assert irreducibility_reason_for("we did not look") is None


# ---------------------------------------------------------------------------
# 2. Falling's damage and its landing, both at the end of the fall
# ---------------------------------------------------------------------------

FALL_DAMAGE = DamageFact(
    damage_type=DamageType.BLUDGEONING,
    dice=D6,
    maximum_dice=20,
    per=DamageInterval(
        basis=ScalingBasis.DISTANCE_FALLEN, amount=10, unit=DistanceUnit.FOOT
    ),
)


def test_falling_damage_and_landing_are_authorable_together() -> None:
    """One component, stating what happens at the end of the fall.

    The damage is 1d6 per 10 feet fallen capped at 20d6 — one fact, one reading
    — and the landing applies Prone unless no damage was taken, which is the
    source's own negative phrasing kept rather than folded into ``ANY_DAMAGE``.
    """
    component = ComponentDraft(
        record_key="hazard.falling",
        semantic_key="fall_damage",
        handling=ComponentHandling.STRUCTURED,
        facts=(
            FALL_DAMAGE,
            ConditionEffectFact(
                condition=ConditionKind.PRONE, effect=ConditionEffectKind.APPLIES
            ),
        ),
        fact_qualifiers=(
            FactQualifier(
                fact_key=fact_key(
                    ConditionEffectFact(
                        condition=ConditionKind.PRONE,
                        effect=ConditionEffectKind.APPLIES,
                    )
                ),
                applies_when=Applicability(
                    kind=ApplicabilityKind.DAMAGE_OUTCOME,
                    negated=True,
                    damage_outcome=DamageOutcome.NO_DAMAGE,
                ),
            ),
        ),
    )
    assert _authorable(component) == []


def test_the_landing_exception_qualifies_only_the_landing() -> None:
    """Component-wide, the exception would gate the damage on itself.

    A component ``applies_when`` composes over everything the component holds,
    so putting *"unless it avoids taking any damage from the fall"* there would
    say the fall deals no damage unless it dealt damage. The qualifier scopes it
    to the one fact the source attaches it to.
    """
    prone = ConditionEffectFact(
        condition=ConditionKind.PRONE, effect=ConditionEffectKind.APPLIES
    )
    qualifier = FactQualifier(
        fact_key=fact_key(prone),
        applies_when=Applicability(
            kind=ApplicabilityKind.DAMAGE_OUTCOME,
            negated=True,
            damage_outcome=DamageOutcome.NO_DAMAGE,
        ),
    )
    component = ComponentDraft(
        record_key="hazard.falling",
        semantic_key="fall_damage",
        handling=ComponentHandling.STRUCTURED,
        facts=(FALL_DAMAGE, prone),
        fact_qualifiers=(qualifier,),
    )
    assert component.qualifier_for(prone) is qualifier.applies_when
    assert component.qualifier_for(FALL_DAMAGE) is None


# ---------------------------------------------------------------------------
# 3. The halving belongs to the surface check that establishes its roll
# ---------------------------------------------------------------------------

SURFACE_CHECK = AbilityCheckFact(
    ability=AbilityScore.STRENGTH,
    dc_kind=DcKind.FIXED,
    dc_value=15,
    skill=Skill.ATHLETICS,
    context=RollContext.ABILITY_CHECK,
    alternatives=(
        RollSpec(
            actor=RollActor.SUBJECT,
            context=RollContext.ABILITY_CHECK,
            ability=AbilityScore.DEXTERITY,
            skill=Skill.ACROBATICS,
        ),
        RollSpec(
            actor=RollActor.SUBJECT,
            context=RollContext.ABILITY_CHECK,
            ability=AbilityScore.STRENGTH,
            skill=Skill.ATHLETICS,
        ),
    ),
)
HALVED = DamageModificationFact(
    direction=DamageModDirection.REDUCE,
    factor=Rational(1, 2),
    # Falling states a halving and nothing about rounding; the Round Down entry
    # states its own rule in its own batch, and a fact must not claim provenance
    # over a span this batch never accounted.
    rounding=None,
)
ON_SUCCESS = Applicability(
    kind=ApplicabilityKind.ROLL_OUTCOME, outcome=AutomaticOutcome.SUCCESS
)


def test_the_halving_sits_in_the_component_that_holds_the_check() -> None:
    """The preferred shape, and now the only authorable one.

    *"On a successful check, any damage resulting from the fall is halved"* is a
    condition on the check this same component calls for. The Reaction the
    component also states is **not** conditioned on succeeding, so the outcome
    qualifies exactly one fact rather than the component.
    """
    component = ComponentDraft(
        record_key="hazard.falling",
        semantic_key="surface_check",
        handling=ComponentHandling.MIXED,
        irreducibility_reason_code="contextual_applicability",
        facts=(
            ActionEconomyFact(cost=ActionCost.REACTION),
            SURFACE_CHECK,
            HALVED,
        ),
        fact_qualifiers=(
            FactQualifier(fact_key=fact_key(HALVED), applies_when=ON_SUCCESS),
        ),
    )
    assert _authorable(component) == []


def test_a_detached_halving_component_is_refused() -> None:
    """The shape the rejection named: an outcome with no roll in scope.

    Authored as its own component, *"on a successful check"* names the outcome
    of nothing — a consumer has no way to know which D20 Test to read, and the
    halving becomes unreachable authority.
    """
    detached = ComponentDraft(
        record_key="hazard.falling",
        semantic_key="fall_halving",
        handling=ComponentHandling.STRUCTURED,
        facts=(HALVED,),
        applies_when=ON_SUCCESS,
    )
    findings = _authorable(detached)
    assert any("outcome of nothing" in f for f in findings), findings


def test_an_ambiguous_owning_roll_is_refused() -> None:
    """Two rolls in scope is worse than none: a consumer picks one."""
    ambiguous = ComponentDraft(
        record_key="hazard.falling",
        semantic_key="surface_check",
        handling=ComponentHandling.STRUCTURED,
        facts=(
            SURFACE_CHECK,
            AbilityCheckFact(
                ability=AbilityScore.CONSTITUTION,
                dc_kind=DcKind.FIXED,
                dc_value=10,
                context=RollContext.SAVING_THROW,
            ),
            HALVED,
        ),
        fact_qualifiers=(
            FactQualifier(fact_key=fact_key(HALVED), applies_when=ON_SUCCESS),
        ),
    )
    findings = _authorable(ambiguous)
    assert any("which one the outcome is about is unstated" in f for f in findings)


# ---------------------------------------------------------------------------
# 4. Both Malnutrition paths, exactly
# ---------------------------------------------------------------------------

GAIN_1 = ConditionLevelFact(
    condition=ConditionKind.EXHAUSTION, direction=LevelDirection.GAIN, amount=1
)
CON_SAVE = AbilityCheckFact(
    ability=AbilityScore.CONSTITUTION,
    dc_kind=DcKind.FIXED,
    dc_value=10,
    context=RollContext.SAVING_THROW,
)


def _food(**kw: object) -> Applicability:
    return Applicability(
        kind=ApplicabilityKind.CONSUMPTION_THRESHOLD,
        band=ConsumptionBand(
            quantity=RequiredQuantity.FOOD, period=TimePeriod.DAY, **kw  # type: ignore[arg-type]
        ),
    )


PARTIAL = _food(lower=Rational(0, 1), upper=Rational(1, 2))
NONE_FOR_FIVE_DAYS = _food(
    lower=Rational(0, 1),
    lower_inclusive=True,
    upper=Rational(0, 1),
    upper_inclusive=True,
    sustained_at_least=5,
    sustained_unit=TimeUnit.DAY,
)


def test_the_partial_eating_path_is_authorable_exactly() -> None:
    """*"eats **but** consumes less than half ... must succeed on a DC 10
    Constitution saving throw or gain 1 Exhaustion level at the day's end"*.

    Four distinct pieces, each in the structure that states it: the band
    excludes zero, the save is typed as a *save*, the level gain is conditioned
    on failing it, and the cadence is the component's recurrence.
    """
    component = ComponentDraft(
        record_key="hazard.malnutrition",
        semantic_key="starvation_save",
        handling=ComponentHandling.STRUCTURED,
        facts=(CON_SAVE, GAIN_1),
        applies_when=PARTIAL,
        recurs=Recurrence(boundary=RecurrenceBoundary.END_OF_DAY),
        fact_qualifiers=(
            FactQualifier(
                fact_key=fact_key(GAIN_1),
                applies_when=Applicability(
                    kind=ApplicabilityKind.ROLL_OUTCOME,
                    outcome=AutomaticOutcome.FAILURE,
                ),
            ),
        ),
    )
    assert _authorable(component) == []
    assert component.applies_when is not None
    assert component.applies_when.band is not None
    assert component.applies_when.band.lower_inclusive is False


def test_the_no_food_path_is_authorable_exactly() -> None:
    """*"eats nothing for 5 days automatically gains 1 Exhaustion level at the
    end of the fifth day as well as an additional level at the end of each
    subsequent day without food"*.

    The band is the point ``x = 0`` sustained for at least five days, and the
    recurrence supplies "each subsequent day". No roll is called for and none is
    conditioned on, so nothing here names a roll outcome.
    """
    component = ComponentDraft(
        record_key="hazard.malnutrition",
        semantic_key="starvation_automatic",
        handling=ComponentHandling.STRUCTURED,
        facts=(GAIN_1,),
        applies_when=NONE_FOR_FIVE_DAYS,
        recurs=Recurrence(boundary=RecurrenceBoundary.END_OF_DAY),
    )
    assert _authorable(component) == []


def test_the_two_malnutrition_paths_do_not_collapse_into_each_other() -> None:
    """The whole point: one band admits a creature that ate nothing, the other
    does not, and they carry different consequences."""
    assert PARTIAL != NONE_FOR_FIVE_DAYS
    assert PARTIAL.band is not None and NONE_FOR_FIVE_DAYS.band is not None
    assert PARTIAL.band.upper == Rational(1, 2)
    assert NONE_FOR_FIVE_DAYS.band.upper == Rational(0, 1)
    assert PARTIAL.band.sustained_at_least is None
    assert NONE_FOR_FIVE_DAYS.band.sustained_at_least == 5


def test_resumed_eating_leaves_the_no_food_band() -> None:
    """ "Each subsequent day **without food**" is the band's own persistence.

    The accrual is gated by the component's applicability, so a day with food is
    a day the component does not apply and the recurrence does not fire. That is
    declared component semantics — ``applies_when`` is *"when this component
    applies at all"* — rather than a second structure, which is why the schema
    adds none for it.
    """
    resumed = _food(
        lower=Rational(0, 1),
        lower_inclusive=False,
        upper=Rational(1, 2),
        sustained_at_least=5,
        sustained_unit=TimeUnit.DAY,
    )
    assert applicability_violations(resumed) == []
    # A creature that has eaten something is inside a different band, and the
    # two are different authority rather than one band read two ways.
    assert resumed != NONE_FOR_FIVE_DAYS


def test_neither_path_uses_an_elapsed_duration_to_mean_no_food() -> None:
    """The substitution the brief forbids, refused by being a different value.

    ``ELAPSED_DURATION(5, DAY)`` says five days have passed, which is true of
    every creature alive on day five. It remains a legal applicability for a
    clause that actually means that; it simply is not this one.
    """
    elapsed = Applicability(
        kind=ApplicabilityKind.ELAPSED_DURATION, value=5, unit=TimeUnit.DAY
    )
    assert applicability_violations(elapsed) == []
    assert elapsed != NONE_FOR_FIVE_DAYS
    assert elapsed.band is None
    assert NONE_FOR_FIVE_DAYS.value is None


@pytest.mark.parametrize(
    "component",
    [
        pytest.param(
            ComponentDraft(
                record_key="hazard.malnutrition",
                semantic_key="starvation_save",
                handling=ComponentHandling.STRUCTURED,
                facts=(GAIN_1,),
                applies_when=PARTIAL,
                fact_qualifiers=(
                    FactQualifier(
                        fact_key=fact_key(GAIN_1),
                        applies_when=Applicability(
                            kind=ApplicabilityKind.ROLL_OUTCOME,
                            outcome=AutomaticOutcome.FAILURE,
                        ),
                    ),
                ),
            ),
            id="a failure branch with no save to fail",
        ),
    ],
)
def test_a_failure_branch_needs_the_roll_it_branches_on(
    component: ComponentDraft,
) -> None:
    """Dropping the save leaves *"or gain 1 Exhaustion level"* conditioned on
    the failure of a roll nothing calls for."""
    assert any("outcome of nothing" in f for f in _authorable(component))
