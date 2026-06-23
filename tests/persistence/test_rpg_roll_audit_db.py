"""DB-level tests for rpg_roll_audit — append-only triggers and FK integrity.

CRD Issue 15 remediation Round 7: rpg_roll_audit.turn_id FK must NOT cascade-delete
audit rows. Tests cover ORM metadata, migration FK, trigger enforcement, and rollback.
"""

from __future__ import annotations

import os
import tempfile
from datetime import UTC, datetime
from uuid import uuid4

import pytest
import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError

import afterworlds.persistence.orm.rpg  # noqa: F401 — register tables with Base.metadata
from afterworlds.models.enums import IntentType
from afterworlds.models.turn import Turn
from afterworlds.persistence.crud.node import create_turn
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.persistence.orm.base import Base
from afterworlds.persistence.orm.rpg import RpgRollAuditORM
from tests.persistence.conftest import make_story


@pytest.fixture()
def engine():  # type: ignore[no-untyped-def]
    """In-memory SQLite engine with tables and append-only triggers installed.

    create_all() sets up ORM schema; triggers are added manually because they
    live in the Alembic migration (op.execute), not in ORM metadata.
    """
    eng = create_engine("sqlite://")
    Base.metadata.create_all(eng)
    with eng.connect() as conn:
        conn.execute(sa.text(_AUDIT_DELETE_TRIGGER))
        conn.execute(sa.text(_AUDIT_UPDATE_TRIGGER))
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


_NOW = datetime(2026, 1, 1, tzinfo=UTC)

_AUDIT_DELETE_TRIGGER = """
CREATE TRIGGER prevent_rpg_roll_audit_delete
BEFORE DELETE ON rpg_roll_audit
BEGIN
    SELECT RAISE(ABORT, 'rpg_roll_audit is append-only: DELETE is forbidden');
END
"""
_AUDIT_UPDATE_TRIGGER = """
CREATE TRIGGER prevent_rpg_roll_audit_update
BEFORE UPDATE ON rpg_roll_audit
BEGIN
    SELECT RAISE(ABORT, 'rpg_roll_audit is append-only: UPDATE is forbidden');
END
"""


def _make_turn(session: object) -> str:
    """Insert a committed Turn; return turn_id string."""
    from afterworlds.persistence.crud.story import create_story

    story = make_story()
    create_story(session, story)  # type: ignore[arg-type]
    turn = Turn(
        user_input="test",
        assistant_output="test",
        timestamp=_NOW,
        intent_classification=IntentType.IN_CHARACTER_ACTION,
        node_id=None,
    )
    create_turn(session, turn)  # type: ignore[arg-type]
    session.commit()  # type: ignore[attr-defined]
    return str(turn.turn_id)


def _make_audit_row(turn_id: str) -> RpgRollAuditORM:
    return RpgRollAuditORM(
        turn_id=turn_id,
        story_id=str(uuid4()),
        session_id=str(uuid4()),
        character_id=str(uuid4()),
        check_label="Stealth Check",
        visibility="player",
        expression="1d20",
        raw_rolls_json="[12]",
        modifiers_json="{}",
        total=12,
        dc=None,
        outcome="undetermined",
        source="ai",
        gm_cheating_at_roll=False,
        sheet_effects_json="[]",
        created_at=_NOW.isoformat(),
    )


# ---------------------------------------------------------------------------
# ORM metadata: turn_id FK must have no cascade
# ---------------------------------------------------------------------------


def test_rpg_roll_audit_orm_turn_id_fk_no_cascade() -> None:
    """RpgRollAuditORM.turn_id FK has ondelete=None (no CASCADE)."""
    col = RpgRollAuditORM.__table__.c.turn_id
    fk = next(iter(col.foreign_keys))
    assert fk.ondelete is None


# ---------------------------------------------------------------------------
# Migration FK: alembic upgrade head — PRAGMA confirms no CASCADE on turn_id
# ---------------------------------------------------------------------------


