"""CRD Issue 15b Phase 3: the RPG action routes' own contract, on the real
``create_app`` without a published rules store.

- the one per-story lock shared by turns, rolls, adjustments, decisions and
  resume (15b-29, AC30);
- the seam's story scoping and its typed, fixed-message error translation;
- resume's typed refusals, including the success-equivalent
  ``action_sequence_already_completed`` (15b-32, AC27);
- the generated public shapes: player views only (15b-17, AC32).

The lifecycle end to end is ``test_rpg_actions_on_published_release``.
"""

from __future__ import annotations

import inspect
import threading
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import pytest
import sqlalchemy as sa

from afterworlds.api import rpg_actions as seam
from afterworlds.api.deps import get_orchestrator, get_rpg_actions
from afterworlds.api.errors import ApiErrorResponse
from afterworlds.models.enums import (
    DiceSelectionRule,
    RollContribution,
    RollPurpose,
    RpgInteractionPhase,
)
from afterworlds.models.rpg import (
    ActionResolutionAdvanceResult,
    MechanicalDecisionOption,
    MechanicalDecisionSubmission,
    PendingMechanicalDecisionView,
    PhysicalAggregateRollSubmission,
    PlayerRollInstructionView,
    PlayerRollTermView,
    SequenceProgressView,
)
from afterworlds.pipeline.orchestrator.models import OrchestrationResult
from afterworlds.pipeline.rpg import models as rpg_models
from tests.api._fixtures import make_delivered_result, make_pipeline_error_result
from tests.api.test_turns import _create_story, _seed_hosted

_REPO = Path(__file__).resolve().parents[2]
_BACKEND_MESSAGE = "hidden-modifier-17 AC 15"


def _backend_errors() -> list[type[rpg_models.ActionResolutionError]]:
    return [
        cls
        for cls in vars(rpg_models).values()
        if inspect.isclass(cls) and issubclass(cls, rpg_models.ActionResolutionError)
    ]


def _roll_view(request_id: UUID) -> ActionResolutionAdvanceResult:
    sequence = uuid4()
    return ActionResolutionAdvanceResult(
        sequence_id=sequence,
        interaction_phase=RpgInteractionPhase.PENDING_ROLL,
        pending_roll=PlayerRollInstructionView(
            pending_roll_request_id=request_id,
            sequence_id=sequence,
            instruction_id=uuid4(),
            instruction_revision=1,
            purpose=RollPurpose.ATTACK,
            interaction_phase=RpgInteractionPhase.PENDING_ROLL,
            progress=SequenceProgressView(step_index=1),
            display_label="Club attack",
            display_expression="1d20 + 1",
            terms=(
                PlayerRollTermView(
                    term_id=uuid4(),
                    count=1,
                    sides=20,
                    selection_rule=DiceSelectionRule.SUM_ALL,
                    contribution=RollContribution.ADD,
                ),
            ),
            visible_modifiers=(),
            visible_modifier_total=1,
            adjustment_options=(),
        ),
    )


def _decision_view(decision_id: UUID) -> ActionResolutionAdvanceResult:
    sequence = uuid4()
    return ActionResolutionAdvanceResult(
        sequence_id=sequence,
        interaction_phase=RpgInteractionPhase.PENDING_MECHANICAL_DECISION,
        pending_decision=PendingMechanicalDecisionView(
            decision_request_id=decision_id,
            sequence_id=sequence,
            decision_revision=1,
            interaction_phase=RpgInteractionPhase.PENDING_MECHANICAL_DECISION,
            prompt="Knock it out?",
            options=(
                MechanicalDecisionOption(
                    option_id="knock_out", player_visible_label="Yes"
                ),
            ),
        ),
    )


class _Sequences:
    """A stand-in ActionResolutionService: a fixed current interaction, and
    every delegated call recorded (raising *error* when given)."""

    def __init__(
        self,
        current: ActionResolutionAdvanceResult | None,
        error: Exception | None = None,
    ) -> None:
        self._current = current
        self._error = error
        self.calls: list[str] = []

    def current(self, story_id: UUID) -> ActionResolutionAdvanceResult | None:
        return self._current

    def _delegate(self, name: str) -> ActionResolutionAdvanceResult:
        self.calls.append(name)
        if self._error is not None:
            raise self._error
        assert self._current is not None
        return self._current

    def consume_roll(self, submission: Any) -> ActionResolutionAdvanceResult:
        return self._delegate("consume_roll")

    def apply_adjustment(self, *args: Any) -> ActionResolutionAdvanceResult:
        return self._delegate("apply_adjustment")

    def submit_decision(self, submission: Any) -> ActionResolutionAdvanceResult:
        return self._delegate("submit_decision")


