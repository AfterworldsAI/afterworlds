"""Provider credential metadata, route config, and refusal log — CRD Issue 14a.

Creates three tables:
  - ``provider_credential_metadata``: non-secret observability metadata for
    Sojourner BYOK credentials (no key/hash/token column).
  - ``provider_route_config``: per-Sojourner provider routing configuration
    (model identifiers, active flag).
  - ``provider_refusal_log``: append-only log of provider refusal events;
    coarse and non-sensitive only (no prompts, inputs, excerpts, or key material).

Revision ID: 0010
Revises: 0009
Create Date: 2026-06-10
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0010"
down_revision: Union[str, None] = "0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # provider_credential_metadata
    # ------------------------------------------------------------------
    op.create_table(
        "provider_credential_metadata",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("sojourner_id", sa.String(36), nullable=False),
        sa.Column("provider_name", sa.String(64), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="1"),
        sa.Column(
            "validation_status",
            sa.String(16),
            nullable=False,
            server_default="untested",
        ),
        sa.Column("last_validated_at", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.UniqueConstraint(
            "sojourner_id",
            "provider_name",
            name="uq_credential_sojourner_provider",
        ),
    )

    # ------------------------------------------------------------------
    # provider_route_config
    # ------------------------------------------------------------------
    op.create_table(
        "provider_route_config",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("sojourner_id", sa.String(36), nullable=False),
        sa.Column("provider_name", sa.String(64), nullable=False),
        sa.Column("preferred_model_identifier", sa.String(256), nullable=True),
        sa.Column("fallback_model_identifier", sa.String(256), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="1"),
        sa.UniqueConstraint(
            "sojourner_id",
            "provider_name",
            name="uq_route_config_sojourner_provider",
        ),
    )

    # ------------------------------------------------------------------
    # provider_refusal_log — append-only
    # ------------------------------------------------------------------
    op.create_table(
        "provider_refusal_log",
        # INTEGER PRIMARY KEY = SQLite rowid alias; auto-increments.
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("turn_id", sa.String(36), nullable=True),
        sa.Column("sojourner_id", sa.String(36), nullable=True),
        sa.Column("pass_id", sa.String(32), nullable=False),
        sa.Column("primary_provider_name", sa.String(64), nullable=False),
        sa.Column("primary_model_identifier", sa.String(256), nullable=False),
        sa.Column("refusal_category", sa.String(32), nullable=False),
        sa.Column("fallback_outcome", sa.String(64), nullable=False),
        sa.Column("fallback_provider_name", sa.String(64), nullable=True),
        sa.Column("fallback_model_identifier", sa.String(256), nullable=True),
        sa.Column("coarse_metadata_json", sa.String(1024), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )

    op.create_index(
        "ix_provider_refusal_log_turn_id",
        "provider_refusal_log",
        ["turn_id"],
    )
    op.create_index(
        "ix_provider_refusal_log_sojourner_id",
        "provider_refusal_log",
        ["sojourner_id"],
    )
    op.create_index(
        "ix_provider_refusal_log_created_at",
        "provider_refusal_log",
        ["created_at"],
    )

    # Append-only triggers: prevent UPDATE and DELETE on provider_refusal_log.
    op.execute(
        """
        CREATE TRIGGER prevent_provider_refusal_log_update
        BEFORE UPDATE ON provider_refusal_log
        BEGIN
            SELECT RAISE(ABORT, 'provider_refusal_log is append-only: UPDATE is forbidden');
        END
        """
    )
    op.execute(
        """
        CREATE TRIGGER prevent_provider_refusal_log_delete
        BEFORE DELETE ON provider_refusal_log
        BEGIN
            SELECT RAISE(ABORT, 'provider_refusal_log is append-only: DELETE is forbidden');
        END
        """
    )


def downgrade() -> None:
    # Drop triggers before dropping the table.
    op.execute("DROP TRIGGER IF EXISTS prevent_provider_refusal_log_delete")
    op.execute("DROP TRIGGER IF EXISTS prevent_provider_refusal_log_update")

    op.drop_index("ix_provider_refusal_log_created_at", table_name="provider_refusal_log")
    op.drop_index("ix_provider_refusal_log_sojourner_id", table_name="provider_refusal_log")
    op.drop_index("ix_provider_refusal_log_turn_id", table_name="provider_refusal_log")

    op.drop_table("provider_refusal_log")
    op.drop_table("provider_route_config")
    op.drop_table("provider_credential_metadata")
