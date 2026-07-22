"""Unit tests for the action-resolution event ledger's typed payloads.

CRD Issue 15b (ADR-015b 15b-34). Issue #127 criteria 42 (kind-safe payload),
43 (decision event identity/option typing), 44 (adjustment event option
typing), 55 (mandatory roll total), 56 (bounded roll outcome) — PR #129
sibling audit closing a gap where these had no persisted test coverage.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from afterworlds.models.enums import DiceSelectionRule, ResolvedStepKind, RollPurpose
from afterworlds.models.rpg import (
    ActionResolutionEvent,
    AdjustmentEventPayload,
    MechanicalDecisionEventPayload,
    MechanicalDecisionOptionSnapshot,
    MechanicalDecisionSnapshot,
    RollEventPayload,
    RollInstructionSnapshot,
    RollTerm,
)

_NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _instruction() -> RollInstructionSnapshot:
    return RollInstructionSnapshot(
        instruction_id=uuid4(),
        instruction_revision=1,
        purpose=RollPurpose.SKILL_CHECK,
        terms=(
            RollTerm(
                term_id=uuid4(),
                count=1,
                sides=20,
                selection_rule=DiceSelectionRule.SUM_ALL,
                keep_count=None,
            ),
        ),
        modifier_components=(),
        display_expression="1d20",
        display_label="Stealth Check",
        source_rule_refs=(),
        adjustment_options=(),
        sequence_id=uuid4(),
        step_id=uuid4(),
    )


def _roll_payload(**overrides: object) -> RollEventPayload:
    defaults: dict[str, object] = {
        "kind": ResolvedStepKind.PLAYER_ROLL,
        "instruction_snapshot": _instruction(),
        "submission_source": None,
        "pending_roll_request_id": uuid4(),
        "raw_input_json": "[]",
        "aggregate_input_json": None,
        "derived_selections_json": "[]",
        "subtotal": 14,
        "total": 17,
        "outcome": "success",
        "gm_cheating_at_roll": False,
    }
    defaults.update(overrides)
    return RollEventPayload(**defaults)  # type: ignore[arg-type]


def _decision_snapshot() -> MechanicalDecisionSnapshot:
    return MechanicalDecisionSnapshot(
        decision_id=uuid4(),
        decision_revision=1,
        prompt="Choose a condition to apply.",
        options=(
            MechanicalDecisionOptionSnapshot(
                option_id="poisoned",
                player_visible_label="Poisoned",
                source_rule_ref=None,
                provisional_effects_json="[]",
            ),
        ),
        source_rule_refs=(),
        sequence_id=uuid4(),
        step_id=uuid4(),
    )


def _event(*, kind: ResolvedStepKind, payload: object) -> ActionResolutionEvent:
    return ActionResolutionEvent(
        event_id=uuid4(),
        sequence_id=uuid4(),
        step_id=uuid4(),
        story_id=uuid4(),
        session_id=uuid4(),
        character_id=uuid4(),
        event_order=1,
        kind=kind,
        mechanical_provenance="test",
        provisional_effects_json="[]",
        created_at=_NOW,
        payload=payload,  # type: ignore[arg-type]
    )


# ---------------------------------------------------------------------------
# Criterion 42 — kind-safe payload
# ---------------------------------------------------------------------------


def test_roll_kind_with_roll_payload_constructs() -> None:
    event = _event(kind=ResolvedStepKind.PLAYER_ROLL, payload=_roll_payload())
    assert event.kind is ResolvedStepKind.PLAYER_ROLL


def test_roll_kind_with_adjustment_payload_rejected() -> None:
    """An impossible cross-kind combination must fail construction."""
    payload = AdjustmentEventPayload(
        resulting_instruction_snapshot=_instruction(),
        accepted_adjustment_option_id="advantage",
    )
    with pytest.raises(ValidationError):
        _event(kind=ResolvedStepKind.PLAYER_ROLL, payload=payload)


def test_adjustment_kind_with_roll_payload_rejected() -> None:
    with pytest.raises(ValidationError):
        _event(kind=ResolvedStepKind.ADJUSTMENT, payload=_roll_payload())


def test_decision_kind_with_roll_payload_rejected() -> None:
    with pytest.raises(ValidationError):
        _event(kind=ResolvedStepKind.MECHANICAL_DECISION, payload=_roll_payload())


def test_roll_payload_rejects_decision_snapshot_field() -> None:
    """A roll event can never carry decision_snapshot -- extra="forbid"."""
    with pytest.raises(ValidationError):
        RollEventPayload(
            kind=ResolvedStepKind.PLAYER_ROLL,
            instruction_snapshot=_instruction(),
            submission_source=None,
            pending_roll_request_id=uuid4(),
            raw_input_json="[]",
            aggregate_input_json=None,
            derived_selections_json="[]",
            subtotal=14,
            total=17,
            outcome="success",
            gm_cheating_at_roll=False,
            decision_snapshot=_decision_snapshot(),  # type: ignore[call-arg]
        )


def test_decision_payload_rejects_instruction_id_field() -> None:
    """A decision event can never carry roll-instruction identity."""
    with pytest.raises(ValidationError):
        MechanicalDecisionEventPayload(
            decision_snapshot=_decision_snapshot(),
            accepted_decision_option_id="poisoned",
            instruction_id=uuid4(),  # type: ignore[call-arg]
        )


# ---------------------------------------------------------------------------
# Criteria 43/44 — decision/adjustment event identity and option typing
# ---------------------------------------------------------------------------


def test_decision_event_preserves_complete_snapshot_and_str_option_id() -> None:
    snapshot = _decision_snapshot()
    payload = MechanicalDecisionEventPayload(
        decision_snapshot=snapshot,
        accepted_decision_option_id="poisoned",
    )
    event = _event(kind=ResolvedStepKind.MECHANICAL_DECISION, payload=payload)
    assert isinstance(event.payload, MechanicalDecisionEventPayload)
    assert event.payload.decision_snapshot.decision_id == snapshot.decision_id
    assert (
        event.payload.decision_snapshot.decision_revision == snapshot.decision_revision
    )
    assert isinstance(event.payload.accepted_decision_option_id, str)
    assert event.payload.accepted_decision_option_id == "poisoned"


def test_adjustment_event_option_id_is_str() -> None:
    payload = AdjustmentEventPayload(
        resulting_instruction_snapshot=_instruction(),
        accepted_adjustment_option_id="advantage",
    )
    event = _event(kind=ResolvedStepKind.ADJUSTMENT, payload=payload)
    assert isinstance(event.payload, AdjustmentEventPayload)
    assert isinstance(event.payload.accepted_adjustment_option_id, str)


# ---------------------------------------------------------------------------
# Criteria 55/56 — mandatory total, bounded outcome
# ---------------------------------------------------------------------------


def test_roll_payload_requires_non_null_total() -> None:
    with pytest.raises(ValidationError):
        _roll_payload(total=None)


def test_roll_payload_rejects_out_of_set_outcome() -> None:
    with pytest.raises(ValidationError):
        _roll_payload(outcome="maybe")


def test_roll_payload_requires_non_null_outcome() -> None:
    with pytest.raises(ValidationError):
        _roll_payload(outcome=None)


@pytest.mark.parametrize(
    "outcome",
    ["success", "failure", "critical_success", "critical_failure", "undetermined"],
)
def test_roll_payload_accepts_every_bounded_outcome(outcome: str) -> None:
    assert _roll_payload(outcome=outcome).outcome == outcome
