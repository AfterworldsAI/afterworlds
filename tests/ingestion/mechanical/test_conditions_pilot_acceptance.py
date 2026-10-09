"""The Conditions pilot in the Owner-approved replacement chain (#132, #137).

``.claude/review-notes/issue-5d-class-spell-tables-REPLACEMENT-ACCEPT.py``
recorded the replacement authority through the native seam, ``accept_proposal``,
with this batch first over no prior. These tests hold the state after this batch
to what the Owner approved: the exact regenerated proposal, all of its spans and
review units, its representation unchanged, nothing inherited — and a release
that still cannot publish, because the scope is 17 entries of a whole release
and the ``glossary.unarmed_strike`` target remains undefined.

The recorded states bind the superseded release, whose physical source is not
available: their findings are replayed representation-only and the former
uncovered-leaf claim is retired (``correction-followup.md``).
"""

from __future__ import annotations

from afterworlds.ingestion.mechanical.models import ReviewState
from afterworlds.ingestion.mechanical.oracle import (
    AcceptedInputs,
    candidate_from_accepted_inputs,
)
from afterworlds.ingestion.mechanical.proposal import load_proposal, proposal_identity
from afterworlds.ingestion.mechanical.validation import (
    relationship_and_reference_violations,
)
from tests.ingestion.mechanical._replacement_chain import (
    REPLACEMENT,
    identity,
    proposal_path,
    through,
)
from tests.ingestion.mechanical._schema_pins import lifted

UNKNOWN_UNARMED_STRIKE = (
    "reference srd-5.2.1/rules-glossary:'Unarmed Strike': "
    "unknown target record glossary.unarmed_strike"
)


BATCH = "conditions-pilot"
PROPOSAL = load_proposal(proposal_path(BATCH))
INPUTS = through(BATCH)


def test_it_records_the_owner_acceptance_of_the_exact_proposal() -> None:
    assert proposal_identity(PROPOSAL) == identity(BATCH)
    (batch,) = INPUTS.batches
    assert batch.batch_id == BATCH
    assert batch.proposal_identity == identity(BATCH)
    assert batch.rule == REPLACEMENT.APPROVAL
    assert {a.reviewer for a in INPUTS.acceptances} == {"Ravenlok (Owner)"}
    assert {a.reviewer for a in INPUTS.review_unit_acceptances} == {"Ravenlok (Owner)"}
    assert {a.accepted_at for a in INPUTS.acceptances} == {REPLACEMENT.ACCEPTED_AT}


def test_the_whole_scope_is_accepted_and_nothing_is_inherited() -> None:
    proposed = {p.span.span_id for p in PROPOSAL.proposed_spans}
    assert len(proposed) == 79
    assert set(INPUTS.batches[0].resolved_scope) == proposed
    assert {s.span_id for s in INPUTS.oracle.spans} == proposed
    assert {s.review_state for s in INPUTS.oracle.spans} == {ReviewState.ACCEPTED}
    units = {u.unit_id for u in PROPOSAL.proposed_review_units}
    assert len(units) == 17
    assert {u.unit_id for u in INPUTS.oracle.review_units} == units
    assert {a.unit_id for a in INPUTS.review_unit_acceptances} == units
    assert INPUTS.oracle.representation == PROPOSAL.proposed_representation
    assert INPUTS.oracle.binding == PROPOSAL.binding
    assert (INPUTS.oracle.schema_version, INPUTS.oracle.schema_hash) == (
        PROPOSAL.schema_version,
        PROPOSAL.schema_hash,
    )
    assert INPUTS.lifts == () and INPUTS.policy_transitions == ()


def test_the_unarmed_strike_target_stays_explicit_and_unresolved() -> None:
    representation = INPUTS.oracle.representation
    targets = {r.target_record_key for r in representation.references}
    assert "glossary.unarmed_strike" in targets
    assert "glossary.unarmed_strike" not in {
        r.semantic_key for r in representation.records
    }
    assert INPUTS.oracle.reference_resolutions == ()


def _covered(inputs: AcceptedInputs) -> set[str]:
    oracle = inputs.oracle
    return {s.leaf_id for s in oracle.spans} | {
        leaf for u in oracle.review_units for leaf in u.leaf_ids
    }


def _references(inputs: AcceptedInputs) -> list[str]:
    # The effective representation's own relationship and reference findings
    # (resolutions applied). The recorded state binds the superseded release,
    # whose physical source is not available: representation-only replay.
    return relationship_and_reference_violations(
        candidate_from_accepted_inputs(lifted(inputs)).representation
    )


def test_the_recorded_state_keeps_exactly_its_unresolved_references() -> None:
    # The superseded release's uncovered-leaf counts are retired with its
    # physical source (``correction-followup.md``).
    # Native refusal of an incomplete or unreviewed projection is pinned on the
    # current release by ``test_gate.py``
    # (``test_the_same_projection_claiming_no_unit_is_refused_as_incomplete``)
    # and ``test_source_release_readiness.py``
    # (``test_publishing_an_unreviewed_projection_is_typed_refused``).
    assert sorted(_references(INPUTS)) == [UNKNOWN_UNARMED_STRIKE]
