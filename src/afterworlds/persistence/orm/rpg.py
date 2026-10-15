"""ORM models for the RPG audit log, pending roll requests, action-resolution
sequences and their append-only event ledger.

CRD Issues 15 and 15b.
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
        sa.ForeignKey("turns.turn_id"),
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
    # CRD Issue 15b (migration 0043): nullable for rows written before it and
    # for rows of a turn resolved without a sequence. A row derived from the
    # event ledger fills every one of them (ADR-015b Final Audit Projection).
    sequence_id: Mapped[str | None] = mapped_column(sa.String(36), nullable=True)
    step_id: Mapped[str | None] = mapped_column(sa.String(36), nullable=True)
    pending_roll_request_id: Mapped[str | None] = mapped_column(
        sa.String(36), nullable=True
    )
    instruction_id: Mapped[str | None] = mapped_column(sa.String(36), nullable=True)
    instruction_revision: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    instruction_schema_version: Mapped[int | None] = mapped_column(
        sa.Integer, nullable=True
    )
    instruction_snapshot_json: Mapped[str | None] = mapped_column(
        sa.Text, nullable=True
    )
    submission_source: Mapped[str | None] = mapped_column(sa.String(24), nullable=True)
    raw_values_complete: Mapped[bool | None] = mapped_column(sa.Boolean, nullable=True)
    #: Set only on a contest-completing roll's row (ADR-015b Group 17).
    contest_resolution_json: Mapped[str | None] = mapped_column(sa.Text, nullable=True)


class PendingRollRequestORM(Base):
    """One player die of an action-resolution sequence (CRD Issue 15b).

    Created when a sequence pauses for the Sojourner's roll, inside the same
    transaction; consumed atomically (``status = 'pending'`` predicate) by the
    accepted submission. ``instruction_snapshot_json`` is the only instruction
    authority (Owner Decision 15b-36 dropped the eight legacy display
    columns). ``schema_version`` is a diagnostic marker (2 with a structured
    instruction); ``adapter_context_hash`` a non-authoritative diagnostic.
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
    visibility: Mapped[str] = mapped_column(sa.String(16), nullable=False)
    source_proposal_ref: Mapped[str] = mapped_column(sa.Text, nullable=False)
    status: Mapped[str] = mapped_column(
        sa.String(16), nullable=False, server_default="pending"
    )
    created_at: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    schema_version: Mapped[int] = mapped_column(
        sa.Integer, nullable=False, server_default="1"
    )
    adapter_context_hash: Mapped[str | None] = mapped_column(
        sa.String(64), nullable=True
    )
    #: The sequence and step this die belongs to (no FK: SQLite cannot drop
    #: a foreign-key column on downgrade; the service writes both together).
    sequence_id: Mapped[str | None] = mapped_column(sa.String(36), nullable=True)
    step_id: Mapped[str | None] = mapped_column(sa.String(36), nullable=True)
    instruction_id: Mapped[str | None] = mapped_column(sa.String(36), nullable=True)
    instruction_revision: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    instruction_schema_version: Mapped[int | None] = mapped_column(
        sa.Integer, nullable=True
    )
    instruction_snapshot_json: Mapped[str | None] = mapped_column(
        sa.Text, nullable=True
    )

    additional_data: Mapped[dict[str, Any] | None] = mapped_column(
        sa.JSON, nullable=True
    )


class ActionResolutionSequenceORM(Base):
    """One declared action or linked action group across deterministic
    interactions (CRD Issue 15b, ADR-015b Group 6).

    Identity, status and the one-pending-interaction pointers are real
    columns; the partial unique index allows one unresolved sequence per
    story. The JSON columns are the sequence's provisional working state
    (no audit weight): its proposals and reads, the operations resolved so
    far, projected state and accumulated provisional effects. ``revision``
    is the compare-and-swap guard of every advancement.
    """

    __tablename__ = "action_resolution_sequences"
    __table_args__ = (
        sa.Index(
            "uq_unresolved_action_resolution_per_story",
            "story_id",
            unique=True,
            sqlite_where=sa.text("status IN ('active', 'ready_for_narration')"),
        ),
    )

    sequence_id: Mapped[str] = mapped_column(sa.String(36), primary_key=True)
    story_id: Mapped[str] = mapped_column(
        sa.String(36),
        sa.ForeignKey("stories.story_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_id: Mapped[str] = mapped_column(sa.String(36), nullable=False)
    node_id: Mapped[str] = mapped_column(
        sa.String(36),
        sa.ForeignKey("nodes.node_id", ondelete="CASCADE"),
        nullable=False,
    )
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
    status: Mapped[str] = mapped_column(sa.String(24), nullable=False)
    current_interaction_kind: Mapped[str] = mapped_column(sa.String(16), nullable=False)
    current_pending_roll_request_id: Mapped[str | None] = mapped_column(
        sa.String(36), nullable=True
    )
    current_decision_request_id: Mapped[str | None] = mapped_column(
        sa.String(36), nullable=True
    )
    current_decision_snapshot_json: Mapped[str | None] = mapped_column(
        sa.Text, nullable=True
    )
    plan_json: Mapped[str] = mapped_column(sa.Text, nullable=False)
    reads_json: Mapped[str] = mapped_column(sa.Text, nullable=False)
    records_json: Mapped[str] = mapped_column(sa.Text, nullable=False)
    unattached_json: Mapped[str] = mapped_column(sa.Text, nullable=False)
    resolved_steps_json: Mapped[str] = mapped_column(sa.Text, nullable=False)
    projected_state_json: Mapped[str] = mapped_column(sa.Text, nullable=False)
    provisional_effects_json: Mapped[str] = mapped_column(sa.Text, nullable=False)
    revision: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    created_at: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    updated_at: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    schema_version: Mapped[int] = mapped_column(
        sa.Integer, nullable=False, server_default="1"
    )


class ActionResolutionEventORM(Base):
    """The append-only action-resolution event ledger (ADR-015b 15b-34).

    One row per accepted roll, adjustment or decision, written in the
    transaction that advances its sequence. UPDATE and DELETE are refused by
    DB-layer triggers (migration 0043); ``(sequence_id, event_order)`` is
    unique. ``payload_json`` is the kind-discriminated payload.
    """

    __tablename__ = "action_resolution_events"
    __table_args__ = (
        sa.Index(
            "uq_action_resolution_events_sequence_order",
            "sequence_id",
            "event_order",
            unique=True,
        ),
    )

    event_id: Mapped[str] = mapped_column(sa.String(36), primary_key=True)
    sequence_id: Mapped[str] = mapped_column(sa.String(36), nullable=False)
    step_id: Mapped[str] = mapped_column(sa.String(36), nullable=False)
    story_id: Mapped[str] = mapped_column(sa.String(36), nullable=False)
    session_id: Mapped[str] = mapped_column(sa.String(36), nullable=False)
    character_id: Mapped[str] = mapped_column(sa.String(36), nullable=False)
    event_order: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    kind: Mapped[str] = mapped_column(sa.String(24), nullable=False)
    mechanical_provenance: Mapped[str] = mapped_column(sa.Text, nullable=False)
    provisional_effects_json: Mapped[str] = mapped_column(sa.Text, nullable=False)
    created_at: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    payload_json: Mapped[str] = mapped_column(sa.Text, nullable=False)
    schema_version: Mapped[int] = mapped_column(
        sa.Integer, nullable=False, server_default="1"
    )
