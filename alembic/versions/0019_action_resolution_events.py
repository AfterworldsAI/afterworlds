"""Action-resolution event ledger — CRD Issue 15b (ADR-015b 15b-34).

Creates ``action_resolution_events``: an append-only ledger of accepted
mechanical outcomes (rolls, adjustments, mechanical decisions), written
inside the intermediate transaction that advances an
``ActionResolutionSequence`` — distinct from ``rpg_roll_audit``, which
remains the sole final delivered-result audit written only inside the
final delivery transaction (ADR-015 Decision 1). See ADR-015b's "Audit
Contract" and "Final Audit Projection" sections.

UPDATE and DELETE are prevented by DB-layer triggers, the same pattern
``rpg_roll_audit`` already uses (migration 0011). The unique index on
``(sequence_id, event_order)`` is the DB-level backstop against a duplicate
or racing event write for the same sequence position.

Revision ID: 0019
Revises: 0018
Create Date: 2026-07-14
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0019"
down_revision: str | None = "0018"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLE = "action_resolution_events"


def upgrade() -> None:
    op.create_table(
        _TABLE,
        sa.Column("event_id", sa.String(36), primary_key=True),
        sa.Column("sequence_id", sa.String(36), nullable=False),
        sa.Column("step_id", sa.String(36), nullable=False),
        sa.Column("story_id", sa.String(36), nullable=False),
        sa.Column("session_id", sa.String(36), nullable=False),
        sa.Column("character_id", sa.String(36), nullable=False),
        sa.Column("event_order", sa.Integer, nullable=False),
        sa.Column("kind", sa.String(24), nullable=False),
        sa.Column("mechanical_provenance", sa.Text, nullable=False),
        sa.Column("provisional_effects_json", sa.Text, nullable=False),
        sa.Column("created_at", sa.String(64), nullable=False),
        sa.Column("payload_json", sa.Text, nullable=False),
        sa.Column("schema_version", sa.Integer, nullable=False, server_default="1"),
    )
    op.create_index(
        "uq_action_resolution_events_sequence_order",
        _TABLE,
        ["sequence_id", "event_order"],
        unique=True,
    )

    op.execute(f"""
        CREATE TRIGGER prevent_{_TABLE}_update
        BEFORE UPDATE ON {_TABLE}
        BEGIN
            SELECT RAISE(ABORT, '{_TABLE} is append-only: UPDATE is forbidden');
        END
        """)
    op.execute(f"""
        CREATE TRIGGER prevent_{_TABLE}_delete
        BEFORE DELETE ON {_TABLE}
        BEGIN
            SELECT RAISE(ABORT, '{_TABLE} is append-only: DELETE is forbidden');
        END
        """)


def downgrade() -> None:
    op.execute(f"DROP TRIGGER IF EXISTS prevent_{_TABLE}_delete")
    op.execute(f"DROP TRIGGER IF EXISTS prevent_{_TABLE}_update")
    op.drop_index("uq_action_resolution_events_sequence_order", table_name=_TABLE)
    op.drop_table(_TABLE)
