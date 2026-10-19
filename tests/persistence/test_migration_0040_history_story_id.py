"""Migration 0040 (#50): durable story_id on sb_dynamic_field_history."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config

import afterworlds.persistence.orm.story  # noqa: F401
import afterworlds.persistence.orm.story_bible  # noqa: F401
from afterworlds.persistence.orm.base import Base

_REPO = Path(__file__).resolve().parents[2]
_TABLE = "sb_dynamic_field_history"
_SEED = (
    "INSERT INTO stories (story_id, title, mode, created_at, updated_at) VALUES"
    " ('s1', 't', 'rpg', 'now', 'now'), ('s2', 't', 'rpg', 'now', 'now')",
    "INSERT INTO sb_cast_entries (cast_id, story_id, static_name, static_role,"
    " static_traits, static_goals, static_secrets, dynamic_is_alive, is_active,"
    " created_at) VALUES ('c1', 's1', 'A', 'protagonist', '[]', '[]', '[]', 1, 1,"
    " 'now'), ('c2', 's2', 'B', 'protagonist', '[]', '[]', '[]', 1, 0, 'now')",
    "INSERT INTO sb_relationship_ledger (relationship_id, story_id,"
    " subject_cast_id, object_cast_id, relationship_type, is_active, created_at,"
    " updated_at) VALUES ('r2', 's2', 'c2', 'c2', 'self', 1, 'now', 'now')",
    "INSERT INTO sb_dynamic_field_history (history_id, entity_type, entity_id,"
    " field_name, old_value, changed_at) VALUES"
    " ('h1', 'cast_entry', 'c1', 'current_location', '\"gate\"', 'now'),"
    " ('h2', 'cast_entry', 'c2', 'is_alive', 'true', 'now'),"
    " ('h3', 'relationship_ledger', 'r2', 'current_status_description', NULL,"
    " 'now')",
)
_ORPHANS = (
    "INSERT INTO sb_dynamic_field_history (history_id, entity_type, entity_id,"
    " field_name, old_value, changed_at) VALUES"
    " ('h4', 'cast_entry', 'gone', 'current_location', NULL, 'now'),"
    " ('h5', 'cast', 'c1', 'current_location', NULL, 'now')",
)


def _cfg(db: Path) -> Config:
    cfg = Config(str(_REPO / "alembic.ini"))
    cfg.set_main_option(
        "script_location", str(_REPO / "src" / "afterworlds" / "migrations" / "content")
    )
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db.as_posix()}")
    return cfg


def _execute(db: Path, *sql: str) -> None:
    engine = sa.create_engine(f"sqlite:///{db.as_posix()}")
    with engine.begin() as conn:
        for statement in sql:
            conn.execute(sa.text(statement))
    engine.dispose()


def _seeded(db: Path, *sql: str) -> Path:
    command.upgrade(_cfg(db), "0039")
    _execute(db, *_SEED, *sql)
    return db


def _schema(db: Path) -> dict[str, Any]:
    engine = sa.create_engine(f"sqlite:///{db.as_posix()}")
    inspector = sa.inspect(engine)
    out = {
        "columns": {
            c["name"]: (str(c["type"]), c["nullable"])
            for c in inspector.get_columns(_TABLE)
        },
        "fks": inspector.get_foreign_keys(_TABLE),
        "indexes": sorted(
            (ix["name"], tuple(ix["column_names"]), bool(ix["unique"]))
            for ix in inspector.get_indexes(_TABLE)
        ),
    }
    engine.dispose()
    return out


def _snapshot(db: Path) -> dict[str, Any]:
    engine = sa.create_engine(f"sqlite:///{db.as_posix()}")
    with engine.connect() as conn:
        version = conn.execute(sa.text("SELECT version_num FROM alembic_version"))
        rows = conn.execute(sa.text(f"SELECT * FROM {_TABLE}"))  # noqa: S608
        out = {
            **_schema(db),
            "version": version.scalar(),
            "rows": {r.history_id: dict(r._mapping) for r in rows},
        }
    engine.dispose()
    return out


def test_populated_upgrade_backfills_owner_and_downgrade_restores(
    tmp_path: Path,
) -> None:
    db = _seeded(tmp_path / "populated.db")
    before = _snapshot(db)

    command.upgrade(_cfg(db), "0040")
    after = _snapshot(db)
    assert {h: r["story_id"] for h, r in after["rows"].items()} == {
        "h1": "s1",
        "h2": "s2",  # soft-deleted owner still owns its history
        "h3": "s2",
    }
    assert {h: {**r, "story_id": None} for h, r in after["rows"].items()} == {
        h: {**r, "story_id": None} for h, r in before["rows"].items()
    }
    assert after["columns"]["story_id"] == ("VARCHAR(36)", False)
    assert after["fks"] == []
    assert after["indexes"] == before["indexes"]

    command.downgrade(_cfg(db), "0039")
    assert _snapshot(db) == before


def test_unresolvable_owner_fails_visibly_and_changes_nothing(
    tmp_path: Path,
) -> None:
    db = _seeded(tmp_path / "orphans.db", *_ORPHANS)
    before = _snapshot(db)

    with pytest.raises(RuntimeError, match=r"2 sb_dynamic_field_history") as err:
        command.upgrade(_cfg(db), "head")
    assert "h4 (cast_entry gone)" in str(err.value)
    assert "h5 (cast c1)" in str(err.value)
    assert _snapshot(db) == before
    assert before["version"] == "0039"
    assert "story_id" not in before["columns"]


def test_migrated_and_orm_created_history_schemas_match(tmp_path: Path) -> None:
    migrated = tmp_path / "migrated.db"
    command.upgrade(_cfg(migrated), "head")

    created = tmp_path / "created.db"
    engine = sa.create_engine(f"sqlite:///{created.as_posix()}")
    Base.metadata.create_all(engine, tables=[Base.metadata.tables[_TABLE]])
    engine.dispose()

    assert _schema(migrated) == _schema(created)
    assert _schema(created)["columns"]["story_id"] == ("VARCHAR(36)", False)
    assert _schema(created)["fks"] == []
