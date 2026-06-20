"""RPG adjudication tables and session-state extension — CRD Issue 15.

Creates four new tables and extends one existing table:
  - ``dnd5e_active_conditions``: sheet-owned active conditions/effects (child
    table of ``dnd5e_character_sheets``).
  - ``rpg_roll_audit``: append-only audit log of all resolved adjudication
    rolls; UPDATE and DELETE prevented by DB-layer triggers.
  - ``pending_roll_requests``: player-roll announce/consume lifecycle state.

Extends one existing table:
  - ``rpg_session_states``: adds play_status, setup_phase, gm_cheating, tone,
    session_type, genre_flavor, house_rules, and acceptable_content columns.
    All new columns have server-default values for existing rows.

Revision ID: 0011
Revises: 0010
Create Date: 2026-06-20
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0011"
down_revision: Union[str, None] = "0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # Extend rpg_session_states with play-status and configuration columns.
    # All new columns use server_default so existing rows remain valid.
    # ------------------------------------------------------------------
    op.add_column(
        "rpg_session_states",
        sa.Column(
            "play_status",
            sa.String(16),
            nullable=False,
            server_default="setup",
        ),
    )
    op.add_column(
        "rpg_session_states",
        sa.Column(
            "setup_phase",
            sa.String(32),
            nullable=False,
            server_default="world_setup",
        ),
    )
    op.add_column(
        "rpg_session_states",
        sa.Column(
            "gm_cheating",
            sa.Boolean,
            nullable=False,
            server_default="1",
        ),
    )
    op.add_column(
        "rpg_session_states",
        sa.Column(
            "tone",
            sa.String(16),
            nullable=False,
            server_default="balanced",
        ),
    )
    op.add_column(
        "rpg_session_states",
        sa.Column(
            "session_type",
            sa.String(32),
            nullable=False,
            server_default="open_ended",
        ),
    )
    op.add_column(
        "rpg_session_states",
        sa.Column("genre_flavor", sa.Text, nullable=True),
    )
    op.add_column(
        "rpg_session_states",
        sa.Column("house_rules", sa.Text, nullable=True),
    )
    op.add_column(
        "rpg_session_states",
        sa.Column("acceptable_content", sa.Text, nullable=True),
    )

    # ------------------------------------------------------------------
    # dnd5e_active_conditions — sheet-owned active conditions/effects
    # FK → dnd5e_character_sheets.sheet_id (CASCADE on delete).
    # ------------------------------------------------------------------
    op.create_table(
        "dnd5e_active_conditions",
        sa.Column("condition_id", sa.String(36), primary_key=True),
        sa.Column(
            "sheet_id",
            sa.String(36),
            sa.ForeignKey("dnd5e_character_sheets.sheet_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("identifier", sa.String(128), nullable=False),
        sa.Column("display_label", sa.Text, nullable=False),
        sa.Column("source", sa.Text, nullable=False),
        sa.Column("visibility", sa.String(16), nullable=False),
        sa.Column("duration_policy", sa.Text, nullable=True),
        sa.Column("applied_turn_id", sa.String(36), nullable=True),
        sa.Column("rules_package_ref", sa.Text, nullable=True),
        sa.Column(
            "schema_version", sa.Integer, nullable=False, server_default="1"
        ),
    )
    op.create_index(
        "ix_dnd5e_active_conditions_sheet_id",
        "dnd5e_active_conditions",
        ["sheet_id"],
    )
    op.create_index(
        "ix_dnd5e_active_conditions_identifier",
        "dnd5e_active_conditions",
        ["sheet_id", "identifier"],
    )

    # ------------------------------------------------------------------
    # rpg_roll_audit — append-only audit log
    # INTEGER PRIMARY KEY = SQLite rowid alias; auto-increments without
    # AUTOINCREMENT keyword.  Do NOT use BIGINT or UUID for this column.
    # ------------------------------------------------------------------
    op.create_table(
        "rpg_roll_audit",
        sa.Column("global_sequence", sa.Integer, primary_key=True),
        sa.Column(
            "turn_id",
            sa.String(36),
            sa.ForeignKey("turns.turn_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("story_id", sa.String(36), nullable=False),
        sa.Column("session_id", sa.String(36), nullable=False),
        sa.Column("character_id", sa.String(36), nullable=False),
        sa.Column("check_label", sa.Text, nullable=False),
        sa.Column("visibility", sa.String(16), nullable=False),
        sa.Column("expression", sa.String(64), nullable=False),
        sa.Column("raw_rolls_json", sa.Text, nullable=False),
        sa.Column("modifiers_json", sa.Text, nullable=False),
        sa.Column("total", sa.Integer, nullable=False),
        sa.Column("dc", sa.Integer, nullable=True),
        sa.Column("outcome", sa.String(32), nullable=False),
        sa.Column("source", sa.String(16), nullable=False),
        sa.Column("gm_cheating_at_roll", sa.Boolean, nullable=False),
        sa.Column("sheet_effects_json", sa.Text, nullable=False),
        sa.Column("created_at", sa.String(64), nullable=False),
    )
    op.create_index(
        "ix_rpg_roll_audit_turn_id",
        "rpg_roll_audit",
        ["turn_id"],
    )
    op.create_index(
        "ix_rpg_roll_audit_story_id",
        "rpg_roll_audit",
        ["story_id"],
    )

    # Append-only triggers: prevent UPDATE and DELETE on rpg_roll_audit.
    op.execute(
        """
        CREATE TRIGGER prevent_rpg_roll_audit_update
        BEFORE UPDATE ON rpg_roll_audit
        BEGIN
            SELECT RAISE(ABORT, 'rpg_roll_audit is append-only: UPDATE is forbidden');
        END
        """
    )
    op.execute(
        """
        CREATE TRIGGER prevent_rpg_roll_audit_delete
        BEFORE DELETE ON rpg_roll_audit
        BEGIN
            SELECT RAISE(ABORT, 'rpg_roll_audit is append-only: DELETE is forbidden');
        END
        """
    )

    # ------------------------------------------------------------------
    # pending_roll_requests — player-roll announce/consume lifecycle
    # ------------------------------------------------------------------
    op.create_table(
        "pending_roll_requests",
        sa.Column("request_id", sa.String(36), primary_key=True),
        sa.Column(
            "story_id",
            sa.String(36),
            sa.ForeignKey("stories.story_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("session_id", sa.String(36), nullable=False),
        sa.Column(
            "character_id",
            sa.String(36),
            sa.ForeignKey(
                "rpg_character_sheet_bases.sheet_id", ondelete="RESTRICT"
            ),
            nullable=False,
        ),
        sa.Column(
            "originating_turn_id",
            sa.String(36),
            sa.ForeignKey("turns.turn_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "consumed_turn_id",
            sa.String(36),
            sa.ForeignKey("turns.turn_id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("check_label", sa.Text, nullable=False),
        sa.Column("player_facing_instruction", sa.Text, nullable=False),
        sa.Column("expected_value_shape", sa.Text, nullable=False),
        sa.Column("visible_modifier_note", sa.Text, nullable=True),
        sa.Column("visibility", sa.String(16), nullable=False),
        sa.Column("source_proposal_ref", sa.Text, nullable=False),
        sa.Column(
            "status", sa.String(16), nullable=False, server_default="pending"
        ),
        sa.Column("created_at", sa.String(64), nullable=False),
        sa.Column(
            "schema_version", sa.Integer, nullable=False, server_default="1"
        ),
        sa.Column("roll_expression", sa.String(64), nullable=False),
        sa.Column("visible_modifier_total", sa.Integer, nullable=True),
        sa.Column("visible_modifier_breakdown_json", sa.Text, nullable=True),
        sa.Column(
            "hidden_modifier_present",
            sa.Boolean,
            nullable=False,
            server_default="0",
        ),
        sa.Column("adapter_context_hash", sa.String(64), nullable=True),
        sa.Column("additional_data", sa.JSON, nullable=True),
    )
    op.create_index(
        "ix_pending_roll_requests_story_id",
        "pending_roll_requests",
        ["story_id"],
    )
    op.create_index(
        "ix_pending_roll_requests_status",
        "pending_roll_requests",
        ["story_id", "status"],
    )


def downgrade() -> None:
    op.drop_table("pending_roll_requests")

    # Drop triggers before dropping rpg_roll_audit.
    op.execute("DROP TRIGGER IF EXISTS prevent_rpg_roll_audit_delete")
    op.execute("DROP TRIGGER IF EXISTS prevent_rpg_roll_audit_update")

    op.drop_index("ix_rpg_roll_audit_story_id", table_name="rpg_roll_audit")
    op.drop_index("ix_rpg_roll_audit_turn_id", table_name="rpg_roll_audit")
    op.drop_table("rpg_roll_audit")

    op.drop_index(
        "ix_dnd5e_active_conditions_identifier",
        table_name="dnd5e_active_conditions",
    )
    op.drop_index(
        "ix_dnd5e_active_conditions_sheet_id",
        table_name="dnd5e_active_conditions",
    )
    op.drop_table("dnd5e_active_conditions")

    op.drop_column("rpg_session_states", "acceptable_content")
    op.drop_column("rpg_session_states", "house_rules")
    op.drop_column("rpg_session_states", "genre_flavor")
    op.drop_column("rpg_session_states", "session_type")
    op.drop_column("rpg_session_states", "tone")
    op.drop_column("rpg_session_states", "gm_cheating")
    op.drop_column("rpg_session_states", "setup_phase")
    op.drop_column("rpg_session_states", "play_status")
