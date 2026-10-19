"""Structured RPG roll lifecycle: action-resolution sequences, their event
ledger, the revised pending roll and the audit linkage — CRD Issue 15b.

Owner Decision 15b-36 (pre-release clean schema cutover) governs
``pending_roll_requests``: the eight legacy display/derivation columns are
dropped outright, with no conversion. The migration first asserts the table
is empty and raises before **any** DDL if it is not: a populated table means
the pre-release assumption is false for that database, which must be reset or
migrated separately by a reviewed conversion. This guard also refuses an
unrecognised legacy expression visibly, since it refuses every legacy row.

Every change is a direct ``ALTER TABLE`` or ``CREATE``: SQLite >= 3.35
supports ``ADD COLUMN``/``DROP COLUMN``, and none of the dropped columns is
indexed or in a foreign key. No rebuild, no ``PRAGMA foreign_keys`` toggle and
no row copy, so ``rpg_roll_audit``'s append-only triggers (migration 0011),
which a batch rebuild would not carry over, stay in place.

* ``action_resolution_sequences``: ``session_id`` NOT NULL from creation; one
  unresolved (``active``/``ready_for_narration``) sequence per story by a
  partial unique index (ADR-015b 15b-18).
* ``action_resolution_events``: the append-only ledger (15b-34); UPDATE and
  DELETE raise by trigger, as on ``rpg_roll_audit``; ``(sequence_id,
  event_order)`` unique. Created empty: no earlier intermediate provenance
  exists to backfill.
* ``pending_roll_requests``: the six structured columns.
* ``rpg_roll_audit``: the nine nullable linkage columns of the Final Audit
  Projection and ``contest_resolution_json`` (ADR-015b Group 17).

Downgrade restores the empty pre-0043 schema only. It refuses before any
change while a pending roll, sequence, event or ledger-linked audit row exists
(:func:`require_no_lifecycle_data`): their provenance has no legacy form.

Supersedes #129's unmerged 0017/0019, whose revision ids are taken on main.

Revision ID: 0043
Revises: 0042
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision: str = "0043"
down_revision: str | None = "0042"
branch_labels: str | None = None
depends_on: str | None = None

_PENDING = "pending_roll_requests"
_EVENTS = "action_resolution_events"

#: Dropped by Owner Decision 15b-36; restored (as placeholders) on downgrade.
_LEGACY: tuple[tuple[str, sa.types.TypeEngine[object], str | None], ...] = (
    ("check_label", sa.Text(), "''"),
    ("player_facing_instruction", sa.Text(), "''"),
    ("expected_value_shape", sa.Text(), "'integer'"),
    ("visible_modifier_note", sa.Text(), None),
    ("roll_expression", sa.String(64), "'1d20'"),
    ("visible_modifier_total", sa.Integer(), None),
    ("visible_modifier_breakdown_json", sa.Text(), None),
    ("hidden_modifier_present", sa.Boolean(), "0"),
)
_STRUCTURED: tuple[tuple[str, sa.types.TypeEngine[object] | type], ...] = (
    ("sequence_id", sa.String(36)),
    ("step_id", sa.String(36)),
    ("instruction_id", sa.String(36)),
    ("instruction_revision", sa.Integer),
    ("instruction_schema_version", sa.Integer),
    ("instruction_snapshot_json", sa.Text),
)
_AUDIT: tuple[tuple[str, sa.types.TypeEngine[object] | type], ...] = (
    ("sequence_id", sa.String(36)),
    ("step_id", sa.String(36)),
    ("pending_roll_request_id", sa.String(36)),
    ("instruction_id", sa.String(36)),
    ("instruction_revision", sa.Integer),
    ("instruction_schema_version", sa.Integer),
    ("instruction_snapshot_json", sa.Text),
    ("submission_source", sa.String(24)),
    ("raw_values_complete", sa.Boolean),
    ("contest_resolution_json", sa.Text),
)


def require_empty_pending(connection: sa.engine.Connection) -> None:
    """Owner Decision 15b-36's precondition, checked before any change."""
    count = connection.execute(sa.text(f"SELECT COUNT(*) FROM {_PENDING}")).scalar()
    if count:
        raise RuntimeError(
            f"Migration 0043: {_PENDING} contains {count} row(s). Owner Decision "
            "15b-36 (pre-release clean schema cutover) drops its eight legacy "
            "display/derivation columns with no conversion, and no supported "
            "database is promised to hold such a row. Nothing was changed. Reset "
            "this database, or migrate its rows separately by a reviewed "
            "conversion, before upgrading."
        )


