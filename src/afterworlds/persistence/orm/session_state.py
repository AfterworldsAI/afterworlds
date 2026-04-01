"""ORM models for mode-specific session states."""

from __future__ import annotations

from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from afterworlds.persistence.orm.base import Base


class RpgSessionStateORM(Base):
    """Persisted RpgSessionState row — one active row per story."""

    __tablename__ = "rpg_session_states"
    __table_args__ = (
        sa.UniqueConstraint("story_id", name="uq_rpg_session_states_story_id"),
    )

    session_id: Mapped[str] = mapped_column(sa.String(36), primary_key=True)
    story_id: Mapped[str] = mapped_column(
        sa.String(36),
        sa.ForeignKey("stories.story_id", ondelete="CASCADE"),
        nullable=False,
    )
    character_sheet_id: Mapped[str] = mapped_column(sa.String(36), nullable=False)
    dice_handling: Mapped[str] = mapped_column(sa.String(32), nullable=False)
    active_quests: Mapped[list[Any]] = mapped_column(sa.JSON, nullable=False)
    combat_context: Mapped[dict[str, Any]] = mapped_column(sa.JSON, nullable=False)


class BranchingSessionStateORM(Base):
    """Persisted BranchingSessionState row — one active row per story."""

    __tablename__ = "branching_session_states"
    __table_args__ = (
        sa.UniqueConstraint("story_id", name="uq_branching_session_states_story_id"),
    )

    session_id: Mapped[str] = mapped_column(sa.String(36), primary_key=True)
    story_id: Mapped[str] = mapped_column(
        sa.String(36),
        sa.ForeignKey("stories.story_id", ondelete="CASCADE"),
        nullable=False,
    )
    pacing_stage: Mapped[str] = mapped_column(sa.String(32), nullable=False)
    branch_tree: Mapped[dict[str, Any]] = mapped_column(sa.JSON, nullable=False)
    plot_thread_tracker: Mapped[list[Any]] = mapped_column(sa.JSON, nullable=False)
    current_node_id: Mapped[str | None] = mapped_column(sa.String(36), nullable=True)


class WritingSessionStateORM(Base):
    """Persisted WritingSessionState row — one active row per story."""

    __tablename__ = "writing_session_states"
    __table_args__ = (
        sa.UniqueConstraint("story_id", name="uq_writing_session_states_story_id"),
    )

    session_id: Mapped[str] = mapped_column(sa.String(36), primary_key=True)
    story_id: Mapped[str] = mapped_column(
        sa.String(36),
        sa.ForeignKey("stories.story_id", ondelete="CASCADE"),
        nullable=False,
    )
    beat_constraints: Mapped[list[Any]] = mapped_column(sa.JSON, nullable=False)
    version_history_pointers: Mapped[list[Any]] = mapped_column(sa.JSON, nullable=False)
    persona: Mapped[str | None] = mapped_column(sa.String(32), nullable=True)
