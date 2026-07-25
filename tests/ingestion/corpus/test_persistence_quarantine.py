"""Persistence, tamper-detection, and legacy-quarantine tests — Issue 5c.

Maps to Acceptance #1/#8 (persisted-corpus digest round-trip), the tamper-
detection test requirement, Acceptance #12 (legacy zero-reachability), and the
PR #134 remediation regression set: DB-grounded final gating, fail-closed
chunk-runtime-membership verification, idempotent republication, and no
partial content on a failed gate.
"""

from __future__ import annotations

import copy
import dataclasses
from uuid import UUID

import pytest
from sqlalchemy import delete, select

import afterworlds.ingestion.corpus.persistence as persistence_mod
from afterworlds.ingestion.corpus.bundle import persisted_corpus_payload
from afterworlds.ingestion.corpus.persistence import (
    _load_policy,
    finalize_release,
    persist_release,
    reconstruct_payload,
    verify_chunk_runtime_membership,
    verify_persisted_digest,
)
from afterworlds.ingestion.corpus.pipeline import CandidateRelease
from afterworlds.ingestion.corpus.policy import PolicyReconstructionError
from afterworlds.ingestion.corpus.quarantine import (
    LEGACY_ARTIFACT_SHA256,
    check_active_store,
    check_legacy_reachability,
)
from afterworlds.ingestion.corpus.vector_publication import read_actual_vector_state
from afterworlds.models.enums import PublicationStatusEnum, RuleSubsystemEnum
from afterworlds.persistence.orm.corpus import (
    CorpusProjectionORM,
    CorpusReleaseORM,
    LedgerLeafORM,
    ReconciliationORM,
    ReconciliationPolicyORM,
)
from afterworlds.persistence.orm.rules_package import (
    RuleChunkORM,
    RuleSourceORM,
    RulesPackageORM,
)
from afterworlds.pipeline.retrieval.rules_corpus_service import RulesCorpusService
from afterworlds.services.rules_package import RulesPackageService

from .conftest import REPO_ROOT

_NOW = "2026-07-23T00:00:00Z"


def _finalize(session, candidate, chroma_client, retrieval_config, fake_embedding):
    """Publish *candidate* through the real cross-store lifecycle."""
    return finalize_release(
        session,
        candidate,
        repo_root=REPO_ROOT,
        now=_NOW,
        chroma_client=chroma_client,
        retrieval_config=retrieval_config,
        embedding_function=fake_embedding,
    )


def _persist(session, release, chroma_client, retrieval_config, fake_embedding):
    """Re-persist a finalized release's SQL state into a fresh DB and reindex its
    vectors, so the SQL-tamper tests below can exercise digest verification in a
    store whose vector logical state matches the fixture's."""
    persist_release(session, release, now=_NOW)
    session.commit()
    pkg = release.release.package_uuid
    RulesCorpusService(
        chroma_client, retrieval_config, fake_embedding
    ).reindex_from_sql(session, UUID(pkg))
    return pkg


def _vstate(session, pkg, chroma_client, retrieval_config, fake_embedding):
    """The actual read-back vector logical state, as a digest-ready payload."""
    return read_actual_vector_state(
        chroma_client, pkg, retrieval_config, fake_embedding
    ).to_payload()


def test_persist_round_trip_digest_matches(
    session, release, chroma_client, retrieval_config, fake_embedding
):
    pkg = _persist(session, release, chroma_client, retrieval_config, fake_embedding)
    vs = _vstate(session, pkg, chroma_client, retrieval_config, fake_embedding)
    assert verify_persisted_digest(session, pkg, vs)


def test_reconstructed_payload_equals_in_memory(
    session, release, chroma_client, retrieval_config, fake_embedding
):
    pkg = _persist(session, release, chroma_client, retrieval_config, fake_embedding)
    vs = _vstate(session, pkg, chroma_client, retrieval_config, fake_embedding)
    in_mem = persisted_corpus_payload(
        pkg,
        release.release.release_version,
        release.ledger,
        release.members,
        release.reconciliation,
        release.policy,
        vs,
    )
    assert reconstruct_payload(session, pkg, vs) == in_mem


