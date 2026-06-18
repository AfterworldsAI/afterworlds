"""Shared fixtures for pipeline/provider tests."""

from __future__ import annotations

import pytest
from sqlalchemy import text

import afterworlds.pipeline.provider._refusal_log  # noqa: F401 — registers ORM
import afterworlds.pipeline.provider._route_config  # noqa: F401 — registers ORM
import afterworlds.pipeline.provider.credentials._metadata  # noqa: F401 — registers ORM
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.persistence.orm.base import Base


@pytest.fixture()
def engine():  # type: ignore[no-untyped-def]
    """In-memory SQLite engine with provider tables and append-only triggers."""
    eng = create_engine("sqlite://")
    Base.metadata.create_all(eng)
    with eng.begin() as conn:
        conn.execute(
            text(
                "CREATE TRIGGER prevent_provider_refusal_log_update "
                "BEFORE UPDATE ON provider_refusal_log BEGIN "
                "SELECT RAISE(ABORT, 'provider_refusal_log is append-only:"
                " UPDATE is forbidden'); END"
            )
        )
        conn.execute(
            text(
                "CREATE TRIGGER prevent_provider_refusal_log_delete "
                "BEFORE DELETE ON provider_refusal_log BEGIN "
                "SELECT RAISE(ABORT, 'provider_refusal_log is append-only:"
                " DELETE is forbidden'); END"
            )
        )
    yield eng
    Base.metadata.drop_all(eng)
    eng.dispose()


@pytest.fixture()
def session(engine):  # type: ignore[no-untyped-def]
    """SQLAlchemy session bound to the in-memory engine."""
    factory = create_session_factory(engine)
    sess = factory()
    try:
        yield sess
    finally:
        sess.close()
