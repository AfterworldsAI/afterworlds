"""CRD Issue 22: the guarded lifecycle exception to append-only history.

Ordinary DELETE and every UPDATE on a guarded table stay refused; only
``operations.lifecycle.dispose_rows`` removes rows, and its grants never
outlive the transaction."""

from __future__ import annotations

from pathlib import Path

import pytest
import sqlalchemy as sa
from sqlalchemy.exc import DatabaseError

from afterworlds.api.db_bootstrap import upgrade_to_head
from afterworlds.operations.lifecycle import GUARDED_TABLES, dispose_rows
from afterworlds.operations.orm import OperationsBase
from afterworlds.remote.control_store import upgrade_control_to_head

SRC = Path(__file__).resolve().parents[2] / "src" / "afterworlds"


def _content(tmp_path: Path) -> sa.Engine:
    url = f"sqlite:///{tmp_path / 'content.db'}"
    upgrade_to_head(url)
    return sa.create_engine(url)


def _refusal(conn: sa.Connection, row_id: int) -> None:
    conn.execute(
        sa.text(
            "INSERT INTO provider_refusal_log (id, turn_id, sojourner_id, pass_id,"
            " primary_provider_name, primary_model_identifier, refusal_category,"
            " fallback_outcome, created_at) VALUES (:id, NULL, 's', 'writer',"
            " 'anthropic', 'm', 'policy', 'none', '2026-01-01 00:00:00')"
        ),
        {"id": row_id},
    )


def test_ordinary_delete_and_update_stay_refused(tmp_path: Path) -> None:
    engine = _content(tmp_path)
    with engine.begin() as conn:
        _refusal(conn, 1)
    for statement in (
        "DELETE FROM provider_refusal_log",
        "UPDATE provider_refusal_log SET pass_id = 'x'",
    ):
        with pytest.raises(DatabaseError, match="append-only"), engine.begin() as c:
            c.execute(sa.text(statement))
    with engine.connect() as conn:
        assert conn.scalar(sa.text("SELECT count(*) FROM provider_refusal_log")) == 1


def test_dispose_rows_removes_only_granted_rows_and_leaves_no_grant(
    tmp_path: Path,
) -> None:
    engine = _content(tmp_path)
    with engine.begin() as conn:
        _refusal(conn, 1)
        _refusal(conn, 2)
    with sa.orm.Session(engine) as session:
        removed = dispose_rows(session, "provider_refusal_log", sa.column("id") == 1)
        session.commit()
    assert removed == 1
    with engine.connect() as conn:
        assert conn.scalar(sa.text("SELECT id FROM provider_refusal_log")) == 2
        assert (
            conn.scalar(sa.text("SELECT count(*) FROM lifecycle_disposal_grants")) == 0
        )
    with pytest.raises(DatabaseError, match="append-only"), engine.begin() as conn:
        conn.execute(sa.text("DELETE FROM provider_refusal_log"))


def test_rolled_back_disposal_removes_nothing(tmp_path: Path) -> None:
    engine = _content(tmp_path)
    with engine.begin() as conn:
        _refusal(conn, 1)
    with sa.orm.Session(engine) as session:
        dispose_rows(session, "provider_refusal_log", sa.column("id") == 1)
        session.rollback()
    with engine.connect() as conn:
        assert conn.scalar(sa.text("SELECT count(*) FROM provider_refusal_log")) == 1


def test_every_guarded_table_has_a_guarded_trigger(tmp_path: Path) -> None:
    content = _content(tmp_path)
    control_url = f"sqlite:///{tmp_path / 'control.db'}"
    upgrade_control_to_head(control_url)
    sql = []
    for engine in (content, sa.create_engine(control_url)):
        with engine.connect() as conn:
            sql += list(
                conn.scalars(
                    sa.text("SELECT sql FROM sqlite_master WHERE type='trigger'")
                )
            )
    for table in GUARDED_TABLES:
        deletes = [s for s in sql if f"BEFORE DELETE ON {table}" in s]
        assert deletes and all("lifecycle_disposal_grants" in s for s in deletes), table
        assert any(f"BEFORE UPDATE ON {table}" in s for s in sql), table


def test_orm_matches_both_chains(tmp_path: Path) -> None:
    content = _content(tmp_path)
    control_url = f"sqlite:///{tmp_path / 'control.db'}"
    upgrade_control_to_head(control_url)
    for engine in (content, sa.create_engine(control_url)):
        inspector = sa.inspect(engine)
        for table in OperationsBase.metadata.sorted_tables:
            migrated = {c["name"] for c in inspector.get_columns(table.name)}
            assert migrated == set(table.columns.keys()), table.name


def test_only_the_lifecycle_module_writes_grants() -> None:
    allowed = {
        SRC / "operations" / "lifecycle.py",
        SRC / "operations" / "schema.py",
        SRC / "operations" / "orm.py",
    }
    writers = [
        p
        for p in SRC.rglob("*.py")
        if "lifecycle_disposal_grants" in p.read_text(encoding="utf-8")
        and p not in allowed
        and "migrations" not in p.parts
    ]
    assert writers == []
