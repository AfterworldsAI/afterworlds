"""CRD Issue 15c — several operations of one turn on one subject.

Each operation reads the state the turn's earlier operations left, so two
hits on one target compound; the preflight checks every operation, before any
die, with every condition the earlier operations could apply; a refusal after
a die was rolled is a named preflight defect, never an ordinary refusal.
"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock

import pytest

from afterworlds.models.dnd5e_state import ZeroHitPointTreatment
from afterworlds.models.enums import DiceHandling, RollVisibility
from afterworlds.models.rpg import DiceResult
from afterworlds.pipeline.rpg.adapter import D20RulesSystemAdapter
from afterworlds.pipeline.rpg.capability import AdjudicationRefusal
from afterworlds.pipeline.rpg.models import PreflightGapError
from afterworlds.pipeline.rpg.service import RpgAdjudicationPassService
from afterworlds.services.dnd5e_state.turn import TurnCreature
from tests.pipeline.rpg.test_adjudication_service import (
    _STORY_ID,
    _TURN_ID,
    _FakeProvider,
    _make_assembled,
    _make_session,
)
from tests.pipeline.rpg.test_weapon_attacks import CLUB, DAGGER, _attacker, _creature


def _attack(target: TurnCreature, label: str) -> dict[str, Any]:
    return {
        "check_label": label,
        "subsystem_tag": "attack",
        "skill_or_attribute_label": None,
        "visible_modifier_note": None,
        "difficulty_reference_note": None,
        "visibility": RollVisibility.SHOWN.value,
        "operation": "weapon_attack",
        "weapon_attack": {
            "weapon_item_id": str(CLUB.item_id),
            "target": {"kind": "creature", "subject_id": str(target.subject_id)},
            "range": "within_reach",
            "cover": "none",
            "attacker_light": "bright",
            "target_light": "bright",
        },
    }


def _thrown_dagger(target: TurnCreature) -> dict[str, Any]:
    # A ranged attack: whether the attacker is within 5 feet is not given.
    proposal = _attack(target, "Thrown dagger")
    proposal["weapon_attack"].update(
        weapon_item_id=str(DAGGER.item_id),
        range="within_normal_range",
        thrown=True,
        hostile_within_5_feet=False,
        ability="dexterity",
    )
    return proposal


def _dice() -> MagicMock:
    dice = MagicMock()

    def roll(expression: str) -> DiceResult:
        if "d20" in expression:
            return DiceResult(expression=expression, raw_rolls=(15,), chosen=15)
        return DiceResult(expression=expression, raw_rolls=(3,), chosen=3)

    dice.roll.side_effect = roll
    return dice


def _run(
    target: TurnCreature,
    dice: MagicMock,
    adapter: D20RulesSystemAdapter | None = None,
    second: dict[str, Any] | None = None,
) -> Any:
    service = RpgAdjudicationPassService(
        adapter=adapter or D20RulesSystemAdapter(),
        subject_loader=lambda _story, _ref: target,
    )
    return service.adjudicate(
        _make_assembled(),
        _make_session(DiceHandling.AI_ROLLS),
        _attacker(CLUB, DAGGER),
        dice,
        provider=_FakeProvider(
            [_attack(target, "First"), second or _attack(target, "Second")]
        ),
        story_id=_STORY_ID,
        originating_turn_id=_TURN_ID,
    )


def _hp_set(record: Any) -> int:
    (effect,) = [e for e in record.sheet_effects if e.target == "current_hp"]
    return int(json.loads(effect.value_json))


def test_two_hits_on_one_target_compound() -> None:
    wolf = _creature(hp=40)
    result = _run(wolf, _dice())
    first, second = result.proposals
    taken = [json.loads(r.modifiers_json)["damage"]["taken"] for r in result.proposals]
    assert _hp_set(first) == 40 - taken[0]
    assert _hp_set(second) == 40 - taken[0] - taken[1]
    # The orchestrator rechecks and applies to the snapshot the turn read.
    (subject,) = result.subjects
    assert subject.stored.state.hit_points.current == 40


def test_an_attack_after_one_that_could_knock_the_target_out_is_preflighted() -> None:
    # Treated as a character, the first hit could leave it Unconscious; the
    # second is checked with that condition before any die is rolled.
    # A thrown dagger against a Prone target needs whether the thrower is
    # within 5 feet; the preflight finds that before any die.
    wolf = _creature(hp=40, treatment=ZeroHitPointTreatment(subject="character"))
    dice = _dice()
    with pytest.raises(AdjudicationRefusal) as caught:
        _run(wolf, dice, second=_thrown_dagger(wolf))
    assert "within 5 feet" in caught.value.detail
    dice.roll.assert_not_called()


def test_a_refusal_after_dice_is_a_named_preflight_defect() -> None:
    # 2 damage takes it to exactly 0: Unconscious, not massive damage.
    wolf = _creature(hp=2, treatment=ZeroHitPointTreatment(subject="character"))
    adapter = D20RulesSystemAdapter()
    adapter.possible_conditions = lambda *_: {}  # type: ignore[method-assign]
    dice = _dice()
    with pytest.raises(PreflightGapError):
        _run(wolf, dice, adapter, second=_thrown_dagger(wolf))
    dice.roll.assert_called()