def _actions(sequences: _Sequences) -> seam.RpgActions:
    return seam.RpgActions(sequences)  # type: ignore[arg-type]


def _aggregate(request_id: UUID) -> PhysicalAggregateRollSubmission:
    return PhysicalAggregateRollSubmission(
        source="physical_self_report",
        pending_roll_request_id=request_id,
        expected_instruction_revision=1,
        reported_aggregate=12,
    )


# ---------------------------------------------------------------------------
# The seam: error table, fixed messages, story scoping
# ---------------------------------------------------------------------------


def test_every_backend_code_translates_one_to_one_into_the_envelope() -> None:
    codes = {cls.code for cls in _backend_errors()}
    assert set(seam.ACTION_ERRORS) == codes
    for key, (status, error_code, message) in seam.ACTION_ERRORS.items():
        assert error_code.value == key.lower()
        assert status in (403, 404, 409, 422)
        assert "{" not in message  # fixed text, nothing interpolated


@pytest.mark.parametrize("error", _backend_errors(), ids=lambda cls: cls.__name__)
def test_a_backend_refusal_reaches_the_client_typed_with_a_fixed_message(
    error: type[rpg_models.ActionResolutionError],
) -> None:
    request_id = uuid4()
    sequences = _Sequences(_roll_view(request_id), error(_BACKEND_MESSAGE))
    with pytest.raises(ApiErrorResponse) as raised:
        _actions(sequences).submit_roll(uuid4(), _aggregate(request_id))
    status, error_code, message = seam.ACTION_ERRORS[error.code]
    assert raised.value.status_code == status
    assert raised.value.error.error_code is error_code
    assert raised.value.error.message == message
    assert _BACKEND_MESSAGE not in raised.value.error.model_dump_json()


def test_a_submission_for_another_pending_interaction_is_never_delegated() -> None:
    story = uuid4()
    roll = _Sequences(_roll_view(uuid4()))
    actions = _actions(roll)
    for submit in (
        lambda: actions.submit_roll(story, _aggregate(uuid4())),
        lambda: actions.adjust(story, uuid4(), 1, "finesse_dexterity"),
    ):
        with pytest.raises(ApiErrorResponse) as raised:
            submit()
        assert raised.value.error.error_code.value == "pending_roll_not_found"
    decision = _Sequences(_decision_view(uuid4()))
    for sequences in (decision, _Sequences(None)):
        with pytest.raises(ApiErrorResponse) as raised:
            _actions(sequences).decide(
                story,
                MechanicalDecisionSubmission(
                    decision_request_id=uuid4(),
                    expected_decision_revision=1,
                    option_id="knock_out",
                ),
            )
        assert raised.value.error.error_code.value == "mechanical_decision_invalid"
    # A roll id while a decision is pending, and anything with none pending.
    for sequences in (decision, _Sequences(None)):
        with pytest.raises(ApiErrorResponse):
            _actions(sequences).submit_roll(story, _aggregate(uuid4()))
    assert roll.calls == decision.calls == []


def test_the_current_pending_interaction_is_delegated() -> None:
    request_id, decision_id = uuid4(), uuid4()
    roll = _Sequences(_roll_view(request_id))
    _actions(roll).submit_roll(uuid4(), _aggregate(request_id))
    _actions(roll).adjust(uuid4(), request_id, 1, "finesse_dexterity")
    decision = _Sequences(_decision_view(decision_id))
    _actions(decision).decide(
        uuid4(),
        MechanicalDecisionSubmission(
            decision_request_id=decision_id,
            expected_decision_revision=1,
            option_id="knock_out",
        ),
    )
    assert roll.calls == ["consume_roll", "apply_adjustment"]
    assert decision.calls == ["submit_decision"]


# ---------------------------------------------------------------------------
# One story lock for every mutation (AC30)
# ---------------------------------------------------------------------------


class _BlockingSequences(_Sequences):
    def __init__(self, request_id: UUID) -> None:
        super().__init__(_roll_view(request_id))
        self.entered = threading.Event()
        self.release = threading.Event()

    def consume_roll(self, submission: Any) -> ActionResolutionAdvanceResult:
        self.entered.set()
        assert self.release.wait(timeout=10)
        return super().consume_roll(submission)


class _BlockingOrchestrator:
    def __init__(self) -> None:
        self.entered = threading.Event()
        self.release = threading.Event()

    def orchestrate_turn(self, *args: Any, **kwargs: Any) -> OrchestrationResult:
        self.entered.set()
        assert self.release.wait(timeout=10)
        return make_delivered_result()


