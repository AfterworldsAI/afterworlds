"""Issue #211: Sojourn records a fall's damage and Prone (ADR-015 Fork B1).

The fall is rolled by movement adjudication; these tests check the record
the Turn audits and the sheet effects it applies, through the same in-memory
applier the Turn uses. The mapper writes none of this."""

from __future__ import annotations

import dataclasses
import json

from afterworlds.ingestion.mechanical.representation import ConditionKind
from afterworlds.models.dnd5e_state import ConditionInstance, HitPoints
from afterworlds.models.enums import ConditionVisibility, RollVisibility
from afterworlds.pipeline.orchestrator.service import _with_fall
from afterworlds.pipeline.rpg.falls import fall_record
from afterworlds.pipeline.rpg.models import AdjudicationPassResult
from afterworlds.pipeline.rpg.movement import FallRoll, MoveOutcome
from afterworlds.services.dnd5e_state.turn import TurnCharacter, with_effects
from tests.rpg_characters import srd_character

TEN_FT = FallRoll(depth_ft=10, expression="1d6", raw_rolls=(4,), total=4, prone=True)


def _hero(
    *, hp: int | None = None, conditions: tuple[ConditionInstance, ...] = ()
) -> TurnCharacter:
    hero = srd_character()
    state = hero.stored.state
    points = state.hit_points
    assert points is not None
    state = state.model_copy(
        update={
            "hit_points": HitPoints(
                current=points.maximum if hp is None else hp,
                maximum=points.maximum,
                temporary=0,
            ),
            "conditions": conditions,
        }
    )
    return dataclasses.replace(
        hero, stored=dataclasses.replace(hero.stored, state=state)
    )


def _after(hero: TurnCharacter, fall: FallRoll = TEN_FT) -> TurnCharacter:
    record, _ = fall_record(fall, hero, gm_cheating=False)
    return with_effects(hero, list(record.sheet_effects))


def _prone(hero: TurnCharacter) -> list[ConditionInstance]:
    return [
        c
        for c in hero.stored.state.conditions or ()
        if c.condition is ConditionKind.PRONE
    ]


def test_a_fall_is_one_shown_record_of_its_dice() -> None:
    hero = _hero()
    record, view = fall_record(TEN_FT, hero, gm_cheating=True)
    assert record.check_label == view.check_label == "Falling 10 ft"
    assert record.visibility is RollVisibility.SHOWN
    assert (record.expression, record.raw_rolls, record.total) == ("1d6", (4,), 4)
    assert record.outcome == "undetermined"
    assert record.source == "ai"
    assert record.gm_cheating_at_roll is True
    provenance = json.loads(record.modifiers_json)
    assert provenance["operation"] == "fall"
    assert provenance["damage"]["taken"] == 4
    assert provenance["prone"] == "applied"
    assert view.total == 4
    assert view.player_facing_summary == (
        "Fell 10 ft, took 4 bludgeoning damage, landed Prone."
    )


def test_the_fall_takes_hit_points_and_leaves_the_mover_prone() -> None:
    hero = _hero()
    points = hero.stored.state.hit_points
    assert points is not None
    after = _after(hero)
    assert after.stored.state.hit_points is not None
    assert after.stored.state.hit_points.current == points.maximum - 4
    (prone,) = _prone(after)
    assert prone.visibility is ConditionVisibility.VISIBLE
    assert prone.source is not None
    assert prone.source.record_key == "glossary.falling"
    record, _ = fall_record(TEN_FT, hero, gm_cheating=False)
    assert all(
        e.subject_kind == "character" and e.subject_id == hero.sheet_id
        for e in record.sheet_effects
    )


def test_a_mover_already_prone_gets_no_second_prone() -> None:
    hero = _after(_hero(), FallRoll(5, "", (), 0, prone=True))
    record, _ = fall_record(TEN_FT, hero, gm_cheating=False)
    assert [e.target for e in record.sheet_effects] == ["current_hp"]
    assert json.loads(record.modifiers_json)["prone"] == "already_prone"
    assert len(_prone(with_effects(hero, list(record.sheet_effects)))) == 1


