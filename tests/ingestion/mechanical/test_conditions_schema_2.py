"""Schema-2: applicability, exhaustive actor choice, and the six new families.

CRD Issue 5d (#137). Everything here fails against ``5d-representation-schema-1``:
the families did not exist, and a component could not carry either a condition
or a choice.

The load-bearing tests are the rejection ones. A choice that can be authored as
a conjunction, or a qualifier that can carry two vocabularies at once, would let
mutually exclusive authority be published as simultaneously applicable — which
is the one thing this structure exists to prevent, and the one failure no
downstream consumer could detect.

**Kept under its original name after schema 3 succeeded schema 2.** The
structures it guards — applicability, the exhaustive actor choice, and the six
families schema 2 added — are all still current; only the *types* used to build
them gained fields. Its facts are therefore constructed as valid schema-3 facts
while every assertion remains schema 2's. What schema 3 itself added is tested
in ``test_conditions_schema_3.py``.
"""

from __future__ import annotations

import pytest

from afterworlds.ingestion.mechanical.projection import applicability_payload
from afterworlds.ingestion.mechanical.representation import (
    Applicability,
    ApplicabilityKind,
    Comparison,
    ComponentDraft,
    ComponentHandling,
    ComponentOption,
    ConditionEffectFact,
    ConditionEffectKind,
    ConditionKind,
    ConditionLevelFact,
    CreatureSize,
    LevelDirection,
    MovementAmount,
    MovementCostFact,
    MovementCostKind,
    MovementMode,
    MovementPermissionFact,
    MovementTransportFact,
    ParticipantRole,
    Phase,
    QuantityMultiplierFact,
    RecoveryTrigger,
    RoundingRule,
    Sense,
    SensoryCapabilityFact,
    SizeComparison,
    SizeRelation,
    StateEffectFact,
    StateEffectKind,
    TrackedQuantity,
    TransformationFact,
    TransformedForm,
    TransportKind,
    applicability_violations,
    fact_from_payload,
    fact_invariant_violations,
    fact_payload,
    fact_target_key,
    size_comparison_violations,
)
from afterworlds.ingestion.mechanical.validation import _validate_options

CRAWL = MovementPermissionFact(mode=MovementMode.CRAWL)
STAND = MovementCostFact(
    kind=MovementCostKind.EXPENDITURE,
    amount=MovementAmount.HALF_SPEED,
    payer=ParticipantRole.SUBJECT,
    rounding=RoundingRule.DOWN,
)
NOT_SPEED_ZERO = Applicability(
    kind=ApplicabilityKind.QUANTITY_THRESHOLD,
    negated=True,
    quantity=TrackedQuantity.SPEED,
    comparison=Comparison.EQUALS,
    value=0,
)


def _component(**overrides: object) -> ComponentDraft:
    base = {
        "record_key": "condition.prone",
        "semantic_key": "restricted_movement",
        "handling": ComponentHandling.STRUCTURED,
    }
    return ComponentDraft(**{**base, **overrides})  # type: ignore[arg-type]


# --- the six new families ----------------------------------------------------


@pytest.mark.parametrize(
    "fact",
    [
        SensoryCapabilityFact(sense=Sense.SIGHT, can_perceive=False),
        SensoryCapabilityFact(sense=Sense.HEARING, can_perceive=False),
        ConditionLevelFact(
            condition=ConditionKind.EXHAUSTION,
            direction=LevelDirection.GAIN,
            amount=1,
            cumulative=True,
        ),
        ConditionLevelFact(
            condition=ConditionKind.EXHAUSTION,
            direction=LevelDirection.REMOVE,
            all_levels=True,
        ),
        MovementCostFact(
            kind=MovementCostKind.PER_FOOT_SURCHARGE,
            amount=MovementAmount.FEET,
            payer=ParticipantRole.COUNTERPART,
            feet=1,
        ),
        MovementTransportFact(
            carrier=ParticipantRole.COUNTERPART,
            carried=ParticipantRole.SUBJECT,
            kind=TransportKind.PERMITTED,
        ),
        STAND,
        CRAWL,
        TransformationFact(
            becomes=TransformedForm.OBJECT, carried_nonmagical_included=True
        ),
        QuantityMultiplierFact(quantity=TrackedQuantity.WEIGHT, factor=10),
        StateEffectFact(StateEffectKind.DIES),
        StateEffectFact(StateEffectKind.AGING_SUSPENDED),
    ],
)
def test_a_new_family_round_trips_and_holds_its_contract(fact: object) -> None:
    assert fact_invariant_violations(fact) == ()
    assert fact_from_payload(fact_payload(fact)) == fact


