"""Prerequisite A (ADR-016b): saved setup, a distinct Begin story operation,
the first cards, selection and persisted reload -- through the real app with
the production provider resolver and only the provider transport scripted.
"""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

import pytest
from sqlalchemy import func, select

from afterworlds.models.enums import BranchingPlayStatus
from afterworlds.persistence.crud.session_state import (
    get_branching_session_state_by_story,
)
from afterworlds.persistence.orm.node import TurnORM
from scripts.scripted_provider import Reply
from tests.api._spine import Spine

_CARD_STYLES = [("hybrid", "2-3"), ("true_cyoa", "2-4")]


def _play_status(s: Spine, story_id: str) -> BranchingPlayStatus:
    with s.session_factory() as session:
        state = get_branching_session_state_by_story(session, UUID(story_id))
        assert state is not None
        return state.play_status


def _turn_count(s: Spine) -> int:
    with s.session_factory() as session:
        return int(session.scalar(select(func.count()).select_from(TurnORM)) or 0)


def _begin_ready(s: Spine, style: str, count_range: str | None) -> str:
    story_id = s.create("branching")
    saved = s.setup_branching(story_id, style, count_range)
    # Setup saves configuration only: still ready to begin, no turn.
    assert saved["visible_state"]["play_status"] == "setup"
    assert _play_status(s, story_id) is BranchingPlayStatus.SETUP
    return story_id


@pytest.mark.parametrize("path", ["hosted", "byok"])
@pytest.mark.parametrize(
    ("style", "count_range"),
    [("freeform_only", None), *_CARD_STYLES],
)
def test_begin_opens_play_with_first_cards_and_reloads(
    spine: Spine, path: str, style: str, count_range: str | None
) -> None:
    s = spine
    if path == "hosted":
        s.seed_hosted()
    else:
        s.seed_byok()
    story_id = _begin_ready(s, style, count_range)
    assert s.visible(story_id)["play_status"] == "setup"  # reload before start

    begun = s.begin(story_id)
    assert begun["outcome"] == "started", begun["turn"]["pipeline_error_summary"]
    turn = begun["turn"]
    assert turn["disposition"] == "delivered", turn
    vs = begun["visible_state"]
    assert vs["play_status"] == "in_play"
    assert _play_status(s, story_id) is BranchingPlayStatus.IN_PLAY

    calls = {c.pass_name for c in s.provider.calls}
    # Classification of the opening is code-owned: no classifier call.
    assert "intent_classifier" not in calls
    assert {"planner", "extractor", "contradiction"} <= calls
    if style == "freeform_only":
        assert "writer" in calls and "branching_writer" not in calls
        assert vs["last_branch_options"] is None
    else:
        assert "branching_writer" in calls
        cards = vs["last_branch_options"]
        assert cards and [c["option_id"] for c in cards][0] == "opt_1"
        assert vs["last_presentation_state"] == "shown"

    # The binding was the selected path's production adapter and key.
    keys = {c.api_key for c in s.provider.calls}
    assert len(keys) == 1
    assert ("byok" in next(iter(keys)).lower()) is (path == "byok")
    deductions = s.deductions()
    if path == "hosted":
        assert deductions[turn["turn_id"]] > Decimal("0")
    else:
        assert deductions == {}

    # Reload after start: play and the committed cards come back.
    reloaded = s.visible(story_id)
    assert reloaded == vs
    transcript = s.transcript(story_id)
    assert [t["user_input"] for t in transcript] == ["[Begin story]"]

    # The next interaction.
    if style == "freeform_only":
        nxt = s.turn(story_id, "I walk to the harbor.")
    else:
        nxt = s.turn(story_id, "I choose opt_2 and keep my torch low")
    assert nxt["disposition"] == "delivered", nxt
    if style != "freeform_only":
        selected = s.provider.calls_for("branching_writer")[-1]
        joined = "\n".join(selected.texts)
        assert "option_id: opt_2" in joined and "annotation:" in joined


@pytest.mark.parametrize(("style", "count_range"), _CARD_STYLES)
def test_repeated_begin_is_a_no_op(spine: Spine, style: str, count_range: str) -> None:
    s = spine
    s.seed_hosted()
    story_id = _begin_ready(s, style, count_range)
    first = s.begin(story_id)
    assert first["outcome"] == "started"
    calls, turns, deductions = len(s.provider.calls), _turn_count(s), s.deductions()

    again = s.begin(story_id)
    assert again["outcome"] == "already_started"
    assert again["turn"] is None
    assert again["visible_state"] == s.visible(story_id)
    assert len(s.provider.calls) == calls  # no provider call
    assert _turn_count(s) == turns  # no second opening
    assert s.deductions() == deductions  # no second deduction


