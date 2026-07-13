"""Structured RPG roll lifecycle: action-resolution sequences — CRD Issue 15b.

Creates ``action_resolution_sequences`` (persisted unit spanning one declared
action or mechanically linked action group; at most one unresolved sequence
per story via a partial unique index, mirroring the existing
``uq_pending_roll_requests_story_active`` pattern).

Revises ``pending_roll_requests`` per ADR-015b's Column Disposition table:
retires ``roll_expression``, ``expected_value_shape``, ``visible_modifier_total``,
``visible_modifier_breakdown_json``, ``check_label``, ``player_facing_instruction``,
``visible_modifier_note``, ``hidden_modifier_present`` after backfilling every
unconsumed (``status='pending'``) row into a deterministic single-step ``ACTIVE``
sequence with an equivalent ``RollInstructionSnapshot``. Historical consumed
rows keep nullable sequence/instruction linkage (spec migration items 6-7) —
only pending rows are wrapped.

``pending_roll_requests`` requires an explicit manual table-recreate (create
new table, copy data, drop old, rename) rather than ``batch_alter_table``:
this table carries a partial-unique-index ``WHERE`` predicate and four FKs
with three distinct ``ondelete`` actions (CASCADE/RESTRICT/CASCADE/SET NULL),
both of which Alembic's SQLite batch-mode reflection has historically
mishandled on recreate. Declaring the full target schema explicitly removes
any dependency on what reflection does or doesn't preserve.

``rpg_roll_audit`` gets its new nullable columns via plain ``op.add_column``
(NOT batch mode) because this table has the append-only UPDATE/DELETE
triggers from migration 0011 — SQLite batch mode is copy-and-swap and does
not reflect triggers onto the new table, which would silently drop the
append-only guard. Plain ``ADD COLUMN`` is sufficient here since every new
column is nullable with no default, which SQLite's native ``ALTER TABLE ADD
COLUMN`` supports without a table recreate.

Legacy pending-row conversion: only the three literal expressions the
shipped adapter (``pipeline/rpg/adapter.py``) ever produced —
``1d20``, ``2d20kh1``, ``2d20kl1`` — are recognized. Any pending row whose
``roll_expression`` does not match one of these is corruption or an
out-of-band write; the whole migration collects every such offender and
raises once (not on the first bad row, not a per-row quarantine — a
quarantine state would either lose data or have to resurrect the retired
legacy columns it's meant to replace) rather than coercing to a default roll.
Purpose is inferred deterministically from ``check_label`` via the same
skill/save lookup the adapter uses (skill match -> SKILL_CHECK, save match ->
SAVING_THROW, else -> ABILITY_CHECK fallback); the shipped adapter's
``_ModifierBreakdown`` always sets ``has_hidden=False``, so no pending row
can carry a hidden modifier component that would need reconstruction.

Revision ID: 0017
Revises: 0016
Create Date: 2026-07-13
"""

from __future__ import annotations

import json
import re
import uuid
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0017"
down_revision: str | None = "0016"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLE = "pending_roll_requests"
_SEQUENCE_NS = uuid.UUID("6f2b8e4a-0d1a-4b3e-9c1f-15b000000001")
_STEP_NS = uuid.UUID("6f2b8e4a-0d1a-4b3e-9c1f-15b000000002")
_INSTRUCTION_NS = uuid.UUID("6f2b8e4a-0d1a-4b3e-9c1f-15b000000003")

# Mirrors pipeline/rpg/adapter.py's _SKILL_ABILITY / _SAVE_ABILITY keys.
# Migrations must not import application code, so this is a narrow,
# purpose-inference-only local copy — not a second source of adjudication truth.
_SKILL_KEYS = frozenset(
    {
        "acrobatics",
        "animal_handling",
        "arcana",
        "athletics",
        "deception",
        "history",
        "insight",
        "intimidation",
        "investigation",
        "medicine",
        "nature",
        "perception",
        "performance",
        "persuasion",
        "religion",
        "sleight_of_hand",
        "stealth",
        "survival",
    }
)
_SAVE_KEYS = frozenset(
    {
        "strength_save",
        "dexterity_save",
        "constitution_save",
        "intelligence_save",
        "wisdom_save",
        "charisma_save",
    }
)