@pytest.mark.parametrize(
    ("fact", "fragment"),
    [
        # A removal has no range: the source states one only for a grant.
        (
            SensoryCapabilityFact(sense=Sense.SIGHT, can_perceive=False, range_feet=30),
            "removed capability carries a range",
        ),
        # Neither an amount nor all_levels states no change at all.
        (
            ConditionLevelFact(
                condition=ConditionKind.EXHAUSTION, direction=LevelDirection.GAIN
            ),
            "neither an amount nor all_levels",
        ),
        # Both is two claims wearing one shape.
        (
            ConditionLevelFact(
                condition=ConditionKind.EXHAUSTION,
                direction=LevelDirection.REMOVE,
                amount=1,
                all_levels=True,
            ),
            "all_levels carries an amount",
        ),
        (
            ConditionLevelFact(
                condition=ConditionKind.EXHAUSTION,
                direction=LevelDirection.REMOVE,
                amount=1,
                cumulative=True,
            ),
            "only an accrual can be cumulative",
        ),
        # HALF_SPEED states no number, exactly as SpeedChange.HALVED does not.
        (
            MovementCostFact(
                kind=MovementCostKind.EXPENDITURE,
                amount=MovementAmount.HALF_SPEED,
                payer=ParticipantRole.SUBJECT,
                feet=15,
                rounding=RoundingRule.DOWN,
            ),
            "carries a distance",
        ),
        (
            MovementCostFact(
                kind=MovementCostKind.PER_FOOT_SURCHARGE,
                amount=MovementAmount.FEET,
                payer=ParticipantRole.SUBJECT,
            ),
            "no feet",
        ),
        # A factor of 1 multiplies nothing; a rule that changes no value is not
        # a weaker rule, it is no rule.
        (
            QuantityMultiplierFact(quantity=TrackedQuantity.WEIGHT, factor=1),
            "states no change",
        ),
    ],
)
def test_a_vacuous_or_contradictory_fact_is_refused(
    fact: object, fragment: str
) -> None:
    violations = fact_invariant_violations(fact)
    assert any(fragment in v for v in violations), violations


# --- applicability -----------------------------------------------------------


@pytest.mark.parametrize(
    "applicability",
    [
        NOT_SPEED_ZERO,
        Applicability(
            kind=ApplicabilityKind.QUANTITY_THRESHOLD,
            quantity=TrackedQuantity.CONDITION_LEVEL,
            comparison=Comparison.REACHES,
            value=0,
        ),
        Applicability(
            kind=ApplicabilityKind.TRIGGER, trigger=RecoveryTrigger.LONG_REST
        ),
        Applicability(kind=ApplicabilityKind.PHASE, phase=Phase.ON_END),
        Applicability(
            kind=ApplicabilityKind.SIZE_COMPARISON,
            negated=True,
            any_of=(
                SizeComparison(
                    category=CreatureSize.TINY,
                    measured=ParticipantRole.SUBJECT,
                ),
                SizeComparison(
                    relation=SizeRelation.SMALLER,
                    at_least=2,
                    measured=ParticipantRole.SUBJECT,
                    reference=ParticipantRole.COUNTERPART,
                ),
            ),
        ),
    ],
)
def test_a_well_formed_applicability_is_accepted(applicability: Applicability) -> None:
    assert applicability_violations(applicability) == []
    assert applicability_payload(applicability)["kind"] == applicability.kind.value