def require_no_lifecycle_data(connection: sa.engine.Connection) -> None:
    """Downgrade's precondition: no data this revision's schema holds.

    A pending roll, sequence, event or audit row linked to the ledger is
    structured provenance (an instruction snapshot, an append-only event) that
    the legacy columns cannot represent; restoring them would fabricate
    legacy authority (``1d20``, a blank label). Downgrade therefore refuses
    before any change while any exists. There is no reverse converter.
    """
    held = {
        _PENDING: f"SELECT COUNT(*) FROM {_PENDING}",
        "action_resolution_sequences": (
            "SELECT COUNT(*) FROM action_resolution_sequences"
        ),
        _EVENTS: f"SELECT COUNT(*) FROM {_EVENTS}",
        "rpg_roll_audit (ledger-linked)": (
            "SELECT COUNT(*) FROM rpg_roll_audit WHERE sequence_id IS NOT NULL"
            " OR instruction_id IS NOT NULL OR contest_resolution_json IS NOT NULL"
        ),
    }
    found = {
        table: count
        for table, sql in held.items()
        if (count := connection.execute(sa.text(sql)).scalar())
    }
    if found:
        raise RuntimeError(
            "Migration 0043 downgrade: action-resolution data exists "
            f"({', '.join(f'{t}: {n}' for t, n in found.items())}). Its structured "
            "snapshots and append-only ledger have no legacy representation, and "
            "nothing is fabricated for them. Nothing was changed."
        )


def upgrade() -> None:
    require_empty_pending(op.get_bind())

    op.create_table(
        "action_resolution_sequences",
        sa.Column("sequence_id", sa.String(36), primary_key=True),
        sa.Column(
            "story_id",
            sa.String(36),
            sa.ForeignKey("stories.story_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("session_id", sa.String(36), nullable=False),
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
        sa.Column(
            "originating_turn_id",
            sa.String(36),
            sa.ForeignKey("turns.turn_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("current_interaction_kind", sa.String(16), nullable=False),
        sa.Column("current_pending_roll_request_id", sa.String(36), nullable=True),
        sa.Column("current_decision_request_id", sa.String(36), nullable=True),
        sa.Column("current_decision_snapshot_json", sa.Text, nullable=True),
        sa.Column("plan_json", sa.Text, nullable=False),
        sa.Column("reads_json", sa.Text, nullable=False),
        sa.Column("records_json", sa.Text, nullable=False),
        sa.Column("unattached_json", sa.Text, nullable=False),
        sa.Column("resolved_steps_json", sa.Text, nullable=False),
        sa.Column("projected_state_json", sa.Text, nullable=False),
        sa.Column("provisional_effects_json", sa.Text, nullable=False),
        sa.Column("revision", sa.Integer, nullable=False),
        sa.Column("created_at", sa.String(64), nullable=False),
        sa.Column("updated_at", sa.String(64), nullable=False),
        sa.Column("schema_version", sa.Integer, nullable=False, server_default="1"),
    )
    op.create_index(
        "ix_action_resolution_sequences_story_id",
        "action_resolution_sequences",
        ["story_id"],
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_unresolved_action_resolution_per_story "
        "ON action_resolution_sequences (story_id) "
        "WHERE status IN ('active', 'ready_for_narration')"
    )

    op.create_table(
        _EVENTS,
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
        _EVENTS,
        ["sequence_id", "event_order"],
        unique=True,
    )
    for action in ("UPDATE", "DELETE"):
        op.execute(
            f"CREATE TRIGGER prevent_{_EVENTS}_{action.lower()} "
            f"BEFORE {action} ON {_EVENTS} BEGIN "
            f"SELECT RAISE(ABORT, '{_EVENTS} is append-only: {action} is forbidden'); "
            "END"
        )

    for name, type_ in _STRUCTURED:
        op.add_column(_PENDING, sa.Column(name, type_, nullable=True))
    for name, _type, _default in _LEGACY:
        op.drop_column(_PENDING, name)

    for name, type_ in _AUDIT:
        op.add_column("rpg_roll_audit", sa.Column(name, type_, nullable=True))


def downgrade() -> None:
    require_no_lifecycle_data(op.get_bind())
    for name, _type in reversed(_AUDIT):
        op.drop_column("rpg_roll_audit", name)
    for name, type_, default in _LEGACY:
        op.add_column(
            _PENDING,
            sa.Column(
                name,
                type_,
                nullable=default is None,
                server_default=sa.text(default) if default is not None else None,
            ),
        )
    for name, _type in reversed(_STRUCTURED):
        op.drop_column(_PENDING, name)
    for action in ("DELETE", "UPDATE"):
        op.execute(f"DROP TRIGGER IF EXISTS prevent_{_EVENTS}_{action.lower()}")
    op.drop_index("uq_action_resolution_events_sequence_order", table_name=_EVENTS)
    op.drop_table(_EVENTS)
    op.execute("DROP INDEX IF EXISTS uq_unresolved_action_resolution_per_story")
    op.drop_index(
        "ix_action_resolution_sequences_story_id",
        table_name="action_resolution_sequences",
    )
    op.drop_table("action_resolution_sequences")