def test_authoritative_chunks_persist_into_rp_chunks(
    session, release, chroma_client, retrieval_config, fake_embedding
):
    pkg = _persist(session, release, chroma_client, retrieval_config, fake_embedding)
    count = len(
        session.execute(
            select(RuleChunkORM).where(RuleChunkORM.rules_package_id == pkg)
        )
        .scalars()
        .all()
    )
    assert count == len(release.members.chunks)


def test_tamper_leaf_content_breaks_digest(
    session, release, chroma_client, retrieval_config, fake_embedding
):
    pkg = _persist(session, release, chroma_client, retrieval_config, fake_embedding)
    row = session.execute(
        select(LedgerLeafORM).where(LedgerLeafORM.package_uuid == pkg).limit(1)
    ).scalar_one()
    row.content = row.content + " TAMPERED"
    session.commit()
    vs = _vstate(session, pkg, chroma_client, retrieval_config, fake_embedding)
    assert not verify_persisted_digest(session, pkg, vs)


def test_tamper_projection_subspan_breaks_digest(
    session, release, chroma_client, retrieval_config, fake_embedding
):
    pkg = _persist(session, release, chroma_client, retrieval_config, fake_embedding)
    row = session.execute(
        select(CorpusProjectionORM)
        .where(CorpusProjectionORM.package_uuid == pkg)
        .limit(1)
    ).scalar_one()
    row.cover_end = row.cover_end + 1
    session.commit()
    vs = _vstate(session, pkg, chroma_client, retrieval_config, fake_embedding)
    assert not verify_persisted_digest(session, pkg, vs)


def test_tamper_reconciliation_findings_breaks_digest(
    session, release, chroma_client, retrieval_config, fake_embedding
):
    pkg = _persist(session, release, chroma_client, retrieval_config, fake_embedding)
    row = session.execute(
        select(ReconciliationORM).where(ReconciliationORM.package_uuid == pkg)
    ).scalar_one()
    findings = dict(row.findings)
    findings["gaps"] = ["fabricated"]
    row.findings = findings
    session.commit()
    vs = _vstate(session, pkg, chroma_client, retrieval_config, fake_embedding)
    assert not verify_persisted_digest(session, pkg, vs)


def _tamper_chunk_provenance_breaks_digest(
    session, release, chroma_client, retrieval_config, fake_embedding, field, newvalue
):
    """DF2: tampering any persisted runtime-visible RuleChunk provenance field
    (source_document / source_locator_type / source_locator_value) must break
    the persisted-corpus digest — those citations are served to callers and must
    be attested, not left free to corrupt silently."""
    pkg = _persist(session, release, chroma_client, retrieval_config, fake_embedding)
    row = session.execute(
        select(RuleChunkORM).where(RuleChunkORM.rules_package_id == pkg).limit(1)
    ).scalar_one()
    setattr(row, field, newvalue)
    session.commit()
    vs = _vstate(session, pkg, chroma_client, retrieval_config, fake_embedding)
    assert not verify_persisted_digest(session, pkg, vs)


def test_tamper_chunk_source_document_breaks_digest(
    session, release, chroma_client, retrieval_config, fake_embedding
):
    _tamper_chunk_provenance_breaks_digest(
        session,
        release,
        chroma_client,
        retrieval_config,
        fake_embedding,
        "source_document",
        "FORGED SOURCE",
    )


def test_tamper_chunk_locator_type_breaks_digest(
    session, release, chroma_client, retrieval_config, fake_embedding
):
    _tamper_chunk_provenance_breaks_digest(
        session,
        release,
        chroma_client,
        retrieval_config,
        fake_embedding,
        "source_locator_type",
        "section",
    )


def test_tamper_chunk_locator_value_breaks_digest(
    session, release, chroma_client, retrieval_config, fake_embedding
):
    _tamper_chunk_provenance_breaks_digest(
        session,
        release,
        chroma_client,
        retrieval_config,
        fake_embedding,
        "source_locator_value",
        "p. 9999",
    )


# --- Persisted reconciliation policy reconstruction (PR #134 P1) --------------
# Reconstruction reads and validates the persisted rp_reconciliation_policies row
# and its cross-references, never FROZEN_POLICY / a caller policy. A missing,
# malformed, deleted, or inconsistent persisted policy fails closed.