def test_rpg_roll_audit_migration_turn_id_fk_no_cascade() -> None:
    """After alembic upgrade head, rpg_roll_audit.turn_id on_delete != CASCADE."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        from alembic.config import Config

        from alembic import command

        ini_path = os.path.join(os.path.dirname(__file__), "..", "..", "alembic.ini")
        cfg = Config(ini_path)
        cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
        command.upgrade(cfg, "head")

        engine = sa.create_engine(f"sqlite:///{db_path}")
        with engine.connect() as conn:
            rows = conn.execute(
                sa.text("PRAGMA foreign_key_list('rpg_roll_audit')")
            ).fetchall()
        engine.dispose()

        # Column positions: id(0), seq(1), table(2), from(3), to(4), on_update(5),
        # on_delete(6), match(7)
        turn_fk_rows = [r for r in rows if r[3] == "turn_id"]
        assert len(turn_fk_rows) == 1, "Expected exactly one FK on turn_id"
        on_del = turn_fk_rows[0][6]
        assert on_del != "CASCADE", f"turn_id on_delete must not be CASCADE: {on_del!r}"
    finally:
        os.unlink(db_path)


# ---------------------------------------------------------------------------
# Behavioral: delete Turn with committed audit rows raises IntegrityError (FK)
# ---------------------------------------------------------------------------


def test_delete_audited_turn_raises_integrity_error(session) -> None:  # type: ignore[no-untyped-def]
    """FK blocks Turn deletion: IntegrityError (not the trigger's abort message)."""
    from afterworlds.persistence.orm.node import TurnORM

    turn_id = _make_turn(session)
    session.add(_make_audit_row(turn_id))
    session.commit()

    row = session.get(TurnORM, turn_id)
    assert row is not None
    session.delete(row)
    with pytest.raises(IntegrityError) as exc_info:
        session.flush()
    assert (
        "append-only" not in str(exc_info.value).lower()
    ), "Expected FK IntegrityError, not append-only trigger message"


# ---------------------------------------------------------------------------
# Behavioral: direct DELETE on rpg_roll_audit blocked by trigger
# ---------------------------------------------------------------------------


def test_direct_delete_rpg_roll_audit_blocked_by_trigger(session) -> None:  # type: ignore[no-untyped-def]
    """Direct DELETE on rpg_roll_audit is aborted by the append-only trigger."""
    turn_id = _make_turn(session)
    session.add(_make_audit_row(turn_id))
    session.commit()

    with pytest.raises(IntegrityError, match="append-only"):
        session.execute(sa.text("DELETE FROM rpg_roll_audit"))


# ---------------------------------------------------------------------------
# Behavioral: transaction rollback removes uncommitted Turn + audit rows
# ---------------------------------------------------------------------------


def test_transaction_rollback_removes_uncommitted_audit_rows(session) -> None:  # type: ignore[no-untyped-def]
    """Rollback removes uncommitted Turn and audit rows without hitting the trigger."""
    from afterworlds.persistence.crud.story import create_story

    story = make_story()
    create_story(session, story)  # type: ignore[arg-type]
    turn = Turn(
        user_input="test",
        assistant_output="test",
        timestamp=_NOW,
        intent_classification=IntentType.IN_CHARACTER_ACTION,
        node_id=None,
    )
    create_turn(session, turn)  # type: ignore[arg-type]
    session.flush()  # Turn row visible within transaction but not committed

    turn_id = str(turn.turn_id)
    audit_row = _make_audit_row(turn_id)
    session.add(audit_row)
    session.flush()  # audit row visible within transaction

    session.rollback()  # neither Turn nor audit row should persist

    from afterworlds.persistence.orm.node import TurnORM

    assert session.get(TurnORM, turn_id) is None
    count = session.execute(
        sa.text("SELECT COUNT(*) FROM rpg_roll_audit WHERE turn_id = :tid"),
        {"tid": turn_id},
    ).scalar()
    assert count == 0
