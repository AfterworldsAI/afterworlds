"""Tests for Rules Package schema, models, and service — CRD Issue 5a.

Acceptance criteria verified:
  AC-RP-001  rp_* table prefix — every rp_* table registered
  AC-RP-002  No rp_* FK to non-rp_* tables (also in test_schema_separation_invariant)
  AC-RP-003  Publication lifecycle — draft/retired not surfaced at play time
  AC-RP-004  Source membership — disabled-source chunks excluded
  AC-RP-005  Source provenance — source_id non-nullable (ADR-0008)

The final CRD Issue 5d cutover (#137 contract 6, AC22) retired the obsolete
``MechanicalEntity`` family and the legacy chunk/entity ``RuleOverride``
authority, so the former AC-RP-006..011 tests of entity models, entity lookup,
legacy override layering/precedence and the legacy ``get_active_rule_slice``
were deleted with the code they graded. Their replacements are the typed
authority's own tests under ``tests/services/rules_authority/`` and the
production consumer tests in ``test_rule_slice_consumer_cutover.py``; the
retirement itself is proved by ``test_legacy_authority_retirement.py``.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Session

import afterworlds.persistence.orm.corpus  # noqa: F401
import afterworlds.persistence.orm.mechanical  # noqa: F401
import afterworlds.persistence.orm.rules_authority  # noqa: F401
import afterworlds.persistence.orm.rules_package  # noqa: F401
from afterworlds.models.enums import (
    PublicationStatusEnum,
    RuleSubsystemEnum,
)
from afterworlds.persistence.orm.base import Base
from afterworlds.persistence.orm.rules_package import (
    RuleChunkORM,
    RuleSourceORM,
    RulesPackageORM,
)
from afterworlds.services.rules_package import (
    RulesPackageService,
)

# ---------------------------------------------------------------------------
# Helpers — direct ORM row inserts for test setup
# ---------------------------------------------------------------------------

_NOW_ISO = datetime(2026, 4, 9, tzinfo=UTC).isoformat()


def _insert_package(
    session: Session,
    *,
    package_id: str | None = None,
    name: str = "Test Package",
    system: str = "d20",
    version: str = "1.0",
    is_enabled: bool = True,
    publication_status: str = "published",
    published_at: str | None = _NOW_ISO,
) -> str:
    pid = package_id or str(uuid4())
    session.execute(
        sa.insert(RulesPackageORM).values(
            rules_package_id=pid,
            name=name,
            system=system,
            version=version,
            is_enabled=is_enabled,
            publication_status=publication_status,
            published_at=published_at,
            created_at=_NOW_ISO,
            updated_at=_NOW_ISO,
        )
    )
    return pid


def _insert_source(
    session: Session,
    *,
    source_id: str | None = None,
    package_id: str,
    name: str = "Player's Handbook",
    category: str = "core_rulebook",
    precedence_rank: int = 1,
    is_enabled: bool = True,
) -> str:
    sid = source_id or str(uuid4())
    session.execute(
        sa.insert(RuleSourceORM).values(
            source_id=sid,
            rules_package_id=package_id,
            name=name,
            category=category,
            precedence_rank=precedence_rank,
            is_enabled=is_enabled,
            created_at=_NOW_ISO,
        )
    )
    return sid


def _insert_chunk(
    session: Session,
    *,
    chunk_id: str | None = None,
    package_id: str,
    source_id: str,
    subsystem: str = "combat",
    content: str = "Attack action.",
    is_enabled: bool = True,
) -> str:
    cid = chunk_id or str(uuid4())
    session.execute(
        sa.insert(RuleChunkORM).values(
            chunk_id=cid,
            rules_package_id=package_id,
            source_id=source_id,
            subsystem=subsystem,
            content=content,
            source_document="PHB",
            source_locator_type="page",
            source_locator_value="195",
            source_section_label=None,
            is_enabled=is_enabled,
            created_at=_NOW_ISO,
        )
    )
    return cid


# ---------------------------------------------------------------------------
# Service fixture
# ---------------------------------------------------------------------------


@pytest.fixture()
def svc(session: Session) -> RulesPackageService:
    return RulesPackageService(session)


# ---------------------------------------------------------------------------
# AC-RP-001: rp_* table prefix
# ---------------------------------------------------------------------------


class TestRpTablePrefix:
    def test_all_rp_tables_registered(self) -> None:
        expected = {
            "rp_packages",
            "rp_sources",
            "rp_chunks",
            "rp_manifests",
            # CRD Issue 5c (#132) corpus-integrity release tables.
            "rp_corpus_releases",
            "rp_source_ledgers",
            "rp_ledger_containers",
            "rp_ledger_leaves",
            "rp_reconciliation_policies",
            "rp_reconciliations",
            "rp_corpus_projections",
            # CRD Issue 5d (#137) mechanical-authority projection tables.
            "rp_mech_projections",
            "rp_mech_spans",
            "rp_mech_acceptance_batches",
            "rp_mech_batch_scope",
            "rp_mech_batch_diff",
            "rp_mech_acceptances",
            "rp_mech_records",
            "rp_mech_component_options",
            "rp_mech_components",
            "rp_mech_facts",
            "rp_mech_prose_bindings",
            "rp_mech_relationships",
            "rp_mech_references",
            "rp_mech_provenance",
            "rp_mech_active_projections",
            # CRD Issue 5d runtime authority: the typed override authoring
            # surface and the retained immutable override-set versions.
            "rp_mech_overrides",
            "rp_override_set_versions",
            "rp_override_set_entries",
            "rp_override_set_scopes",
            # CRD Issue 5d practical reliability: what a human reviewed, and
            # what that review was required to contain.
            "rp_mech_review_units",
            "rp_mech_review_expectations",
            "rp_mech_review_groups",
            "rp_mech_review_unit_acceptances",
        }
        actual = {n for n in Base.metadata.tables if n.startswith("rp_")}
        assert (
            expected == actual
        ), f"Expected rp_* tables: {sorted(expected)}\nFound: {sorted(actual)}"


# ---------------------------------------------------------------------------
# AC-RP-002: All rp_* FKs stay within the rp_* namespace
# ---------------------------------------------------------------------------


class TestRpFkSeparation:
    def test_all_rp_fks_stay_within_rp_namespace(self) -> None:
        """Every FK from an rp_* table must target another rp_* table."""
        violations: list[str] = []
        for table_name, table in Base.metadata.tables.items():
            if not table_name.startswith("rp_"):
                continue
            for fk in table.foreign_keys:
                target = fk.column.table.name
                if not target.startswith("rp_"):
                    violations.append(
                        f"  {table_name}.{fk.parent.name} → {target}.{fk.column.name}"
                    )
        assert not violations, (
            "rp_* tables must not carry FK constraints to non-rp_* tables.\n"
            "Violations:\n" + "\n".join(violations)
        )


# ---------------------------------------------------------------------------
# AC-RP-005: Source provenance — source_id non-nullable at ORM level
# ---------------------------------------------------------------------------


class TestSourceProvenance:
    def test_chunk_source_id_is_non_nullable(self) -> None:
        col = RuleChunkORM.__table__.c["source_id"]
        assert (
            not col.nullable
        ), "source_id on rp_chunks must be non-nullable (ADR-0008)"


# ---------------------------------------------------------------------------
# AC-RP-003: Publication lifecycle
# ---------------------------------------------------------------------------


class TestPublicationLifecycle:
    def test_draft_package_not_surfaced_at_play_time(
        self, session: Session, svc: RulesPackageService
    ) -> None:
        pid = _insert_package(session, publication_status="draft", published_at=None)
        session.commit()
        assert svc.get_package_by_id(UUID(pid)) is None

    def test_published_package_surfaced_at_play_time(
        self, session: Session, svc: RulesPackageService
    ) -> None:
        pid = _insert_package(session, publication_status="published")
        session.commit()
        result = svc.get_package_by_id(UUID(pid))
        assert result is not None
        assert result.publication_status == PublicationStatusEnum.PUBLISHED

    def test_retired_package_not_surfaced_at_play_time(
        self, session: Session, svc: RulesPackageService
    ) -> None:
        pid = _insert_package(session, publication_status="retired")
        session.commit()
        assert svc.get_package_by_id(UUID(pid)) is None

    def test_draft_accessible_with_include_non_published(
        self, session: Session, svc: RulesPackageService
    ) -> None:
        pid = _insert_package(session, publication_status="draft", published_at=None)
        session.commit()
        result = svc.get_package_by_id(UUID(pid), include_non_published=True)
        assert result is not None
        assert result.publication_status == PublicationStatusEnum.DRAFT

    def test_disabled_package_never_surfaced(
        self, session: Session, svc: RulesPackageService
    ) -> None:
        pid = _insert_package(session, is_enabled=False, publication_status="published")
        session.commit()
        assert svc.get_package_by_id(UUID(pid)) is None
        assert svc.get_package_by_id(UUID(pid), include_non_published=True) is None

    def test_draft_chunks_not_surfaced_at_play_time(
        self, session: Session, svc: RulesPackageService
    ) -> None:
        pid = _insert_package(session, publication_status="draft", published_at=None)
        sid = _insert_source(session, package_id=pid)
        _insert_chunk(session, package_id=pid, source_id=sid)
        session.commit()
        result = svc.get_chunks_by_subsystem(UUID(pid), RuleSubsystemEnum.COMBAT)
        assert result.chunks == []


# ---------------------------------------------------------------------------
# AC-RP-004: Source membership — disabled source excludes its records
# ---------------------------------------------------------------------------


class TestSourceMembership:
    def test_chunks_from_disabled_source_excluded(
        self, session: Session, svc: RulesPackageService
    ) -> None:
        pid = _insert_package(session)
        enabled_sid = _insert_source(
            session,
            package_id=pid,
            name="Enabled",
            is_enabled=True,
            precedence_rank=1,
        )
        disabled_sid = _insert_source(
            session,
            package_id=pid,
            name="Disabled",
            is_enabled=False,
            precedence_rank=2,
        )
        _insert_chunk(
            session,
            package_id=pid,
            source_id=enabled_sid,
            content="Enabled chunk.",
        )
        _insert_chunk(
            session,
            package_id=pid,
            source_id=disabled_sid,
            content="Disabled chunk.",
        )
        session.commit()
        result = svc.get_chunks_by_subsystem(UUID(pid), RuleSubsystemEnum.COMBAT)
        assert len(result.chunks) == 1
        assert result.chunks[0].content == "Enabled chunk."

    def test_no_enabled_sources_returns_empty_chunks(
        self, session: Session, svc: RulesPackageService
    ) -> None:
        pid = _insert_package(session)
        disabled_sid = _insert_source(session, package_id=pid, is_enabled=False)
        _insert_chunk(session, package_id=pid, source_id=disabled_sid)
        session.commit()
        result = svc.get_chunks_by_subsystem(UUID(pid), RuleSubsystemEnum.COMBAT)
        assert result.chunks == []


# ---------------------------------------------------------------------------
# get_package_by_id — sources are included and ordered by precedence
# ---------------------------------------------------------------------------


class TestGetPackageById:
    def test_returns_sources_ordered_by_precedence(
        self, session: Session, svc: RulesPackageService
    ) -> None:
        pid = _insert_package(session)
        _insert_source(session, package_id=pid, name="Supplement", precedence_rank=2)
        _insert_source(session, package_id=pid, name="Core Rulebook", precedence_rank=1)
        session.commit()
        result = svc.get_package_by_id(UUID(pid))
        assert result is not None
        assert [s.name for s in result.sources] == ["Core Rulebook", "Supplement"]

    def test_nonexistent_package_returns_none(self, svc: RulesPackageService) -> None:
        assert svc.get_package_by_id(uuid4()) is None


# ---------------------------------------------------------------------------
# Deterministic ordering — chunk list, entity resolution, override ordering
# ---------------------------------------------------------------------------


class TestDeterministicOrdering:
    def test_chunks_ordered_by_source_precedence_then_chunk_id(
        self, session: Session, svc: RulesPackageService
    ) -> None:
        """Chunks from lower precedence_rank sources appear first; within a
        source, chunks are ordered by chunk_id for stable iteration."""
        pid = _insert_package(session)
        sid_low = _insert_source(
            session, package_id=pid, name="Core", precedence_rank=1
        )
        sid_high = _insert_source(
            session, package_id=pid, name="Supplement", precedence_rank=2
        )
        # Insert in reverse order to confirm ordering is not insertion-based.
        cid_b = _insert_chunk(
            session,
            package_id=pid,
            source_id=sid_low,
            content="Core chunk B",
            chunk_id="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
        )
        cid_a = _insert_chunk(
            session,
            package_id=pid,
            source_id=sid_low,
            content="Core chunk A",
            chunk_id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        )
        cid_supp = _insert_chunk(
            session, package_id=pid, source_id=sid_high, content="Supplement chunk"
        )
        session.commit()
        result = svc.get_chunks_by_subsystem(UUID(pid), RuleSubsystemEnum.COMBAT)
        ids = [str(c.chunk_id) for c in result.chunks]
        # Core (rank 1) chunks before Supplement (rank 2); within Core, UUID order.
        assert ids.index(cid_a) < ids.index(cid_b)
        assert ids.index(cid_b) < ids.index(cid_supp)


# ---------------------------------------------------------------------------
# get_package_by_id — disabled sources excluded from returned detail
# ---------------------------------------------------------------------------


class TestGetPackageByIdDisabledSources:
    def test_disabled_source_excluded_from_package_detail(
        self, session: Session, svc: RulesPackageService
    ) -> None:
        """get_package_by_id must not include disabled sources in the returned
        RulesPackageDetail.sources list."""
        pid = _insert_package(session)
        _insert_source(session, package_id=pid, name="Active Source", is_enabled=True)
        _insert_source(
            session, package_id=pid, name="Disabled Source", is_enabled=False
        )
        session.commit()

        result = svc.get_package_by_id(UUID(pid))

        assert result is not None
        assert [s.name for s in result.sources] == ["Active Source"]

    def test_package_with_all_sources_disabled_returns_empty_sources(
        self, session: Session, svc: RulesPackageService
    ) -> None:
        """A package with every source disabled returns an empty sources list."""
        pid = _insert_package(session)
        _insert_source(session, package_id=pid, is_enabled=False)
        session.commit()

        result = svc.get_package_by_id(UUID(pid))

        assert result is not None
        assert result.sources == []


# ---------------------------------------------------------------------------
# get_package_by_id — source ordering is fully stable (tie-break by source_id)
# ---------------------------------------------------------------------------


class TestGetPackageByIdSourceOrdering:
    def test_equal_precedence_sources_ordered_by_source_id(
        self, session: Session, svc: RulesPackageService
    ) -> None:
        """When two sources share the same precedence_rank, source_id provides
        a stable secondary sort so the order is deterministic across reads."""
        pid = _insert_package(session)
        sid_high = "ffffffff-ffff-ffff-ffff-ffffffffffff"
        sid_low = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        # Insert high source_id first to confirm ordering is not insertion-based.
        _insert_source(
            session,
            source_id=sid_high,
            package_id=pid,
            name="High ID",
            precedence_rank=1,
        )
        _insert_source(
            session,
            source_id=sid_low,
            package_id=pid,
            name="Low ID",
            precedence_rank=1,
        )
        session.commit()

        result = svc.get_package_by_id(UUID(pid))

        assert result is not None
        assert [str(s.source_id) for s in result.sources] == [sid_low, sid_high]


# ---------------------------------------------------------------------------
# rp_packages — logical-key uniqueness: (name, version, system)
# AC from issue #60
# ---------------------------------------------------------------------------


class TestRpPackagesLogicalKeyUniqueness:
    def test_duplicate_name_version_system_rejected(self, session: Session) -> None:
        """Inserting two rp_packages rows with the same (name, version, system)
        must raise IntegrityError at the DB layer."""
        _insert_package(session, name="Core Rules", system="d20", version="5.0")
        session.commit()
        with pytest.raises(sa.exc.IntegrityError):
            _insert_package(session, name="Core Rules", system="d20", version="5.0")
            session.commit()

    def test_same_name_version_different_system_allowed(self, session: Session) -> None:
        """Two packages with the same name and version but different system
        are distinct logical identities and must both be accepted."""
        _insert_package(session, name="Core Rules", system="d20", version="5.0")
        _insert_package(session, name="Core Rules", system="gurps", version="5.0")
        session.commit()
        rows = session.execute(sa.select(RulesPackageORM)).scalars().all()
        assert len(rows) == 2

    def test_same_name_system_different_version_allowed(self, session: Session) -> None:
        """Two packages with the same name and system but different version
        are distinct logical identities and must both be accepted."""
        _insert_package(session, name="Core Rules", system="d20", version="5.0")
        _insert_package(session, name="Core Rules", system="d20", version="6.0")
        session.commit()
        rows = session.execute(sa.select(RulesPackageORM)).scalars().all()
        assert len(rows) == 2

    def test_upsert_package_finds_existing_row_after_constraint_added(
        self, session: Session
    ) -> None:
        """IngestionService._upsert_package returns existing package_id when a
        package with the same (name, version, system) already exists — confirming
        the service read-before-insert path is conflict-safe against the new
        unique constraint."""
        from afterworlds.ingestion.ingestion_service import IngestionService
        from afterworlds.models.rules_package import IngestionConfig

        cfg = IngestionConfig(
            package_name="Core Rules", package_version="5.0", system="d20"
        )
        svc = IngestionService(cfg)
        from datetime import UTC, datetime

        now = datetime.now(UTC).isoformat()
        pid_first = svc._upsert_package(session, now)
        session.commit()

        pid_second = svc._upsert_package(session, now)
        assert pid_first == pid_second


# ---------------------------------------------------------------------------
# rp_sources — logical-key uniqueness: (rules_package_id, name)
# AC from issue #60
# ---------------------------------------------------------------------------


class TestRpSourcesLogicalKeyUniqueness:
    def test_duplicate_package_id_name_rejected(self, session: Session) -> None:
        """Inserting two rp_sources rows with the same (rules_package_id, name)
        must raise IntegrityError at the DB layer."""
        pid = _insert_package(session)
        session.commit()
        _insert_source(session, package_id=pid, name="SRD 5.2.1")
        session.commit()
        with pytest.raises(sa.exc.IntegrityError):
            _insert_source(session, package_id=pid, name="SRD 5.2.1")
            session.commit()

    def test_same_name_different_package_allowed(self, session: Session) -> None:
        """The same source name under two different packages is allowed — the
        logical key is scoped to the package."""
        pid_a = _insert_package(session, name="Package A")
        pid_b = _insert_package(session, name="Package B")
        session.commit()
        _insert_source(session, package_id=pid_a, name="SRD 5.2.1")
        _insert_source(session, package_id=pid_b, name="SRD 5.2.1")
        session.commit()
        rows = session.execute(sa.select(RuleSourceORM)).scalars().all()
        assert len(rows) == 2

    def test_upsert_source_finds_existing_row_after_constraint_added(
        self, session: Session
    ) -> None:
        """IngestionService._upsert_source returns existing source_id when a
        source with the same (rules_package_id, name) already exists — confirming
        the service read-before-insert path is conflict-safe."""
        from afterworlds.ingestion.ingestion_service import IngestionService
        from afterworlds.models.rules_package import IngestionConfig

        cfg = IngestionConfig(
            package_name="Test Package",
            package_version="1.0",
            system="d20",
            source_name="Core Rulebook",
        )
        svc_obj = IngestionService(cfg)
        from datetime import UTC, datetime

        now = datetime.now(UTC).isoformat()
        pid = svc_obj._upsert_package(session, now)
        sid_first = svc_obj._upsert_source(session, pid, now)
        session.commit()

        sid_second = svc_obj._upsert_source(session, pid, now)
        assert sid_first == sid_second


# ---------------------------------------------------------------------------
# rp_manifests — table name alignment with rp_* family (issue #60 rename)
# ---------------------------------------------------------------------------


class TestRpManifestTableName:
    def test_manifest_table_is_rp_manifests(self) -> None:
        """The manifest ORM class must use the rp_manifests table name, not
        the legacy rules_package_manifests name."""
        from afterworlds.persistence.orm.rules_package import RulesPackageManifestORM

        assert RulesPackageManifestORM.__tablename__ == "rp_manifests"

    def test_manifest_table_included_in_rp_family(self) -> None:
        """rp_manifests must be present in Base.metadata under the rp_* prefix
        so the FK separation invariant check covers it."""
        assert "rp_manifests" in Base.metadata.tables
        assert "rules_package_manifests" not in Base.metadata.tables