_KNOWN_EXPRESSIONS = {
    "1d20": {"count": 1, "sides": 20, "selection_rule": "sum_all", "keep_count": None},
    "2d20kh1": {
        "count": 2,
        "sides": 20,
        "selection_rule": "keep_highest",
        "keep_count": 1,
    },
    "2d20kl1": {
        "count": 2,
        "sides": 20,
        "selection_rule": "keep_lowest",
        "keep_count": 1,
    },
}


def _normalize_key(value: str) -> str:
    return re.sub(r"[\s\-]+", "_", value.strip()).lower()


def _infer_purpose(check_label: str) -> str:
    key = _normalize_key(check_label)
    if key in _SKILL_KEYS:
        return "skill_check"
    if key in _SAVE_KEYS:
        return "saving_throw"
    return "ability_check"


def _build_instruction_snapshot_json(
    *,
    instruction_id: str,
    sequence_id: str,
    step_id: str,
    roll_expression: str,
    check_label: str,
    visible_modifier_total: int | None,
    visible_modifier_breakdown_json: str | None,
) -> str:
    term_shape = _KNOWN_EXPRESSIONS[roll_expression]
    term_id = str(uuid.uuid5(_INSTRUCTION_NS, f"term:{instruction_id}"))
    terms = [
        {
            "schema_version": 1,
            "term_id": term_id,
            "count": term_shape["count"],
            "sides": term_shape["sides"],
            "selection_rule": term_shape["selection_rule"],
            "keep_count": term_shape["keep_count"],
            "contribution": "add",
            "label": None,
        }
    ]

    modifier_components: list[dict] = []
    breakdown: dict = {}
    if visible_modifier_breakdown_json:
        try:
            breakdown = json.loads(visible_modifier_breakdown_json)
        except (json.JSONDecodeError, TypeError):
            breakdown = {}
    if breakdown:
        for label, value in breakdown.items():
            modifier_components.append(
                {
                    "schema_version": 1,
                    "modifier_id": str(
                        uuid.uuid5(_INSTRUCTION_NS, f"mod:{instruction_id}:{label}")
                    ),
                    "label": label,
                    "value": value,
                    "visibility": "player_visible",
                    "source_kind": "legacy_migration",
                    "source_reference": None,
                }
            )
    elif visible_modifier_total:
        modifier_components.append(
            {
                "schema_version": 1,
                "modifier_id": str(
                    uuid.uuid5(_INSTRUCTION_NS, f"mod:{instruction_id}:total")
                ),
                "label": "legacy_modifier",
                "value": visible_modifier_total,
                "visibility": "player_visible",
                "source_kind": "legacy_migration",
                "source_reference": None,
            }
        )

    snapshot = {
        "schema_version": 1,
        "instruction_id": instruction_id,
        "instruction_revision": 1,
        "purpose": _infer_purpose(check_label),
        "terms": terms,
        "modifier_components": modifier_components,
        "display_expression": roll_expression,
        "display_label": check_label,
        "source_rule_refs": [],
        "adjustment_options": [],
        "sequence_id": sequence_id,
        "step_id": step_id,
    }
    return json.dumps(snapshot)


