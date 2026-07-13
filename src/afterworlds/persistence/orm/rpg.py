"""ORM models for RPG adjudication audit log, pending roll requests, and
action-resolution sequences.

CRD Issue 15. Revised by CRD Issue 15b (structured roll instructions,
action-resolution sequences, player-roll lifecycle completion — ADR-015b).
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

    CRD Issue 15b columns (``sequence_id`` through ``raw_values_complete``)
    are nullable for legacy-row compatibility. Migration must use plain
    ``op.add_column`` for these — NOT ``batch_alter_table`` — because SQLite
    batch mode is copy-and-swap and does not reflect triggers onto the new
    table, which would silently drop the append-only guard above.
    ``submission_source`` enforces, for new rows: PLAYER source implies
    INLINE_UI or PHYSICAL_SELF_REPORT; AI/HIDDEN source implies
    BACKEND_DICE_SERVICE. Legacy rows may retain ``submission_source = NULL``.
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

    # -- CRD Issue 15b additions (nullable; legacy rows leave these NULL) ----
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


class PendingRollRequestORM(Base):
    """Persisted state for a player-roll request, linked to its sequence.

    Revised by CRD Issue 15b per ADR-015b's Column Disposition table. Retired
    display/derivation columns (``roll_expression``, ``expected_value_shape``,
    ``visible_modifier_total``, ``visible_modifier_breakdown_json``,
    ``check_label``, ``player_facing_instruction``, ``visible_modifier_note``,
    ``hidden_modifier_present``) are dropped after migration backfill; display
    text now derives from ``instruction_snapshot_json``. New rows require
    ``sequence_id``/``step_id``/``instruction_id``/``instruction_revision``/
    ``instruction_schema_version``/``instruction_snapshot_json``; legacy
    consumed rows may retain nullable sequence/instruction linkage.
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

    # -- CRD Issue 15b: structured instruction linkage -----------------------
    sequence_id: Mapped[str | None] = mapped_column(
        sa.String(36),
        sa.ForeignKey("action_resolution_sequences.sequence_id", ondelete="CASCADE"),
        nullable=True,
    )
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
    """Persisted unit spanning one declared action or mechanically linked action group.

    CRD Issue 15b. At most one unresolved sequence exists per story, enforced
    by the partial unique index below over ``active``/``ready_for_narration``
    statuses — the same pattern already used by
    ``uq_pending_roll_requests_story_active``.

    ``current_pending_roll_request_id`` and ``current_decision_request_id``
    are plain UUID-string pointers, not FK-constrained: the integrity
    direction that matters is ``PendingRollRequestORM.sequence_id -> here``,
    not the reverse, and a real reverse FK would create a circular
    table-creation dependency for no correctness benefit. Identity, status,
    and the pending-interaction pointers are real typed/queryable columns;
    ``resolved_steps_json``/``projected_state_json``/``provisional_effects_json``
    are JSON blobs because they are only ever loaded whole and interpreted in
    Python by ``ActionResolutionService`` — never queried or indexed by SQL —
    matching this module's existing convention for similar payloads
    (``raw_rolls_json``, ``modifiers_json``, ``sheet_effects_json``).
    ``current_decision_snapshot_json`` similarly holds the small ephemeral
    prompt/options payload for a pending mechanical decision; a dedicated
    child table for a single-slot-per-sequence value would be unjustified.
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
    )
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

    status: Mapped[str] = mapped_column(
        sa.String(24), nullable=False, server_default="active"
    )
    current_interaction_kind: Mapped[str] = mapped_column(
        sa.String(16), nullable=False, server_default="none"
    )
    current_pending_roll_request_id: Mapped[str | None] = mapped_column(
        sa.String(36), nullable=True
    )
    current_decision_request_id: Mapped[str | None] = mapped_column(
        sa.String(36), nullable=True
    )
    current_decision_snapshot_json: Mapped[str | None] = mapped_column(
        sa.Text, nullable=True
    )

    resolved_steps_json: Mapped[str] = mapped_column(
        sa.Text, nullable=False, server_default="[]"
    )
    projected_state_json: Mapped[str] = mapped_column(
        sa.Text, nullable=False, server_default="{}"
    )
    provisional_effects_json: Mapped[str] = mapped_column(
        sa.Text, nullable=False, server_default="[]"
    )

    created_at: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    updated_at: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    schema_version: Mapped[int] = mapped_column(
        sa.Integer, nullable=False, server_default="1"
    )
