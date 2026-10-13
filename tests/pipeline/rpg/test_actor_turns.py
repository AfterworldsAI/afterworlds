"""CRD Issue 15c — actor-turn edges and the death save (contract G1).

``begin_turn``/``end_turn`` are explicit GameMaster edges validated before any
die; a dying subject's turn begins with its death save, every number and
result from typed authority and code-rolled dice.
"""

from __future__ import annotations

import dataclasses
import json
from typing import Any
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from afterworlds.models.dnd5e_state import (
    ActiveTurn,
    ConditionInstance,
    DeathState,
    GrantSource,
    HitPoints,
    OriginSelection,
    SubjectReference,
    TurnCoordination,
    ZeroHitPointTreatment,
)
from afterworlds.models.enums import ConditionVisibility, DiceHandling, RollVisibility
from afterworlds.models.rpg import RollProposal, SubjectRef
from afterworlds.pipeline.rpg.adapter import D20RulesSystemAdapter
from afterworlds.pipeline.rpg.capability import AdjudicationRefusal, RefusalKind
from afterworlds.pipeline.rpg.service import RpgAdjudicationPassService
from afterworlds.services.dnd5e_state.coordination import StoredCoordination
from afterworlds.services.dnd5e_state.turn import TurnCreature
from tests.pipeline.rpg.test_adjudication_service import (
    _STORY_ID,
    _TURN_ID,
    _FakeProvider,
    _make_assembled,
    _make_session,
)
from tests.pipeline.rpg.test_weapon_attacks import _attacker, _creature, _dice

CHARACTER = ZeroHitPointTreatment(subject="character")
_FALLING = GrantSource(
    record_key="play.damage_and_healing", component_key="falling_unconscious"
)


def _dying(successes: int = 0, failures: int = 0) -> TurnCreature:
    wolf = _creature(hp=11, treatment=CHARACTER)
    state = wolf.stored.state.model_copy(
        update={
            "hit_points": HitPoints(current=0, maximum=11, temporary=0),
            "death_state": DeathState(
                successes=successes, failures=failures, stable=False, dead=False
            ),
            "conditions": (
                ConditionInstance(
                    instance_id="fell",
                    condition="unconscious",  # type: ignore[arg-type]
                    visibility=ConditionVisibility.VISIBLE,
                    source=_FALLING,
                ),
            ),
        }
    )
    return dataclasses.replace(
        wolf, stored=dataclasses.replace(wolf.stored, state=state)
    )


def _edge(subject: Any, operation: str = "begin_turn") -> RollProposal:
    kind = "creature" if isinstance(subject, TurnCreature) else "character"
    return RollProposal(
        check_label="Turn",
        subsystem_tag="turn",
        visibility=RollVisibility.SHOWN,
        operation=operation,
        subject=SubjectRef(kind=kind, subject_id=subject.subject_id),
    )


def _begin(subject: TurnCreature, d20: int, d4: int = 1) -> Any:
    dice = _dice((d20,), (d4,))
    record = D20RulesSystemAdapter().resolve_roll(
        _edge(subject),
        _attacker(),
        None,
        dice,
        gm_cheating=False,
        subjects={("creature", str(subject.subject_id)): subject},
    )
    return record, dice


def _death_state(record: Any) -> DeathState:
    (effect,) = [e for e in record.sheet_effects if e.target == "death_state"]
    return DeathState.model_validate(json.loads(effect.value_json))


def test_a_dying_subjects_turn_begins_with_its_death_save() -> None:
    record, dice = _begin(_dying(), 10)
    assert dice.calls == ["1d20"]
    assert (record.total, record.dc, record.outcome) == (10, 10, "success")
    assert _death_state(record).successes == 1
    assert record.turn_edge.kind == "begin"


def test_a_natural_1_counts_two_failures() -> None:
    record, _ = _begin(_dying(failures=0), 1)
    assert record.outcome == "critical_failure"
    assert _death_state(record).failures == 2


def test_a_third_failure_is_death() -> None:
    record, _ = _begin(_dying(failures=2), 9)
    after = _death_state(record)
    assert after.dead and after.failures == 3


def test_a_third_success_is_stable_with_a_rolled_recovery_interval() -> None:
    record, dice = _begin(_dying(successes=2), 15, d4=3)
    after = _death_state(record)
    assert dice.calls == ["1d20", "1d4"]
    assert (after.stable, after.successes, after.failures) == (True, 0, 0)
    assert after.stable_recovery is not None
    assert (after.stable_recovery.interval, after.stable_recovery.unit.value) == (
        3,
        "hour",
    )


