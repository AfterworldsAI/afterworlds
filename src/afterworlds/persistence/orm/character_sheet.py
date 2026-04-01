"""ORM models for the RPG character sheet two-table chain."""

from __future__ import annotations

from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from afterworlds.persistence.orm.base import Base


class RpgCharacterSheetBaseORM(Base):
    """Persisted RpgCharacterSheetBase row.

    FK → stories.  The dnd5e concrete sheet FK → this table (not to stories).
    """

    __tablename__ = "rpg_character_sheet_bases"

    sheet_id: Mapped[str] = mapped_column(sa.String(36), primary_key=True)
    story_id: Mapped[str] = mapped_column(
        sa.String(36),
        sa.ForeignKey("stories.story_id", ondelete="CASCADE"),
        nullable=False,
    )
    rules_package_id: Mapped[str] = mapped_column(sa.Text, nullable=False)
    character_name: Mapped[str] = mapped_column(sa.Text, nullable=False)
    created_at: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    updated_at: Mapped[str] = mapped_column(sa.String(64), nullable=False)

    dnd5e_sheet: Mapped[Dnd5eCharacterSheetORM | None] = relationship(
        "Dnd5eCharacterSheetORM",
        back_populates="base",
        cascade="all, delete-orphan",
        uselist=False,
    )


class Dnd5eCharacterSheetORM(Base):
    """Persisted Dnd5eCharacterSheet row.

    FK → rpg_character_sheet_bases (NOT directly to stories).
    """

    __tablename__ = "dnd5e_character_sheets"

    sheet_id: Mapped[str] = mapped_column(
        sa.String(36),
        sa.ForeignKey("rpg_character_sheet_bases.sheet_id", ondelete="CASCADE"),
        primary_key=True,
    )
    character_class: Mapped[str] = mapped_column(sa.Text, nullable=False)
    background: Mapped[str] = mapped_column(sa.Text, nullable=False)
    level: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    ability_scores: Mapped[dict[str, Any]] = mapped_column(sa.JSON, nullable=False)
    skills: Mapped[dict[str, Any]] = mapped_column(sa.JSON, nullable=False)
    equipment: Mapped[list[Any]] = mapped_column(sa.JSON, nullable=False)
    current_hp: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    maximum_hp: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    spell_slots: Mapped[dict[str, Any]] = mapped_column(sa.JSON, nullable=False)

    base: Mapped[RpgCharacterSheetBaseORM] = relationship(
        "RpgCharacterSheetBaseORM", back_populates="dnd5e_sheet"
    )
