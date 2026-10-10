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

Final CRD Issue 5d cutover (#137 contract 6, AC22): ``rp_mechanical_entities``
(the obsolete prose-only ``MechanicalEntity`` family) and ``rp_overrides`` (the
legacy chunk/entity override authority) are dropped by migration 0037. Typed
mechanical overrides live in ``rp_mech_overrides``; see
:mod:`afterworlds.persistence.orm.rules_authority`.
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from afterworlds.persistence.orm.base import Base


class RulesPackageORM(Base):
    """Persisted RulesPackage row."""

    __tablename__ = "rp_packages"
    __table_args__ = (
        sa.UniqueConstraint(
            "name",
            "version",
            "system",
            name="uq_rp_packages_name_version_system",
        ),
    )

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
        # Logical-identity uniqueness: (rules_package_id, name) is the natural
        # key for a RuleSource within a package.  Enforces the same dedup key
        # used by IngestionService._upsert_source() at the DB level.
        sa.UniqueConstraint(
            "rules_package_id",
            "name",
            name="uq_rp_sources_name",
        ),
        # Required for the composite FK target from rp_chunks (formerly also
        # rp_mechanical_entities, dropped in 0037).  SQLAlchemy / SQLite
        # require the referenced column set to be covered by a UNIQUE
        # constraint.  Since source_id is
        # already a UUID PK (globally unique), this constraint is redundant as a
        # uniqueness guard but cannot be dropped without breaking the composite
        # FK references above.
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


class RulesPackageManifestORM(Base):
    """Persisted RulesPackageManifest row — one per package, publication gate.

    The manifest carries attribution, licensing, and ingest-completion flags.
    Publication is blocked until both ``sql_ingest_complete`` and
    ``vector_write_complete`` are True.

    One manifest per package is enforced at the DB layer via a UNIQUE constraint
    on ``rules_package_id``.
    """

    __tablename__ = "rp_manifests"
    __table_args__ = (
        sa.UniqueConstraint(
            "rules_package_id",
            name="uq_rp_manifests_package",
        ),
    )

    manifest_id: Mapped[str] = mapped_column(sa.String(36), primary_key=True)
    rules_package_id: Mapped[str] = mapped_column(
        sa.String(36),
        sa.ForeignKey("rp_packages.rules_package_id", ondelete="CASCADE"),
        nullable=False,
    )
    authoritative_source_document: Mapped[str] = mapped_column(sa.Text, nullable=False)
    authoritative_source_version: Mapped[str] = mapped_column(sa.Text, nullable=False)
    package_license: Mapped[str] = mapped_column(sa.Text, nullable=False)
    transform_status: Mapped[str] = mapped_column(sa.Text, nullable=False)
    parsing_convenience_source: Mapped[str | None] = mapped_column(
        sa.Text, nullable=True
    )
    attribution_text: Mapped[str] = mapped_column(sa.Text, nullable=False)
    sql_ingest_complete: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, default=False
    )
    vector_write_complete: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, default=False
    )
    created_at: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    updated_at: Mapped[str] = mapped_column(sa.String(64), nullable=False)
