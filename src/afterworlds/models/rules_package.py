"""Pydantic models for the Rules Package — mechanical canon subsystem.

The Rules Package governs mechanical adjudication canon (rules, stats,
entities).  It is structurally separate from the Story Bible, which governs
narrative canon.

Architecture invariant: no field in these models carries a reference to
Story, Arc, Chapter, Node, Turn, or any Story Bible entity.  The Rules
Package is a standalone corpus with no cross-dependency on narrative state.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, model_validator
from typing_extensions import Self

from afterworlds.models.enums import (
    MechanicalEntityTypeEnum,
    OverrideOperationEnum,
    OverrideOriginEnum,
    PublicationStatusEnum,
    RuleSourceCategoryEnum,
    RuleSubsystemEnum,
    RulesSystemEnum,
    SourceLocatorTypeEnum,
)

# ---------------------------------------------------------------------------
# Mechanical entity data models — one distinct typed model per entity_type
# ---------------------------------------------------------------------------


class SpellEntity(BaseModel):
    """Typed data for a spell mechanical entity (d20 v1 shape).

    Fields reflect what Issue 15 adjudication will need.
    """

    casting_time: str
    range: str
    duration: str
    components: list[str] = Field(default_factory=list)
    effect_description: str


class ConditionEntity(BaseModel):
    """Typed data for a condition mechanical entity."""

    effects: list[str] = Field(default_factory=list)


class StatBlockEntity(BaseModel):
    """Typed data for a stat block mechanical entity (d20 v1 shape)."""

    armor_class: int
    hit_points: int
    speed: str
    strength: int
    dexterity: int
    constitution: int
    intelligence: int
    wisdom: int
    charisma: int
    actions: list[str] = Field(default_factory=list)


class ActionEntity(BaseModel):
    """Typed data for an action mechanical entity."""

    action_type: str
    description: str
    attack_bonus: int | None = None
    effect: str | None = None


class ItemEntity(BaseModel):
    """Typed data for an item mechanical entity (d20 v1 shape)."""

    item_type: str
    properties: list[str] = Field(default_factory=list)
    weight: float | None = None
    value: str | None = None


# Union of all entity data types.  The sole source of truth for which
# concrete models are valid for ``MechanicalEntity.structured_data``.
EntityData = SpellEntity | ConditionEntity | StatBlockEntity | ActionEntity | ItemEntity


# ---------------------------------------------------------------------------
# Override payload model
# ---------------------------------------------------------------------------


class ChunkOverridePayload(BaseModel):
    """Fully typed payload for chunk-targeting RuleOverride records.

    For replace/append operations, ``content`` carries the replacement or
    appended text.  For disable operations, ``content`` is None.

    Entity-targeting override patch semantics (structured patch shapes for
    StatBlockEntity, SpellEntity, etc.) are deferred.  In this issue,
    entity-targeting overrides carry a plain ``{"content": ...}`` payload
    only.  See ADR-0007.
    """

    content: str | None = None


# ---------------------------------------------------------------------------
# Source-document model — defined before RulesPackageDetail which references it
# ---------------------------------------------------------------------------


class RuleSource(BaseModel):
    """Source-document metadata within a RulesPackage.

    Records where rules came from to support traceability and explicit
    authority ordering.  Source records are immutable after creation; all
    layered changes go through ``RuleOverride``.

    ``category`` classifies the source type.  ``precedence_rank`` determines
    authority ordering within the package.  These are separate concerns —
    do not infer winning-rule behaviour from ``category`` alone.
    """

    source_id: UUID = Field(default_factory=uuid4)
    rules_package_id: UUID
    name: str
    category: RuleSourceCategoryEnum
    precedence_rank: int
    is_enabled: bool = True
    created_at: datetime


# ---------------------------------------------------------------------------
# Core package models
# ---------------------------------------------------------------------------


class RulesPackage(BaseModel):
    """Top-level Rules Package metadata record."""

    rules_package_id: UUID = Field(default_factory=uuid4)
    name: str
    system: RulesSystemEnum
    version: str
    is_enabled: bool = True
    publication_status: PublicationStatusEnum = PublicationStatusEnum.DRAFT
    published_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class RulesPackageDetail(BaseModel):
    """Full package metadata including its RuleSource records.

    Returned by ``RulesPackageService.get_package_by_id``.
    """

    rules_package_id: UUID
    name: str
    system: RulesSystemEnum
    version: str
    is_enabled: bool
    publication_status: PublicationStatusEnum
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime
    sources: list[RuleSource]


# ---------------------------------------------------------------------------
# Atomic rule chunk
# ---------------------------------------------------------------------------


class RuleChunk(BaseModel):
    """Atomic unit of rule text within a RulesPackage.

    Source provenance is required and non-nullable.  There are no orphaned
    chunks — every chunk belongs to a named RuleSource.  Source records are
    immutable after creation; layered changes go through RuleOverride.
    """

    chunk_id: UUID = Field(default_factory=uuid4)
    rules_package_id: UUID
    source_id: UUID  # Required; no orphaned chunks
    subsystem: RuleSubsystemEnum
    content: str
    source_document: str  # Non-nullable provenance
    source_locator_type: SourceLocatorTypeEnum
    source_locator_value: str  # Non-nullable
    source_section_label: str | None = None
    is_enabled: bool = True
    created_at: datetime


# ---------------------------------------------------------------------------
# Structured mechanical entity
# ---------------------------------------------------------------------------


class MechanicalEntity(BaseModel):
    """Structured mechanical entity — typed, not a freeform blob.

    ``structured_data`` holds a fully typed model for the given
    ``entity_type``.  The service layer validates and deserialises to the
    correct concrete type using ``entity_type`` as the discriminator.

    Source records are immutable after creation; layered changes go through
    RuleOverride.
    """

    entity_id: UUID = Field(default_factory=uuid4)
    rules_package_id: UUID
    source_id: UUID  # Required; no orphaned entities
    entity_type: MechanicalEntityTypeEnum
    name: str
    structured_data: EntityData
    source_document: str  # Non-nullable provenance
    source_locator_type: SourceLocatorTypeEnum
    source_locator_value: str  # Non-nullable
    source_section_label: str | None = None
    is_enabled: bool = True
    created_at: datetime


# ---------------------------------------------------------------------------
# Non-mutating layered override
# ---------------------------------------------------------------------------


class RuleOverride(BaseModel):
    """Non-mutating layered override record.

    Source records (RuleChunk, MechanicalEntity) are never modified after
    creation.  All layered changes are expressed as RuleOverride rows.

    Exactly one of ``target_chunk_id`` or ``target_entity_id`` must be set.
    This invariant is enforced at the model layer and in the database via a
    check constraint.

    Override precedence resolution lives in the service layer; callers do
    not reimplement it.

    Entity-targeting override patch semantics (structured patch shapes) are
    deferred.  Entity-targeting overrides in this issue carry a plain content
    payload only.  See ADR-0007.
    """

    override_id: UUID = Field(default_factory=uuid4)
    rules_package_id: UUID
    target_chunk_id: UUID | None = None
    target_entity_id: UUID | None = None
    override_origin: OverrideOriginEnum
    override_operation: OverrideOperationEnum
    # JSON-serialised payload.  For chunk targets: ChunkOverridePayload.
    # For entity targets: {"content": "<text>"} (deferred typed patch shape).
    override_payload: str
    precedence: int
    is_enabled: bool = True
    created_at: datetime

    @model_validator(mode="after")
    def exactly_one_target(self) -> Self:
        """Exactly one of target_chunk_id or target_entity_id must be set."""
        chunk_set = self.target_chunk_id is not None
        entity_set = self.target_entity_id is not None
        if chunk_set == entity_set:
            raise ValueError(
                "Exactly one of target_chunk_id or target_entity_id must be set; "
                f"got chunk={self.target_chunk_id!r}, entity={self.target_entity_id!r}"
            )
        return self


# ---------------------------------------------------------------------------
# Service return types — stable named Pydantic models
# ---------------------------------------------------------------------------


class ChunksResult(BaseModel):
    """Return type for RulesPackageService.get_chunks_by_subsystem."""

    package_id: UUID
    subsystem: RuleSubsystemEnum
    chunks: list[RuleChunk]


class AppliedChunk(BaseModel):
    """A rule chunk with active overrides applied in precedence order."""

    chunk: RuleChunk
    applied_content: str  # Content after override layering; empty if disabled
    is_disabled: bool  # True when a disable override is active
    override_ids_applied: list[UUID]


class AppliedEntity(BaseModel):
    """A mechanical entity with active overrides recorded.

    Entity override patch semantics are deferred (see ADR-0007).  This
    records which overrides are active; the Context Builder applies them
    when structured patch shapes are defined in the issue that first
    requires them.
    """

    entity: MechanicalEntity
    override_ids_applied: list[UUID]


class ActiveRuleSlice(BaseModel):
    """Stable named typed payload returned by get_active_rule_slice.

    This is the return type the Context Builder (Issue 8) will consume.
    It contains rule chunks filtered by subsystem and specific mechanical
    entities, with chunk override layering applied in precedence order.

    Deterministic lookup against provided subsystem/entity references only.
    Not a semantic search result — semantic retrieval belongs to Issue 18.
    """

    package_id: UUID
    chunks: list[AppliedChunk]
    entities: list[AppliedEntity]
