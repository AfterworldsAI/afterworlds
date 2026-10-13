"""Apply code-derived sheet effects to typed character or creature state —
CRD Issues 2b and 15c.

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
from typing import cast
from uuid import uuid4

from afterworlds.models.dnd5e_state import (
    ActiveEffect,
    ConditionInstance,
    CreatureState,
    DeathState,
    Dnd5eCharacterState,
    UsageCounter,
)
from afterworlds.models.rpg import SheetEffect

__all__ = ["apply_effects"]

#: A subject's typed state: a character's or a continuing creature's.
_State = Dnd5eCharacterState | CreatureState


def _int(value: object, target: str) -> int:
    if type(value) is not int:
        raise ValueError(f"{target}: value must be an integer, got {value!r}")
    return value


def _hp(state: _State, effect: SheetEffect, value: object) -> _State:
    hp = state.hit_points
    if hp is None:
        raise ValueError("current_hp: the subject records no hit points")
    amount = _int(value, effect.target)
    current = hp.current + amount if effect.operation == "delta" else amount
    current = min(hp.maximum, current)
    # Only ``current`` changes; every other recorded field is kept.
    return state.model_copy(
        update={"hit_points": hp.model_copy(update={"current": current})}
    )


def _temporary_hp(state: _State, effect: SheetEffect, value: object) -> _State:
    """Temporary hit points: ``set`` only (damage absorbs them; code derives
    the remaining amount)."""
    hp = state.hit_points
    if hp is None or effect.operation != "set":
        raise ValueError("temporary_hp: needs recorded hit points and a set")
    amount = _int(value, effect.target)
    if amount < 0:
        raise ValueError("temporary_hp cannot be negative")
    source = hp.temporary_source if amount else None
    return state.model_copy(
        update={
            "hit_points": hp.model_copy(
                update={"temporary": amount, "temporary_source": source}
            )
        }
    )


def _death_state(state: _State, effect: SheetEffect, value: object) -> _State:
    """Death-save counters, Stable and dead: ``set`` to a whole typed value."""
    if effect.operation != "set" or not isinstance(value, dict):
        raise ValueError("death_state: set a JSON object")
    return state.model_copy(update={"death_state": DeathState.model_validate(value)})


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


def _usage_counter(state: _State, effect: SheetEffect, value: object) -> _State:
    """``set`` one usage counter, by ``counter_id``: replaced, or added."""
    if effect.operation != "set" or not isinstance(value, dict):
        raise ValueError("usage_counter: set a JSON object")
    if state.usage_counters is None:
        raise ValueError("usage_counter: the subject records no usage counters")
    counter = UsageCounter.model_validate(value)
    kept = tuple(c for c in state.usage_counters if c.counter_id != counter.counter_id)
    return state.model_copy(update={"usage_counters": (*kept, counter)})


def apply_effects[S: _State](state: S, effects: tuple[SheetEffect, ...]) -> S:
    """*state* after *effects*, re-validated as its own document type."""
    return cast(S, _apply(state, effects))


def _apply(state: _State, effects: tuple[SheetEffect, ...]) -> _State:
    for effect in effects:
        value = json.loads(effect.value_json)
        if effect.operation in ("delta", "set"):
            if effect.target == "current_hp":
                state = _hp(state, effect, value)
            elif effect.target == "temporary_hp":
                state = _temporary_hp(state, effect, value)
            elif effect.target == "death_state":
                state = _death_state(state, effect, value)
            elif effect.target == "usage_counter":
                state = _usage_counter(state, effect, value)
            elif effect.target.startswith("spell_slot."):
                if not isinstance(state, Dnd5eCharacterState):
                    raise ValueError(f"{effect.target}: a creature records no slots")
                state = _slot(state, effect, value)
            else:
                raise ValueError(f"Unknown sheet-effect target: {effect.target!r}")
        elif effect.operation == "apply_condition":
            if not isinstance(value, dict):
                raise ValueError("apply_condition value_json must be a JSON object")
            if state.conditions is None:
                raise ValueError("apply_condition: the subject records no conditions")
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
                raise ValueError("clear_condition: the subject records no conditions")
            kept = tuple(
                c
                for c in state.conditions
                if c.instance_id != value.get("instance_id")
                and c.condition.value != value.get("condition")
            )
            # A condition lasting while a removed instance ends with it.
            ids = {c.instance_id for c in kept}
            kept = tuple(
                c
                for c in kept
                if c.lasts_while_instance is None or c.lasts_while_instance in ids
            )
            state = state.model_copy(update={"conditions": kept})
        elif effect.operation == "apply_effect":
            if state.active_effects is None:
                raise ValueError("apply_effect: the subject records no active effects")
            added = ActiveEffect.model_validate(value)
            state = state.model_copy(
                update={"active_effects": (*state.active_effects, added)}
            )
        elif effect.operation == "end_effect":
            if not isinstance(value, dict) or not value.get("instance_id"):
                raise ValueError("end_effect value_json must name an instance_id")
            if state.active_effects is None:
                raise ValueError("end_effect: the subject records no active effects")
            state = state.model_copy(
                update={
                    "active_effects": tuple(
                        e
                        for e in state.active_effects
                        if e.instance_id != value["instance_id"]
                    )
                }
            )
        else:
            raise ValueError(f"Unknown sheet-effect operation: {effect.operation!r}")
    # Re-validate the whole document: model_copy does not run validators.
    return type(state).model_validate(state.model_dump(mode="python"))
