"""CRD Issue 15b: typed ingress and event-provenance shapes refuse at
construction and on reconstruction from stored JSON (#127 Validation 5,
ADR-015b event model)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from afterworlds.models.enums import (
    DiceSelectionRule,
    RollPurpose,
)
from afterworlds.models.rpg import (
    ActionResolutionEvent,
    ContestLinkage,
    ContestParticipantResult,
    ContestResolution,
    MechanicalDecisionSubmission,
    PhysicalAggregateRollSubmission,
    PlayerRollTermResult,
    RawPlayerRollSubmission,
    RollEventPayload,
    RollInstructionSnapshot,
    RollTerm,
    SubjectRef,
)

SEQUENCE, STEP = uuid4(), uuid4()
ME = SubjectRef(kind="character", subject_id=uuid4())
APE = SubjectRef(kind="creature", subject_id=uuid4())


def _snapshot(**changes: Any) -> RollInstructionSnapshot:
    fields: dict[str, Any] = {
        "instruction_id": uuid4(),
        "instruction_revision": 1,
        "purpose": RollPurpose.ABILITY_CHECK,
        "terms": (
            RollTerm(
                term_id=uuid4(),
                count=1,
                sides=20,
                selection_rule=DiceSelectionRule.SUM_ALL,
            ),
        ),
        "modifier_components": (),
        "display_expression": "1d20",
        "display_label": "Strength check",
        "source_rule_refs": (),
        "sequence_id": SEQUENCE,
        "step_id": STEP,
        "roller": ME,
        "operation_index": 0,
        "die_index": 0,
    }
    return RollInstructionSnapshot(**(fields | changes))


def _payload(**changes: Any) -> dict[str, Any]:
    """A valid inline player roll, as JSON-shaped stored data."""
    values = {
        "kind": "player_roll",
        "instruction_snapshot": json.loads(_snapshot().model_dump_json()),
        "submission_source": "inline_ui",
        "pending_roll_request_id": str(uuid4()),
        "raw_input_json": "[]",
        "aggregate_input_json": None,
        "derived_selections_json": '[{"values": [12]}]',
        "subtotal": 12,
        "total": 12,
        "outcome": "undetermined",
        "gm_cheating_at_roll": False,
    }
    return values | changes


# ---------------------------------------------------------------------------
# Finding 3: exact integers at ingress (and the expected-revision siblings)
# ---------------------------------------------------------------------------

_NOT_INTEGERS = ["5", 5.0, True]


@pytest.mark.parametrize("bad", _NOT_INTEGERS, ids=["str", "float", "bool"])
def test_roll_and_decision_submissions_refuse_non_integers(bad: object) -> None:
    request, term = str(uuid4()), str(uuid4())
    shapes: list[tuple[type[Any], dict[str, Any]]] = [
        (PlayerRollTermResult, {"term_id": term, "values": [bad]}),
        (
            RawPlayerRollSubmission,
            {
                "source": "inline_ui",
                "pending_roll_request_id": request,
                "expected_instruction_revision": bad,
                "term_results": [{"term_id": term, "values": [5]}],
            },
        ),
        (
            PhysicalAggregateRollSubmission,
            {
                "source": "physical_self_report",
                "pending_roll_request_id": request,
                "expected_instruction_revision": 1,
                "reported_aggregate": bad,
            },
        ),
        (
            PhysicalAggregateRollSubmission,
            {
                "source": "physical_self_report",
                "pending_roll_request_id": request,
                "expected_instruction_revision": bad,
                "reported_aggregate": 5,
            },
        ),
        (
            MechanicalDecisionSubmission,
            {
                "decision_request_id": request,
                "expected_decision_revision": bad,
                "option_id": "knock_out",
            },
        ),
    ]
    for model, data in shapes:
        with pytest.raises(ValidationError):
            model.model_validate(data)
        with pytest.raises(ValidationError):
            model.model_validate_json(json.dumps(data))


def test_exact_integers_are_accepted() -> None:
    term = PlayerRollTermResult.model_validate_json(
        json.dumps({"term_id": str(uuid4()), "values": [1, 20]})
    )
    assert term.values == (1, 20)


# ---------------------------------------------------------------------------
# Finding 4: accepted channel/shape combinations only
# ---------------------------------------------------------------------------


def test_a_valid_player_roll_payload_reconstructs() -> None:
    RollEventPayload.model_validate(_payload())


@pytest.mark.parametrize(
    "changes",
    [
        # An aggregate-only report from a channel that knows every die.
        {
            "raw_input_json": None,
            "aggregate_input_json": "12",
            "derived_selections_json": "[]",
            "subtotal": None,
        },
        # An aggregate-only report that still claims a selection or subtotal.
        {
            "submission_source": "physical_self_report",
            "raw_input_json": None,
            "aggregate_input_json": "12",
            "subtotal": 12,
        },
        {
            "submission_source": "physical_self_report",
            "raw_input_json": None,
            "aggregate_input_json": "12",
            "subtotal": None,
        },
        # Raw values with no derived subtotal.
        {"subtotal": None},
        # Both or neither input.
        {"aggregate_input_json": "12"},
        {"raw_input_json": None},
        # A player roll by the backend, a backend roll with a pending request.
        {"submission_source": "backend_dice_service"},
        {"kind": "ai_roll"},
        {"kind": "hidden_roll", "submission_source": "inline_ui"},
        {
            "kind": "ai_roll",
            "submission_source": "backend_dice_service",
            "pending_roll_request_id": str(uuid4()),
        },
        # A determined outcome with no target.
        {"outcome": "success"},
    ],
    ids=[
        "inline-aggregate",
        "aggregate-with-subtotal",
        "aggregate-with-selection",
        "raw-without-subtotal",
        "both-inputs",
        "no-input",
        "player-by-backend",
        "ai-with-player-source",
        "hidden-with-player-source",
        "backend-with-pending",
        "outcome-without-target",
    ],
)
def test_impossible_roll_provenance_refuses(changes: dict[str, Any]) -> None:
    data = _payload(**changes)
    with pytest.raises(ValidationError):
        RollEventPayload.model_validate(data)
    with pytest.raises(ValidationError):
        RollEventPayload.model_validate_json(json.dumps(data))


def test_a_physical_aggregate_only_report_is_the_one_aggregate_shape() -> None:
    RollEventPayload.model_validate(
        _payload(
            submission_source="physical_self_report",
            raw_input_json=None,
            aggregate_input_json="12",
            derived_selections_json="[]",
            subtotal=None,
        )
    )


def _resolution(contest_id: UUID) -> dict[str, Any]:
    return json.loads(
        ContestResolution(
            contest_id=contest_id,
            participants=(
                ContestParticipantResult(subject=ME, step_id=uuid4(), total=12),
                ContestParticipantResult(subject=APE, step_id=STEP, total=9),
            ),
            result="win",
            winner=ME,
            certificate={},
        ).model_dump_json()
    )


def test_only_a_roll_of_that_contest_carries_its_resolution() -> None:
    contest_id = uuid4()
    linked = _snapshot(
        contest=ContestLinkage(
            contest_id=contest_id,
            participant=APE,
            counterpart=ME,
            counterpart_perceived=True,
            certificate={},
        )
    )
    backend = {
        "kind": "ai_roll",
        "submission_source": "backend_dice_service",
        "pending_roll_request_id": None,
        "instruction_snapshot": json.loads(linked.model_dump_json()),
    }
    RollEventPayload.model_validate(
        _payload(**backend, contest_resolution=_resolution(contest_id))
    )
    with pytest.raises(ValidationError):  # another contest's resolution
        RollEventPayload.model_validate(
            _payload(**backend, contest_resolution=_resolution(uuid4()))
        )
    with pytest.raises(ValidationError):  # a roll of no contest
        RollEventPayload.model_validate(
            _payload(contest_resolution=_resolution(contest_id))
        )


def _event(**changes: Any) -> dict[str, Any]:
    values = {
        "event_id": str(uuid4()),
        "sequence_id": str(SEQUENCE),
        "step_id": str(STEP),
        "story_id": str(uuid4()),
        "session_id": str(uuid4()),
        "character_id": str(ME.subject_id),
        "event_order": 1,
        "kind": "player_roll",
        "mechanical_provenance": "{}",
        "provisional_effects_json": "[]",
        "created_at": datetime(2026, 10, 14, tzinfo=UTC).isoformat(),
        "payload": _payload(),
    }
    return values | changes


def test_the_event_envelope_agrees_with_its_payload() -> None:
    ActionResolutionEvent.model_validate_json(json.dumps(_event()))
    for changes in (
        {"kind": "ai_roll"},  # envelope kind against payload kind
        {"step_id": str(uuid4())},  # another step's snapshot
        {"sequence_id": str(uuid4())},  # another sequence's snapshot
    ):
        with pytest.raises(ValidationError):
            ActionResolutionEvent.model_validate_json(json.dumps(_event(**changes)))
