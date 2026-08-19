"""Applicability payloads fail closed on primitive types — PR #155.

Codex review round 3, second of two merge-blocking families. Both loaders
coerced ``negated`` with ``bool(...)``, so JSON ``"false"`` reconstructed as
``True`` — an applicability that means the exact opposite of what the malformed
authority states, then canonicalized and able to pass publication against an
identically coerced oracle. ``value`` and the nested ``at_least`` had no exact
integer check either: ``true`` satisfied every range test as ``1`` because
``bool`` is an ``int`` subclass, and ``"3"`` raised an incidental ``TypeError``
from a comparison rather than a stated finding.

The rule is stated once, on the build side. ``applicability_violations`` and
``size_comparison_violations`` own the typed contract and both loaders already
call them after construction, so removing the coercions is what lets a
malformed value *reach* the check. The half the typed invariants cannot see —
a missing or misspelled JSON key — is
:func:`applicability_payload_violations`, which both loaders run first.

Nothing is normalized, defaulted, or reinterpreted. An accepted-input failure
is :class:`OracleLoadError`; a stored-state failure is
:class:`PersistedStateReconstructionError`.
"""

from __future__ import annotations

import copy
import json
from typing import Any

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from afterworlds.ingestion.mechanical.oracle import OracleLoadError, _applicability
from afterworlds.ingestion.mechanical.persistence import (
    _applicability_from_row,
    persist_draft,
    reconstruct_candidate,
)
from afterworlds.ingestion.mechanical.projection import (
    applicability_payload,
    identify_projection,
)
from afterworlds.ingestion.mechanical.raw_state import (
    PersistedStateReconstructionError,
)
from afterworlds.ingestion.mechanical.representation import (
    Applicability,
    ApplicabilityKind,
    Comparison,
    CreatureSize,
    SizeComparison,
    SizeRelation,
    TrackedQuantity,
    applicability_violations,
    size_comparison_violations,
)
from tests.ingestion.mechanical.conftest import (
    NOW,
    build_candidate,
    build_representation_with_options,
)

THRESHOLD = Applicability(
    kind=ApplicabilityKind.QUANTITY_THRESHOLD,
    negated=True,
    quantity=TrackedQuantity.SPEED,
    comparison=Comparison.EQUALS,
    value=0,
)
SIZE = Applicability(
    kind=ApplicabilityKind.SIZE_COMPARISON,
    negated=True,
    any_of=(
        SizeComparison(category=CreatureSize.TINY),
        SizeComparison(relation=SizeRelation.SMALLER, at_least=2),
    ),
)


def _payload(applicability: Applicability) -> dict[str, Any]:
    built = applicability_payload(applicability)
    assert built is not None
    return built


def _mutated(applicability: Applicability, mutate: Any) -> dict[str, Any]:
    payload = copy.deepcopy(_payload(applicability))
    mutate(payload)
    return payload


# ---------------------------------------------------------------------------
# The honest payloads still load, through both doors
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("applicability", [THRESHOLD, SIZE])
def test_a_well_formed_applicability_still_round_trips(
    applicability: Applicability,
) -> None:
    payload = _payload(applicability)
    assert _applicability(payload, "where") == applicability
    assert _applicability_from_row(payload, "table", "where") == applicability


def test_absence_is_still_absence_not_a_malformed_value() -> None:
    assert _applicability(None, "where") is None
    assert _applicability_from_row(None, "table", "where") is None


# ---------------------------------------------------------------------------
# Malformed primitives, missing keys, extra keys
# ---------------------------------------------------------------------------


def _set(key: str, value: object) -> Any:
    return lambda p: p.__setitem__(key, value)


def _set_member(key: str, value: object) -> Any:
    return lambda p: p["any_of"][0].__setitem__(key, value)


