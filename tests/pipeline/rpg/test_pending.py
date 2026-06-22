"""Unit tests for PendingRollRequestService — CRD Issue 15 Phase 6."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from afterworlds.models.enums import RollVisibility
from afterworlds.models.rpg import PendingRollRequest
from afterworlds.pipeline.rpg.pending import (
    PendingRollAlreadyConsumedError,
    PendingRollDuplicateError,
    PendingRollRequestService,
    _orm_to_model,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_pending_orm(
    story_id: str | None = None,
    request_id: str | None = None,
    status: str = "pending",
) -> MagicMock:
    """Return a mock PendingRollRequestORM with sensible defaults."""
    orm = MagicMock()
    orm.request_id = request_id or str(uuid4())
    orm.story_id = story_id or str(uuid4())
    orm.session_id = str(uuid4())
    orm.character_id = str(uuid4())
    orm.check_label = "Stealth Check"
    orm.player_facing_instruction = "Roll a Stealth Check!"
    orm.expected_value_shape = "d20"
    orm.visible_modifier_note = "proficient"
    orm.visibility = "player"
    orm.source_proposal_ref = "roll_0"
    orm.originating_turn_id = str(uuid4())
    orm.consumed_turn_id = None
    orm.status = status
    orm.created_at = datetime.now(tz=UTC).isoformat()
    orm.schema_version = 1
    orm.roll_expression = "1d20+5"
    orm.visible_modifier_total = 5
    orm.visible_modifier_breakdown_json = '{"proficiency": 2, "ability": 3}'
    orm.hidden_modifier_present = False
    orm.adapter_context_hash = None
    return orm


# ---------------------------------------------------------------------------
# _orm_to_model
# ---------------------------------------------------------------------------


def test_orm_to_model_converts_fields() -> None:
    sid = uuid4()
    orm = _make_pending_orm(story_id=str(sid))
    model = _orm_to_model(orm)
    assert model.story_id == sid
    assert model.check_label == "Stealth Check"
    assert model.visibility == RollVisibility.PLAYER
    assert model.status == "pending"
    assert model.schema_version == 1
    assert model.visible_modifier_total == 5
    assert model.hidden_modifier_present is False


def test_orm_to_model_handles_null_consumed_turn() -> None:
    orm = _make_pending_orm()
    orm.consumed_turn_id = None
    model = _orm_to_model(orm)
    assert model.consumed_turn_id is None


def test_orm_to_model_handles_consumed_turn() -> None:
    consumed = uuid4()
    orm = _make_pending_orm()
    orm.consumed_turn_id = str(consumed)
    model = _orm_to_model(orm)
    assert model.consumed_turn_id == consumed


# ---------------------------------------------------------------------------
# PendingRollRequestService.load_pending_for_story
# ---------------------------------------------------------------------------


def test_load_pending_returns_none_when_no_row() -> None:
    mock_session = MagicMock()
    mock_session.query.return_value.filter_by.return_value.one_or_none.return_value = (
        None
    )
    factory = MagicMock(return_value=mock_session)
    svc = PendingRollRequestService(session_factory=factory)

    result = svc.load_pending_for_story(uuid4())

    assert result is None
    mock_session.close.assert_called_once()


def test_load_pending_returns_model_when_row_exists() -> None:
    sid = uuid4()
    orm = _make_pending_orm(story_id=str(sid))
    mock_session = MagicMock()
    mock_session.query.return_value.filter_by.return_value.one_or_none.return_value = (
        orm
    )
    factory = MagicMock(return_value=mock_session)
    svc = PendingRollRequestService(session_factory=factory)

    result = svc.load_pending_for_story(sid)

    assert isinstance(result, PendingRollRequest)
    assert result.story_id == sid
    mock_session.close.assert_called_once()


def test_load_pending_closes_session_on_exception() -> None:
    mock_session = MagicMock()
    mock_session.query.side_effect = RuntimeError("db error")
    factory = MagicMock(return_value=mock_session)
    svc = PendingRollRequestService(session_factory=factory)

    with pytest.raises(RuntimeError, match="db error"):
        svc.load_pending_for_story(uuid4())

    mock_session.close.assert_called_once()


# ---------------------------------------------------------------------------
# PendingRollRequestService.mark_consumed
# ---------------------------------------------------------------------------


def test_mark_consumed_updates_status() -> None:
    mock_session = MagicMock()
    mock_query = mock_session.query.return_value.filter_by.return_value
    mock_query.update.return_value = 1
    factory = MagicMock(return_value=mock_session)
    svc = PendingRollRequestService(session_factory=factory)

    request_id = uuid4()
    turn_id = uuid4()
    svc.mark_consumed(mock_session, request_id, turn_id)

    mock_query.update.assert_called_once_with(
        {"status": "consumed", "consumed_turn_id": str(turn_id)}
    )


def test_mark_consumed_filters_on_pending_status() -> None:
    mock_session = MagicMock()
    mock_query = mock_session.query.return_value.filter_by.return_value
    mock_query.update.return_value = 1
    factory = MagicMock(return_value=mock_session)
    svc = PendingRollRequestService(session_factory=factory)

    request_id = uuid4()
    turn_id = uuid4()
    svc.mark_consumed(mock_session, request_id, turn_id)

    mock_session.query.return_value.filter_by.assert_called_once_with(
        request_id=str(request_id), status="pending"
    )


def test_mark_consumed_raises_when_zero_rows_updated() -> None:
    mock_session = MagicMock()
    mock_query = mock_session.query.return_value.filter_by.return_value
    mock_query.update.return_value = 0
    factory = MagicMock(return_value=mock_session)
    svc = PendingRollRequestService(session_factory=factory)

    with pytest.raises(
        PendingRollAlreadyConsumedError, match="not in 'pending' status"
    ):
        svc.mark_consumed(mock_session, uuid4(), uuid4())


# ---------------------------------------------------------------------------
# PendingRollRequestService.check_no_pending_for_story
# ---------------------------------------------------------------------------


def test_check_no_pending_does_not_raise_when_empty() -> None:
    mock_session = MagicMock()
    mock_session.query.return_value.filter_by.return_value.first.return_value = None
    factory = MagicMock(return_value=mock_session)
    svc = PendingRollRequestService(session_factory=factory)

    # Must not raise
    svc.check_no_pending_for_story(mock_session, uuid4())


def test_check_no_pending_raises_when_exists() -> None:
    existing = _make_pending_orm()
    mock_session = MagicMock()
    mock_session.query.return_value.filter_by.return_value.first.return_value = existing
    factory = MagicMock(return_value=mock_session)
    svc = PendingRollRequestService(session_factory=factory)

    with pytest.raises(
        PendingRollDuplicateError, match="already has an active pending"
    ):
        svc.check_no_pending_for_story(mock_session, uuid4())
