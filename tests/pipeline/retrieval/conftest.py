"""Shared fixtures for pipeline/retrieval tests."""

from __future__ import annotations

import pytest

# Import all ORM models to ensure they register with Base.metadata
import afterworlds.persistence.orm.character_sheet  # noqa: F401
import afterworlds.persistence.orm.node  # noqa: F401
import afterworlds.persistence.orm.retrieval  # noqa: F401
import afterworlds.persistence.orm.rules_package  # noqa: F401
import afterworlds.persistence.orm.session_state  # noqa: F401
import afterworlds.persistence.orm.state  # noqa: F401
import afterworlds.persistence.orm.story  # noqa: F401
import afterworlds.persistence.orm.story_bible  # noqa: F401
from afterworlds.persistence.database import create_engine
from afterworlds.persistence.orm.base import Base


@pytest.fixture()
def engine():  # type: ignore[no-untyped-def]
    """In-memory SQLite engine with all tables created."""
    eng = create_engine("sqlite://")
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)
    eng.dispose()
