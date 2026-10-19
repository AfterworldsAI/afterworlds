"""rolling_summaries table — CRD Issue 6.

Creates the ``rolling_summaries`` table with:
  - Coverage metadata columns: compressed_from_turn_id, compressed_through_turn_id
    (both non-nullable FKs to turns.turn_id with RESTRICT on delete).
  - version_number: monotonically increasing integer per story (starts at 1).
  - is_current: boolean marking the single active row per story.
  - UNIQUE constraint on (story_id, compressed_through_turn_id) — DB-layer
    idempotency gate preventing duplicate coverage.
  - Partial unique index on story_id WHERE is_current = 1 — SQLite-compatible
    mechanism enforcing at most one current row per story.

The partial index is created via op.execute() because Alembic's create_index()
does not natively support a SQLite partial-index WHERE clause.

Revision ID: 0006
Revises: 0005
Create Date: 2026-04-17
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # rolling_summaries — compressed narrative history
    # ------------------------------------------------------------------
    op.create_table(
        "rolling_summaries",
        sa.Column("summary_id", sa.String(36), primary_key=True),
        sa.Column(
            "story_id",
            sa.String(36),
            sa.ForeignKey("stories.story_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column(
            "compressed_from_turn_id",
            sa.String(36),
            sa.ForeignKey("turns.turn_id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "compressed_through_turn_id",
            sa.String(36),
            sa.ForeignKey("turns.turn_id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("version_number", sa.Integer, nullable=False),
        sa.Column("is_current", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("created_at", sa.String(64), nullable=False),
        sa.UniqueConstraint(
            "story_id",
            "compressed_through_turn_id",
            name="uq_rs_story_through_turn",
        ),
    )

    # Partial unique index: at most one is_current = 1 row per story.
    # SQLite supports partial indexes natively.  Alembic's create_index()
    # does not accept a WHERE clause for SQLite, so op.execute() is used.
    op.execute(
        "CREATE UNIQUE INDEX uq_rs_current_per_story "
        "ON rolling_summaries (story_id) "
        "WHERE is_current = 1"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_rs_current_per_story")
    op.drop_table("rolling_summaries")
