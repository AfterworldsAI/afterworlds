"""Weapon masteries' standing effects — CRD Issue 15c.

Sap, Slow and Vex leave an active effect that lasts until an edge of the
wielder's turn (contract G2). Each is reviewed for every roll it could touch:

* Sap — its holder's next attack roll has Disadvantage, then it is spent;
* Vex — its holder's next attack roll against the named creature has
  Advantage, then it is spent;
* Slow — a Speed reduction only; no roll.

Every other active effect still refuses the rolls it could change
(:func:`other_effects`). The masteries a weapon attack executes are in
:mod:`.attacks`.
"""

from __future__ import annotations

import json
from typing import Literal
from uuid import uuid4

from afterworlds.models.dnd5e_state import (
    ActiveEffect,
    EffectEnd,
    GrantSource,
    SubjectReference,
    TurnBoundEnd,
    TurnCoordination,
)
from afterworlds.models.rpg import SheetEffect
from afterworlds.services.dnd5e_state.turn import TurnCreature, TurnSubject

__all__ = [
    "MASTERY_EFFECTS",
    "attack_effects",
    "expiring",
    "new_effect",
    "other_effects",
    "reference",
]

_SAP, _SLOW, _VEX = (f"equipment.weapons.{m}" for m in ("sap", "slow", "vex"))
#: The masteries whose standing effects are executed where they apply.
MASTERY_EFFECTS: frozenset[str] = frozenset({_SAP, _SLOW, _VEX})


def other_effects(subject: TurnSubject) -> tuple[ActiveEffect, ...]:
    """*subject*'s active effects that are not a reviewed mastery effect."""
    return tuple(
        e
        for e in subject.stored.state.active_effects or ()
        if e.source.record_key not in MASTERY_EFFECTS
    )


def _kind(subject: TurnSubject) -> Literal["character", "creature"]:
    return "creature" if isinstance(subject, TurnCreature) else "character"


def reference(subject: TurnSubject) -> SubjectReference:
    return SubjectReference(kind=_kind(subject), subject_id=subject.subject_id)


def new_effect(
    holder: TurnSubject,
    mastery: str,
    wielder: TurnSubject,
    boundary: str,
    coordination: TurnCoordination | None,
    target: TurnSubject | None = None,
) -> SheetEffect:
    """The effect that adds *mastery*'s standing effect to *holder*, lasting
    until the *boundary* (``start``/``end``) of the wielder's next turn."""
    of = reference(wielder)
    active = coordination.active if coordination is not None else None
    effect = ActiveEffect(
        instance_id=str(uuid4()),
        source=GrantSource(
            record_key=f"equipment.weapons.{mastery}", component_key=mastery
        ),
        concentration=False,
        caster=of,
        targets=(reference(target),) if target is not None else None,
        ends=EffectEnd(
            kind="special",  # type: ignore[arg-type]
            turn=TurnBoundEnd(
                boundary=boundary,  # type: ignore[arg-type]
                of=of,
                created_in_turn=(
                    active.instance
                    if active is not None and active.subject == of
                    else None
                ),
            ),
        ),
    )
    return SheetEffect(
        target=mastery,
        operation="apply_effect",
        value_json=effect.model_dump_json(),
        subject_kind=_kind(holder),
        subject_id=holder.subject_id,
    )


def _end(holder: TurnSubject, effect: ActiveEffect) -> SheetEffect:
    return SheetEffect(
        target=effect.source.record_key.removeprefix("equipment.weapons."),
        operation="end_effect",
        value_json=json.dumps({"instance_id": effect.instance_id}),
        subject_kind=_kind(holder),
        subject_id=holder.subject_id,
    )


def attack_effects(
    attacker: TurnSubject, target: TurnSubject
) -> tuple[list[str], list[str], list[SheetEffect]]:
    """Advantage and Disadvantage the attacker's mastery effects give this
    attack roll, and the effects that spend them."""
    advantage: list[str] = []
    disadvantage: list[str] = []
    spent: list[SheetEffect] = []
    target_ref = reference(target)
    for effect in attacker.stored.state.active_effects or ():
        key = effect.source.record_key
        if key == _SAP:
            disadvantage.append(f"{_SAP}/sap")
            spent.append(_end(attacker, effect))
        elif key == _VEX and target_ref in (effect.targets or ()):
            advantage.append(f"{_VEX}/vex")
            spent.append(_end(attacker, effect))
    return advantage, disadvantage, spent


def expiring(
    subject: TurnSubject, kind: str, of: SubjectReference, instance: int
) -> list[SheetEffect]:
    """The effects that end *subject*'s turn-bounded mastery effects at this
    edge: a ``start`` boundary at the next ``begin`` of *of*; an ``end``
    boundary at the end of a turn of *of* after the one it began in."""
    out = []
    for effect in subject.stored.state.active_effects or ():
        turn = effect.ends.turn if effect.ends is not None else None
        if turn is None or turn.of != of:
            continue
        if (
            kind == "begin"
            and turn.boundary == "start"
            or (
                kind == "end"
                and turn.boundary == "end"
                and (turn.created_in_turn is None or instance > turn.created_in_turn)
            )
        ):
            out.append(_end(subject, effect))
    return out
