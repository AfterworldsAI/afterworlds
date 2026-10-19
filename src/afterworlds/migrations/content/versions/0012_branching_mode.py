"""Branching mode interaction configuration — CRD Issue 16.

Extends the existing ``branching_session_states`` table with interaction-
configuration and setup-context columns required by the typed output contract
and code-owned affordances introduced in Issue 16.

All new columns except ``play_status`` are nullable so existing rows are never
silently backfilled to a default interaction style.  ``play_status`` has a safe
server-default of ``setup`` (matching the Pydantic model's BranchingPlayStatus
default) so existing rows stay in the setup phase.

Revision ID: 0012
Revises: 0011
Create Date: 2026-06-24
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0012"
down_revision: Union[str, None] = "0011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # Extend branching_session_states with interaction-configuration columns.
    # interaction_style / branching_cadence / length_preference /
    # branch_count_range are nullable — conservative backfill rule: never
    # silently assign freeform_only to rows that predate Issue 16.
    # play_status is NOT NULL with server_default "setup" (safe for all rows).
    # ------------------------------------------------------------------
    op.add_column(
        "branching_session_states",
        sa.Column("interaction_style", sa.String(32), nullable=True),
    )
    op.add_column(
        "branching_session_states",
        sa.Column("branching_cadence", sa.String(32), nullable=True),
    )
    op.add_column(
        "branching_session_states",
        sa.Column("length_preference", sa.String(32), nullable=True),
    )
    op.add_column(
        "branching_session_states",
        sa.Column("branch_count_range", sa.String(8), nullable=True),
    )
    op.add_column(
        "branching_session_states",
        sa.Column(
            "play_status",
            sa.String(16),
            nullable=False,
            server_default="setup",
        ),
    )
    # Setup-context text fields — all nullable, narrative scaffolding only.
    op.add_column(
        "branching_session_states",
        sa.Column("world_summary", sa.Text, nullable=True),
    )
    op.add_column(
        "branching_session_states",
        sa.Column("story_seeds", sa.Text, nullable=True),
    )
    op.add_column(
        "branching_session_states",
        sa.Column("character_concept", sa.Text, nullable=True),
    )
    op.add_column(
        "branching_session_states",
        sa.Column("supporting_cast", sa.Text, nullable=True),
    )
    op.add_column(
        "branching_session_states",
        sa.Column("world_constraints", sa.Text, nullable=True),
    )
    op.add_column(
        "branching_session_states",
        sa.Column("pacing_notes", sa.Text, nullable=True),
    )
    op.add_column(
        "branching_session_states",
        sa.Column("acceptable_content", sa.Text, nullable=True),
    )


def downgrade() -> None:
    op.drop_column("branching_session_states", "acceptable_content")
    op.drop_column("branching_session_states", "pacing_notes")
    op.drop_column("branching_session_states", "world_constraints")
    op.drop_column("branching_session_states", "supporting_cast")
    op.drop_column("branching_session_states", "character_concept")
    op.drop_column("branching_session_states", "story_seeds")
    op.drop_column("branching_session_states", "world_summary")
    op.drop_column("branching_session_states", "play_status")
    op.drop_column("branching_session_states", "branch_count_range")
    op.drop_column("branching_session_states", "length_preference")
    op.drop_column("branching_session_states", "branching_cadence")
    op.drop_column("branching_session_states", "interaction_style")