def _mutations(story: str, request_id: UUID) -> list[tuple[str, dict[str, Any] | None]]:
    roll = {
        "source": "physical_self_report",
        "pending_roll_request_id": str(request_id),
        "expected_instruction_revision": 1,
        "reported_aggregate": 12,
    }
    return [
        (f"/api/stories/{story}/turns", {"user_input": "x"}),
        (f"/api/stories/{story}/rpg/rolls", roll),
        (
            f"/api/stories/{story}/rpg/adjustments",
            {
                "pending_roll_request_id": str(request_id),
                "expected_instruction_revision": 1,
                "option_id": "finesse_dexterity",
            },
        ),
        (
            f"/api/stories/{story}/rpg/decisions",
            {
                "decision_request_id": str(uuid4()),
                "expected_decision_revision": 1,
                "option_id": "knock_out",
            },
        ),
        (f"/api/stories/{story}/rpg/sequences/{uuid4()}/resume", None),
    ]


def _all_in_flight(client: Any, calls: list[tuple[str, dict[str, Any] | None]]) -> None:
    for path, body in calls:
        resp = client.post(path, json=body) if body is not None else client.post(path)
        assert resp.status_code == 409, (path, resp.text)
        assert resp.json()["error_code"] == "turn_in_flight", path


def test_a_roll_in_flight_holds_every_mutation_of_its_story(client) -> None:  # type: ignore[no-untyped-def]
    story = _create_story(client)
    request_id = uuid4()
    sequences = _BlockingSequences(request_id)
    client.app.dependency_overrides[get_rpg_actions] = lambda: _actions(sequences)
    first = _mutations(story, request_id)[1]
    results: list[int] = []
    holder = threading.Thread(
        target=lambda: results.append(client.post(first[0], json=first[1]).status_code)
    )
    holder.start()
    try:
        assert sequences.entered.wait(timeout=10)
        _all_in_flight(client, _mutations(story, request_id))
        # Another story is not held.
        other = _create_story(client)
        resp = client.get(f"/api/stories/{other}/rpg/pending-interaction")
        assert resp.status_code == 200, resp.text
    finally:
        sequences.release.set()
        holder.join(timeout=10)
    assert results == [200]
    assert sequences.calls == ["consume_roll"]
    assert not client.app.state.story_locks[UUID(story)].locked()


def test_a_turn_in_flight_holds_every_rpg_operation_of_its_story(client) -> None:  # type: ignore[no-untyped-def]
    story = _create_story(client)
    _seed_hosted(client)
    orchestrator = _BlockingOrchestrator()
    client.app.dependency_overrides[get_orchestrator] = lambda: orchestrator
    request_id = uuid4()
    sequences = _Sequences(_roll_view(request_id))
    client.app.dependency_overrides[get_rpg_actions] = lambda: _actions(sequences)
    results: list[int] = []
    holder = threading.Thread(
        target=lambda: results.append(
            client.post(
                f"/api/stories/{story}/turns", json={"user_input": "x"}
            ).status_code
        )
    )
    holder.start()
    try:
        assert orchestrator.entered.wait(timeout=10)
        _all_in_flight(client, _mutations(story, request_id))
    finally:
        orchestrator.release.set()
        holder.join(timeout=10)
    assert results == [200]
    assert sequences.calls == []


# ---------------------------------------------------------------------------
# Resume: typed refusals and the already-completed contract
# ---------------------------------------------------------------------------


class _ResumeOrchestrator:
    def __init__(self, code: str) -> None:
        self._code = code
        self.calls: list[tuple[Any, ...]] = []

    def orchestrate_rpg_resume(
        self, story_id: UUID, node_id: UUID, sequence_id: UUID, **kw: Any
    ) -> OrchestrationResult:
        self.calls.append((story_id, node_id, sequence_id, kw["access_path"]))
        return make_pipeline_error_result(f"[{self._code}]").model_copy(
            update={"action_sequence_error": self._code, "planner_skipped": True}
        )