def _persist_sql_only(session, release):
    """Persist a finalized release's SQL state (no reindex) and return its pkg.

    The policy-tamper checks below fail closed in ``_load_policy`` *before* any
    vector state is read, so they need no Chroma collection — passing ``{}`` as
    the vector state to ``verify_persisted_digest`` is enough."""
    persist_release(session, release, now=_NOW)
    session.commit()
    return release.release.package_uuid


def test_load_policy_accepts_clean_release_positive_control(
    session, release, chroma_client, retrieval_config, fake_embedding
):
    """Positive control: a clean release round-trips payload -> policy -> hash
    back to the stored hash, passes every cross-check, and verifies — so the
    tamper tests below are rejecting real inconsistencies, not a broken feature."""
    pkg = _persist(session, release, chroma_client, retrieval_config, fake_embedding)
    policy = _load_policy(session, pkg)
    assert policy.policy_version == release.policy.policy_version
    assert policy.projection_roles == release.policy.projection_roles
    assert policy.exclusion_reasons == release.policy.exclusion_reasons
    vs = _vstate(session, pkg, chroma_client, retrieval_config, fake_embedding)
    assert verify_persisted_digest(session, pkg, vs)


def test_deleting_policy_row_fails_closed(session, release):
    pkg = _persist_sql_only(session, release)
    session.execute(
        delete(ReconciliationPolicyORM).where(
            ReconciliationPolicyORM.package_uuid == pkg
        )
    )
    session.commit()
    with pytest.raises(PolicyReconstructionError):
        verify_persisted_digest(session, pkg, {})


def _tamper_policy_row(session, pkg, mutate):
    row = session.execute(
        select(ReconciliationPolicyORM).where(
            ReconciliationPolicyORM.package_uuid == pkg
        )
    ).scalar_one()
    mutate(row)
    session.commit()


def test_tamper_policy_version_fails_closed(session, release):
    pkg = _persist_sql_only(session, release)

    def _m(row):
        row.policy_version = "tampered-version"

    _tamper_policy_row(session, pkg, _m)
    with pytest.raises(PolicyReconstructionError):
        verify_persisted_digest(session, pkg, {})


def test_tamper_policy_hash_fails_closed(session, release):
    pkg = _persist_sql_only(session, release)

    def _m(row):
        row.policy_hash = "0" * 64

    _tamper_policy_row(session, pkg, _m)
    with pytest.raises(PolicyReconstructionError):
        verify_persisted_digest(session, pkg, {})


def test_tamper_policy_payload_fails_closed(session, release):
    pkg = _persist_sql_only(session, release)

    def _m(row):
        payload = copy.deepcopy(row.payload)
        payload["exclusion_reasons"][0]["description"] = "TAMPERED REASON"
        row.payload = payload

    _tamper_policy_row(session, pkg, _m)
    with pytest.raises(PolicyReconstructionError):
        verify_persisted_digest(session, pkg, {})


def test_tamper_reconciliation_policy_cross_reference_fails_closed(session, release):
    """rp_reconciliations.policy_hash must match the policy row."""
    pkg = _persist_sql_only(session, release)
    recon = session.execute(
        select(ReconciliationORM).where(ReconciliationORM.package_uuid == pkg)
    ).scalar_one()
    recon.policy_hash = "0" * 64
    session.commit()
    with pytest.raises(PolicyReconstructionError):
        verify_persisted_digest(session, pkg, {})


def test_tamper_release_policy_cross_reference_fails_closed(session, release):
    """rp_corpus_releases.policy_hash must match the policy row."""
    pkg = _persist_sql_only(session, release)
    rel = session.execute(
        select(CorpusReleaseORM).where(CorpusReleaseORM.package_uuid == pkg)
    ).scalar_one()
    rel.policy_hash = "0" * 64
    session.commit()
    with pytest.raises(PolicyReconstructionError):
        verify_persisted_digest(session, pkg, {})


def test_tamper_transform_config_policy_cross_reference_fails_closed(session, release):
    """The reconstructed policy must match the policy embedded in the stored
    transform configuration."""
    pkg = _persist_sql_only(session, release)
    rel = session.execute(
        select(CorpusReleaseORM).where(CorpusReleaseORM.package_uuid == pkg)
    ).scalar_one()
    tc = copy.deepcopy(rel.transform_config)
    tc["reconciliation_policy"]["policy_version"] = "spoofed"
    rel.transform_config = tc
    session.commit()
    with pytest.raises(PolicyReconstructionError):
        verify_persisted_digest(session, pkg, {})


