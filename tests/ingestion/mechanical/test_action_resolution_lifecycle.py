"""CRD Issue 15b Phase 2: action-resolution lifecycle proofs on the backend
(``sequence_stack``: an isolated store, the existing backend services, a
test-owned ``ActionResolutionService``; no ``create_app`` or HTTP route).

Contests run with the S1 supplement applied in memory only (``s1``).
"""

from __future__ import annotations

import dataclasses
import json
from typing import Any
from uuid import UUID, uuid4

import pytest
import sqlalchemy as sa
from pydantic import ValidationError

from afterworlds.entitlement.enums import RuntimeAccessPath
from afterworlds.models.dnd5e_state import DeathState, ZeroHitPointTreatment
from afterworlds.models.enums import DiceHandling, RpgInteractionPhase
from afterworlds.models.rpg import (
    MechanicalDecisionSubmission,
    PhysicalAggregateRollSubmission,
    PlayerRollTermResult,
    RawPlayerRollSubmission,
)
from afterworlds.pipeline.orchestrator.models import PipelineDisposition
from afterworlds.pipeline.rpg import sequence as sequence_module
from afterworlds.pipeline.rpg.models import (
    ActionAdjustmentNotAllowedError,
    ActionSequenceStateConflictError,
    MechanicalDecisionInvalidError,
    MechanicalDecisionRevisionMismatchError,
    PendingRollAlreadyConsumedError,
    PendingRollInvalidAggregateError,
    PendingRollInvalidValueError,
    PendingRollRevisionMismatchError,
    PendingRollTermMismatchError,
)
from afterworlds.pipeline.rpg.sequence import ActionResolutionService
from afterworlds.services.dnd5e_state import service as state_service
from afterworlds.services.dnd5e_state.authority import AuthorityIndex
from tests.ingestion.mechanical.sequence_stack import (
    NOW,
    Stack,
    Story_,
    no_backend_dice,
    s1,
    scripted_dice,
    stack,
)
from tests.ingestion.mechanical.test_action_resolution_on_published_release import (
    _keys,
    begin,
    club_attack,
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


def _reconstructed(stack: Stack, story: Story_, kind: str) -> Any:
    """The story's one event of *kind*, rebuilt from its own row only."""
    (row,) = stack.rows(
        "SELECT * FROM action_resolution_events WHERE story_id = :s AND kind = :k",
        s=str(story.story_id),
        k=kind,
    )
    return sequence_module._event_from(row)  # noqa: SLF001


def _corrupt_working_state(stack: Stack, story: Story_) -> None:
    """Blank the sequence row's mutable working copies (no authority)."""
    with stack.factory() as s:
        s.execute(
            sa.text(
                "UPDATE action_resolution_sequences SET plan_json = '{}',"
                " reads_json = '{}', records_json = '[]',"
                " resolved_steps_json = '[]', projected_state_json = '{}',"
                " provisional_effects_json = '[]',"
                " current_decision_snapshot_json = NULL WHERE story_id = :s"
            ),
            {"s": str(story.story_id)},
        )
        s.commit()


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
    """A failure writing the counterpart's event, after the Sojourner's
    event was written and the counterpart die drawn, rolls the whole write
    back: no event, the pending roll still pending, the revision unmoved. The
    discarded die never becomes authority: the retry draws its own."""
    index = s1(monkeypatch)
    rolled = _faces(monkeypatch, 15, 2)
    story, ape = _contest_story(stack, index)
    pending = _announce(stack, gm, story, _contest(story, ape))
    before = _state(stack, story)

    real_append = sequence_module._append  # noqa: SLF001
    written: list[str] = []

    def failing(session: Any, row: Any, kind: Any, *args: Any) -> Any:
        if len(written) == 1:  # the counterpart's event, the second written
            written.append("failed")
            raise RuntimeError("injected event write failure")
        written.append(kind.value)
        return real_append(session, row, kind, *args)

    monkeypatch.setattr(sequence_module, "_append", failing)
    with pytest.raises(RuntimeError, match="injected"):
        stack.roll(pending, 12)
    assert written == ["player_roll", "failed"]
    assert rolled == ["1d20"]  # drawn inside the failed write
    assert _state(stack, story) == before
    monkeypatch.setattr(sequence_module, "_append", real_append)

    stack.roll(pending, 12)
    assert rolled == ["1d20", "1d20"]
    mine, theirs = _payloads(stack, story)
    assert theirs["total"] == 7  # the retry's 2 + 5, not the discarded 15 + 5
    assert theirs["contest_resolution"]["winner"]["subject_id"] == str(story.sheet_id)


def test_state_moved_after_preparation_refuses_before_any_die(
    stack: Stack, gm: GM, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The Ape's state changes between the dice-free preparation and the
    accepting write (an ordinary state-service update). The recheck after the
    claim refuses: no counterpart die, no event, nothing consumed."""
    index = s1(monkeypatch)
    rolled = _faces(monkeypatch, 15)
    story, ape = _contest_story(stack, index)
    pending = _announce(stack, gm, story, _contest(story, ape))
    before = _state(stack, story)
    real_read = ActionResolutionService._read  # noqa: SLF001

    def moving(self: ActionResolutionService, *args: Any) -> Any:
        prepared = real_read(self, *args)
        _hurt(stack, ape)
        return prepared

    monkeypatch.setattr(ActionResolutionService, "_read", moving)
    with pytest.raises(ActionSequenceStateConflictError, match="changed"):
        stack.roll(pending, 12)
    assert rolled == []
    assert _state(stack, story) == before


def _hurt(stack: Stack, creature: UUID) -> None:
    """One point of damage through the state service: a new revision."""
    with stack.factory() as s:
        stored = state_service.read_creature(s, creature)
        hp = stored.state.hit_points
        state_service.update_creature(
            s,
            creature,
            stored.state.model_copy(
                update={"hit_points": hp.model_copy(update={"current": hp.current - 1})}
            ),
            expected_revision=stored.revision,
            now=NOW,
        )
        s.commit()


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


# ---------------------------------------------------------------------------
# Finesse: a pre-roll ability adjustment (15b-9 to 15b-13)
# ---------------------------------------------------------------------------


def _dagger_attack(stack: Stack, story: Story_, target: UUID) -> dict[str, Any]:
    attack = club_attack(stack, story, target)
    dagger = stack.item(story, "equipment.weapons.dagger", equipped=True)
    attack["check_label"] = "Dagger attack"
    attack["weapon_attack"] |= {
        "weapon_item_id": str(dagger),
        "hands": {"held": [{"item_id": str(dagger), "hands": 1}], "free_hands": 1},
        "ability": "strength",
    }
    return attack


def test_a_finesse_adjustment_revises_the_pending_attack_and_its_damage(
    stack: Stack, gm: GM, monkeypatch: pytest.MonkeyPatch
) -> None:
    rolled = no_backend_dice(monkeypatch)
    story = stack.story(DiceHandling.PLAYER_ROLLS)
    wolf = stack.creature(story)
    gm.append([begin(story), _dagger_attack(stack, story, wolf)])
    stack.turn(story, "I stab the wolf.")
    view = stack.sequences.current(story.story_id)
    assert view is not None and view.pending_roll is not None
    attack = view.pending_roll
    assert attack.display_expression == "1d20 + 1"  # Str -1, proficiency +2
    (option,) = attack.adjustment_options
    assert option.option_id == "finesse_dexterity"
    assert "ability_id" not in _keys(attack.model_dump(mode="json"))
    before = _state(stack, story)

    # Refused, changing nothing: a stale or inexact revision, an option not
    # offered.
    for revision in (attack.instruction_revision + 1, True, 1.0):
        with pytest.raises(PendingRollRevisionMismatchError):
            stack.sequences.apply_adjustment(
                attack.pending_roll_request_id,
                revision,  # type: ignore[arg-type]
                "finesse_dexterity",
            )
    with pytest.raises(ActionAdjustmentNotAllowedError):
        stack.sequences.apply_adjustment(
            attack.pending_roll_request_id,
            attack.instruction_revision,
            "finesse_strength",  # the ability it already uses
        )
    assert _state(stack, story) == before

    revised_view = stack.sequences.apply_adjustment(
        attack.pending_roll_request_id,
        attack.instruction_revision,
        "finesse_dexterity",
    )
    revised = revised_view.pending_roll
    assert revised is not None
    assert revised.interaction_phase is RpgInteractionPhase.PENDING_ROLL
    assert revised.instruction_id == attack.instruction_id
    assert revised.instruction_revision == attack.instruction_revision + 1
    assert revised.display_expression == "1d20 + 4"  # Dex +2, proficiency +2
    assert [o.option_id for o in revised.adjustment_options] == ["finesse_strength"]
    assert stack.sequences.current(story.story_id) == revised_view  # reload
    assert [e.kind for e in stack.events(story)] == ["adjustment"]
    (pending_row,) = stack.rows(
        "SELECT instruction_snapshot_json FROM pending_roll_requests"
        " WHERE request_id = :r",
        r=str(attack.pending_roll_request_id),
    )
    adjusted = _reconstructed(stack, story, "adjustment")
    resulting = adjusted.payload.resulting_instruction_snapshot
    assert resulting.model_dump_json() == pending_row.instruction_snapshot_json
    assert (resulting.instruction_id, resulting.instruction_revision) == (
        revised.instruction_id,
        revised.instruction_revision,
    )
    assert adjusted.payload.accepted_adjustment_option_id == "finesse_dexterity"
    assert type(adjusted.payload.accepted_adjustment_option_id) is str
    with pytest.raises(PendingRollRevisionMismatchError):
        stack.roll(attack, 15)  # the superseded instruction

    damage = stack.roll(revised, 15).pending_roll  # 15 + 4 = 19 hits AC 12
    assert damage is not None and damage.display_expression == "1d4 + 2"  # Dex
    ready = stack.roll(damage, 3)
    assert ready.interaction_phase is RpgInteractionPhase.READY_FOR_NARRATION
    result = stack.resume(story)
    assert result.disposition is PipelineDisposition.DELIVERED, result
    assert rolled == []
    assert stack.hp(wolf) == (2, 6)
    # The adjustment is an event, never an audit row.
    assert [(a.check_label, a.total) for a in stack.audit(story)] == [
        ("Dagger attack", 19),
        ("Dagger damage", 5),
    ]
    assert [e.kind for e in stack.events(story)] == [
        "adjustment",
        "player_roll",
        "player_roll",
    ]
    _corrupt_working_state(stack, story)
    assert _reconstructed(stack, story, "adjustment") == adjusted


# ---------------------------------------------------------------------------
# Knocking out: a result-triggered mechanical decision (15b-35)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("choice", ["knock_out", "no_knock_out"])
def test_a_knockout_choice_is_a_stored_decision_of_the_sojourner(
    stack: Stack, gm: GM, monkeypatch: pytest.MonkeyPatch, choice: str
) -> None:
    no_backend_dice(monkeypatch)
    story = stack.story(DiceHandling.PLAYER_ROLLS)
    wolf = stack.creature(story, hp=2)
    gm.append([begin(story), club_attack(stack, story, wolf)])
    stack.turn(story, "I club the wolf.")
    view = stack.sequences.current(story.story_id)
    assert view is not None and view.pending_roll is not None
    damage = stack.roll(view.pending_roll, 15).pending_roll
    assert damage is not None
    paused = stack.roll(damage, 4)  # 3 damage would drop the wolf's 2 HP
    decision = paused.pending_decision
    assert decision is not None
    assert paused.interaction_phase is RpgInteractionPhase.PENDING_MECHANICAL_DECISION
    assert [o.option_id for o in decision.options] == ["knock_out", "no_knock_out"]
    public = _keys(decision.model_dump(mode="json"))
    assert not {"source_rule_ref", "provisional_effects_json"} & public
    assert stack.sequences.current(story.story_id) == paused  # reload
    stored = json.loads(stack.sequence(story)["current_decision_snapshot_json"])
    assert stored["decision_id"] == str(decision.decision_request_id)
    assert stored["decision_revision"] == decision.decision_revision
    before = _state(stack, story)

    def submit(option: str, revision: int | None = None) -> Any:
        return stack.sequences.submit_decision(
            MechanicalDecisionSubmission(
                decision_request_id=decision.decision_request_id,
                expected_decision_revision=(
                    decision.decision_revision if revision is None else revision
                ),
                option_id=option,
            )
        )

    with pytest.raises(MechanicalDecisionInvalidError):
        submit("knock_out_twice")
    with pytest.raises(MechanicalDecisionRevisionMismatchError):
        submit(choice, decision.decision_revision + 1)
    assert (
        stack.rows(
            "SELECT 1 FROM action_resolution_events WHERE kind ="
            " 'mechanical_decision'"
        )
        == []
    )
    with pytest.raises(ValidationError):  # an inexact revision never arrives
        MechanicalDecisionSubmission.model_validate_json(
            json.dumps(
                {
                    "decision_request_id": str(decision.decision_request_id),
                    "expected_decision_revision": True,
                    "option_id": choice,
                }
            )
        )
    assert _state(stack, story) == before

    ready = submit(choice)
    assert ready.interaction_phase is RpgInteractionPhase.READY_FOR_NARRATION
    with pytest.raises(MechanicalDecisionInvalidError):
        submit(choice)  # a duplicate: the decision is no longer pending
    reconstructed = _reconstructed(stack, story, "mechanical_decision")
    payload = reconstructed.payload
    assert payload.decision_snapshot.model_dump(mode="json") == stored
    assert payload.decision_snapshot.decision_id == decision.decision_request_id
    assert payload.decision_snapshot.decision_revision == decision.decision_revision
    assert payload.accepted_decision_option_id == choice
    assert type(payload.accepted_decision_option_id) is str
    assert reconstructed.step_id == payload.decision_snapshot.step_id
    assert [e.kind for e in stack.events(story)] == [
        "player_roll",
        "player_roll",
        "mechanical_decision",
    ]
    result = stack.resume(story)
    assert result.disposition is PipelineDisposition.DELIVERED, result
    (row,) = stack.rows(
        "SELECT document FROM dnd5e_creatures WHERE creature_id = :c", c=str(wolf)
    )
    document = (
        row.document if isinstance(row.document, dict) else json.loads(row.document)
    )
    conditions = {c["condition"] for c in document["conditions"]}
    if choice == "knock_out":
        assert document["hit_points"]["current"] == 1 and "unconscious" in conditions
    else:
        assert document["hit_points"]["current"] == 0
    assert len(stack.audit(story)) == 2  # a decision is never an audit row
    # Reconstruction reads the event row alone: the completed sequence, its
    # working copies and the moved live wolf change nothing.
    _corrupt_working_state(stack, story)
    assert _reconstructed(stack, story, "mechanical_decision") == reconstructed


def test_a_stored_decision_is_validated_by_snapshot_then_state_guarded(
    stack: Stack, gm: GM, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Membership is judged by the stored snapshot alone: an option it does
    not list refuses as invalid whatever live state says. A listed option is
    then a continuation of the sequence, guarded by live state: the wolf's
    state moved since the decision was offered, so it refuses as a state
    conflict, with no event and the decision still pending as stored."""
    no_backend_dice(monkeypatch)
    story = stack.story(DiceHandling.PLAYER_ROLLS)
    wolf = stack.creature(story, hp=2)
    gm.append([begin(story), club_attack(stack, story, wolf)])
    stack.turn(story, "I club the wolf.")
    view = stack.sequences.current(story.story_id)
    assert view is not None and view.pending_roll is not None
    damage = stack.roll(view.pending_roll, 15).pending_roll
    assert damage is not None
    paused = stack.roll(damage, 4)
    decision = paused.pending_decision
    assert decision is not None
    _hurt(stack, wolf)  # 2 -> 1 HP, a new revision
    before = _state(stack, story)

    def submit(option: str) -> Any:
        return stack.sequences.submit_decision(
            MechanicalDecisionSubmission(
                decision_request_id=decision.decision_request_id,
                expected_decision_revision=decision.decision_revision,
                option_id=option,
            )
        )

    with pytest.raises(MechanicalDecisionInvalidError):
        submit("surrender")
    with pytest.raises(ActionSequenceStateConflictError, match="changed"):
        submit("knock_out")
    assert _state(stack, story) == before
    assert stack.sequences.current(story.story_id) == paused
    assert [e.kind for e in stack.events(story)] == ["player_roll", "player_roll"]


def test_an_ai_rolled_hit_starts_a_decision_first_sequence(
    stack: Stack, gm: GM, monkeypatch: pytest.MonkeyPatch
) -> None:
    """With the GameMaster rolling, the announce turn draws both dice and
    pauses for the knockout decision alone: no pending roll exists, and the
    announce turn is still a procedural request, never retrieval memory."""
    from afterworlds.models.enums import RpgTurnRetrievalCategory
    from afterworlds.persistence.crud.retrieval import (
        get_rpg_turn_retrieval_marker,
        has_pending_roll_request_originating_from_turn,
    )

    faces = iter([15, 4])
    rolled = scripted_dice(monkeypatch, lambda _e: (next(faces),))
    story = stack.story(DiceHandling.AI_ROLLS)
    wolf = stack.creature(story, hp=2)
    gm.append([begin(story), club_attack(stack, story, wolf)])
    announce = stack.turn(story, "I club the wolf.")
    assert announce.disposition is PipelineDisposition.DELIVERED, announce
    assert announce.turn_id is not None
    assert rolled == ["1d20", "1d4"]
    view = stack.sequences.current(story.story_id)
    assert view is not None and view.pending_decision is not None
    assert stack.rows("SELECT 1 FROM pending_roll_requests") == []
    assert [e.kind for e in stack.events(story)] == ["ai_roll", "ai_roll"]
    with stack.factory() as s:
        assert has_pending_roll_request_originating_from_turn(s, announce.turn_id)
        marker = get_rpg_turn_retrieval_marker(s, announce.turn_id)
    assert marker is RpgTurnRetrievalCategory.ROLL_REQUEST

    stack.sequences.submit_decision(
        MechanicalDecisionSubmission(
            decision_request_id=view.pending_decision.decision_request_id,
            expected_decision_revision=view.pending_decision.decision_revision,
            option_id="knock_out",
        )
    )
    result = stack.resume(story)
    assert result.disposition is PipelineDisposition.DELIVERED, result
    assert [(a.source, a.submission_source) for a in stack.audit(story)] == [
        ("ai", "backend_dice_service"),
        ("ai", "backend_dice_service"),
    ]
    assert rolled == ["1d20", "1d4"]  # nothing redrawn on replay or delivery
    assert stack.hp(wolf)[1] == 1


# ---------------------------------------------------------------------------
# Player submissions: physical aggregates and malformed input
# ---------------------------------------------------------------------------


def test_malformed_submissions_change_nothing_and_an_aggregate_is_accepted(
    stack: Stack, gm: GM, monkeypatch: pytest.MonkeyPatch
) -> None:
    no_backend_dice(monkeypatch)
    story = stack.story(DiceHandling.PLAYER_ROLLS)
    wolf = stack.creature(story)
    gm.append([begin(story), club_attack(stack, story, wolf)])
    stack.turn(story, "I swing my club.")
    view = stack.sequences.current(story.story_id)
    assert view is not None and view.pending_roll is not None
    attack = view.pending_roll
    (term,) = attack.terms
    before = _state(stack, story)

    def raw(term_id: UUID, *values: int) -> RawPlayerRollSubmission:
        return RawPlayerRollSubmission(
            source="inline_ui",
            pending_roll_request_id=attack.pending_roll_request_id,
            expected_instruction_revision=attack.instruction_revision,
            term_results=(PlayerRollTermResult(term_id=term_id, values=values),),
        )

    def aggregate(total: int) -> PhysicalAggregateRollSubmission:
        return PhysicalAggregateRollSubmission(
            source="physical_self_report",
            pending_roll_request_id=attack.pending_roll_request_id,
            expected_instruction_revision=attack.instruction_revision,
            reported_aggregate=total,
        )

    bad: list[tuple[Any, type[Exception]]] = [
        (raw(term.term_id, 21), PendingRollInvalidValueError),  # no such face
        (raw(term.term_id, 0), PendingRollInvalidValueError),
        (raw(term.term_id, 5, 5), PendingRollInvalidValueError),  # two faces
        (raw(uuid4(), 5), PendingRollTermMismatchError),  # another term
        (aggregate(22), PendingRollInvalidAggregateError),  # above 1d20 + 1
        (aggregate(1), PendingRollInvalidAggregateError),
    ]
    for submission, error in bad:
        with pytest.raises(error):
            stack.sequences.consume_roll(submission)
    for payload in (  # inexact integers never reach the service
        {"term_id": str(term.term_id), "values": [5.0]},
        {"term_id": str(term.term_id), "values": ["5"]},
        {"term_id": str(term.term_id), "values": [True]},
    ):
        with pytest.raises(ValidationError):
            PlayerRollTermResult.model_validate_json(json.dumps(payload))
    assert _state(stack, story) == before

    damage = stack.sequences.consume_roll(aggregate(16)).pending_roll  # hits AC 12
    assert damage is not None
    stack.roll(damage, 4)
    result = stack.resume(story)
    assert result.disposition is PipelineDisposition.DELIVERED, result
    first, _ = stack.audit(story)
    assert (first.total, first.submission_source, first.raw_values_complete) == (
        16,
        "physical_self_report",
        False,
    )


# ---------------------------------------------------------------------------
# Duration: a bounded mechanic's interval die in the sequence
# ---------------------------------------------------------------------------


def test_stabilizing_draws_the_recovery_interval_in_the_accepting_write(
    stack: Stack, gm: GM, monkeypatch: pytest.MonkeyPatch
) -> None:
    """First aid on a dying wolf (treated like a character): the Sojourner's
    Medicine check is accepted, and the stable creature's recovery interval
    (a DURATION die, the wolf's own) is drawn by the backend in the same
    write. The delivered effect holds that interval."""
    rolled = _faces(monkeypatch, 3)
    story = stack.story(DiceHandling.PLAYER_ROLLS)
    wolf = stack.creature(story, treatment=ZeroHitPointTreatment(subject="character"))
    _dying(stack, wolf)
    gm.append(
        [
            begin(story),
            {
                "check_label": "First aid",
                "subsystem_tag": "lifecycle",
                "visibility": "shown",
                "operation": "stabilize",
                "subject": {"kind": "creature", "subject_id": str(wolf)},
            },
        ]
    )
    stack.turn(story, "I bind the wolf's wounds.")
    view = stack.sequences.current(story.story_id)
    assert view is not None and view.pending_roll is not None
    assert rolled == []
    ready = stack.roll(view.pending_roll, 15)  # Medicine against DC 10
    assert ready.interaction_phase is RpgInteractionPhase.READY_FOR_NARRATION
    assert rolled == ["1d4"]
    check, interval = _payloads(stack, story)
    assert (check["kind"], interval["kind"]) == ("player_roll", "ai_roll")
    assert interval["instruction_snapshot"]["purpose"] == "duration"
    assert interval["total"] == 3
    result = stack.resume(story)
    assert result.disposition is PipelineDisposition.DELIVERED, result
    (row,) = stack.rows(
        "SELECT document FROM dnd5e_creatures WHERE creature_id = :c", c=str(wolf)
    )
    document = (
        row.document if isinstance(row.document, dict) else json.loads(row.document)
    )
    recovery = document["death_state"]["stable_recovery"]
    assert document["death_state"]["stable"] and recovery["interval"] == 3
    assert [a.check_label for a in stack.audit(story)] == [
        view.pending_roll.display_label,
        "Recovery interval",
    ]


def _dying(stack: Stack, creature: UUID) -> None:
    from afterworlds.models.dnd5e_state import ConditionInstance, GrantSource
    from afterworlds.models.enums import ConditionVisibility

    with stack.factory() as s:
        stored = state_service.read_creature(s, creature)
        state_service.update_creature(
            s,
            creature,
            stored.state.model_copy(
                update={
                    "hit_points": stored.state.hit_points.model_copy(
                        update={"current": 0}
                    ),
                    "death_state": DeathState(
                        successes=0, failures=0, stable=False, dead=False
                    ),
                    "conditions": (
                        ConditionInstance(
                            instance_id="fell",
                            condition="unconscious",  # type: ignore[arg-type]
                            visibility=ConditionVisibility.VISIBLE,
                            source=GrantSource(
                                record_key="play.damage_and_healing",
                                component_key="falling_unconscious",
                            ),
                        ),
                    ),
                }
            ),
            expected_revision=stored.revision,
            now=NOW,
        )
        s.commit()


# ---------------------------------------------------------------------------
# Intermediate operations: gated turns, no provider, access or settlement
# ---------------------------------------------------------------------------


def _counts(stack: Stack) -> dict[str, int]:
    """Every table's row count (settlement, usage, Turns, effects ...)."""
    tables = [
        r.name
        for r in stack.rows(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
            " AND name NOT LIKE 'sqlite_%'"
        )
    ]
    return {t: stack.rows(f'SELECT COUNT(*) AS n FROM "{t}"')[0].n for t in tables}


def test_intermediate_operations_touch_only_the_sequence_and_gate_turns(
    stack: Stack, gm: GM, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Each pending phase blocks an ordinary in-character turn before any
    provider call; and accepting a roll or a decision calls no provider and
    writes nothing but the sequence's own tables: no Turn, effect, audit,
    usage or settlement row."""
    from tests.ingestion.mechanical.test_bounded_d20_on_published_release import (
        REQUESTS,
    )

    no_backend_dice(monkeypatch)
    story = stack.story(DiceHandling.PLAYER_ROLLS)
    wolf = stack.creature(story, hp=2)
    gm.append([begin(story), club_attack(stack, story, wolf)])
    stack.turn(story, "I club the wolf.")
    sequence_tables = {"action_resolution_events", "pending_roll_requests"}

    def gated() -> None:
        calls = len(REQUESTS)
        blocked = stack.turn(story, "I keep swinging.")
        assert blocked.disposition is PipelineDisposition.BLOCKED_PENDING_ROLL
        assert blocked.pending_roll_redirect_message
        assert blocked.turn_id is None
        # Only the intent is classified (it decides whether the gate
        # applies): no Planner, adjudication or Writer call.
        assert {r.pass_id.value for r in REQUESTS[calls:]} == {"intent_classifier"}

    def quiet(operation: Any) -> Any:
        calls, before = len(REQUESTS), _counts(stack)
        result = operation()
        after = _counts(stack)
        assert len(REQUESTS) == calls
        changed = {t for t in before if before[t] != after[t]}
        assert changed <= sequence_tables, changed
        return result

    view = stack.sequences.current(story.story_id)
    assert view is not None and view.pending_roll is not None
    gated()
    damage = quiet(lambda: stack.roll(view.pending_roll, 15)).pending_roll
    gated()
    paused = quiet(lambda: stack.roll(damage, 4))
    assert paused.pending_decision is not None
    gated()
    ready = quiet(
        lambda: stack.sequences.submit_decision(
            MechanicalDecisionSubmission(
                decision_request_id=paused.pending_decision.decision_request_id,
                expected_decision_revision=paused.pending_decision.decision_revision,
                option_id="knock_out",
            )
        )
    )
    assert ready.interaction_phase is RpgInteractionPhase.READY_FOR_NARRATION
    gated()
    assert stack.hp(wolf) == (1, 2)  # projected only until narration
    assert stack.resume(story).disposition is PipelineDisposition.DELIVERED
    unblocked = stack.turn(story, "I look around.")
    assert unblocked.disposition is PipelineDisposition.DELIVERED, unblocked


# ---------------------------------------------------------------------------
# Final narration: typed refusals, failures and identical-facts retry
# ---------------------------------------------------------------------------


def _ready_attack(stack: Stack, gm: GM) -> tuple[Story_, UUID]:
    story = stack.story(DiceHandling.PLAYER_ROLLS)
    wolf = stack.creature(story)
    gm.append([begin(story), club_attack(stack, story, wolf)])
    stack.turn(story, "I swing my club.")
    view = stack.sequences.current(story.story_id)
    assert view is not None and view.pending_roll is not None
    damage = stack.roll(view.pending_roll, 15).pending_roll
    assert damage is not None
    stack.roll(damage, 4)
    return story, wolf


def _delivery_facts(stack: Stack, story: Story_) -> list[tuple[Any, ...]]:
    return [
        (
            a.check_label,
            a.total,
            a.dc,
            a.outcome,
            a.raw_rolls_json,
            a.step_id,
            a.instruction_snapshot_json,
            a.sheet_effects_json,
        )
        for a in stack.audit(story)
    ]


def test_resume_refuses_typed_before_any_provider_call(
    stack: Stack, gm: GM, monkeypatch: pytest.MonkeyPatch
) -> None:
    from tests.ingestion.mechanical.test_bounded_d20_on_published_release import (
        REQUESTS,
    )

    no_backend_dice(monkeypatch)
    story = stack.story(DiceHandling.PLAYER_ROLLS)
    wolf = stack.creature(story)
    gm.append([begin(story), club_attack(stack, story, wolf)])
    stack.turn(story, "I swing my club.")
    sequence_id = UUID(stack.sequence(story)["sequence_id"])
    calls, turns = len(REQUESTS), stack.turns()

    def resume(sequence: UUID, node: UUID) -> Any:
        return stack.orchestrator.orchestrate_rpg_resume(
            story.story_id,
            node,
            sequence,
            access_path=RuntimeAccessPath.HOSTED,
            sojourner_id=stack.sojourner_id,
        )

    for sequence, node, code in (
        (sequence_id, story.node_id, "SEQUENCE_NOT_READY_FOR_NARRATION"),
        (uuid4(), story.node_id, "ACTION_SEQUENCE_NOT_FOUND"),
    ):
        result = resume(sequence, node)
        assert result.disposition is PipelineDisposition.PIPELINE_ERROR
        assert result.action_sequence_error == code
    view = stack.sequences.current(story.story_id)
    assert view is not None and view.pending_roll is not None
    damage = stack.roll(view.pending_roll, 15).pending_roll
    assert damage is not None
    stack.roll(damage, 4)
    other = stack.story(DiceHandling.PLAYER_ROLLS)  # another story's node
    result = resume(sequence_id, other.node_id)
    assert result.action_sequence_error == "ACTION_SEQUENCE_STATE_CONFLICT"
    assert len(REQUESTS) == calls and stack.turns() == turns
    assert stack.sequence(story)["status"] == "ready_for_narration"


@pytest.mark.parametrize("failure", ["writer_error", "writer_refusal", "output_block"])
def test_a_failed_narration_keeps_the_ledger_and_the_retry_delivers_it(
    stack: Stack, gm: GM, monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    """The narration fails (a Writer error, a provider refusal, or an output
    audit block): the ready sequence, its events, the creature and every
    audit table stay as they were (a refusal's own log row excepted, written
    after the rollback). The retry delivers exactly the ledger's facts, once.

    The turn binding is the production shape around the fake adapter: the
    refusal router with the buffering refusal log proxy and its
    pre/post-transaction hooks (the fake resolver binds the bare adapter)."""
    from afterworlds.api.fake_pipeline import FakeProviderResolver
    from afterworlds.pipeline.provider._resolver import RefusalLogProxy
    from afterworlds.pipeline.provider.adapters._fallback import (
        RefusalFallbackRouter,
    )

    real_resolve = FakeProviderResolver.resolve_for_turn
    flushed: list[int] = []

    def resolve(self: Any, access_path: Any, sojourner_id: Any) -> Any:
        binding = real_resolve(self, access_path, sojourner_id)
        proxy = RefusalLogProxy(stack.factory)

        def flush() -> None:
            flushed.append(len(proxy._buffer or []))  # noqa: SLF001
            proxy.flush()

        return dataclasses.replace(
            binding,
            adapter=RefusalFallbackRouter(binding.adapter, None, proxy),
            pre_transaction_fn=proxy.start_buffering,
            post_transaction_fn=flush,
        )

    monkeypatch.setattr(FakeProviderResolver, "resolve_for_turn", resolve)
    from afterworlds.api.fake_pipeline import FakeProviderAdapter
    from afterworlds.pipeline._refusal import PassIdentifier
    from afterworlds.pipeline.safety.models import (
        SafetyCategory,
        SafetyConcern,
        SafetyReport,
        SafetyResult,
        SafetyTarget,
    )
    from tests.pipeline.orchestrator.conftest import make_refusal

    no_backend_dice(monkeypatch)
    story, wolf = _ready_attack(stack, gm)
    events = stack.events(story)
    before = (_state(stack, story), stack.hp(wolf), stack.turns(), stack.audit(story))
    refusals = len(stack.rows("SELECT 1 FROM provider_refusal_log"))
    real_call = FakeProviderAdapter.call
    once = [failure]

    def call(self: Any, request: Any) -> Any:
        if once and request.pass_id.value == "writer" and failure != "output_block":
            once.pop()
            if failure == "writer_refusal":
                raise make_refusal(PassIdentifier.WRITER)
            raise RuntimeError("injected writer failure")
        return real_call(self, request)

    monkeypatch.setattr(FakeProviderAdapter, "call", call)
    orchestrator = stack.orchestrator
    if failure == "output_block":
        real_check = orchestrator._safety_service.check  # noqa: SLF001

        def check(ctx: Any, text: str, target: Any, **kw: Any) -> Any:
            if once and target is SafetyTarget.OUTPUT:
                once.pop()
                return SafetyResult(
                    report=SafetyReport(
                        concerns=[
                            SafetyConcern(
                                category=SafetyCategory.OTHER,
                                description="injected",
                                evidence_summary="injected",
                            )
                        ]
                    ),
                    target=SafetyTarget.OUTPUT,
                )
            return real_check(ctx, text, target, **kw)

        monkeypatch.setattr(
            orchestrator._safety_service, "check", check
        )  # noqa: SLF001
        monkeypatch.setattr(
            orchestrator._safety_policy,  # noqa: SLF001
            "should_run_output_audit",
            lambda _ctx: True,
        )

    failed = stack.resume(story)
    assert (
        failed.disposition
        is {
            "writer_error": PipelineDisposition.PIPELINE_ERROR,
            "writer_refusal": PipelineDisposition.REFUSED_BY_PROVIDER,
            "output_block": PipelineDisposition.BLOCKED_OUTPUT_SAFETY,
        }[failure]
    ), failed
    assert failed.turn_id is None
    assert (
        _state(stack, story),
        stack.hp(wolf),
        stack.turns(),
        stack.audit(story),
    ) == before
    assert stack.events(story) == events
    logged = len(stack.rows("SELECT 1 FROM provider_refusal_log")) - refusals
    assert logged == (1 if failure == "writer_refusal" else 0)
    # A refusal inside the delivery transaction was buffered, then written
    # after the rollback, so it survives it.
    assert flushed[-1] == (1 if failure == "writer_refusal" else 0)

    retried = stack.resume(story)
    assert retried.disposition is PipelineDisposition.DELIVERED, retried
    assert stack.events(story) == events
    assert stack.hp(wolf) == (2, 8)
    facts = _delivery_facts(stack, story)
    assert [f[:4] for f in facts] == [
        ("Club attack", 16, 12, "success"),
        ("Club damage", 3, None, "undetermined"),
    ]
    again = stack.resume(story)
    assert again.action_sequence_error == "ACTION_SEQUENCE_ALREADY_COMPLETED"
    assert _delivery_facts(stack, story) == facts


def test_the_final_audit_is_projected_from_the_events_alone(
    stack: Stack, gm: GM, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The sequence row's working copies (records, steps, projected state,
    accumulated effects) carry no audit weight: corrupting them changes no
    delivered audit fact or effect."""
    no_backend_dice(monkeypatch)
    story, wolf = _ready_attack(stack, gm)
    with stack.factory() as s:
        s.execute(
            sa.text(
                "UPDATE action_resolution_sequences SET records_json = '[]',"
                " resolved_steps_json = '[]', projected_state_json = '{}',"
                " provisional_effects_json = '[]' WHERE story_id = :s"
            ),
            {"s": str(story.story_id)},
        )
        s.commit()
    result = stack.resume(story)
    assert result.disposition is PipelineDisposition.DELIVERED, result
    assert stack.hp(wolf) == (2, 8)
    payloads = _payloads(stack, story)
    audit = stack.audit(story)
    assert [
        (a.total, a.outcome, json.loads(a.instruction_snapshot_json)["step_id"])
        for a in audit
    ] == [
        (p["total"], p["outcome"], p["instruction_snapshot"]["step_id"])
        for p in payloads
    ]
    assert [a.step_id for a in audit] == [
        e.step_id
        for e in stack.rows(
            "SELECT step_id FROM action_resolution_events WHERE story_id = :s"
            " ORDER BY event_order",
            s=str(story.story_id),
        )
    ]


# ---------------------------------------------------------------------------
# Group 17: an all-backend contest's ledger, completed with its own Turn
# ---------------------------------------------------------------------------


def _ledger(stack: Stack, story: Story_) -> list[Any]:
    return stack.rows(
        "SELECT sequence_id, status, originating_turn_id, revision"
        " FROM action_resolution_sequences WHERE story_id = :s",
        s=str(story.story_id),
    )


def test_an_all_backend_contest_persists_both_participants_with_its_turn(
    stack: Stack, gm: GM, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The GameMaster rolls both checks inside the originating turn's
    adjudication (Group 17 Timing). The delivered Turn still commits, in its
    one transaction: both participants' roll events, the combined resolution
    on the completing one, the sequence completed (no pending interaction,
    no resume), and one audit row per participant from its event alone."""
    from afterworlds.models.enums import RpgTurnRetrievalCategory
    from afterworlds.persistence.crud.retrieval import (
        get_rpg_turn_retrieval_marker,
        has_pending_roll_request_originating_from_turn,
    )

    index = s1(monkeypatch)
    rolled = _faces(monkeypatch, 15, 5)
    story = stack.story(
        DiceHandling.AI_ROLLS,
        character=complete_character(index, "classes.wizard", 3),
        binding=index.binding,
    )
    ape = stack.creature(story, "animals.ape", hp=19, name="Ape", binding=index.binding)
    gm.append([_contest(story, ape)])
    result = stack.turn(story, "I challenge the ape to arm wrestling.")
    assert result.disposition is PipelineDisposition.DELIVERED, result
    assert result.turn_id is not None
    assert rolled == ["1d20", "1d20"]
    (ledger,) = _ledger(stack, story)
    assert (ledger.status, ledger.originating_turn_id) == (
        "completed",
        str(result.turn_id),
    )
    assert stack.sequences.current(story.story_id) is None  # nothing pending
    mine, theirs = _payloads(stack, story)
    assert (mine["kind"], theirs["kind"]) == ("ai_roll", "ai_roll")
    assert (mine["total"], theirs["total"]) == (14, 10)  # 15 - 1; 5 + 5
    assert mine["contest_resolution"] is None
    resolution = theirs["contest_resolution"]
    assert resolution["winner"]["subject_id"] == str(story.sheet_id)
    events = stack.rows(
        "SELECT step_id FROM action_resolution_events WHERE story_id = :s"
        " ORDER BY event_order",
        s=str(story.story_id),
    )
    assert [p["step_id"] for p in resolution["participants"]] == [
        e.step_id for e in events
    ]
    audit = stack.audit(story)
    assert [(a.source, a.total, a.step_id, a.turn_id) for a in audit] == [
        ("ai", 14, events[0].step_id, str(result.turn_id)),
        ("ai", 10, events[1].step_id, str(result.turn_id)),
    ]
    assert [a.contest_resolution_json is not None for a in audit] == [False, True]
    assert json.loads(audit[1].contest_resolution_json) == resolution
    # It narrated an outcome: not a procedural request.
    with stack.factory() as s:
        assert not has_pending_roll_request_originating_from_turn(s, result.turn_id)
        marker = get_rpg_turn_retrieval_marker(s, result.turn_id)
    assert marker is RpgTurnRetrievalCategory.ORDINARY_NARRATIVE


@pytest.mark.parametrize("failure", ["writer_error", "output_block"])
def test_a_failed_all_backend_contest_turn_leaves_no_ledger(
    stack: Stack, gm: GM, monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    """The ledger commits with its Turn or not at all: a failed or blocked
    delivery leaves no sequence, event, audit row or Turn."""
    from afterworlds.api.fake_pipeline import FakeProviderAdapter
    from afterworlds.pipeline.safety.models import (
        SafetyCategory,
        SafetyConcern,
        SafetyReport,
        SafetyResult,
        SafetyTarget,
    )

    index = s1(monkeypatch)
    _faces(monkeypatch, 15, 5)
    story = stack.story(
        DiceHandling.AI_ROLLS,
        character=complete_character(index, "classes.wizard", 3),
        binding=index.binding,
    )
    ape = stack.creature(story, "animals.ape", hp=19, name="Ape", binding=index.binding)
    turns = stack.turns()
    real_call = FakeProviderAdapter.call

    def call(self: Any, request: Any) -> Any:
        if failure == "writer_error" and request.pass_id.value == "writer":
            raise RuntimeError("injected writer failure")
        return real_call(self, request)

    monkeypatch.setattr(FakeProviderAdapter, "call", call)
    if failure == "output_block":
        orchestrator = stack.orchestrator
        real_check = orchestrator._safety_service.check  # noqa: SLF001

        def check(ctx: Any, text: str, target: Any, **kw: Any) -> Any:
            if target is SafetyTarget.OUTPUT:
                return SafetyResult(
                    report=SafetyReport(
                        concerns=[
                            SafetyConcern(
                                category=SafetyCategory.OTHER,
                                description="injected",
                                evidence_summary="injected",
                            )
                        ]
                    ),
                    target=SafetyTarget.OUTPUT,
                )
            return real_check(ctx, text, target, **kw)

        monkeypatch.setattr(
            orchestrator._safety_service, "check", check
        )  # noqa: SLF001
        monkeypatch.setattr(
            orchestrator._safety_policy,  # noqa: SLF001
            "should_run_output_audit",
            lambda _ctx: True,
        )
    gm.append([_contest(story, ape)])
    result = stack.turn(story, "I challenge the ape to arm wrestling.")
    assert (
        result.disposition
        is {
            "writer_error": PipelineDisposition.PIPELINE_ERROR,
            "output_block": PipelineDisposition.BLOCKED_OUTPUT_SAFETY,
        }[failure]
    ), result
    assert result.turn_id is None
    assert _ledger(stack, story) == []
    assert stack.events(story) == [] and stack.audit(story) == []
    assert stack.turns() == turns


# ---------------------------------------------------------------------------
# A linked action whose later step depends on an earlier provisional effect
# ---------------------------------------------------------------------------


def test_a_later_attack_resolves_against_the_earlier_hits_projected_state(
    stack: Stack, gm: GM, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The Club attack (Attack action) and the Dagger's Light extra attack
    (Bonus Action) on a 4-HP wolf, every die the Sojourner's, reloaded at
    each step. The Club's 3 damage is provisional: the live wolf keeps 4 HP.
    The Dagger's 2 damage then resolves against the projected 1 HP, so it
    would drop the wolf to 0 and the knockout decision is offered; against
    the live 4 HP it would not be. One Writer call narrates the whole
    action, after the last step."""
    from tests.ingestion.mechanical.test_bounded_d20_on_published_release import (
        REQUESTS,
    )

    no_backend_dice(monkeypatch)
    story = stack.story(DiceHandling.PLAYER_ROLLS)
    wolf = stack.creature(story, hp=4)
    club_attack_ = club_attack(stack, story, wolf)
    club = club_attack_["weapon_attack"]["weapon_item_id"]
    dagger = str(stack.item(story, "equipment.weapons.dagger", equipped=True))
    hands = {
        "held": [{"item_id": club, "hands": 1}, {"item_id": dagger, "hands": 1}],
        "free_hands": 0,
    }
    club_attack_["weapon_attack"]["hands"] = hands
    light = {
        **club_attack_,
        "check_label": "Dagger attack",
        "weapon_attack": {
            **club_attack_["weapon_attack"],
            "weapon_item_id": dagger,
            "ability": "strength",
            "extra": "light",
        },
    }
    gm.append([begin(story), club_attack_, light])
    stack.turn(story, "I club the wolf, then stab with my off-hand dagger.")
    writes = len([r for r in REQUESTS if r.pass_id.value == "writer"])

    def step(view: Any, face: int) -> Any:
        advanced = stack.roll(view, face)
        assert stack.sequences.current(story.story_id) == advanced  # reload
        return advanced

    view = stack.sequences.current(story.story_id)
    assert view is not None and view.pending_roll is not None
    club_damage = step(view.pending_roll, 15).pending_roll  # 16 hits AC 12
    assert club_damage is not None
    dagger_attack = step(club_damage, 4).pending_roll  # 3 damage: 4 -> 1
    assert dagger_attack is not None
    assert dagger_attack.display_label == "Dagger attack"
    seq = stack.sequence(story)
    projected = json.loads(seq["projected_state_json"])
    assert projected[f"creature:{wolf}"]["hit_points"]["current"] == 1
    assert stack.hp(wolf) == (1, 4)  # the live sheet is unchanged
    dagger_damage = step(dagger_attack, 15).pending_roll
    assert dagger_damage is not None and dagger_damage.display_expression == "1d4 - 1"
    paused = step(dagger_damage, 3)  # 2 damage against the projected 1 HP
    assert paused.pending_decision is not None
    assert stack.hp(wolf) == (1, 4)
    ready = stack.sequences.submit_decision(
        MechanicalDecisionSubmission(
            decision_request_id=paused.pending_decision.decision_request_id,
            expected_decision_revision=paused.pending_decision.decision_revision,
            option_id="knock_out",
        )
    )
    assert ready.interaction_phase is RpgInteractionPhase.READY_FOR_NARRATION
    assert len([r for r in REQUESTS if r.pass_id.value == "writer"]) == writes
    result = stack.resume(story)
    assert result.disposition is PipelineDisposition.DELIVERED, result
    assert len([r for r in REQUESTS if r.pass_id.value == "writer"]) == writes + 1
    assert stack.hp(wolf) == (2, 1)
    assert [(a.check_label, a.total) for a in stack.audit(story)] == [
        ("Club attack", 16),
        ("Club damage", 3),
        ("Dagger attack", 16),
        ("Dagger damage", 2),
    ]
