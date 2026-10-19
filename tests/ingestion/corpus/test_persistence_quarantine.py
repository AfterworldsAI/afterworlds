"""Pre-release clean-baseline guards — Issue 5c.

What remains of the original persistence suite. Its persist, tamper, policy,
membership, rollback and reuse tests ran on the six-canary-page *compact*
candidate built by the retired PDF-geometric transform; they had been skipped
since the 21 September 2026 quarantine and were removed with that corpus under
the Owner Decision's Step 5. The publication lifecycle, tamper detection,
rollback and verified reuse are covered on the source corpus in
``test_source_lifecycle.py``.

These guards are independent of any corpus: the obsolete structured SRD JSON
stays absent, no production code names it, migration 0018 removes the
incomplete legacy package, and a candidate cannot claim persistence.
"""

from __future__ import annotations

import dataclasses
import re

from sqlalchemy import event, select

from afterworlds.ingestion.corpus.pipeline import CandidateRelease
from afterworlds.persistence.orm.rules_package import (
    RuleChunkORM,
    RuleSourceORM,
    RulesPackageORM,
)

from .conftest import REPO_ROOT

_NOW = "2026-07-23T00:00:00Z"


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
    from alembic import command
    from alembic.config import Config

    cfg = Config(str(REPO_ROOT / "alembic.ini"))
    cfg.set_main_option(
        "script_location",
        str(REPO_ROOT / "src" / "afterworlds" / "migrations" / "content"),
    )
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
