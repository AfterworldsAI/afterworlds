"""ORM models for the Rules Package — mechanical canon subsystem.

ARCHITECTURE INVARIANT:
  Rules Package tables (prefix ``rp_``) are structurally separate from:
  - Story Bible tables (prefix ``sb_``)
  - Story hierarchy tables (stories, arcs, chapters, nodes, turns)
  - Session state tables

  No ``rp_*`` table carries a FK to any of the above.  Cross-subsystem
  references (e.g. the character sheet's ``rules_package_id`` field) are
  stored as plain strings without FK constraints, preserving the structural
  independence of the Rules Package subsystem.

  ``rp_*`` tables may carry FKs to other ``rp_*`` tables — this is
  intra-subsystem cohesion, not cross-subsystem coupling.
"""

from __future__ import annotations

from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from afterworlds.persistence.orm.base import Base


class RulesPackageORM(Base):
    """Persisted RulesPackage row."""

    __tablename__ = "rp_packages"

    rules_package_id: Mapped[str] = mapped_column(sa.String(36), primary_key=True)
    name: Mapped[str] = mapped_column(sa.Text, nullable=False)
    system: Mapped[str] = mapped_column(sa.String(32), nullable=False)
    version: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    is_enabled: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=True)
    publication_status: Mapped[str] = mapped_column(
        sa.String(32), nullable=False, default="draft"
    )
    published_at: Mapped[str | None] = mapped_column(sa.String(64), nullable=True)
    created_at: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    updated_at: Mapped[str] = mapped_column(sa.String(64), nullable=False)


class RuleSourceORM(Base):
    """Persisted RuleSource row — immutable after creation.

    ``category`` classifies the source type; ``precedence_rank`` determines
    authority ordering.  These are separate concerns — do not infer
    winning-rule behaviour from category alone.
    """

    __tablename__ = "rp_sources"
    __table_args__ = (
        sa.UniqueConstraint(
            "rules_package_id", "source_id", name="uq_rp_sources_package_source"
        ),
    )

    source_id: Mapped[str] = mapped_column(sa.String(36), primary_key=True)
    rules_package_id: Mapped[str] = mapped_column(
        sa.String(36),
        sa.ForeignKey("rp_packages.rules_package_id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(sa.Text, nullable=False)
    category: Mapped[str] = mapped_column(sa.String(32), nullable=False)
    precedence_rank: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    is_enabled: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=True)
    created_at: Mapped[str] = mapped_column(sa.String(64), nullable=False)


class RuleChunkORM(Base):
    """Persisted RuleChunk row — immutable after creation.

    ``source_id`` is non-nullable by design: every chunk belongs to a named
    source document.  Orphaned chunks (no source membership) are forbidden.
    See ADR-0008.

    Source provenance fields (``source_document``, ``source_locator_type``,
    ``source_locator_value``) are non-nullable.
    """

    __tablename__ = "rp_chunks"
    __table_args__ = (
        sa.UniqueConstraint(
            "rules_package_id", "chunk_id", name="uq_rp_chunks_package_chunk"
        ),
        sa.ForeignKeyConstraint(
            ["rules_package_id", "source_id"],
            ["rp_sources.rules_package_id", "rp_sources.source_id"],
            ondelete="CASCADE",
            name="fk_rp_chunks_package_source",
        ),
    )

    chunk_id: Mapped[str] = mapped_column(sa.String(36), primary_key=True)
    rules_package_id: Mapped[str] = mapped_column(
        sa.String(36),
        sa.ForeignKey("rp_packages.rules_package_id", ondelete="CASCADE"),
        nullable=False,
    )
    source_id: Mapped[str] = mapped_column(sa.String(36), nullable=False)
    subsystem: Mapped[str] = mapped_column(sa.String(32), nullable=False)
    content: Mapped[str] = mapped_column(sa.Text, nullable=False)
    source_document: Mapped[str] = mapped_column(sa.Text, nullable=False)
    source_locator_type: Mapped[str] = mapped_column(sa.String(32), nullable=False)
    source_locator_value: Mapped[str] = mapped_column(sa.Text, nullable=False)
    source_section_label: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    is_enabled: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=True)
    created_at: Mapped[str] = mapped_column(sa.String(64), nullable=False)