def test_reuse_fails_closed_on_deleted_policy_row(
    session, candidate, chroma_client, retrieval_config, fake_embedding
):
    """Reuse must not republish against a missing persisted policy — it reports
    an ordinary failed result (not a raw exception) and never reuses."""
    first = _finalize(
        session, candidate, chroma_client, retrieval_config, fake_embedding
    )
    assert first.published and not first.reused

    session.execute(
        delete(ReconciliationPolicyORM).where(
            ReconciliationPolicyORM.package_uuid == candidate.package_uuid
        )
    )
    session.commit()

    result = _finalize(
        session, candidate, chroma_client, retrieval_config, fake_embedding
    )
    assert not result.published and not result.reused
    assert result.gate is not None
    assert any("policy" in f for f in result.gate.failures)


# --- Legacy quarantine (Component L / Acceptance #12) -------------------------


def test_zero_legacy_reachability_in_repo():
    assert check_legacy_reachability(None, REPO_ROOT) == []


def test_legacy_artifact_not_at_default_ingestion_path():
    assert not (REPO_ROOT / "data" / "srd" / "srd_5_2_1_structured.json").exists()


def test_quarantined_evidence_documented_with_hash():
    readme = (REPO_ROOT / "docs" / "legacy" / "quarantine" / "README.md").read_text(
        encoding="utf-8"
    )
    assert LEGACY_ARTIFACT_SHA256 in readme


def test_active_store_flags_a_legacy_package_row(session):
    session.add(
        RulesPackageORM(
            rules_package_id="legacy-1",
            name="D&D SRD 5.2.1",
            system="d20",
            version="5.2.1",
            is_enabled=True,
            publication_status="published",
            published_at=None,
            created_at=_NOW,
            updated_at=_NOW,
        )
    )
    session.commit()
    violations = check_active_store(session)
    assert any("legacy-1" in v for v in violations)


def test_corpus_release_is_not_flagged_as_legacy(
    session, release, chroma_client, retrieval_config, fake_embedding
):
    pkg = _persist(session, release, chroma_client, retrieval_config, fake_embedding)
    # The new corpus release uses a different package name; never flagged.
    assert check_active_store(session) == []
    assert pkg


# --- Chunk runtime-membership verification (PR #134 remediation, req. 4) -----


def test_orphan_enabled_chunk_breaks_runtime_membership_verification(
    session, release, chroma_client, retrieval_config, fake_embedding
):
    """An extra enabled rp_chunks row with no declared projection is invisible
    to the digest but would be served by runtime reads — verification must
    catch it even though the digest itself still matches."""
    pkg = _persist(session, release, chroma_client, retrieval_config, fake_embedding)
    session.add(
        RuleChunkORM(
            chunk_id="orphan-chunk-1",
            rules_package_id=pkg,
            source_id=pkg,
            subsystem="general",
            content="stray content with no declared projection",
            source_document="D&D SRD 5.2.1",
            source_locator_type="page",
            source_locator_value="p. 1",
            is_enabled=True,
            created_at=_NOW,
        )
    )
    session.commit()
    # Read the vector state as it stood before the orphan was added (no reindex),
    # so the digest — scoped to the declared-projection set on both sides — still
    # matches; the orphan is caught only by the separate membership gate.
    vs = _vstate(session, pkg, chroma_client, retrieval_config, fake_embedding)
    assert verify_persisted_digest(session, pkg, vs)  # digest scoped to declared set
    violations = verify_chunk_runtime_membership(session, pkg)
    assert any("orphan-chunk-1" in v for v in violations)


def test_disabled_projected_chunk_breaks_runtime_membership_verification(
    session, release, chroma_client, retrieval_config, fake_embedding
):
    """A declared-projected chunk disabled after persistence would vanish from
    runtime reads while the digest (which doesn't track is_enabled) stays
    unaffected — verification must fail closed on the mismatch."""
    pkg = _persist(session, release, chroma_client, retrieval_config, fake_embedding)
    row = session.execute(
        select(RuleChunkORM).where(RuleChunkORM.rules_package_id == pkg).limit(1)
    ).scalar_one()
    row.is_enabled = False
    session.commit()
    violations = verify_chunk_runtime_membership(session, pkg)
    assert any(row.chunk_id in v and "disabled" in v for v in violations)


