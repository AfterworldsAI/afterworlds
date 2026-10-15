"""DB-level tests for pending_roll_requests — the partial unique index.

CRD Issue 15 remediation: partial unique index on (story_id) WHERE status='pending'.
The legacy ``PendingRollRequestService.mark_consumed`` path is retired (CRD Issue
15b): a pending roll is consumed only by the action-resolution sequence's
conditional update, proven in ``test_action_resolution_lifecycle.py``.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

import afterworlds.persistence.orm.rpg  # noqa: F401 — register tables with Base.metadata
from afterworlds.models.enums import IntentType
from afterworlds.models.turn import Turn
from afterworlds.persistence.crud.character_sheet import create_rpg_base_sheet
from afterworlds.persistence.crud.node import create_turn
from afterworlds.persistence.crud.story import create_story
from afterworlds.persistence.orm.rpg import PendingRollRequestORM
from tests.persistence.conftest import make_base_sheet, make_story

_NOW = datetime(2026, 1, 1, tzinfo=UTC)


# ---------------------------------------------------------------------------
# Shared setup helpers
# ---------------------------------------------------------------------------


def _seed_prerequisites(session: object) -> tuple[str, str, str]:
    """Create story + base sheet + turn; return (story_id, character_id, turn_id)."""
    story = make_story()
    create_story(session, story)  # type: ignore[arg-type]
    base = make_base_sheet(str(story.story_id))
    create_rpg_base_sheet(session, base)  # type: ignore[arg-type]
    turn = Turn(
        user_input="test",
        assistant_output="test",
        timestamp=_NOW,
        intent_classification=IntentType.IN_CHARACTER_ACTION,
        node_id=None,
    )
    create_turn(session, turn)  # type: ignore[arg-type]
    session.commit()  # type: ignore[attr-defined]
    return str(story.story_id), str(base.sheet_id), str(turn.turn_id)


def _make_orm_row(
    story_id: str,
    character_id: str,
    turn_id: str,
    *,
    status: str = "pending",
    request_id: str | None = None,
) -> PendingRollRequestORM:
    return PendingRollRequestORM(
        request_id=request_id or str(uuid4()),
        story_id=story_id,
        session_id=str(uuid4()),
        character_id=character_id,
        originating_turn_id=turn_id,
        visibility="player",
        source_proposal_ref="roll_0",
        status=status,
        created_at=_NOW.isoformat(),
        schema_version=2,
        sequence_id=str(uuid4()),
        step_id=str(uuid4()),
        instruction_id=str(uuid4()),
        instruction_revision=1,
        instruction_schema_version=1,
        instruction_snapshot_json="{}",
    )


# ---------------------------------------------------------------------------
# Partial unique index constraint tests
# ---------------------------------------------------------------------------


def test_cannot_insert_two_pending_rows_for_same_story(session) -> None:  # type: ignore[no-untyped-def]
    """Two rows with status='pending' for the same story violates the partial index."""
    story_id, char_id, turn_id = _seed_prerequisites(session)
    session.add(_make_orm_row(story_id, char_id, turn_id, status="pending"))
    session.flush()

    session.add(_make_orm_row(story_id, char_id, turn_id, status="pending"))
    with pytest.raises(IntegrityError):
        session.flush()


def test_can_insert_pending_and_consumed_for_same_story(session) -> None:  # type: ignore[no-untyped-def]
    """A consumed row plus a pending row for the same story is allowed."""
    story_id, char_id, turn_id = _seed_prerequisites(session)
    session.add(_make_orm_row(story_id, char_id, turn_id, status="consumed"))
    session.add(_make_orm_row(story_id, char_id, turn_id, status="pending"))
    session.flush()
    session.commit()


def test_can_insert_multiple_consumed_rows_for_same_story(session) -> None:  # type: ignore[no-untyped-def]
    """Multiple consumed rows for the same story are allowed."""
    story_id, char_id, turn_id = _seed_prerequisites(session)
    session.add(_make_orm_row(story_id, char_id, turn_id, status="consumed"))
    session.add(_make_orm_row(story_id, char_id, turn_id, status="consumed"))
    session.flush()
    session.commit()