def upgrade() -> None:
    # ------------------------------------------------------------------
    # action_resolution_sequences — must exist before pending_roll_requests
    # gains its FK to it.
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
    # Read every legacy row up front so validation (Phase 1) always
    # completes, and any bad row aborts, before the destructive table
    # swap (Phase 2) touches anything.
    # ------------------------------------------------------------------
    conn = op.get_bind()
    legacy_rows = conn.execute(
        sa.text(
            "SELECT request_id, story_id, session_id, character_id,"
            " originating_turn_id, consumed_turn_id, check_label,"
            " player_facing_instruction, expected_value_shape,"
            " visible_modifier_note, visibility, source_proposal_ref, status,"
            " created_at, schema_version, roll_expression,"
            " visible_modifier_total, visible_modifier_breakdown_json,"
            " hidden_modifier_present, adapter_context_hash, additional_data"
            " FROM pending_roll_requests"
        )
    ).fetchall()

    pending_rows = [r for r in legacy_rows if r.status == "pending"]
    offenders = [
        (r.request_id, r.roll_expression)
        for r in pending_rows
        if r.roll_expression not in _KNOWN_EXPRESSIONS
    ]
    if offenders:
        raise RuntimeError(
            "Migration 0017: cannot convert unrecognized pending roll "
            "expression(s) — these are never coerced to a default roll: "
            + ", ".join(f"{rid!r} -> {expr!r}" for rid, expr in offenders)
        )

    now_iso = conn.execute(sa.text("SELECT CURRENT_TIMESTAMP")).scalar()

    sequence_inserts: list[dict] = []
    pending_new_rows: list[dict] = []
    for r in legacy_rows:
        base = {
            "request_id": r.request_id,
            "story_id": r.story_id,
            "session_id": r.session_id,
            "character_id": r.character_id,
            "originating_turn_id": r.originating_turn_id,
            "consumed_turn_id": r.consumed_turn_id,
            "visibility": r.visibility,
            "source_proposal_ref": r.source_proposal_ref,
            "status": r.status,
            "created_at": r.created_at,
            "schema_version": r.schema_version,
            "adapter_context_hash": r.adapter_context_hash,
            "additional_data": r.additional_data,
            "sequence_id": None,
            "step_id": None,
            "instruction_id": None,
            "instruction_revision": None,
            "instruction_schema_version": None,
            "instruction_snapshot_json": None,
        }
        if r.status == "pending":
            sequence_id = str(uuid.uuid5(_SEQUENCE_NS, r.request_id))
            step_id = str(uuid.uuid5(_STEP_NS, r.request_id))
            instruction_id = str(uuid.uuid5(_INSTRUCTION_NS, r.request_id))
            snapshot_json = _build_instruction_snapshot_json(
                instruction_id=instruction_id,
                sequence_id=sequence_id,
                step_id=step_id,
                roll_expression=r.roll_expression,
                check_label=r.check_label,
                visible_modifier_total=r.visible_modifier_total,
                visible_modifier_breakdown_json=r.visible_modifier_breakdown_json,
            )
            base.update(
                sequence_id=sequence_id,
                step_id=step_id,
                instruction_id=instruction_id,
                instruction_revision=1,
                instruction_schema_version=1,
                instruction_snapshot_json=snapshot_json,
            )
            sequence_inserts.append(
                {
                    "sequence_id": sequence_id,
                    "story_id": r.story_id,
                    "node_id": None,  # legacy rows carry no node_id; see note below
                    "character_id": r.character_id,
                    "originating_turn_id": r.originating_turn_id,
                    "status": "active",
                    "current_interaction_kind": "roll",
                    "current_pending_roll_request_id": r.request_id,
                    "current_decision_request_id": None,
                    "current_decision_snapshot_json": None,
                    "resolved_steps_json": "[]",
                    "projected_state_json": "{}",
                    "provisional_effects_json": "[]",
                    "created_at": r.created_at,
                    "updated_at": now_iso,
                    "schema_version": 1,
                }
            )
        pending_new_rows.append(base)

    # ``node_id`` is required (NOT NULL, FK) on action_resolution_sequences but
    # was never carried by the legacy pending_roll_requests row — the pre-15b
    # schema had no node linkage for a player-roll announce. Resolve it from
    # the originating Turn's node_id, which does exist, rather than leaving a
    # NOT NULL column unset.
    for seq in sequence_inserts:
        node_row = conn.execute(
            sa.text("SELECT node_id FROM turns WHERE turn_id = :tid"),
            {"tid": seq["originating_turn_id"]},
        ).fetchone()
        if node_row is None or node_row.node_id is None:
            raise RuntimeError(
                "Migration 0017: cannot resolve node_id for pending roll "
                f"{seq['current_pending_roll_request_id']!r} — originating "
                f"turn {seq['originating_turn_id']!r} has no node_id"
            )
        seq["node_id"] = node_row.node_id

    # ------------------------------------------------------------------
    # Explicit table swap (see module docstring for why not batch mode).
    # op.create_table (not a bare sa.Table(...).create(bind=conn)) is
    # required here: SQLAlchemy's DDL compiler resolves bare-string
    # sa.ForeignKey("stories.story_id", ...) targets by looking them up in
    # the SAME MetaData as the owning table, which a freshly constructed
    # sa.Table(name, sa.MetaData(), ...) never has — it would raise
    # NoReferencedTableError. Alembic's op.create_table does not require
    # that resolution.
    # ------------------------------------------------------------------
    op.rename_table(_TABLE, "_pending_roll_requests_legacy")
    op.create_table(
        _TABLE,
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
            sa.ForeignKey("rpg_character_sheet_bases.sheet_id", ondelete="RESTRICT"),
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
        sa.Column("visibility", sa.String(16), nullable=False),
        sa.Column("source_proposal_ref", sa.Text, nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.String(64), nullable=False),
        sa.Column("schema_version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("adapter_context_hash", sa.String(64), nullable=True),
        sa.Column(
            "sequence_id",
            sa.String(36),
            sa.ForeignKey(
                "action_resolution_sequences.sequence_id", ondelete="CASCADE"
            ),
            nullable=True,
        ),
        sa.Column("step_id", sa.String(36), nullable=True),
        sa.Column("instruction_id", sa.String(36), nullable=True),
        sa.Column("instruction_revision", sa.Integer, nullable=True),
        sa.Column("instruction_schema_version", sa.Integer, nullable=True),
        sa.Column("instruction_snapshot_json", sa.Text, nullable=True),
        sa.Column("additional_data", sa.JSON, nullable=True),
    )

    if sequence_inserts:
        conn.execute(
            sa.text(
                "INSERT INTO action_resolution_sequences ("
                " sequence_id, story_id, node_id, character_id,"
                " originating_turn_id, status, current_interaction_kind,"
                " current_pending_roll_request_id, current_decision_request_id,"
                " current_decision_snapshot_json, resolved_steps_json,"
                " projected_state_json, provisional_effects_json,"
                " created_at, updated_at, schema_version"
                ") VALUES ("
                " :sequence_id, :story_id, :node_id, :character_id,"
                " :originating_turn_id, :status, :current_interaction_kind,"
                " :current_pending_roll_request_id, :current_decision_request_id,"
                " :current_decision_snapshot_json, :resolved_steps_json,"
                " :projected_state_json, :provisional_effects_json,"
                " :created_at, :updated_at, :schema_version"
                ")"
            ),
            sequence_inserts,
        )
    if pending_new_rows:
        conn.execute(
            sa.text(
                f"INSERT INTO {_TABLE} ("
                " request_id, story_id, session_id, character_id,"
                " originating_turn_id, consumed_turn_id, visibility,"
                " source_proposal_ref, status, created_at, schema_version,"
                " adapter_context_hash, additional_data, sequence_id,"
                " step_id, instruction_id, instruction_revision,"
                " instruction_schema_version, instruction_snapshot_json"
                ") VALUES ("
                " :request_id, :story_id, :session_id, :character_id,"
                " :originating_turn_id, :consumed_turn_id, :visibility,"
                " :source_proposal_ref, :status, :created_at, :schema_version,"
                " :adapter_context_hash, :additional_data, :sequence_id,"
                " :step_id, :instruction_id, :instruction_revision,"
                " :instruction_schema_version, :instruction_snapshot_json"
                ")"
            ),
            pending_new_rows,
        )

    op.drop_table("_pending_roll_requests_legacy")

    op.create_index(
        "ix_pending_roll_requests_story_id",
        _TABLE,
        ["story_id"],
    )
    op.create_index(
        "ix_pending_roll_requests_status",
        _TABLE,
        ["story_id", "status"],
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_pending_roll_requests_story_active "
        "ON pending_roll_requests (story_id) WHERE status = 'pending'"
    )

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

    op.execute("DROP INDEX IF EXISTS uq_pending_roll_requests_story_active")
    op.drop_index("ix_pending_roll_requests_status", table_name=_TABLE)
    op.drop_index("ix_pending_roll_requests_story_id", table_name=_TABLE)

    conn = op.get_bind()
    rows = conn.execute(
        sa.text(
            "SELECT request_id, story_id, session_id, character_id,"
            " originating_turn_id, consumed_turn_id, visibility,"
            " source_proposal_ref, status, created_at, schema_version,"
            " adapter_context_hash, instruction_snapshot_json, additional_data"
            " FROM pending_roll_requests"
        )
    ).fetchall()

    legacy_rows: list[dict] = []
    for r in rows:
        snapshot: dict = {}
        if r.instruction_snapshot_json:
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
        legacy_rows.append(
            {
                "request_id": r.request_id,
                "story_id": r.story_id,
                "session_id": r.session_id,
                "character_id": r.character_id,
                "originating_turn_id": r.originating_turn_id,
                "consumed_turn_id": r.consumed_turn_id,
                "check_label": snapshot.get("display_label", ""),
                "player_facing_instruction": snapshot.get("display_expression", ""),
                "expected_value_shape": "integer",
                "visible_modifier_note": None,
                "visibility": r.visibility,
                "source_proposal_ref": r.source_proposal_ref,
                "status": r.status,
                "created_at": r.created_at,
                "schema_version": 1,
                "roll_expression": snapshot.get("display_expression", "1d20"),
                "visible_modifier_total": visible_total,
                "visible_modifier_breakdown_json": breakdown_json,
                "hidden_modifier_present": False,
                "adapter_context_hash": r.adapter_context_hash,
                "additional_data": r.additional_data,
            }
        )

    op.rename_table(_TABLE, "_pending_roll_requests_new")
    op.create_table(
        _TABLE,
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
            sa.ForeignKey("rpg_character_sheet_bases.sheet_id", ondelete="RESTRICT"),
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
        sa.Column("status", sa.String(16), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.String(64), nullable=False),
        sa.Column("schema_version", sa.Integer, nullable=False, server_default="1"),
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
    if legacy_rows:
        conn.execute(
            sa.text(
                f"INSERT INTO {_TABLE} ("
                " request_id, story_id, session_id, character_id,"
                " originating_turn_id, consumed_turn_id, check_label,"
                " player_facing_instruction, expected_value_shape,"
                " visible_modifier_note, visibility, source_proposal_ref,"
                " status, created_at, schema_version, roll_expression,"
                " visible_modifier_total, visible_modifier_breakdown_json,"
                " hidden_modifier_present, adapter_context_hash, additional_data"
                ") VALUES ("
                " :request_id, :story_id, :session_id, :character_id,"
                " :originating_turn_id, :consumed_turn_id, :check_label,"
                " :player_facing_instruction, :expected_value_shape,"
                " :visible_modifier_note, :visibility, :source_proposal_ref,"
                " :status, :created_at, :schema_version, :roll_expression,"
                " :visible_modifier_total, :visible_modifier_breakdown_json,"
                " :hidden_modifier_present, :adapter_context_hash, :additional_data"
                ")"
            ),
            legacy_rows,
        )
    op.drop_table("_pending_roll_requests_new")

    op.create_index(
        "ix_pending_roll_requests_story_id",
        _TABLE,
        ["story_id"],
    )
    op.create_index(
        "ix_pending_roll_requests_status",
        _TABLE,
        ["story_id", "status"],
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_pending_roll_requests_story_active "
        "ON pending_roll_requests (story_id) WHERE status = 'pending'"
    )

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
