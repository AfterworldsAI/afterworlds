"""Shared fixtures for persistence tests."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

import afterworlds.persistence.orm.character_sheet  # noqa: F401
import afterworlds.persistence.orm.node  # noqa: F401
import afterworlds.persistence.orm.session_state  # noqa: F401
import afterworlds.persistence.orm.state  # noqa: F401

# Import all ORM models to ensure they register with Base.metadata
import afterworlds.persistence.orm.story  # noqa: F401
from afterworlds.models.enums import StoryMode
from afterworlds.models.story import Arc, Chapter, Story
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.persistence.orm.base import Base


@pytest.fixture()
def engine():  # type: ignore[no-untyped-def]
    """In-memory SQLite engine with all tables created."""
    eng = create_engine("sqlite://")
    Base.metadata.create_all(eng)
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


def make_story(
    title: str = "Test Story",
    mode: StoryMode = StoryMode.RPG,
) -> Story:
    """Return a valid Story Pydantic instance."""
    now = datetime(2026, 1, 1, tzinfo=UTC)
    return Story(title=title, mode=mode, created_at=now, updated_at=now)


def make_arc(story_id: str, title: str = "Arc One", order: int = 1) -> Arc:
    from uuid import UUID

    return Arc(story_id=UUID(story_id), title=title, order=order)


def make_chapter(arc_id: str, title: str = "Chapter One", order: int = 1) -> Chapter:
    from uuid import UUID

    return Chapter(arc_id=UUID(arc_id), title=title, order=order)
