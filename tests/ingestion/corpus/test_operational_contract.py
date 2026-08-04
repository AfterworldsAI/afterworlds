"""Versioned downstream corpus trust seam — CRD Issue 5c (#145)."""

from __future__ import annotations

import pytest
from sqlalchemy import delete, select

from afterworlds.ingestion.corpus.operational import (
    CORPUS_CONTRACT_VERSION,
    OperationalCorpusVerificationError,
    load_verified_operational_corpus,
)
from afterworlds.ingestion.corpus.persistence import persist_release
from afterworlds.persistence.orm.corpus import (
    CorpusProjectionORM,
    CorpusReleaseORM,
    LedgerLeafORM,
)
from afterworlds.persistence.orm.rules_package import RuleChunkORM, RulesPackageORM

_NOW = "2026-08-03T00:00:00Z"


def _published(session, release):  # type: ignore[no-untyped-def]
    persist_release(session, release, now=_NOW)
    package_uuid = release.release.package_uuid
    package = session.get(RulesPackageORM, package_uuid)
    corpus = session.get(CorpusReleaseORM, package_uuid)
    assert package is not None and corpus is not None
    package.publication_status = "published"
    corpus.publication_status = "published"
    session.commit()
    return package_uuid


def _load(session, release):  # type: ignore[no-untyped-def]
    identity = release.release.identity
    return load_verified_operational_corpus(
        session,
        release.release.package_uuid,
        release_version=release.release.release_version,
        authoritative_source_hash=identity.authoritative_source_hash,
        transform_config_hash=identity.transform_config_hash,
        bundle_root_hash=identity.bundle_root_hash,
        persisted_corpus_digest=identity.persisted_corpus_digest,
        supported_contract_versions=frozenset({CORPUS_CONTRACT_VERSION}),
    )


def test_honest_release_returns_the_exact_downstream_snapshot(session, compact_release):
    _published(session, compact_release)
    snapshot = _load(session, compact_release)
    assert snapshot.corpus_contract_version == CORPUS_CONTRACT_VERSION
    assert len(snapshot.leaves) == compact_release.reconciliation.represented_leaves
    assert {chunk.chunk_id for chunk in snapshot.chunks} == {
        chunk.chunk_id for chunk in compact_release.members.chunks
    }


@pytest.mark.parametrize(
    "mutation",
    ["leaf_content", "chunk_content", "projection_coverage", "missing_chunk"],
)
def test_sqlite_corpus_mutation_fails_direct_integrity(
    session, compact_release, mutation
):
    package_uuid = _published(session, compact_release)
    if mutation == "leaf_content":
        row = session.execute(
            select(LedgerLeafORM)
            .where(
                LedgerLeafORM.package_uuid == package_uuid,
                LedgerLeafORM.disposition == "represented",
            )
            .limit(1)
        ).scalar_one()
        row.content += " tampered"
    elif mutation == "chunk_content":
        row = session.execute(
            select(RuleChunkORM)
            .where(RuleChunkORM.rules_package_id == package_uuid)
            .limit(1)
        ).scalar_one()
        row.content += " tampered"
    elif mutation == "projection_coverage":
        row = session.execute(
            select(CorpusProjectionORM)
            .where(CorpusProjectionORM.package_uuid == package_uuid)
            .limit(1)
        ).scalar_one()
        row.cover_end += 1
    else:
        chunk_id = session.execute(
            select(RuleChunkORM.chunk_id)
            .where(RuleChunkORM.rules_package_id == package_uuid)
            .limit(1)
        ).scalar_one()
        session.execute(delete(RuleChunkORM).where(RuleChunkORM.chunk_id == chunk_id))
    session.commit()

    with pytest.raises(OperationalCorpusVerificationError):
        _load(session, compact_release)


def test_unpublished_or_unsupported_release_fails_closed(session, compact_release):
    package_uuid = _published(session, compact_release)
    row = session.get(CorpusReleaseORM, package_uuid)
    assert row is not None
    row.corpus_contract_version = "future-contract"
    session.commit()
    with pytest.raises(OperationalCorpusVerificationError, match="unsupported"):
        _load(session, compact_release)

    row.corpus_contract_version = CORPUS_CONTRACT_VERSION
    row.publication_status = "draft"
    session.commit()
    with pytest.raises(OperationalCorpusVerificationError, match="not published"):
        _load(session, compact_release)


def test_diagnostic_report_is_not_downstream_authority(session, compact_release):
    package_uuid = _published(session, compact_release)
    row = session.get(CorpusReleaseORM, package_uuid)
    assert row is not None
    row.report_payload = {"diagnostic": "new shape"}
    row.evidence_report_hash = "not consulted by the operational seam"
    row.corpus_report_reference = "also diagnostic"
    session.commit()
    assert _load(session, compact_release).package_uuid == package_uuid
