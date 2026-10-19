"""Migration 0042 (CRD Issue 15c): the kind of a held tool. On temporary
stores only; never a shared store."""

from __future__ import annotations

from pathlib import Path

import sqlalchemy as sa
from alembic import command
from alembic.config import Config

import afterworlds.persistence.orm.dnd5e_state  # noqa: F401
from afterworlds.persistence.orm.base import Base

_REPO = Path(__file__).resolve().parents[2]
_TABLE = "dnd5e_item_instances"


def _cfg(db: Path) -> Config:
    cfg = Config(str(_REPO / "alembic.ini"))
    cfg.set_main_option(
        "script_location", str(_REPO / "src" / "afterworlds" / "migrations" / "content")
    )
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db.as_posix()}")
    return cfg


def _shape(db: Path) -> tuple[list[str], list[str], list[str]]:
    engine = sa.create_engine(f"sqlite:///{db.as_posix()}")
    inspector = sa.inspect(engine)
    shape = (
        sorted(c["name"] for c in inspector.get_columns(_TABLE)),
        sorted(str(c["name"]) for c in inspector.get_check_constraints(_TABLE)),
        sorted(str(k["referred_table"]) for k in inspector.get_foreign_keys(_TABLE)),
    )
    engine.dispose()
    return shape


def test_upgrade_adds_the_orm_column_and_downgrade_restores_the_table(
    tmp_path: Path,
) -> None:
    db = tmp_path / "store.db"
    command.upgrade(_cfg(db), "0041")
    before = _shape(db)
    command.upgrade(_cfg(db), "0042")
    after = _shape(db)
    assert after[0] == sorted(c.name for c in Base.metadata.tables[_TABLE].columns)
    assert after[0] == sorted([*before[0], "tool_variant"])
    assert after[1:] == before[1:]
    command.downgrade(_cfg(db), "0041")
    assert _shape(db) == before