CORRUPTIONS: list[tuple[str, Applicability, Any, str]] = [
    # The reported defect, exactly: JSON "false" must not become True.
    ("negated is the string false", THRESHOLD, _set("negated", "false"), "negated"),
    ("negated is the string true", THRESHOLD, _set("negated", "true"), "negated"),
    ("negated is 0", THRESHOLD, _set("negated", 0), "negated"),
    ("negated is 1", THRESHOLD, _set("negated", 1), "negated"),
    ("negated is null", THRESHOLD, _set("negated", None), "negated"),
    # bool is an int subclass; the range check below would pass it silently.
    ("value is true", THRESHOLD, _set("value", True), "threshold value"),
    ("value is false", THRESHOLD, _set("value", False), "threshold value"),
    # A string would have raised an incidental TypeError from `value < 0`.
    ("value is a string integer", THRESHOLD, _set("value", "0"), "threshold value"),
    ("value is a float", THRESHOLD, _set("value", 0.0), "threshold value"),
    # The same two holes, one level down, guarded by `at_least < 1`.
    ("at_least is true", SIZE, _set_member("at_least", True), "size distance"),
    ("at_least is a string", SIZE, _set_member("at_least", "2"), "size distance"),
    ("at_least is a float", SIZE, _set_member("at_least", 2.0), "size distance"),
    # Key sets, which the typed invariants cannot see at all.
    ("a key is missing", THRESHOLD, lambda p: p.pop("phase"), "missing"),
    ("a key is misspelled", THRESHOLD, _set("negatedd", True), "unexpected"),
    ("an extra key is present", SIZE, _set("extra", 1), "unexpected"),
    (
        "a size member is missing a key",
        SIZE,
        lambda p: p["any_of"][0].pop("category"),
        "missing",
    ),
    ("a size member has an extra key", SIZE, _set_member("junk", 1), "unexpected"),
    ("any_of is a string", SIZE, _set("any_of", "abc"), "not an array"),
    ("any_of holds a scalar", SIZE, _set("any_of", [3]), "not an object"),
    ("the whole payload is a list", THRESHOLD, None, "object"),
]


@pytest.mark.parametrize(
    ("label", "base", "mutate", "expected"),
    CORRUPTIONS,
    ids=[c[0] for c in CORRUPTIONS],
)
def test_accepted_input_loading_refuses_malformed_authority(
    label: str, base: Applicability, mutate: Any, expected: str
) -> None:
    payload = [] if mutate is None else _mutated(base, mutate)
    with pytest.raises(OracleLoadError, match=expected):
        _applicability(payload, "where")


@pytest.mark.parametrize(
    ("label", "base", "mutate", "expected"),
    CORRUPTIONS,
    ids=[c[0] for c in CORRUPTIONS],
)
def test_persisted_reconstruction_refuses_the_same_corruption(
    label: str, base: Applicability, mutate: Any, expected: str
) -> None:
    """The stored-state door reports the reconstruction error, not the load one.

    Component-level and option-level applicability are the same payload through
    the same function (``persistence.py`` calls it for both), so one corruption
    table covers both scopes.
    """
    payload = [] if mutate is None else _mutated(base, mutate)
    with pytest.raises(PersistedStateReconstructionError, match=expected):
        _applicability_from_row(payload, "rp_mech_components", "where")


def test_a_string_false_never_reconstructs_as_its_own_negation() -> None:
    """Named separately because it is the reported symptom, not a variant.

    ``bool("false")`` is ``True``. Under the old loader this payload — which
    reads as *not* negated — became a negated applicability, was canonicalized
    in that form, and could pass publication against an identically coerced
    oracle.
    """
    payload = _mutated(THRESHOLD, _set("negated", "false"))
    with pytest.raises(OracleLoadError):
        _applicability(payload, "where")
    with pytest.raises(PersistedStateReconstructionError):
        _applicability_from_row(payload, "rp_mech_components", "where")


