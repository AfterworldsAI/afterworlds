"""Issue #211, Codex round 5: the mover's conditions limit its movement.

``glossary.grappled``, ``paralyzed``, ``petrified``, ``restrained`` and
``unconscious`` set Speed to 0 and it can't increase; Exhaustion reduces it
by 5 feet a level; Prone leaves only crawling (``glossary.prone ›
restricted_movement``, prose). These read the conditions the Turn's own
character records, through its exact authority."""

from __future__ import annotations

import dataclasses

import pytest

from afterworlds.ingestion.mechanical.representation import ConditionKind
from afterworlds.models.dnd5e_state import (
    ActiveEffect,
    ConditionInstance,
    GrantSource,
)
from afterworlds.models.enums import ConditionVisibility
from afterworlds.pipeline.rpg.movement import (
    EFFECT_HELD,
    MoverProfile,
    under_conditions,
)
from afterworlds.pipeline.rpg.spatial_turn import price_character
from afterworlds.services.dnd5e_state.turn import TurnCharacter
from tests.rpg_characters import srd_character

BASE = MoverProfile(token_id="hero", walk_ft=30, strength=14, swim_ft=15)


def _with(*kinds: ConditionKind, level: int | None = None) -> TurnCharacter:
    hero = srd_character()
    conditions = tuple(
        ConditionInstance(
            instance_id=f"c{i}",
            condition=kind,
            visibility=ConditionVisibility.VISIBLE,
            level=level if kind is ConditionKind.EXHAUSTION else None,
        )
        for i, kind in enumerate(kinds)
    )
    state = hero.stored.state.model_copy(update={"conditions": conditions})
    return dataclasses.replace(
        hero, stored=dataclasses.replace(hero.stored, state=state)
    )


def test_no_conditions_leave_the_profile_as_it_is() -> None:
    assert under_conditions(BASE, _with()) == BASE


@pytest.mark.parametrize(
    "kind",
    [
        ConditionKind.GRAPPLED,
        ConditionKind.PARALYZED,
        ConditionKind.PETRIFIED,
        ConditionKind.RESTRAINED,
        ConditionKind.UNCONSCIOUS,
    ],
)
def test_speed_zero_conditions_stop_all_movement(kind: ConditionKind) -> None:
    limited = under_conditions(BASE, _with(kind))
    assert limited is not None
    assert (limited.walk_ft, limited.swim_ft, limited.climb_ft) == (0, 0, 0)


def test_exhaustion_takes_five_feet_a_level_from_every_speed() -> None:
    limited = under_conditions(BASE, _with(ConditionKind.EXHAUSTION, level=2))
    assert limited is not None
    assert (limited.walk_ft, limited.swim_ft) == (20, 5)
    deep = under_conditions(BASE, _with(ConditionKind.EXHAUSTION, level=5))
    assert deep is not None and (deep.walk_ft, deep.swim_ft) == (5, 0)


def test_prone_leaves_only_crawling() -> None:
    limited = under_conditions(BASE, _with(ConditionKind.PRONE))
    assert limited is not None and limited.crawling and limited.walk_ft == 30


def test_speed_zero_wins_over_everything_else() -> None:
    limited = under_conditions(
        BASE,
        _with(
            ConditionKind.PRONE,
            ConditionKind.GRAPPLED,
            ConditionKind.EXHAUSTION,
            level=1,
        ),
    )
    assert limited is not None and limited.walk_ft == 0


def test_a_character_that_records_no_conditions_cannot_be_priced() -> None:
    hero = srd_character()
    state = hero.stored.state.model_copy(update={"conditions": None})
    unknown = dataclasses.replace(
        hero, stored=dataclasses.replace(hero.stored, state=state)
    )
    assert under_conditions(BASE, unknown) is None


def test_the_turn_prices_the_sojourner_under_its_conditions() -> None:
    """The production entry point (``pipeline_wiring``'s mover) prices the
    character through :func:`price_character`."""
    free = price_character(_with())
    held = price_character(_with(ConditionKind.GRAPPLED))
    down = price_character(_with(ConditionKind.PRONE))
    assert free is not None and held is not None and down is not None
    assert free[0].walk_ft > 0 and not free[0].crawling
    assert held[0].walk_ft == 0
    assert down[0].crawling and down[1].crawl_extra_per_ft == 1


def _under(record_key: str) -> TurnCharacter:
    hero = _with()
    effect = ActiveEffect(
        instance_id="e1",
        source=GrantSource(record_key=record_key),
        concentration=False,
    )
    state = hero.stored.state.model_copy(update={"active_effects": (effect,)})
    return dataclasses.replace(
        hero, stored=dataclasses.replace(hero.stored, state=state)
    )


@pytest.mark.parametrize(
    "record_key", ["spells.longstrider", "spells.haste", "equipment.weapons.slow"]
)
def test_an_effect_that_may_change_speed_holds_the_move(record_key: str) -> None:
    """No spell, feature or item states a typed Speed fact the move could
    execute, so any of them in effect holds it, as checks do (Codex round 5)."""
    priced = price_character(_under(record_key))
    assert priced is not None and priced[0].held == EFFECT_HELD


@pytest.mark.parametrize("mastery", ["sap", "vex"])
def test_masteries_that_never_change_speed_do_not_hold_it(mastery: str) -> None:
    priced = price_character(_under(f"equipment.weapons.{mastery}"))
    assert priced is not None and priced[0].held is None
