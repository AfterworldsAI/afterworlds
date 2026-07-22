"""Structured RPG roll lifecycle: action-resolution sequences — CRD Issue 15b.

Creates ``action_resolution_sequences`` (persisted unit spanning one declared
action or mechanically linked action group; at most one unresolved sequence
per story via a partial unique index, mirroring the existing
``uq_pending_roll_requests_story_active`` pattern). ``session_id`` is a real
``NOT NULL`` column from creation (PR #129 remediation — earlier drafts of
this migration added it nullable via a separate follow-up migration 0018;
since neither had merged to main, 0018 is folded in here rather than kept as
a second migration correcting the first).

Revises ``pending_roll_requests`` per ADR-015b's Column Disposition table and
Owner Decision 15b-36 (pre-release clean schema cutover, PR #129
remediation): drops ``roll_expression``, ``expected_value_shape``,
``visible_modifier_total``, ``visible_modifier_breakdown_json``,
``check_label``, ``player_facing_instruction``, ``visible_modifier_note``,
``hidden_modifier_present`` outright. No historical-row conversion is
attempted or promised — Afterworlds has never been deployed or run, and no
supported database is expected to contain a row in the legacy shape. Before
the destructive column drop, this migration asserts ``pending_roll_requests``
is empty and raises, aborting before any ``ALTER TABLE`` runs, if that
precondition is false; a populated table means the pre-release
clean-schema-cutover assumption does not hold for that database, and it must
be reset or migrated separately with a hand-authored, reviewed conversion —
this migration does not improvise one.

``pending_roll_requests`` needs no table recreate for the column changes:
this project's runtime (SQLite >= 3.35, confirmed 3.49.1; SQLAlchemy 2.0;
Alembic 1.18) supports ``ALTER TABLE ... ADD COLUMN`` and
``ALTER TABLE ... DROP COLUMN`` natively, and none of the eight dropped
columns participate in this table's only index
(``uq_pending_roll_requests_story_active``, on ``story_id`` alone) or any
foreign key. Each column add/drop below is a single direct ``ALTER TABLE``
statement — no ``PRAGMA foreign_keys`` toggling, table rename, or row copy.
The table's other columns, its two ``create_index`` indexes, its partial
unique index, and its four foreign keys (all created in migration 0011) are
untouched by this migration and are not recreated here.

``rpg_roll_audit`` gets its new nullable columns via plain ``op.add_column``
(NOT batch mode) because this table has the append-only UPDATE/DELETE
triggers from migration 0011 — SQLite batch mode is copy-and-swap and does
not reflect triggers onto the new table, which would silently drop the
append-only guard. Plain ``ADD COLUMN`` is sufficient here since every new
column is nullable with no default, which SQLite's native ``ALTER TABLE ADD
COLUMN`` supports without a table recreate.

``downgrade()`` re-adds the eight legacy columns and best-effort
reconstructs display text for any row that has a structured
``instruction_snapshot_json`` to reconstruct it from (real post-Phase-2 rows
created by ``ActionResolutionService.start_sequence``, not migration
backfill — this migration performs no backfill). Reconstruction is
inherently lossy for the eight legacy columns' own text where a snapshot
doesn't cover it exactly; rows with no snapshot get the placeholder default.

Revision ID: 0017
Revises: 0016
Create Date: 2026-07-13
"""

from __future__ import annotations

import json
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0017"
down_revision: str | None = "0016"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLE = "pending_roll_requests"

_LEGACY_COLUMNS = (
    "roll_expression",
    "expected_value_shape",
    "visible_modifier_total",
    "visible_modifier_breakdown_json",
    "check_label",
    "player_facing_instruction",
    "visible_modifier_note",
    "hidden_modifier_present",
)


def _assert_pending_roll_requests_empty(conn: sa.engine.Connection) -> None:
    """Owner Decision 15b-36's precondition, enforced before any destructive change.

    Raises rather than coercing to a default shape or silently skipping the
    conversion — a populated table here means the pre-release
    clean-schema-cutover assumption is false for this database.
    """
    count = conn.execute(sa.text(f"SELECT COUNT(*) FROM {_TABLE}")).scalar()
    if count:
        raise RuntimeError(
            f"Migration 0017: {_TABLE!r} contains {count} row(s), but "
            "ADR-015b Owner Decision 15b-36 (pre-release clean schema "
            "cutover) requires this table to be empty before dropping its "
            "eight legacy display/derivation columns -- no supported "
            "database is promised to contain a row in this shape. This "
            "database must be reset (if disposable) or migrated separately "
            "with a hand-authored, reviewed conversion for its existing "
            "row(s) before this migration can run."
        )


