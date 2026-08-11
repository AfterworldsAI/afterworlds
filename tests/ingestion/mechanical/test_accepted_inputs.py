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
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from afterworlds.ingestion.mechanical.acceptance import AcceptanceError, accept_proposal
from afterworlds.ingestion.mechanical.accounting import validate_acceptance
from afterworlds.ingestion.mechanical.gate import (
    GateFailureCategory,
    run_publication_gate,
)
from afterworlds.ingestion.mechanical.models import ComponentHandling
from afterworlds.ingestion.mechanical.oracle import (
    COMMITTED_ORACLE_DIR,
    OracleLoadError,
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
    record_persisted_state_digest,
    verify_persisted_state,
)
from afterworlds.ingestion.mechanical.policy import (
    SEMANTIC_POLICY_VERSION,
    semantic_policy_hash,
)
from afterworlds.ingestion.mechanical.projection import identify_projection
from afterworlds.ingestion.mechanical.proposal import (
    MechanicalProposal,
    ProposedSpan,
    proposal_identity,
)
from afterworlds.ingestion.mechanical.publication import (
    PublicationOutcome,
    publish_from_committed_oracle,
    resolve_active_projection,
)
from afterworlds.ingestion.mechanical.representation import (
    ComponentDraft,
    RecordDraft,
    RecordKind,
    SpellDescriptorFact,
    SpellSchool,
)
from afterworlds.ingestion.mechanical.validation import validate_representation
from afterworlds.persistence.orm.mechanical import MechanicalAcceptanceBatchORM
from tests.ingestion.mechanical.conftest import (
    BOUNDED_ORACLE_PATH,
    DESCRIPTOR_KEY,
    NOW,
    PACKAGE_UUID,
    RELEASE_BINDING,
    SPELL_KEY,
    bound_corpus,
    build_ledger,
    build_representation,
    mark_release_published,
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


# ---------------------------------------------------------------------------
# PR #151 review remediation — evidence binding, keyed merge, disjoint scopes
# ---------------------------------------------------------------------------
#
# Three findings, one function, one invariant: a batch's retained evidence has
# to describe the authority acceptance actually draws in, and accumulating
# batches have to compose into a ledger that still loads.


def _two_batch_scopes() -> tuple[tuple[str, ...], tuple[str, ...]]:
    """One complete proposal's spans, split into two disjoint review batches."""
    span_ids = [p.span.span_id for p in _proposal().proposed_spans]
    return (span_ids[0],), tuple(span_ids[1:])


def _accept_in_two_batches() -> Any:
    """The workflow full-corpus review needs: one proposal, two disjoint batches."""
    proposal = _proposal()
    first_scope, second_scope = _two_batch_scopes()
    first = accept_proposal(
        proposal,
        batch_id="batch-1",
        rule="the first reviewed span",
        resolved_scope=first_scope,
        reviewer="owner",
        accepted_at="2026-08-09T00:00:00Z",
    )
    return accept_proposal(
        proposal,
        batch_id="batch-2",
        rule="the remaining spans",
        resolved_scope=second_scope,
        reviewer="owner",
        accepted_at="2026-08-10T00:00:00Z",
        prior=first,
    )


# -- 1. evidence names the representation, not only the spans -----------------


def test_identical_span_acceptance_over_different_representations_differs() -> None:
    """The defect this closes: same spans, same diff, different authority.

    A batch that records only span transitions cannot distinguish these two
    acceptances, so its evidence could not establish that the reviewer saw the
    representation about to be published. The recorded proposal identity can.
    """
    baseline = _proposal()
    restated = _proposal(
        proposed_representation=build_representation(
            components=(
                ComponentDraft(
                    record_key=SPELL_KEY,
                    semantic_key=DESCRIPTOR_KEY,
                    handling=ComponentHandling.STRUCTURED,
                    # Level 8, not 9. Not one span disposition differs.
                    facts=(
                        SpellDescriptorFact(
                            level=8,
                            school=SpellSchool.CONJURATION,
                            ritual=False,
                            concentration=False,
                        ),
                    ),
                ),
                build_representation().components[1],
            )
        )
    )
    scope = tuple(p.span.span_id for p in baseline.proposed_spans)
    kwargs = dict(
        batch_id="batch-1",
        rule="every span, reviewed together",
        resolved_scope=scope,
        reviewer="owner",
        accepted_at="2026-08-09T00:00:00Z",
    )
    first = accept_proposal(baseline, **kwargs)  # type: ignore[arg-type]
    second = accept_proposal(restated, **kwargs)  # type: ignore[arg-type]

    # The classification evidence is genuinely identical...
    assert first.batches[0].resolved_scope == second.batches[0].resolved_scope
    assert first.batches[0].diff == second.batches[0].diff
    assert first.batches[0].semantic_diff_hash == second.batches[0].semantic_diff_hash
    # ...and the representation evidence is not.
    assert first.batches[0].proposal_identity == proposal_identity(baseline)
    assert second.batches[0].proposal_identity == proposal_identity(restated)
    assert first.batches[0].proposal_identity != second.batches[0].proposal_identity


def test_the_reviewed_proposal_identity_round_trips(tmp_path: Path) -> None:
    inputs = _accept()
    path = tmp_path / "accepted.json"
    path.write_text(json.dumps(accepted_inputs_payload(inputs)), encoding="utf-8")
    reloaded = load_accepted_inputs(path)
    assert reloaded.batches[0].proposal_identity == inputs.batches[0].proposal_identity


def test_the_reviewed_proposal_identity_is_evidence_not_identity() -> None:
    """Audit metadata, exactly like reviewer and timestamp.

    Two acceptances that reached the same accepted result from differently
    *identified* proposals are still the same authority, so neither the oracle
    identity nor the projection UUID may move.
    """
    inputs = _accept()
    restamped = replace(
        inputs,
        batches=(replace(inputs.batches[0], proposal_identity="b" * 64),),
    )
    assert restamped.batches[0].proposal_identity != inputs.batches[0].proposal_identity
    assert oracle_identity(restamped.oracle) == oracle_identity(inputs.oracle)
    assert (
        identify_projection(candidate_from_accepted_inputs(restamped)).projection_uuid
        == identify_projection(candidate_from_accepted_inputs(inputs)).projection_uuid
    )


# -- 2. one complete proposal, two batches, one copy of everything ------------


def test_two_disjoint_batches_of_one_proposal_do_not_duplicate_authority(
    session: Session,
) -> None:
    """The keyed union, end to end.

    Each batch supplies the *same complete* representation, because that is what
    reviewing one proposal in two sittings means. Concatenating it would
    duplicate every record and component, and the finished artifact could never
    publish.
    """
    merged = _accept_in_two_batches()
    expected = build_representation()
    actual = merged.oracle.representation

    for field in (
        "records",
        "components",
        "prose_bindings",
        "relationships",
        "references",
        "provenance",
    ):
        got = getattr(actual, field)
        assert list(got) == list(getattr(expected, field)), field
        assert len(got) == len(set(got)), f"{field} carries a duplicate"

    # Both batches are recorded, every span is accepted exactly once, and the
    # ledger validates as internally honest review evidence.
    assert [b.batch_id for b in merged.batches] == ["batch-1", "batch-2"]
    assert len(merged.acceptances) == len(merged.oracle.spans)
    assert validate_acceptance(merged.classification()) == ()
    assert (
        validate_representation(actual, merged.classification(), bound_corpus()) == ()
    )


def test_the_merged_artifact_survives_persistence_and_reconstruction(
    session: Session,
) -> None:
    merged = _accept_in_two_batches()
    identified = identify_projection(candidate_from_accepted_inputs(merged))
    persist_draft(session, identified, now=NOW)
    session.flush()

    rebuilt = reconstruct_candidate(session, identified.projection_uuid)
    assert rebuilt.representation == merged.oracle.representation
    assert {
        b.batch_id: b.proposal_identity for b in rebuilt.classification.batches
    } == {b.batch_id: b.proposal_identity for b in merged.batches}
    assert identify_projection(rebuilt).projection_uuid == identified.projection_uuid


def test_a_merged_artifact_round_trips_through_its_committed_form(
    tmp_path: Path,
) -> None:
    merged = _accept_in_two_batches()
    path = tmp_path / "merged.json"
    path.write_text(json.dumps(accepted_inputs_payload(merged)), encoding="utf-8")
    reloaded = load_accepted_inputs(path)
    assert oracle_identity(reloaded.oracle) == oracle_identity(merged.oracle)
    assert reloaded.batches == merged.batches


# -- 3. a conflicting element under an accepted key fails closed --------------


@pytest.mark.parametrize(
    ("mutation", "label"),
    [
        (
            lambda base: {
                "records": (
                    RecordDraft(semantic_key=SPELL_KEY, kind=RecordKind.CONDITION),
                    base.records[1],
                )
            },
            "record",
        ),
        (
            lambda base: {
                "components": (
                    replace(base.components[0], handling=ComponentHandling.MIXED),
                    base.components[1],
                )
            },
            "component",
        ),
        (
            lambda base: {
                "prose_bindings": (replace(base.prose_bindings[0], chunk_char_end=17),)
            },
            "prose binding",
        ),
    ],
    ids=["record-kind-changed", "component-handling-changed", "prose-extent-changed"],
)
def test_a_conflicting_element_under_an_accepted_key_fails_closed(
    mutation: Any, label: str
) -> None:
    """Not a merge conflict to resolve — one reviewer's authority replacing another's.

    These are the three collections whose keys are narrower than their content,
    so they are the three where a key collision can mean disagreement rather
    than repetition.
    """
    proposal = _proposal()
    base = proposal.proposed_representation
    first_scope, second_scope = _two_batch_scopes()
    first = accept_proposal(
        proposal,
        batch_id="batch-1",
        rule="the first reviewed span",
        resolved_scope=first_scope,
        reviewer="owner",
        accepted_at="2026-08-09T00:00:00Z",
    )
    conflicting = _proposal(
        proposed_representation=build_representation(**mutation(base))
    )
    with pytest.raises(AcceptanceError, match="different content") as exc:
        accept_proposal(
            conflicting,
            batch_id="batch-2",
            rule="the remaining spans",
            resolved_scope=second_scope,
            reviewer="owner",
            accepted_at="2026-08-10T00:00:00Z",
            prior=first,
        )
    assert label in str(exc.value)


# -- 4. overlapping re-acceptance is refused ----------------------------------


def test_an_overlapping_re_acceptance_is_refused() -> None:
    """Refused before an artifact exists, rather than producing an unloadable one.

    Re-accepting a span used to strand the earlier batch: its scope member would
    name the newer batch, so the older batch had no acceptance record naming it
    and the ledger failed its own validation from then on.
    """
    proposal = _proposal()
    first_scope, _ = _two_batch_scopes()
    first = accept_proposal(
        proposal,
        batch_id="batch-1",
        rule="the first reviewed span",
        resolved_scope=first_scope,
        reviewer="owner",
        accepted_at="2026-08-09T00:00:00Z",
    )
    with pytest.raises(AcceptanceError, match="re-accepts spans already accepted"):
        accept_proposal(
            proposal,
            batch_id="batch-2",
            rule="reviewing the same span again",
            resolved_scope=first_scope,
            reviewer="second-reviewer",
            accepted_at="2026-08-10T00:00:00Z",
            prior=first,
        )


def test_every_accumulated_ledger_stays_valid() -> None:
    """The property the refusal protects, asserted directly.

    Whatever sequence of accepted batches exists, each batch is named by the
    acceptance records of exactly its own scope — which is what
    ``validate_acceptance`` requires and what re-acceptance used to break.
    """
    merged = _accept_in_two_batches()
    by_batch: dict[str | None, set[str]] = {}
    for record in merged.acceptances:
        by_batch.setdefault(record.batch_id, set()).add(record.span_id)
    for batch in merged.batches:
        assert by_batch[batch.batch_id] == set(batch.resolved_scope)
    assert validate_acceptance(merged.classification()) == ()


# -- 5. missing, malformed, and corrupted evidence ----------------------------


def test_an_artifact_without_a_reviewed_proposal_identity_is_rejected(
    tmp_path: Path,
) -> None:
    payload = accepted_inputs_payload(_accept())
    for batch in payload["acceptance"]["batches"]:  # type: ignore[index]
        del batch["proposal_identity"]
    path = tmp_path / "missing.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(OracleLoadError, match=r"missing \['proposal_identity'\]"):
        load_accepted_inputs(path)


@pytest.mark.parametrize(
    ("identity", "why"),
    [
        ("   ", "blank"),
        ("banana", "a readable placeholder"),
        ("a" * 63, "one character short of a digest"),
        ("a" * 65, "one character long"),
        (("a" * 63 + "A"), "uppercase hex the hashing function never emits"),
        (("z" * 64), "the right length but not hexadecimal"),
        (("0123456789abcdef" * 3 + "0123456789abcde "), "a digest with a stray space"),
    ],
    ids=[
        "blank",
        "readable-placeholder",
        "too-short",
        "too-long",
        "uppercase",
        "non-hex",
        "trailing-space",
    ],
)
def test_a_non_canonical_reviewed_proposal_identity_is_rejected(
    tmp_path: Path, identity: str, why: str
) -> None:
    """Only what ``hash_obj`` can actually emit counts as this evidence.

    A nonblank string was the previous bar, and it let through every value
    below. None of them could have been produced by the repository's hashing
    function, so none of them names a proposal anybody reviewed — the
    difference between weak evidence and evidence that was never generated.
    """
    payload = accepted_inputs_payload(_accept())
    for batch in payload["acceptance"]["batches"]:  # type: ignore[index]
        batch["proposal_identity"] = identity
    path = tmp_path / "non-canonical.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(OracleLoadError) as exc:
        load_accepted_inputs(path)
    message = str(exc.value)
    assert "reviewed proposal identity" in message, why
    assert "is not a canonical SHA-256 digest" in message, why


def test_a_canonical_digest_naming_another_proposal_is_still_accepted() -> None:
    """The stated limit of the shape check, asserted so nobody infers more.

    A canonical digest naming some *other* proposal passes: nothing in the
    accepted artifact can recompute the reviewed proposal, so this layer cannot
    tell the difference — and it is not the layer that should. Reviewer
    authenticity comes from Git review of the committed artifact, which is the
    independently reviewed authority; the persisted-state digest separately
    detects later mutation of stored evidence. Neither this check nor that one
    attests to human review, and #137 does not require self-authenticating
    proposal history.
    """
    inputs = _accept()
    other = replace(
        inputs,
        batches=(replace(inputs.batches[0], proposal_identity="0" * 64),),
    )
    assert validate_acceptance(other.classification()) == ()


def test_a_mistyped_reviewed_proposal_identity_is_rejected(tmp_path: Path) -> None:
    payload = accepted_inputs_payload(_accept())
    for batch in payload["acceptance"]["batches"]:  # type: ignore[index]
        batch["proposal_identity"] = 12345
    path = tmp_path / "mistyped.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(OracleLoadError, match="expected a string"):
        load_accepted_inputs(path)


def test_the_persisted_state_digest_covers_the_reviewed_proposal_identity(
    session: Session,
) -> None:
    """Rewriting it after the fact is detected, exactly like a rewritten reviewer.

    It sits outside semantic identity by design, so without digest coverage a
    stored identity could be swapped for one naming a proposal nobody reviewed
    and every other check would still pass.
    """
    inputs = _accept()
    identified = identify_projection(candidate_from_accepted_inputs(inputs))
    persist_draft(session, identified, now=NOW)
    record_persisted_state_digest(session, identified.projection_uuid)
    session.flush()
    assert verify_persisted_state(session, identified.projection_uuid) == ()

    row = session.execute(
        select(MechanicalAcceptanceBatchORM).where(
            MechanicalAcceptanceBatchORM.projection_uuid == identified.projection_uuid
        )
    ).scalar_one()
    row.proposal_identity = "c" * 64
    session.flush()

    findings = verify_persisted_state(session, identified.projection_uuid)
    assert any("digest" in f for f in findings), findings


def test_a_corrupted_persisted_proposal_identity_cannot_pass_verification(
    session: Session,
) -> None:
    """Reconstructed evidence is held to the same shape as a committed file.

    The committed artifact is not the only way this evidence reaches a
    projection: it is persisted, read back, and judged. Editing the stored value
    to something no hashing function could emit must fail the same check, or the
    database would be a way around the file loader.
    """
    inputs = _accept()
    identified = identify_projection(candidate_from_accepted_inputs(inputs))
    persist_draft(session, identified, now=NOW)
    record_persisted_state_digest(session, identified.projection_uuid)
    session.flush()

    row = session.execute(
        select(MechanicalAcceptanceBatchORM).where(
            MechanicalAcceptanceBatchORM.projection_uuid == identified.projection_uuid
        )
    ).scalar_one()
    row.proposal_identity = "not-a-digest"
    session.flush()

    rebuilt = reconstruct_candidate(session, identified.projection_uuid)
    findings = validate_acceptance(rebuilt.classification)
    assert any("is not a canonical SHA-256 digest" in f for f in findings), findings

    # And the digest still catches it independently, so the two layers do not
    # depend on each other.
    assert any(
        "digest" in f
        for f in verify_persisted_state(session, identified.projection_uuid)
    )


def test_a_corrupted_persisted_proposal_identity_fails_the_publication_gate(
    session: Session,
) -> None:
    """The gate runs acceptance validation over reconstructed state, so it refuses.

    Publication is the decision that matters; asserting the finding without
    asserting the refusal would leave open whether anything acts on it.
    """
    inputs = _accept()
    identified = identify_projection(candidate_from_accepted_inputs(inputs))
    persist_draft(session, identified, now=NOW)
    record_persisted_state_digest(session, identified.projection_uuid)
    mark_release_published(session)
    session.flush()

    row = session.execute(
        select(MechanicalAcceptanceBatchORM).where(
            MechanicalAcceptanceBatchORM.projection_uuid == identified.projection_uuid
        )
    ).scalar_one()
    row.proposal_identity = "0" * 63
    session.flush()

    result = run_publication_gate(session, identified.projection_uuid, inputs.oracle)
    assert not result.passed
    assert GateFailureCategory.SEMANTIC_VALIDATION in result.categories()
    assert any("is not a canonical SHA-256 digest" in f.detail for f in result.failures)
