"""ORM models for Node and Turn."""

from __future__ import annotations

from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from afterworlds.persistence.orm.base import Base


class NodeORM(Base):
    """Persisted Node row — a story beat / state transition."""

    __tablename__ = "nodes"

    node_id: Mapped[str] = mapped_column(sa.String(36), primary_key=True)
    chapter_id: Mapped[str] = mapped_column(
        sa.String(36),
        sa.ForeignKey("chapters.chapter_id", ondelete="CASCADE"),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(sa.Text, nullable=False)
    state_delta: Mapped[dict[str, Any]] = mapped_column(sa.JSON, nullable=False)
    branching_logic: Mapped[list[Any]] = mapped_column(sa.JSON, nullable=False)
    intent_type: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata", sa.JSON, nullable=False
    )
    mode_metadata: Mapped[dict[str, Any] | None] = mapped_column(sa.JSON, nullable=True)

    chapter: Mapped[ChapterORM] = relationship("ChapterORM", back_populates="nodes")
    turns: Mapped[list[TurnORM]] = relationship(
        "TurnORM",
        back_populates="node",
        cascade="save-update, merge",
    )


class TurnORM(Base):
    """Persisted Turn row — one user input / AI response interaction unit."""

    __tablename__ = "turns"

    turn_id: Mapped[str] = mapped_column(sa.String(36), primary_key=True)
    node_id: Mapped[str | None] = mapped_column(
        sa.String(36),
        sa.ForeignKey("nodes.node_id", ondelete="SET NULL"),
        nullable=True,
    )
    user_input: Mapped[str] = mapped_column(sa.Text, nullable=False)
    assistant_output: Mapped[str] = mapped_column(sa.Text, nullable=False)
    timestamp: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    intent_classification: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    intent_classification_result: Mapped[dict[str, Any] | None] = mapped_column(
        sa.JSON, nullable=True
    )
    mode_metadata: Mapped[dict[str, Any] | None] = mapped_column(sa.JSON, nullable=True)

    node: Mapped[NodeORM | None] = relationship("NodeORM", back_populates="turns")


# Resolve forward reference used in story.py
from afterworlds.persistence.orm.story import ChapterORM  # noqa: E402, F401
