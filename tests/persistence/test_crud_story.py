"""Tests for Story, Arc, and Chapter CRUD operations."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from afterworlds.models.enums import StoryMode
from afterworlds.persistence.crud.story import (
    create_arc,
    create_chapter,
    create_story,
    delete_arc,
    delete_story,
    get_arc,
    get_chapter,
    get_story,
    update_arc,
    update_chapter,
    update_story,
)
from tests.persistence.conftest import make_arc, make_chapter, make_story


def test_create_and_get_story(session):  # type: ignore[no-untyped-def]
    """Round-trip: create a Story, retrieve it, verify fields."""
    story = make_story()
    created = create_story(session, story)
    session.commit()

    fetched = get_story(session, created.story_id)
    assert fetched is not None
    assert fetched.story_id == story.story_id
    assert fetched.title == story.title
    assert fetched.mode == story.mode
    assert fetched.arc_ids == []


def test_get_story_not_found(session):  # type: ignore[no-untyped-def]
    """get_story returns None for an unknown ID."""
    assert get_story(session, uuid4()) is None


def test_update_story(session):  # type: ignore[no-untyped-def]
    """update_story changes title and mode."""
    story = make_story()
    create_story(session, story)
    session.commit()

    updated = story.model_copy(
        update={
            "title": "Updated Title",
            "mode": StoryMode.BRANCHING,
            "updated_at": datetime(2026, 6, 1, tzinfo=UTC),
        }
    )
    result = update_story(session, updated)
    session.commit()

    assert result is not None
    fetched = get_story(session, story.story_id)
    assert fetched is not None
    assert fetched.title == "Updated Title"
    assert fetched.mode == StoryMode.BRANCHING


def test_delete_story(session):  # type: ignore[no-untyped-def]
    """delete_story removes the row; get_story returns None afterwards."""
    story = make_story()
    create_story(session, story)
    session.commit()

    deleted = delete_story(session, story.story_id)
    session.commit()

    assert deleted is True
    assert get_story(session, story.story_id) is None


def test_delete_story_not_found(session):  # type: ignore[no-untyped-def]
    """delete_story returns False for unknown ID."""
    assert delete_story(session, uuid4()) is False


def test_cascade_delete_story_to_arcs(session):  # type: ignore[no-untyped-def]
    """Deleting a Story cascades to its Arcs."""
    story = make_story()
    create_story(session, story)
    arc = make_arc(str(story.story_id))
    create_arc(session, arc)
    session.commit()

    delete_story(session, story.story_id)
    session.commit()

    assert get_arc(session, arc.arc_id) is None


def test_cascade_delete_arc_to_chapters(session):  # type: ignore[no-untyped-def]
    """Deleting an Arc cascades to its Chapters."""
    story = make_story()
    create_story(session, story)
    arc = make_arc(str(story.story_id))
    create_arc(session, arc)
    chapter = make_chapter(str(arc.arc_id))
    create_chapter(session, chapter)
    session.commit()

    delete_arc(session, arc.arc_id)
    session.commit()

    assert get_chapter(session, chapter.chapter_id) is None


def test_arc_fk_enforced(session):  # type: ignore[no-untyped-def]
    """Creating an Arc with a non-existent story_id raises IntegrityError."""
    arc = make_arc(str(uuid4()))
    with pytest.raises(IntegrityError):
        create_arc(session, arc)
        session.flush()


def test_chapter_fk_enforced(session):  # type: ignore[no-untyped-def]
    """Creating a Chapter with a non-existent arc_id raises IntegrityError."""
    chapter = make_chapter(str(uuid4()))
    with pytest.raises(IntegrityError):
        create_chapter(session, chapter)
        session.flush()


def test_arc_round_trip(session):  # type: ignore[no-untyped-def]
    """Round-trip: create Arc, retrieve it, verify fields."""
    story = make_story()
    create_story(session, story)
    arc = make_arc(str(story.story_id), title="My Arc", order=2)
    created = create_arc(session, arc)
    session.commit()

    fetched = get_arc(session, created.arc_id)
    assert fetched is not None
    assert fetched.arc_id == arc.arc_id
    assert fetched.story_id == story.story_id
    assert fetched.title == "My Arc"
    assert fetched.order == 2
    assert fetched.chapter_ids == []


def test_chapter_round_trip(session):  # type: ignore[no-untyped-def]
    """Round-trip: create Chapter, retrieve it, verify fields."""
    story = make_story()
    create_story(session, story)
    arc = make_arc(str(story.story_id))
    create_arc(session, arc)
    chapter = make_chapter(str(arc.arc_id), title="Opening Chapter", order=1)
    created = create_chapter(session, chapter)
    session.commit()

    fetched = get_chapter(session, created.chapter_id)
    assert fetched is not None
    assert fetched.chapter_id == chapter.chapter_id
    assert fetched.title == "Opening Chapter"
    assert fetched.node_ids == []


def test_story_arc_ids_populated(session):  # type: ignore[no-untyped-def]
    """Story.arc_ids is populated from the arcs table."""
    story = make_story()
    create_story(session, story)
    arc1 = make_arc(str(story.story_id), title="Arc 1", order=1)
    arc2 = make_arc(str(story.story_id), title="Arc 2", order=2)
    create_arc(session, arc1)
    create_arc(session, arc2)
    session.commit()

    fetched = get_story(session, story.story_id)
    assert fetched is not None
    assert len(fetched.arc_ids) == 2
    assert arc1.arc_id in fetched.arc_ids
    assert arc2.arc_id in fetched.arc_ids


def test_arc_chapter_ids_populated(session):  # type: ignore[no-untyped-def]
    """Arc.chapter_ids is populated from the chapters table."""
    story = make_story()
    create_story(session, story)
    arc = make_arc(str(story.story_id))
    create_arc(session, arc)
    ch1 = make_chapter(str(arc.arc_id), title="Ch 1", order=1)
    ch2 = make_chapter(str(arc.arc_id), title="Ch 2", order=2)
    create_chapter(session, ch1)
    create_chapter(session, ch2)
    session.commit()

    fetched = get_arc(session, arc.arc_id)
    assert fetched is not None
    assert len(fetched.chapter_ids) == 2


def test_update_arc(session):  # type: ignore[no-untyped-def]
    """update_arc changes title and order."""
    story = make_story()
    create_story(session, story)
    arc = make_arc(str(story.story_id), title="Old", order=1)
    create_arc(session, arc)
    session.commit()

    updated_arc = arc.model_copy(update={"title": "New", "order": 5})
    result = update_arc(session, updated_arc)
    session.commit()

    assert result is not None
    fetched = get_arc(session, arc.arc_id)
    assert fetched is not None
    assert fetched.title == "New"
    assert fetched.order == 5


def test_update_chapter(session):  # type: ignore[no-untyped-def]
    """update_chapter changes title and order."""
    story = make_story()
    create_story(session, story)
    arc = make_arc(str(story.story_id))
    create_arc(session, arc)
    chapter = make_chapter(str(arc.arc_id), title="Old", order=1)
    create_chapter(session, chapter)
    session.commit()

    updated = chapter.model_copy(update={"title": "New", "order": 3})
    result = update_chapter(session, updated)
    session.commit()

    assert result is not None
    fetched = get_chapter(session, chapter.chapter_id)
    assert fetched is not None
    assert fetched.title == "New"
    assert fetched.order == 3