@pytest.mark.parametrize(
    ("code", "status"),
    [
        ("ACTION_SEQUENCE_ALREADY_COMPLETED", 409),
        ("ACTION_SEQUENCE_NOT_FOUND", 404),
        ("ACTION_SEQUENCE_STATE_CONFLICT", 409),
        ("SEQUENCE_NOT_READY_FOR_NARRATION", 409),
    ],
)
def test_resume_translates_the_orchestrators_typed_refusals(  # type: ignore[no-untyped-def]
    client, code: str, status: int
) -> None:
    story = _create_story(client)
    _seed_hosted(client)
    orchestrator = _ResumeOrchestrator(code)
    client.app.dependency_overrides[get_orchestrator] = lambda: orchestrator
    sequence = uuid4()
    with client.app.state.session_factory() as s:
        events = s.execute(
            sa.text("SELECT COUNT(*) FROM entitlement_event")
        ).scalar_one()
    resp = client.post(f"/api/stories/{story}/rpg/sequences/{sequence}/resume")
    assert resp.status_code == status, resp.text
    assert resp.json() == {
        "error_code": code.lower(),
        "message": seam.ACTION_ERRORS[code][2],
        "detail": None,
        "schema_version": 1,
    }
    # The current canonical node and the server-selected path were passed;
    # nothing was settled.
    ((story_id, node_id, sequence_id, access_path),) = orchestrator.calls
    assert (str(story_id), sequence_id, access_path.value) == (
        story,
        sequence,
        "hosted",
    )
    assert isinstance(node_id, UUID)
    with client.app.state.session_factory() as s:
        assert (
            s.execute(sa.text("SELECT COUNT(*) FROM entitlement_event")).scalar_one()
            == events
        )


class _DeliverySequences(_Sequences):
    """The owning service's delivery check, refusing with *error*."""

    def __init__(
        self,
        current: ActionResolutionAdvanceResult | None,
        error: rpg_models.ActionResolutionError,
    ) -> None:
        super().__init__(current)
        self._delivery_error = error
        self.deliveries: list[UUID] = []

    def prepare_delivery(self, story_id: UUID, sequence_id: UUID, node_id: UUID) -> Any:
        self.deliveries.append(sequence_id)
        raise self._delivery_error


@pytest.mark.parametrize(
    ("error", "status"),
    [
        (rpg_models.ActionSequenceAlreadyCompletedError("narrated"), 409),
        (rpg_models.ActionSequenceNotFoundError("absent"), 404),
    ],
)
def test_a_settled_resume_is_classified_even_without_a_runnable_access_path(  # type: ignore[no-untyped-def]
    client, error: rpg_models.ActionResolutionError, status: int
) -> None:
    """15b-32 after the narration exhausted access: no entitlement here, so
    no access path is runnable. A sequence that is not the story's
    unresolved one still gets the owning service's typed classification;
    the orchestrator (providers, settlement) is never reached."""
    story = _create_story(client)
    orchestrator = _ResumeOrchestrator("unused")
    client.app.dependency_overrides[get_orchestrator] = lambda: orchestrator
    sequences = _DeliverySequences(None, error)
    client.app.dependency_overrides[get_rpg_actions] = lambda: _actions(sequences)
    sequence = uuid4()
    resp = client.post(f"/api/stories/{story}/rpg/sequences/{sequence}/resume")
    assert resp.status_code == status, resp.text
    assert resp.json()["error_code"] == error.code.lower()
    assert sequences.deliveries == [sequence]
    assert orchestrator.calls == []


def test_the_storys_ready_sequence_stays_blocked_without_an_access_path(  # type: ignore[no-untyped-def]
    client,
) -> None:
    story = _create_story(client)
    orchestrator = _ResumeOrchestrator("unused")
    client.app.dependency_overrides[get_orchestrator] = lambda: orchestrator
    sequence = uuid4()
    ready = ActionResolutionAdvanceResult(
        sequence_id=sequence,
        interaction_phase=RpgInteractionPhase.READY_FOR_NARRATION,
    )
    sequences = _DeliverySequences(
        ready, rpg_models.ActionSequenceAlreadyCompletedError("unused")
    )
    client.app.dependency_overrides[get_rpg_actions] = lambda: _actions(sequences)
    resp = client.post(f"/api/stories/{story}/rpg/sequences/{sequence}/resume")
    assert resp.status_code == 403, resp.text
    assert resp.json()["error_code"] == "entitlement_blocked"
    assert sequences.deliveries == [] and orchestrator.calls == []


def test_reading_an_unknown_storys_pending_interaction_is_not_found(client) -> None:  # type: ignore[no-untyped-def]
    resp = client.get(f"/api/stories/{uuid4()}/rpg/pending-interaction")
    assert resp.status_code == 404
    assert resp.json()["error_code"] == "not_found"
    story = _create_story(client)  # a Writing story: nothing pending
    resp = client.get(f"/api/stories/{story}/rpg/pending-interaction")
    assert resp.json() == {"interaction": None, "schema_version": 1}


