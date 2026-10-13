"""CRD Issue 15c — creature save effects and usage limits: damage rolled once
for every target, full on a failure and halved on a success when printed;
Recharge spent on use and rolled at the start of the creature's turn."""

from __future__ import annotations

import dataclasses
import json
from typing import Any
from unittest.mock import MagicMock

import pytest

from afterworlds.models.dnd5e_state import GrantSource, UsageCounter
from afterworlds.models.enums import RollVisibility
from afterworlds.models.rpg import (
    CreatureSaveEffectSelection,
    DiceResult,
    RollProposal,
    SubjectRef,
)
from afterworlds.pipeline.rpg.adapter import D20RulesSystemAdapter
from afterworlds.pipeline.rpg.capability import AdjudicationRefusal, RefusalKind
from afterworlds.services.dnd5e_state.turn import TurnCreature
from tests.pipeline.rpg.test_creature_attacks import _medium_wizard, _ref
from tests.pipeline.rpg.test_weapon_attacks import _creature

WYRMLING = "monsters.black_dragons.black_dragon_wyrmling"


def _wyrmling(spent: bool = False) -> TurnCreature:
    dragon = _creature(WYRMLING, hp=33)
    counters = (
        (
            UsageCounter(
                counter_id=f"{WYRMLING}/Acid Breath",
                source=GrantSource(record_key=WYRMLING),
                maximum=1,
                expended=1,
            ),
        )
        if spent
        else ()
    )
    state = dragon.stored.state.model_copy(update={"usage_counters": counters})
    return dataclasses.replace(
        dragon, stored=dataclasses.replace(dragon.stored, state=state)
    )


def _breath(dragon: TurnCreature, *targets: Any) -> RollProposal:
    return RollProposal(
        check_label="Acid Breath",
        subsystem_tag="breath",
        visibility=RollVisibility.SHOWN,
        operation="creature_save_effect",
        creature_save_effect=CreatureSaveEffectSelection(
            source=_ref(dragon), entry="Acid Breath", targets=tuple(map(_ref, targets))
        ),
    )


def _dice(d20s: list[int], d6: int = 1) -> MagicMock:
    dice = MagicMock()

    def roll(expression: str) -> DiceResult:
        if "d20" in expression:
            face = d20s.pop(0)
        elif expression == "1d6":
            face = d6
        else:
            face = 20  # 5d8
        return DiceResult(expression=expression, raw_rolls=(face,), chosen=face)

    dice.roll.side_effect = roll
    return dice


def _subjects(*creatures: TurnCreature) -> dict[tuple[str, str], Any]:
    return {("creature", str(c.subject_id)): c for c in creatures}


def test_a_breath_rolls_once_full_on_a_failure_and_half_on_a_success() -> None:
    dragon, wolf, wizard = _wyrmling(), _creature(hp=40), _medium_wizard()
    dice = _dice([2, 19])  # the wizard fails, the wolf succeeds
    record = D20RulesSystemAdapter().resolve_roll(
        _breath(dragon, wizard, wolf),
        wizard,
        None,
        dice,
        False,
        _subjects(dragon, wolf),
    )
    provenance = json.loads(record.modifiers_json)
    assert provenance["damage_rolls"] == [20]
    wizard_result, wolf_result = provenance["targets"]
    assert wizard_result["damage"]["taken"] == 20
    assert wolf_result["damage"]["taken"] == 10
    (counter,) = [e for e in record.sheet_effects if e.target == "usage_counter"]
    assert json.loads(counter.value_json)["expended"] == 1
    assert D20RulesSystemAdapter().to_writer_view(record).total is None


def test_a_spent_recharge_entry_refuses_before_any_die() -> None:
    dragon, wizard = _wyrmling(spent=True), _medium_wizard()
    with pytest.raises(AdjudicationRefusal) as caught:
        D20RulesSystemAdapter().require_supported(
            _breath(dragon, wizard), wizard, _subjects(dragon)
        )
    assert caught.value.kind is RefusalKind.INVALID_SELECTION


@pytest.mark.parametrize(("d6", "recharged"), [(5, True), (4, False)])
def test_recharge_is_rolled_when_the_creatures_turn_begins(
    d6: int, recharged: bool
) -> None:
    dragon = _wyrmling(spent=True)
    begin = RollProposal(
        check_label="Turn",
        subsystem_tag="turn",
        visibility=RollVisibility.SHOWN,
        operation="begin_turn",
        subject=SubjectRef(kind="creature", subject_id=dragon.subject_id),
    )
    record = D20RulesSystemAdapter().resolve_roll(
        begin, _medium_wizard(), None, _dice([], d6), False, _subjects(dragon)
    )
    (roll,) = json.loads(record.modifiers_json)["recharge"]
    assert roll["recharged"] is recharged
    counters = [e for e in record.sheet_effects if e.target == "usage_counter"]
    assert bool(counters) is recharged
