"""Writing mode integration — CRD Issue 17.

Extends the existing ``writing_session_states`` table with persona provenance,
authoring controls, play status, beat constraints, and minimal version pointers.

Conservative backfill rule: all new columns except ``play_status``,
``specific_goals``, ``critique_intensity``, and ``style_density`` are nullable
so existing rows are never silently promoted to a configured state.

``play_status`` has a server_default of ``setup`` so existing rows stay in the
setup phase.  ``specific_goals`` defaults to empty string, and
``critique_intensity`` / ``style_density`` default to ``balanced``.

The legacy ``version_history_pointers`` column is renamed to ``version_pointers``
and its payload is converted from ``list[str UUID]`` to ``list[dict]`` shaped as
``WritingVersionPointer`` objects (schema_version, pointer_id, kind, label,
description, created_at, source_turn_id=null, source_node_id=null).  A null-safe
empty-list no-op ensures rows with ``[]`` or ``null`` are untouched.

The legacy ``persona`` string column is backfilled into the new ``persona_id``
column before being dropped, so existing configured sessions keep their persona.

Migration is structured in safe phases for SQLite batch mode:

  Phase 1 (batch):   add new columns (including persona_id); do not rename/drop yet.
  Phase 2 (SQL):     copy persona → persona_id; convert version_history_pointers JSON.
  Phase 3 (batch):   rename version_history_pointers → version_pointers; drop persona.

Downgrade mirrors these phases in reverse.

Revision ID: 0013
Revises: 0012
Create Date: 2026-06-29
"""

from __future__ import annotations

import datetime
import json
from typing import Any, Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0013"
down_revision: Union[str, None] = "0012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLE = "writing_session_states"


# ---------------------------------------------------------------------------
# Local pure helpers — no app model imports allowed in migrations
# ---------------------------------------------------------------------------


def _convert_uuid_strings_to_pointers(raw: Any) -> str:
    """Convert a legacy list[UUID-string] payload to list[WritingVersionPointer-dict].

    If ``raw`` is falsy, already a list-of-dicts, or unparseable, returns the
    JSON for an empty list so the column stays valid.  Does not import Pydantic.
    """
    if not raw:
        return "[]"
    try:
        items: Any = json.loads(raw) if isinstance(raw, str) else raw
    except (json.JSONDecodeError, TypeError):
        return "[]"
    if not isinstance(items, list) or not items:
        return "[]"
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    result = []
    for item in items:
        if isinstance(item, str):
            result.append(
                {
                    "schema_version": 1,
                    "pointer_id": item,
                    "kind": "draft_label",
                    "label": f"Legacy version pointer {item}",
                    "source_turn_id": None,
                    "source_node_id": None,
                    "description": (
                        "Migrated from legacy version_history_pointers"
                        " by migration 0013."
                    ),
                    "created_at": now_iso,
                }
            )
        elif isinstance(item, dict):
            # Already in new shape (shouldn't happen on pre-17 rows, but be safe).
            result.append(item)
    return json.dumps(result)


def _convert_pointers_to_uuid_strings(raw: Any) -> str:
    """Convert a list[WritingVersionPointer-dict] back to a legacy list[UUID-string].

    Best-effort downgrade: uses pointer_id where present, otherwise skips.
    """
    if not raw:
        return "[]"
    try:
        items: Any = json.loads(raw) if isinstance(raw, str) else raw
    except (json.JSONDecodeError, TypeError):
        return "[]"
    if not isinstance(items, list) or not items:
        return "[]"
    result = []
    for item in items:
        if isinstance(item, dict) and "pointer_id" in item:
            result.append(str(item["pointer_id"]))
        elif isinstance(item, str):
            result.append(item)
    return json.dumps(result)


# ---------------------------------------------------------------------------
# Upgrade
# ---------------------------------------------------------------------------


