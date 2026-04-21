"""Shared fixtures for Story Bible service tests."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import pytest

# Import all ORM models to ensure Base.metadata is fully populated
import afterworlds.persistence.orm.character_sheet  # noqa: F401
import afterworlds.persistence.orm.node  # noqa: F401
import afterworlds.persistence.orm.rules_package  # noqa: F401
import afterworlds.persistence.orm.session_state  # noqa: F401
import afterworlds.persistence.orm.state  # noqa: F401
import afterworlds.persistence.orm.story  # noqa: F401
import afterworlds.persistence.orm.story_bible  # noqa: F401
from afterworlds.models.enums import CastRole, EventSignificance, StoryMode
from afterworlds.models.story import Story
from afterworlds.models.story_bible import (
    CastEntry,
    Event,
    ForbiddenFact,
    LockedFact,
    RelationshipLedger,
    StoryBibleSetting,
    UnresolvedThread,
)
from afterworlds.persistence.crud.story import create_story
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.persistence.orm.base import Base
from afterworlds.services.story_bible import StoryBibleService


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


@pytest.fixture()
def service(session):  # type: ignore[no-untyped-def]
    """StoryBibleService bound to the in-memory session."""
    return StoryBibleService(session)


@pytest.fixture()
def story_id(session) -> UUID:  # type: ignore[no-untyped-def]
    """Persist a minimal Story and return its UUID."""
    now = datetime(2026, 1, 1, tzinfo=UTC)
    story = Story(
        title="Test Story", mode=StoryMode.RPG, created_at=now, updated_at=now
    )
    create_story(session, story)
    session.commit()
    return story.story_id


def make_setting(story_id: UUID) -> StoryBibleSetting:
    return StoryBibleSetting(
        story_id=story_id,
        summary="A dark fantasy realm.",
        world_rules=("Magic exists", "The dead stay dead"),
        geography="Northern continent",
        time_period="Medieval",
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


def make_cast_entry(story_id: UUID, name: str = "Aldric") -> CastEntry:
    return CastEntry(
        story_id=story_id,
        name=name,
        role=CastRole.PROTAGONIST,
        traits=("brave", "reckless"),
        goals=("find the artifact",),
        secrets=("killed his brother",),
        background="Former soldier",
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


def make_locked_fact(story_id: UUID, text: str = "The king is dead.") -> LockedFact:
    return LockedFact(
        story_id=story_id,
        fact_text=text,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


def make_forbidden_fact(
    story_id: UUID, text: str = "The prophecy must not be fulfilled."
) -> ForbiddenFact:
    return ForbiddenFact(
        story_id=story_id,
        fact_text=text,
        source="sojourner",
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


def make_event(
    story_id: UUID,
    desc: str = "The king was slain.",
    significance: EventSignificance = EventSignificance.CHARACTER_DEATH,
) -> Event:
    return Event(
        story_id=story_id,
        description=desc,
        significance=significance,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


def make_relationship(
    story_id: UUID,
    subject_id: UUID,
    object_id: UUID,
) -> RelationshipLedger:
    from afterworlds.models.enums import RelationshipType

    now = datetime(2026, 1, 1, tzinfo=UTC)
    return RelationshipLedger(
        story_id=story_id,
        subject_cast_id=subject_id,
        object_cast_id=object_id,
        relationship_type=RelationshipType.ALLY,
        current_status_description="Trusted comrade",
        created_at=now,
        updated_at=now,
    )


def make_thread(
    story_id: UUID, desc: str = "Where is the artifact?"
) -> UnresolvedThread:
    return UnresolvedThread(
        story_id=story_id,
        description=desc,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
