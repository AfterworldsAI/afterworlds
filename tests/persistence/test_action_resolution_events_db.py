"""DB-level tests for action_resolution_events — append-only triggers and uniqueness.

CRD Issue 15b (ADR-015b 15b-34). Identity columns on this table are
deliberately unconstrained strings, not FK-constrained (see
ActionResolutionEventORM's docstring), so these tests need no parent
story/turn/character rows.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError

import afterworlds.persistence.orm.rpg  # noqa: F401 — register tables with Base.metadata
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.persistence.orm.base import Base
from afterworlds.persistence.orm.rpg import ActionResolutionEventORM

_NOW = datetime(2026, 1, 1, tzinfo=UTC)

_EVENTS_DELETE_TRIGGER = """
CREATE TRIGGER prevent_action_resolution_events_delete
BEFORE DELETE ON action_resolution_events
BEGIN
    SELECT RAISE(ABORT, 'action_resolution_events is append-only: DELETE is forbidden');
END
"""
_EVENTS_UPDATE_TRIGGER = """
CREATE TRIGGER prevent_action_resolution_events_update
BEFORE UPDATE ON action_resolution_events
BEGIN
    SELECT RAISE(ABORT, 'action_resolution_events is append-only: UPDATE is forbidden');
END
"""


@pytest.fixture()
def engine():  # type: ignore[no-untyped-def]
    """In-memory SQLite engine with tables and append-only triggers installed.

    create_all() sets up ORM schema; triggers are added manually because they
    live in the Alembic migration (op.execute), not in ORM metadata.
    """
    eng = create_engine("sqlite://")
    Base.metadata.create_all(eng)
    with eng.connect() as conn:
        conn.execute(sa.text(_EVENTS_DELETE_TRIGGER))
        conn.execute(sa.text(_EVENTS_UPDATE_TRIGGER))
        conn.commit()
    yield eng
    Base.metadata.drop_all(eng)
    eng.dispose()


@pytest.fixture()
def session(engine):  # type: ignore[no-untyped-def]
    factory = create_session_factory(engine)
    sess = factory()
    try:
        yield sess
    finally:
        sess.close()


def _make_event_row(*, sequence_id: str, event_order: int) -> ActionResolutionEventORM:
    return ActionResolutionEventORM(
        event_id=str(uuid4()),
        sequence_id=sequence_id,
        step_id=str(uuid4()),
        story_id=str(uuid4()),
        session_id=str(uuid4()),
        character_id=str(uuid4()),
        event_order=event_order,
        kind="player_roll",
        mechanical_provenance="adapter:d20",
        provisional_effects_json="[]",
        created_at=_NOW.isoformat(),
        payload_json="{}",
    )


def test_direct_delete_action_resolution_events_blocked_by_trigger(session) -> None:  # type: ignore[no-untyped-def]
    """Direct DELETE on action_resolution_events is aborted by the trigger."""
    session.add(_make_event_row(sequence_id=str(uuid4()), event_order=1))
    session.commit()

    with pytest.raises(IntegrityError, match="append-only"):
        session.execute(sa.text("DELETE FROM action_resolution_events"))


def test_direct_update_action_resolution_events_blocked_by_trigger(session) -> None:  # type: ignore[no-untyped-def]
    """Direct UPDATE on action_resolution_events is aborted by the trigger."""
    row = _make_event_row(sequence_id=str(uuid4()), event_order=1)
    session.add(row)
    session.commit()

    with pytest.raises(IntegrityError, match="append-only"):
        session.execute(
            sa.text(
                "UPDATE action_resolution_events SET kind = 'ai_roll' "
                "WHERE event_id = :eid"
            ),
            {"eid": row.event_id},
        )


def test_duplicate_sequence_event_order_rejected(session) -> None:  # type: ignore[no-untyped-def]
    """The unique (sequence_id, event_order) index rejects a duplicate position."""
    sequence_id = str(uuid4())
    session.add(_make_event_row(sequence_id=sequence_id, event_order=1))
    session.commit()

    session.add(_make_event_row(sequence_id=sequence_id, event_order=1))
    with pytest.raises(IntegrityError):
        session.flush()


def test_transaction_rollback_removes_uncommitted_event_rows(session) -> None:  # type: ignore[no-untyped-def]
    """Rollback removes an uncommitted event row without hitting the trigger."""
    sequence_id = str(uuid4())
    session.add(_make_event_row(sequence_id=sequence_id, event_order=1))
    session.flush()  # row visible within transaction but not committed

    session.rollback()

    count = session.execute(
        sa.text(
            "SELECT COUNT(*) FROM action_resolution_events WHERE sequence_id = :sid"
        ),
        {"sid": sequence_id},
    ).scalar()
    assert count == 0
