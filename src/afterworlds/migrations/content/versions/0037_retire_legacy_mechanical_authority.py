"""Retire the obsolete legacy mechanical-authority tables.

Final CRD Issue 5d cutover (#137 contract 6 and AC22; ADR-005d; Recorded Owner
Decision 2026-09-21). Two tables leave the schema:

* ``rp_mechanical_entities`` — the obsolete prose-only ``MechanicalEntity``
  family. Mechanical authority is the accepted typed projection
  (``rp_mech_*``), read through ``RulesAuthorityService``.
* ``rp_overrides`` — the legacy chunk/entity override authority. Typed
  overrides live in ``rp_mech_overrides`` with retained, replayable
  override-set versions (migration 0024); nothing here reads or migrates the
  legacy rows into them.

**Clean-baseline policy.** Rows in either table are pre-release development
data with no mapping into the typed authority, so they are deleted with their
table and never guessed into new authority (#137 contract 6). Nothing else is
touched: the authoritative source corpus (``rp_packages``, ``rp_sources``,
``rp_chunks``, ``rp_manifests``) and every ``rp_mech_*`` / override-set table
keep their rows and schema.

``rp_overrides`` is dropped first: its composite foreign key references
``rp_mechanical_entities``.

**Downgrade** recreates both tables exactly as migration 0003 defined them
(neither changed afterwards), **empty**. Their former rows are not restorable;
a downgrade only returns the schema to revision 0036 so earlier code can run.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0037"
down_revision: str | None = "0036"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.drop_table("rp_overrides")
    op.drop_table("rp_mechanical_entities")


def downgrade() -> None:
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