def test_disabled_required_source_breaks_runtime_membership_verification(
    session, release, chroma_client, retrieval_config, fake_embedding
):
    """Disabling the source of every declared-projected chunk empties runtime
    reads for the whole package while leaving the digest unaffected."""
    pkg = _persist(session, release, chroma_client, retrieval_config, fake_embedding)
    source = session.execute(
        select(RuleSourceORM).where(RuleSourceORM.rules_package_id == pkg)
    ).scalar_one()
    source.is_enabled = False
    session.commit()
    violations = verify_chunk_runtime_membership(session, pkg)
    assert violations
    assert all("source" in v and "disabled" in v for v in violations)


# --- Candidate construction cannot claim persistence (req. 1) -----------------


def test_candidate_release_carries_no_persistence_claim():
    """CandidateRelease is structurally incapable of claiming persistence: it
    has no report, no release/publication record, and no persisted-corpus
    digest field for a caller-supplied boolean to fake."""
    field_names = {f.name for f in dataclasses.fields(CandidateRelease)}
    assert "report" not in field_names
    assert "release" not in field_names
    assert "persisted_corpus_digest" not in field_names
    assert "evidence_report_hash" not in field_names


# --- finalize_release lifecycle: legacy blocking, idempotency, rollback ------


def test_legacy_active_row_blocks_publication(
    session, candidate, chroma_client, retrieval_config, fake_embedding
):
    session.add(
        RulesPackageORM(
            rules_package_id="legacy-active-1",
            name="D&D SRD 5.2.1",
            system="d20",
            version="5.2.1",
            is_enabled=True,
            publication_status="published",
            published_at=None,
            created_at=_NOW,
            updated_at=_NOW,
        )
    )
    session.commit()

    result = _finalize(
        session, candidate, chroma_client, retrieval_config, fake_embedding
    )

    assert not result.published
    assert result.gate is not None
    assert any("legacy" in f for f in result.gate.failures)
    # No partial content: the new release never became visible.
    assert (
        session.execute(
            select(CorpusReleaseORM).where(
                CorpusReleaseORM.package_uuid == candidate.package_uuid
            )
        ).scalar_one_or_none()
        is None
    )


def test_repeated_finalize_is_idempotent_and_does_not_mutate(
    session, candidate, chroma_client, retrieval_config, fake_embedding
):
    first = _finalize(
        session, candidate, chroma_client, retrieval_config, fake_embedding
    )
    assert first.published and not first.reused and first.artifacts is not None

    second = finalize_release(
        session,
        candidate,
        repo_root=REPO_ROOT,
        now="2026-07-24T00:00:00Z",
        chroma_client=chroma_client,
        retrieval_config=retrieval_config,
        embedding_function=fake_embedding,
    )
    assert second.published and second.reused and second.artifacts is not None
    assert second.artifacts.release.identity == first.artifacts.release.identity

    rows = (
        session.execute(
            select(CorpusReleaseORM).where(
                CorpusReleaseORM.package_uuid == candidate.package_uuid
            )
        )
        .scalars()
        .all()
    )
    assert len(rows) == 1  # not a duplicate-key failure, not a second row

    pkg_row = session.execute(
        select(RulesPackageORM).where(
            RulesPackageORM.rules_package_id == candidate.package_uuid
        )
    ).scalar_one()
    assert pkg_row.published_at == _NOW  # reuse never mutated the publish record


def test_reuse_rejects_inconsistent_package_row_state(
    session, candidate, chroma_client, retrieval_config, fake_embedding
):
    """A published rp_corpus_releases row is not, by itself, sufficient
    evidence for reuse — the rp_packages row must independently confirm
    published+enabled, or reuse must fail closed rather than report success."""
    first = _finalize(
        session, candidate, chroma_client, retrieval_config, fake_embedding
    )
    assert first.published and not first.reused

    pkg_row = session.execute(
        select(RulesPackageORM).where(
            RulesPackageORM.rules_package_id == candidate.package_uuid
        )
    ).scalar_one()
    pkg_row.publication_status = "draft"
    session.commit()

    result = _finalize(
        session, candidate, chroma_client, retrieval_config, fake_embedding
    )
    assert not result.published and not result.reused
    assert result.gate is not None
    assert any("rp_packages" in f for f in result.gate.failures)


