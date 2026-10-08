"""The Actions pilot in the Owner-approved replacement chain (#132, #137).

``.claude/review-notes/issue-5d-class-spell-tables-REPLACEMENT-ACCEPT.py``
accepted the regenerated Actions pilot through ``accept_proposal`` with the
Conditions pilot as ``prior``. These tests hold the state after this batch to
the exact approved proposal and all of its spans and units, to the Conditions
acceptance retained unchanged inside it, and to its reference findings:
Unarmed Strike resolves, but five targets stay undefined.
``test_reference_closure_acceptance`` holds the next state.

The recorded state binds the superseded release, whose physical source is not
available, so its findings are replayed representation-only. The former
uncovered-leaf claim against that release is retired (``correction-followup.md``).
"""

from __future__ import annotations

import dataclasses

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

OUTSTANDING = sorted(
    f"reference srd-5.2.1/rules-glossary:'{text}': "
    f"unknown target record glossary.{slug}"
    for text, slug in [
        ("Concentration", "concentration"),
        ("Friendly", "friendly"),
        ("Hostile", "hostile"),
        ("Indifferent", "indifferent"),
        ("Speed", "speed"),
    ]
)


BATCH = "actions-pilot"
PROPOSAL = load_proposal(proposal_path(BATCH))
CONDITIONS = through("conditions-pilot")
_binding = PROPOSAL.binding
INPUTS = through(BATCH)


def test_the_conditions_acceptance_is_retained() -> None:
    batches = {b.batch_id: b for b in INPUTS.batches}
    assert sorted(batches) == ["actions-pilot", "conditions-pilot"]
    (conditions,) = CONDITIONS.batches
    retained = batches["conditions-pilot"]
    # Loading orders the diff canonically; its entries and hash are unchanged.
    assert set(retained.diff) == set(conditions.diff)
    assert dataclasses.replace(retained, diff=conditions.diff) == conditions
    assert set(CONDITIONS.acceptances) <= set(INPUTS.acceptances)
    assert set(CONDITIONS.review_unit_acceptances) <= set(
        INPUTS.review_unit_acceptances
    )


def test_it_records_the_owner_acceptance_of_the_exact_proposal() -> None:
    assert proposal_identity(PROPOSAL) == identity(BATCH)
    (batch,) = [b for b in INPUTS.batches if b.batch_id == BATCH]
    assert batch.proposal_identity == identity(BATCH)
    assert batch.rule == REPLACEMENT.APPROVAL
    assert {a.reviewer for a in INPUTS.acceptances} == {"Ravenlok (Owner)"}
    assert {a.accepted_at for a in INPUTS.acceptances} == {REPLACEMENT.ACCEPTED_AT}


def test_the_whole_scope_is_accepted_beside_the_conditions_scope() -> None:
    proposed = {p.span.span_id for p in PROPOSAL.proposed_spans}
    prior = {s.span_id for s in CONDITIONS.oracle.spans}
    assert (len(proposed), len(prior)) == (75, 79)
    (batch,) = [b for b in INPUTS.batches if b.batch_id == "actions-pilot"]
    assert set(batch.resolved_scope) == proposed
    assert {s.span_id for s in INPUTS.oracle.spans} == proposed | prior
    assert {s.review_state for s in INPUTS.oracle.spans} == {ReviewState.ACCEPTED}
    units = {u.unit_id for u in PROPOSAL.proposed_review_units}
    prior_units = {u.unit_id for u in CONDITIONS.oracle.review_units}
    assert (len(units), len(prior_units)) == (13, 17)
    assert {u.unit_id for u in INPUTS.oracle.review_units} == units | prior_units
    assert {a.unit_id for a in INPUTS.review_unit_acceptances} == units | prior_units
    assert INPUTS.oracle.binding == PROPOSAL.binding == CONDITIONS.oracle.binding
    assert INPUTS.lifts == () and INPUTS.policy_transitions == ()
    assert INPUTS.oracle.reference_resolutions == ()


def test_the_representation_is_both_accepted_representations_unchanged() -> None:
    combined = INPUTS.oracle.representation
    for field in dataclasses.fields(combined):
        assert set(getattr(combined, field.name)) == set(
            getattr(CONDITIONS.oracle.representation, field.name)
        ) | set(getattr(PROPOSAL.proposed_representation, field.name)), field.name


def _references(inputs: AcceptedInputs) -> list[str]:
    # The effective representation's own relationship and reference findings
    # (resolutions applied): no corpus, so none of the superseded release's is
    # needed.
    return relationship_and_reference_violations(
        candidate_from_accepted_inputs(lifted(inputs)).representation
    )


def test_unarmed_strike_closes_and_five_targets_stay_unresolved() -> None:
    closed = _references(CONDITIONS)
    assert any("glossary.unarmed_strike" in f for f in closed)

    findings = _references(INPUTS)
    unknown = sorted(f for f in findings if "unknown target record" in f)
    assert unknown == OUTSTANDING
    assert "glossary.unarmed_strike" in {
        r.semantic_key for r in INPUTS.oracle.representation.records
    }


def test_the_recorded_state_keeps_exactly_its_unresolved_references() -> None:
    # Representation-only: every finding the recorded state still carries is
    # one of the five unresolved references. The physical claim that the
    # superseded release has leaves this authority leaves uncovered is retired
    # with that release's source. Native refusal of an incomplete or unreviewed
    # projection is pinned on the current release by ``test_gate.py``
    # (``test_the_same_projection_claiming_no_unit_is_refused_as_incomplete``)
    # and ``test_source_release_readiness.py``
    # (``test_publishing_an_unreviewed_projection_is_typed_refused``).
    assert sorted(_references(INPUTS)) == OUTSTANDING
