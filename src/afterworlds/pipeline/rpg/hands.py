"""Hand and grip facts — CRD Issue 15c (Owner decision 2026-10-12).

The GameMaster states, for the acting subject and from its actual holdings,
which items are in its hands with what grip, and how many hands are free
(``HandFacts``). An ``equipped`` flag is not proof of either. Code validates
the facts against holdings and the source's hand rules:

* every named item is one the subject holds, named once; hands used plus
  free hands are at most two (other held objects may fill the rest);
* a Shield is held in one hand; a Two-Handed weapon in two;
* the attacking weapon is in hand; a Versatile weapon's two-handed damage
  needs it held in two;
* loading a one-handed ammunition weapon needs a free hand
  (``ammunition_expenditure.loading_requires_free_hand``).

The facts cannot create ammunition, waive a requirement or grant an action.
Within one delivered Turn a subject's facts must agree across operations; no
operation changes grip, so a difference is a contradiction and refuses.
"""

from __future__ import annotations

from afterworlds.ingestion.mechanical.representation import (
    AmmunitionExpenditureFact,
    FreeHandWhen,
    WeaponProperty,
)
from afterworlds.models.rpg import HandFacts
from afterworlds.pipeline.rpg.capability import AdjudicationRefusal, RefusalKind
from afterworlds.pipeline.rpg.defense import facts_of
from afterworlds.services.dnd5e_state.holdings import ItemInstance
from afterworlds.services.dnd5e_state.turn import TurnSubject

__all__ = ["check_weapon_grip", "held"]

_SHIELD = "equipment.armor.shield"


def _refuse(kind: RefusalKind, detail: str) -> AdjudicationRefusal:
    return AdjudicationRefusal(kind, detail)


def held(subject: TurnSubject, facts: HandFacts | None) -> dict[object, int]:
    """The validated hands each named item is held in, by item id."""
    if facts is None:
        raise _refuse(
            RefusalKind.MISSING_STATE,
            "the attack needs the attacker's hand facts (what it holds, how)",
        )
    owned: dict[object, ItemInstance] = {i.item_id: i for i in subject.items}
    grips: dict[object, int] = {}
    for entry in facts.held:
        if entry.item_id not in owned:
            raise _refuse(
                RefusalKind.INVALID_SELECTION,
                f"item {entry.item_id} is not held by the attacker",
            )
        if entry.item_id in grips:
            raise _refuse(RefusalKind.INVALID_SELECTION, "an item is named twice")
        if owned[entry.item_id].record_key == _SHIELD and entry.hands != 1:
            raise _refuse(RefusalKind.INVALID_SELECTION, "a Shield is held in one hand")
        grips[entry.item_id] = entry.hands
    if sum(grips.values()) + facts.free_hands > 2:
        raise _refuse(
            RefusalKind.INVALID_SELECTION,
            "the hand facts account for more than two hands",
        )
    return grips


def check_weapon_grip(
    subject: TurnSubject,
    facts: HandFacts | None,
    item: ItemInstance,
    props: set[WeaponProperty],
    *,
    two_handed: bool,
) -> None:
    """Refuse unless *item* is in hand with a grip its properties allow, and
    an ammunition weapon held in one hand has a hand free to load it."""
    grips = held(subject, facts)
    assert facts is not None and subject.index is not None
    if item.item_id not in grips:
        raise _refuse(
            RefusalKind.INVALID_SELECTION, f"{item.record_key} is not in hand"
        )
    hands = grips[item.item_id]
    if WeaponProperty.TWO_HANDED in props and hands != 2:
        raise _refuse(
            RefusalKind.INVALID_SELECTION,
            f"{item.record_key} is Two-Handed and must be held in two hands",
        )
    if two_handed and hands != 2:
        raise _refuse(
            RefusalKind.INVALID_SELECTION,
            f"a two-handed Versatile attack holds {item.record_key} in two hands",
        )
    for other_id, other_hands in grips.items():
        other = next(i for i in subject.items if i.item_id == other_id)
        if other.record_key == _SHIELD and hands + other_hands > 2:
            raise _refuse(
                RefusalKind.INVALID_SELECTION, "a Shield leaves no second hand"
            )
    if WeaponProperty.AMMUNITION in props and hands == 1:
        rules = [
            f
            for f in facts_of(subject.index, "equipment.weapons.ammunition")
            if isinstance(f, AmmunitionExpenditureFact)
        ]
        if len(rules) != 1:
            raise _refuse(RefusalKind.MISSING_AUTHORITY, "Ammunition is untyped")
        rule = rules[0].loading_requires_free_hand
        if (
            rule is not None
            and rule.when is FreeHandWhen.WEAPON_IS_ONE_HANDED
            and facts.free_hands < 1
        ):
            raise _refuse(
                RefusalKind.INVALID_SELECTION,
                f"loading {item.record_key} in one hand needs a free hand",
            )
