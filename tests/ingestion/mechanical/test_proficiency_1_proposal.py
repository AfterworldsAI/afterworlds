"""The retained ``proficiency-1`` proposal is loadable coverage — CRD Issue 5d.

``proficiency-1`` is the first regular-section pilot: *Playing the Game >
Proficiency*, proposed and **not accepted**. Nothing here accepts it. The
acceptance exercised below is in-memory evidence that the proposal is
structurally acceptable through the production path — it writes no file, and
this module asserts that the committed accepted artifact is byte-identical
afterwards.

What is pinned, and why each pin is the one that would catch a real regression:

* the retained bytes still derive the identity a reviewer would be shown;
* the section's review unit is coverage the representation actually satisfies
  (``review_unit_violations``, the production check, on the loaded artifact);
* **all eight Proficiency Bonus bands are present**, four from the table
  container and four from the paragraph 5c represents *outside* it. The
  progression is the thing a table-shaped review silently truncates, so the
  band set is asserted as an exact set of triples rather than a count; and
* dropping one of those later rows is *reported*. That is the whole claim the
  review unit makes, so it is proved by mutation rather than assumed.

Deliberately not added to ``test_retained_proposals.py``: that module is over
proposals an accepted batch names, and no batch names this one.
"""

from __future__ import annotations

import hashlib
import pathlib

from afterworlds.ingestion.mechanical.acceptance import accept_proposal
from afterworlds.ingestion.mechanical.models import ReviewState, ReviewUnitKind
from afterworlds.ingestion.mechanical.oracle import (
    COMMITTED_ORACLE_DIR,
    load_accepted_inputs,
)
from afterworlds.ingestion.mechanical.policy import SEMANTIC_POLICY_VERSION
from afterworlds.ingestion.mechanical.projection import review_unit_violations
from afterworlds.ingestion.mechanical.proposal import (
    PROPOSAL_SCHEMA_VERSION_2,
    load_proposal,
    proposal_identity,
)
from afterworlds.ingestion.mechanical.representation import (
    REPRESENTATION_SCHEMA_VERSION,
    ComponentHandling,
    FactFamily,
    ProficiencyBonusBandFact,
    representation_schema_hash,
)

REVIEW_NOTES = pathlib.Path(__file__).resolve().parents[3] / ".claude" / "review-notes"
PROPOSAL_PATH = REVIEW_NOTES / "issue-5d-batch-proficiency-1-PROPOSAL.json"
COMMITTED_ARTIFACT = COMMITTED_ORACLE_DIR / "srd-5-2-1-corpus-36b786d8-fa2.json"

#: The identity the review packet reports and a reviewer would be shown.
PROPOSAL_IDENTITY = "c941c262081eb2ba485ee6963b90c0a2bf79578662a2790baf703f5ed1cac219"  # noqa: E501  # pragma: allowlist secret

RECORD = "play.proficiency"
UNIT_ID = "proficiency-1-section"

#: ``(bonus, minimum, maximum)``. The first row prints "Up to 4", which states
#: no lower bound, so the band is open below rather than starting at 1. The
#: last four are the rows 5c represents outside the table container.
EXPECTED_BANDS = {
    (2, None, 4),
    (3, 5, 8),
    (4, 9, 12),
    (5, 13, 16),
    (6, 17, 20),
    (7, 21, 24),
    (8, 25, 28),
    (9, 29, 30),
}


def _proposal():  # type: ignore[no-untyped-def]
    return load_proposal(PROPOSAL_PATH)


def test_the_retained_bytes_still_derive_the_reviewed_identity() -> None:
    """A proposal nobody can reproduce is not evidence of what was reviewed."""
    proposal = _proposal()
    assert proposal_identity(proposal) == PROPOSAL_IDENTITY
    assert proposal.proposal_schema_version == PROPOSAL_SCHEMA_VERSION_2
    assert proposal.schema_version == REPRESENTATION_SCHEMA_VERSION
    assert proposal.schema_hash == representation_schema_hash()
    assert proposal.policy_version == SEMANTIC_POLICY_VERSION


def test_nothing_in_this_proposal_is_accepted() -> None:
    """It is a proposal. Every proposed row says so, and no batch names it."""
    proposal = _proposal()
    assert {p.span.review_state for p in proposal.proposed_spans} == {
        ReviewState.PROPOSED
    }
    named = {
        batch.proposal_identity
        for batch in load_accepted_inputs(COMMITTED_ARTIFACT).batches
    }
    assert PROPOSAL_IDENTITY not in named


