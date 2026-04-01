"""CRUD operations for Story, Arc, and Chapter."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from afterworlds.models.story import Arc, Chapter, Story
from afterworlds.persistence.orm.story import ArcORM, ChapterORM, StoryORM

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _story_orm_to_model(row: StoryORM) -> Story:
    return Story(
        story_id=UUID(row.story_id),
        title=row.title,
        mode=row.mode,  # type: ignore[arg-type]
        created_at=row.created_at,  # type: ignore[arg-type]
        updated_at=row.updated_at,  # type: ignore[arg-type]
        arc_ids=[UUID(a.arc_id) for a in row.arcs],
    )


def _arc_orm_to_model(row: ArcORM) -> Arc:
    return Arc(
        arc_id=UUID(row.arc_id),
        story_id=UUID(row.story_id),
        title=row.title,
        order=row.order,
        chapter_ids=[UUID(c.chapter_id) for c in row.chapters],
    )


def _chapter_orm_to_model(row: ChapterORM) -> Chapter:
    return Chapter(
        chapter_id=UUID(row.chapter_id),
        arc_id=UUID(row.arc_id),
        title=row.title,
        order=row.order,
        node_ids=[UUID(n.node_id) for n in row.nodes],
    )


# ---------------------------------------------------------------------------
# Story CRUD
# ---------------------------------------------------------------------------


def create_story(session: Session, story: Story) -> Story:
    """Persist a new Story and return it."""
    row = StoryORM(
        story_id=str(story.story_id),
        title=story.title,
        mode=story.mode.value,
        created_at=story.created_at.isoformat(),
        updated_at=story.updated_at.isoformat(),
    )
    session.add(row)
    session.flush()
    return _story_orm_to_model(row)


def get_story(session: Session, story_id: UUID) -> Story | None:
    """Return a Story by primary key, or None if not found."""
    row = session.get(StoryORM, str(story_id))
    if row is None:
        return None
    return _story_orm_to_model(row)


def update_story(session: Session, story: Story) -> Story | None:
    """Update title, mode, and updated_at for an existing Story."""
    row = session.get(StoryORM, str(story.story_id))
    if row is None:
        return None
    row.title = story.title
    row.mode = story.mode.value
    row.updated_at = story.updated_at.isoformat()
    session.flush()
    return _story_orm_to_model(row)


def delete_story(session: Session, story_id: UUID) -> bool:
    """Delete a Story (cascades to arcs, chapters, nodes).  Returns True if deleted."""
    row = session.get(StoryORM, str(story_id))
    if row is None:
        return False
    session.delete(row)
    session.flush()
    return True


# ---------------------------------------------------------------------------
# Arc CRUD
# ---------------------------------------------------------------------------


def create_arc(session: Session, arc: Arc) -> Arc:
    """Persist a new Arc and return it."""
    row = ArcORM(
        arc_id=str(arc.arc_id),
        story_id=str(arc.story_id),
        title=arc.title,
        order=arc.order,
    )
    session.add(row)
    session.flush()
    return _arc_orm_to_model(row)


def get_arc(session: Session, arc_id: UUID) -> Arc | None:
    """Return an Arc by primary key, or None if not found."""
    row = session.get(ArcORM, str(arc_id))
    if row is None:
        return None
    return _arc_orm_to_model(row)


def update_arc(session: Session, arc: Arc) -> Arc | None:
    """Update title and order for an existing Arc."""
    row = session.get(ArcORM, str(arc.arc_id))
    if row is None:
        return None
    row.title = arc.title
    row.order = arc.order
    session.flush()
    return _arc_orm_to_model(row)


def delete_arc(session: Session, arc_id: UUID) -> bool:
    """Delete an Arc (cascades to chapters/nodes).  Returns True if deleted."""
    row = session.get(ArcORM, str(arc_id))
    if row is None:
        return False
    session.delete(row)
    session.flush()
    return True


# ---------------------------------------------------------------------------
# Chapter CRUD
# ---------------------------------------------------------------------------


def create_chapter(session: Session, chapter: Chapter) -> Chapter:
    """Persist a new Chapter and return it."""
    row = ChapterORM(
        chapter_id=str(chapter.chapter_id),
        arc_id=str(chapter.arc_id),
        title=chapter.title,
        order=chapter.order,
    )
    session.add(row)
    session.flush()
    return _chapter_orm_to_model(row)


def get_chapter(session: Session, chapter_id: UUID) -> Chapter | None:
    """Return a Chapter by primary key, or None if not found."""
    row = session.get(ChapterORM, str(chapter_id))
    if row is None:
        return None
    return _chapter_orm_to_model(row)


def update_chapter(session: Session, chapter: Chapter) -> Chapter | None:
    """Update title and order for an existing Chapter."""
    row = session.get(ChapterORM, str(chapter.chapter_id))
    if row is None:
        return None
    row.title = chapter.title
    row.order = chapter.order
    session.flush()
    return _chapter_orm_to_model(row)


def delete_chapter(session: Session, chapter_id: UUID) -> bool:
    """Delete a Chapter (cascades to nodes).  Returns True if deleted."""
    row = session.get(ChapterORM, str(chapter_id))
    if row is None:
        return False
    session.delete(row)
    session.flush()
    return True
