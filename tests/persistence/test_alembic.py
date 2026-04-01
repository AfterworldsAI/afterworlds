"""Tests that the Alembic baseline migration runs cleanly."""

from __future__ import annotations

import os
import tempfile


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
