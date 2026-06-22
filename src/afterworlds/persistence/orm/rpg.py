"""ORM models for RPG adjudication audit log and pending roll requests.

CRD Issue 15.
"""

from __future__ import annotations

from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from afterworlds.persistence.orm.base import Base


class RpgRollAuditORM(Base):
    """Append-only audit log of all resolved RPG adjudication rolls.

    ``global_sequence`` is an INTEGER PRIMARY KEY (SQLite rowid alias);
    it auto-increments without the AUTOINCREMENT keyword.  Do NOT use BIGINT
    or UUID for this column.

    UPDATE and DELETE are prevented by DB-layer triggers (see migration 0011).
    Rows are written inside the 12c outer transaction after the provisional
    turn_id exists; they are rolled back atomically with the Turn if any block
    disposition fires.
    """

    __tablename__ = "rpg_roll_audit"

    global_sequence: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    turn_id: Mapped[str] = mapped_column(
        sa.String(36),
        sa.ForeignKey("turns.turn_id", ondelete="CASCADE"),
        nullable=False,
    )
    story_id: Mapped[str] = mapped_column(sa.String(36), nullable=False)
    session_id: Mapped[str] = mapped_column(sa.String(36), nullable=False)
    character_id: Mapped[str] = mapped_column(sa.String(36), nullable=False)
    check_label: Mapped[str] = mapped_column(sa.Text, nullable=False)
    visibility: Mapped[str] = mapped_column(sa.String(16), nullable=False)
    expression: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    raw_rolls_json: Mapped[str] = mapped_column(sa.Text, nullable=False)
    modifiers_json: Mapped[str] = mapped_column(sa.Text, nullable=False)
    total: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    dc: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    outcome: Mapped[str] = mapped_column(sa.String(32), nullable=False)
    source: Mapped[str] = mapped_column(sa.String(16), nullable=False)
    gm_cheating_at_roll: Mapped[bool] = mapped_column(sa.Boolean, nullable=False)
    sheet_effects_json: Mapped[str] = mapped_column(sa.Text, nullable=False)
    created_at: Mapped[str] = mapped_column(sa.String(64), nullable=False)


class PendingRollRequestORM(Base):
    """Persisted state for a player-roll request spanning two turns.

    Created on the announce turn (written inside the 12c outer transaction).
    Consumed on the turn the Sojourner reports the result.

    ``hidden_modifier_present`` is stored for internal audit only and must
    never be exposed in player-facing output, prompts, or delivered turn data.
    """

    __tablename__ = "pending_roll_requests"
    __table_args__ = (
        sa.Index(
            "uq_pending_roll_requests_story_active",
            "story_id",
            unique=True,
            sqlite_where=sa.text("status = 'pending'"),
        ),
    )

    request_id: Mapped[str] = mapped_column(sa.String(36), primary_key=True)
    story_id: Mapped[str] = mapped_column(
        sa.String(36),
        sa.ForeignKey("stories.story_id", ondelete="CASCADE"),
        nullable=False,
    )
    session_id: Mapped[str] = mapped_column(sa.String(36), nullable=False)
    character_id: Mapped[str] = mapped_column(
        sa.String(36),
        sa.ForeignKey("rpg_character_sheet_bases.sheet_id", ondelete="RESTRICT"),
        nullable=False,
    )
    originating_turn_id: Mapped[str] = mapped_column(
        sa.String(36),
        sa.ForeignKey("turns.turn_id", ondelete="CASCADE"),
        nullable=False,
    )
    consumed_turn_id: Mapped[str | None] = mapped_column(
        sa.String(36),
        sa.ForeignKey("turns.turn_id", ondelete="SET NULL"),
        nullable=True,
    )
    check_label: Mapped[str] = mapped_column(sa.Text, nullable=False)
    player_facing_instruction: Mapped[str] = mapped_column(sa.Text, nullable=False)
    expected_value_shape: Mapped[str] = mapped_column(sa.Text, nullable=False)
    visible_modifier_note: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    visibility: Mapped[str] = mapped_column(sa.String(16), nullable=False)
    source_proposal_ref: Mapped[str] = mapped_column(sa.Text, nullable=False)
    status: Mapped[str] = mapped_column(
        sa.String(16), nullable=False, server_default="pending"
    )
    created_at: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    schema_version: Mapped[int] = mapped_column(
        sa.Integer, nullable=False, server_default="1"
    )
    roll_expression: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    visible_modifier_total: Mapped[int | None] = mapped_column(
        sa.Integer, nullable=True
    )
    visible_modifier_breakdown_json: Mapped[str | None] = mapped_column(
        sa.Text, nullable=True
    )
    hidden_modifier_present: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, server_default="0"
    )
    adapter_context_hash: Mapped[str | None] = mapped_column(
        sa.String(64), nullable=True
    )

    additional_data: Mapped[dict[str, Any] | None] = mapped_column(
        sa.JSON, nullable=True
    )
