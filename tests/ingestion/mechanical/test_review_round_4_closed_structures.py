"""Closed schema-2 structures reject subclasses — PR #155, round 4.

Codex review round 4. `applicability_violations()` never required
``type(applicability) is Applicability``, and the ``any_of`` loop used
``isinstance``. A dataclass subclass carrying an extra meaning-bearing field
therefore validated cleanly while `applicability_payload()` silently omitted
that field — so two applicabilities asserting *different* conditions received
one canonical payload, one persisted form, and one identity.

A subclass can also redefine equality. `applicability_violations()` detects
duplicate size comparisons with a ``set``, so a subclass whose ``__eq__``
ignores its extra field turns two distinct comparisons into one member and the
duplicate is never reported.

The rule is the one the fact-family validator already applied
(`_FACT_TYPES[family] is not type(fact)`), now spelled once as
:func:`exact_type_violations` and applied to the closed structures schema 2
introduced.
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from afterworlds.ingestion.mechanical.oracle import OracleLoadError, _applicability
from afterworlds.ingestion.mechanical.persistence import _applicability_from_row
from afterworlds.ingestion.mechanical.projection import applicability_payload
from afterworlds.ingestion.mechanical.raw_state import (
    PersistedStateReconstructionError,
)
from afterworlds.ingestion.mechanical.representation import (
    Applicability,
    ApplicabilityKind,
    Comparison,
    ComponentDraft,
    ComponentHandling,
    ComponentOption,
    CreatureSize,
    ParticipantRole,
    Phase,
    SizeComparison,
    SizeRelation,
    TrackedQuantity,
    applicability_violations,
    exact_type_violations,
    size_comparison_violations,
)
from afterworlds.ingestion.mechanical.validation import _validate_options
from tests.ingestion.mechanical.conftest import CRAWL_FACT, STAND_FACT

# ---------------------------------------------------------------------------
# Subclasses carrying undeclared meaning
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SizeComparisonWithReach(SizeComparison):
    """A size test that also claims a reach requirement.

    The extra field is *meaning-bearing*: two of these differing only in
    ``reach_feet`` assert different conditions, yet
    ``applicability_payload`` emits only the three declared keys.
    """

    reach_feet: int = 5


@dataclass(frozen=True, eq=False)
class SizeComparisonIgnoringReach(SizeComparison):
    """The equality-evasion vector: distinct content, colliding as a set member.

    ``eq=False`` inherits :class:`SizeComparison`'s ``__eq__``, which compares
    only the declared fields — so two of these with different ``reach_feet``
    are "equal" and collapse into one entry of the duplicate-detection set.
    """

    reach_feet: int = 5


@dataclass(frozen=True)
class ApplicabilityWithScope(Applicability):
    """An applicability that also claims a scope no payload key carries."""

    scope: str = "self"


@dataclass(frozen=True)
class ComponentOptionWithCost(ComponentOption):
    """An option that also claims a cost the option payload never emits."""

    extra_cost: int = 1


THRESHOLD = Applicability(
    kind=ApplicabilityKind.QUANTITY_THRESHOLD,
    quantity=TrackedQuantity.SPEED,
    comparison=Comparison.EQUALS,
    value=0,
)


# ---------------------------------------------------------------------------
# The rule itself
# ---------------------------------------------------------------------------


def test_the_exact_type_rule_admits_the_declared_type_and_nothing_else() -> None:
    assert exact_type_violations(THRESHOLD, Applicability, "x") == []
    (finding,) = exact_type_violations(
        ApplicabilityWithScope(kind=ApplicabilityKind.PHASE, phase=Phase.WHILE_ACTIVE),
        Applicability,
        "x",
    )
    assert "must be Applicability" in finding


# ---------------------------------------------------------------------------
# Applicability and SizeComparison
# ---------------------------------------------------------------------------


def test_an_applicability_subclass_is_refused() -> None:
    findings = applicability_violations(
        ApplicabilityWithScope(kind=ApplicabilityKind.PHASE, phase=Phase.WHILE_ACTIVE)
    )
    assert any("must be Applicability" in f for f in findings)


def test_the_type_gate_precedes_every_field_read() -> None:
    """A subclass could shadow ``kind``; the gate runs before ``kind`` is read."""

    @dataclass(frozen=True)
    class Shadowing(Applicability):
        kind: object = "not-an-applicability-kind"  # type: ignore[assignment]

    findings = applicability_violations(Shadowing())
    # The type name, and no longer the value. Rendering a rejected object runs
    # its ``__repr__``, which on a frozen dataclass reads every declared field —
    # so the refusal itself was observing what it refuses (#137 round 12).
    assert findings == ["applicability must be Applicability, got Shadowing"]


def test_a_size_comparison_subclass_is_refused() -> None:
    findings = size_comparison_violations(
        SizeComparisonWithReach(
            relation=SizeRelation.SMALLER,
            at_least=2,
            measured=ParticipantRole.SUBJECT,
            reference=ParticipantRole.COUNTERPART,
        )
    )
    assert any("must be SizeComparison" in f for f in findings)


def test_a_size_comparison_subclass_inside_any_of_is_refused() -> None:
    """The nested position is the one the old `isinstance` check let through."""
    findings = applicability_violations(
        Applicability(
            kind=ApplicabilityKind.SIZE_COMPARISON,
            any_of=(
                SizeComparisonWithReach(
                    relation=SizeRelation.SMALLER,
                    at_least=2,
                    measured=ParticipantRole.SUBJECT,
                    reference=ParticipantRole.COUNTERPART,
                ),
            ),
        )
    )
    assert findings == ["any_of is not a tuple of size comparisons"]


def test_undeclared_state_would_otherwise_share_one_canonical_payload() -> None:
    """The reason the gate exists, stated as a property rather than asserted.

    Two subclass instances asserting *different* conditions emit byte-identical
    canonical payloads. That is the identity leak; the gate is what stops the
    values reaching this function at all.
    """
    near = ApplicabilityWithScope(
        kind=ApplicabilityKind.PHASE, phase=Phase.WHILE_ACTIVE
    )
    far = ApplicabilityWithScope(
        kind=ApplicabilityKind.PHASE, phase=Phase.WHILE_ACTIVE, scope="allies"
    )
    assert near != far
    assert applicability_payload(near) == applicability_payload(far)
    # ...and both are refused before they can be persisted under one identity.
    assert applicability_violations(near)
    assert applicability_violations(far)


def test_a_subclass_can_evade_duplicate_detection_and_is_refused_first() -> None:
    """Distinct comparisons, equal as set members — the dedup-evasion vector.

    Without the type gate these two are one entry in the ``seen`` set, so the
    duplicate is never reported *and* the differing ``reach_feet`` never reaches
    the payload. The gate fires before the dedup loop runs.
    """
    a = SizeComparisonIgnoringReach(
        relation=SizeRelation.SMALLER,
        at_least=2,
        measured=ParticipantRole.SUBJECT,
        reference=ParticipantRole.COUNTERPART,
    )
    b = SizeComparisonIgnoringReach(
        relation=SizeRelation.SMALLER,
        at_least=2,
        measured=ParticipantRole.SUBJECT,
        reference=ParticipantRole.COUNTERPART,
        reach_feet=99,
    )
    assert a == b and a.reach_feet != b.reach_feet
    assert len({a, b}) == 1  # the collision the dedup check would have seen

    findings = applicability_violations(
        Applicability(kind=ApplicabilityKind.SIZE_COMPARISON, any_of=(a, b))
    )
    assert findings == ["any_of is not a tuple of size comparisons"]


# ---------------------------------------------------------------------------
# Both applicability scopes fail deterministically
# ---------------------------------------------------------------------------


def _choice(*options: ComponentOption) -> ComponentDraft:
    return ComponentDraft(
        record_key="spell:wish",
        semantic_key="qualifier-probe",
        handling=ComponentHandling.STRUCTURED,
        options=options,
    )


SUBCLASS_QUALIFIER = ApplicabilityWithScope(
    kind=ApplicabilityKind.PHASE, phase=Phase.WHILE_ACTIVE
)


def test_a_component_level_subclass_applicability_fails() -> None:
    """The scope `validation.py` checks with `applicability_violations` directly."""
    findings = applicability_violations(SUBCLASS_QUALIFIER)
    assert any("must be Applicability" in f for f in findings)


def test_an_option_level_subclass_applicability_fails() -> None:
    """The nested scope, through the option validator that owns it."""
    findings = _validate_options(
        _choice(
            ComponentOption(semantic_key="a", facts=(CRAWL_FACT,)),
            ComponentOption(
                semantic_key="b",
                facts=(STAND_FACT,),
                applies_when=SUBCLASS_QUALIFIER,
            ),
        ),
        "component spell:wish/qualifier-probe",
    )
    assert any("must be Applicability" in f for f in findings)


def test_both_applicability_scopes_fail_on_the_same_value() -> None:
    """Deterministically, and for the same stated reason in both places."""
    component_level = applicability_violations(SUBCLASS_QUALIFIER)
    option_level = _validate_options(
        _choice(
            ComponentOption(semantic_key="a", facts=(CRAWL_FACT,)),
            ComponentOption(
                semantic_key="b", facts=(STAND_FACT,), applies_when=SUBCLASS_QUALIFIER
            ),
        ),
        "tag",
    )
    assert component_level and option_level
    assert all("must be Applicability" in f for f in component_level)
    assert any("must be Applicability" in f for f in option_level)


def test_an_option_subclass_is_refused() -> None:
    findings = _validate_options(
        _choice(
            ComponentOption(semantic_key="a", facts=(CRAWL_FACT,)),
            ComponentOptionWithCost(semantic_key="b", facts=(STAND_FACT,)),
        ),
        "component spell:wish/qualifier-probe",
    )
    assert any("must be ComponentOption" in f for f in findings)


def test_an_option_subclass_does_not_also_report_downstream_noise() -> None:
    """One defect, one finding: the loop skips a drifted option rather than
    reading fields off a type it just refused."""
    findings = _validate_options(
        _choice(
            ComponentOption(semantic_key="a", facts=(CRAWL_FACT,)),
            ComponentOptionWithCost(semantic_key="b", facts=(STAND_FACT,)),
        ),
        "tag",
    )
    assert len(findings) == 1


def test_well_formed_options_still_validate_clean() -> None:
    assert (
        _validate_options(
            _choice(
                ComponentOption(semantic_key="a", facts=(CRAWL_FACT,)),
                ComponentOption(semantic_key="b", facts=(STAND_FACT,)),
            ),
            "tag",
        )
        == []
    )


# ---------------------------------------------------------------------------
# The loaders inherit the gate
# ---------------------------------------------------------------------------


def test_both_loaders_still_accept_the_declared_types() -> None:
    """The gate must not have closed the ordinary door."""
    payload = applicability_payload(
        Applicability(
            kind=ApplicabilityKind.SIZE_COMPARISON,
            any_of=(
                SizeComparison(
                    category=CreatureSize.TINY,
                    measured=ParticipantRole.SUBJECT,
                ),
            ),
        )
    )
    assert payload is not None
    assert _applicability(payload, "where") is not None
    assert _applicability_from_row(payload, "table", "where") is not None


@pytest.mark.parametrize(
    ("loader", "error"),
    [
        (lambda p: _applicability(p, "where"), OracleLoadError),
        (
            lambda p: _applicability_from_row(p, "rp_mech_components", "where"),
            PersistedStateReconstructionError,
        ),
    ],
    ids=["accepted-input", "persisted-state"],
)
def test_neither_loader_can_construct_a_subclass(loader, error) -> None:  # type: ignore[no-untyped-def]
    """Both build the declared type by name, so this is structural.

    Asserted rather than assumed: a loader that grew a polymorphic constructor
    would reopen exactly the leak the gate closes.
    """
    payload = applicability_payload(THRESHOLD)
    assert payload is not None
    built = loader(payload)
    assert type(built) is Applicability
    with pytest.raises(error):
        loader({**payload, "kind": "not-a-kind"})