def test_a_natural_20_regains_1_hit_point_ending_unconscious_and_leaving_prone() -> (
    None
):
    record, _ = _begin(_dying(failures=2), 20)
    by_target = {e.target: e for e in record.sheet_effects}
    assert record.outcome == "critical_success"
    assert json.loads(by_target["current_hp"].value_json) == 1
    assert _death_state(record) == DeathState(
        successes=0, failures=0, stable=False, dead=False
    )
    assert json.loads(by_target["unconscious"].value_json) == {"instance_id": "fell"}
    assert json.loads(by_target["prone"].value_json)["condition"] == "prone"


def test_a_turn_that_is_not_dying_begins_without_a_roll() -> None:
    wolf = _creature()
    record, dice = _begin(wolf, 10)
    dice.roll.assert_not_called()
    assert record.sheet_effects == () and record.turn_edge.kind == "begin"
    view = D20RulesSystemAdapter().to_writer_view(record)
    assert (view.total, view.outcome) == (None, None)


def test_a_death_save_is_never_named_alone() -> None:
    with pytest.raises(AdjudicationRefusal) as caught:
        D20RulesSystemAdapter().require_supported(
            _edge(_dying(), "death_saving_throw"), _attacker(), {}
        )
    assert caught.value.kind is RefusalKind.INVALID_SELECTION


def test_a_death_save_contributor_refuses_before_rolling() -> None:
    halfling = _attacker(
        species=OriginSelection(record_key="character_origins.halfling"),
        hit_points=HitPoints(current=0, maximum=9, temporary=0),
        death_state=DeathState(successes=0, failures=0, stable=False, dead=False),
    )
    with pytest.raises(AdjudicationRefusal) as caught:
        D20RulesSystemAdapter().require_supported(_edge(halfling), halfling, {})
    assert "luck" in caught.value.detail


# ---------------------------------------------------------------------------
# The service: transitions checked before any die, coordination handed on
# ---------------------------------------------------------------------------


def _proposal_dict(subject: Any, operation: str) -> dict[str, Any]:
    kind = "creature" if isinstance(subject, TurnCreature) else "character"
    return {
        "check_label": operation,
        "subsystem_tag": "turn",
        "visibility": RollVisibility.SHOWN.value,
        "operation": operation,
        "subject": {"kind": kind, "subject_id": str(subject.subject_id)},
    }


def _service_run(subject: TurnCreature, document: TurnCoordination, *ops: str) -> Any:
    read = StoredCoordination(_STORY_ID, 4, document)
    service = RpgAdjudicationPassService(
        adapter=D20RulesSystemAdapter(),
        subject_loader=lambda _story, _ref: subject,
        coordination_loader=lambda _story: read,
        bounded_loader=lambda _story, _ref: [],
    )
    dice = _dice((10,), (1,))
    result = service.adjudicate(
        _make_assembled(),
        _make_session(DiceHandling.AI_ROLLS),
        _attacker(),
        dice,
        provider=_FakeProvider([_proposal_dict(subject, op) for op in ops]),
        story_id=_STORY_ID,
        originating_turn_id=_TURN_ID,
    )
    return result, dice


def test_the_service_hands_the_coordination_it_read_to_the_commit() -> None:
    wolf = _dying()
    result, dice = _service_run(wolf, TurnCoordination(), "begin_turn", "end_turn")
    assert result.coordination.revision == 4
    assert [r.turn_edge.kind for r in result.proposals] == ["begin", "end"]
    assert dice.calls == ["1d20"]


@pytest.mark.parametrize(
    ("document", "ops"),
    [
        (
            TurnCoordination(
                active=ActiveTurn(
                    subject=SubjectReference(kind="character", subject_id=uuid4()),
                    instance=3,
                ),
                next_instance=4,
            ),
            ("begin_turn",),
        ),
        (TurnCoordination(), ("end_turn",)),
        (TurnCoordination(), ("begin_turn", "end_turn", "begin_turn")),
    ],
)
def test_an_illegal_edge_refuses_before_any_die(
    document: TurnCoordination, ops: tuple[str, ...]
) -> None:
    wolf = _dying()
    dice = MagicMock()
    with pytest.raises(AdjudicationRefusal) as caught:
        read = StoredCoordination(_STORY_ID, 1, document)
        RpgAdjudicationPassService(
            adapter=D20RulesSystemAdapter(),
            subject_loader=lambda _story, _ref: wolf,
            coordination_loader=lambda _story: read,
            bounded_loader=lambda _story, _ref: [],
        ).adjudicate(
            _make_assembled(),
            _make_session(DiceHandling.AI_ROLLS),
            _attacker(),
            dice,
            provider=_FakeProvider([_proposal_dict(wolf, op) for op in ops]),
            story_id=_STORY_ID,
            originating_turn_id=_TURN_ID,
        )
    assert caught.value.kind is RefusalKind.INVALID_SELECTION
    dice.roll.assert_not_called()
