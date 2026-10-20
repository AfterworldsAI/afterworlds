"""Migration 0043 — CRD Issue 15b's action-resolution schema (AC34, AC52-54).

Each test migrates a private file-backed SQLite store with the app's own
Alembic chain. Rows are seeded with raw SQL and foreign keys off, so only the
migration's own behaviour is under test.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

_INI = Path(__file__).parents[2] / "alembic.ini"
_LEGACY = {
    "check_label",
    "player_facing_instruction",
    "expected_value_shape",
    "visible_modifier_note",
    "roll_expression",
    "visible_modifier_total",
    "visible_modifier_breakdown_json",
    "hidden_modifier_present",
}
_STRUCTURED = {
    "sequence_id",
    "step_id",
    "instruction_id",
    "instruction_revision",
    "instruction_schema_version",
    "instruction_snapshot_json",
}


@pytest.fixture()
def db(tmp_path: Path) -> Iterator[Path]:
    yield tmp_path / "store.db"


def _cfg(path: Path) -> Config:
    cfg = Config(str(_INI))
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{path}")
    return cfg


def _sql(path: Path, sql: str, *params: object) -> list[tuple[object, ...]]:
    with sqlite3.connect(path) as conn:
        conn.execute("PRAGMA foreign_keys = OFF")
        rows = conn.execute(sql, params).fetchall()
        conn.commit()
        return rows


def _columns(path: Path, table: str) -> dict[str, bool]:
    """Column name → NOT NULL."""
    return {r[1]: bool(r[3]) for r in _sql(path, f"PRAGMA table_info({table})")}  # type: ignore[index, misc]


def _triggers(path: Path) -> set[str]:
    return {
        str(r[0])
        for r in _sql(path, "SELECT name FROM sqlite_master WHERE type = 'trigger'")
    }


def _version(path: Path) -> str:
    return str(_sql(path, "SELECT version_num FROM alembic_version")[0][0])


def _legacy_pending_row(path: Path) -> None:
    """A pending roll in the shipped pre-15b shape."""
    _sql(
        path,
        "INSERT INTO pending_roll_requests (request_id, story_id, session_id,"
        " character_id, originating_turn_id, check_label,"
        " player_facing_instruction, expected_value_shape, visibility,"
        " source_proposal_ref, status, created_at, schema_version,"
        " roll_expression, hidden_modifier_present)"
        " VALUES ('r1', 's1', 'ss1', 'c1', 't1', 'Stealth', 'Roll 1d20',"
        " 'integer', 'player', 'tag/Stealth', 'pending', 'now', 1, '1d20', 0)",
    )


def test_the_upgrade_drops_eight_columns_adds_six_and_creates_the_ledger(
    db: Path,
) -> None:
    command.upgrade(_cfg(db), "head")
    pending = _columns(db, "pending_roll_requests")
    assert not _LEGACY & pending.keys()
    assert pending.keys() >= _STRUCTURED
    assert not any(pending[c] for c in _STRUCTURED)  # nullable at the ORM layer
    sequences = _columns(db, "action_resolution_sequences")
    assert sequences["session_id"]  # NOT NULL from creation (AC52)
    for nullable in (
        "current_pending_roll_request_id",
        "current_decision_request_id",
        "current_decision_snapshot_json",
    ):
        assert not sequences[nullable]
    for required in ("plan_json", "reads_json", "projected_state_json", "revision"):
        assert sequences[required]
    audit = _columns(db, "rpg_roll_audit")
    assert {
        *(_STRUCTURED - {"instruction_schema_version"}),
        "pending_roll_request_id",
        "instruction_schema_version",
        "submission_source",
        "raw_values_complete",
        "contest_resolution_json",
    } <= audit.keys()
    # rpg_roll_audit's own append-only triggers survive (no rebuild).
    assert {
        "prevent_action_resolution_events_update",
        "prevent_action_resolution_events_delete",
    } <= _triggers(db)
    assert any("rpg_roll_audit" in t for t in _triggers(db))


def test_the_event_ledger_refuses_update_and_delete(db: Path) -> None:
    """AC34: append-only at the database layer."""
    command.upgrade(_cfg(db), "head")
    _sql(
        db,
        "INSERT INTO action_resolution_events (event_id, sequence_id, step_id,"
        " story_id, session_id, character_id, event_order, kind,"
        " mechanical_provenance, provisional_effects_json, created_at,"
        " payload_json) VALUES ('e1', 'q1', 'p1', 's1', 'ss1', 'c1', 1,"
        " 'player_roll', '{}', '[]', 'now', '{}')",
    )
    for statement in (
        "UPDATE action_resolution_events SET kind = 'ai_roll'",
        "DELETE FROM action_resolution_events",
    ):
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            _sql(db, statement)
    assert _sql(db, "SELECT kind FROM action_resolution_events") == [("player_roll",)]
    # The order is unique per sequence.
    with pytest.raises(sqlite3.IntegrityError):
        _sql(
            db,
            "INSERT INTO action_resolution_events (event_id, sequence_id, step_id,"
            " story_id, session_id, character_id, event_order, kind,"
            " mechanical_provenance, provisional_effects_json, created_at,"
            " payload_json) VALUES ('e2', 'q1', 'p1', 's1', 'ss1', 'c1', 1,"
            " 'player_roll', '{}', '[]', 'now', '{}')",
        )


@pytest.mark.parametrize("status", ["pending", "consumed"])
def test_a_seeded_pending_row_aborts_the_upgrade_before_any_change(
    db: Path, status: str
) -> None:
    """AC53/AC54 (Owner Decision 15b-36): any existing row, pending or
    consumed and whatever its expression, aborts before any DDL."""
    command.upgrade(_cfg(db), "0042")
    _legacy_pending_row(db)
    _sql(
        db,
        "UPDATE pending_roll_requests SET status = ?, roll_expression = ?",
        status,
        "3d7",
    )
    before = _columns(db, "pending_roll_requests")
    with pytest.raises(RuntimeError, match="15b-36"):
        command.upgrade(_cfg(db), "head")
    assert _version(db) == "0042"
    assert _columns(db, "pending_roll_requests") == before  # no column dropped or added
    assert _sql(db, "SELECT roll_expression, status FROM pending_roll_requests") == [
        ("3d7", status)
    ]
    tables = {
        r[0] for r in _sql(db, "SELECT name FROM sqlite_master WHERE type='table'")
    }
    assert "action_resolution_sequences" not in tables
    assert "action_resolution_events" not in tables


def test_the_empty_schema_round_trips(db: Path) -> None:
    command.upgrade(_cfg(db), "head")
    command.downgrade(_cfg(db), "0042")
    pending = _columns(db, "pending_roll_requests")
    assert pending.keys() >= _LEGACY and not _STRUCTURED & pending.keys()
    assert "contest_resolution_json" not in _columns(db, "rpg_roll_audit")
    assert any("rpg_roll_audit" in t for t in _triggers(db))
    command.upgrade(_cfg(db), "head")
    assert _version(db) == "0046"  # head: CRD Issue 22 operations records


@pytest.mark.parametrize(
    "seed",
    [
        "INSERT INTO pending_roll_requests (request_id, story_id, session_id,"
        " character_id, originating_turn_id, visibility, source_proposal_ref,"
        " status, created_at, schema_version, instruction_id,"
        " instruction_snapshot_json) VALUES ('r1', 's1', 'ss1', 'c1', 't1',"
        " 'player', 'q/0/0', 'pending', 'now', 2, 'i1', '{}')",
        "INSERT INTO action_resolution_events (event_id, sequence_id, step_id,"
        " story_id, session_id, character_id, event_order, kind,"
        " mechanical_provenance, provisional_effects_json, created_at,"
        " payload_json) VALUES ('e1', 'q1', 'p1', 's1', 'ss1', 'c1', 1,"
        " 'player_roll', '{}', '[]', 'now', '{}')",
        "INSERT INTO rpg_roll_audit (turn_id, story_id, session_id, character_id,"
        " check_label, visibility, expression, raw_rolls_json, modifiers_json,"
        " total, outcome, source, gm_cheating_at_roll, sheet_effects_json,"
        " created_at, sequence_id) VALUES ('t1', 's1', 'ss1', 'c1', 'Attack',"
        " 'player', '1d20', '[]', '[]', 16, 'success', 'player', 0, '[]', 'now',"
        " 'q1')",
    ],
    ids=["pending-roll", "event", "linked-audit"],
)
def test_downgrade_refuses_while_lifecycle_data_exists(db: Path, seed: str) -> None:
    """No legacy authority is fabricated for structured provenance: the
    downgrade refuses before any change, leaving rows, columns and triggers."""
    command.upgrade(_cfg(db), "head")
    _sql(db, seed)
    # Later revisions' own downgrades (e.g. CRD Issue 22's 0046 operations
    # tables) run first; the refusal under test is 0043's.
    command.downgrade(_cfg(db), "0043")
    pending, triggers = _columns(db, "pending_roll_requests"), _triggers(db)
    with pytest.raises(RuntimeError, match="Nothing was changed"):
        command.downgrade(_cfg(db), "0042")
    assert _version(db) == "0043"
    assert _columns(db, "pending_roll_requests") == pending
    assert _triggers(db) == triggers
    table = seed.split()[2]
    assert len(_sql(db, f"SELECT 1 FROM {table}")) == 1


def test_one_unresolved_sequence_per_story(db: Path) -> None:
    """15b-18: the partial unique index over active and ready sequences."""
    command.upgrade(_cfg(db), "head")

    def sequence(sequence_id: str, status: str) -> None:
        _sql(
            db,
            "INSERT INTO action_resolution_sequences (sequence_id, story_id,"
            " session_id, node_id, character_id, originating_turn_id, status,"
            " current_interaction_kind, plan_json, reads_json, records_json,"
            " unattached_json, resolved_steps_json, projected_state_json,"
            " provisional_effects_json, revision, created_at, updated_at)"
            " VALUES (?, 's1', 'ss1', 'n1', 'c1', 't1', ?, 'none', '{}', '{}',"
            " '[]', '[]', '[]', '{}', '[]', 1, 'now', 'now')",
            sequence_id,
            status,
        )

    sequence("q1", "completed")
    sequence("q2", "active")
    with pytest.raises(sqlite3.IntegrityError):
        sequence("q3", "ready_for_narration")
    sequence("q4", "completed")