@pytest.mark.parametrize(
    ("applicability", "fragment"),
    [
        # A kind carrying a field it does not range over is not a weaker claim;
        # it is a claim about a vocabulary it has nothing to say about. This is
        # the guard that stops the qualifier drifting into a predicate language,
        # because it is what would let one payload mean a conjunction.
        (
            Applicability(kind=ApplicabilityKind.PHASE, phase=Phase.ON_END, value=3),
            "carries value",
        ),
        (
            Applicability(
                kind=ApplicabilityKind.QUANTITY_THRESHOLD,
                quantity=TrackedQuantity.SPEED,
                comparison=Comparison.EQUALS,
                value=0,
                any_of=(
                    SizeComparison(
                        category=CreatureSize.TINY,
                        measured=ParticipantRole.SUBJECT,
                    ),
                ),
            ),
            "carries any_of",
        ),
        (Applicability(kind=ApplicabilityKind.PHASE), "states no phase"),
        (
            Applicability(
                kind=ApplicabilityKind.QUANTITY_THRESHOLD,
                quantity=TrackedQuantity.SPEED,
                comparison=Comparison.EQUALS,
            ),
            "states no value",
        ),
        (
            Applicability(
                kind=ApplicabilityKind.SIZE_COMPARISON,
                any_of=(
                    SizeComparison(
                        category=CreatureSize.TINY,
                        measured=ParticipantRole.SUBJECT,
                    ),
                    SizeComparison(
                        category=CreatureSize.TINY,
                        measured=ParticipantRole.SUBJECT,
                    ),
                ),
            ),
            "duplicate size comparison",
        ),
    ],
)
def test_a_malformed_applicability_is_refused(
    applicability: Applicability, fragment: str
) -> None:
    violations = applicability_violations(applicability)
    assert any(fragment in v for v in violations), violations


@pytest.mark.parametrize(
    ("comparison", "fragment"),
    [
        (
            SizeComparison(measured=ParticipantRole.SUBJECT),
            "neither a category nor a distance",
        ),
        (
            SizeComparison(
                category=CreatureSize.TINY,
                relation=SizeRelation.SMALLER,
                measured=ParticipantRole.SUBJECT,
            ),
            "both an absolute category and a relative distance",
        ),
        (
            SizeComparison(
                relation=SizeRelation.SMALLER,
                measured=ParticipantRole.SUBJECT,
                reference=ParticipantRole.COUNTERPART,
            ),
            "states no distance",
        ),
        (
            SizeComparison(
                relation=SizeRelation.SMALLER,
                at_least=0,
                measured=ParticipantRole.SUBJECT,
                reference=ParticipantRole.COUNTERPART,
            ),
            "compares nothing",
        ),
    ],
)
def test_a_malformed_size_comparison_is_refused(
    comparison: SizeComparison, fragment: str
) -> None:
    violations = size_comparison_violations(comparison)
    assert any(fragment in v for v in violations), violations


# --- the exhaustive actor choice ---------------------------------------------


def test_a_well_formed_choice_is_accepted() -> None:
    component = _component(
        options=(
            ComponentOption(semantic_key="crawl", facts=(CRAWL,)),
            ComponentOption(
                semantic_key="stand", facts=(STAND,), applies_when=NOT_SPEED_ZERO
            ),
        )
    )
    assert _validate_options(component, "prone") == []
    # Option facts are published authority, so they count as structured.
    assert component.all_facts() == (CRAWL, STAND)


@pytest.mark.parametrize(
    ("component", "fragment"),
    [
        # A conjunction and a choice at once has no single reading: are the
        # direct facts always true, or only alongside the chosen option?
        (
            _component(
                facts=(CRAWL,),
                options=(
                    ComponentOption(semantic_key="a", facts=(STAND,)),
                    ComponentOption(
                        semantic_key="b",
                        facts=(
                            MovementCostFact(
                                kind=MovementCostKind.PER_FOOT_SURCHARGE,
                                amount=MovementAmount.FEET,
                                payer=ParticipantRole.SUBJECT,
                                feet=1,
                            ),
                        ),
                    ),
                ),
            ),
            "a conjunction or a choice, never both",
        ),
        (
            _component(options=(ComponentOption(semantic_key="only", facts=(CRAWL,)),)),
            "a choice of one",
        ),
        (
            _component(
                options=(
                    ComponentOption(semantic_key="dup", facts=(CRAWL,)),
                    ComponentOption(semantic_key="dup", facts=(STAND,)),
                )
            ),
            "duplicate option key",
        ),
        (
            _component(
                options=(
                    ComponentOption(semantic_key="a", facts=(CRAWL,)),
                    ComponentOption(semantic_key="b", facts=(CRAWL,)),
                )
            ),
            "two options state the same typed facts",
        ),
        (
            _component(
                options=(
                    ComponentOption(semantic_key="a", facts=()),
                    ComponentOption(semantic_key="b", facts=(STAND,)),
                )
            ),
            "states no typed facts",
        ),
        (
            _component(
                options=(
                    ComponentOption(semantic_key="  ", facts=(CRAWL,)),
                    ComponentOption(semantic_key="b", facts=(STAND,)),
                )
            ),
            "blank semantic key",
        ),
    ],
)
def test_a_misshapen_choice_is_refused(
    component: ComponentDraft, fragment: str
) -> None:
    findings = _validate_options(component, "prone")
    assert any(fragment in f for f in findings), findings