def test_reuse_rejects_tampered_release_row(
    session, candidate, chroma_client, retrieval_config, fake_embedding
):
    """Reuse must re-run the full gate against the reconstructed existing
    release, not just the digest — a tampered proof-identity field (here,
    bundle_root_hash) must fail reuse even if the digest itself still
    matches."""
    first = _finalize(
        session, candidate, chroma_client, retrieval_config, fake_embedding
    )
    assert first.published and not first.reused

    release_row = session.execute(
        select(CorpusReleaseORM).where(
            CorpusReleaseORM.package_uuid == candidate.package_uuid
        )
    ).scalar_one()
    release_row.bundle_root_hash = "0" * 64
    session.commit()

    result = _finalize(
        session, candidate, chroma_client, retrieval_config, fake_embedding
    )
    assert not result.published and not result.reused
    assert result.gate is not None
    assert any("bundle_root_hash" in f for f in result.gate.failures)


def test_reuse_rejects_missing_vector_collection(
    session, candidate, chroma_client, retrieval_config, fake_embedding
):
    """DF1: a reuse cannot claim success against missing/stale vectors. After a
    clean publish, dropping the rules-corpus collection must make the next
    reuse attempt fail closed (empty read-back → digest + vector verification
    both fail), not report a successful no-op."""
    from afterworlds.ingestion.corpus.vector_publication import (
        cleanup_vector_collection,
    )

    first = _finalize(
        session, candidate, chroma_client, retrieval_config, fake_embedding
    )
    assert first.published and not first.reused

    cleanup_vector_collection(chroma_client, candidate.package_uuid)

    result = _finalize(
        session, candidate, chroma_client, retrieval_config, fake_embedding
    )
    assert not result.published and not result.reused
    assert result.gate is not None
    assert any("vector" in f or "digest" in f for f in result.gate.failures)


def test_final_gate_failure_does_not_publish_partial_content(
    session, candidate, chroma_client, retrieval_config, fake_embedding
):
    tampered = dataclasses.replace(candidate, transform_config_hash="0" * 64)

    result = _finalize(
        session, tampered, chroma_client, retrieval_config, fake_embedding
    )

    assert not result.published
    assert result.gate is not None and not result.gate.passed
    assert (
        session.execute(
            select(RulesPackageORM).where(
                RulesPackageORM.rules_package_id == tampered.package_uuid
            )
        ).scalar_one_or_none()
        is None
    )
    assert (
        session.execute(
            select(CorpusReleaseORM).where(
                CorpusReleaseORM.package_uuid == tampered.package_uuid
            )
        ).scalar_one_or_none()
        is None
    )
    # No partial vector content either: the collection this attempt wrote was
    # cleaned up on the failed gate.
    leftover = read_actual_vector_state(
        chroma_client, tampered.package_uuid, retrieval_config, fake_embedding
    )
    assert leftover.count == 0


def test_published_package_retrievable_via_rules_package_service(
    session, candidate, chroma_client, retrieval_config, fake_embedding
):
    """A successful ingest publishes both records, and RulesPackageService's
    normal published-only play-time path can retrieve the package and its
    chunks — no draft-visibility backdoor is needed or used."""
    result = _finalize(
        session, candidate, chroma_client, retrieval_config, fake_embedding
    )
    assert result.published and not result.reused

    svc = RulesPackageService(session)
    pkg_id = UUID(candidate.package_uuid)

    detail = svc.get_package_by_id(pkg_id)
    assert detail is not None
    assert detail.publication_status == PublicationStatusEnum.PUBLISHED
    assert detail.sources

    chunks = svc.get_chunks_by_subsystem(pkg_id, RuleSubsystemEnum.GENERAL)
    assert chunks.chunks


# ---------------------------------------------------------------------------
# Cross-store compensation: the fresh-publish vector attempt through a
# successful commit is one exception-safe boundary. Cleanup is armed before the
# reindex and disarmed only after commit, so every unsuccessful exit — failed
# gate, ordinary exception, or commit exception — rolls back SQL and drops this
# attempt's rules-corpus collection. Reuse (verification only) never deletes an
# existing published collection. (PR #134 P2, AGENTS.md transaction/rollback.)
# ---------------------------------------------------------------------------


class _Boom(RuntimeError):
    """Injected fault, distinct from any real error the pipeline can raise."""


