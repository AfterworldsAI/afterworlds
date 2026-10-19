"""Rules Package schema — rp_* tables for CRD Issue 5a.

Rules Package tables carry the ``rp_`` prefix to make their separation from
Story Bible tables (``sb_``), session state, and story hierarchy structurally
visible and machine-verifiable.

Architecture invariant:
  No ``rp_*`` table carries a FK to any Story Bible table, session state
  table, or story hierarchy table (stories, arcs, chapters, nodes, turns).
  ``rp_*`` tables may FK to other ``rp_*`` tables.

Revision ID: 0003
Revises: 0002
Create Date: 2026-04-09
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # rp_packages — top-level Rules Package metadata
    # ------------------------------------------------------------------
    op.create_table(
        "rp_packages",
        sa.Column("rules_package_id", sa.String(36), primary_key=True),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("system", sa.String(32), nullable=False),
        sa.Column("version", sa.String(64), nullable=False),
        sa.Column("is_enabled", sa.Boolean, nullable=False, default=True),
        sa.Column("publication_status", sa.String(32), nullable=False, default="draft"),
        sa.Column("published_at", sa.String(64), nullable=True),
        sa.Column("created_at", sa.String(64), nullable=False),
        sa.Column("updated_at", sa.String(64), nullable=False),
    )

    # ------------------------------------------------------------------
    # rp_sources — source-document metadata within a package
    # Immutable after creation.  category ≠ authority ordering.
    # ------------------------------------------------------------------
    op.create_table(
        "rp_sources",
        sa.Column("source_id", sa.String(36), primary_key=True),
        sa.Column(
            "rules_package_id",
            sa.String(36),
            sa.ForeignKey("rp_packages.rules_package_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("category", sa.String(32), nullable=False),
        sa.Column("precedence_rank", sa.Integer, nullable=False),
        sa.Column("is_enabled", sa.Boolean, nullable=False, default=True),
        sa.Column("created_at", sa.String(64), nullable=False),
        sa.UniqueConstraint(
            "rules_package_id",
            "source_id",
            name="uq_rp_sources_package_source",
        ),
    )

    # ------------------------------------------------------------------
    # rp_chunks — atomic rule text units (immutable after creation)
    # source_id is non-nullable by design (ADR-0008).
    # Composite FK enforces that source_id belongs to the same package.
    # ------------------------------------------------------------------
    op.create_table(
        "rp_chunks",
        sa.Column("chunk_id", sa.String(36), primary_key=True),
        sa.Column(
            "rules_package_id",
            sa.String(36),
            sa.ForeignKey("rp_packages.rules_package_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("source_id", sa.String(36), nullable=False),
        sa.UniqueConstraint(
            "rules_package_id", "chunk_id", name="uq_rp_chunks_package_chunk"
        ),
        sa.ForeignKeyConstraint(
            ["rules_package_id", "source_id"],
            ["rp_sources.rules_package_id", "rp_sources.source_id"],
            ondelete="CASCADE",
            name="fk_rp_chunks_package_source",
        ),
        sa.Column("subsystem", sa.String(32), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("source_document", sa.Text, nullable=False),
        sa.Column("source_locator_type", sa.String(32), nullable=False),
        sa.Column("source_locator_value", sa.Text, nullable=False),
        sa.Column("source_section_label", sa.Text, nullable=True),
        sa.Column("is_enabled", sa.Boolean, nullable=False, default=True),
        sa.Column("created_at", sa.String(64), nullable=False),
    )

    # ------------------------------------------------------------------
    # rp_mechanical_entities — typed structured entity records
    # source_id is non-nullable by design (ADR-0008).
    # Composite FK enforces that source_id belongs to the same package.
    # ------------------------------------------------------------------
    op.create_table(
        "rp_mechanical_entities",
        sa.Column("entity_id", sa.String(36), primary_key=True),
        sa.Column(
            "rules_package_id",
            sa.String(36),
            sa.ForeignKey("rp_packages.rules_package_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("source_id", sa.String(36), nullable=False),
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
        sa.Column("entity_type", sa.String(32), nullable=False),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("structured_data", sa.JSON, nullable=False),
        sa.Column("source_document", sa.Text, nullable=False),
        sa.Column("source_locator_type", sa.String(32), nullable=False),
        sa.Column("source_locator_value", sa.Text, nullable=False),
        sa.Column("source_section_label", sa.Text, nullable=True),
        sa.Column("is_enabled", sa.Boolean, nullable=False, default=True),
        sa.Column("created_at", sa.String(64), nullable=False),
    )

    # ------------------------------------------------------------------
    # rp_overrides — non-mutating layered override records
    # Exactly one of target_chunk_id / target_entity_id must be set.
    # ------------------------------------------------------------------
    op.create_table(
        "rp_overrides",
        sa.Column("override_id", sa.String(36), primary_key=True),
        sa.Column(
            "rules_package_id",
            sa.String(36),
            sa.ForeignKey("rp_packages.rules_package_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("target_chunk_id", sa.String(36), nullable=True),
        sa.Column("target_entity_id", sa.String(36), nullable=True),
        sa.Column("override_origin", sa.String(32), nullable=False),
        sa.Column("override_operation", sa.String(32), nullable=False),
        sa.Column("override_payload", sa.Text, nullable=False),
        sa.Column("precedence", sa.Integer, nullable=False),
        sa.Column("is_enabled", sa.Boolean, nullable=False, default=True),
        sa.Column("created_at", sa.String(64), nullable=False),
        sa.CheckConstraint(
            "(target_chunk_id IS NULL AND target_entity_id IS NOT NULL)"
            " OR (target_chunk_id IS NOT NULL AND target_entity_id IS NULL)",
            name="ck_rp_overrides_exactly_one_target",
        ),
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


def downgrade() -> None:
    op.drop_table("rp_overrides")
    op.drop_table("rp_mechanical_entities")
    op.drop_table("rp_chunks")
    op.drop_table("rp_sources")
    op.drop_table("rp_packages")
