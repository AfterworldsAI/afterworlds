"""Persistence, tamper-detection, and legacy-quarantine tests — Issue 5c.

Maps to Acceptance #1/#8 (persisted-corpus digest round-trip), the tamper-
detection test requirement, Acceptance #12 (legacy zero-reachability), and the
PR #134 remediation regression set: DB-grounded final gating, fail-closed
chunk-runtime-membership verification, idempotent republication, and no
partial content on a failed gate.
"""

from __future__ import annotations

import dataclasses
from uuid import UUID

from sqlalchemy import select

from afterworlds.ingestion.corpus.bundle import persisted_corpus_payload
from afterworlds.ingestion.corpus.persistence import (
    finalize_release,
    persist_release,
    reconstruct_payload,
    verify_chunk_runtime_membership,
    verify_persisted_digest,
)
from afterworlds.ingestion.corpus.pipeline import CandidateRelease
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