def upgrade() -> None:
    # --- Phase 1: add new columns (persona_id included; rename/drop deferred) ---
    with op.batch_alter_table(_TABLE) as batch_op:
        batch_op.add_column(sa.Column("persona_id", sa.String(64), nullable=True))
        batch_op.add_column(
            sa.Column("persona_registry_version", sa.Integer, nullable=True)
        )
        batch_op.add_column(
            sa.Column("persona_profile_version", sa.Integer, nullable=True)
        )
        batch_op.add_column(
            sa.Column("persona_prompt_fingerprint", sa.String(128), nullable=True)
        )
        batch_op.add_column(
            sa.Column(
                "play_status",
                sa.String(16),
                nullable=False,
                server_default="setup",
            )
        )
        batch_op.add_column(
            sa.Column("reading_interests", sa.Text, nullable=True)
        )
        batch_op.add_column(
            sa.Column("writing_interests", sa.Text, nullable=True)
        )
        batch_op.add_column(sa.Column("form", sa.String(32), nullable=True))
        batch_op.add_column(sa.Column("form_other", sa.Text, nullable=True))
        batch_op.add_column(
            sa.Column(
                "specific_goals",
                sa.Text,
                nullable=False,
                server_default="",
            )
        )
        batch_op.add_column(
            sa.Column(
                "critique_intensity",
                sa.String(16),
                nullable=False,
                server_default="balanced",
            )
        )
        batch_op.add_column(sa.Column("tense", sa.Text, nullable=True))
        batch_op.add_column(sa.Column("pov", sa.Text, nullable=True))
        batch_op.add_column(
            sa.Column(
                "style_density",
                sa.String(16),
                nullable=False,
                server_default="balanced",
            )
        )
        batch_op.add_column(
            sa.Column("dialogue_narration_ratio", sa.Integer, nullable=True)
        )
        batch_op.add_column(
            sa.Column("genre_conventions", sa.Text, nullable=True)
        )
        batch_op.add_column(
            sa.Column("acceptable_content", sa.Text, nullable=True)
        )

    # --- Phase 2: data transforms using the column names that exist NOW ---
    conn = op.get_bind()

    # 2a. Backfill persona_id from legacy persona column where not already set.
    conn.execute(
        sa.text(
            "UPDATE writing_session_states"
            " SET persona_id = persona"
            " WHERE persona IS NOT NULL AND persona_id IS NULL"
        )
    )

    # 2b. Convert legacy version_history_pointers (list[UUID-str]) →
    #     list[WritingVersionPointer-dict].  Read, convert, write back.
    rows = conn.execute(
        sa.text(
            "SELECT session_id, version_history_pointers"
            " FROM writing_session_states"
        )
    ).fetchall()
    for row in rows:
        session_id = row[0]
        raw_vhp = row[1]
        new_vp = _convert_uuid_strings_to_pointers(raw_vhp)
        conn.execute(
            sa.text(
                "UPDATE writing_session_states"
                " SET version_history_pointers = :vhp"
                " WHERE session_id = :sid"
            ),
            {"vhp": new_vp, "sid": session_id},
        )

    # --- Phase 3: rename version_history_pointers → version_pointers; drop persona ---
    with op.batch_alter_table(_TABLE) as batch_op:
        batch_op.alter_column(
            "version_history_pointers",
            new_column_name="version_pointers",
            existing_type=sa.JSON,
            existing_nullable=False,
        )
        batch_op.drop_column("persona")


# ---------------------------------------------------------------------------
# Downgrade
# ---------------------------------------------------------------------------


def downgrade() -> None:
    # --- Phase 1: add back legacy persona column ---
    with op.batch_alter_table(_TABLE) as batch_op:
        batch_op.add_column(
            sa.Column("persona", sa.String(32), nullable=True)
        )

    # --- Phase 2: data transforms ---
    conn = op.get_bind()

    # 2a. Restore persona from persona_id (best-effort; NULL if slug too long).
    conn.execute(
        sa.text(
            "UPDATE writing_session_states"
            " SET persona = CASE"
            "   WHEN persona_id IS NOT NULL AND length(persona_id) <= 32"
            "   THEN persona_id"
            "   ELSE NULL"
            " END"
        )
    )

    # 2b. Convert version_pointers back to legacy list[UUID-str] format.
    rows = conn.execute(
        sa.text(
            "SELECT session_id, version_pointers FROM writing_session_states"
        )
    ).fetchall()
    for row in rows:
        session_id = row[0]
        raw_vp = row[1]
        old_vhp = _convert_pointers_to_uuid_strings(raw_vp)
        conn.execute(
            sa.text(
                "UPDATE writing_session_states"
                " SET version_pointers = :vp"
                " WHERE session_id = :sid"
            ),
            {"vp": old_vhp, "sid": session_id},
        )

    # --- Phase 3: rename version_pointers → version_history_pointers; drop Issue 17 cols ---
    with op.batch_alter_table(_TABLE) as batch_op:
        batch_op.alter_column(
            "version_pointers",
            new_column_name="version_history_pointers",
            existing_type=sa.JSON,
            existing_nullable=False,
        )
        for col in (
            "acceptable_content",
            "genre_conventions",
            "dialogue_narration_ratio",
            "style_density",
            "pov",
            "tense",
            "critique_intensity",
            "specific_goals",
            "form_other",
            "form",
            "writing_interests",
            "reading_interests",
            "play_status",
            "persona_prompt_fingerprint",
            "persona_profile_version",
            "persona_registry_version",
            "persona_id",
        ):
            batch_op.drop_column(col)
