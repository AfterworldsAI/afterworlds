"""The Proficiency Bonus band, under representation schema 13 — CRD Issue 5d (#137).

Schema 13 adds exactly one family, ``ProficiencyBonusBandFact``, for the one
numeric input the *Playing the Game > Proficiency* section prints that a v1
consumer cannot derive: the level-or-CR to bonus progression. Everything else
in that section is reused vocabulary or exact governing prose.

**What this module covers, and what it deliberately leaves to the suite.**
Generic family behaviour — payload round-tripping for every declared family,
unknown-family refusal, persistence, canonicalization — is already covered by
``test_fact_families.py`` and the per-schema modules, and is not repeated here.
What is specific to this family, and therefore here:

* the eight bands the source actually prints, including the first one, which
  is **open below** because the source prints *"Up to 4"* and states no lower
  bound. ``minimum=None`` is that absence, and it survives the payload as an
  explicit null rather than defaulting to 1;
* the numeric contract — a bonus that adds nothing, an upper bound below the
  first level or CR, a lower bound below it, and a band that runs backwards
  are each refused by the declared invariants rather than stored; and
* the schema introduction itself: schema 12 **cannot** state this family, and
  schema 13 can. That is asserted on the committed ``proficiency-1`` proposal,
  so the check is over the artifact a reviewer is actually shown.

Nothing here accepts the proposal, publishes anything, or reads a band at
runtime. No consumer is wired to this family.
"""

from __future__ import annotations

import pathlib

import pytest

from afterworlds.ingestion.mechanical.proposal import load_proposal
from afterworlds.ingestion.mechanical.representation import (
    REPRESENTATION_SCHEMA_VERSION,
    FactFamily,
    MalformedFactPayloadError,
    ProficiencyBonusBandFact,
    declared_meaning_violations,
    fact_from_payload,
    fact_invariant_violations,
    fact_payload,
)
from afterworlds.ingestion.mechanical.schema_lift import (
    SCHEMA_11_HASH,
    SCHEMA_11_VERSION,
    SCHEMA_12_HASH,
    SCHEMA_12_VERSION,
    SCHEMA_13_HASH,
    SCHEMA_13_VERSION,
    lift_path,
)

PROPOSAL_PATH = (
    pathlib.Path(__file__).resolve().parents[3]
    / ".claude"
    / "review-notes"
    / "issue-5d-batch-proficiency-1-PROPOSAL.json"
)

#: ``(bonus, minimum, maximum)`` exactly as the source prints them. The first
#: row is *"Up to 4"*; the last four are the rows 5c represents in a paragraph
#: outside the table container.
PRINTED_BANDS = (
    (2, None, 4),
    (3, 5, 8),
    (4, 9, 12),
    (5, 13, 16),
    (6, 17, 20),
    (7, 21, 24),
    (8, 25, 28),
    (9, 29, 30),
)


def _band(bonus: int, minimum: int | None, maximum: int) -> ProficiencyBonusBandFact:
    return ProficiencyBonusBandFact(bonus=bonus, maximum=maximum, minimum=minimum)


# ---------------------------------------------------------------------------
# The numeric contract
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("bonus", "minimum", "maximum"),
    PRINTED_BANDS,
    ids=[f"+{b}" for b, _, _ in PRINTED_BANDS],
)
def test_every_printed_band_is_well_formed_and_round_trips(
    bonus: int, minimum: int | None, maximum: int
) -> None:
    """The open band and the seven bounded ones, through the payload and back."""
    fact = _band(bonus, minimum, maximum)
    assert fact_invariant_violations(fact) == ()

    payload = fact_payload(fact)
    assert payload["family"] == FactFamily.PROFICIENCY_BONUS_BAND.value
    assert payload["minimum"] == minimum  # explicit null for the open band

    rebuilt = fact_from_payload(payload)
    assert rebuilt == fact
    assert fact_payload(rebuilt) == payload


def test_a_band_open_below_is_not_the_same_band_as_one_starting_at_one() -> None:
    """*"Up to 4"* states no lower bound, and the absence is the represented fact.

    Defaulting ``minimum`` to 1 would make a claim about level 0 and CR 0
    creatures the source never prints. Both facts are legal; they are not
    equal, and the payload keeps them distinguishable.
    """
    open_below = _band(2, None, 4)
    from_one = _band(2, 1, 4)

    assert fact_invariant_violations(open_below) == ()
    assert fact_invariant_violations(from_one) == ()
    assert open_below != from_one
    assert fact_payload(open_below)["minimum"] is None
    assert fact_payload(from_one)["minimum"] == 1
    assert fact_from_payload(fact_payload(open_below)).minimum is None


