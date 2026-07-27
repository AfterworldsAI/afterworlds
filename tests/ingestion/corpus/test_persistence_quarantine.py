"""Persistence, tamper-detection, and pre-release clean-baseline tests — Issue 5c.

Maps to Acceptance #1/#8 (persisted-corpus digest round-trip), the tamper-
detection test requirement, and the PR #134 remediation regression set:
DB-grounded final gating, fail-closed chunk-runtime-membership verification,
idempotent republication, and no partial content on a failed gate.

The former strict cross-store quarantine (repo/runtime zero-reachability scan +
publication-gate legacy check) was superseded by a breaking pre-release clean
baseline (Issue 5c Rev7 / Issue 18 Rev6): the obsolete SRD JSON and its
machinery are deleted, and the incomplete legacy SQL package is removed by
migration 0018 rather than blocked at publication time.
"""

from __future__ import annotations

import copy
import dataclasses
import re
from uuid import UUID

import pytest
from sqlalchemy import delete, event, select

import afterworlds.ingestion.corpus.persistence as persistence_mod
from afterworlds.ingestion.corpus.bundle import (
    build_bundle,
    derive_package_uuid,
    derive_release_version,
    persisted_corpus_payload,
    reconciliation_hash,
    transform_config_hash,
    transform_config_payload,
)
from afterworlds.ingestion.corpus.pdf_source import PDF_SHA256, extraction_config
from afterworlds.ingestion.corpus.persistence import (
    _finalize_core,
    _load_policy,
    finalize_release,
    persist_release,
    reconstruct_payload,
    verify_chunk_runtime_membership,
    verify_persisted_digest,
    verify_persisted_page_coverage,
    verify_single_source,
)
from afterworlds.ingestion.corpus.pipeline import CandidateRelease
from afterworlds.ingestion.corpus.policy import FROZEN_POLICY, PolicyReconstructionError
from afterworlds.ingestion.corpus.reconcile import reconcile
from afterworlds.ingestion.corpus.transform import build_corpus
from afterworlds.ingestion.corpus.vector_publication import read_actual_vector_state
from afterworlds.models.enums import PublicationStatusEnum, RuleSubsystemEnum
from afterworlds.models.retrieval import rules_corpus_vector_identity
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
from afterworlds.pipeline.retrieval.config import RetrievalMemoryConfig
from afterworlds.pipeline.retrieval.rules_corpus_service import RulesCorpusService
from afterworlds.services.rules_package import RulesPackageService

from .conftest import REPO_ROOT

_NOW = "2026-07-23T00:00:00Z"


# ---------------------------------------------------------------------------
# Performance: in THIS module `candidate`/`release` are deliberately the COMPACT
# (six-canary-page) fixtures — ~250 chunks instead of 13,658 — so the many
# policy/tamper/rollback/membership/fault-injection tests exercise the genuine,
# unmocked finalize/gate/persist/reindex path without repeatedly rebuilding the
# full SRD. The small number of tests that must prove the COMPLETE corpus persists
# /reconstructs/digests/gates/publishes/reuses request ``full_candidate`` /
# ``full_release`` explicitly (see test_persist_round_trip_digest_matches,
# test_repeated_finalize_is_idempotent_and_does_not_mutate,
# test_published_package_retrievable_via_rules_package_service). The shadows depend
# on the conftest compact fixtures, which depend on ``full_candidate`` (never
# shadowed) — no recursion.
# ---------------------------------------------------------------------------


@pytest.fixture()
def candidate(compact_candidate):  # type: ignore[no-untyped-def]
    return compact_candidate


@pytest.fixture()
def release(compact_release):  # type: ignore[no-untyped-def]
    return compact_release


def _finalize(session, candidate, chroma_client, retrieval_config, fake_embedding):
    """Publish *candidate* through the real cross-store persist/gate lifecycle.

    Uses the private ``_finalize_core`` seam — the sanctioned lower-layer entry
    that runs the genuine persist→reconstruct→digest→gate→publish machinery
    without the public completeness guard — so these lifecycle/rollback/reuse
    tests can exercise it on the COMPACT (six-page) corpus. The public
    ``finalize_release`` completeness guard is proven separately by the negative
    control and the completeness regressions below (PR #134)."""
    return _finalize_core(
        session,
        candidate,
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
    session, full_release, chroma_client, retrieval_config, fake_embedding
):
    """Full-SRD integration: the complete corpus persists, reconstructs, and
    digest-verifies (with a full vector reindex)."""
    pkg = _persist(
        session, full_release, chroma_client, retrieval_config, fake_embedding
    )
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
        release.sources,
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


