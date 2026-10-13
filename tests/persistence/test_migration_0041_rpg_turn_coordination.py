"""Migration 0041 (CRD Issue 15c): actor-turn coordination and its edge log.
Create-only, on temporary stores; never a shared store."""

from __future__ import annotations

from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic.config import Config

import afterworlds.persistence.orm.dnd5e_state  # noqa: F401
from afterworlds.persistence.orm.base import Base
from alembic import command

_REPO = Path(__file__).resolve().parents[2]
_NEW = ("rpg_turn_coordination", "rpg_turn_edges")
_STORY = (
    "INSERT INTO stories (story_id, title, mode, created_at, updated_at) "
    "VALUES ('s1', 't', 'rpg', 'now', 'now')"
)


def _cfg(db: Path) -> Config:
    cfg = Config(str(_REPO / "alembic.ini"))
    cfg.set_main_option("script_location", str(_REPO / "alembic"))
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db.as_posix()}")
    return cfg


def _tables(db: Path) -> dict[str, list[str]]:
    engine = sa.create_engine(f"sqlite:///{db.as_posix()}")
    inspector = sa.inspect(engine)
    out = {
        t: sorted(c["name"] for c in inspector.get_columns(t))
        for t in inspector.get_table_names()
    }
    engine.dispose()
    return out


def _execute(db: Path, *sql: str) -> None:
    engine = sa.create_engine(f"sqlite:///{db.as_posix()}")
    with engine.begin() as conn:
        for statement in sql:
            conn.execute(sa.text(statement))
    engine.dispose()


def _edge(sequence: int, kind: str = "begin") -> str:
    return (
        "INSERT INTO rpg_turn_edges (edge_id, story_id, sequence, turn_id, kind,"
        " subject_kind, subject_id, turn_instance, coordination_revision,"
        f" recorded_at) VALUES ('e{sequence}{kind}', 's1', {sequence}, 't1',"
        f" '{kind}', 'character', 'c1', 1, 0, 'now')"
    )


def test_upgrade_creates_the_orm_tables_and_downgrade_removes_them(
    tmp_path: Path,
) -> None:
    db = tmp_path / "store.db"
    command.upgrade(_cfg(db), "0040")
    before = _tables(db)
    command.upgrade(_cfg(db), "0041")
    after = _tables(db)
    for table in _NEW:
        assert after[table] == sorted(
            c.name for c in Base.metadata.tables[table].columns
        ), table
    assert {t: c for t, c in after.items() if t not in _NEW} == before
    command.downgrade(_cfg(db), "0040")
    assert _tables(db) == before


def test_the_edge_log_enforces_its_sequence_and_kind(tmp_path: Path) -> None:
    db = tmp_path / "store.db"
    command.upgrade(_cfg(db), "head")
    _execute(db, _STORY, _edge(1))
    with pytest.raises(sa.exc.IntegrityError):
        _execute(db, _edge(1, "end"))
    with pytest.raises(sa.exc.IntegrityError):
        _execute(db, _edge(2, "round"))
