"""Tests that the Alembic baseline migration runs cleanly."""

from __future__ import annotations

import importlib.util
import json
import os
import tempfile


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
