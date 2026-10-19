"""Remote account ownership map and store marker -- prerequisite #205.

Adds ``account_resources`` (hosted-account ownership of remote Story roots)
and ``remote_store_marker``. Both start empty: no existing row is assigned an
owner, so a pre-existing Story stays unowned and is inaccessible remotely
(ADR-021 D7). A local deployment never writes either table.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0045"
down_revision: str | None = "0044"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "account_resources",
        sa.Column("mapping_id", sa.String(36), primary_key=True),
        sa.Column("account_id", sa.String(36), nullable=False),
        sa.Column("resource_type", sa.String(16), nullable=False),
        sa.Column("resource_id", sa.String(36), nullable=False),
        sa.Column("ownership_revision", sa.Integer, nullable=False),
        sa.Column("created_at", sa.String(64), nullable=False),
        sa.Column("retired_at", sa.String(64), nullable=True),
        sa.Column("source_operation_ref", sa.String(36), nullable=False),
        sa.UniqueConstraint("resource_type", "resource_id", "ownership_revision"),
    )
    op.create_index(
        "ix_account_resources_account",
        "account_resources",
        ["account_id", "resource_type"],
    )
    # At most one active owner per resource, enforced by the store itself.
    op.create_index(
        "uq_account_resources_active",
        "account_resources",
        ["resource_type", "resource_id"],
        unique=True,
        sqlite_where=sa.text("retired_at IS NULL"),
    )
    op.create_table(
        "remote_store_marker",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("content_store_id", sa.String(36), nullable=False),
        sa.Column("initialized_at", sa.String(64), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("remote_store_marker")
    op.drop_index("uq_account_resources_active", table_name="account_resources")
    op.drop_index("ix_account_resources_account", table_name="account_resources")
    op.drop_table("account_resources")
