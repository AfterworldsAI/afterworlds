"""Engine factory and PRAGMA setup for SQLite."""

from __future__ import annotations

import sqlite3
from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import Session, sessionmaker


def _set_sqlite_pragmas(
    dbapi_connection: Any, connection_record: Any  # noqa: ARG001
) -> None:
    """Enable foreign keys and WAL mode on every new SQLite connection."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.execute("PRAGMA journal_mode = WAL")
    cursor.close()


def create_engine(url: str, **kwargs: Any) -> sa.Engine:
    """Create a SQLAlchemy engine with SQLite-appropriate PRAGMA settings.

    ``PRAGMA foreign_keys = ON`` and ``PRAGMA journal_mode = WAL`` are
    applied via a connection event listener so they apply to every new
    connection, not just the first one.
    """
    engine = sa.create_engine(url, **kwargs)
    sa.event.listen(engine, "connect", _set_sqlite_pragmas)
    return engine


def create_session_factory(engine: sa.Engine) -> sessionmaker[Session]:
    """Return a configured :class:`sessionmaker` bound to *engine*."""
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


def ensure_physical_transaction(session: Session) -> None:
    """Guarantee that SQLite has actually issued ``BEGIN`` for *session*.

    ``sqlite3`` is used here with its legacy transaction control, so the driver
    opens a transaction implicitly only before ``INSERT``/``UPDATE``/``DELETE``/
    ``REPLACE``. A session that has so far only read is logically inside a
    SQLAlchemy transaction while the connection is still in **autocommit** at the
    SQLite level, and the two disagreeing is not merely cosmetic:

    * ``SAVEPOINT`` issued in autocommit *starts* a transaction, and releasing
      that outermost savepoint therefore **commits** it. Work a caller believed
      was pending in its own transaction is durable the moment the savepoint is
      released, and a later ``rollback()`` — even one from an explicit
      ``with session.begin():`` — cannot take it back.
    * SQLAlchemy's logical transaction state does not tell you which case you are
      in, so this checks the DBAPI connection itself rather than inferring it.

    Emitting ``BEGIN`` first makes any subsequent savepoint genuinely nested:
    release stops committing, and the enclosing transaction owns the commit
    boundary as callers already assume. The statement goes through the same
    connection SQLAlchemy is using, and ``sqlite3`` tracks the resulting
    transaction through ``sqlite3_get_autocommit``, so ``commit()`` and
    ``rollback()`` continue to behave normally.

    A no-op on any other driver, and on a session that has already written:
    those have a physical transaction open already. Deliberately scoped to the
    call sites that need it rather than applied engine-wide — making every
    SQLAlchemy transaction physical would change lock acquisition for every
    service and migration in the repository, which is a far wider change than
    the guarantee it buys here.
    """
    connection = session.connection()
    raw = connection.connection.dbapi_connection
    if isinstance(raw, sqlite3.Connection) and not raw.in_transaction:
        connection.exec_driver_sql("BEGIN")
