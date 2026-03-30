"""Unit tests for Story, Arc, and Chapter models."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from afterworlds.models.enums import StoryMode
from afterworlds.models.story import Arc, Chapter, Story
from tests.models.factories import make_datetime


class TestStory:
    def test_instantiation_valid(self) -> None:
        story = Story(
            title="The Locked Room",
            mode=StoryMode.BRANCHING,
            created_at=make_datetime(),
            updated_at=make_datetime(),
        )
        assert story.title == "The Locked Room"
        assert story.mode == StoryMode.BRANCHING
        assert story.arc_ids == []

    def test_story_id_auto_generated(self) -> None:
        s1 = Story(
            title="A",
            mode=StoryMode.RPG,
            created_at=make_datetime(),
            updated_at=make_datetime(),
        )
        s2 = Story(
            title="B",
            mode=StoryMode.RPG,
            created_at=make_datetime(),
            updated_at=make_datetime(),
        )
        assert s1.story_id != s2.story_id

    def test_invalid_mode(self) -> None:
        with pytest.raises(ValidationError):
            Story(
                title="Bad",
                mode="invalid_mode",  # type: ignore[arg-type]
                created_at=make_datetime(),
                updated_at=make_datetime(),
            )

    def test_arc_ids_optional(self) -> None:
        story = Story(
            title="X",
            mode=StoryMode.WRITING,
            created_at=make_datetime(),
            updated_at=make_datetime(),
        )
        assert story.arc_ids == []

    def test_arc_ids_with_values(self) -> None:
        uid = uuid4()
        story = Story(
            title="X",
            mode=StoryMode.WRITING,
            arc_ids=[uid],
            created_at=make_datetime(),
            updated_at=make_datetime(),
        )
        assert story.arc_ids == [uid]

    def test_all_three_modes(self) -> None:
        for mode in StoryMode:
            s = Story(
                title="X",
                mode=mode,
                created_at=make_datetime(),
                updated_at=make_datetime(),
            )
            assert s.mode == mode


class TestArc:
    def test_instantiation_valid(self) -> None:
        arc = Arc(story_id=uuid4(), title="Act I", order=1)
        assert arc.title == "Act I"
        assert arc.order == 1
        assert arc.chapter_ids == []

    def test_arc_id_auto_generated(self) -> None:
        a1 = Arc(story_id=uuid4(), title="A", order=1)
        a2 = Arc(story_id=uuid4(), title="B", order=2)
        assert a1.arc_id != a2.arc_id

    def test_invalid_story_id_type(self) -> None:
        with pytest.raises(ValidationError):
            Arc(
                story_id="not-a-uuid",  # type: ignore[arg-type]
                title="X",
                order=1,
            )

    def test_chapter_ids_optional(self) -> None:
        arc = Arc(story_id=uuid4(), title="X", order=0)
        assert arc.chapter_ids == []

    def test_chapter_ids_populated(self) -> None:
        uid = uuid4()
        arc = Arc(story_id=uuid4(), title="X", order=0, chapter_ids=[uid])
        assert arc.chapter_ids == [uid]


class TestChapter:
    def test_instantiation_valid(self) -> None:
        chapter = Chapter(arc_id=uuid4(), title="Chapter 1", order=1)
        assert chapter.title == "Chapter 1"
        assert chapter.order == 1
        assert chapter.node_ids == []

    def test_chapter_id_auto_generated(self) -> None:
        c1 = Chapter(arc_id=uuid4(), title="A", order=1)
        c2 = Chapter(arc_id=uuid4(), title="B", order=2)
        assert c1.chapter_id != c2.chapter_id

    def test_node_ids_optional(self) -> None:
        chapter = Chapter(arc_id=uuid4(), title="X", order=0)
        assert chapter.node_ids == []

    def test_node_ids_populated(self) -> None:
        uid = uuid4()
        chapter = Chapter(arc_id=uuid4(), title="X", order=0, node_ids=[uid])
        assert chapter.node_ids == [uid]

    def test_invalid_arc_id_type(self) -> None:
        with pytest.raises(ValidationError):
            Chapter(
                arc_id="not-a-uuid",  # type: ignore[arg-type]
                title="X",
                order=1,
            )
