"""CRD Issue 15b Phase 2: a player-rolled attack and its damage, end to end
on the backend (``sequence_stack``: isolated store and services, no
``create_app`` or HTTP route).
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from afterworlds.models.enums import DiceHandling, RpgInteractionPhase
from afterworlds.pipeline.orchestrator.models import PipelineDisposition
from tests.ingestion.mechanical.sequence_stack import (
    Stack,
    Story_,
    no_backend_dice,
    stack,
)
from tests.ingestion.mechanical.test_bounded_d20_on_published_release import (
    g1_store,
    gm,
)

__all__ = ["g1_store", "gm", "stack"]  # fixtures used by pytest


def club_attack(
    stack: Stack, story: Story_, target: Any, **facts: Any
) -> dict[str, Any]:
    club = stack.item(story, "equipment.weapons.club", equipped=True)
    return {
        "check_label": "Club attack",
        "subsystem_tag": "attack",
        "visibility": "shown",
        "operation": "weapon_attack",
        "weapon_attack": {
            "weapon_item_id": str(club),
            "target": {"kind": "creature", "subject_id": str(target)},
            "range": "within_reach",
            "cover": "none",
            "attacker_light": "bright",
            "target_light": "bright",
            "hands": {"held": [{"item_id": str(club), "hands": 1}], "free_hands": 1},
            **facts,
        },
    }


def begin(story: Story_) -> dict[str, Any]:
    return {
        "check_label": "Turn",
        "subsystem_tag": "turn",
        "visibility": "shown",
        "operation": "begin_turn",
        "subject": {"kind": "character", "subject_id": str(story.sheet_id)},
    }


def test_a_player_rolled_attack_and_its_damage_resolve_as_one_sequence(
    stack: Stack, gm: list[list[dict[str, Any]]], monkeypatch: pytest.MonkeyPatch
) -> None:
    """The acting character's Club attack in a player-rolled story pauses for
    the attack die, then the damage die, with a reload in between, and is
    narrated once; nothing applies before that narration."""
    rolled = no_backend_dice(monkeypatch)
    story = stack.story(DiceHandling.PLAYER_ROLLS)
    wolf = stack.creature(story)
    gm.append([begin(story), club_attack(stack, story, wolf)])
    announce = stack.turn(story, "I swing my club at the wolf.")
    assert announce.disposition is PipelineDisposition.DELIVERED, announce
    # The announce Turn starts the sequence: no audit and no effect exist.
    assert stack.audit(story) == [] and stack.hp(wolf) == (1, 11)

    first = stack.sequences.current(story.story_id)
    assert first is not None and first.pending_roll is not None
    attack = first.pending_roll
    assert attack.interaction_phase is RpgInteractionPhase.PENDING_ROLL
    assert attack.display_expression == "1d20 + 1"  # Str -1, proficiency +2
    assert attack.progress.step_index == 1
    public = attack.model_dump_json()
    assert '"dc"' not in public and "12" not in public  # the Wolf's AC stays hidden
    assert stack.sequences.current(story.story_id) == first  # reload: identical

    damage_view = stack.roll(attack, 15)  # 15 + 1 = 16 hits AC 12
    damage = damage_view.pending_roll
    assert damage is not None and damage.display_expression == "1d4 - 1"
    assert damage.progress.step_index == 2
    assert stack.sequences.current(story.story_id) == damage_view

    ready = stack.roll(damage, 4)  # 4 - 1 = 3 damage
    assert ready.interaction_phase is RpgInteractionPhase.READY_FOR_NARRATION
    seq = stack.sequence(story)
    assert seq["status"] == "ready_for_narration"
    projected = json.loads(seq["projected_state_json"])
    assert projected[f"creature:{wolf}"]["hit_points"]["current"] == 8
    assert stack.hp(wolf) == (1, 11)  # projected only

    result = stack.resume(story)
    assert result.disposition is PipelineDisposition.DELIVERED, result
    assert result.planner_skipped and result.planner_result is None
    assert rolled == []  # every die was the Sojourner's
    assert stack.hp(wolf) == (2, 8)
    audit = stack.audit(story)
    assert [(a.check_label, a.source, a.total, a.dc, a.outcome) for a in audit] == [
        ("Club attack", "player", 16, 12, "success"),
        ("Club damage", "player", 3, None, "undetermined"),
    ]
    assert all(
        a.submission_source == "inline_ui"
        and a.raw_values_complete
        and a.pending_roll_request_id is not None
        and a.turn_id == str(result.turn_id)
        for a in audit
    )
    # The begin_turn edge (no die) committed with the narrated Turn.
    assert stack.rows("SELECT kind FROM rpg_turn_edges") == [
        ("begin",),
        ("use",),
        ("use",),
    ]

    again = stack.resume(story)
    assert again.disposition is PipelineDisposition.PIPELINE_ERROR
    assert again.action_sequence_error == "ACTION_SEQUENCE_ALREADY_COMPLETED"
    assert len(stack.audit(story)) == 2
