"""ORM models for Story → Arc → Chapter hierarchy."""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from afterworlds.persistence.orm.base import Base


class StoryORM(Base):
    """Persisted Story row."""

    __tablename__ = "stories"

    story_id: Mapped[str] = mapped_column(sa.String(36), primary_key=True)
    title: Mapped[str] = mapped_column(sa.Text, nullable=False)
    mode: Mapped[str] = mapped_column(sa.String(32), nullable=False)
    created_at: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    updated_at: Mapped[str] = mapped_column(sa.String(64), nullable=False)

    arcs: Mapped[list[ArcORM]] = relationship(
        "ArcORM",
        back_populates="story",
        cascade="all, delete-orphan",
        order_by="ArcORM.order",
    )


class ArcORM(Base):
    """Persisted Arc row — major narrative division within a Story."""

    __tablename__ = "arcs"

    arc_id: Mapped[str] = mapped_column(sa.String(36), primary_key=True)
    story_id: Mapped[str] = mapped_column(
        sa.String(36),
        sa.ForeignKey("stories.story_id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(sa.Text, nullable=False)
    order: Mapped[int] = mapped_column(sa.Integer, nullable=False)

    story: Mapped[StoryORM] = relationship("StoryORM", back_populates="arcs")
    chapters: Mapped[list[ChapterORM]] = relationship(
        "ChapterORM",
        back_populates="arc",
        cascade="all, delete-orphan",
        order_by="ChapterORM.order",
    )


class ChapterORM(Base):
    """Persisted Chapter row — subdivision within an Arc."""

    __tablename__ = "chapters"

    chapter_id: Mapped[str] = mapped_column(sa.String(36), primary_key=True)
    arc_id: Mapped[str] = mapped_column(
        sa.String(36),
        sa.ForeignKey("arcs.arc_id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(sa.Text, nullable=False)
    order: Mapped[int] = mapped_column(sa.Integer, nullable=False)

    arc: Mapped[ArcORM] = relationship("ArcORM", back_populates="chapters")
    nodes: Mapped[list[NodeORM]] = relationship(
        "NodeORM",
        back_populates="chapter",
        cascade="all, delete-orphan",
    )


# Import here to avoid circular reference at module level
from afterworlds.persistence.orm.node import NodeORM  # noqa: E402, F401
