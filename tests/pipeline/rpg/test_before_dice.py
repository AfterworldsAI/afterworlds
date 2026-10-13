"""Before-dice completeness for creature operations — CRD Issue 15c
(codex-creature-execution-final-review P1): every refusal-capable read an
operation could make happens before any die, on hit and miss alike."""

from __future__ import annotations

import dataclasses
from typing import Any
from unittest.mock import MagicMock

import pytest

from afterworlds.ingestion.mechanical.representation import ConditionKind
from afterworlds.models.enums import DiceHandling, RollVisibility
from afterworlds.models.rpg import CreatureSaveEffectSelection, RollProposal
from afterworlds.pipeline.rpg.adapter import D20RulesSystemAdapter
from afterworlds.pipeline.rpg.capability import AdjudicationRefusal, RefusalKind
from afterworlds.pipeline.rpg.service import RpgAdjudicationPassService
from tests.pipeline.rpg.test_adjudication_service import (
    _STORY_ID,
    _TURN_ID,
    _FakeProvider,
    _make_assembled,
    _make_session,
)
from tests.pipeline.rpg.test_creature_attacks import _bite, _medium_wizard, _ref
from tests.pipeline.rpg.test_turn_sequencing import actor_turn
from tests.pipeline.rpg.test_weapon_attacks import _creature


def _changed(subject: Any, **values: Any) -> Any:
    state = type(subject.stored.state).model_validate(
        {**subject.stored.state.model_dump(mode="python"), **values}
    )
    return dataclasses.replace(
        subject, stored=dataclasses.replace(subject.stored, state=state)
    )


def _turn(source: Any, target: Any, proposal: RollProposal) -> tuple[Any, MagicMock]:
    dice = MagicMock()
    with pytest.raises(AdjudicationRefusal) as caught:
        RpgAdjudicationPassService(
            adapter=D20RulesSystemAdapter(),
            subject_loader=lambda _story, _ref: source,
            coordination_loader=actor_turn(source),
            bounded_loader=lambda _story, _ref: [],
            aura_loader=lambda _story: [],
        ).adjudicate(
            _make_assembled(),
            _make_session(DiceHandling.AI_ROLLS),
            target,
            dice,
            provider=_FakeProvider(
                [proposal.model_dump(mode="json", exclude_none=True)]
            ),
            story_id=_STORY_ID,
            originating_turn_id=_TURN_ID,
        )
    return caught.value, dice


def _immune(kind: ConditionKind) -> Any:
    return _changed(_medium_wizard(), condition_immunities=(kind,))


@pytest.mark.parametrize(
    ("template", "entry", "immunity", "facts"),
    [
        ("animals.wolf", "Bite", ConditionKind.PRONE, {}),  # direct rider
        (
            "monsters.purple_worm.purple_worm",
            "Bite",
            ConditionKind.RESTRAINED,  # linked rider
            {"target_within_5_feet": False},
        ),
        (
            "animals.allosaurus",
            "Claws",
            ConditionKind.PRONE,  # clause under a holding charge predicate
            {"moved_straight_toward_target": True},
        ),
    ],
)
def test_an_unvalidated_recorded_immunity_refuses_with_no_die(
    template: str, entry: str, immunity: ConditionKind, facts: dict[str, Any]
) -> None:
    source, target = _creature(template, hp=250), _immune(immunity)
    refusal, dice = _turn(source, target, _bite(source, target, entry=entry, **facts))
    assert refusal.kind is RefusalKind.UNSUPPORTED_CAPABILITY
    dice.roll.assert_not_called()


def test_a_bloodied_predicate_on_missing_hit_points_refuses_with_no_die() -> None:
    swarm = _changed(_creature("animals.swarm_of_rats"), hit_points=None)
    wizard = _medium_wizard()
    refusal, dice = _turn(
        swarm, wizard, _bite(swarm, wizard, entry="Bites", target_within_5_feet=True)
    )
    assert refusal.kind is RefusalKind.MISSING_STATE
    dice.roll.assert_not_called()


def test_a_condition_that_cannot_apply_is_not_read() -> None:
    """The Wolf's Prone is limited to Large or smaller: against a larger
    target its immunity is never consulted, and the bite proceeds."""
    wolf, mammoth = _creature(), _creature("animals.mammoth", hp=126)
    D20RulesSystemAdapter().require_supported(
        _bite(wolf, mammoth),
        _medium_wizard(),
        {
            ("creature", str(wolf.subject_id)): wolf,
            ("creature", str(mammoth.subject_id)): mammoth,
        },
    )


def test_a_save_effects_condition_immunity_is_read_before_any_die() -> None:
    lion, target = _creature("animals.lion", hp=60), _immune(ConditionKind.FRIGHTENED)
    proposal = RollProposal(
        check_label="Roar",
        subsystem_tag="save",
        visibility=RollVisibility.SHOWN,
        operation="creature_save_effect",
        creature_save_effect=CreatureSaveEffectSelection(
            source=_ref(lion), entry="Roar", targets=(_ref(target),), auras_in_range=()
        ),
    )
    refusal, dice = _turn(lion, target, proposal)
    assert refusal.kind is RefusalKind.UNSUPPORTED_CAPABILITY
    dice.roll.assert_not_called()
