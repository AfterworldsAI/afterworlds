"""Tests verifying SQLite PRAGMA settings are applied correctly."""

from __future__ import annotations

import afterworlds.persistence.orm.character_sheet  # noqa: F401
import afterworlds.persistence.orm.node  # noqa: F401
import afterworlds.persistence.orm.session_state  # noqa: F401
import afterworlds.persistence.orm.state  # noqa: F401
import afterworlds.persistence.orm.story  # noqa: F401
from afterworlds.persistence.database import create_engine
from afterworlds.persistence.orm.base import Base


def test_foreign_keys_pragma_on() -> None:
    """PRAGMA foreign_keys must be ON for every connection."""
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with engine.connect() as conn:
        result = conn.execute(__import__("sqlalchemy").text("PRAGMA foreign_keys"))
        value = result.scalar()
    engine.dispose()
    assert value == 1


def test_journal_mode_wal() -> None:
    """PRAGMA journal_mode must be WAL for every connection."""
    import os
    import tempfile

    # WAL mode only works with file-based databases
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(engine)
        with engine.connect() as conn:
            result = conn.execute(__import__("sqlalchemy").text("PRAGMA journal_mode"))
            value = result.scalar()
        engine.dispose()
        assert value == "wal"
    finally:
        os.unlink(db_path)


def test_foreign_keys_pragma_on_fresh_connection() -> None:
    """PRAGMA foreign_keys must be ON on each new connection (not just first)."""
    import sqlalchemy as sa

    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)

    # Check multiple raw connections
    for _ in range(3):
        with engine.connect() as conn:
            result = conn.execute(sa.text("PRAGMA foreign_keys"))
            value = result.scalar()
            assert value == 1, "foreign_keys must be ON on every connection"

    engine.dispose()
