"""Schema-3: transport authority, cost payer, rounding, and size operands.

CRD Issue 5d (#137). Everything here fails against ``5d-representation-schema-2``:
the transport family did not exist, a movement cost named no payer, a fractional
amount stated no rounding, and a size comparison kept neither operand.

The load-bearing tests are the ones asserting that two rules which schema 2
rendered *identical* are now distinguishable. Grappled's surcharge is charged to
the grappler and Darkmantle's transport runs the opposite way; under schema 2
each pair collapsed to one typed fact, which is a false representation rather
than a lossy one — the same defect ``RollSpec.actor`` was introduced to remove.

The counterpart rule has its own section. ``COUNTERPART`` is only meaningful
where a closed structure in the same component establishes the binary relation,
and the tests below assert that a component naming it without establishing it is
refused rather than published.
"""

from __future__ import annotations

import pytest

from afterworlds.ingestion.mechanical.projection import applicability_payload
from afterworlds.ingestion.mechanical.representation import (
    Applicability,
    ApplicabilityKind,
    ComponentDraft,
    ComponentHandling,
    ComponentOption,
    ConditionEffectFact,
    ConditionEffectKind,
    ConditionKind,
    CreatureSize,
    MovementAmount,
    MovementCostFact,
    MovementCostKind,
    MovementMode,
    MovementPermissionFact,
    MovementTransportFact,
    ParticipantRole,
    RoundingRule,
    SizeComparison,
    SizeRelation,
    TransportKind,
    component_participant_violations,
    fact_from_payload,
    fact_invariant_violations,
    fact_key,
    fact_payload,
    size_comparison_violations,
)

SUBJECT, COUNTERPART = ParticipantRole.SUBJECT, ParticipantRole.COUNTERPART

#: Grappled > Movable, stated in full. "The grappler can drag or carry you when
#: it moves, but every foot of movement costs it 1 extra foot unless you are
#: Tiny or two or more sizes smaller than it."
GRAPPLED_TRANSPORT = MovementTransportFact(
    carrier=COUNTERPART, carried=SUBJECT, kind=TransportKind.PERMITTED
)
GRAPPLED_SURCHARGE = MovementCostFact(
    kind=MovementCostKind.PER_FOOT_SURCHARGE,
    amount=MovementAmount.FEET,
    payer=COUNTERPART,
    feet=1,
)
GRAPPLED_SIZE_EXCEPTION = Applicability(
    kind=ApplicabilityKind.SIZE_COMPARISON,
    negated=True,
    any_of=(
        SizeComparison(category=CreatureSize.TINY, measured=SUBJECT),
        SizeComparison(
            relation=SizeRelation.SMALLER,
            at_least=2,
            measured=SUBJECT,
            reference=COUNTERPART,
        ),
    ),
)


def _component(
    facts: tuple[object, ...] = (),
    options: tuple[ComponentOption, ...] = (),
    applies_when: Applicability | None = None,
) -> ComponentDraft:
    return ComponentDraft(
        record_key="condition.grappled",
        semantic_key="movable",
        handling=ComponentHandling.STRUCTURED,
        facts=facts,  # type: ignore[arg-type]
        options=options,
        applies_when=applies_when,
    )


# ---------------------------------------------------------------------------
# Transport authority
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "fact",
    [
        GRAPPLED_TRANSPORT,
        # Gelatinous Cube: "When the cube moves, the engulfed target moves with
        # it." The carrier is the subject — the opposite of Grappled.
        MovementTransportFact(
            carrier=SUBJECT, carried=COUNTERPART, kind=TransportKind.AUTOMATIC
        ),
        GRAPPLED_SURCHARGE,
        # Prone: "spend an amount of movement equal to half your Speed (round
        # down) to right yourself".
        MovementCostFact(
            kind=MovementCostKind.EXPENDITURE,
            amount=MovementAmount.HALF_SPEED,
            payer=SUBJECT,
            rounding=RoundingRule.DOWN,
        ),
    ],
)
def test_a_schema_3_fact_round_trips_and_holds_its_contract(fact: object) -> None:
    assert fact_invariant_violations(fact) == ()
    assert fact_from_payload(fact_payload(fact)) == fact


