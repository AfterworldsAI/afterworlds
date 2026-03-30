"""RPG character sheet models.

The character sheet is a first-class persistent object — not a blob, not a
freeform field on session state, not a dict.

Architecture invariants enforced here:
- The character sheet is the source of truth for persistent mutable character
  resources it owns (HP, spell slots).  RPG session state must not create a
  competing source of truth for these values.
- ``current_hp`` cannot exceed ``maximum_hp``.
- Spell slot ``used`` cannot exceed ``total``.
- Ability scores are validated within the D&D 5e range (1–30).

``Dnd5eCharacterSheet`` is the v1 concrete implementation targeting D&D 5e.
It uses a base-plus-concrete model structure:
- ``RpgCharacterSheetBase`` — system-agnostic identity and binding fields
- ``Dnd5eCharacterSheet`` — typed D&D 5e fields

This does NOT imply the base class is a system-agnostic universal contract.
Broader cross-system abstractions are deferred to Issue 5a/5b.
"""

from datetime import datetime
from typing import Self
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, model_validator

# D&D 5e ability score range:
# 1 is the minimum meaningful value; 30 is the absolute maximum achievable
# through class features, racial traits, and magical effects.  The normal
# adventurer cap is 20, but effects like Epic Boons or Wish can exceed it.
_ABILITY_SCORE_MIN = 1
_ABILITY_SCORE_MAX = 30


class AbilityScores(BaseModel):
    """The six D&D 5e ability scores.

    Valid range: 1–30.  The practical adventurer cap is 20; values above 20
    are possible via magical effects and are therefore included in the schema.
    """

    strength: int
    dexterity: int
    constitution: int
    intelligence: int
    wisdom: int
    charisma: int

    @model_validator(mode="after")
    def scores_in_valid_range(self) -> Self:
        for name, value in self.model_dump().items():
            if not (_ABILITY_SCORE_MIN <= value <= _ABILITY_SCORE_MAX):
                raise ValueError(
                    f"{name} must be between {_ABILITY_SCORE_MIN} and "
                    f"{_ABILITY_SCORE_MAX}, got {value}"
                )
        return self


class SpellSlotLevel(BaseModel):
    """Spell-slot tracking for one spell level.

    The character sheet is the source of truth for spell slot state.
    RPG session state does not duplicate these values.
    """

    total: int = Field(ge=0)
    used: int = Field(ge=0)

    @model_validator(mode="after")
    def used_cannot_exceed_total(self) -> Self:
        if self.used > self.total:
            raise ValueError(f"used ({self.used}) cannot exceed total ({self.total})")
        return self


class RpgCharacterSheetBase(BaseModel):
    """Base persistent RPG character sheet — identity and ruleset binding.

    Contains fields common to all RPG systems.  Concrete implementations
    (e.g., ``Dnd5eCharacterSheet``) add system-specific typed fields.
    """

    sheet_id: UUID = Field(default_factory=uuid4)
    story_id: UUID
    rules_package_id: str
    character_name: str
    created_at: datetime
    updated_at: datetime


class Dnd5eCharacterSheet(RpgCharacterSheetBase):
    """Concrete D&D 5e character sheet.

    All fields are typed and explicit — this is not a blob or freeform dict.
    The character sheet is the source of truth for: current_hp, maximum_hp,
    spell_slots.  RPG session state must not store competing copies of these.
    """

    character_class: str
    background: str
    level: int = Field(default=1, ge=1, le=20)
    ability_scores: AbilityScores
    skills: dict[str, int] = Field(default_factory=dict)
    equipment: list[str] = Field(default_factory=list)
    current_hp: int
    maximum_hp: int = Field(ge=0)
    spell_slots: dict[int, SpellSlotLevel] = Field(default_factory=dict)

    @model_validator(mode="after")
    def current_hp_within_maximum(self) -> Self:
        if self.current_hp > self.maximum_hp:
            raise ValueError(
                f"current_hp ({self.current_hp}) cannot exceed "
                f"maximum_hp ({self.maximum_hp})"
            )
        return self
