"""Persistence, tamper-detection, and legacy-quarantine tests — Issue 5c.

Maps to Acceptance #1/#8 (persisted-corpus digest round-trip), the tamper-
detection test requirement, and Acceptance #12 (legacy zero-reachability).
"""

from __future__ import annotations

from sqlalchemy import select

from afterworlds.ingestion.corpus.bundle import persisted_corpus_payload
from afterworlds.ingestion.corpus.persistence import (
    persist_release,
    reconstruct_payload,
    verify_persisted_digest,
)
from afterworlds.ingestion.corpus.quarantine import (
    LEGACY_ARTIFACT_SHA256,
    check_active_store,
    check_legacy_reachability,
)
from afterworlds.persistence.orm.corpus import (
    CorpusProjectionORM,
    LedgerLeafORM,
    ReconciliationORM,
)
from afterworlds.persistence.orm.rules_package import RuleChunkORM, RulesPackageORM

from .conftest import REPO_ROOT

_NOW = "2026-07-23T00:00:00Z"


def _persist(session, release):
    persist_release(session, release, now=_NOW)
    session.commit()
    return release.release.package_uuid


def test_persist_round_trip_digest_matches(session, release):
    pkg = _persist(session, release)
    assert verify_persisted_digest(session, pkg)


def test_reconstructed_payload_equals_in_memory(session, release):
    pkg = _persist(session, release)
    in_mem = persisted_corpus_payload(
        pkg,
        release.release.release_version,
        release.ledger,
        release.members,
        release.reconciliation,
        release.policy,
    )
    assert reconstruct_payload(session, pkg) == in_mem


def test_authoritative_chunks_persist_into_rp_chunks(session, release):
    pkg = _persist(session, release)
    count = len(
        session.execute(
            select(RuleChunkORM).where(RuleChunkORM.rules_package_id == pkg)
        )
        .scalars()
        .all()
    )
    assert count == len(release.members.chunks)


def test_tamper_leaf_content_breaks_digest(session, release):
    pkg = _persist(session, release)
    row = session.execute(
        select(LedgerLeafORM).where(LedgerLeafORM.package_uuid == pkg).limit(1)
    ).scalar_one()
    row.content = row.content + " TAMPERED"
    session.commit()
    assert not verify_persisted_digest(session, pkg)


def test_tamper_projection_subspan_breaks_digest(session, release):
    pkg = _persist(session, release)
    row = session.execute(
        select(CorpusProjectionORM)
        .where(CorpusProjectionORM.package_uuid == pkg)
        .limit(1)
    ).scalar_one()
    row.cover_end = row.cover_end + 1
    session.commit()
    assert not verify_persisted_digest(session, pkg)


def test_tamper_reconciliation_findings_breaks_digest(session, release):
    pkg = _persist(session, release)
    row = session.execute(
        select(ReconciliationORM).where(ReconciliationORM.package_uuid == pkg)
    ).scalar_one()
    findings = dict(row.findings)
    findings["gaps"] = ["fabricated"]
    row.findings = findings
    session.commit()
    assert not verify_persisted_digest(session, pkg)


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


def test_corpus_release_is_not_flagged_as_legacy(session, release):
    pkg = _persist(session, release)
    # The new corpus release uses a different package name; never flagged.
    assert check_active_store(session) == []
    assert pkg