def _vcount(chroma_client, pkg, retrieval_config, fake_embedding):
    return read_actual_vector_state(
        chroma_client, pkg, retrieval_config, fake_embedding
    ).count


def _pkg_row_absent(session, pkg):
    return (
        session.execute(
            select(RulesPackageORM).where(RulesPackageORM.rules_package_id == pkg)
        ).scalar_one_or_none()
        is None
    )


def test_exception_during_reconstruction_rolls_back_and_removes_collection(
    session, candidate, chroma_client, retrieval_config, fake_embedding, monkeypatch
):
    """An exception AFTER the reindex wrote the collection (here, during report
    preparation) rolls back SQL, removes the collection, and propagates."""

    def boom(*args, **kwargs):
        raise _Boom("report preparation failed after vector write")

    # build_report runs after reindex_and_verify returns (which verified it wrote
    # N>0 docs), so the collection provably existed → count 0 proves removal.
    monkeypatch.setattr(persistence_mod, "build_report", boom)

    with pytest.raises(_Boom):
        _finalize(session, candidate, chroma_client, retrieval_config, fake_embedding)

    assert _pkg_row_absent(session, candidate.package_uuid)
    assert (
        _vcount(chroma_client, candidate.package_uuid, retrieval_config, fake_embedding)
        == 0
    )


def test_exception_from_run_gate_rolls_back_and_removes_collection(
    session, candidate, chroma_client, retrieval_config, fake_embedding, monkeypatch
):
    """An exception raised by run_gate receives the same compensation."""

    def boom(*args, **kwargs):
        raise _Boom("gate execution failed")

    monkeypatch.setattr(persistence_mod, "run_gate", boom)

    with pytest.raises(_Boom):
        _finalize(session, candidate, chroma_client, retrieval_config, fake_embedding)

    assert _pkg_row_absent(session, candidate.package_uuid)
    assert (
        _vcount(chroma_client, candidate.package_uuid, retrieval_config, fake_embedding)
        == 0
    )


def test_commit_exception_rolls_back_and_removes_collection(
    session, candidate, chroma_client, retrieval_config, fake_embedding, monkeypatch
):
    """A session.commit() exception (the last step, after the gate passed and the
    publish mutations were applied) rolls back SQL, removes the collection, and
    propagates — compensation is not disarmed until commit actually returns."""

    def boom():
        raise _Boom("commit failed")

    # Only the publish commits in this path (reindex_from_sql / legacy check do
    # not commit), so this fires exactly at the publication commit.
    monkeypatch.setattr(session, "commit", boom)

    with pytest.raises(_Boom):
        _finalize(session, candidate, chroma_client, retrieval_config, fake_embedding)

    assert _pkg_row_absent(session, candidate.package_uuid)
    assert (
        _vcount(chroma_client, candidate.package_uuid, retrieval_config, fake_embedding)
        == 0
    )


# The "normal failed gate leaves neither SQL rows nor vectors" case (an ordinary
# FinalizeResult, no exception) is already proven by
# test_final_gate_failure_does_not_publish_partial_content above; not duplicated
# here (each case does a full-corpus reindex).


def test_reuse_verification_exception_does_not_delete_published_collection(
    session, candidate, chroma_client, retrieval_config, fake_embedding, monkeypatch
):
    """A reuse-path verification exception must NOT delete the previously
    published collection (reuse verifies only, never compensates); and a
    successful fresh commit retains the collection."""
    first = _finalize(
        session, candidate, chroma_client, retrieval_config, fake_embedding
    )
    assert first.published and not first.reused
    published_count = _vcount(
        chroma_client, candidate.package_uuid, retrieval_config, fake_embedding
    )
    assert published_count > 0  # successful fresh commit retains the collection

    def boom(*args, **kwargs):
        raise _Boom("reuse verification failed")

    monkeypatch.setattr(persistence_mod, "verify_only", boom)

    with pytest.raises(_Boom):
        _finalize(session, candidate, chroma_client, retrieval_config, fake_embedding)

    # The published collection and SQL row both survive — reuse never drops them.
    assert (
        _vcount(chroma_client, candidate.package_uuid, retrieval_config, fake_embedding)
        == published_count
    )
    assert not _pkg_row_absent(session, candidate.package_uuid)