def test_a_short_fall_rolls_nothing_but_still_lands_prone() -> None:
    short = FallRoll(depth_ft=5, expression="", raw_rolls=(), total=0, prone=True)
    hero = _hero()
    record, view = fall_record(short, hero, gm_cheating=False)
    assert (record.expression, record.raw_rolls, record.total) == ("", (), 0)
    assert [e.target for e in record.sheet_effects] == ["prone"]
    assert json.loads(record.modifiers_json)["damage"] is None
    assert view.player_facing_summary == "Fell 5 ft, landed Prone."


def test_a_fall_to_zero_hit_points_leaves_the_mover_dying_and_prone() -> None:
    after = _after(_hero(hp=3))
    state = after.stored.state
    assert state.hit_points is not None and state.hit_points.current == 0
    kinds = {c.condition for c in state.conditions or ()}
    assert {ConditionKind.UNCONSCIOUS, ConditionKind.PRONE} <= kinds
    assert state.death_state is not None and not state.death_state.dead
    _, view = fall_record(TEN_FT, _hero(hp=3), gm_cheating=False)
    assert "Unconscious" in view.player_facing_summary


def test_a_fall_that_kills_leaves_no_prone() -> None:
    hero = _hero(hp=1)
    points = hero.stored.state.hit_points
    assert points is not None
    # Overflow past 0 of at least the Hit Point maximum is massive damage.
    big = points.maximum + 1
    deep = FallRoll(
        depth_ft=200, expression="20d6", raw_rolls=(), total=big, prone=True
    )
    record, view = fall_record(deep, hero, gm_cheating=False)
    assert json.loads(record.modifiers_json)["prone"] == "dead"
    assert "prone" not in [e.target for e in record.sheet_effects]
    assert with_effects(hero, list(record.sheet_effects)).stored.state.death_state
    assert view.player_facing_summary.endswith("died.")


# -- the Turn's guards (orchestrator ``_with_fall``) -----------------------


def _moved(fall: FallRoll = TEN_FT) -> MoveOutcome:
    return MoveOutcome(
        token_id="hero",
        status="stopped",
        route=((1, 4), (2, 4)),
        travelled=((1, 4), (2, 4)),
        distance_ft=5,
        movement_spent_ft=5,
        final_square=(2, 4),
        stopped_by="pit:p1",
        refused=None,
        dash=False,
        disengage=False,
        source="drawn",
        fall=fall,
    )


def _merged(
    hero: TurnCharacter,
    adj: AdjudicationPassResult | None = None,
    roller: tuple[str, str] | None = None,
) -> AdjudicationPassResult | str:
    return _with_fall(
        adj or AdjudicationPassResult(proposals=(), writer_views=()),
        _moved(),
        roller or ("character", str(hero.sheet_id)),
        hero,
        gm_cheating=False,
    )


def test_the_turn_adds_the_fall_after_its_other_records() -> None:
    hero = _hero()
    merged = _merged(hero)
    assert isinstance(merged, AdjudicationPassResult)
    [record] = merged.proposals
    [view] = merged.writer_views
    assert record.check_label == view.check_label == "Falling 10 ft"


def test_the_turn_refuses_a_fall_on_another_mover() -> None:
    hero = _hero()
    assert _merged(hero, roller=("character", "someone-else")) == (
        "a fall landed on a mover that is not this Turn's character"
    )


def test_the_turn_refuses_a_fall_beside_a_sequence() -> None:
    hero = _hero()
    paused = AdjudicationPassResult(proposals=(), writer_views=(), sequence=object())
    assert "action sequence" in str(_merged(hero, paused))


def test_the_turn_refuses_a_fall_beside_other_hit_point_changes() -> None:
    hero = _hero()
    first, view = fall_record(TEN_FT, hero, gm_cheating=False)
    other = AdjudicationPassResult(proposals=(first,), writer_views=(view,))
    assert "Hit Points" in str(_merged(hero, other))


def test_the_turn_refuses_a_fall_its_authority_cannot_settle() -> None:
    hero = dataclasses.replace(_hero(), index=None)
    assert "could not be adjudicated" in str(_merged(hero))
