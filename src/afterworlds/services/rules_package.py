"""Rules Package service — typed read surface for mechanical canon.

This module provides the typed read interface that downstream issues
(CRD Issue 5b ingestion, CRD Issue 8 Context Builder) depend on.

Play-time queries
-----------------
Surface only published, enabled content.  Disabled packages, disabled
sources, and their associated chunks/entities are excluded.

Administrative / internal queries
----------------------------------
Pass ``include_non_published=True`` to access draft packages during
ingestion validation and publication flow support (CRD Issue 5b).

Source record immutability
--------------------------
Source records (RuleChunk, MechanicalEntity) are immutable after creation.
All layered changes are expressed as RuleOverride rows.  No service method
in this module modifies a source record.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from afterworlds.models.enums import (
    MechanicalEntityTypeEnum,
    OverrideOperationEnum,
    OverrideOriginEnum,
    PublicationStatusEnum,
    RuleSourceCategoryEnum,
    RulesSystemEnum,
    RuleSubsystemEnum,
    SourceLocatorTypeEnum,
)
from afterworlds.models.rules_package import (
    ActionEntity,
    ActiveRuleSlice,
    AppliedChunk,
    AppliedEntity,
    ChunkOverridePayload,
    ChunksResult,
    ConditionEntity,
    EntityData,
    ItemEntity,
    MechanicalEntity,
    RuleChunk,
    RuleOverride,
    RuleSource,
    RulesPackageDetail,
    SpellEntity,
    StatBlockEntity,
)
from afterworlds.persistence.orm.rules_package import (
    MechanicalEntityORM,
    RuleChunkORM,
    RuleOverrideORM,
    RuleSourceORM,
    RulesPackageORM,
)

# ---------------------------------------------------------------------------
# Module-level helpers — ORM row → Pydantic model conversion
# These are pure functions with no side effects.
# ---------------------------------------------------------------------------


def _orm_to_package_detail(
    row: RulesPackageORM, sources: list[RuleSource]
) -> RulesPackageDetail:
    return RulesPackageDetail(
        rules_package_id=UUID(row.rules_package_id),
        name=row.name,
        system=RulesSystemEnum(row.system),
        version=row.version,
        is_enabled=row.is_enabled,
        publication_status=PublicationStatusEnum(row.publication_status),
        published_at=(
            datetime.fromisoformat(row.published_at) if row.published_at else None
        ),
        created_at=datetime.fromisoformat(row.created_at),
        updated_at=datetime.fromisoformat(row.updated_at),
        sources=sources,
    )


def _orm_to_source(row: RuleSourceORM) -> RuleSource:
    return RuleSource(
        source_id=UUID(row.source_id),
        rules_package_id=UUID(row.rules_package_id),
        name=row.name,
        category=RuleSourceCategoryEnum(row.category),
        precedence_rank=row.precedence_rank,
        is_enabled=row.is_enabled,
        created_at=datetime.fromisoformat(row.created_at),
    )


def _orm_to_chunk(row: RuleChunkORM) -> RuleChunk:
    return RuleChunk(
        chunk_id=UUID(row.chunk_id),
        rules_package_id=UUID(row.rules_package_id),
        source_id=UUID(row.source_id),
        subsystem=RuleSubsystemEnum(row.subsystem),
        content=row.content,
        source_document=row.source_document,
        source_locator_type=SourceLocatorTypeEnum(row.source_locator_type),
        source_locator_value=row.source_locator_value,
        source_section_label=row.source_section_label,
        is_enabled=row.is_enabled,
        created_at=datetime.fromisoformat(row.created_at),
    )


def _deserialize_entity_data(
    entity_type: MechanicalEntityTypeEnum, data: dict[str, Any]
) -> EntityData:
    """Deserialise a structured_data dict to the correct typed entity model."""
    if entity_type == MechanicalEntityTypeEnum.SPELL:
        return SpellEntity.model_validate(data)
    if entity_type == MechanicalEntityTypeEnum.CONDITION:
        return ConditionEntity.model_validate(data)
    if entity_type == MechanicalEntityTypeEnum.STAT_BLOCK:
        return StatBlockEntity.model_validate(data)
    if entity_type == MechanicalEntityTypeEnum.ACTION:
        return ActionEntity.model_validate(data)
    if entity_type == MechanicalEntityTypeEnum.ITEM:
        return ItemEntity.model_validate(data)
    raise ValueError(f"Unhandled entity type: {entity_type!r}")  # pragma: no cover


def _orm_to_entity(row: MechanicalEntityORM) -> MechanicalEntity:
    entity_type = MechanicalEntityTypeEnum(row.entity_type)
    structured_data = _deserialize_entity_data(entity_type, row.structured_data)
    return MechanicalEntity(
        entity_id=UUID(row.entity_id),
        rules_package_id=UUID(row.rules_package_id),
        source_id=UUID(row.source_id),
        entity_type=entity_type,
        name=row.name,
        structured_data=structured_data,
        source_document=row.source_document,
        source_locator_type=SourceLocatorTypeEnum(row.source_locator_type),
        source_locator_value=row.source_locator_value,
        source_section_label=row.source_section_label,
        is_enabled=row.is_enabled,
        created_at=datetime.fromisoformat(row.created_at),
    )


def _orm_to_override(row: RuleOverrideORM) -> RuleOverride:
    return RuleOverride(
        override_id=UUID(row.override_id),
        rules_package_id=UUID(row.rules_package_id),
        target_chunk_id=(UUID(row.target_chunk_id) if row.target_chunk_id else None),
        target_entity_id=(UUID(row.target_entity_id) if row.target_entity_id else None),
        override_origin=OverrideOriginEnum(row.override_origin),
        override_operation=OverrideOperationEnum(row.override_operation),
        override_payload=row.override_payload,
        precedence=row.precedence,
        is_enabled=row.is_enabled,
        created_at=datetime.fromisoformat(row.created_at),
    )


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class RulesPackageService:
    """Read-oriented service for the Rules Package subsystem.

    Play-time methods surface only published, enabled content.
    Administrative/internal callers may opt into draft reads via
    ``include_non_published=True``.

    Source records (RuleChunk, MechanicalEntity) are never modified by this
    service.  All layered changes are expressed as RuleOverride rows.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    # -- Accessibility helpers ----------------------------------------------

    def _package_accessible(
        self, row: RulesPackageORM, include_non_published: bool
    ) -> bool:
        """Return True if *row* is accessible under the given query policy."""
        if not row.is_enabled:
            return False
        if not include_non_published:
            return row.publication_status == PublicationStatusEnum.PUBLISHED.value
        return True

    def _enabled_source_ids_for_package(self, package_id: UUID) -> list[str]:
        """Return string source IDs for all enabled sources in *package_id*."""
        rows = (
            self._session.execute(
                select(RuleSourceORM.source_id).where(
                    RuleSourceORM.rules_package_id == str(package_id),
                    RuleSourceORM.is_enabled == True,  # noqa: E712
                )
            )
            .scalars()
            .all()
        )
        return list(rows)

    # -- Public read methods ------------------------------------------------

    def get_package_by_id(
        self,
        package_id: UUID,
        include_non_published: bool = False,
    ) -> RulesPackageDetail | None:
        """Fetch full package metadata including its RuleSource records.

        Returns None if the package does not exist or is not accessible under
        the current query policy.

        Administrative/internal callers may pass ``include_non_published=True``
        to access draft packages during ingestion validation and publication
        flow support (CRD Issue 5b).
        """
        row = self._session.execute(
            select(RulesPackageORM).where(
                RulesPackageORM.rules_package_id == str(package_id)
            )
        ).scalar_one_or_none()

        if row is None:
            return None
        if not self._package_accessible(row, include_non_published):
            return None

        source_rows = (
            self._session.execute(
                select(RuleSourceORM)
                .where(RuleSourceORM.rules_package_id == str(package_id))
                .order_by(RuleSourceORM.precedence_rank)
            )
            .scalars()
            .all()
        )
        sources = [_orm_to_source(src) for src in source_rows]
        return _orm_to_package_detail(row, sources)

    def get_chunks_by_subsystem(
        self,
        package_id: UUID,
        subsystem: RuleSubsystemEnum,
        include_non_published: bool = False,
    ) -> ChunksResult:
        """Retrieve rule chunks for a package/subsystem.

        Respects package, RuleSource, and chunk enable/disable state.
        Play-time (default): only published and enabled content is surfaced.
        """
        pkg_row = self._session.execute(
            select(RulesPackageORM).where(
                RulesPackageORM.rules_package_id == str(package_id)
            )
        ).scalar_one_or_none()

        if pkg_row is None or not self._package_accessible(
            pkg_row, include_non_published
        ):
            return ChunksResult(package_id=package_id, subsystem=subsystem, chunks=[])

        enabled_source_ids = self._enabled_source_ids_for_package(package_id)
        if not enabled_source_ids:
            return ChunksResult(package_id=package_id, subsystem=subsystem, chunks=[])

        chunk_rows = (
            self._session.execute(
                select(RuleChunkORM).where(
                    RuleChunkORM.rules_package_id == str(package_id),
                    RuleChunkORM.subsystem == subsystem.value,
                    RuleChunkORM.is_enabled == True,  # noqa: E712
                    RuleChunkORM.source_id.in_(enabled_source_ids),
                )
            )
            .scalars()
            .all()
        )
        return ChunksResult(
            package_id=package_id,
            subsystem=subsystem,
            chunks=[_orm_to_chunk(r) for r in chunk_rows],
        )

    def get_entity_by_type_and_name(
        self,
        package_id: UUID,
        entity_type: MechanicalEntityTypeEnum,
        name: str,
        source_id: UUID | None = None,
        include_non_published: bool = False,
    ) -> MechanicalEntity | None:
        """Retrieve a specific mechanical entity scoped to a package.

        Optional ``source_id`` filter resolves ambiguity when the same name
        exists across multiple RuleSource records within the package.

        Returns None if not found or not accessible.
        """
        pkg_row = self._session.execute(
            select(RulesPackageORM).where(
                RulesPackageORM.rules_package_id == str(package_id)
            )
        ).scalar_one_or_none()

        if pkg_row is None or not self._package_accessible(
            pkg_row, include_non_published
        ):
            return None

        enabled_source_ids = self._enabled_source_ids_for_package(package_id)
        if not enabled_source_ids:
            return None

        stmt = (
            select(MechanicalEntityORM)
            .join(
                RuleSourceORM,
                MechanicalEntityORM.source_id == RuleSourceORM.source_id,
            )
            .where(
                MechanicalEntityORM.rules_package_id == str(package_id),
                MechanicalEntityORM.entity_type == entity_type.value,
                MechanicalEntityORM.name == name,
                MechanicalEntityORM.is_enabled == True,  # noqa: E712
                MechanicalEntityORM.source_id.in_(enabled_source_ids),
            )
            .order_by(RuleSourceORM.precedence_rank)
        )
        if source_id is not None:
            stmt = stmt.where(MechanicalEntityORM.source_id == str(source_id))

        row = self._session.execute(stmt).scalars().first()
        return _orm_to_entity(row) if row is not None else None

    def get_overrides_for_chunk(
        self, chunk_id: UUID, package_id: UUID
    ) -> list[RuleOverride]:
        """Retrieve active overrides for a chunk, scoped to its package."""
        rows = (
            self._session.execute(
                select(RuleOverrideORM)
                .where(
                    RuleOverrideORM.rules_package_id == str(package_id),
                    RuleOverrideORM.target_chunk_id == str(chunk_id),
                    RuleOverrideORM.is_enabled == True,  # noqa: E712
                )
                .order_by(RuleOverrideORM.precedence)
            )
            .scalars()
            .all()
        )
        return [_orm_to_override(r) for r in rows]

    def get_overrides_for_entity(
        self, entity_id: UUID, package_id: UUID
    ) -> list[RuleOverride]:
        """Retrieve active overrides for an entity, scoped to its package."""
        rows = (
            self._session.execute(
                select(RuleOverrideORM)
                .where(
                    RuleOverrideORM.rules_package_id == str(package_id),
                    RuleOverrideORM.target_entity_id == str(entity_id),
                    RuleOverrideORM.is_enabled == True,  # noqa: E712
                )
                .order_by(RuleOverrideORM.precedence)
            )
            .scalars()
            .all()
        )
        return [_orm_to_override(r) for r in rows]

    def get_active_rule_slice(
        self,
        package_id: UUID,
        subsystem_tags: list[RuleSubsystemEnum],
        entity_refs: list[tuple[MechanicalEntityTypeEnum, str]],
        include_non_published: bool = False,
    ) -> ActiveRuleSlice:
        """Assemble relevant rule chunks and entities for a turn context.

        This is deterministic lookup against the provided subsystem tags and
        entity references only.  Not a semantic search.  Semantic retrieval
        belongs to CRD Issue 18.

        Returns an ``ActiveRuleSlice`` with chunk override layering applied
        in precedence order.  Disabled (``is_enabled=False``) chunks, sources,
        and packages are excluded.  Override-disabled chunks appear with
        ``is_disabled=True`` and empty ``applied_content``.

        The return type ``ActiveRuleSlice`` is a stable named Pydantic model;
        the Context Builder (CRD Issue 8) may depend on its shape.
        """
        pkg_row = self._session.execute(
            select(RulesPackageORM).where(
                RulesPackageORM.rules_package_id == str(package_id)
            )
        ).scalar_one_or_none()

        if pkg_row is None or not self._package_accessible(
            pkg_row, include_non_published
        ):
            return ActiveRuleSlice(package_id=package_id, chunks=[], entities=[])

        enabled_source_ids = self._enabled_source_ids_for_package(package_id)

        # Collect and apply overrides to chunks for all requested subsystems
        applied_chunks: list[AppliedChunk] = []
        if subsystem_tags and enabled_source_ids:
            subsystem_values = [s.value for s in subsystem_tags]
            chunk_rows = (
                self._session.execute(
                    select(RuleChunkORM).where(
                        RuleChunkORM.rules_package_id == str(package_id),
                        RuleChunkORM.subsystem.in_(subsystem_values),
                        RuleChunkORM.is_enabled == True,  # noqa: E712
                        RuleChunkORM.source_id.in_(enabled_source_ids),
                    )
                )
                .scalars()
                .all()
            )
            for chunk_row in chunk_rows:
                chunk = _orm_to_chunk(chunk_row)
                applied_chunks.append(self._apply_chunk_overrides(chunk))

        # Collect specific entities by (type, name) reference
        applied_entities: list[AppliedEntity] = []
        for etype, ename in entity_refs:
            entity = self.get_entity_by_type_and_name(
                package_id,
                etype,
                ename,
                include_non_published=include_non_published,
            )
            if entity is not None:
                overrides = self.get_overrides_for_entity(
                    entity.entity_id, entity.rules_package_id
                )
                applied_entities.append(
                    AppliedEntity(
                        entity=entity,
                        override_ids_applied=[o.override_id for o in overrides],
                    )
                )

        return ActiveRuleSlice(
            package_id=package_id,
            chunks=applied_chunks,
            entities=applied_entities,
        )

    # -- Internal helpers ---------------------------------------------------

    def _apply_chunk_overrides(self, chunk: RuleChunk) -> AppliedChunk:
        """Apply active overrides to *chunk* in ascending precedence order.

        - ``disable``: marks the chunk as disabled; stops further processing.
        - ``replace``: replaces current content with payload content.
        - ``append``: appends payload content to current content.
        """
        overrides = self.get_overrides_for_chunk(chunk.chunk_id, chunk.rules_package_id)
        content = chunk.content
        is_disabled = False
        applied_ids: list[UUID] = []

        for override in overrides:
            applied_ids.append(override.override_id)
            if override.override_operation == OverrideOperationEnum.DISABLE:
                is_disabled = True
                break
            elif override.override_operation == OverrideOperationEnum.REPLACE:
                payload = ChunkOverridePayload.model_validate_json(
                    override.override_payload
                )
                content = payload.content or ""
            elif override.override_operation == OverrideOperationEnum.APPEND:
                payload = ChunkOverridePayload.model_validate_json(
                    override.override_payload
                )
                content = content + (payload.content or "")

        return AppliedChunk(
            chunk=chunk,
            applied_content="" if is_disabled else content,
            is_disabled=is_disabled,
            override_ids_applied=applied_ids,
        )