def test_reversing_the_transport_roles_is_a_different_mechanic() -> None:
    """Grappled and Darkmantle, which schema 2 could not tell apart.

    Grappled's grappler carries the subject; the darkmantle is itself carried by
    the creature it attached to. Same surface phrasing, opposite mechanics.
    """
    darkmantle = MovementTransportFact(
        carrier=SUBJECT, carried=COUNTERPART, kind=TransportKind.PERMITTED
    )
    assert darkmantle != GRAPPLED_TRANSPORT
    assert fact_key(GRAPPLED_TRANSPORT) != fact_key(darkmantle)


@pytest.mark.parametrize("role", list(ParticipantRole))
def test_a_creature_transporting_itself_is_refused(role: ParticipantRole) -> None:
    """Ordinary movement is not transport, and must not be authored as it."""
    findings = fact_invariant_violations(
        MovementTransportFact(carrier=role, carried=role, kind=TransportKind.AUTOMATIC)
    )
    assert any("is not transport" in f for f in findings), findings


@pytest.mark.parametrize("bad", ["counterpart", 0, None])
def test_a_non_role_participant_is_a_finding_not_a_type_error(bad: object) -> None:
    findings = fact_invariant_violations(
        MovementTransportFact(
            carrier=bad,  # type: ignore[arg-type]
            carried=SUBJECT,
            kind=TransportKind.AUTOMATIC,
        )
    )
    assert any("carrier" in f for f in findings), findings


# ---------------------------------------------------------------------------
# The counterpart-establishment rule
# ---------------------------------------------------------------------------
#
# This is what keeps COUNTERPART from becoming "some other entity in the prose".


def test_grappleds_component_establishes_its_own_counterpart() -> None:
    """The worked example: transport, cost, and size exception in one component.

    The transport fact establishes the relation, so the surcharge's payer and
    both operands of the size exception resolve against the same counterpart.
    """
    assert (
        component_participant_violations(
            [GRAPPLED_TRANSPORT, GRAPPLED_SURCHARGE], [GRAPPLED_SIZE_EXCEPTION]
        )
        == []
    )


def test_a_counterpart_paid_cost_without_transport_is_refused() -> None:
    """A cost charged to a creature the component never established.

    Nothing in this component says who the counterpart *is*, so the claim is
    about an entity the typed structure cannot name.
    """
    findings = component_participant_violations([GRAPPLED_SURCHARGE], [None])
    assert len(findings) == 1
    assert "nothing in the component establishes one" in findings[0]


def test_a_counterpart_size_test_without_transport_is_refused() -> None:
    findings = component_participant_violations([], [GRAPPLED_SIZE_EXCEPTION])
    assert findings
    assert all("establishes one" in f for f in findings)


def test_a_subject_only_component_needs_no_counterpart() -> None:
    """Prone's stand-up cost names no counterpart, so it establishes none."""
    prone_stand = MovementCostFact(
        kind=MovementCostKind.EXPENDITURE,
        amount=MovementAmount.HALF_SPEED,
        payer=SUBJECT,
        rounding=RoundingRule.DOWN,
    )
    assert component_participant_violations([prone_stand], [None]) == []


def test_the_rule_reaches_option_facts_and_option_applicability() -> None:
    """A choice arm cannot smuggle in a counterpart the component never states.

    The component-level scan is offered every scope at once precisely so an
    option cannot be the hole in it.
    """
    component = _component(
        options=(
            ComponentOption(
                semantic_key="crawl",
                facts=(MovementPermissionFact(mode=MovementMode.CRAWL),),
            ),
            ComponentOption(semantic_key="dragged", facts=(GRAPPLED_SURCHARGE,)),
        )
    )
    findings = component_participant_violations(
        [*component.facts, *(f for o in component.options for f in o.facts)],
        [component.applies_when, *(o.applies_when for o in component.options)],
    )
    assert findings, "an option's counterpart cost must still be caught"