# ---------------------------------------------------------------------------
# Generated public shapes (AC32)
# ---------------------------------------------------------------------------

#: Exactly the deliberate player views and requests.
_PUBLIC = {
    "PendingInteractionResponse": {"interaction", "schema_version"},
    "ActionResolutionAdvanceResult": {
        "schema_version",
        "sequence_id",
        "interaction_phase",
        "pending_roll",
        "pending_decision",
    },
    "PlayerRollInstructionView": {
        "schema_version",
        "pending_roll_request_id",
        "sequence_id",
        "instruction_id",
        "instruction_revision",
        "purpose",
        "interaction_phase",
        "progress",
        "display_label",
        "display_expression",
        "terms",
        "visible_modifiers",
        "visible_modifier_total",
        "adjustment_options",
    },
    "PlayerRollTermView": {
        "schema_version",
        "term_id",
        "count",
        "sides",
        "selection_rule",
        "keep_count",
        "contribution",
        "label",
    },
    "PlayerModifierView": {"schema_version", "modifier_id", "label", "value"},
    "PlayerAdjustmentOptionView": {
        "schema_version",
        "option_id",
        "player_visible_label",
        "resource_preview",
    },
    "SequenceProgressView": {
        "schema_version",
        "step_index",
        "known_step_count",
        "step_label",
        "sequence_label",
    },
    "PendingMechanicalDecisionView": {
        "schema_version",
        "decision_request_id",
        "sequence_id",
        "decision_revision",
        "interaction_phase",
        "prompt",
        "options",
    },
    "MechanicalDecisionOption": {"schema_version", "option_id", "player_visible_label"},
    "RawPlayerRollSubmission": {
        "schema_version",
        "source",
        "pending_roll_request_id",
        "expected_instruction_revision",
        "term_results",
    },
    "PlayerRollTermResult": {"schema_version", "term_id", "values"},
    "PhysicalAggregateRollSubmission": {
        "schema_version",
        "source",
        "pending_roll_request_id",
        "expected_instruction_revision",
        "reported_aggregate",
    },
    "RollAdjustmentRequest": {
        "schema_version",
        "pending_roll_request_id",
        "expected_instruction_revision",
        "option_id",
    },
    "MechanicalDecisionSubmission": {
        "schema_version",
        "decision_request_id",
        "expected_decision_revision",
        "option_id",
    },
    "ApiError": {"error_code", "message", "detail", "schema_version"},
}

#: Backend authority that must never be a public schema.
_BACKEND = {
    "RollInstructionSnapshot",
    "RollModifierComponent",
    "RollAdjustmentOption",
    "NaturalOutcome",
    "ContestLinkage",
    "MechanicalDecisionSnapshot",
    "MechanicalDecisionOptionSnapshot",
    "ReadyActionResolutionBundle",
    "ResolvedSequenceStep",
    "DerivedRollTermResult",
    "ActionResolutionSequence",
    "ActionResolutionEvent",
    "RollEventPayload",
    "AdjustmentEventPayload",
    "MechanicalDecisionEventPayload",
    "WriterAdjudicationView",
    "ResolvedAdjudicationRecord",
    "SheetEffect",
}


def test_the_generated_contract_exposes_only_deliberate_player_shapes(client) -> None:  # type: ignore[no-untyped-def]
    schema = client.app.openapi()
    components = schema["components"]["schemas"]
    for name, fields in _PUBLIC.items():
        assert set(components[name]["properties"]) == fields, name
    assert not _BACKEND & set(components)
    codes = set(components["ApiErrorCode"]["enum"])
    assert {code.lower() for code in seam.ACTION_ERRORS} <= codes
    resume = schema["paths"][
        "/api/stories/{story_id}/rpg/sequences/{sequence_id}/resume"
    ]
    assert "requestBody" not in resume["post"]
    conflict = resume["post"]["responses"]["409"]["content"]["application/json"]
    assert conflict["schema"] == {"$ref": "#/components/schemas/ApiError"}
    for path in ("rolls", "adjustments", "decisions"):
        assert f"/api/stories/{{story_id}}/rpg/{path}" in schema["paths"]
    # The committed TypeScript carries the same deliberate shapes.
    generated = (_REPO / "frontend" / "src" / "api" / "schema.ts").read_text(
        encoding="utf-8"
    )
    assert '"action_sequence_already_completed"' in generated
    assert '"/api/stories/{story_id}/rpg/pending-interaction"' in generated
    for name in _BACKEND:
        assert f"        {name}: {{" not in generated, name
