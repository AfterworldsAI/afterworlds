"""ORM models for WorldState and CharacterState with explicit partition columns."""

from __future__ import annotations

from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from afterworlds.persistence.orm.base import Base


class WorldStateORM(Base):
    """Persisted WorldState row.

    Static and dynamic partition columns are stored on the same table with
    ``static_`` / ``dynamic_`` prefixes.  The partition boundary is enforced
    by the CRUD service's separate update paths.
    """

    __tablename__ = "world_states"
    __table_args__ = (sa.UniqueConstraint("story_id", name="uq_world_states_story_id"),)

    world_state_id: Mapped[str] = mapped_column(sa.String(36), primary_key=True)
    story_id: Mapped[str] = mapped_column(
        sa.String(36),
        sa.ForeignKey("stories.story_id", ondelete="CASCADE"),
        nullable=False,
    )

    # Static partition
    static_setting_name: Mapped[str] = mapped_column(sa.Text, nullable=False)
    static_world_rules: Mapped[list[Any]] = mapped_column(sa.JSON, nullable=False)
    static_geography: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    static_time_period: Mapped[str | None] = mapped_column(sa.Text, nullable=True)

    # Dynamic partition
    dynamic_current_location: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    dynamic_time_of_day: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    dynamic_weather: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    dynamic_faction_standings: Mapped[dict[str, Any]] = mapped_column(
        sa.JSON, nullable=False
    )
    updated_at: Mapped[str] = mapped_column(sa.String(64), nullable=False)


class CharacterStateORM(Base):
    """Persisted CharacterState row.

    Static and dynamic partition columns are stored on the same table with
    ``static_`` / ``dynamic_`` prefixes.
    """

    __tablename__ = "character_states"
    __table_args__ = (
        sa.UniqueConstraint("story_id", name="uq_character_states_story_id"),
    )

    character_state_id: Mapped[str] = mapped_column(sa.String(36), primary_key=True)
    story_id: Mapped[str] = mapped_column(
        sa.String(36),
        sa.ForeignKey("stories.story_id", ondelete="CASCADE"),
        nullable=False,
    )

    # Static partition
    static_character_name: Mapped[str] = mapped_column(sa.Text, nullable=False)

    # Dynamic partition
    dynamic_current_location: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    dynamic_status_effects: Mapped[list[Any]] = mapped_column(sa.JSON, nullable=False)
    dynamic_relationship_meters: Mapped[dict[str, Any]] = mapped_column(
        sa.JSON, nullable=False
    )
    dynamic_inventory: Mapped[list[Any]] = mapped_column(sa.JSON, nullable=False)
    updated_at: Mapped[str] = mapped_column(sa.String(64), nullable=False)