class MechanicalEntityORM(Base):
    """Persisted MechanicalEntity row — immutable after creation.

    ``structured_data`` is a JSON column holding the typed entity data dict.
    The service layer deserialises it to the correct typed Pydantic model
    using ``entity_type`` as the discriminator.

    ``source_id`` is non-nullable by design.  See ADR-0008.
    Source provenance fields are non-nullable.
    """

    __tablename__ = "rp_mechanical_entities"
    __table_args__ = (
        sa.UniqueConstraint(
            "rules_package_id",
            "entity_id",
            name="uq_rp_entities_package_entity",
        ),
        sa.ForeignKeyConstraint(
            ["rules_package_id", "source_id"],
            ["rp_sources.rules_package_id", "rp_sources.source_id"],
            ondelete="CASCADE",
            name="fk_rp_mechanical_entities_package_source",
        ),
    )

    entity_id: Mapped[str] = mapped_column(sa.String(36), primary_key=True)
    rules_package_id: Mapped[str] = mapped_column(
        sa.String(36),
        sa.ForeignKey("rp_packages.rules_package_id", ondelete="CASCADE"),
        nullable=False,
    )
    source_id: Mapped[str] = mapped_column(sa.String(36), nullable=False)
    entity_type: Mapped[str] = mapped_column(sa.String(32), nullable=False)
    name: Mapped[str] = mapped_column(sa.Text, nullable=False)
    structured_data: Mapped[dict[str, Any]] = mapped_column(sa.JSON, nullable=False)
    source_document: Mapped[str] = mapped_column(sa.Text, nullable=False)
    source_locator_type: Mapped[str] = mapped_column(sa.String(32), nullable=False)
    source_locator_value: Mapped[str] = mapped_column(sa.Text, nullable=False)
    source_section_label: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    is_enabled: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=True)
    created_at: Mapped[str] = mapped_column(sa.String(64), nullable=False)


class RuleOverrideORM(Base):
    """Persisted RuleOverride row — non-mutating layered override record.

    Exactly one of ``target_chunk_id`` or ``target_entity_id`` must be set.
    Enforced by a DB-level check constraint and the Pydantic model validator.

    Override precedence resolution lives in the service layer.
    """

    __tablename__ = "rp_overrides"
    __table_args__ = (
        sa.CheckConstraint(
            "(target_chunk_id IS NULL AND target_entity_id IS NOT NULL)"
            " OR (target_chunk_id IS NOT NULL AND target_entity_id IS NULL)",
            name="ck_rp_overrides_exactly_one_target",
        ),
        # Composite FKs enforce that target belongs to the same package as
        # the override.  NULL target_chunk_id / target_entity_id is exempt
        # from FK checking per SQL standard (the other column is set instead).
        sa.ForeignKeyConstraint(
            ["rules_package_id", "target_chunk_id"],
            ["rp_chunks.rules_package_id", "rp_chunks.chunk_id"],
            ondelete="CASCADE",
            name="fk_rp_overrides_package_chunk",
        ),
        sa.ForeignKeyConstraint(
            ["rules_package_id", "target_entity_id"],
            [
                "rp_mechanical_entities.rules_package_id",
                "rp_mechanical_entities.entity_id",
            ],
            ondelete="CASCADE",
            name="fk_rp_overrides_package_entity",
        ),
    )

    override_id: Mapped[str] = mapped_column(sa.String(36), primary_key=True)
    rules_package_id: Mapped[str] = mapped_column(
        sa.String(36),
        sa.ForeignKey("rp_packages.rules_package_id", ondelete="CASCADE"),
        nullable=False,
    )
    target_chunk_id: Mapped[str | None] = mapped_column(sa.String(36), nullable=True)
    target_entity_id: Mapped[str | None] = mapped_column(sa.String(36), nullable=True)
    override_origin: Mapped[str] = mapped_column(sa.String(32), nullable=False)
    override_operation: Mapped[str] = mapped_column(sa.String(32), nullable=False)
    # JSON-serialised payload string.
    # Chunk targets: serialised ChunkOverridePayload.
    # Entity targets: {"content": "<text>"} — deferred structured patch shape.
    override_payload: Mapped[str] = mapped_column(sa.Text, nullable=False)
    precedence: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    is_enabled: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=True)
    created_at: Mapped[str] = mapped_column(sa.String(64), nullable=False)
