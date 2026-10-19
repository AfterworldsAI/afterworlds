"""Migration 0039 (#44): Story Bible secondary indexes, rows untouched."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import sqlalchemy as sa
from alembic import command
from alembic.config import Config

import afterworlds.persistence.orm.story  # noqa: F401
import afterworlds.persistence.orm.story_bible  # noqa: F401
from afterworlds.persistence.orm.base import Base

_REPO = Path(__file__).resolve().parents[2]
_EXPECTED = {
    ("sb_settings", "ix_sb_settings_story_id", ("story_id",)),
    ("sb_cast_entries", "ix_sb_cast_entries_story_id", ("story_id",)),
    ("sb_locked_facts", "ix_sb_locked_facts_story_id", ("story_id",)),
    ("sb_forbidden_facts", "ix_sb_forbidden_facts_story_id", ("story_id",)),
    ("sb_events", "ix_sb_events_story_id", ("story_id",)),
    ("sb_relationship_ledger", "ix_sb_relationship_ledger_story_id", ("story_id",)),
    ("sb_unresolved_threads", "ix_sb_unresolved_threads_story_id", ("story_id",)),
    ("sb_provisional_staging", "ix_sb_provisional_staging_story_id", ("story_id",)),
    (
        "sb_dynamic_field_history",
        "ix_sb_dynamic_field_history_entity",
        ("entity_type", "entity_id"),
    ),
}
_SB_TABLES = sorted({table for table, _, _ in _EXPECTED})
_ROWS = (
    "INSERT INTO stories (story_id, title, mode, created_at, updated_at) "
    "VALUES ('s1', 't', 'rpg', 'now', 'now')",
    "INSERT INTO sb_settings (setting_id, story_id, summary, world_rules,"
    " is_active, created_at) VALUES ('st1', 's1', 'a city', '[\"r\"]', 1, 'now')",
    "INSERT INTO sb_cast_entries (cast_id, story_id, static_name, static_role,"
    " static_traits, static_goals, static_secrets, dynamic_is_alive, is_active,"
    " created_at) VALUES ('c1', 's1', 'Ilse', 'protagonist', '[]', '[]', '[]',"
    " 1, 1, 'now')",
    "INSERT INTO sb_locked_facts (locked_fact_id, story_id, fact_text, is_active,"
    " created_at) VALUES ('l1', 's1', 'sky is red', 1, 'now')",
    "INSERT INTO sb_forbidden_facts (forbidden_fact_id, story_id, fact_text,"
    " source, is_active, created_at) VALUES ('f1', 's1', 'no dragons', 'owner',"
    " 1, 'now')",
    "INSERT INTO sb_events (event_id, story_id, description, significance,"
    " is_active, created_at) VALUES ('e1', 's1', 'arrived', 'major', 1, 'now')",
    "INSERT INTO sb_relationship_ledger (relationship_id, story_id,"
    " subject_cast_id, object_cast_id, relationship_type, is_active, created_at,"
    " updated_at) VALUES ('r1', 's1', 'c1', 'c1', 'self', 1, 'now', 'now')",
    "INSERT INTO sb_unresolved_threads (thread_id, story_id, description, status,"
    " is_active, created_at) VALUES ('t1', 's1', 'who?', 'open', 1, 'now')",
    "INSERT INTO sb_provisional_staging (proposal_id, story_id, proposal_type,"
    " proposed_value, status, requires_confirmation, is_active, created_at)"
    " VALUES ('p1', 's1', 'soft_fact', '{}', 'pending', 0, 1, 'now')",
    "INSERT INTO sb_dynamic_field_history (history_id, entity_type, entity_id,"
    " field_name, old_value, changed_at) VALUES ('h1', 'cast', 'c1',"
    " 'current_location', 'gate', 'now')",
)


def _cfg(db: Path) -> Config:
    cfg = Config(str(_REPO / "alembic.ini"))
    cfg.set_main_option(
        "script_location", str(_REPO / "src" / "afterworlds" / "migrations" / "content")
    )
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db.as_posix()}")
    return cfg


def _indexes(db: Path) -> set[tuple[str, str, tuple[str, ...], bool]]:
    engine = sa.create_engine(f"sqlite:///{db.as_posix()}")
    inspector = sa.inspect(engine)
    out = {
        (table, ix["name"], tuple(ix["column_names"]), bool(ix["unique"]))
        for table in inspector.get_table_names()
        for ix in inspector.get_indexes(table)
    }
    engine.dispose()
    return out


def _rows(db: Path) -> dict[str, list[Any]]:
    engine = sa.create_engine(f"sqlite:///{db.as_posix()}")
    with engine.connect() as conn:
        out = {
            table: list(
                conn.execute(
                    sa.text(f"SELECT * FROM {table} ORDER BY rowid")
                )  # noqa: S608
            )
            for table in ("stories", *_SB_TABLES)
        }
    engine.dispose()
    return out


def _sb(indexes: set[tuple[str, str, tuple[str, ...], bool]]) -> set[Any]:
    return {ix for ix in indexes if ix[0] in _SB_TABLES}


def test_a_populated_store_gains_and_loses_only_these_indexes(tmp_path: Path) -> None:
    db = tmp_path / "populated.db"
    command.upgrade(_cfg(db), "0038")
    engine = sa.create_engine(f"sqlite:///{db.as_posix()}")
    with engine.begin() as conn:
        for sql in _ROWS:
            conn.execute(sa.text(sql))
    engine.dispose()
    rows, before = _rows(db), _indexes(db)
    assert all(rows[table] for table in rows)

    command.upgrade(_cfg(db), "0039")
    assert _rows(db) == rows
    added = _indexes(db) - before
    assert added == {(t, n, c, False) for t, n, c in _EXPECTED}
    assert before <= _indexes(db)

    command.downgrade(_cfg(db), "0038")
    assert _rows(db) == rows
    assert _indexes(db) == before

    # Pinned to 0039: this fixture's history row is unowned, which 0040 rejects.
    command.upgrade(_cfg(db), "0039")
    assert _rows(db) == rows
    assert {(t, n, c, False) for t, n, c in _EXPECTED} <= _indexes(db)


def test_migrated_and_orm_created_schemas_carry_the_same_story_bible_indexes(
    tmp_path: Path,
) -> None:
    migrated = tmp_path / "migrated.db"
    command.upgrade(_cfg(migrated), "head")

    created = tmp_path / "created.db"
    engine = sa.create_engine(f"sqlite:///{created.as_posix()}")
    Base.metadata.create_all(
        engine,
        tables=[Base.metadata.tables[t] for t in ("stories", *_SB_TABLES)],
    )
    engine.dispose()

    expected = {(t, n, c, False) for t, n, c in _EXPECTED}
    assert _sb(_indexes(migrated)) == expected
    assert _sb(_indexes(created)) == expected