def upgrade() -> None:
    # ------------------------------------------------------------------
    # action_resolution_sequences — must exist before pending_roll_requests
    # gains its FK to it. session_id is NOT NULL from creation (PR #129
    # remediation; previously added nullable via a separate migration 0018).
    # ------------------------------------------------------------------
    op.create_table(
        "action_resolution_sequences",
        sa.Column("sequence_id", sa.String(36), primary_key=True),
        sa.Column(
            "story_id",
            sa.String(36),
            sa.ForeignKey("stories.story_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "node_id",
            sa.String(36),
            sa.ForeignKey("nodes.node_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "character_id",
            sa.String(36),
            sa.ForeignKey("rpg_character_sheet_bases.sheet_id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("session_id", sa.String(36), nullable=False),
        sa.Column(
            "originating_turn_id",
            sa.String(36),
            sa.ForeignKey("turns.turn_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(24), nullable=False, server_default="active"),
        sa.Column(
            "current_interaction_kind",
            sa.String(16),
            nullable=False,
            server_default="none",
        ),
        sa.Column("current_pending_roll_request_id", sa.String(36), nullable=True),
        sa.Column("current_decision_request_id", sa.String(36), nullable=True),
        sa.Column("current_decision_snapshot_json", sa.Text, nullable=True),
        sa.Column("resolved_steps_json", sa.Text, nullable=False, server_default="[]"),
        sa.Column("projected_state_json", sa.Text, nullable=False, server_default="{}"),
        sa.Column(
            "provisional_effects_json", sa.Text, nullable=False, server_default="[]"
        ),
        sa.Column("created_at", sa.String(64), nullable=False),
        sa.Column("updated_at", sa.String(64), nullable=False),
        sa.Column("schema_version", sa.Integer, nullable=False, server_default="1"),
    )
    op.create_index(
        "ix_action_resolution_sequences_story_id",
        "action_resolution_sequences",
        ["story_id"],
    )
    op.create_index(
        "ix_action_resolution_sequences_node_id",
        "action_resolution_sequences",
        ["node_id"],
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_unresolved_action_resolution_per_story "
        "ON action_resolution_sequences (story_id) "
        "WHERE status IN ('active', 'ready_for_narration')"
    )

    # ------------------------------------------------------------------
    # pending_roll_requests — add the six new nullable structured columns.
    # Direct ALTER TABLE ADD COLUMN; no recreate needed (see module docstring).
    # Purely additive — safe regardless of the table's row count, so this
    # runs before the zero-row precondition check below, which only guards
    # the destructive column drop.
    #
    # sequence_id carries a foreign key, so it can't go through Alembic's
    # op.add_column on SQLite: Alembic treats any ADD COLUMN carrying a
    # constraint as an unsupported "ALTER of constraints" and raises,
    # directing to batch mode — a restriction in Alembic's SQLite dialect,
    # not in SQLite itself, which has always supported an inline REFERENCES
    # clause in ALTER TABLE ADD COLUMN. Issued as raw DDL via op.execute to
    # get the FK without triggering Alembic's batch-mode requirement.
    # ------------------------------------------------------------------
    op.execute(
        "ALTER TABLE pending_roll_requests ADD COLUMN sequence_id VARCHAR(36) "
        "REFERENCES action_resolution_sequences (sequence_id) ON DELETE CASCADE"
    )
    op.add_column(_TABLE, sa.Column("step_id", sa.String(36), nullable=True))
    op.add_column(_TABLE, sa.Column("instruction_id", sa.String(36), nullable=True))
    op.add_column(_TABLE, sa.Column("instruction_revision", sa.Integer, nullable=True))
    op.add_column(
        _TABLE, sa.Column("instruction_schema_version", sa.Integer, nullable=True)
    )
    op.add_column(
        _TABLE, sa.Column("instruction_snapshot_json", sa.Text, nullable=True)
    )

    # ------------------------------------------------------------------
    # Owner Decision 15b-36: hard precondition before any destructive
    # change. No backfill/conversion pass exists — a populated table means
    # the pre-release clean-cutover assumption is false for this database.
    # ------------------------------------------------------------------
    conn = op.get_bind()
    _assert_pending_roll_requests_empty(conn)

    # ------------------------------------------------------------------
    # Drop the eight legacy display/derivation columns outright — no
    # historical-row compatibility is promised (Owner Decision 15b-36).
    # Direct ALTER TABLE DROP COLUMN; none of these participate in this
    # table's index or any foreign key.
    # ------------------------------------------------------------------
    for col_name in _LEGACY_COLUMNS:
        op.drop_column(_TABLE, col_name)

    # ------------------------------------------------------------------
    # rpg_roll_audit — plain ADD COLUMN only; batch mode would drop the
    # append-only triggers from migration 0011 (not reflected on recreate).
    # ------------------------------------------------------------------
    for col in (
        sa.Column("sequence_id", sa.String(36), nullable=True),
        sa.Column("step_id", sa.String(36), nullable=True),
        sa.Column("pending_roll_request_id", sa.String(36), nullable=True),
        sa.Column("instruction_id", sa.String(36), nullable=True),
        sa.Column("instruction_revision", sa.Integer, nullable=True),
        sa.Column("instruction_schema_version", sa.Integer, nullable=True),
        sa.Column("instruction_snapshot_json", sa.Text, nullable=True),
        sa.Column("submission_source", sa.String(24), nullable=True),
        sa.Column("raw_values_complete", sa.Boolean, nullable=True),
    ):
        op.add_column("rpg_roll_audit", col)


def downgrade() -> None:
    for col in (
        "raw_values_complete",
        "submission_source",
        "instruction_snapshot_json",
        "instruction_schema_version",
        "instruction_revision",
        "instruction_id",
        "pending_roll_request_id",
        "step_id",
        "sequence_id",
    ):
        op.drop_column("rpg_roll_audit", col)

    # Re-add the eight legacy columns. Best-effort reconstruction from
    # instruction_snapshot_json covers real post-Phase-2 rows (this
    # migration performs no backfill of its own); rows with no snapshot get
    # the placeholder default.
    op.add_column(
        _TABLE, sa.Column("check_label", sa.Text, nullable=False, server_default="")
    )
    op.add_column(
        _TABLE,
        sa.Column(
            "player_facing_instruction", sa.Text, nullable=False, server_default=""
        ),
    )
    op.add_column(
        _TABLE,
        sa.Column(
            "expected_value_shape", sa.Text, nullable=False, server_default="integer"
        ),
    )
    op.add_column(_TABLE, sa.Column("visible_modifier_note", sa.Text, nullable=True))
    op.add_column(
        _TABLE,
        sa.Column(
            "roll_expression", sa.String(64), nullable=False, server_default="1d20"
        ),
    )
    op.add_column(
        _TABLE, sa.Column("visible_modifier_total", sa.Integer, nullable=True)
    )
    op.add_column(
        _TABLE, sa.Column("visible_modifier_breakdown_json", sa.Text, nullable=True)
    )
    op.add_column(
        _TABLE,
        sa.Column(
            "hidden_modifier_present",
            sa.Boolean,
            nullable=False,
            server_default="0",
        ),
    )

    conn = op.get_bind()
    rows = conn.execute(
        sa.text(
            f"SELECT request_id, instruction_snapshot_json FROM {_TABLE}"
            " WHERE instruction_snapshot_json IS NOT NULL"
        )
    ).fetchall()

    updates: list[dict] = []
    for r in rows:
        snapshot: dict = {}
        try:
            snapshot = json.loads(r.instruction_snapshot_json)
        except (json.JSONDecodeError, TypeError):
            snapshot = {}
        modifier_components = snapshot.get("modifier_components") or []
        visible_total = (
            sum(int(m.get("value", 0)) for m in modifier_components)
            if modifier_components
            else None
        )
        breakdown_json = (
            json.dumps({m["label"]: m["value"] for m in modifier_components})
            if modifier_components
            else None
        )
        updates.append(
            {
                "request_id": r.request_id,
                "check_label": snapshot.get("display_label", ""),
                "player_facing_instruction": snapshot.get("display_expression", ""),
                "roll_expression": snapshot.get("display_expression", "1d20"),
                "visible_modifier_total": visible_total,
                "visible_modifier_breakdown_json": breakdown_json,
            }
        )
    if updates:
        conn.execute(
            sa.text(
                f"UPDATE {_TABLE} SET"
                " check_label = :check_label,"
                " player_facing_instruction = :player_facing_instruction,"
                " roll_expression = :roll_expression,"
                " visible_modifier_total = :visible_modifier_total,"
                " visible_modifier_breakdown_json = :visible_modifier_breakdown_json"
                " WHERE request_id = :request_id"
            ),
            updates,
        )

    op.drop_column(_TABLE, "instruction_snapshot_json")
    op.drop_column(_TABLE, "instruction_schema_version")
    op.drop_column(_TABLE, "instruction_revision")
    op.drop_column(_TABLE, "instruction_id")
    op.drop_column(_TABLE, "step_id")
    op.drop_column(_TABLE, "sequence_id")

    op.execute("DROP INDEX IF EXISTS uq_unresolved_action_resolution_per_story")
    op.drop_index(
        "ix_action_resolution_sequences_node_id",
        table_name="action_resolution_sequences",
    )
    op.drop_index(
        "ix_action_resolution_sequences_story_id",
        table_name="action_resolution_sequences",
    )
    op.drop_table("action_resolution_sequences")
