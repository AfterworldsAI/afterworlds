"""ORM models for the mapper's spatial record (issue #211, M1).

One ``spatial_maps`` row per place, keyed by ``(story_id, place_key)``; each
change is an immutable ``spatial_map_revisions`` row holding the updates
applied and the resulting snapshot, pointing at the Turn that committed it.
Revisions are staged in the Turn's delivery-gated transaction, so a Turn that
is not delivered leaves no revision behind.
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from afterworlds.persistence.orm.base import Base


class SpatialMapORM(Base):
    __tablename__ = "spatial_maps"

    map_id: Mapped[str] = mapped_column(sa.String(36), primary_key=True)
    story_id: Mapped[str] = mapped_column(
        sa.String(36),
        sa.ForeignKey("stories.story_id", ondelete="CASCADE"),
        nullable=False,
    )
    place_key: Mapped[str] = mapped_column(sa.String(200), nullable=False)
    label: Mapped[str] = mapped_column(sa.Text, nullable=False)
    status: Mapped[str] = mapped_column(sa.String(16), nullable=False)
    grid_type: Mapped[str] = mapped_column(sa.String(16), nullable=False)
    seed: Mapped[int] = mapped_column(sa.BigInteger, nullable=False)
    generator_version: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    style: Mapped[dict[str, str]] = mapped_column(sa.JSON, nullable=False)
    revision: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    created_turn_id: Mapped[str | None] = mapped_column(
        sa.String(36),
        sa.ForeignKey("turns.turn_id", ondelete="RESTRICT"),
        nullable=True,
    )
    created_at: Mapped[str] = mapped_column(sa.String(64), nullable=False)

    __table_args__ = (
        sa.UniqueConstraint("story_id", "place_key", name="uq_spatial_maps_place"),
        sa.CheckConstraint(
            "status IN ('active', 'archived')", name="ck_spatial_maps_status"
        ),
    )


class SpatialMapRevisionORM(Base):
    __tablename__ = "spatial_map_revisions"

    map_id: Mapped[str] = mapped_column(
        sa.String(36),
        sa.ForeignKey("spatial_maps.map_id", ondelete="CASCADE"),
        primary_key=True,
    )
    revision: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    parent_revision: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    turn_id: Mapped[str | None] = mapped_column(
        sa.String(36),
        sa.ForeignKey("turns.turn_id", ondelete="RESTRICT"),
        nullable=True,
    )
    node_id: Mapped[str | None] = mapped_column(sa.String(36), nullable=True)
    sequence_id: Mapped[str | None] = mapped_column(sa.String(36), nullable=True)
    updates: Mapped[list[object]] = mapped_column(sa.JSON, nullable=False)
    snapshot: Mapped[dict[str, object]] = mapped_column(sa.JSON, nullable=False)
    content_hash: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    created_at: Mapped[str] = mapped_column(sa.String(64), nullable=False)
