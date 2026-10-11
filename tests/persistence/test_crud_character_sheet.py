"""Tests for RPG character identity CRUD."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from afterworlds.models.character_sheet import RpgCharacterSheetBase
from afterworlds.models.dnd5e_state import Dnd5eCharacterState
from afterworlds.persistence.crud.character_sheet import (
    create_rpg_base_sheet,
    delete_rpg_base_sheet,
    get_rpg_base_sheet,
    update_rpg_base_sheet,
)
from afterworlds.persistence.crud.story import create_story
from afterworlds.services.dnd5e_state import store
from tests.persistence.conftest import make_story
from tests.rpg_characters import BINDING

NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _make_base_sheet(story_id: str) -> RpgCharacterSheetBase:
    return RpgCharacterSheetBase(
        story_id=UUID(story_id),
        character_name="Thorin",
        created_at=NOW,
        updated_at=NOW,
    )


# ---------------------------------------------------------------------------
# RpgCharacterSheetBase tests
# ---------------------------------------------------------------------------


def test_rpg_base_sheet_round_trip(session):  # type: ignore[no-untyped-def]
    """Round-trip RpgCharacterSheetBase: create → get → verify fields."""
    story = make_story()
    create_story(session, story)
    sheet = _make_base_sheet(str(story.story_id))
    created = create_rpg_base_sheet(session, sheet)
    session.commit()

    fetched = get_rpg_base_sheet(session, created.sheet_id)
    assert fetched is not None
    assert fetched.sheet_id == sheet.sheet_id
    assert fetched.story_id == story.story_id
    assert fetched.character_name == "Thorin"


def test_rpg_base_sheet_fk_enforced(session):  # type: ignore[no-untyped-def]
    """Creating base sheet with non-existent story_id raises IntegrityError."""
    sheet = _make_base_sheet(str(uuid4()))
    with pytest.raises(IntegrityError):
        create_rpg_base_sheet(session, sheet)
        session.flush()


def test_rpg_base_sheet_update(session):  # type: ignore[no-untyped-def]
    """update_rpg_base_sheet changes character_name."""
    story = make_story()
    create_story(session, story)
    sheet = _make_base_sheet(str(story.story_id))
    create_rpg_base_sheet(session, sheet)
    session.commit()

    updated = sheet.model_copy(update={"character_name": "Gimli"})
    update_rpg_base_sheet(session, updated)
    session.commit()

    fetched = get_rpg_base_sheet(session, sheet.sheet_id)
    assert fetched is not None
    assert fetched.character_name == "Gimli"


def test_delete_rpg_base_sheet(session):  # type: ignore[no-untyped-def]
    """delete_rpg_base_sheet removes the row."""
    story = make_story()
    create_story(session, story)
    sheet = _make_base_sheet(str(story.story_id))
    create_rpg_base_sheet(session, sheet)
    session.commit()

    assert delete_rpg_base_sheet(session, sheet.sheet_id) is True
    session.commit()
    assert get_rpg_base_sheet(session, sheet.sheet_id) is None


def test_deleting_the_identity_cascades_its_typed_state(session):  # type: ignore[no-untyped-def]
    story = make_story()
    create_story(session, story)
    sheet = _make_base_sheet(str(story.story_id))
    create_rpg_base_sheet(session, sheet)
    store.create_character_state(
        session, sheet.sheet_id, Dnd5eCharacterState(conditions=()), BINDING, now="t"
    )
    session.commit()
    assert delete_rpg_base_sheet(session, sheet.sheet_id) is True
    session.commit()
    assert store.get_character(session, sheet.sheet_id) is None
