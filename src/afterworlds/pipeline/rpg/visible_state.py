"""RpgVisibleStateService — CRD Issue 15 Phase 7.

Builds the player-visible RPG state snapshot from the current character sheet.
Character-visible only: hidden conditions are excluded by construction.

v1 scope: character state and inventory.  Location, relationship meters, and
known objectives are empty; those fields are deferred to a future issue once
the Extractor writes authoritative session state for them.

Note: ``build`` is called from the pre-mutation snapshot assembled by the
resolver before this turn's sheet effects are applied.  Sheet-effect
application is not yet implemented (Issue 15 v1 scope); the visible state
therefore reflects the sheet at the START of the turn.  This is a deliberate
v1 constraint, documented in Architecture Notes.
"""

from __future__ import annotations

from afterworlds.models.character_sheet import Dnd5eCharacterSheet
from afterworlds.models.enums import ConditionVisibility
from afterworlds.models.rpg import (
    RpgVisibleState,
    VisibleCharacterState,
    VisibleItem,
)


class RpgVisibleStateService:
    """Builds RpgVisibleState from a Dnd5eCharacterSheet snapshot."""

    def build(self, sheet: Dnd5eCharacterSheet) -> RpgVisibleState:
        """Return the player-visible snapshot of the given sheet."""
        visible_conditions = tuple(
            c.display_label
            for c in sheet.active_conditions
            if c.visibility is ConditionVisibility.VISIBLE
        )
        return RpgVisibleState(
            character=VisibleCharacterState(
                character_name=sheet.character_name,
                character_class=sheet.character_class,
                level=sheet.level,
                current_hp=sheet.current_hp,
                maximum_hp=sheet.maximum_hp,
                active_conditions=visible_conditions,
            ),
            inventory=tuple(VisibleItem(name=item) for item in sheet.equipment),
            location=None,
            relationship_meters=(),
            known_objectives=(),
        )


__all__ = ["RpgVisibleStateService"]
