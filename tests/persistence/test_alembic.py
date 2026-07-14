"""Tests that the Alembic baseline migration runs cleanly."""

from __future__ import annotations

import importlib.util
import json
import os
import tempfile

import pytest


def _load_migration_0013() -> object:
    """Import the 0013 migration module so we can test its helper functions."""
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    migration_path = os.path.join(
        project_root, "alembic", "versions", "0013_writing_mode.py"
    )
    spec = importlib.util.spec_from_file_location("migration_0013", migration_path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def test_alembic_upgrade_head() -> None:
    """alembic upgrade head must run to completion without error."""
    from alembic.config import Config

    from alembic import command

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        ini_path = os.path.join(os.path.dirname(__file__), "..", "..", "alembic.ini")
        cfg = Config(ini_path)
        cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
        # Run the migration — must not raise
        command.upgrade(cfg, "head")

        # Verify tables were created
        import sqlalchemy as sa

        engine = sa.create_engine(f"sqlite:///{db_path}")
        inspector = sa.inspect(engine)
        table_names = inspector.get_table_names()
        engine.dispose()

        expected_tables = [
            "stories",
            "arcs",
            "chapters",
            "nodes",
            "turns",
            "world_states",
            "character_states",
            "rpg_session_states",
            "branching_session_states",
            "writing_session_states",
            "rpg_character_sheet_bases",
            "dnd5e_character_sheets",
            "rpg_roll_audit",
            "pending_roll_requests",
        ]
        for table in expected_tables:
            assert table in table_names, f"Table {table!r} not found after migration"
    finally:
        os.unlink(db_path)


def test_alembic_downgrade_base() -> None:
    """alembic downgrade base must undo all tables."""
    from alembic.config import Config

    from alembic import command

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        ini_path = os.path.join(os.path.dirname(__file__), "..", "..", "alembic.ini")
        cfg = Config(ini_path)
        cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
        command.upgrade(cfg, "head")
        command.downgrade(cfg, "base")

        import sqlalchemy as sa

        engine = sa.create_engine(f"sqlite:///{db_path}")
        inspector = sa.inspect(engine)
        # After downgrade base all application tables should be gone
        # (alembic_version may remain)
        table_names = [t for t in inspector.get_table_names() if t != "alembic_version"]
        engine.dispose()

        assert table_names == [], f"Tables remain after downgrade: {table_names}"
    finally:
        os.unlink(db_path)


# ---------------------------------------------------------------------------
# Migration 0013 — helper unit tests
# ---------------------------------------------------------------------------


class TestMigrationHelpers:
    """Unit tests for the pure-Python helpers in migration 0013."""

    def setup_method(self) -> None:
        self.mod = _load_migration_0013()
        self.to_pointers = self.mod._convert_uuid_strings_to_pointers  # type: ignore[attr-defined]
        self.to_strings = self.mod._convert_pointers_to_uuid_strings  # type: ignore[attr-defined]

    def test_convert_uuid_strings_to_pointers_happy_path(self) -> None:
        """Two UUID strings → two WritingVersionPointer-shaped dicts."""
        raw = json.dumps(
            [
                "aaaaaaaa-0000-0000-0000-000000000001",
                "aaaaaaaa-0000-0000-0000-000000000002",
            ]
        )
        result = json.loads(self.to_pointers(raw))
        assert len(result) == 2
        p0 = result[0]
        assert p0["schema_version"] == 1
        assert p0["pointer_id"] == "aaaaaaaa-0000-0000-0000-000000000001"
        assert p0["kind"] == "draft_label"
        assert "Legacy version pointer" in p0["label"]
        assert p0["source_turn_id"] is None
        assert p0["source_node_id"] is None
        assert "0013" in p0["description"]

    def test_convert_uuid_strings_to_pointers_empty_input(self) -> None:
        """Empty JSON array → empty array (no conversion needed)."""
        assert json.loads(self.to_pointers("[]")) == []

    def test_convert_uuid_strings_to_pointers_null_input(self) -> None:
        """None/null → empty array (no conversion needed)."""
        assert json.loads(self.to_pointers(None)) == []

    def test_convert_uuid_strings_to_pointers_malformed_json(self) -> None:
        """Malformed JSON → safe empty array, no exception."""
        assert json.loads(self.to_pointers("not-json{{")) == []

    def test_convert_uuid_strings_to_pointers_already_dicts_preserved(self) -> None:
        """List of dicts (already converted) → dicts are preserved as-is."""
        already = [
            {"schema_version": 1, "pointer_id": "abc", "kind": "turn", "label": "x"}
        ]
        raw = json.dumps(already)
        result = json.loads(self.to_pointers(raw))
        assert len(result) == 1
        assert result[0]["kind"] == "turn"

    def test_convert_pointers_to_uuid_strings_roundtrip(self) -> None:
        """Convert UUID strings → pointer dicts → back to UUID strings."""
        uuid_str = "aaaaaaaa-0000-0000-0000-000000000099"
        pointer_json = self.to_pointers(json.dumps([uuid_str]))
        recovered = json.loads(self.to_strings(pointer_json))
        assert recovered == [uuid_str]

    def test_converted_pointer_validates_as_writing_version_pointer(self) -> None:
        """A converted pointer dict validates as a WritingVersionPointer model."""
        from afterworlds.pipeline.writing.models import WritingVersionPointer

        uuid_str = "aaaaaaaa-0000-0000-0000-000000000007"
        pointer_json = self.to_pointers(json.dumps([uuid_str]))
        pointers = json.loads(pointer_json)
        assert len(pointers) == 1
        vp = WritingVersionPointer.model_validate(pointers[0])
        assert str(vp.pointer_id) == uuid_str
        assert vp.label.startswith("Legacy version pointer")

    def test_to_strings_empty_input(self) -> None:
        """Empty pointer list → empty string list."""
        assert json.loads(self.to_strings("[]")) == []

    def test_to_strings_items_without_pointer_id_skipped(self) -> None:
        """Dict items missing pointer_id are skipped during downgrade."""
        raw = json.dumps([{"kind": "draft_label", "label": "x"}])
        result = json.loads(self.to_strings(raw))
        assert result == []


# ---------------------------------------------------------------------------
# Migration 0013 — upgrade behavior with legacy data
# ---------------------------------------------------------------------------


def _alembic_cfg(db_path: str) -> object:
    from alembic.config import Config

    ini_path = os.path.join(os.path.dirname(__file__), "..", "..", "alembic.ini")
    cfg = Config(ini_path)
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
    return cfg


def test_migration_0013_persona_backfill() -> None:
    """0012→0013 upgrade: legacy persona='chiron' → persona_id='chiron'."""  # noqa: E501
    import sqlalchemy as sa

    from alembic import command

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        cfg = _alembic_cfg(db_path)
        command.upgrade(cfg, "0012")

        engine = sa.create_engine(f"sqlite:///{db_path}")
        import uuid

        story_id = str(uuid.uuid4())
        session_id = str(uuid.uuid4())
        with engine.connect() as conn:
            conn.execute(
                sa.text(
                    "INSERT INTO stories"
                    " (story_id, title, mode, created_at, updated_at)"
                    " VALUES (:sid, 'T', 'writing', '2026-01-01', '2026-01-01')"
                ),
                {"sid": story_id},
            )
            conn.execute(
                sa.text(
                    "INSERT INTO writing_session_states (session_id, story_id,"
                    " beat_constraints, version_history_pointers, persona)"  # noqa: E501
                    " VALUES (:ssid, :stid, :bc, :vhp, :persona)"
                ),
                {
                    "ssid": session_id,
                    "stid": story_id,
                    "bc": "[]",
                    "vhp": "[]",
                    "persona": "chiron",
                },
            )
            conn.commit()
        engine.dispose()

        command.upgrade(cfg, "head")

        engine = sa.create_engine(f"sqlite:///{db_path}")
        with engine.connect() as conn:
            row = conn.execute(
                sa.text(
                    "SELECT persona_id FROM writing_session_states"
                    " WHERE session_id = :ssid"
                ),
                {"ssid": session_id},
            ).fetchone()
        engine.dispose()

        assert row is not None
        assert row[0] == "chiron"
    finally:
        os.unlink(db_path)


def test_migration_0013_version_pointers_conversion() -> None:
    """Upgrade from 0012 to 0013: legacy UUID-string list is converted to dict list."""
    import sqlalchemy as sa

    from alembic import command

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    uuid_str = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    try:
        cfg = _alembic_cfg(db_path)
        command.upgrade(cfg, "0012")

        engine = sa.create_engine(f"sqlite:///{db_path}")
        import uuid

        story_id = str(uuid.uuid4())
        session_id = str(uuid.uuid4())
        with engine.connect() as conn:
            conn.execute(
                sa.text(
                    "INSERT INTO stories"
                    " (story_id, title, mode, created_at, updated_at)"
                    " VALUES (:sid, 'T', 'writing', '2026-01-01', '2026-01-01')"
                ),
                {"sid": story_id},
            )
            conn.execute(
                sa.text(
                    "INSERT INTO writing_session_states (session_id, story_id,"
                    " beat_constraints, version_history_pointers, persona)"  # noqa: E501
                    " VALUES (:ssid, :stid, :bc, :vhp, :persona)"
                ),
                {
                    "ssid": session_id,
                    "stid": story_id,
                    "bc": "[]",
                    "vhp": json.dumps([uuid_str]),
                    "persona": None,
                },
            )
            conn.commit()
        engine.dispose()

        command.upgrade(cfg, "head")

        engine = sa.create_engine(f"sqlite:///{db_path}")
        with engine.connect() as conn:
            row = conn.execute(
                sa.text(
                    "SELECT version_pointers FROM writing_session_states"
                    " WHERE session_id = :ssid"
                ),
                {"ssid": session_id},
            ).fetchone()
        engine.dispose()

        assert row is not None
        raw = row[0]
        pointers = json.loads(raw) if isinstance(raw, str) else raw
        assert isinstance(pointers, list)
        assert len(pointers) == 1
        p = pointers[0]
        assert isinstance(p, dict)
        assert p["pointer_id"] == uuid_str
        assert p["kind"] == "draft_label"
        assert p["schema_version"] == 1
    finally:
        os.unlink(db_path)


# ---------------------------------------------------------------------------
# Migration 0017 — Owner Decision 15b-36 (pre-release clean schema cutover)
# ---------------------------------------------------------------------------


def _legacy_pending_roll_insert_kwargs(request_id: str) -> dict:
    """Column values for a pending_roll_requests row in its pre-0017 (0011) shape.

    story_id/character_id/originating_turn_id are synthetic UUIDs, not real
    parent rows — Alembic's own migration-runner connection does not enable
    SQLite foreign-key enforcement (only this project's application engine
    factory does, via its own connect event listener), so this table accepts
    the insert regardless. The precondition test only needs *a row to exist*.
    """
    import uuid

    return {
        "request_id": request_id,
        "story_id": str(uuid.uuid4()),
        "session_id": str(uuid.uuid4()),
        "character_id": str(uuid.uuid4()),
        "originating_turn_id": str(uuid.uuid4()),
        "visibility": "player",
        "source_proposal_ref": "test/stealth",
        "status": "pending",
        "created_at": "2026-01-01T00:00:00",
        "schema_version": 1,
        "roll_expression": "1d20",
        "expected_value_shape": "integer",
        "visible_modifier_total": 2,
        "visible_modifier_breakdown_json": "{}",
        "check_label": "Stealth Check",
        "player_facing_instruction": "Roll 1d20+2",
        "visible_modifier_note": None,
        "hidden_modifier_present": False,
    }


def test_migration_0017_upgrade_head_drops_legacy_columns() -> None:
    """Target schema after `head` carries none of the eight legacy columns."""
    import sqlalchemy as sa

    from alembic import command

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        command.upgrade(_alembic_cfg(db_path), "head")

        engine = sa.create_engine(f"sqlite:///{db_path}")
        inspector = sa.inspect(engine)
        columns = {c["name"] for c in inspector.get_columns("pending_roll_requests")}
        engine.dispose()

        legacy = {
            "roll_expression",
            "expected_value_shape",
            "visible_modifier_total",
            "visible_modifier_breakdown_json",
            "check_label",
            "player_facing_instruction",
            "visible_modifier_note",
            "hidden_modifier_present",
        }
        assert columns & legacy == set(), f"Legacy columns survived: {columns & legacy}"
    finally:
        os.unlink(db_path)


def test_migration_0017_action_resolution_sequences_session_id_non_null() -> None:
    """`action_resolution_sequences.session_id` is NOT NULL from creation."""
    import sqlalchemy as sa

    from alembic import command

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        command.upgrade(_alembic_cfg(db_path), "head")

        engine = sa.create_engine(f"sqlite:///{db_path}")
        inspector = sa.inspect(engine)
        columns = {
            c["name"]: c for c in inspector.get_columns("action_resolution_sequences")
        }
        engine.dispose()

        assert "session_id" in columns
        assert columns["session_id"]["nullable"] is False
    finally:
        os.unlink(db_path)


def test_migration_0017_aborts_before_destructive_change_when_row_exists() -> None:
    """A preexisting pending_roll_requests row aborts 0017 before any ALTER TABLE.

    Owner Decision 15b-36: the migration's zero-row precondition must fail
    visibly rather than silently coerce or skip. Verifies both that the
    upgrade raises and that no destructive change happened first — the
    legacy columns must still all be present afterward, proving the failure
    landed before the drop loop (or that the whole migration's DDL rolled
    back transactionally either way).
    """
    import uuid

    import sqlalchemy as sa

    from alembic import command

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        cfg = _alembic_cfg(db_path)
        command.upgrade(cfg, "0016")

        engine = sa.create_engine(f"sqlite:///{db_path}")
        with engine.connect() as conn:
            conn.execute(
                sa.text(
                    "INSERT INTO pending_roll_requests ("
                    " request_id, story_id, session_id, character_id,"
                    " originating_turn_id, visibility, source_proposal_ref, status,"
                    " created_at, schema_version, roll_expression,"
                    " expected_value_shape, visible_modifier_total,"
                    " visible_modifier_breakdown_json, check_label,"
                    " player_facing_instruction, visible_modifier_note,"
                    " hidden_modifier_present"
                    ") VALUES ("
                    " :request_id, :story_id, :session_id, :character_id,"
                    " :originating_turn_id, :visibility, :source_proposal_ref, :status,"
                    " :created_at, :schema_version, :roll_expression,"
                    " :expected_value_shape, :visible_modifier_total,"
                    " :visible_modifier_breakdown_json, :check_label,"
                    " :player_facing_instruction, :visible_modifier_note,"
                    " :hidden_modifier_present"
                    ")"
                ),
                _legacy_pending_roll_insert_kwargs(str(uuid.uuid4())),
            )
            conn.commit()
        engine.dispose()

        with pytest.raises(Exception, match="pending_roll_requests.*contains"):
            command.upgrade(cfg, "0017")

        engine = sa.create_engine(f"sqlite:///{db_path}")
        inspector = sa.inspect(engine)
        columns = {c["name"] for c in inspector.get_columns("pending_roll_requests")}
        engine.dispose()

        # The legacy columns must all still be present — the destructive
        # drop loop must not have run (or its effects rolled back).
        for col in (
            "roll_expression",
            "expected_value_shape",
            "visible_modifier_total",
            "visible_modifier_breakdown_json",
            "check_label",
            "player_facing_instruction",
            "visible_modifier_note",
            "hidden_modifier_present",
        ):
            assert (
                col in columns
            ), f"Legacy column {col!r} missing after aborted migration"
    finally:
        os.unlink(db_path)


def test_migration_0017_foreign_key_check_and_triggers_sound() -> None:
    """After upgrade head, PRAGMA foreign_key_check is clean and append-only
    triggers on rpg_roll_audit still reject UPDATE/DELETE."""
    import uuid

    import sqlalchemy as sa
    from sqlalchemy.exc import IntegrityError

    from alembic import command

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        command.upgrade(_alembic_cfg(db_path), "head")

        engine = sa.create_engine(f"sqlite:///{db_path}")
        with engine.connect() as conn:
            violations = conn.execute(sa.text("PRAGMA foreign_key_check")).fetchall()
            assert violations == [], f"foreign_key_check violations: {violations}"

            # A row-level trigger needs a row to fire on.
            conn.execute(
                sa.text(
                    "INSERT INTO turns"
                    " (turn_id, node_id, user_input, assistant_output, timestamp,"
                    " intent_classification)"
                    " VALUES"
                    " (:tid, NULL, 'u', 'a', '2026-01-01', 'in_character_action')"
                ),
                {"tid": str(uuid.uuid4())},
            )
            turn_id = conn.execute(
                sa.text("SELECT turn_id FROM turns LIMIT 1")
            ).scalar()
            conn.execute(
                sa.text(
                    "INSERT INTO rpg_roll_audit"
                    " (turn_id, story_id, session_id, character_id, check_label,"
                    " visibility, expression, raw_rolls_json, modifiers_json, total,"
                    " dc, outcome, source, gm_cheating_at_roll, sheet_effects_json,"
                    " created_at)"
                    " VALUES (:turn_id, :sid, :ssid, :cid, 'Stealth', 'player',"
                    " '1d20', '[12]', '{}', 12, NULL, 'undetermined', 'player', 0,"
                    " '[]', '2026-01-01')"
                ),
                {
                    "turn_id": turn_id,
                    "sid": str(uuid.uuid4()),
                    "ssid": str(uuid.uuid4()),
                    "cid": str(uuid.uuid4()),
                },
            )
            conn.commit()

            with pytest.raises(IntegrityError, match="append-only"):
                conn.execute(sa.text("DELETE FROM rpg_roll_audit"))
                conn.commit()
        engine.dispose()
    finally:
        os.unlink(db_path)
