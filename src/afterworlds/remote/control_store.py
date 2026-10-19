"""Control-store bootstrap: its own Alembic chain (``alembic_control/``)."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.util.exc import CommandError
from sqlalchemy.engine import make_url
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from afterworlds.persistence.database import create_engine, create_session_factory

#: The control Alembic chain, shipped inside the package (#205).
CONTROL_MIGRATIONS = Path(__file__).resolve().parents[1] / "migrations" / "control"

#: Version of the accepted retention policy these records are written under.
POLICY_VERSION = "crd22-matrix-r1"


def upgrade_control_to_head(database_url: str) -> None:
    """Apply every control-store migration (idempotent)."""
    config = Config()
    config.set_main_option("script_location", str(CONTROL_MIGRATIONS))
    config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(config, "head")


def open_control_store(database_url: str) -> sessionmaker[Session]:
    """Initialize: migrate the control store, then return its factory.

    Only the coordinated owner calls this -- app startup, holding both store
    locks -- and test fixtures. Operational tools use
    :func:`connect_control_store`, which never changes the schema."""
    upgrade_control_to_head(database_url)
    return create_session_factory(create_engine(database_url))


class ControlStoreUnavailable(RuntimeError):
    """The control store is missing or not at this release's schema."""


def control_head() -> str:
    """This release's single supported control-schema revision. Missing or
    broken migration scripts, no head or several heads are an unavailable
    authority (typed, without repository paths)."""
    config = Config()
    config.set_main_option("script_location", str(CONTROL_MIGRATIONS))
    try:
        head = ScriptDirectory.from_config(config).get_current_head()
    except CommandError:
        raise ControlStoreUnavailable(
            "the supported control schema could not be determined"
        ) from None
    if head is None:
        raise ControlStoreUnavailable("the supported control schema has no revision")
    return head


def connect_control_store(database_url: str) -> sessionmaker[Session]:
    """Open an existing control store at this release's schema, without any
    migration or DDL; refuse (creating nothing) when it is missing, at another
    revision, or records anything but exactly the supported head. The
    supported head is resolved before any connection exists. Upgrading is the
    coordinated startup's job."""
    head = control_head()
    url = make_url(database_url)
    path = url.database if url.get_backend_name() == "sqlite" else None
    if path not in (None, "", ":memory:") and not Path(str(path)).is_file():
        raise ControlStoreUnavailable("the control store does not exist")
    if path not in (None, "", ":memory:") and Path(str(path)).stat().st_nlink > 1:
        raise ControlStoreUnavailable("the control store has more than one hard link")
    engine = create_engine(database_url)
    try:
        with engine.connect() as conn:
            revisions = conn.execute(
                sa.text("SELECT version_num FROM alembic_version")
            ).all()
    except SQLAlchemyError:
        engine.dispose()
        raise ControlStoreUnavailable("the control store is unreadable") from None
    if [tuple(row) for row in revisions] != [(head,)]:
        engine.dispose()
        raise ControlStoreUnavailable(
            "the control store is not at this release's schema; start the "
            "application (which migrates it under the store locks) first"
        )
    return create_session_factory(engine)


def utc_now() -> datetime:
    return datetime.now(UTC)


def iso(value: datetime) -> str:
    return value.astimezone(UTC).isoformat()


def parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(UTC)
