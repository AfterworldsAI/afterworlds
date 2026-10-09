"""The reference-closure batch in the Owner-approved replacement chain (#132, #137).

``.claude/review-notes/issue-5d-class-spell-tables-REPLACEMENT-ACCEPT.py``
accepted the regenerated reference-closure proposal through ``accept_proposal``
with both pilots as ``prior``. These tests hold the state after this batch to
the exact approved proposal and all of its spans and units, to both pilots
retained unchanged inside it, and to a release that cannot publish: the five
targets the pilots left undefined close, but seven reference findings over five
other targets remain and the scope is 44 entries of a whole release.
``test_movement_closure_acceptance`` holds the next state.

The recorded states bind the superseded release, whose physical source is not
available: their findings are replayed representation-only and the former
uncovered-leaf claim is retired (``correction-followup.md``).
"""

from __future__ import annotations

import dataclasses
import hashlib
from pathlib import Path

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
    BATCHES,
    REPLACEMENT,
    identity,
    proposal_path,
    through,
)
from tests.ingestion.mechanical._schema_pins import lifted

NOTES = Path(__file__).resolve().parents[3] / ".claude" / "review-notes"


def _glossary(text: str, slug: str) -> str:
    return (
        f"reference srd-5.2.1/rules-glossary:'{text}': "
        f"unknown target record glossary.{slug}"
    )


#: What the Conditions + Actions acceptance left unresolved.
CLOSED = sorted(
    _glossary(t, s)
    for t, s in [
        ("Concentration", "concentration"),
        ("Friendly", "friendly"),
        ("Hostile", "hostile"),
        ("Indifferent", "indifferent"),
        ("Speed", "speed"),
    ]
)
#: Independently read from the source: seven pointers over five targets.
REMAINING = sorted(
    [_glossary("Difficult Terrain", "difficult_terrain")] * 3
    + [
        _glossary("Falling", "falling"),
        _glossary("High Jump", "high_jump"),
        _glossary("Long Jump", "long_jump"),
        "reference srd-5.2.1/playing-the-game:'Combat': "
        "unknown target record play.combat",
    ]
)


BATCH = "reference-closure"
PROPOSAL = load_proposal(proposal_path(BATCH))
PRIOR = through("actions-pilot")
_binding = PROPOSAL.binding
INPUTS = through(BATCH)


def test_both_pilots_are_retained() -> None:
    batches = {b.batch_id: b for b in INPUTS.batches}
    # Only the restart's batches: nothing quarantined is inherited.
    assert sorted(batches) == ["actions-pilot", "conditions-pilot", "reference-closure"]
    for prior in PRIOR.batches:
        retained = batches[prior.batch_id]
        # Loading orders the diff canonically; its entries and hash are unchanged.
        assert set(retained.diff) == set(prior.diff)
        assert dataclasses.replace(retained, diff=prior.diff) == prior
    assert set(PRIOR.acceptances) <= set(INPUTS.acceptances)
    assert set(PRIOR.review_unit_acceptances) <= set(INPUTS.review_unit_acceptances)


def test_it_records_the_owner_acceptance_of_the_exact_proposal() -> None:
    assert proposal_identity(PROPOSAL) == identity(BATCH)
    raw = proposal_path(BATCH).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == BATCHES[BATCH][1]
    (batch,) = [b for b in INPUTS.batches if b.batch_id == BATCH]
    assert batch.proposal_identity == identity(BATCH)
    assert batch.rule == REPLACEMENT.APPROVAL
    assert {a.reviewer for a in INPUTS.acceptances} == {"Ravenlok (Owner)"}
    assert {a.accepted_at for a in INPUTS.acceptances} == {REPLACEMENT.ACCEPTED_AT}


def test_the_whole_scope_is_accepted_beside_both_pilots() -> None:
    proposed = {p.span.span_id for p in PROPOSAL.proposed_spans}
    prior = {s.span_id for s in PRIOR.oracle.spans}
    assert (len(proposed), len(prior)) == (53, 79 + 75)
    (batch,) = [b for b in INPUTS.batches if b.batch_id == BATCH]
    assert set(batch.resolved_scope) == proposed
    assert {s.span_id for s in INPUTS.oracle.spans} == proposed | prior
    assert {s.review_state for s in INPUTS.oracle.spans} == {ReviewState.ACCEPTED}
    units = {u.unit_id for u in PROPOSAL.proposed_review_units}
    prior_units = {u.unit_id for u in PRIOR.oracle.review_units}
    assert (len(units), len(prior_units)) == (14, 17 + 13)
    assert {u.unit_id for u in INPUTS.oracle.review_units} == units | prior_units
    assert {a.unit_id for a in INPUTS.review_unit_acceptances} == units | prior_units
    assert INPUTS.oracle.binding == PROPOSAL.binding == PRIOR.oracle.binding
    assert INPUTS.lifts == () and INPUTS.policy_transitions == ()
    # No reference closes by resolution: the remaining targets stay unknown.
    assert INPUTS.oracle.reference_resolutions == ()


def test_the_representation_is_both_accepted_representations_unchanged() -> None:
    combined = INPUTS.oracle.representation
    for field in dataclasses.fields(combined):
        assert set(getattr(combined, field.name)) == set(
            getattr(PRIOR.oracle.representation, field.name)
        ) | set(getattr(PROPOSAL.proposed_representation, field.name)), field.name


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


def _unknown(inputs: AcceptedInputs) -> list[str]:
    findings = _references(inputs)
    return sorted(f for f in findings if "unknown target record" in f)


def test_the_five_close_and_seven_findings_over_five_targets_remain() -> None:
    assert _unknown(PRIOR) == CLOSED
    assert _unknown(INPUTS) == REMAINING
    assert len({f.rsplit(" ", 1)[1] for f in REMAINING}) == 5


def test_the_recorded_state_keeps_exactly_its_unresolved_references() -> None:
    # The superseded release's uncovered-leaf counts are retired with its
    # physical source (``correction-followup.md``).
    # Native refusal of an incomplete or unreviewed projection is pinned on the
    # current release by ``test_gate.py``
    # (``test_the_same_projection_claiming_no_unit_is_refused_as_incomplete``)
    # and ``test_source_release_readiness.py``
    # (``test_publishing_an_unreviewed_projection_is_typed_refused``).
    assert sorted(_references(INPUTS)) == REMAINING