# --- Persisted source membership bound into the release proof (PR #134 DF3) ---
# The digest binds every chunk's actual source_id AND the complete canonically
# ordered logical RuleSource set (id/package/name/category/precedence/enabled,
# excluding created_at). The Issue-5c single-source invariant (exactly one
# source, source_id == package_uuid, expected metadata, enabled, every chunk
# assigned to it) is verified from persisted state. Extra/missing/altered/
# disabled/reassigned source state fails both.


def _second_source(session, pkg):
    """Insert a second, otherwise-valid RuleSource for *pkg* and return its id."""
    sid = "1" * 36
    session.add(
        RuleSourceORM(
            source_id=sid,
            rules_package_id=pkg,
            name="Interloper Source",
            category="supplement",
            precedence_rank=2,
            is_enabled=True,
            created_at=_NOW,
        )
    )
    session.flush()
    return sid


def test_clean_source_membership_positive_control(
    session, release, chroma_client, retrieval_config, fake_embedding
):
    """Untampered: exactly one authoritative source and a matching digest."""
    pkg = _persist(session, release, chroma_client, retrieval_config, fake_embedding)
    vs = _vstate(session, pkg, chroma_client, retrieval_config, fake_embedding)
    assert verify_single_source(session, pkg) == ()
    assert verify_persisted_digest(session, pkg, vs)


def test_extra_source_fails_invariant_and_digest(
    session, release, chroma_client, retrieval_config, fake_embedding
):
    pkg = _persist(session, release, chroma_client, retrieval_config, fake_embedding)
    _second_source(session, pkg)
    session.commit()
    vs = _vstate(session, pkg, chroma_client, retrieval_config, fake_embedding)
    assert verify_single_source(session, pkg)  # non-empty violations
    assert not verify_persisted_digest(session, pkg, vs)


def test_reassigned_chunk_source_fails_invariant_and_digest(
    session, release, chroma_client, retrieval_config, fake_embedding
):
    pkg = _persist(session, release, chroma_client, retrieval_config, fake_embedding)
    sid = _second_source(session, pkg)  # a valid FK target to reassign to
    chunk = session.execute(
        select(RuleChunkORM).where(RuleChunkORM.rules_package_id == pkg).limit(1)
    ).scalar_one()
    chunk.source_id = sid
    session.commit()
    vs = _vstate(session, pkg, chroma_client, retrieval_config, fake_embedding)
    violations = verify_single_source(session, pkg)
    assert any("other than the single authoritative source" in v for v in violations)
    assert not verify_persisted_digest(session, pkg, vs)


@pytest.mark.parametrize(
    "field,newvalue,marker",
    [
        ("name", "Forged Name", "name"),
        ("category", "supplement", "category"),
        ("precedence_rank", 7, "precedence_rank"),
        ("is_enabled", False, "disabled"),
    ],
)
def test_altered_source_metadata_fails_invariant_and_digest(
    session,
    release,
    chroma_client,
    retrieval_config,
    fake_embedding,
    field,
    newvalue,
    marker,
):
    pkg = _persist(session, release, chroma_client, retrieval_config, fake_embedding)
    source = session.execute(
        select(RuleSourceORM).where(RuleSourceORM.rules_package_id == pkg)
    ).scalar_one()
    setattr(source, field, newvalue)
    session.commit()
    vs = _vstate(session, pkg, chroma_client, retrieval_config, fake_embedding)
    assert any(marker in v for v in verify_single_source(session, pkg))
    assert not verify_persisted_digest(session, pkg, vs)


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


# --- Pre-release clean baseline: obsolete SRD artifact retired (R18) ----------
# Issue 5c Rev7 / Issue 18 Rev6 replaced the strict cross-store quarantine
# (repo/runtime zero-reachability scan + publication-gate legacy check) with a
# breaking pre-release clean baseline: the obsolete structured JSON and every
# production loader/reader/default/fallback for it are deleted (preserved only in
# Git history + concise docs). The former reachability *machinery* is retired; its
# intent — no runnable path reads the legacy artifact — is now enforced by absence.

_BANNED = re.compile(
    r"srd_5_2_1_structured|corpus\.quarantine|check_legacy_reachability"
)


