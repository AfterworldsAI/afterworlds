"""ORM model for the RPG character identity row.

The character's typed mechanical state is ``dnd5e_character_states``
(:mod:`afterworlds.persistence.orm.dnd5e_state`), which references this row.
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from afterworlds.persistence.orm.base import Base


class RpgCharacterSheetBaseORM(Base):
    """Persisted RpgCharacterSheetBase row (FK -> stories)."""

    __tablename__ = "rpg_character_sheet_bases"

    sheet_id: Mapped[str] = mapped_column(sa.String(36), primary_key=True)
    story_id: Mapped[str] = mapped_column(
        sa.String(36),
        sa.ForeignKey("stories.story_id", ondelete="CASCADE"),
        nullable=False,
    )
    character_name: Mapped[str] = mapped_column(sa.Text, nullable=False)
    created_at: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    updated_at: Mapped[str] = mapped_column(sa.String(64), nullable=False)


# The CRD Issue 2b typed state references this table; registering it here keeps
# every metadata that knows the identity row able to create its state.
import afterworlds.persistence.orm.dnd5e_state  # noqa: E402, F401
