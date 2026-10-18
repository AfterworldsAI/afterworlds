"""Control-store bootstrap: its own Alembic chain (``alembic_control/``)."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from alembic.config import Config
from sqlalchemy.orm import Session, sessionmaker

from afterworlds.persistence.database import create_engine, create_session_factory
from alembic import command

_REPO_ROOT = Path(__file__).resolve().parents[3]

#: Version of the accepted retention policy these records are written under.
POLICY_VERSION = "crd22-matrix-r1"


def upgrade_control_to_head(database_url: str) -> None:
    """Apply every control-store migration (idempotent)."""
    config = Config()
    config.set_main_option("script_location", str(_REPO_ROOT / "alembic_control"))
    config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(config, "head")


def open_control_store(database_url: str) -> sessionmaker[Session]:
    """Migrate the control store and return its session factory."""
    upgrade_control_to_head(database_url)
    return create_session_factory(create_engine(database_url))


def utc_now() -> datetime:
    return datetime.now(UTC)


def iso(value: datetime) -> str:
    return value.astimezone(UTC).isoformat()


def parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(UTC)
