"""``MovementCostFact``'s legal value matrix — PR #155, round 5.

Codex review round 5, finding 2. ``_check_movement_cost()`` validated ``feet``
against ``amount`` but never checked ``kind`` against ``amount``, so
``kind=PER_FOOT_SURCHARGE`` with ``amount=HALF_SPEED`` passed with no findings:
a declared per-foot *rate* stated as the lump form. It names no computable cost,
and it could have been persisted and published as Rules Package mechanical
canon.

**One rule, not two.** The review names two prohibitions — ``PER_FOOT_SURCHARGE``
requires ``FEET``, and ``HALF_SPEED`` requires ``EXPENDITURE``. With both
vocabularies holding two members those forbid the *same single cell*, so
stating them separately would report one malformed fact as two defects. The
matrix is therefore stated as the allowed set, which also stays correct if
either vocabulary gains a member: a new pairing is refused until it is
deliberately admitted, rather than silently legal.
"""

from __future__ import annotations

import pytest

from afterworlds.ingestion.mechanical.representation import (
    MovementAmount,
    MovementCostFact,
    MovementCostKind,
    fact_invariant_violations,
)

K = MovementCostKind
A = MovementAmount

#: Every ``kind × amount × feet-presence`` cell with its expected disposition.
#: ``None`` means the fact is valid; a string is the fragment its sole finding
#: must contain. Exhaustive by construction — the guard below fails if either
#: vocabulary grows without this table growing with it.
MATRIX: list[tuple[K, A, int | None, str | None]] = [
    # A per-foot rate stated in feet: "each foot of movement costs 1 extra foot".
    (K.PER_FOOT_SURCHARGE, A.FEET, 1, None),
    (K.PER_FOOT_SURCHARGE, A.FEET, 10, None),
    (K.PER_FOOT_SURCHARGE, A.FEET, None, "carries no feet"),
    (K.PER_FOOT_SURCHARGE, A.FEET, 0, "costs nothing"),
    (K.PER_FOOT_SURCHARGE, A.FEET, -5, "costs nothing"),
    # The reported defect, and the only forbidden cell.
    (K.PER_FOOT_SURCHARGE, A.HALF_SPEED, None, "cannot state a half_speed amount"),
    (K.PER_FOOT_SURCHARGE, A.HALF_SPEED, 10, "cannot state a half_speed amount"),
    (K.PER_FOOT_SURCHARGE, A.HALF_SPEED, 0, "cannot state a half_speed amount"),
    # A fixed-feet expenditure: "spend 10 feet of movement". Preserved — no
    # repository authority disproves it, and nothing committed asserts against it.
    (K.EXPENDITURE, A.FEET, 10, None),
    (K.EXPENDITURE, A.FEET, None, "carries no feet"),
    (K.EXPENDITURE, A.FEET, 0, "costs nothing"),
    # Prone's stand-up cost: "movement equal to half your Speed", no number.
    (K.EXPENDITURE, A.HALF_SPEED, None, None),
    (K.EXPENDITURE, A.HALF_SPEED, 10, "carries a distance"),
]


@pytest.mark.parametrize(
    ("kind", "amount", "feet", "expected"),
    MATRIX,
    ids=[f"{k.value}-{a.value}-feet={f}" for k, a, f, _ in MATRIX],
)
def test_every_movement_cost_cell_has_an_explicit_disposition(
    kind: K, amount: A, feet: int | None, expected: str | None
) -> None:
    findings = fact_invariant_violations(
        MovementCostFact(kind=kind, amount=amount, feet=feet)
    )
    if expected is None:
        assert findings == (), f"expected valid, got {findings}"
    else:
        assert findings, "expected a finding, got none"
        assert any(expected in f for f in findings), findings


def test_the_matrix_covers_every_kind_and_amount_pairing() -> None:
    """The table above must not silently fall behind a widened vocabulary."""
    covered = {(k, a) for k, a, _, _ in MATRIX}
    assert covered == {(k, a) for k in K for a in A}


def test_one_malformed_fact_yields_one_finding() -> None:
    """The forbidden cell is one defect, and must not be reported twice.

    Both prohibitions the review names forbid this same pairing; stating them
    as two rules would produce two findings describing one thing.
    """
    findings = fact_invariant_violations(
        MovementCostFact(kind=K.PER_FOOT_SURCHARGE, amount=A.HALF_SPEED)
    )
    assert len(findings) == 1


def test_the_kind_amount_check_precedes_the_feet_checks() -> None:
    """A cell that is forbidden outright gets no second opinion about ``feet``.

    ``(PER_FOOT_SURCHARGE, HALF_SPEED, feet=10)`` would otherwise also report
    "half_speed carries a distance" — true, but not the defect.
    """
    (finding,) = fact_invariant_violations(
        MovementCostFact(kind=K.PER_FOOT_SURCHARGE, amount=A.HALF_SPEED, feet=10)
    )
    assert "cannot state a half_speed amount" in finding


@pytest.mark.parametrize("bad", [True, False])
def test_a_boolean_is_not_a_distance(bad: bool) -> None:
    """``bool`` is an ``int`` subclass; ``_is_int`` already excludes it.

    Asserted rather than assumed, because the range checks below it would
    otherwise read ``True`` as the distance ``1``.
    """
    findings = fact_invariant_violations(
        MovementCostFact(kind=K.EXPENDITURE, amount=A.FEET, feet=bad)  # type: ignore[arg-type]
    )
    assert any("must be an integer" in f for f in findings)
