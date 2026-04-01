"""Engine factory and PRAGMA setup for SQLite."""

from __future__ import annotations

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
