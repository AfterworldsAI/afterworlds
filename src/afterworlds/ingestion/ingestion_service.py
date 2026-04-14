"""Rules Package ingestion service — CRD Issue 5b.

Provides an idempotent SQL ingestion pipeline and a publication gate for
RulesPackage records ingested from structured SRD JSON.

Architecture invariants
-----------------------
- Source records (RuleChunk, MechanicalEntity) are immutable after creation.
  The ingestion service NEVER modifies existing source rows.
- One manifest row per package (DB-enforced unique constraint).
- Publication gate: fails explicitly if SQL ingest, manifest, or vector write
  is incomplete.
- Idempotency: re-running with the same data does not duplicate records.
  Existing chunks are detected by (rules_package_id, source_locator_value).
  Existing entities are detected by (rules_package_id, entity_type, name).
  Existing sources are detected by (rules_package_id, name).

KNOWN UNKNOWN: ChromaDB collection schema is designated for CRD Issue 18
revision.  See ``vector_writer.py`` module docstring.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from chromadb.api import ClientAPI as ChromaClientAPI
from sqlalchemy import select
from sqlalchemy.orm import Session

from afterworlds.ingestion.srd_parser import ParsedChunk, ParsedEntity, SRDParser
from afterworlds.ingestion.vector_writer import VectorWriter
from afterworlds.models.enums import (
    PublicationStatusEnum,
    RuleSourceCategoryEnum,
    RulesSystemEnum,
    SourceLocatorTypeEnum,
)
from afterworlds.models.rules_package import IngestionConfig
from afterworlds.persistence.orm.rules_package import (
    MechanicalEntityORM,
    RuleChunkORM,
    RuleSourceORM,
    RulesPackageManifestORM,
    RulesPackageORM,
)

# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------


@dataclass
class IngestionResult:
    """Summary returned by ``IngestionService.ingest``."""

    package_id: str
    source_id: str
    chunks_written: int
    chunks_skipped: int
    entities_written: int
    entities_skipped: int
    vector_chunks_written: int
    errors: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Error types
# ---------------------------------------------------------------------------


class PublicationError(Exception):
    """Raised by ``IngestionService.publish`` when the gate checks fail."""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _make_package_id() -> str:
    return str(uuid4())


def _make_source_id() -> str:
    return str(uuid4())


def _make_chunk_id() -> str:
    return str(uuid4())


def _make_entity_id() -> str:
    return str(uuid4())


def _make_manifest_id() -> str:
    return str(uuid4())


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class IngestionService:
    """Full-cycle ingestion and publication service for RulesPackage records.

    All write operations are idempotent: re-running with the same data will
    skip existing records and return counts of written vs. skipped.

    Parameters
    ----------
    config:
        ``IngestionConfig`` supplying metadata for the package and source.
    """

    def __init__(self, config: IngestionConfig) -> None:
        self._config = config
        self._parser = SRDParser()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def ingest(
        self,
        session: Session,
        srd_data: dict[str, Any],
        source_file_name: str,
        chroma_client: ChromaClientAPI,
    ) -> IngestionResult:
        """Run the full ingestion pipeline.

        1. Upsert RulesPackage row (or locate existing).
        2. Upsert RuleSource row.
        3. Parse sections → RuleChunk rows (idempotent — skip existing).
        4. Parse entities → MechanicalEntity rows (idempotent — skip existing).
        5. Write chunks to ChromaDB vector store.
        6. Upsert manifest row with gate flags.
        7. Commit.

        Parameters
        ----------
        session:
            SQLAlchemy session.
        srd_data:
            Structured SRD data dict (loaded from JSON).
        source_file_name:
            Name of the source file (used as ``source_document`` on records).
        chroma_client:
            ChromaDB client for vector writes.

        Returns
        -------
        IngestionResult
            Counts and package/source IDs.
        """
        now = _now_iso()

        # 1. Upsert package row
        package_id = self._upsert_package(session, now)

        # 2. Upsert source row
        source_id = self._upsert_source(session, package_id, now)

        # 3. Parse + persist chunks
        parsed_chunks = self._parser.parse_chunks(srd_data)
        chunks_written, chunks_skipped, written_chunks, written_chunk_ids = (
            self._persist_chunks(
                session, parsed_chunks, package_id, source_id, source_file_name, now
            )
        )

        # 4. Parse + persist entities
        parsed_entities = self._parser.parse_entities(srd_data)
        entities_written, entities_skipped = self._persist_entities(
            session,
            parsed_entities,
            package_id,
            source_id,
            source_file_name,
            now,
        )

        # 5. Vector write
        vector_writer = VectorWriter(chroma_client)
        vector_writer.write_chunks(written_chunks, package_id, written_chunk_ids)
        vector_chunks_written = len(written_chunks)

        # 6. Upsert manifest
        sql_complete = True
        vector_complete = vector_writer.has_chunks(package_id)
        self._upsert_manifest(
            session,
            package_id,
            source_file_name,
            sql_complete,
            vector_complete,
            now,
        )

        # 7. Commit
        session.commit()

        return IngestionResult(
            package_id=package_id,
            source_id=source_id,
            chunks_written=chunks_written,
            chunks_skipped=chunks_skipped,
            entities_written=entities_written,
            entities_skipped=entities_skipped,
            vector_chunks_written=vector_chunks_written,
        )

    def publish(
        self,
        session: Session,
        package_id: str,
        vector_writer: VectorWriter,
    ) -> None:
        """Publish a RulesPackage after passing all gate checks.

        Gate checks (in order):
        1. Package exists and is accessible.
        2. Manifest row exists for the package.
        3. ``sql_ingest_complete`` is True.
        4. ``vector_write_complete`` is True.

        On success, sets ``publication_status`` = "published" and
        ``published_at`` on the package row.

        Raises
        ------
        PublicationError
            If any gate check fails.
        """
        # Gate 1: package exists
        pkg_row = session.execute(
            select(RulesPackageORM).where(
                RulesPackageORM.rules_package_id == package_id
            )
        ).scalar_one_or_none()
        if pkg_row is None:
            raise PublicationError(
                f"Package {package_id!r} not found — cannot publish."
            )

        # Gate 2: manifest exists
        manifest_row = session.execute(
            select(RulesPackageManifestORM).where(
                RulesPackageManifestORM.rules_package_id == package_id
            )
        ).scalar_one_or_none()
        if manifest_row is None:
            raise PublicationError(
                f"Package {package_id!r} has no manifest row — "
                "run ingest() before publish()."
            )

        # Gate 3: SQL ingest complete
        if not manifest_row.sql_ingest_complete:
            raise PublicationError(
                f"Package {package_id!r}: sql_ingest_complete is False — "
                "SQL ingestion is incomplete."
            )

        # Gate 4: manifest flag records vector write complete
        if not manifest_row.vector_write_complete:
            raise PublicationError(
                f"Package {package_id!r}: vector_write_complete is False — "
                "vector write is incomplete."
            )

        # Gate 5: live vector index check — collection may have been reset
        # after ingest, leaving the manifest flag stale.
        if not vector_writer.has_chunks(package_id):
            raise PublicationError(
                f"Package {package_id!r}: vector index contains no chunks — "
                "re-run ingest() to repopulate before publishing."
            )

        # All gates passed — publish
        now = _now_iso()
        pkg_row.publication_status = PublicationStatusEnum.PUBLISHED.value
        pkg_row.published_at = now
        pkg_row.updated_at = now
        session.commit()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _upsert_package(self, session: Session, now: str) -> str:
        """Return the existing package_id or create a new package row."""
        cfg = self._config
        existing = session.execute(
            select(RulesPackageORM).where(
                RulesPackageORM.name == cfg.package_name,
                RulesPackageORM.version == cfg.package_version,
            )
        ).scalar_one_or_none()
        if existing is not None:
            return str(existing.rules_package_id)
        package_id = _make_package_id()
        session.add(
            RulesPackageORM(
                rules_package_id=package_id,
                name=cfg.package_name,
                system=RulesSystemEnum(cfg.system).value,
                version=cfg.package_version,
                is_enabled=True,
                publication_status=PublicationStatusEnum.DRAFT.value,
                published_at=None,
                created_at=now,
                updated_at=now,
            )
        )
        session.flush()
        return package_id

    def _upsert_source(self, session: Session, package_id: str, now: str) -> str:
        """Return the existing source_id or create a new source row."""
        cfg = self._config
        existing = session.execute(
            select(RuleSourceORM).where(
                RuleSourceORM.rules_package_id == package_id,
                RuleSourceORM.name == cfg.source_name,
            )
        ).scalar_one_or_none()
        if existing is not None:
            return str(existing.source_id)
        source_id = _make_source_id()
        session.add(
            RuleSourceORM(
                source_id=source_id,
                rules_package_id=package_id,
                name=cfg.source_name,
                category=RuleSourceCategoryEnum(cfg.source_category).value,
                precedence_rank=cfg.source_precedence_rank,
                is_enabled=True,
                created_at=now,
            )
        )
        session.flush()
        return source_id

    def _persist_chunks(
        self,
        session: Session,
        parsed_chunks: list[ParsedChunk],
        package_id: str,
        source_id: str,
        source_file_name: str,
        now: str,
    ) -> tuple[int, int, list[ParsedChunk], list[str]]:
        """Persist parsed chunks; skip existing ones by section_path.

        Returns
        -------
        (written_count, skipped_count, written_chunks, written_chunk_ids)
        """
        # Build set of already-persisted section paths for this package
        existing_locators: set[str] = set(
            session.execute(
                select(RuleChunkORM.source_locator_value).where(
                    RuleChunkORM.rules_package_id == package_id
                )
            )
            .scalars()
            .all()
        )
        written = 0
        skipped = 0
        written_chunks: list[ParsedChunk] = []
        written_chunk_ids: list[str] = []
        for chunk in parsed_chunks:
            if chunk.section_path in existing_locators:
                skipped += 1
                continue
            chunk_id = _make_chunk_id()
            session.add(
                RuleChunkORM(
                    chunk_id=chunk_id,
                    rules_package_id=package_id,
                    source_id=source_id,
                    subsystem=chunk.subsystem.value,
                    content=chunk.content,
                    source_document=source_file_name,
                    source_locator_type=SourceLocatorTypeEnum.SECTION_PATH.value,
                    source_locator_value=chunk.section_path,
                    source_section_label=chunk.heading,
                    is_enabled=True,
                    created_at=now,
                )
            )
            existing_locators.add(chunk.section_path)
            written += 1
            written_chunks.append(chunk)
            written_chunk_ids.append(chunk_id)
        session.flush()
        return written, skipped, written_chunks, written_chunk_ids

    def _persist_entities(
        self,
        session: Session,
        parsed_entities: list[ParsedEntity],
        package_id: str,
        source_id: str,
        source_file_name: str,
        now: str,
    ) -> tuple[int, int]:
        """Persist parsed entities; skip existing ones by (entity_type, name).

        Returns
        -------
        (written_count, skipped_count)
        """
        # Build set of (entity_type_value, name) already persisted
        existing_keys: set[tuple[str, str]] = {
            (str(row[0]), str(row[1]))
            for row in session.execute(
                select(
                    MechanicalEntityORM.entity_type,
                    MechanicalEntityORM.name,
                ).where(MechanicalEntityORM.rules_package_id == package_id)
            ).all()
        }
        written = 0
        skipped = 0
        for ent in parsed_entities:
            key = (ent.entity_type.value, ent.name)
            if key in existing_keys:
                skipped += 1
                continue
            entity_id = _make_entity_id()
            session.add(
                MechanicalEntityORM(
                    entity_id=entity_id,
                    rules_package_id=package_id,
                    source_id=source_id,
                    entity_type=ent.entity_type.value,
                    name=ent.name,
                    structured_data=ent.data.model_dump(),
                    source_document=source_file_name,
                    source_locator_type=SourceLocatorTypeEnum.SECTION_PATH.value,
                    source_locator_value=ent.section_path,
                    source_section_label=ent.name,
                    is_enabled=True,
                    created_at=now,
                )
            )
            existing_keys.add(key)
            written += 1
        session.flush()
        return written, skipped

    def _upsert_manifest(
        self,
        session: Session,
        package_id: str,
        source_file_name: str,
        sql_complete: bool,
        vector_complete: bool,
        now: str,
    ) -> None:
        """Create or update the manifest row for *package_id*."""
        cfg = self._config
        existing = session.execute(
            select(RulesPackageManifestORM).where(
                RulesPackageManifestORM.rules_package_id == package_id
            )
        ).scalar_one_or_none()
        if existing is not None:
            existing.sql_ingest_complete = sql_complete
            existing.vector_write_complete = vector_complete
            existing.updated_at = now
        else:
            session.add(
                RulesPackageManifestORM(
                    manifest_id=_make_manifest_id(),
                    rules_package_id=package_id,
                    authoritative_source_document=cfg.authoritative_source_document,
                    authoritative_source_version=cfg.authoritative_source_version,
                    package_license=cfg.package_license,
                    transform_status=cfg.transform_status,
                    parsing_convenience_source=cfg.parsing_convenience_source,
                    attribution_text=cfg.attribution_text,
                    sql_ingest_complete=sql_complete,
                    vector_write_complete=vector_complete,
                    created_at=now,
                    updated_at=now,
                )
            )
        session.flush()
