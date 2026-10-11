"""Migration 0038 (CRD Issue 2b): empty stores only, in both directions."""

from __future__ import annotations

from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic.config import Config

from afterworlds.persistence.orm.base import Base
from alembic import command

_REPO = Path(__file__).resolve().parents[2]
_RETIRED = ("dnd5e_character_sheets", "dnd5e_active_conditions")
_NEW = (
    "dnd5e_character_states",
    "rpg_parties",
    "dnd5e_creatures",
    "dnd5e_creature_associations",
    "dnd5e_item_instances",
    "dnd5e_binding_history",
    "dnd5e_adoption_requests",
    "rpg_turn_leases",
    "rp_mech_shared_changes",
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


def _execute(db: Path, sql: str) -> None:
    engine = sa.create_engine(f"sqlite:///{db.as_posix()}")
    with engine.begin() as conn:
        conn.execute(sa.text(sql))
    engine.dispose()


_STORY = (
    "INSERT INTO stories (story_id, title, mode, created_at, updated_at) "
    "VALUES ('s1', 't', 'rpg', 'now', 'now')"
)


def test_an_empty_store_upgrades_and_downgrades_and_upgrades_again(
    tmp_path: Path,
) -> None:
    db = tmp_path / "empty.db"
    command.upgrade(_cfg(db), "0037")
    before = _tables(db)
    command.upgrade(_cfg(db), "0038")
    after = _tables(db)
    assert set(_RETIRED).isdisjoint(after)
    assert set(_NEW) <= set(after)
    assert "rules_package_id" not in after["rpg_character_sheet_bases"]
    command.downgrade(_cfg(db), "0037")
    assert _tables(db) == before
    command.upgrade(_cfg(db), "head")
    assert set(_NEW) <= set(_tables(db))


def test_the_head_schema_is_the_orm_for_every_2b_table(tmp_path: Path) -> None:
    import afterworlds.persistence.orm.character_sheet  # noqa: F401
    import afterworlds.persistence.orm.rules_authority  # noqa: F401

    db = tmp_path / "head.db"
    command.upgrade(_cfg(db), "head")
    installed = _tables(db)
    for table in (*_NEW, "rpg_character_sheet_bases"):
        assert installed[table] == sorted(
            c.name for c in Base.metadata.tables[table].columns
        ), table


def test_a_populated_predecessor_store_refuses_to_upgrade(tmp_path: Path) -> None:
    db = tmp_path / "populated.db"
    command.upgrade(_cfg(db), "0037")
    _execute(db, _STORY)
    _execute(
        db,
        "INSERT INTO rpg_character_sheet_bases "
        "(sheet_id, story_id, rules_package_id, character_name, created_at,"
        " updated_at) "
        "VALUES ('c1', 's1', 'dnd5e', 'Ilse', 'now', 'now')",
    )
    with pytest.raises(RuntimeError, match="empty stores only"):
        command.upgrade(_cfg(db), "0038")
    assert "dnd5e_character_sheets" in _tables(db)  # nothing converted, nothing dropped


def test_a_populated_2b_store_refuses_to_downgrade(tmp_path: Path) -> None:
    db = tmp_path / "head-populated.db"
    command.upgrade(_cfg(db), "head")
    _execute(db, _STORY)
    _execute(
        db,
        "INSERT INTO rpg_parties (party_id, story_id, label, created_at) "
        "VALUES ('p1', 's1', 'Company', 'now')",
    )
    with pytest.raises(RuntimeError, match="empty stores only"):
        command.downgrade(_cfg(db), "0037")
    assert "rpg_parties" in _tables(db)
