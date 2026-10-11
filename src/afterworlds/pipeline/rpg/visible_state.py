"""RpgVisibleStateService — the player-visible RPG snapshot (CRD Issues 15, 2b).

Built from the CRD Issue 2b typed character state and the item instances the
character holds. Character-visible only: hidden conditions are excluded by
construction. A character whose state does not record classes, hit points
or conditions has no visible snapshot (``None``): the snapshot cannot say
"not recorded", and an unrecorded family is never shown as empty.

Labels are read from the accepted identities themselves (``classes.wizard``
reads "Wizard"); no display name is authored here.
"""

from __future__ import annotations

from afterworlds.models.enums import ConditionVisibility
from afterworlds.models.rpg import (
    RpgVisibleState,
    VisibleCharacterState,
    VisibleItem,
)
from afterworlds.services.dnd5e_state.holdings import ItemInstance
from afterworlds.services.dnd5e_state.store import StoredCharacter


def identity_label(key: str) -> str:
    """``equipment.weapons.war_pick`` -> ``War Pick``."""
    return key.rsplit(".", 1)[-1].replace("_", " ").title()


class RpgVisibleStateService:
    """Builds RpgVisibleState from a stored character and its items."""

    def build(
        self, character: StoredCharacter, items: tuple[ItemInstance, ...]
    ) -> RpgVisibleState | None:
        state = character.state
        if not state.classes or state.hit_points is None or state.conditions is None:
            return None
        classes = " / ".join(
            f"{identity_label(c.class_record_key)} {c.level}" for c in state.classes
        )
        return RpgVisibleState(
            character=VisibleCharacterState(
                character_name=character.character_name,
                character_class=classes,
                level=sum(c.level for c in state.classes),
                current_hp=state.hit_points.current,
                maximum_hp=state.hit_points.maximum,
                active_conditions=tuple(
                    identity_label(c.condition.value)
                    + (f" {c.level}" if c.level is not None else "")
                    for c in state.conditions
                    if c.visibility is ConditionVisibility.VISIBLE
                ),
            ),
            inventory=tuple(
                VisibleItem(
                    name=identity_label(i.component_key or i.record_key),
                    quantity=i.quantity,
                )
                for i in items
            ),
            location=None,
            relationship_meters=(),
            known_objectives=(),
        )


__all__ = ["RpgVisibleStateService", "identity_label"]