def test_begin_refuses_incomplete_or_non_branching_setup(
    spine: Spine,
) -> None:
    s = spine
    s.seed_hosted()
    story_id = s.create("branching")
    resp = s.client.post(f"/api/stories/{story_id}/begin")
    assert resp.status_code == 409
    assert resp.json()["error_code"] == "setup_required"
    s.setup_branching(story_id, "hybrid")  # range still missing
    resp = s.client.post(f"/api/stories/{story_id}/begin")
    assert resp.status_code == 409
    assert "branch_count_range" in resp.json()["message"]

    rpg = s.create("rpg")
    resp = s.client.post(f"/api/stories/{rpg}/begin")
    assert resp.status_code == 409
    assert resp.json()["error_code"] == "setup_state_conflict"
    assert s.provider.calls == []


def test_setup_validates_ranges_and_never_resets_play(
    spine: Spine,
) -> None:
    s = spine
    s.seed_hosted()
    story_id = s.create("branching")
    resp = s.client.post(
        f"/api/stories/{story_id}/setup",
        json={
            "mode": "branching",
            "interaction_style": "hybrid",
            "branching_cadence": "balanced",
            "branch_count_range": "2-5",  # True CYOA only
        },
    )
    assert resp.status_code == 422
    assert "not allowed for hybrid" in resp.json()["message"]

    s.setup_branching(story_id, "true_cyoa", "2-5")
    # Switching to Freeform-only clears the range.
    s.setup_branching(story_id, "freeform_only")
    with s.session_factory() as session:
        state = get_branching_session_state_by_story(session, UUID(story_id))
        assert state is not None and state.branch_count_range is None

    s.setup_branching(story_id, "hybrid", "1-2")
    assert s.begin(story_id)["outcome"] == "started"
    # An in-play edit keeps play and its cards; it may not leave the
    # configuration incomplete.
    s.setup_branching(story_id, "hybrid", "3-4")
    assert _play_status(s, story_id) is BranchingPlayStatus.IN_PLAY
    assert s.visible(story_id)["last_branch_options"]
    resp = s.client.post(
        f"/api/stories/{story_id}/setup",
        json={"mode": "branching", "interaction_style": "true_cyoa"},
    )
    assert resp.status_code == 422
    assert _play_status(s, story_id) is BranchingPlayStatus.IN_PLAY


@pytest.mark.parametrize(
    ("failure", "disposition"),
    [
        (Reply(status=500), "pipeline_error"),
        (Reply(refusal=True), "refused_by_provider"),
        (Reply(tool_input={"narrative_text": "x"}), "pipeline_error"),
    ],
)
def test_failed_opening_leaves_setup_retryable_and_unbilled(
    spine: Spine, failure: Reply, disposition: str
) -> None:
    s = spine
    s.seed_hosted()
    story_id = _begin_ready(s, "true_cyoa", "2-3")
    s.provider.push("branching_writer", failure)

    failed = s.begin(story_id)
    assert failed["outcome"] == "not_started", failed
    assert failed["turn"]["disposition"] == disposition
    assert failed["turn"]["delivered_output"] is None
    assert _play_status(s, story_id) is BranchingPlayStatus.SETUP
    assert _turn_count(s) == 0
    assert s.deductions() == {}
    assert s.visible(story_id)["last_branch_options"] is None

    retried = s.begin(story_id)
    assert retried["outcome"] == "started"
    assert _turn_count(s) == 1


def test_true_cyoa_selection_rails_and_ooc_after_begin(
    spine: Spine,
) -> None:
    s = spine
    s.seed_hosted()
    story_id = _begin_ready(s, "true_cyoa", "2-3")
    s.begin(story_id)
    before = _turn_count(s), s.deductions()

    freeform = s.turn(story_id, "I climb the wall instead.")
    assert freeform["disposition"] == "interaction_rejected"
    assert freeform["interaction_rejection_reason"] == "invalid_for_interaction_style"
    invalid = s.turn(story_id, "I choose opt_9")
    assert invalid["disposition"] == "interaction_rejected"
    assert invalid["interaction_rejection_reason"] == "invalid_branch_selection"
    assert (_turn_count(s), s.deductions()) == before  # non-billable, no Turn

    # OOC is always valid; its configuration change persists without
    # resetting play.
    ooc = s.turn(story_id, "[OOC] please switch me to hybrid mode")
    assert ooc["disposition"] == "ooc_handled", ooc
    vs = s.visible(story_id)
    assert vs["interaction_style"] == "hybrid" and vs["play_status"] == "in_play"
    # Hybrid now accepts freeform input against the committed cards.
    assert s.turn(story_id, "I climb the wall.")["disposition"] == "delivered"
