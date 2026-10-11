"""RPG character identity.

``RpgCharacterSheetBase`` is the character's structural identity: the row the
RPG session state and pending rolls reference. It carries no mechanics and no
Rules Package reference. A character's mechanical state, and the exact
four-part binding it is held under, are the CRD Issue 2b typed state
(:mod:`afterworlds.models.dnd5e_state`). The free-text ``rules_package_id``
and the untyped ``Dnd5eCharacterSheet`` (stored skill totals, free-text class,
background and equipment) are retired.

This is a structural base for the v1 implementation, not a universal contract
for all RPG systems (ADR-0003 Decision 3).
"""

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class RpgCharacterSheetBase(BaseModel):
    """Structural identity of one RPG character within a story."""

    sheet_id: UUID = Field(default_factory=uuid4)
    story_id: UUID
    character_name: str
    created_at: datetime
    updated_at: datetime
