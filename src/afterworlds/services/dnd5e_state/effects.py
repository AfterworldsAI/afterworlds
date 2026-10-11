"""Apply code-derived sheet effects to typed character state — CRD Issue 2b.

Pure: returns the new state, writes nothing. The caller commits it by
compare-and-swap against the revision and binding the turn read.

* ``current_hp`` ``delta``/``set``: no floor (ADR-0003 Decision 2); only the
  retained D&D 5e rule ``current <= maximum`` caps it.
* ``spell_slot.<level>`` ``delta``/``set``: adjusts *expended* slots in the one
  pool that has that level; a level held by several pools (Pact Magic beside
  Spellcasting) is ambiguous and refused rather than guessed.
  ``0 <= expended <= total`` is structural.
* ``apply_condition``: a typed :class:`ConditionInstance` (``condition``,
  ``visibility``, optional ``level``, ``source``, ``instance_id``).
* ``clear_condition``: by ``instance_id``, or every instance of ``condition``.

Anything else, or a family the state does not record, raises ``ValueError``.
"""

from __future__ import annotations

import json
from uuid import uuid4

from afterworlds.models.dnd5e_state import (
    ConditionInstance,
    Dnd5eCharacterState,
)
from afterworlds.models.rpg import SheetEffect

__all__ = ["apply_effects"]


def _int(value: object, target: str) -> int:
    if type(value) is not int:
        raise ValueError(f"{target}: value must be an integer, got {value!r}")
    return value


def _hp(
    state: Dnd5eCharacterState, effect: SheetEffect, value: object
) -> Dnd5eCharacterState:
    hp = state.hit_points
    if hp is None:
        raise ValueError("current_hp: the character records no hit points")
    amount = _int(value, effect.target)
    current = hp.current + amount if effect.operation == "delta" else amount
    current = min(hp.maximum, current)
    # Only ``current`` changes; every other recorded field is kept.
    return state.model_copy(
        update={"hit_points": hp.model_copy(update={"current": current})}
    )


def _slot(
    state: Dnd5eCharacterState, effect: SheetEffect, value: object
) -> Dnd5eCharacterState:
    level_str = effect.target.removeprefix("spell_slot.")
    if not level_str.isdigit():
        raise ValueError(f"Unknown sheet-effect target: {effect.target!r}")
    level = int(level_str)
    pools = state.spell_slot_pools
    if pools is None:
        raise ValueError(f"{effect.target}: the character records no spell slots")
    holding = [p for p in pools if any(s.level == level for s in p.levels)]
    if len(holding) != 1:
        raise ValueError(
            f"{effect.target}: {len(holding)} pools hold level {level}; the "
            "effect must name exactly one"
        )
    (pool,) = holding
    amount = _int(value, effect.target)
    levels = []
    for s in pool.levels:
        if s.level == level:
            expended = s.expended + amount if effect.operation == "delta" else amount
            s = s.model_copy(update={"expended": max(0, min(s.total, expended))})
        levels.append(s)
    new_pool = pool.model_copy(update={"levels": tuple(levels)})
    return state.model_copy(
        update={"spell_slot_pools": tuple(new_pool if p is pool else p for p in pools)}
    )


def apply_effects(
    state: Dnd5eCharacterState, effects: tuple[SheetEffect, ...]
) -> Dnd5eCharacterState:
    for effect in effects:
        value = json.loads(effect.value_json)
        if effect.operation in ("delta", "set"):
            if effect.target == "current_hp":
                state = _hp(state, effect, value)
            elif effect.target.startswith("spell_slot."):
                state = _slot(state, effect, value)
            else:
                raise ValueError(f"Unknown sheet-effect target: {effect.target!r}")
        elif effect.operation == "apply_condition":
            if not isinstance(value, dict):
                raise ValueError("apply_condition value_json must be a JSON object")
            if state.conditions is None:
                raise ValueError("apply_condition: the character records no conditions")
            instance = ConditionInstance.model_validate(
                {"instance_id": str(uuid4()), **value}
            )
            state = state.model_copy(
                update={"conditions": (*state.conditions, instance)}
            )
        elif effect.operation == "clear_condition":
            if not isinstance(value, dict) or not (
                value.get("instance_id") or value.get("condition")
            ):
                raise ValueError(
                    "clear_condition value_json must name an instance_id or a condition"
                )
            if state.conditions is None:
                raise ValueError("clear_condition: the character records no conditions")
            kept = tuple(
                c
                for c in state.conditions
                if c.instance_id != value.get("instance_id")
                and c.condition.value != value.get("condition")
            )
            state = state.model_copy(update={"conditions": kept})
        else:
            raise ValueError(f"Unknown sheet-effect operation: {effect.operation!r}")
    # Re-validate the whole document: model_copy does not run validators.
    return Dnd5eCharacterState.model_validate(state.model_dump(mode="python"))
