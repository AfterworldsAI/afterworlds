"""Retrieval Memory — RPG turn-category markers + marker-era boundary.

CRD Issue 18 / ADR-018 D6.

Adds ``rpg_turn_retrieval_markers``, a sidecar table (not columns on ``turns``)
recording, for each post-boundary RPG narrative-path DELIVERED turn, whether
it is ordinary narrative, a roll-request announce turn, or a setup-
confirmation turn. Only the retrieval-eligibility predicate reads this table.

Also adds ``retrieval_marker_era_boundary``, a singleton row recording the
maximum ``turns.timestamp`` observed at migration-apply time (or NULL if no
turns exist yet). Turns at/before this boundary are legacy — a missing
marker there is expected and is treated as ORDINARY_NARRATIVE. Turns after
this boundary are required to have exactly one marker row; a markerless
post-boundary narrative-path DELIVERED turn is a data-integrity error, never
silently treated as ORDINARY_NARRATIVE.

Revision ID: 0015
Revises: 0014
Create Date: 2026-07-05
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0015"
down_revision: str | None = "0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "rpg_turn_retrieval_markers",
        sa.Column("turn_id", sa.String(36), primary_key=True),
        sa.Column("story_id", sa.String(36), nullable=False),
        sa.Column("category", sa.String(32), nullable=False),
        sa.Column("created_at", sa.String(64), nullable=False),
        sa.ForeignKeyConstraint(
            ["turn_id"], ["turns.turn_id"], ondelete="CASCADE"
        ),
    )
    op.create_index(
        "ix_rpg_turn_retrieval_markers_story_id",
        "rpg_turn_retrieval_markers",
        ["story_id"],
    )

    op.create_table(
        "retrieval_marker_era_boundary",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("boundary_timestamp", sa.String(64), nullable=True),
    )

    # Forward-only boundary snapshot: the maximum timestamp among turns that
    # already exist as of this migration. Never re-run, never updated after
    # this single insert — legacy turns are never retroactively stamped.
    connection = op.get_bind()
    max_timestamp = connection.execute(
        sa.text("SELECT MAX(timestamp) FROM turns")
    ).scalar()
    connection.execute(
        sa.text(
            "INSERT INTO retrieval_marker_era_boundary (id, boundary_timestamp) "
            "VALUES (1, :boundary_timestamp)"
        ),
        {"boundary_timestamp": max_timestamp},
    )


def downgrade() -> None:
    op.drop_table("retrieval_marker_era_boundary")
    op.drop_index(
        "ix_rpg_turn_retrieval_markers_story_id",
        table_name="rpg_turn_retrieval_markers",
    )
    op.drop_table("rpg_turn_retrieval_markers")
