"""Bloodied — CRD Issue 15c (codex-bloodied-linked-conditions-classification):
a certified, hand-authored universal predicate over recorded Hit Points, read
by creature traits, hit-effect damage and creature saves."""

from __future__ import annotations

import dataclasses
import json
from typing import Any

import pytest

from afterworlds.ingestion.mechanical.representation import AbilityScore
from afterworlds.models.dnd5e_state import HitPoints
from afterworlds.pipeline.rpg.adapter import D20RulesSystemAdapter
from afterworlds.pipeline.rpg.capability import AdjudicationRefusal, RefusalKind
from afterworlds.pipeline.rpg.damage import bloodied
from afterworlds.pipeline.rpg.saves import prepare as prepare_save
from afterworlds.services.dnd5e_state.turn import TurnCreature, with_effects
from tests.pipeline.rpg.test_bounded_checks import _with_component
from tests.pipeline.rpg.test_creature_attacks import (
    _bite,
    _medium_wizard,
    _resolve,
    _subjects,
)
from tests.pipeline.rpg.test_weapon_attacks import _creature, _dice
from tests.services.dnd5e_state.builders import real_index

SWARM = "animals.swarm_of_rats"
BERSERKER = "monsters.berserker.berserker"


def _at(creature: TurnCreature, current: int, **hp: Any) -> TurnCreature:
    old = creature.stored.state.hit_points
    assert old is not None
    points = old.model_copy(update={"current": current, **hp})
    state = creature.stored.state.model_copy(update={"hit_points": points})
    return dataclasses.replace(
        creature, stored=dataclasses.replace(creature.stored, state=state)
    )


@pytest.mark.parametrize(
    ("maximum", "current", "extra", "expected"),
    [
        (10, 5, {}, True),  # exactly half
        (10, 6, {}, False),  # just above
        (10, 4, {}, True),  # below
        (11, 5, {}, True),  # odd maximum: 5 is under 5.5
        (11, 6, {}, False),  # 6 is over 5.5: no rounding
        (10, 6, {"maximum_reduction": 2}, False),  # half of 8 is 4
        (10, 4, {"maximum_reduction": 2}, True),
        (10, 5, {"temporary": 20}, True),  # temporary HP are not HP
    ],
)
def test_bloodied_is_half_the_current_maximum_or_fewer(
    maximum: int, current: int, extra: dict[str, int], expected: bool
) -> None:
    creature = _at(_creature(hp=maximum), current, **extra)
    assert bloodied(creature) is expected


def test_no_recorded_hit_points_refuses() -> None:
    creature = _creature()
    state = creature.stored.state.model_copy(update={"hit_points": None})
    creature = dataclasses.replace(
        creature, stored=dataclasses.replace(creature.stored, state=state)
    )
    with pytest.raises(AdjudicationRefusal) as caught:
        bloodied(creature)
    assert caught.value.kind is RefusalKind.MISSING_STATE


@pytest.mark.parametrize(
    "template",
    [
        "animals.swarm_of_bats",
        "animals.swarm_of_insects",
        "animals.swarm_of_rats",
        "animals.swarm_of_ravens",
        "animals.swarm_of_venomous_snakes",
        "monsters.crawling_claw.swarm_of_crawling_claws",
    ],
)
@pytest.mark.parametrize("hurt", [False, True])
def test_a_bloodied_swarm_deals_its_lesser_damage(template: str, hurt: bool) -> None:
    from afterworlds.pipeline.rpg.creature_attacks import _attack_fact

    swarm = _creature(template, hp=40)
    if hurt:
        swarm = _at(swarm, 20)
    (entry,) = [
        f.entry
        for f in __import__(
            "afterworlds.pipeline.rpg.defense", fromlist=["facts_of"]
        ).facts_of(swarm.index, template)
        if type(f).__name__ == "CreatureAttackFact"
    ]
    fact = _attack_fact(swarm, entry)
    assert fact.hit_effect is not None and fact.hit_effect.conditional_damage
    lesser = fact.hit_effect.conditional_damage.term.dice
    full = fact.hit_damage[0].dice
    assert lesser is not None and full is not None
    wizard = _medium_wizard()
    dice = _dice((19,), (1,))
    record = _resolve(
        _bite(swarm, wizard, entry=entry, target_within_5_feet=True),
        wizard,
        _subjects(swarm),
        dice,
    )
    expected = lesser if hurt else full
    assert dice.calls[1] == f"{expected.count}{expected.die.value}"
    assert json.loads(record.modifiers_json)["rider"]["conditional_damage"] is hurt


@pytest.mark.parametrize(("hurt", "expression"), [(False, "1d20"), (True, "2d20kh1")])
def test_a_bloodied_berserker_attacks_and_saves_with_advantage(
    hurt: bool, expression: str
) -> None:
    berserker = _creature(BERSERKER, hp=67)
    if hurt:
        berserker = _at(berserker, 33)
    wizard = _medium_wizard()
    dice = _dice((12, 12), (1,))
    _resolve(
        _bite(berserker, wizard, entry="Greataxe"), wizard, _subjects(berserker), dice
    )
    assert dice.calls[0] == expression
    save = prepare_save(berserker, AbilityScore.DEXTERITY, 13, "test")
    assert bool(save.advantage_sources) is hurt


def test_bloodied_is_read_from_the_turns_advanced_state() -> None:
    """Within one turn, damage taken earlier makes the swarm Bloodied for its
    later attack: the predicate reads the state the operations left."""
    from afterworlds.models.rpg import SheetEffect

    swarm = _creature(SWARM, hp=40)
    hurt = with_effects(
        swarm,
        [
            SheetEffect(
                target="current_hp",
                operation="set",
                value_json="18",
                subject_kind="creature",
                subject_id=swarm.subject_id,
            )
        ],
    )
    assert not bloodied(swarm) and bloodied(hurt)


def test_overriding_the_bloodied_rule_refuses_the_operations_that_read_it() -> None:
    """Certification covers the component's effective prose: an override of
    ``glossary.bloodied/bloodied`` changes the governing fingerprint, and the
    Bloodied swarm's attack refuses as incompatible certification."""
    changed = _with_component(
        real_index(), "glossary.bloodied", "bloodied", supplied_by_override_id="house"
    )
    swarm = dataclasses.replace(_at(_creature(SWARM, hp=40), 20), index=changed)
    wizard = _medium_wizard()
    with pytest.raises(AdjudicationRefusal) as caught:
        D20RulesSystemAdapter().require_supported(
            _bite(swarm, wizard, entry="Bites", target_within_5_feet=True),
            wizard,
            _subjects(swarm),
        )
    assert caught.value.kind is RefusalKind.INCOMPATIBLE_CERTIFICATION


def test_bloodied_needs_no_extra_hp_field() -> None:
    assert HitPoints(current=1, maximum=2, temporary=0).maximum_reduction is None


def test_magic_resistance_on_a_save_refuses_rather_than_always_applying() -> None:
    """Magic Resistance's Advantage turns on whether the forcing effect is a
    spell or magical, which the save does not establish: it refuses, never
    granting Advantage on every save."""
    balor = _creature("monsters.balor.balor", hp=287)
    with pytest.raises(AdjudicationRefusal) as caught:
        prepare_save(balor, AbilityScore.DEXTERITY, 13, "test")
    assert caught.value.kind is RefusalKind.UNSUPPORTED_CAPABILITY
    assert "Magic Resistance" in caught.value.detail
