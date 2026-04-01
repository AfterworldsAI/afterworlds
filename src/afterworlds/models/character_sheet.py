"""RPG character sheet models.

The character sheet is a first-class persistent object — not a blob, not a
freeform field on session state, not a dict.

Architectural boundary
----------------------
This module contains two layers that must stay distinct:

* ``RpgCharacterSheetBase`` — structural identity and ruleset-binding fields
  only.  No rule-adjudication semantics.  It is NOT a universal contract for
  all RPG systems; it is a shared structural base for the v1 implementation.
  Broader cross-system abstractions are deferred to Issue 5a/5b.

* ``Dnd5eCharacterSheet`` — the v1 concrete implementation, explicitly scoped
  to D&D 5e.  All typed fields and validators here are D&D 5e-specific.  The
  active Rules Package and future adjudication layer determine rules meaning,
  legality, and consequences — not this model.

Invariants that live here are either:
  (a) structural / data-integrity constraints (e.g. ``used`` cannot exceed
      ``total`` for a spell slot), or
  (b) explicitly D&D 5e-scoped constraints documented as such (e.g. ability
      score range 1–30, level 1–20, ``current_hp`` cannot exceed
      ``maximum_hp``).

No universal HP floor, death-threshold, or cross-system field assumption is
encoded here.  Rules semantics belong to the Rules Package and adjudication
layer.
"""

from datetime import datetime
from typing import Self
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, model_validator

# D&D 5e ability score range.
# The normal adventurer cap is 20, but class features (Epic Boons) and
# magical effects can exceed it.  30 is the absolute maximum in 5e.
# These constants are scoped to D&D 5e and must not be treated as universal
# RPG truths.
_DND5E_ABILITY_SCORE_MIN = 1
_DND5E_ABILITY_SCORE_MAX = 30


class Dnd5eAbilityScores(BaseModel):
    """The six D&D 5e ability scores.

    Valid range: 1–30, per D&D 5e rules.  The practical adventurer cap is 20;
    values above 20 are possible via class features and magical effects.

    This model is explicitly scoped to D&D 5e.  It is not a universal
    ability-score contract for other RPG systems.
    """

    strength: int
    dexterity: int
    constitution: int
    intelligence: int
    wisdom: int
    charisma: int

    @model_validator(mode="after")
    def scores_in_dnd5e_range(self) -> Self:
        """Validate scores within the D&D 5e range (1–30)."""
        for name, value in self.model_dump().items():
            if not (_DND5E_ABILITY_SCORE_MIN <= value <= _DND5E_ABILITY_SCORE_MAX):
                raise ValueError(
                    f"{name} must be between {_DND5E_ABILITY_SCORE_MIN} and "
                    f"{_DND5E_ABILITY_SCORE_MAX}, got {value}"
                )
        return self


class SpellSlotLevel(BaseModel):
    """Spell-slot tracking for one spell level.

    The character sheet is the source of truth for spell slot state.
    RPG session state does not duplicate these values.

    The ``used`` cannot exceed ``total`` constraint is a structural /
    data-integrity invariant, not a rules-adjudication claim.
    """

    total: int = Field(ge=0)
    used: int = Field(ge=0)

    @model_validator(mode="after")
    def used_cannot_exceed_total(self) -> Self:
        if self.used > self.total:
            raise ValueError(f"used ({self.used}) cannot exceed total ({self.total})")
        return self


class RpgCharacterSheetBase(BaseModel):
    """Structural base for the v1 RPG character sheet.

    Contains identity and ruleset-binding fields used by the v1 concrete
    implementation.  This is NOT a universal contract for all RPG systems and
    does not encode any rule-adjudication semantics.  Broader cross-system
    abstractions are deferred to Issue 5a/5b.
    """

    sheet_id: UUID = Field(default_factory=uuid4)
    story_id: UUID
    rules_package_id: str
    character_name: str
    created_at: datetime
    updated_at: datetime


class Dnd5eCharacterSheet(RpgCharacterSheetBase):
    """Concrete D&D 5e character sheet — v1 ruleset-specific implementation.

    All fields are typed and explicit — this is not a blob or freeform dict.
    All validators are scoped to D&D 5e and are not universal RPG truths.

    The character sheet is the source of truth for: ``current_hp``,
    ``maximum_hp``, ``spell_slots``.  RPG session state must not store
    competing copies of these values.

    Rules meaning, legality, and consequences (e.g. what happens when HP
    reaches zero) are the responsibility of the active Rules Package and the
    future adjudication layer, not this model.
    """

    character_class: str
    background: str
    level: int = Field(default=1, ge=1, le=20)
    ability_scores: Dnd5eAbilityScores
    skills: dict[str, int] = Field(default_factory=dict)
    equipment: list[str] = Field(default_factory=list)
    current_hp: int
    maximum_hp: int = Field(ge=0)
    spell_slots: dict[int, SpellSlotLevel] = Field(default_factory=dict)

    @model_validator(mode="after")
    def current_hp_within_maximum(self) -> Self:
        """D&D 5e-scoped: current HP cannot exceed maximum HP.

        This is an explicitly D&D 5e constraint on this concrete model.
        It is not asserted as a universal RPG truth.  Rules consequences
        for HP states (e.g. reaching zero) belong to the adjudication layer.
        """
        if self.current_hp > self.maximum_hp:
            raise ValueError(
                f"current_hp ({self.current_hp}) cannot exceed "
                f"maximum_hp ({self.maximum_hp})"
            )
        return self