def test_the_section_is_reviewed_as_one_unit_over_thirty_leaves() -> None:
    """One SECTION unit. The table container alone would have truncated it."""
    proposal = _proposal()
    (unit,) = proposal.proposed_review_units
    assert unit.unit_id == UNIT_ID
    assert unit.kind is ReviewUnitKind.SECTION
    assert len(unit.leaf_ids) == 30
    assert len(set(unit.leaf_ids)) == 30
    # 5c excludes the running footer on page 8 of this stretch; a unit naming it
    # would claim review of source the accounting population does not contain.
    assert "bda26fa3-3c42-57a6-93bf-69506f41b67c" not in unit.leaf_ids


def test_the_unit_is_coverage_the_representation_satisfies() -> None:
    """The production coverage check, on the loaded artifact, reports nothing."""
    proposal = _proposal()
    assert (
        review_unit_violations(
            proposal.proposed_review_units,
            proposal.proposed_representation,
            proposal.policy_version,
            tuple(p.span for p in proposal.proposed_spans),
        )
        == []
    )


def test_every_proficiency_bonus_band_is_present() -> None:
    """All eight rows, including the four represented outside the table."""
    proposal = _proposal()
    (table,) = [
        c
        for c in proposal.proposed_representation.components
        if c.semantic_key == "proficiency_bonus_table"
    ]
    assert table.handling is ComponentHandling.STRUCTURED
    bands = [f for f in table.all_facts() if isinstance(f, ProficiencyBonusBandFact)]
    assert {(b.bonus, b.minimum, b.maximum) for b in bands} == EXPECTED_BANDS
    assert len(bands) == len(EXPECTED_BANDS)

    # Each band is expected by the unit under its own family, so an omitted row
    # is a missing expected rule rather than an unnoticed gap.
    band_rules = [
        rule
        for unit in proposal.proposed_review_units
        for rule in unit.expected_rules
        if rule.fact_family == FactFamily.PROFICIENCY_BONUS_BAND.value
    ]
    assert len(band_rules) == 8
    assert all(rule.record_key == RECORD for rule in band_rules)


def test_dropping_a_later_row_is_reported() -> None:
    """The rows outside the table container are exactly the ones at risk."""
    from dataclasses import replace

    proposal = _proposal()
    draft = proposal.proposed_representation
    shortened = replace(
        draft,
        components=tuple(
            (
                replace(
                    c,
                    facts=tuple(
                        f
                        for f in c.facts
                        if not (
                            isinstance(f, ProficiencyBonusBandFact) and f.minimum == 29
                        )
                    ),
                )
                if c.semantic_key == "proficiency_bonus_table"
                else c
            )
            for c in draft.components
        ),
    )
    findings = review_unit_violations(
        proposal.proposed_review_units,
        shortened,
        proposal.policy_version,
        tuple(p.span for p in proposal.proposed_spans),
    )
    assert findings
    assert all("proficiency_bonus_table" in finding for finding in findings)


def test_in_memory_acceptance_is_evidence_and_writes_nothing() -> None:
    """Structurally acceptable through the production path. Not an acceptance.

    ``accept_proposal`` returns an in-memory :class:`AcceptedInputs`; it has no
    output path and persists nothing. The digest comparison is what makes that
    claim checkable here rather than trusted, because this module would
    otherwise be the one place a stray write could hide.
    """
    before = hashlib.sha256(COMMITTED_ARTIFACT.read_bytes()).hexdigest()
    proposal = _proposal()
    prior = load_accepted_inputs(COMMITTED_ARTIFACT)

    accepted = accept_proposal(
        proposal,
        batch_id="proficiency-1-test-evidence-only",
        rule="every span and the one review unit this proposal proposes",
        resolved_scope=tuple(p.span.span_id for p in proposal.proposed_spans),
        reviewer="test-evidence-only",
        accepted_at="2026-09-17T00:00:00Z",
        prior=prior,
        resolved_review_units=(UNIT_ID,),
    )

    # The prior was accepted under an earlier schema, so reaching schema 13 is a
    # verified lift path rather than a re-declaration.
    assert accepted.oracle.schema_version == REPRESENTATION_SCHEMA_VERSION
    assert accepted.oracle.schema_hash == representation_schema_hash()
    assert len(accepted.batches) == len(prior.batches) + 1
    assert {u.unit_id for u in accepted.oracle.review_units} == {UNIT_ID}

    assert hashlib.sha256(COMMITTED_ARTIFACT.read_bytes()).hexdigest() == before
