"""Runtime entitlement state and event log — CRD Issue 13.

Creates ``entitlement_event`` (append-only, INTEGER PRIMARY KEY rowid alias,
UUID event_id with UNIQUE constraint) and ``runtime_entitlement_state`` (one row
per Sojourner, mutable only via ``EntitlementService.receive_entitlement_event``).

Adds partial unique indexes for idempotency and credit-deduction deduplication,
regular indexes for query performance, and SQLite triggers that prevent UPDATE and
DELETE on ``entitlement_event`` at the DB layer.

Revision ID: 0009
Revises: 0008
Create Date: 2026-06-05
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0009"
down_revision: Union[str, None] = "0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # entitlement_event — must be created before runtime_entitlement_state
    # because runtime_entitlement_state.last_entitlement_event_id FK
    # references entitlement_event.event_id.
    # ------------------------------------------------------------------
    op.create_table(
        "entitlement_event",
        # INTEGER PRIMARY KEY = SQLite rowid alias; auto-increments without
        # AUTOINCREMENT keyword.  Do NOT use BIGINT or UUID for this column.
        sa.Column("global_sequence", sa.Integer, primary_key=True),
        sa.Column("event_id", sa.String(36), nullable=False),
        sa.Column("sojourner_id", sa.String(36), nullable=False),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("turn_id", sa.String(36), nullable=True),
        sa.Column("idempotency_key", sa.String(255), nullable=True),
        sa.Column("payload_json", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )

    # event_id must be unique; external references use this column.
    op.create_index(
        "ix_entitlement_event_event_id",
        "entitlement_event",
        ["event_id"],
        unique=True,
    )
    # sojourner, turn, and created_at indexes for query performance.
    op.create_index(
        "ix_entitlement_event_sojourner_id",
        "entitlement_event",
        ["sojourner_id"],
    )
    op.create_index(
        "ix_entitlement_event_turn_id",
        "entitlement_event",
        ["turn_id"],
    )
    op.create_index(
        "ix_entitlement_event_created_at",
        "entitlement_event",
        ["created_at"],
    )

    # Unique partial index on idempotency_key (non-null only) — prevents
    # duplicate external event inserts while allowing NULL for internal events.
    op.execute(
        "CREATE UNIQUE INDEX ix_entitlement_event_idempotency_key "
        "ON entitlement_event (idempotency_key) "
        "WHERE idempotency_key IS NOT NULL"
    )

    # Unique partial index on (sojourner_id, turn_id, event_type) for
    # credit_deduction — enforces one settlement per turn at the DB layer.
    op.execute(
        "CREATE UNIQUE INDEX ix_entitlement_event_credit_deduction "
        "ON entitlement_event (sojourner_id, turn_id, event_type) "
        "WHERE event_type = 'credit_deduction'"
    )

    # Append-only triggers: prevent UPDATE and DELETE on entitlement_event.
    op.execute(
        """
        CREATE TRIGGER prevent_entitlement_event_update
        BEFORE UPDATE ON entitlement_event
        BEGIN
            SELECT RAISE(ABORT, 'entitlement_event is append-only: UPDATE is forbidden');
        END
        """
    )
    op.execute(
        """
        CREATE TRIGGER prevent_entitlement_event_delete
        BEFORE DELETE ON entitlement_event
        BEGIN
            SELECT RAISE(ABORT, 'entitlement_event is append-only: DELETE is forbidden');
        END
        """
    )

    # ------------------------------------------------------------------
    # runtime_entitlement_state — one row per Sojourner
    # ------------------------------------------------------------------
    op.create_table(
        "runtime_entitlement_state",
        sa.Column("sojourner_id", sa.String(36), primary_key=True),
        sa.Column("hosted_access_active", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("hosted_access_plan", sa.String(64), nullable=True),
        # Numeric(12, 4) for credit balances; may go negative (Owner Decision #3).
        sa.Column(
            "hosted_credit_balance",
            sa.Numeric(12, 4),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "top_up_credit_balance",
            sa.Numeric(12, 4),
            nullable=False,
            server_default="0",
        ),
        sa.Column("byok_license_active", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("byok_license_purchased_at", sa.DateTime, nullable=True),
        sa.Column("cloud_services_active", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("cloud_services_expires_at", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        # FK to entitlement_event.event_id (UNIQUE column, not PK).
        sa.Column(
            "last_entitlement_event_id",
            sa.String(36),
            sa.ForeignKey("entitlement_event.event_id"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_table("runtime_entitlement_state")

    # Drop triggers before dropping the table.
    op.execute("DROP TRIGGER IF EXISTS prevent_entitlement_event_delete")
    op.execute("DROP TRIGGER IF EXISTS prevent_entitlement_event_update")

    # Drop partial indexes (created with raw SQL; must be dropped with raw SQL).
    op.execute("DROP INDEX IF EXISTS ix_entitlement_event_credit_deduction")
    op.execute("DROP INDEX IF EXISTS ix_entitlement_event_idempotency_key")

    op.drop_index("ix_entitlement_event_created_at", table_name="entitlement_event")
    op.drop_index("ix_entitlement_event_turn_id", table_name="entitlement_event")
    op.drop_index("ix_entitlement_event_sojourner_id", table_name="entitlement_event")
    op.drop_index("ix_entitlement_event_event_id", table_name="entitlement_event")

    op.drop_table("entitlement_event")