@pytest.mark.parametrize(
    ("bonus", "minimum", "maximum", "expected"),
    [
        (0, 1, 4, "adds nothing"),
        (-1, 1, 4, "adds nothing"),
        (2, None, 0, "covers no level or CR"),
        (2, None, -4, "covers no level or CR"),
        (2, 0, 4, "below the first level or CR"),
        (2, -1, 4, "below the first level or CR"),
        (3, 8, 5, "runs backwards"),
    ],
    ids=[
        "bonus-zero",
        "bonus-negative",
        "maximum-zero",
        "maximum-negative",
        "minimum-zero",
        "minimum-negative",
        "backwards",
    ],
)
def test_a_band_that_states_no_progression_is_refused(
    bonus: int, minimum: int | None, maximum: int, expected: str
) -> None:
    """Well-typed and still not a band, so the declared invariants refuse it.

    Every value here rebuilds without complaint — each is an integer in the
    right field. What makes them wrong is what a band has to *mean*, which is
    the half of the contract the invariants carry.
    """
    fact = _band(bonus, minimum, maximum)
    violations = fact_invariant_violations(fact)
    assert violations, f"{bonus}/{minimum}/{maximum} should not state a band"
    assert any(expected in v for v in violations), violations


def test_a_band_equal_at_both_ends_is_a_real_one_row_band() -> None:
    """``29-30`` is two levels and ``30-30`` would be one; neither runs backwards."""
    assert fact_invariant_violations(_band(9, 30, 30)) == ()


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("bonus", "+2"),
        ("bonus", True),
        ("bonus", 2.0),
        ("maximum", "4"),
        ("maximum", False),
        ("minimum", "5"),
        ("minimum", True),
    ],
    ids=[
        "bonus-str",
        "bonus-bool",
        "bonus-float",
        "maximum-str",
        "maximum-bool",
        "minimum-str",
        "minimum-bool",
    ],
)
def test_a_band_field_that_is_not_an_integer_is_refused_at_the_builder(
    field: str, value: object
) -> None:
    """A level or CR is counted, so a string, a float and a ``bool`` are all wrong.

    ``bool`` matters on its own: ``isinstance(True, int)`` is true in Python, so
    a family that only asked ``isinstance(..., int)`` would silently store
    ``True`` as the bonus ``1``.
    """
    payload = dict(fact_payload(_band(2, None, 4))) | {field: value}
    with pytest.raises(MalformedFactPayloadError) as raised:
        fact_from_payload(payload)
    assert field in str(raised.value)


# ---------------------------------------------------------------------------
# The schema introduction
# ---------------------------------------------------------------------------


def test_the_crossing_from_schema_12_is_exactly_one_registered_step() -> None:
    """One step, looked up rather than named, in the direction it applies."""
    steps = lift_path(
        (SCHEMA_12_VERSION, SCHEMA_12_HASH),
        (SCHEMA_13_VERSION, SCHEMA_13_HASH),
    )
    assert [step.lift_id for step in steps] == ["5d-lift-schema-12-to-13"]


def test_schema_12_refuses_the_reviewed_draft_for_exactly_the_eight_bands() -> None:
    """The succession is real in the refusing direction, on the reviewed artifact.

    The committed ``proficiency-1`` proposal is the draft a reviewer is shown.
    Schema 12 is the immediately preceding contract, so its refusal is the
    narrowest statement of what schema 13 added: the eight band facts and
    nothing else. Schema 13 admits the same draft with no violation at all.
    """
    draft = load_proposal(PROPOSAL_PATH).proposed_representation
    violations = declared_meaning_violations(draft, SCHEMA_12_VERSION)

    assert len(violations) == len(PRINTED_BANDS)
    assert all(FactFamily.PROFICIENCY_BONUS_BAND.value in v for v in violations)
    assert all(SCHEMA_13_VERSION in v for v in violations)

    assert REPRESENTATION_SCHEMA_VERSION == SCHEMA_13_VERSION
    assert declared_meaning_violations(draft, REPRESENTATION_SCHEMA_VERSION) == []


def test_schema_11_refuses_it_for_the_bands_and_the_schema_12_reason_codes() -> None:
    """One contract further back also lacks the retention codes schema 12 minted.

    Asserted so the narrow schema-12 result above cannot be mistaken for the
    whole distance this draft has travelled.
    """
    draft = load_proposal(PROPOSAL_PATH).proposed_representation
    violations = declared_meaning_violations(draft, SCHEMA_11_VERSION)

    bands = [v for v in violations if FactFamily.PROFICIENCY_BONUS_BAND.value in v]
    codes = [v for v in violations if "prose_retention_reason_code" in v]
    assert len(bands) == len(PRINTED_BANDS)
    assert codes
    assert SCHEMA_11_HASH != SCHEMA_12_HASH != SCHEMA_13_HASH