def test_transport_on_the_component_establishes_it_for_an_option() -> None:
    """Grappled states the relation once and both scopes resolve against it."""
    component = _component(
        facts=(GRAPPLED_TRANSPORT,),
        options=(
            ComponentOption(semantic_key="dragged", facts=(GRAPPLED_SURCHARGE,)),
            ComponentOption(
                semantic_key="carried",
                facts=(
                    ConditionEffectFact(
                        ConditionKind.GRAPPLED, ConditionEffectKind.APPLIES
                    ),
                ),
            ),
        ),
    )
    findings = component_participant_violations(
        [*component.facts, *(f for o in component.options for f in o.facts)],
        [component.applies_when, *(o.applies_when for o in component.options)],
    )
    assert findings == []


# ---------------------------------------------------------------------------
# Relational size comparisons
# ---------------------------------------------------------------------------


def test_reversing_the_size_operands_is_a_different_test() -> None:
    """Grappled and Unarmed Strike, which schema 2 could not tell apart.

    "you are two or more sizes smaller than it" (Grappled) versus a test
    measuring the counterpart against the subject. Same shape, opposite claim.
    """
    grappled = SizeComparison(
        relation=SizeRelation.SMALLER,
        at_least=2,
        measured=SUBJECT,
        reference=COUNTERPART,
    )
    reversed_ = SizeComparison(
        relation=SizeRelation.SMALLER,
        at_least=2,
        measured=COUNTERPART,
        reference=SUBJECT,
    )
    assert grappled != reversed_
    assert size_comparison_violations(grappled) == []
    assert size_comparison_violations(reversed_) == []


def test_an_at_most_bound_is_admitted() -> None:
    """Unarmed Strike: "no more than one size larger than you".

    Not representable at all under schema 2, which had only ``at_least``.
    """
    comparison = SizeComparison(
        relation=SizeRelation.LARGER,
        at_most=1,
        measured=COUNTERPART,
        reference=SUBJECT,
    )
    assert size_comparison_violations(comparison) == []


@pytest.mark.parametrize(
    ("comparison", "fragment"),
    [
        # The source states one bound or the other, never a range.
        (
            SizeComparison(
                relation=SizeRelation.SMALLER,
                at_least=2,
                at_most=3,
                measured=SUBJECT,
                reference=COUNTERPART,
            ),
            "both a minimum and a maximum",
        ),
        # "smaller" is not a claim until it says smaller than whom.
        (
            SizeComparison(relation=SizeRelation.SMALLER, at_least=2, measured=SUBJECT),
            "names no reference participant",
        ),
        # An absolute category has no second operand.
        (
            SizeComparison(
                category=CreatureSize.TINY, measured=SUBJECT, reference=COUNTERPART
            ),
            "absolute size comparison names a reference",
        ),
        # A creature is never a size apart from itself.
        (
            SizeComparison(
                relation=SizeRelation.SMALLER,
                at_least=2,
                measured=SUBJECT,
                reference=SUBJECT,
            ),
            "against itself",
        ),
        (
            SizeComparison(
                relation=SizeRelation.LARGER,
                at_most=0,
                measured=COUNTERPART,
                reference=SUBJECT,
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


def test_the_size_operands_reach_the_wire_payload() -> None:
    """An operand the payload drops is an operand the identity cannot see."""
    payload = applicability_payload(GRAPPLED_SIZE_EXCEPTION)
    assert payload is not None
    absolute, relative = payload["any_of"]  # type: ignore[index]
    assert absolute["measured"] == "subject"
    assert absolute["reference"] is None
    assert relative["measured"] == "subject"
    assert relative["reference"] == "counterpart"
    assert relative["at_least"] == 2
    assert relative["at_most"] is None
