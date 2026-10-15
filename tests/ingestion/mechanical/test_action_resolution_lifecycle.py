"""CRD Issue 15b Phase 2: action-resolution lifecycle proofs on the backend
(``sequence_stack``: an isolated store, the existing backend services, a
test-owned ``ActionResolutionService``; no ``create_app`` or HTTP route).

Contests run with the S1 supplement applied in memory only (``s1``).
"""

from __future__ import annotations

import json
from typing import Any
from uuid import UUID

import pytest
import sqlalchemy as sa

from afterworlds.models.enums import DiceHandling, RpgInteractionPhase
from afterworlds.pipeline.orchestrator.models import PipelineDisposition
from afterworlds.pipeline.rpg import sequence as sequence_module
from afterworlds.pipeline.rpg.models import (
    ActionSequenceStateConflictError,
    PendingRollAlreadyConsumedError,
    PendingRollRevisionMismatchError,
)
from afterworlds.pipeline.rpg.sequence import ActionResolutionService
from afterworlds.services.dnd5e_state.authority import AuthorityIndex
from tests.ingestion.mechanical.sequence_stack import (
    Stack,
    Story_,
    s1,
    scripted_dice,
    stack,
)
from tests.ingestion.mechanical.test_bounded_d20_on_published_release import (
    g1_store,
    gm,
)
from tests.services.dnd5e_state.builders import complete_character

__all__ = ["g1_store", "gm", "stack"]  # fixtures used by pytest

GM = list[list[dict[str, Any]]]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _faces(monkeypatch: pytest.MonkeyPatch, *faces: int) -> list[str]:
    """Backend d20s answering *faces* in order; the log of every draw."""
    queue = list(faces)
    return scripted_dice(monkeypatch, lambda _expression: (queue.pop(0),))


def _contest_story(stack: Stack, index: AuthorityIndex) -> tuple[Story_, UUID]:
    """A player-rolled wizard (Str -1, no Athletics) and an Ape (Athletics
    +5), both bound to the S1-supplemented authority."""
    story = stack.story(
        DiceHandling.PLAYER_ROLLS,
        character=complete_character(index, "classes.wizard", 3),
        binding=index.binding,
    )
    ape = stack.creature(story, "animals.ape", hp=19, name="Ape", binding=index.binding)
    return story, ape


def _contest(
    story: Story_,
    ape: UUID,
    *,
    hidden: bool = False,
    perceived: bool = True,
) -> dict[str, Any]:
    return {
        "check_label": "Arm wrestling",
        "subsystem_tag": "contest",
        "visibility": "shown",
        "operation": "contest",
        "contest": {
            "initiator": {
                "subject": {"kind": "character", "subject_id": str(story.sheet_id)},
                "ability": "strength",
                "skill": "athletics",
            },
            "resister": {
                "subject": {"kind": "creature", "subject_id": str(ape)},
                "ability": "strength",
                "skill": "athletics",
                "roll_hidden": hidden,
            },
            "stakes": "the ring on the table",
            "counterpart_perceived": perceived,
        },
    }


def _announce(stack: Stack, gm: GM, story: Story_, proposal: dict[str, Any]) -> Any:
    gm.append([proposal])
    announce = stack.turn(story, "I challenge the ape to arm wrestling.")
    assert announce.disposition is PipelineDisposition.DELIVERED, announce
    view = stack.sequences.current(story.story_id)
    assert view is not None and view.pending_roll is not None
    return view.pending_roll


def _payloads(stack: Stack, story: Story_) -> list[dict[str, Any]]:
    return [json.loads(e.payload_json) for e in stack.events(story)]


def _state(stack: Stack, story: Story_) -> tuple[Any, ...]:
    """Everything an intermediate operation may change."""
    seq = stack.sequence(story)
    pending = stack.rows(
        "SELECT request_id, status, instruction_revision FROM pending_roll_requests"
        " WHERE story_id = :s ORDER BY request_id",
        s=str(story.story_id),
    )
    return (
        seq["status"],
        seq["revision"],
        seq["current_pending_roll_request_id"],
        len(stack.events(story)),
        tuple(tuple(p) for p in pending),
    )


# ---------------------------------------------------------------------------
# Contests (ADR-015b Group 17) on the sequence
# ---------------------------------------------------------------------------