# ---------------------------------------------------------------------------
# The build side rejects the same values deterministically
# ---------------------------------------------------------------------------
#
# In-memory construction bypasses both loaders, so the guards have to live in
# the invariant functions or a malformed value reaches a range comparison and
# either passes or raises an incidental TypeError.


def test_a_boolean_threshold_value_is_a_stated_finding_not_a_silent_pass() -> None:
    """``True < 0`` is ``False``, so the range check alone reported nothing."""
    findings = applicability_violations(
        Applicability(
            kind=ApplicabilityKind.QUANTITY_THRESHOLD,
            quantity=TrackedQuantity.SPEED,
            comparison=Comparison.EQUALS,
            value=True,  # type: ignore[arg-type]
        )
    )
    assert any("not an integer" in f for f in findings)


def test_a_string_threshold_value_is_a_finding_not_a_type_error() -> None:
    findings = applicability_violations(
        Applicability(
            kind=ApplicabilityKind.QUANTITY_THRESHOLD,
            quantity=TrackedQuantity.SPEED,
            comparison=Comparison.EQUALS,
            value="3",  # type: ignore[arg-type]
        )
    )
    assert any("not an integer" in f for f in findings)


def test_a_non_boolean_negated_is_a_finding() -> None:
    findings = applicability_violations(
        Applicability(kind=ApplicabilityKind.PHASE, negated="false")  # type: ignore[arg-type]
    )
    assert any("not a boolean" in f for f in findings)


@pytest.mark.parametrize("bad", [True, "2", 2.0])
def test_a_non_integer_size_distance_is_a_finding_not_a_type_error(
    bad: object,
) -> None:
    findings = size_comparison_violations(
        SizeComparison(relation=SizeRelation.SMALLER, at_least=bad)  # type: ignore[arg-type]
    )
    assert any("not an integer" in f for f in findings)


def test_the_type_domain_reports_before_the_range_domain() -> None:
    """One defect, one finding — not a second misleading opinion about range.

    ``at_least=True`` is not "a distance that compares nothing"; it is not a
    distance at all, and saying both would describe a value the caller never
    supplied.
    """
    findings = size_comparison_violations(
        SizeComparison(relation=SizeRelation.SMALLER, at_least=True)  # type: ignore[arg-type]
    )
    assert findings == ["size distance is bool True, not an integer"]


def test_a_well_formed_applicability_still_reports_nothing() -> None:
    assert applicability_violations(THRESHOLD) == []
    assert applicability_violations(SIZE) == []
    assert size_comparison_violations(SizeComparison(category=CreatureSize.TINY)) == []


# ---------------------------------------------------------------------------
# End to end: corrupt applicability in the database itself
# ---------------------------------------------------------------------------
#
# The parametrized tables above call the reconstruction function directly, which
# is where the guard lives. These two prove the guard is actually reached from
# the persisted rows on both scopes the schema-2 component has — the component's
# own qualifier and an option's.


@pytest.mark.parametrize("table", ["rp_mech_components", "rp_mech_component_options"])
def test_a_corrupt_stored_qualifier_refuses_to_reconstruct(
    session: Session, table: str
) -> None:
    """``negated`` stored as the string ``"false"``, in the database."""
    identified = identify_projection(
        build_candidate(representation=build_representation_with_options())
    )
    persist_draft(session, identified, now=NOW)
    session.flush()

    # Reconstructs cleanly before the corruption, so the refusal below is
    # attributable to the corruption rather than to the fixture.
    assert reconstruct_candidate(session, identified.projection_uuid) is not None

    session.execute(
        text(
            f"UPDATE {table} SET applies_when = :bad "
            "WHERE projection_uuid = :uuid AND applies_when IS NOT NULL"
        ),
        {
            "bad": json.dumps({**_payload(THRESHOLD), "negated": "false"}),
            "uuid": identified.projection_uuid,
        },
    )
    session.flush()
    session.expire_all()

    with pytest.raises(PersistedStateReconstructionError, match="negated"):
        reconstruct_candidate(session, identified.projection_uuid)
