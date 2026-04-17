"""ORM model for the rolling_summaries table.

ARCHITECTURE INVARIANT:
  The rolling_summaries table is structurally separate from Story Bible tables
  (prefix ``sb_``).  It carries no FK to any ``sb_*`` table.  It does carry
  FKs to ``stories.story_id`` (the story hierarchy root) and to ``turns.turn_id``
  (coverage anchors).  These are deliberate:

  - ``story_id`` FK: every summary belongs to exactly one story.
  - ``compressed_from_turn_id`` / ``compressed_through_turn_id`` FKs: each
    summary's coverage range is anchored to real persisted Turn rows, making
    coverage provenance readable from the row itself.

Uniqueness constraints:
  - ``(story_id, compressed_through_turn_id)`` — UNIQUE.  Prevents duplicate
    coverage.  This is the DB-layer idempotency gate.
  - One ``is_current = True`` row per story — enforced by a partial unique index
    created in the Alembic migration via op.execute().  Service logic atomically
    clears the previous current marker before setting the new one.
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from afterworlds.persistence.orm.base import Base


class RollingSummaryORM(Base):
    """Persisted rolling summary row."""

    __tablename__ = "rolling_summaries"

    summary_id: Mapped[str] = mapped_column(sa.String(36), primary_key=True)
    story_id: Mapped[str] = mapped_column(
        sa.String(36),
        sa.ForeignKey("stories.story_id", ondelete="CASCADE"),
        nullable=False,
    )
    text: Mapped[str] = mapped_column(sa.Text, nullable=False)
    compressed_from_turn_id: Mapped[str] = mapped_column(
        sa.String(36),
        sa.ForeignKey("turns.turn_id", ondelete="RESTRICT"),
        nullable=False,
    )
    compressed_through_turn_id: Mapped[str] = mapped_column(
        sa.String(36),
        sa.ForeignKey("turns.turn_id", ondelete="RESTRICT"),
        nullable=False,
    )
    version_number: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    is_current: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=False)
    created_at: Mapped[str] = mapped_column(sa.String(64), nullable=False)

    __table_args__ = (
        sa.UniqueConstraint(
            "story_id",
            "compressed_through_turn_id",
            name="uq_rs_story_through_turn",
        ),
    )
