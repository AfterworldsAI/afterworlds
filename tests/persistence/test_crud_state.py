"""Tests for WorldState and CharacterState CRUD with partition-aware updates."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from afterworlds.models.state import (
    CharacterState,
    CharacterStateDynamicPartition,
    CharacterStateStaticPartition,
    WorldState,
    WorldStateDynamicPartition,
    WorldStateStaticPartition,
)
from afterworlds.persistence.crud.state import (
    create_character_state,
    create_world_state,
    delete_character_state,
    delete_world_state,
    get_character_state,
    get_character_state_by_story,
    get_world_state,
    get_world_state_by_story,
    update_character_state_dynamic,
    update_character_state_static,
    update_world_state_dynamic,
    update_world_state_static,
)
from afterworlds.persistence.crud.story import create_story
from tests.persistence.conftest import make_story

NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _make_world_state(story_id: str) -> WorldState:
    from uuid import UUID

    return WorldState(
        story_id=UUID(story_id),
        static=WorldStateStaticPartition(
            setting_name="Eldoria",
            world_rules=["magic exists", "dragons are rare"],
            geography="Northern continent",
            time_period="Medieval",
        ),
        dynamic=WorldStateDynamicPartition(
            current_location="Thornwood",
            time_of_day="evening",
            weather="stormy",
            faction_standings={"merchants": "neutral"},
        ),
        updated_at=NOW,
    )


def _make_char_state(story_id: str) -> CharacterState:
    from uuid import UUID

    return CharacterState(
        story_id=UUID(story_id),
        static=CharacterStateStaticPartition(character_name="Aria"),
        dynamic=CharacterStateDynamicPartition(
            current_location="Thornwood",
            status_effects=["poisoned"],
            relationship_meters={"king": "friendly"},
            inventory=["dagger", "rope"],
        ),
        updated_at=NOW,
    )


# ---------------------------------------------------------------------------
# WorldState tests
# ---------------------------------------------------------------------------


def test_world_state_round_trip(session):  # type: ignore[no-untyped-def]
    """Round-trip WorldState: create → get → verify all fields."""
    story = make_story()
    create_story(session, story)
    ws = _make_world_state(str(story.story_id))
    created = create_world_state(session, ws)
    session.commit()

    fetched = get_world_state(session, created.world_state_id)
    assert fetched is not None
    assert fetched.world_state_id == ws.world_state_id
    assert fetched.story_id == story.story_id
    assert fetched.static.setting_name == "Eldoria"
    assert fetched.static.world_rules == ["magic exists", "dragons are rare"]
    assert fetched.static.geography == "Northern continent"
    assert fetched.dynamic.current_location == "Thornwood"
    assert fetched.dynamic.faction_standings == {"merchants": "neutral"}


def test_world_state_by_story(session):  # type: ignore[no-untyped-def]
    """get_world_state_by_story returns the correct row."""
    story = make_story()
    create_story(session, story)
    ws = _make_world_state(str(story.story_id))
    create_world_state(session, ws)
    session.commit()

    fetched = get_world_state_by_story(session, story.story_id)
    assert fetched is not None
    assert fetched.story_id == story.story_id


def test_update_world_state_static_only(session):  # type: ignore[no-untyped-def]
    """update_world_state_static must NOT change dynamic columns."""
    story = make_story()
    create_story(session, story)
    ws = _make_world_state(str(story.story_id))
    create_world_state(session, ws)
    session.commit()

    new_static = WorldStateStaticPartition(
        setting_name="New Realm",
        world_rules=["no magic"],
        geography="Southern coast",
        time_period="Ancient",
    )
    result = update_world_state_static(session, story.story_id, new_static)
    session.commit()

    assert result is not None
    fetched = get_world_state_by_story(session, story.story_id)
    assert fetched is not None
    # Static updated
    assert fetched.static.setting_name == "New Realm"
    assert fetched.static.world_rules == ["no magic"]
    # Dynamic untouched
    assert fetched.dynamic.current_location == "Thornwood"
    assert fetched.dynamic.weather == "stormy"


def test_update_world_state_dynamic_only(session):  # type: ignore[no-untyped-def]
    """update_world_state_dynamic must NOT change static columns."""
    story = make_story()
    create_story(session, story)
    ws = _make_world_state(str(story.story_id))
    create_world_state(session, ws)
    session.commit()

    new_dynamic = WorldStateDynamicPartition(
        current_location="Castle",
        time_of_day="noon",
        weather="clear",
        faction_standings={"guild": "hostile"},
    )
    result = update_world_state_dynamic(session, story.story_id, new_dynamic)
    session.commit()

    assert result is not None
    fetched = get_world_state_by_story(session, story.story_id)
    assert fetched is not None
    # Dynamic updated
    assert fetched.dynamic.current_location == "Castle"
    assert fetched.dynamic.weather == "clear"
    # Static untouched
    assert fetched.static.setting_name == "Eldoria"
    assert fetched.static.world_rules == ["magic exists", "dragons are rare"]


def test_world_state_unique_story_constraint(session):  # type: ignore[no-untyped-def]
    """A second WorldState for the same story_id raises IntegrityError."""
    story = make_story()
    create_story(session, story)
    ws1 = _make_world_state(str(story.story_id))
    create_world_state(session, ws1)
    session.commit()

    ws2 = _make_world_state(str(story.story_id))
    with pytest.raises(IntegrityError):
        create_world_state(session, ws2)
        session.flush()


def test_world_state_fk_enforced(session):  # type: ignore[no-untyped-def]
    """Creating WorldState with non-existent story_id raises IntegrityError."""
    ws = _make_world_state(str(uuid4()))
    with pytest.raises(IntegrityError):
        create_world_state(session, ws)
        session.flush()


def test_delete_world_state(session):  # type: ignore[no-untyped-def]
    """delete_world_state removes the row."""
    story = make_story()
    create_story(session, story)
    ws = _make_world_state(str(story.story_id))
    create_world_state(session, ws)
    session.commit()

    assert delete_world_state(session, ws.world_state_id) is True
    session.commit()
    assert get_world_state(session, ws.world_state_id) is None


# ---------------------------------------------------------------------------
# CharacterState tests
# ---------------------------------------------------------------------------


def test_char_state_round_trip(session):  # type: ignore[no-untyped-def]
    """Round-trip CharacterState: create → get → verify all fields."""
    story = make_story()
    create_story(session, story)
    cs = _make_char_state(str(story.story_id))
    created = create_character_state(session, cs)
    session.commit()

    fetched = get_character_state(session, created.character_state_id)
    assert fetched is not None
    assert fetched.static.character_name == "Aria"
    assert fetched.dynamic.status_effects == ["poisoned"]
    assert fetched.dynamic.inventory == ["dagger", "rope"]


def test_update_char_state_static_only(session):  # type: ignore[no-untyped-def]
    """update_character_state_static must NOT change dynamic columns."""
    story = make_story()
    create_story(session, story)
    cs = _make_char_state(str(story.story_id))
    create_character_state(session, cs)
    session.commit()

    new_static = CharacterStateStaticPartition(character_name="Bor")
    update_character_state_static(session, story.story_id, new_static)
    session.commit()

    fetched = get_character_state_by_story(session, story.story_id)
    assert fetched is not None
    assert fetched.static.character_name == "Bor"
    # Dynamic untouched
    assert fetched.dynamic.inventory == ["dagger", "rope"]


def test_update_char_state_dynamic_only(session):  # type: ignore[no-untyped-def]
    """update_character_state_dynamic must NOT change static columns."""
    story = make_story()
    create_story(session, story)
    cs = _make_char_state(str(story.story_id))
    create_character_state(session, cs)
    session.commit()

    new_dynamic = CharacterStateDynamicPartition(
        current_location="Forest",
        status_effects=[],
        relationship_meters={},
        inventory=["new item"],
    )
    update_character_state_dynamic(session, story.story_id, new_dynamic)
    session.commit()

    fetched = get_character_state_by_story(session, story.story_id)
    assert fetched is not None
    assert fetched.dynamic.inventory == ["new item"]
    assert fetched.dynamic.status_effects == []
    # Static untouched
    assert fetched.static.character_name == "Aria"


def test_char_state_unique_story_constraint(session):  # type: ignore[no-untyped-def]
    """A second CharacterState for the same story_id raises IntegrityError."""
    story = make_story()
    create_story(session, story)
    cs1 = _make_char_state(str(story.story_id))
    create_character_state(session, cs1)
    session.commit()

    cs2 = _make_char_state(str(story.story_id))
    with pytest.raises(IntegrityError):
        create_character_state(session, cs2)
        session.flush()


def test_delete_char_state(session):  # type: ignore[no-untyped-def]
    """delete_character_state removes the row."""
    story = make_story()
    create_story(session, story)
    cs = _make_char_state(str(story.story_id))
    create_character_state(session, cs)
    session.commit()

    assert delete_character_state(session, cs.character_state_id) is True
    session.commit()
    assert get_character_state(session, cs.character_state_id) is None


# ---------------------------------------------------------------------------
# updated_at refresh tests
# ---------------------------------------------------------------------------


def test_world_state_static_update_refreshes_updated_at(session):  # type: ignore[no-untyped-def]
    """update_world_state_static must advance updated_at."""
    story = make_story()
    create_story(session, story)
    ws = _make_world_state(str(story.story_id))
    create_world_state(session, ws)
    session.commit()

    new_static = WorldStateStaticPartition(
        setting_name="New Realm",
        world_rules=["no magic"],
        geography=None,
        time_period=None,
    )
    result = update_world_state_static(session, story.story_id, new_static)
    session.commit()

    assert result is not None
    # updated_at stored as ISO string and coerced back to datetime by Pydantic
    assert result.updated_at != ws.updated_at


def test_world_state_dynamic_update_refreshes_updated_at(session):  # type: ignore[no-untyped-def]
    """update_world_state_dynamic must advance updated_at."""
    story = make_story()
    create_story(session, story)
    ws = _make_world_state(str(story.story_id))
    create_world_state(session, ws)
    session.commit()

    new_dynamic = WorldStateDynamicPartition(
        current_location="Castle",
        time_of_day="noon",
        weather="clear",
        faction_standings={},
    )
    result = update_world_state_dynamic(session, story.story_id, new_dynamic)
    session.commit()

    assert result is not None
    assert result.updated_at != ws.updated_at


def test_char_state_static_update_refreshes_updated_at(session):  # type: ignore[no-untyped-def]
    """update_character_state_static must advance updated_at."""
    story = make_story()
    create_story(session, story)
    cs = _make_char_state(str(story.story_id))
    create_character_state(session, cs)
    session.commit()

    new_static = CharacterStateStaticPartition(character_name="New Name")
    result = update_character_state_static(session, story.story_id, new_static)
    session.commit()

    assert result is not None
    assert result.updated_at != cs.updated_at


def test_char_state_dynamic_update_refreshes_updated_at(session):  # type: ignore[no-untyped-def]
    """update_character_state_dynamic must advance updated_at."""
    story = make_story()
    create_story(session, story)
    cs = _make_char_state(str(story.story_id))
    create_character_state(session, cs)
    session.commit()

    new_dynamic = CharacterStateDynamicPartition(
        current_location="City",
        status_effects=[],
        relationship_meters={},
        inventory=[],
    )
    result = update_character_state_dynamic(session, story.story_id, new_dynamic)
    session.commit()

    assert result is not None
    assert result.updated_at != cs.updated_at
