"""``ensure_physical_transaction`` — the driver behaviour it exists to correct.

``sqlite3`` is used with its legacy transaction control, which opens a
transaction implicitly only before ``INSERT``/``UPDATE``/``DELETE``/``REPLACE``.
A session that has only read is therefore inside a SQLAlchemy transaction while
the connection is still in SQLite autocommit — and a ``SAVEPOINT`` opened there
is the *outermost* one, so releasing it commits.

These are characterization tests as much as unit tests: the first pair pins the
driver behaviour the helper depends on, so if a future Python, SQLAlchemy, or
driver-configuration change removes it, the reason this helper exists fails
loudly here rather than silently somewhere downstream.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Session, sessionmaker

from afterworlds.persistence.database import (
    create_engine,
    create_session_factory,
    ensure_physical_transaction,
)


@pytest.fixture()
def factory(tmp_path: Path) -> sessionmaker[Session]:
    """A file-backed engine, so separate sessions are genuinely separate.

    An in-memory URL would hand every session the same connection, which is
    exactly what these tests must not do: "visible elsewhere" is the whole
    assertion.
    """
    engine = create_engine(f"sqlite:///{tmp_path / 'txn.db'}")
    with engine.begin() as conn:
        conn.exec_driver_sql("CREATE TABLE t (k TEXT PRIMARY KEY)")
    return create_session_factory(engine)


def _raw(session: Session) -> sqlite3.Connection:
    connection = session.connection().connection.dbapi_connection
    assert isinstance(connection, sqlite3.Connection)
    return connection


def _visible(factory: sessionmaker[Session]) -> int:
    with factory() as other:
        return int(other.execute(sa.text("SELECT COUNT(*) FROM t")).scalar_one())


def test_a_read_only_session_is_not_yet_in_a_physical_transaction(
    factory: sessionmaker[Session],
) -> None:
    """The premise: SQLAlchemy's logical state does not imply a real BEGIN."""
    with factory() as session:
        session.execute(sa.text("SELECT COUNT(*) FROM t"))
        assert session.in_transaction(), "SQLAlchemy considers itself in one"
        assert not _raw(session).in_transaction, "SQLite does not"


def test_ensure_opens_one_and_is_idempotent(factory: sessionmaker[Session]) -> None:
    """Twice must be safe — SQLite refuses a transaction within a transaction."""
    with factory() as session:
        session.execute(sa.text("SELECT COUNT(*) FROM t"))
        ensure_physical_transaction(session)
        assert _raw(session).in_transaction
        ensure_physical_transaction(session)
        assert _raw(session).in_transaction


def test_ensure_is_a_no_op_once_the_session_has_written(
    factory: sessionmaker[Session],
) -> None:
    """A writing session already has one; issuing a second BEGIN would raise."""
    with factory() as session:
        session.execute(sa.text("INSERT INTO t VALUES ('pre')"))
        assert _raw(session).in_transaction
        ensure_physical_transaction(session)
        session.rollback()
    assert _visible(factory) == 0


def test_without_it_releasing_a_savepoint_commits(
    factory: sessionmaker[Session],
) -> None:
    """The defect, pinned. Not a recommendation — a property being relied upon.

    A savepoint opened in autocommit is the outermost one, so releasing it ends
    the transaction it implicitly started. The caller's later rollback has
    nothing left to undo.
    """
    with factory() as session:
        session.execute(sa.text("SELECT COUNT(*) FROM t"))
        with session.begin_nested():
            session.execute(sa.text("INSERT INTO t VALUES ('a')"))
        session.rollback()
    assert _visible(factory) == 1


def test_with_it_the_savepoint_is_genuinely_nested(
    factory: sessionmaker[Session],
) -> None:
    """The correction: the enclosing transaction owns the commit boundary."""
    with factory() as session:
        session.execute(sa.text("SELECT COUNT(*) FROM t"))
        ensure_physical_transaction(session)
        with session.begin_nested():
            session.execute(sa.text("INSERT INTO t VALUES ('a')"))
        session.rollback()
    assert _visible(factory) == 0


def test_it_does_not_take_over_the_commit(factory: sessionmaker[Session]) -> None:
    """Committing still works, and the connection returns to autocommit."""
    with factory() as session:
        session.execute(sa.text("SELECT COUNT(*) FROM t"))
        ensure_physical_transaction(session)
        with session.begin_nested():
            session.execute(sa.text("INSERT INTO t VALUES ('a')"))
        session.commit()
        assert not _raw(session).in_transaction
    assert _visible(factory) == 1
