"""Runtime mechanical authority: typed overrides and retained override sets.

CRD Issue 5d (#137), PR 3. Adds the runtime half of ADR-005d Decisions 9 and 10:

* ``rp_mech_overrides`` — the mutable authoring surface for typed
  record/component/fact overrides. Separate from ``rp_overrides``, which holds
  the distinct chunk-targeting prose override family and still carries the
  obsolete ``target_entity_id`` column the final legacy-retirement PR removes.
* ``rp_override_set_versions`` / ``rp_override_set_entries`` — the immutable,
  append-only replay evidence an ``override_set_uuid`` names. The version's
  primary key *is* the content-derived identity of the canonical ordered
  override state, so recording an identical state twice is a no-op and two
  different states can never share a version.

Additive only. Nothing existing is altered or dropped, no projection becomes
active by migrating, and the legacy ``MechanicalEntity`` path is untouched.

Revision ID: 0024
Revises: 0023
Create Date: 2026-08-08
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0024"
down_revision: str | None = "0023"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "rp_mech_overrides",
        sa.Column("override_id", sa.String(36), primary_key=True),
        sa.Column(
            "package_uuid",
            sa.String(36),
            sa.ForeignKey("rp_packages.rules_package_id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("release_version", sa.String(64), nullable=False),
        sa.Column("target_kind", sa.String(16), nullable=False),
        sa.Column("target_record_key", sa.String(255), nullable=False),
        sa.Column("target_component_key", sa.String(255), nullable=True),
        sa.Column("target_fact_key", sa.String(32), nullable=True),
        sa.Column("override_origin", sa.String(32), nullable=False),
        sa.Column("override_operation", sa.String(16), nullable=False),
        sa.Column("payload", sa.JSON, nullable=False),
        sa.Column("precedence", sa.Integer, nullable=False),
        sa.Column(
            "is_enabled", sa.Boolean, nullable=False, server_default=sa.true()
        ),
        sa.Column("created_at", sa.String(64), nullable=False),
        sa.Column("created_by", sa.String(255), nullable=True),
        sa.Column("note", sa.Text, nullable=True),
    )

    op.create_table(
        "rp_override_set_versions",
        sa.Column("override_set_uuid", sa.String(36), primary_key=True),
        sa.Column(
            "package_uuid",
            sa.String(36),
            sa.ForeignKey("rp_packages.rules_package_id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("release_version", sa.String(64), nullable=False),
        sa.Column("entry_count", sa.Integer, nullable=False),
        sa.Column("recorded_at", sa.String(64), nullable=False),
    )

    op.create_table(
        "rp_override_set_entries",
        sa.Column("row_id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "override_set_uuid",
            sa.String(36),
            sa.ForeignKey(
                "rp_override_set_versions.override_set_uuid", ondelete="CASCADE"
            ),
            nullable=False,
            index=True,
        ),
        sa.Column("apply_order", sa.Integer, nullable=False),
        sa.Column("override_id", sa.String(36), nullable=False),
        sa.Column("override_origin", sa.String(32), nullable=False),
        sa.Column("target_kind", sa.String(16), nullable=False),
        sa.Column("target_record_key", sa.String(255), nullable=False),
        sa.Column("target_component_key", sa.String(255), nullable=True),
        sa.Column("target_fact_key", sa.String(32), nullable=True),
        sa.Column("override_operation", sa.String(16), nullable=False),
        sa.Column("precedence", sa.Integer, nullable=False),
        sa.Column("is_enabled", sa.Boolean, nullable=False),
        sa.Column("payload", sa.JSON, nullable=False),
        sa.UniqueConstraint(
            "override_set_uuid", "apply_order", name="uq_rp_override_set_entry_order"
        ),
    )


def downgrade() -> None:
    op.drop_table("rp_override_set_entries")
    op.drop_table("rp_override_set_versions")
    op.drop_table("rp_mech_overrides")