def test_nesting_is_unrepresentable_rather_than_rejected() -> None:
    """The strongest form of the no-nesting rule.

    A check can be forgotten or bypassed by a loader; a field that does not
    exist cannot. ``ComponentOption`` has no options of its own, so a nested
    choice is not a shape that fails validation — it is a shape that cannot be
    constructed at all.
    """
    assert not hasattr(ComponentOption("k", (CRAWL,)), "options")
    assert "options" not in {f for f in ComponentOption.__dataclass_fields__}


def test_options_are_exhaustive_by_definition_in_this_version() -> None:
    """No ``options_exhaustive`` flag exists, deliberately.

    Prone states *"your **only** movement options are"*, and no corpus instance
    of a non-exhaustive option set was found. A flag whose one observed value is
    ``True`` would be a field the source never varies.
    """
    assert "options_exhaustive" not in ComponentDraft.__dataclass_fields__


# --- provenance addressing ----------------------------------------------------


def test_facts_in_different_options_have_distinct_provenance_identities() -> None:
    same = CRAWL
    left = fact_target_key("condition.prone", "restricted_movement", same, "crawl")
    right = fact_target_key("condition.prone", "restricted_movement", same, "stand")
    assert left != right
    assert left[-1] == "crawl" and right[-1] == "stand"


def test_a_direct_fact_keeps_its_pre_schema_2_key() -> None:
    """Ordinary component facts must not be re-addressed by this change.

    Every existing provenance claim, override target, and derived fact id is
    built from this three-element key; growing it would silently invalidate all
    of them.
    """
    direct = fact_target_key("r", "c", CRAWL)
    assert direct == ("r", "c", direct[2])
    assert len(direct) == 3
    assert len(fact_target_key("r", "c", CRAWL, "opt")) == 4


# --- semantic-honesty canaries -------------------------------------------------


def test_prone_options_are_not_published_as_simultaneous_effects() -> None:
    """The failure this whole structure exists to prevent.

    Crawling and standing up are alternatives. If they were ever flattened into
    one fact list, a consumer would read "you may crawl **and** you may stand
    up" as both applying at once — authority the source does not state, and a
    difference no count-based check would notice.
    """
    component = _component(
        options=(
            ComponentOption(semantic_key="crawl", facts=(CRAWL,)),
            ComponentOption(semantic_key="stand", facts=(STAND,)),
        )
    )
    assert component.facts == ()
    assert {o.semantic_key for o in component.options} == {"crawl", "stand"}
    # all_facts() deliberately loses the boundary and is documented as such, so
    # it must never be what a component's own `facts` reports.
    assert component.all_facts() != component.facts


def test_a_condition_level_is_not_representable_as_a_bare_condition_effect() -> None:
    """*"gains 1 Exhaustion level"* is not *"gains the Exhaustion condition"*.

    The level is the mechanic — level 1 and level 6 differ by death — so the
    bare application is lossy in a way that changes the rule.
    """
    level = ConditionLevelFact(
        condition=ConditionKind.EXHAUSTION, direction=LevelDirection.GAIN, amount=1
    )
    bare = ConditionEffectFact(
        condition=ConditionKind.EXHAUSTION, effect=ConditionEffectKind.APPLIES
    )
    assert fact_payload(level) != fact_payload(bare)
    assert "amount" in fact_payload(level)


def test_prone_stand_up_is_not_a_speed_modification() -> None:
    """Prone charges a one-off expenditure derived from Speed.

    It does not halve Speed, so ``SpeedModificationFact(HALVED)`` here would be
    false rather than lossy.
    """
    assert fact_payload(STAND)["family"] == "movement_cost"
    assert fact_payload(STAND)["kind"] == MovementCostKind.EXPENDITURE.value
