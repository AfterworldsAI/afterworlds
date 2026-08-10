"""The committed accepted-inputs artifact — CRD Issue 5d, #137 contract 4.

One file carries both halves of accepted authority, and the split between them
is load-bearing:

* the **result** — binding, policy, spans, representation, obligations — is what
  the publication gate judges against and what projection identity is derived
  from; and
* the **evidence** — exact scope, full semantic diff, reviewer, timestamp — is
  retained, persisted, and reconstructable, and reaches no identity.

Keeping them in one file means they cannot drift apart. Keeping them in separate
fields means the evidence cannot leak into identity. These tests hold both ends.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from sqlalchemy.orm import Session

from afterworlds.ingestion.mechanical.acceptance import AcceptanceError, accept_proposal
from afterworlds.ingestion.mechanical.oracle import (
    COMMITTED_ORACLE_DIR,
    accepted_inputs_payload,
    candidate_from_accepted_inputs,
    committed_inputs_for,
    committed_oracle_for,
    load_accepted_inputs,
    oracle_identity,
)
from afterworlds.ingestion.mechanical.persistence import (
    persist_draft,
    reconstruct_candidate,
)
from afterworlds.ingestion.mechanical.policy import (
    SEMANTIC_POLICY_VERSION,
    semantic_policy_hash,
)
from afterworlds.ingestion.mechanical.projection import identify_projection
from afterworlds.ingestion.mechanical.proposal import MechanicalProposal, ProposedSpan
from afterworlds.ingestion.mechanical.publication import (
    PublicationOutcome,
    publish_from_committed_oracle,
    resolve_active_projection,
)
from tests.ingestion.mechanical.conftest import (
    BOUNDED_ORACLE_PATH,
    NOW,
    PACKAGE_UUID,
    RELEASE_BINDING,
    build_ledger,
    build_representation,
)

#: The exact production binding, from the merged CRD Issue 5c release. Stated
#: here so the "nothing is accepted yet" guard names the real release rather
#: than trusting that no file happens to exist.
PRODUCTION_PACKAGE = "4458fa10-4a66-5e0e-9ecc-ea37530ad2b4"
PRODUCTION_RELEASE = "5.2.1-corpus.36b786d8-fa2"


def _proposal(**overrides: object) -> MechanicalProposal:
    base = dict(
        binding=RELEASE_BINDING,
        policy_version=SEMANTIC_POLICY_VERSION,
        policy_hash=semantic_policy_hash(),
        proposed_spans=tuple(
            ProposedSpan(span, "tool:classifier@0", "stated basis")
            for span in build_ledger().spans
        ),
        proposed_representation=build_representation(),
        proposal_origin="tool:proposer@0",
    )
    return MechanicalProposal(**{**base, **overrides})  # type: ignore[arg-type]


def _accept(**overrides: object):  # type: ignore[no-untyped-def]
    proposal = _proposal()
    base = dict(
        batch_id="batch-1",
        rule="every span of the bounded fixture, reviewed together",
        resolved_scope=tuple(p.span.span_id for p in proposal.proposed_spans),
        reviewer="owner",
        accepted_at="2026-08-09T00:00:00Z",
    )
    return accept_proposal(proposal, **{**base, **overrides})  # type: ignore[arg-type]


# -- the committed fixture carries both halves --------------------------------


def test_the_committed_artifact_carries_its_review_evidence() -> None:
    inputs = load_accepted_inputs(BOUNDED_ORACLE_PATH)
    assert inputs.acceptances
    assert {a.span_id for a in inputs.acceptances} == {
        s.span_id for s in inputs.oracle.spans
    }
    assert all(a.reviewer and a.accepted_at for a in inputs.acceptances)


def test_a_batch_retains_its_full_diff_not_only_a_digest() -> None:
    (batch,) = load_accepted_inputs(BOUNDED_ORACLE_PATH).batches
    assert batch.rule
    assert batch.resolved_scope
    assert len(batch.diff) == len(batch.resolved_scope)
    assert batch.semantic_diff_hash


def test_an_artifact_missing_its_acceptance_evidence_is_rejected(
    tmp_path: Path,
) -> None:
    """A claim of acceptance with the acceptance missing is not weaker — it is false."""
    payload = json.loads(BOUNDED_ORACLE_PATH.read_text(encoding="utf-8"))
    payload["acceptance"] = {"batches": [], "records": []}
    path = tmp_path / "hollow.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(Exception, match="acceptance evidence is not complete"):
        load_accepted_inputs(path)


# -- evidence is retained, and reaches no identity ----------------------------


def test_evidence_does_not_participate_in_semantic_identity() -> None:
    """Re-reviewing an unchanged classification must not remint a projection.

    Same accepted result, different reviewer, timestamp, batch id, and selection
    rule — one authority (#137 acceptance criterion 11).
    """
    first = _accept()
    second = _accept(
        batch_id="batch-2",
        rule="re-reviewed after a policy question",
        reviewer="second-reviewer",
        accepted_at="2026-09-01T00:00:00Z",
    )
    assert first.acceptances != second.acceptances
    assert oracle_identity(first.oracle) == oracle_identity(second.oracle)
    assert (
        identify_projection(candidate_from_accepted_inputs(first)).projection_uuid
        == identify_projection(candidate_from_accepted_inputs(second)).projection_uuid
    )


def test_evidence_survives_persistence_and_reconstruction(session: Session) -> None:
    """The gate reads acceptance from reconstructed state, so it has to get there."""
    inputs = _accept()
    identified = identify_projection(candidate_from_accepted_inputs(inputs))
    persist_draft(session, identified, now=NOW)
    session.flush()

    rebuilt = reconstruct_candidate(session, identified.projection_uuid)
    assert {(a.span_id, a.reviewer) for a in rebuilt.classification.acceptances} == {
        (a.span_id, a.reviewer) for a in inputs.acceptances
    }
    (batch,) = rebuilt.classification.batches
    assert batch.rule == "every span of the bounded fixture, reviewed together"
    assert batch.diff == inputs.batches[0].diff
    # And the round trip did not change what the projection *is*.
    assert identify_projection(rebuilt).projection_uuid == identified.projection_uuid


# -- acceptance is explicit, scoped, and merging ------------------------------


def test_only_spans_named_in_the_scope_are_accepted() -> None:
    proposal = _proposal()
    chosen = proposal.proposed_spans[0].span.span_id
    inputs = _accept(resolved_scope=(chosen,))
    assert {s.span_id for s in inputs.oracle.spans} == {chosen}


def test_an_unscoped_or_unattributed_acceptance_is_refused() -> None:
    for kwargs in (
        {"resolved_scope": ()},
        {"reviewer": "  "},
        {"rule": ""},
        {"resolved_scope": ("span:not-proposed",)},
    ):
        with pytest.raises(AcceptanceError):
            _accept(**kwargs)


def test_a_later_batch_does_not_discard_an_earlier_ones_work() -> None:
    proposal = _proposal()
    first_span, *rest = [p.span.span_id for p in proposal.proposed_spans]
    first = _accept(resolved_scope=(first_span,))
    second = accept_proposal(
        proposal,
        batch_id="batch-2",
        rule="the remaining spans",
        resolved_scope=tuple(rest),
        reviewer="owner",
        accepted_at="2026-08-10T00:00:00Z",
        prior=first,
    )
    assert {s.span_id for s in second.oracle.spans} == {first_span, *rest}
    assert [b.batch_id for b in second.batches] == ["batch-1", "batch-2"]


def test_reusing_a_batch_id_is_refused() -> None:
    with pytest.raises(AcceptanceError, match="already recorded"):
        accept_proposal(
            _proposal(),
            batch_id="batch-1",
            rule="again",
            resolved_scope=(_proposal().proposed_spans[0].span.span_id,),
            reviewer="owner",
            accepted_at="2026-08-10T00:00:00Z",
            prior=_accept(),
        )


def test_an_accepted_artifact_round_trips_through_its_committed_form(
    tmp_path: Path,
) -> None:
    inputs = _accept()
    path = tmp_path / "accepted.json"
    path.write_text(json.dumps(accepted_inputs_payload(inputs)), encoding="utf-8")
    reloaded = load_accepted_inputs(path)
    assert oracle_identity(reloaded.oracle) == oracle_identity(inputs.oracle)
    assert reloaded.acceptances == inputs.acceptances
    assert reloaded.batches == inputs.batches


# -- production is unpublished and inactive -----------------------------------


def test_no_production_authority_is_committed() -> None:
    """This PR builds the workflow; it accepts no production content.

    Stated as a test rather than a claim in a PR description, so the day
    somebody commits production authority without review, this fails.
    """
    assert sorted(p.name for p in COMMITTED_ORACLE_DIR.glob("*.json")) == []
    assert committed_oracle_for(PRODUCTION_PACKAGE, PRODUCTION_RELEASE) is None
    assert committed_inputs_for(PRODUCTION_PACKAGE, PRODUCTION_RELEASE) is None


def test_the_production_release_cannot_publish_or_activate(session: Session) -> None:
    """No accepted authority means ABSENT, and nothing becomes active.

    ``publish_from_committed_oracle`` is the production entry point; there is no
    parameter that would let a caller supply authority of its own.
    """
    result = publish_from_committed_oracle(session, "any-projection-uuid", now=NOW)
    assert result.outcome is PublicationOutcome.ABSENT
    # Typed absence, never a null that a caller could read as "fine".
    for package in (PRODUCTION_PACKAGE, PACKAGE_UUID):
        active = resolve_active_projection(session, package)
        assert active.outcome is PublicationOutcome.UNPUBLISHED
        assert active.projection_uuid is None
