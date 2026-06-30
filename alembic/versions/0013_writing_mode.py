"""Writing mode integration — CRD Issue 17.

Extends the existing ``writing_session_states`` table with persona provenance,
authoring controls, play status, beat constraints (renamed from
version_history_pointers), and minimal version pointers.

Conservative backfill rule: all new columns except ``play_status``,
``specific_goals``, ``critique_intensity``, and ``style_density`` are nullable
so existing rows are never silently promoted to a configured state.

``play_status`` has a server_default of ``setup`` so existing rows stay in the
setup phase.  ``specific_goals`` defaults to empty string, and
``critique_intensity`` / ``style_density`` default to ``balanced``.

The legacy ``version_history_pointers`` column is renamed to ``version_pointers``
to match the new typed ``WritingVersionPointer`` shape (list of dicts rather
than list of UUID strings).  Existing data is preserved in the column.

Revision ID: 0013
Revises: 0012
Create Date: 2026-06-29
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0013"
down_revision: Union[str, None] = "0012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("writing_session_states") as batch_op:
        # Persona provenance
        batch_op.add_column(
            sa.Column("persona_id", sa.String(64), nullable=True)
        )
        batch_op.add_column(
            sa.Column("persona_registry_version", sa.Integer, nullable=True)
        )
        batch_op.add_column(
            sa.Column("persona_profile_version", sa.Integer, nullable=True)
        )
        batch_op.add_column(
            sa.Column("persona_prompt_fingerprint", sa.String(128), nullable=True)
        )

        # Play status — safe server_default keeps existing rows in setup
        batch_op.add_column(
            sa.Column(
                "play_status",
                sa.String(16),
                nullable=False,
                server_default="setup",
            )
        )

        # Authoring controls
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

        # Rename version_history_pointers → version_pointers
        batch_op.alter_column(
            "version_history_pointers",
            new_column_name="version_pointers",
            existing_type=sa.JSON,
            existing_nullable=False,
        )

        # Drop legacy persona string column (replaced by persona_id slug)
        batch_op.drop_column("persona")


def downgrade() -> None:
    with op.batch_alter_table("writing_session_states") as batch_op:
        # Restore legacy persona column
        batch_op.add_column(
            sa.Column("persona", sa.String(32), nullable=True)
        )

        # Rename version_pointers back
        batch_op.alter_column(
            "version_pointers",
            new_column_name="version_history_pointers",
            existing_type=sa.JSON,
            existing_nullable=False,
        )

        # Remove Issue 17 columns
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
