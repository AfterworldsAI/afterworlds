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


# ---------------------------------------------------------------------------
# Limited uses are counted before any die (codex-c7-limited-use addendum)
# ---------------------------------------------------------------------------


def _turns_of(creature: TurnCreature, *proposals: RollProposal) -> MagicMock:
    from afterworlds.models.enums import DiceHandling
    from afterworlds.pipeline.rpg.service import RpgAdjudicationPassService
    from tests.pipeline.rpg.test_adjudication_service import (
        _STORY_ID,
        _TURN_ID,
        _FakeProvider,
        _make_assembled,
        _make_session,
    )
    from tests.pipeline.rpg.test_turn_sequencing import actor_turn

    wizard = _medium_wizard()
    dice = MagicMock()
    with pytest.raises(AdjudicationRefusal) as caught:
        RpgAdjudicationPassService(
            adapter=D20RulesSystemAdapter(),
            subject_loader=lambda _story, ref: (
                creature if ref.kind == "creature" else wizard
            ),
            coordination_loader=actor_turn(creature),
            bounded_loader=lambda _story, _ref: [],
        ).adjudicate(
            _make_assembled(),
            _make_session(DiceHandling.AI_ROLLS),
            wizard,
            dice,
            provider=_FakeProvider(
                [p.model_dump(mode="json", exclude_none=True) for p in proposals]
            ),
            story_id=_STORY_ID,
            originating_turn_id=_TURN_ID,
        )
    assert caught.value.kind is RefusalKind.INVALID_SELECTION
    assert "use(s) left" in caught.value.detail
    dice.roll.assert_not_called()
    return dice


def _edge(creature: TurnCreature, operation: str) -> RollProposal:
    return RollProposal(
        check_label=operation,
        subsystem_tag="turn",
        visibility=RollVisibility.SHOWN,
        operation=operation,
        subject=_ref(creature),
    )


def test_a_ready_recharge_entry_used_twice_refuses_before_any_die() -> None:
    # The second breath would turn on a random recharge at the fresh begin:
    # that branch is held, so the composition refuses before any die.
    dragon, wizard = _wyrmling(), _medium_wizard()
    _turns_of(
        dragon,
        _breath(dragon, wizard),
        _edge(dragon, "end_turn"),
        _edge(dragon, "begin_turn"),
        _breath(dragon, wizard),
    )


def test_crossing_a_daily_quota_refuses_before_any_die() -> None:
    vrock = dataclasses.replace(
        _creature("monsters.vrock.vrock", hp=104),
    )
    state = vrock.stored.state.model_copy(update={"usage_counters": ()})
    vrock = dataclasses.replace(
        vrock, stored=dataclasses.replace(vrock.stored, state=state)
    )
    wizard = _medium_wizard()
    screech = RollProposal(
        check_label="Stunning Screech",
        subsystem_tag="screech",
        visibility=RollVisibility.SHOWN,
        operation="creature_save_effect",
        creature_save_effect=CreatureSaveEffectSelection(
            source=_ref(vrock), entry="Stunning Screech", targets=(_ref(wizard),)
        ),
    )
    _turns_of(
        vrock, screech, _edge(vrock, "end_turn"), _edge(vrock, "begin_turn"), screech
    )


# ---------------------------------------------------------------------------
# Another creature's aura can change a save: holders are found and named
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("named", "kind"),
    [
        (None, RefusalKind.MISSING_STATE),  # holders exist, none stated
        ("paladin", RefusalKind.UNSUPPORTED_CAPABILITY),  # in range: unexecuted
        ((), None),  # stated out of range: the save proceeds
    ],
)
def test_a_save_another_creatures_aura_could_change(named: Any, kind: Any) -> None:
    from afterworlds.models.enums import DiceHandling
    from afterworlds.pipeline.rpg.service import RpgAdjudicationPassService
    from tests.pipeline.rpg.test_adjudication_service import (
        _STORY_ID,
        _TURN_ID,
        _FakeProvider,
        _make_assembled,
        _make_session,
    )
    from tests.pipeline.rpg.test_turn_sequencing import actor_turn
    from tests.rpg_characters import srd_character
    from tests.services.dnd5e_state.builders import complete_character, real_index

    dragon, wizard = _wyrmling(), _medium_wizard()
    paladin = srd_character(complete_character(real_index(), "classes.paladin", 6))
    in_range = (_ref(paladin),) if named == "paladin" else named
    breath = _breath(dragon, wizard)
    assert breath.creature_save_effect is not None
    breath = breath.model_copy(
        update={
            "creature_save_effect": breath.creature_save_effect.model_copy(
                update={"auras_in_range": in_range}
            )
        }
    )
    service = RpgAdjudicationPassService(
        adapter=D20RulesSystemAdapter(),
        subject_loader=lambda _story, _ref: dragon,
        coordination_loader=actor_turn(dragon),
        aura_loader=lambda _story: [paladin, wizard],
    )

    def run() -> Any:
        return service.adjudicate(
            _make_assembled(),
            _make_session(DiceHandling.AI_ROLLS),
            wizard,
            _dice([2]),
            provider=_FakeProvider([breath.model_dump(mode="json", exclude_none=True)]),
            story_id=_STORY_ID,
            originating_turn_id=_TURN_ID,
        )

    if kind is None:
        result = run()
        # The holder was read with the turn, so its revision is rechecked.
        assert any(s.subject_id == paladin.subject_id for s in result.subjects)
        return
    with pytest.raises(AdjudicationRefusal) as caught:
        run()
    assert caught.value.kind is kind