def test_a_player_contest_draws_the_counterpart_inside_the_accepting_write(
    stack: Stack, gm: GM, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The announce Turn freezes both instructions and draws no die; the
    Sojourner's die is accepted and the Ape's counterpart die is drawn in that
    same intermediate transaction; the delivered Turn audits both rolls and
    the one combined resolution."""
    index = s1(monkeypatch)
    rolled = _faces(monkeypatch, 15)
    story, ape = _contest_story(stack, index)
    pending = _announce(stack, gm, story, _contest(story, ape))
    assert rolled == []  # no counterpart die before the Sojourner's
    assert pending.display_expression == "1d20 - 1"
    assert pending.display_label.endswith("contest")

    ready = stack.roll(pending, 12)  # 11 against the Ape's 15 + 5 = 20
    assert ready.interaction_phase is RpgInteractionPhase.READY_FOR_NARRATION
    assert rolled == ["1d20"]
    mine, theirs = _payloads(stack, story)
    assert (mine["kind"], theirs["kind"]) == ("player_roll", "ai_roll")
    assert (mine["total"], theirs["total"]) == (11, 20)
    assert mine["contest_resolution"] is None
    resolution = theirs["contest_resolution"]
    # One resolution, identified by the participants' actual steps.
    steps = [p["step_id"] for p in resolution["participants"]]
    events = stack.rows(
        "SELECT step_id FROM action_resolution_events WHERE story_id = :s"
        " ORDER BY event_order",
        s=str(story.story_id),
    )
    assert steps == [e.step_id for e in events]
    assert resolution["result"] == "win"
    assert resolution["winner"]["subject_id"] == str(ape)
    (record,) = [
        r["record"]
        for e in stack.events(story)
        for r in json.loads(e.mechanical_provenance)["records"]
    ]
    assert record["contest_resolution"] == resolution

    result = stack.resume(story)
    assert result.disposition is PipelineDisposition.DELIVERED, result
    audit = stack.audit(story)
    assert [(a.source, a.total) for a in audit] == [("player", 11), ("ai", 20)]
    stored = [
        json.loads(a.contest_resolution_json)
        for a in audit
        if a.contest_resolution_json
    ]
    assert stored == [resolution]
    assert rolled == ["1d20"]  # delivery draws nothing


def test_a_losing_concurrent_submission_draws_no_counterpart_die(
    stack: Stack, gm: GM, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Two submissions of the same pending roll: the second to claim the
    sequence fails at the claim, before any die; only the winner's
    counterpart die was ever drawn."""
    index = s1(monkeypatch)
    rolled = _faces(monkeypatch, 15)
    story, ape = _contest_story(stack, index)
    pending = _announce(stack, gm, story, _contest(story, ape))

    real_advance = ActionResolutionService._advance  # noqa: SLF001
    raced: list[str] = []

    def racing(self: ActionResolutionService, *args: Any, **kwargs: Any) -> Any:
        if not raced:  # the loser has read and validated; the winner commits first
            raced.append("winner")
            stack.roll(pending, 12)
        return real_advance(self, *args, **kwargs)

    monkeypatch.setattr(ActionResolutionService, "_advance", racing)
    with pytest.raises(ActionSequenceStateConflictError):
        stack.roll(pending, 3)
    assert rolled == ["1d20"]  # the winner's counterpart only
    assert [p["total"] for p in _payloads(stack, story)] == [11, 20]
    assert stack.sequence(story)["status"] == "ready_for_narration"


def test_stale_and_duplicate_submissions_draw_nothing_and_change_nothing(
    stack: Stack, gm: GM, monkeypatch: pytest.MonkeyPatch
) -> None:
    index = s1(monkeypatch)
    rolled = _faces(monkeypatch, 15)
    story, ape = _contest_story(stack, index)
    pending = _announce(stack, gm, story, _contest(story, ape))
    before = _state(stack, story)
    with pytest.raises(PendingRollRevisionMismatchError):
        stack.roll(pending, 12, revision=pending.instruction_revision + 1)
    assert rolled == [] and _state(stack, story) == before

    stack.roll(pending, 12)
    after = _state(stack, story)
    with pytest.raises(PendingRollAlreadyConsumedError):
        stack.roll(pending, 12)  # a duplicate of the accepted submission
    assert rolled == ["1d20"] and _state(stack, story) == after


def test_a_failed_accepting_write_discards_its_counterpart_die(
    stack: Stack, gm: GM, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A failure after the counterpart die is drawn rolls the whole write
    back: no event, the pending roll still pending, the revision unmoved. The
    discarded die never becomes authority: the retry draws its own."""
    index = s1(monkeypatch)
    rolled = _faces(monkeypatch, 15, 2)
    story, ape = _contest_story(stack, index)
    pending = _announce(stack, gm, story, _contest(story, ape))
    before = _state(stack, story)

    real_recheck = sequence_module._recheck  # noqa: SLF001
    failures = ["once"]

    def failing(session: Any, prepared: Any) -> None:
        if failures:
            failures.pop()
            raise ActionSequenceStateConflictError("injected write failure")
        real_recheck(session, prepared)

    monkeypatch.setattr(sequence_module, "_recheck", failing)
    with pytest.raises(ActionSequenceStateConflictError, match="injected"):
        stack.roll(pending, 12)
    assert rolled == ["1d20"]  # drawn inside the failed write
    assert _state(stack, story) == before

    stack.roll(pending, 12)
    assert rolled == ["1d20", "1d20"]
    mine, theirs = _payloads(stack, story)
    assert theirs["total"] == 7  # the retry's 2 + 5, not the discarded 15 + 5
    assert theirs["contest_resolution"]["winner"]["subject_id"] == str(story.sheet_id)


@pytest.mark.parametrize("target", ["record", "event"])
def test_a_tampered_contest_resolution_refuses_delivery(
    stack: Stack, gm: GM, monkeypatch: pytest.MonkeyPatch, target: str
) -> None:
    """The record's copy and the completing event's resolution are one: a
    copy that disagrees, or a resolution its participant events do not
    reproduce, is an integrity failure at delivery and nothing changes."""
    index = s1(monkeypatch)
    _faces(monkeypatch, 15)
    story, ape = _contest_story(stack, index)
    stack.roll(_announce(stack, gm, story, _contest(story, ape)), 12)
    (completing,) = stack.rows(
        "SELECT event_id, payload_json, mechanical_provenance"
        " FROM action_resolution_events WHERE story_id = :s AND kind = 'ai_roll'",
        s=str(story.story_id),
    )
    payload = json.loads(completing.payload_json)
    provenance = json.loads(completing.mechanical_provenance)
    if target == "record":
        (entry,) = provenance["records"]
        entry["record"]["contest_resolution"]["participants"][0]["step_id"] = str(
            ape  # any other identity
        )
    else:
        payload["contest_resolution"]["participants"][1]["total"] = 25
    with stack.factory() as s:  # a corrupted store: the ledger is append-only
        s.execute(sa.text("DROP TRIGGER prevent_action_resolution_events_update"))
        s.execute(
            sa.text(
                "UPDATE action_resolution_events SET payload_json = :p,"
                " mechanical_provenance = :m WHERE event_id = :e"
            ),
            {
                "p": json.dumps(payload),
                "m": json.dumps(provenance),
                "e": completing.event_id,
            },
        )
        s.commit()
    before = (_state(stack, story), stack.turns())
    result = stack.resume(story)
    assert result.disposition is PipelineDisposition.PIPELINE_ERROR
    assert result.action_sequence_error == "ACTION_SEQUENCE_STATE_CONFLICT"
    assert "contest" in (result.pipeline_error_summary or "")
    assert (_state(stack, story), stack.turns()) == before
    assert stack.audit(story) == []


def test_a_hidden_counterpart_is_a_hidden_roll_and_stays_out_of_the_views(
    stack: Stack, gm: GM, monkeypatch: pytest.MonkeyPatch
) -> None:
    index = s1(monkeypatch)
    _faces(monkeypatch, 15)
    story, ape = _contest_story(stack, index)
    pending = _announce(stack, gm, story, _contest(story, ape, hidden=True))
    ready = stack.roll(pending, 12)
    assert ready.interaction_phase is RpgInteractionPhase.READY_FOR_NARRATION
    assert [p["kind"] for p in _payloads(stack, story)] == [
        "player_roll",
        "hidden_roll",
    ]
    bundle = stack.sequences.get_ready_bundle(
        story.story_id, UUID(stack.sequence(story)["sequence_id"]), story.node_id
    )
    (view,) = bundle.writer_views
    assert view.total == 11 and "lost" in view.player_facing_summary
    assert "20" not in view.model_dump_json()  # the Ape's hidden total
    result = stack.resume(story)
    assert result.disposition is PipelineDisposition.DELIVERED, result
    assert [a.source for a in stack.audit(story)] == ["player", "hidden"]


def test_an_unperceived_counterpart_reads_as_the_players_ordinary_check(
    stack: Stack, gm: GM, monkeypatch: pytest.MonkeyPatch
) -> None:
    index = s1(monkeypatch)
    _faces(monkeypatch, 15)
    story, ape = _contest_story(stack, index)
    pending = _announce(
        stack, gm, story, _contest(story, ape, hidden=True, perceived=False)
    )
    assert pending.purpose.value == "skill_check"
    assert pending.display_label.endswith("check")
    assert "ape" not in pending.model_dump_json().lower()
    stack.roll(pending, 12)
    bundle = stack.sequences.get_ready_bundle(
        story.story_id, UUID(stack.sequence(story)["sequence_id"]), story.node_id
    )
    (view,) = bundle.writer_views
    assert view.check_label == "Strength (Athletics) check"
    assert view.outcome == "failure"