def test_obsolete_srd_artifact_absent_from_repo():
    """Regression 1: the obsolete JSON is gone from its old default path AND the
    former quarantine location (retained only in Git history)."""
    assert not (REPO_ROOT / "data" / "srd" / "srd_5_2_1_structured.json").exists()
    assert not (
        REPO_ROOT
        / "docs"
        / "legacy"
        / "quarantine"
        / "srd_5_2_1_structured.legacy.json"
    ).exists()


def test_no_production_reference_to_obsolete_artifact_or_retired_quarantine():
    """Regression 1: no production code (src/ or scripts/) references the obsolete
    artifact or the retired quarantine module/reachability checker. This replaces
    the deleted repo-scan reachability checker with an absence guarantee."""
    hits = []
    for base in ("src", "scripts"):
        root = REPO_ROOT / base
        if not root.exists():
            continue
        for path in root.rglob("*.py"):
            if _BANNED.search(path.read_text(encoding="utf-8")):
                hits.append(str(path.relative_to(REPO_ROOT)))
    assert (
        hits == []
    ), f"obsolete-artifact / retired-quarantine references remain: {hits}"


def test_migration_0018_deletes_incomplete_package_and_dependent_rows(tmp_path):
    """Regression 2: the SQL migration removes the incomplete legacy package and
    its dependent RuleChunk/MechanicalEntity/manifest rows (FK cascade), and never
    touches the Issue-5c corpus release (different name/version)."""
    from afterworlds.persistence.database import (
        create_engine as _create_engine,
    )
    from afterworlds.persistence.database import (
        create_session_factory as _factory,
    )

    db_url = f"sqlite:///{tmp_path / 'baseline.db'}"
    # Bring a fresh DB to the revision *before* 0018, seed the legacy package +
    # dependent rows, then run 0018 and confirm the targeted deletion.
    from alembic.config import Config

    from alembic import command

    cfg = Config(str(REPO_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(REPO_ROOT / "alembic"))
    cfg.set_main_option("sqlalchemy.url", db_url)
    command.upgrade(cfg, "0017")

    eng = _create_engine(db_url)

    @event.listens_for(eng, "connect")
    def _fk(dbapi, _rec):  # type: ignore[no-untyped-def]
        dbapi.execute("PRAGMA foreign_keys=ON")

    sess = _factory(eng)()
    sess.add(
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
    sess.flush()
    sess.add(
        RuleSourceORM(
            source_id="legacy-src-1",
            rules_package_id="legacy-1",
            name="legacy",
            category="core_rulebook",
            precedence_rank=1,
            is_enabled=True,
            created_at=_NOW,
        )
    )
    sess.flush()
    sess.add(
        RuleChunkORM(
            chunk_id="legacy-chunk-1",
            rules_package_id="legacy-1",
            source_id="legacy-src-1",
            subsystem="combat",
            content="obsolete",
            source_document="legacy",
            source_locator_type="page",
            source_locator_value="p. 1",
            is_enabled=True,
            created_at=_NOW,
        )
    )
    sess.commit()
    sess.close()
    eng.dispose()

    command.upgrade(cfg, "0018")

    sess = _factory(_create_engine(db_url))()
    assert (
        sess.execute(
            select(RulesPackageORM).where(
                RulesPackageORM.rules_package_id == "legacy-1"
            )
        ).scalar_one_or_none()
        is None
    )
    assert (
        sess.execute(
            select(RuleChunkORM).where(RuleChunkORM.chunk_id == "legacy-chunk-1")
        ).scalar_one_or_none()
        is None
    )
    sess.close()


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


# --- Authoritative-source completeness proof (PR #134 completeness defect) ----
# The public finalize_release rejects a candidate that does not exhaustively
# match the exact 364-page authoritative PDF — before any SQL or Chroma
# mutation, so a rejected candidate leaves no package/release/vector state. The
# six-canary-page compact candidate (which passes the internal _finalize_core
# seam) is the canonical negative control: it must NOT pass production
# finalization.


def _finalize_public(
    session, candidate, chroma_client, retrieval_config, fake_embedding
):
    return finalize_release(
        session,
        candidate,
        now=_NOW,
        chroma_client=chroma_client,
        retrieval_config=retrieval_config,
        embedding_function=fake_embedding,
    )


def _assert_left_no_state(
    session, chroma_client, pkg, retrieval_config, fake_embedding
):
    assert (
        session.execute(
            select(RulesPackageORM).where(RulesPackageORM.rules_package_id == pkg)
        ).scalar_one_or_none()
        is None
    )
    assert (
        session.execute(
            select(CorpusReleaseORM).where(CorpusReleaseORM.package_uuid == pkg)
        ).scalar_one_or_none()
        is None
    )
    # No vector collection was created (guard runs before any reindex).
    assert (
        read_actual_vector_state(
            chroma_client, pkg, retrieval_config, fake_embedding
        ).count
        == 0
    )


def test_six_canary_page_candidate_is_rejected_by_production_finalize(
    session, compact_candidate, chroma_client, retrieval_config, fake_embedding
):
    """Negative control: the compact six-page candidate carries the real PDF hash
    yet does not exhaust the authoritative PDF, so production finalization must
    reject it and persist nothing (PR #134 completeness proof)."""
    result = _finalize_public(
        session, compact_candidate, chroma_client, retrieval_config, fake_embedding
    )
    assert not result.published and not result.reused
    assert result.gate is not None and not result.gate.passed
    assert any(
        "extraction hash" in f or "page sequence" in f or "extracted pages" in f
        for f in result.gate.failures
    )
    _assert_left_no_state(
        session,
        chroma_client,
        compact_candidate.package_uuid,
        retrieval_config,
        fake_embedding,
    )


def _corruption_cases(full_pages):
    """Return (id, corrupted-pages) for each completeness failure mode."""
    omitted = full_pages[:-1]
    duplicated = full_pages + [full_pages[-1]]
    reordered = list(full_pages)
    reordered[10], reordered[20] = reordered[20], reordered[10]
    # Substituted: keep the exact page sequence but swap one page's *content*
    # (lines) for another page's, so only the content hash diverges.
    substituted = list(full_pages)
    substituted[30] = dataclasses.replace(substituted[30], lines=substituted[31].lines)
    # Geometry-only: same page text, but a moved line coordinate (R15 F2) — must
    # still be rejected before any store mutation.
    geometry = list(full_pages)
    pg = geometry[40]
    moved = dataclasses.replace(pg.lines[0], top=pg.lines[0].top + 5.0)
    geometry[40] = dataclasses.replace(pg, lines=(moved, *pg.lines[1:]))
    return [
        ("omitted", omitted),
        ("duplicated", duplicated),
        ("reordered", reordered),
        ("substituted", substituted),
        ("geometry", geometry),
    ]


def test_persisted_page_coverage_flags_partial_corpus(
    session, release, chroma_client, retrieval_config, fake_embedding
):
    """Reuse-path DB-grounded complement: a partial persisted corpus (the compact
    six-page release) does not cover printed pages 1..364, so the reuse-path page
    coverage check flags it (PR #134)."""
    pkg = _persist(session, release, chroma_client, retrieval_config, fake_embedding)
    assert verify_persisted_page_coverage(session, pkg)  # non-empty violations


@pytest.mark.parametrize(
    "mode",
    ["omitted", "duplicated", "reordered", "substituted", "geometry"],
)
def test_completeness_rejects_page_corruption_and_leaves_no_state(
    session,
    full_candidate,
    chroma_client,
    retrieval_config,
    fake_embedding,
    mode,
):
    """An omitted, duplicated, reordered, or substituted page fails production
    finalization before any mutation (PR #134). Only ``.pages`` is corrupted; the
    guard runs on that, so the rest of the (valid) candidate never persists."""
    cases = dict(_corruption_cases(full_candidate.pages))
    corrupted = dataclasses.replace(full_candidate, pages=cases[mode])
    result = _finalize_public(
        session, corrupted, chroma_client, retrieval_config, fake_embedding
    )
    assert not result.published and not result.reused
    assert result.gate is not None and not result.gate.passed
    _assert_left_no_state(
        session,
        chroma_client,
        corrupted.package_uuid,
        retrieval_config,
        fake_embedding,
    )


# --- finalize_release lifecycle: idempotency, rollback -----------------------
# (Under the pre-release clean baseline the publication-time legacy-reachability
#  gate is retired; the incomplete legacy package is removed by migration 0018 —
#  see test_migration_0018_deletes_incomplete_package_and_dependent_rows.)


def test_report_schema_ok_fails_closed_on_bad_schema():
    """R17 unit: ``_report_schema_ok`` is the reuse-path backstop for the evidence-
    report schema. Current + matching (report AND transform config) → True;
    obsolete, contradictory, missing, or malformed → False (fail closed)."""
    from afterworlds.ingestion.corpus.persistence import _report_schema_ok
    from afterworlds.ingestion.corpus.report import EVIDENCE_REPORT_SCHEMA_VERSION as V

    assert _report_schema_ok(
        {"report_version": V}, {"evidence_report_schema_version": V}
    )
    # obsolete pre-R16 report version
    assert not _report_schema_ok(
        {"report_version": "5c-evidence-1"}, {"evidence_report_schema_version": V}
    )
    # contradictory: report current, transform config stale or absent
    assert not _report_schema_ok({"report_version": V}, {})
    assert not _report_schema_ok(
        {"report_version": V}, {"evidence_report_schema_version": "5c-evidence-1"}
    )
    # missing report version
    assert not _report_schema_ok({}, {"evidence_report_schema_version": V})
    # malformed payloads
    assert not _report_schema_ok(None, {"evidence_report_schema_version": V})
    assert not _report_schema_ok({"report_version": V}, None)


def test_reuse_rejects_obsolete_evidence_report_schema(
    session, candidate, chroma_client, retrieval_config, fake_embedding
):
    """R17: reuse fails closed when the persisted evidence report is a valid but
    *obsolete* (pre-R16) schema whose stored hash still matches — the case the
    report-hash check cannot catch. Simulate a pre-R16 ``report_version`` on the
    published release (recomputing the stored hash so the gate's hash check passes,
    isolating the schema backstop) and assert the reuse attempt surfaces the schema
    failure and does not reuse."""
    from afterworlds.ingestion.corpus.report import EvidenceReport, report_hash

    first = _finalize(
        session, candidate, chroma_client, retrieval_config, fake_embedding
    )
    assert first.published and not first.reused
    row = session.execute(
        select(CorpusReleaseORM).where(
            CorpusReleaseORM.package_uuid == candidate.package_uuid
        )
    ).scalar_one()
    payload = dict(row.report_payload)
    payload["report_version"] = "5c-evidence-1"  # obsolete pre-R16 shape marker
    row.report_payload = payload
    # Keep the stored hash consistent with the tampered payload so the gate's
    # evidence_report_hash check passes — this isolates the schema backstop.
    row.evidence_report_hash = report_hash(
        EvidenceReport(payload=payload, persisted=True)
    )
    session.commit()

    result = _finalize(
        session, candidate, chroma_client, retrieval_config, fake_embedding
    )
    assert not result.published and not result.reused
    assert result.gate is not None
    assert any("schema version" in f for f in result.gate.failures)


def test_repeated_finalize_is_idempotent_and_does_not_mutate(
    session, full_candidate, chroma_client, retrieval_config, fake_embedding
):
    """Full-SRD integration: the complete corpus is finalized/gated/published,
    then a repeat finalize is an idempotent verified reuse (current schema on both
    sides — R17 byte-identical reuse positive control)."""
    first = _finalize(
        session, full_candidate, chroma_client, retrieval_config, fake_embedding
    )
    assert first.published and not first.reused and first.artifacts is not None

    second = finalize_release(
        session,
        full_candidate,
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
                CorpusReleaseORM.package_uuid == full_candidate.package_uuid
            )
        )
        .scalars()
        .all()
    )
    assert len(rows) == 1  # not a duplicate-key failure, not a second row

    pkg_row = session.execute(
        select(RulesPackageORM).where(
            RulesPackageORM.rules_package_id == full_candidate.package_uuid
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
    session, full_candidate, chroma_client, retrieval_config, fake_embedding
):
    """Full-SRD integration: a successful ingest of the complete corpus publishes
    both records, and RulesPackageService's normal published-only play-time path
    can retrieve the package and its chunks (incl. a GENERAL-subsystem slice) —
    no draft-visibility backdoor is needed or used."""
    result = _finalize(
        session, full_candidate, chroma_client, retrieval_config, fake_embedding
    )
    assert result.published and not result.reused

    svc = RulesPackageService(session)
    pkg_id = UUID(full_candidate.package_uuid)

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


# --- Full-persistence release coexistence (PR #134 P1) ------------------------
# Output chunk IDs are now scoped to the immutable package_uuid, so two releases
# differing only in an identity-bearing input coexist in the global rp_chunks PK.
# These prove coexistence through the ACTUAL chunk/projection rows, not rp_packages
# alone (the package-only version-key tests live in test_release_identity.py /
# test_vector_identity.py).

_COEXIST_MODEL = "coexistence-test-model-v2"


def _variant_candidate(candidate, embedding_model_id):
    """A CandidateRelease differing from *candidate* only in the embedding model
    (an identity-bearing input) — reuses its expensive pages/ledger and recomputes
    only the identity-scoped parts (package_uuid, chunk IDs, reconciliation,
    bundle)."""
    ex = extraction_config()
    vid = rules_corpus_vector_identity(embedding_model_id)
    tconfig = transform_config_payload(ex, FROZEN_POLICY, vid)
    thash = transform_config_hash(ex, FROZEN_POLICY, vid)
    pkg = derive_package_uuid(PDF_SHA256, thash)
    ver = derive_release_version(PDF_SHA256, thash)
    members = build_corpus(candidate.ledger, pkg)
    recon = reconcile(candidate.ledger, members, FROZEN_POLICY)
    bundle = build_bundle(candidate.ledger, members, recon)
    return CandidateRelease(
        pages=candidate.pages,
        ledger=candidate.ledger,
        members=members,
        reconciliation=recon,
        policy=FROZEN_POLICY,
        bundle=bundle,
        package_uuid=pkg,
        release_version=ver,
        authoritative_source_hash=PDF_SHA256,
        transform_config_hash=thash,
        transform_config=tconfig,
        ledger_hash=candidate.ledger_hash,
        policy_hash=candidate.policy_hash,
        reconciliation_hash=reconciliation_hash(recon),
    )


def _chunk_ids(session, pkg):
    return set(
        session.execute(
            select(RuleChunkORM.chunk_id).where(RuleChunkORM.rules_package_id == pkg)
        ).scalars()
    )


def test_two_releases_coexist_fully_persisted_with_disjoint_chunks(
    session, candidate, chroma_client, retrieval_config, fake_embedding
):
    """A model-only identity change: both releases persist fully (chunks +
    projections) in ONE database with no IntegrityError; chunk sets are complete
    and disjoint; the predecessor is untouched; both digests/vectors verify."""
    # Release A — the default-model candidate.
    a = _finalize(session, candidate, chroma_client, retrieval_config, fake_embedding)
    assert a.published and not a.reused

    # Release B — same leaves, embedding-model-only difference → new package_uuid,
    # release-scoped chunk IDs.
    candidate_b = _variant_candidate(candidate, _COEXIST_MODEL)
    assert candidate_b.package_uuid != candidate.package_uuid
    assert candidate_b.release_version != candidate.release_version
    config_b = RetrievalMemoryConfig(embedding_model_id=_COEXIST_MODEL)
    b = _finalize(session, candidate_b, chroma_client, config_b, fake_embedding)
    assert b.published and not b.reused  # full persistence: no IntegrityError

    # Both chunk sets complete and disjoint (same leaves -> same count).
    ids_a = _chunk_ids(session, candidate.package_uuid)
    ids_b = _chunk_ids(session, candidate_b.package_uuid)
    assert len(ids_a) == len(candidate.members.chunks)
    assert len(ids_b) == len(candidate_b.members.chunks)
    assert len(ids_a) == len(ids_b)
    assert ids_a.isdisjoint(ids_b)

    # Projections for both packages persist and reference their own chunk IDs.
    proj_a = set(
        session.execute(
            select(CorpusProjectionORM.chunk_id).where(
                CorpusProjectionORM.package_uuid == candidate.package_uuid
            )
        ).scalars()
    )
    proj_b = set(
        session.execute(
            select(CorpusProjectionORM.chunk_id).where(
                CorpusProjectionORM.package_uuid == candidate_b.package_uuid
            )
        ).scalars()
    )
    assert proj_a <= ids_a and proj_b <= ids_b
    assert proj_a.isdisjoint(proj_b)

    # Predecessor unchanged: A still published + enabled with its own version.
    pkg_a = session.get(RulesPackageORM, candidate.package_uuid)
    assert pkg_a.publication_status == "published" and pkg_a.is_enabled
    assert pkg_a.version == candidate.release_version

    # Both digests still verify against their actual persisted + vector state.
    vs_a = _vstate(
        session, candidate.package_uuid, chroma_client, retrieval_config, fake_embedding
    )
    vs_b = _vstate(
        session, candidate_b.package_uuid, chroma_client, config_b, fake_embedding
    )
    assert verify_persisted_digest(session, candidate.package_uuid, vs_a)
    assert verify_persisted_digest(session, candidate_b.package_uuid, vs_b)
