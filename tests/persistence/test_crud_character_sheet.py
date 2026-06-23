"""Tests for RPG character sheet CRUD operations."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from afterworlds.models.character_sheet import (
    Dnd5eAbilityScores,
    Dnd5eActiveCondition,
    Dnd5eCharacterSheet,
    RpgCharacterSheetBase,
    SpellSlotLevel,
)
from afterworlds.models.enums import ConditionVisibility
from afterworlds.persistence.crud.character_sheet import (
    create_dnd5e_sheet,
    create_rpg_base_sheet,
    delete_dnd5e_sheet,
    delete_rpg_base_sheet,
    get_dnd5e_sheet,
    get_rpg_base_sheet,
    update_dnd5e_sheet,
    update_rpg_base_sheet,
)
from afterworlds.persistence.crud.story import create_story
from tests.persistence.conftest import make_story

NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _make_base_sheet_from_dnd5e(sheet: Dnd5eCharacterSheet) -> RpgCharacterSheetBase:
    return RpgCharacterSheetBase(
        sheet_id=sheet.sheet_id,
        story_id=sheet.story_id,
        rules_package_id=sheet.rules_package_id,
        character_name=sheet.character_name,
        created_at=sheet.created_at,
        updated_at=sheet.updated_at,
    )


def _make_base_sheet(story_id: str) -> RpgCharacterSheetBase:
    from uuid import UUID

    return RpgCharacterSheetBase(
        story_id=UUID(story_id),
        rules_package_id="dnd5e_v1",
        character_name="Thorin",
        created_at=NOW,
        updated_at=NOW,
    )


def _make_dnd5e_sheet(story_id: str) -> Dnd5eCharacterSheet:
    from uuid import UUID

    return Dnd5eCharacterSheet(
        story_id=UUID(story_id),
        rules_package_id="dnd5e_v1",
        character_name="Thorin",
        created_at=NOW,
        updated_at=NOW,
        character_class="Fighter",
        background="Soldier",
        level=5,
        ability_scores=Dnd5eAbilityScores(
            strength=18,
            dexterity=12,
            constitution=16,
            intelligence=10,
            wisdom=13,
            charisma=8,
        ),
        skills={"athletics": 7, "perception": 3},
        equipment=["longsword", "shield"],
        current_hp=40,
        maximum_hp=52,
        spell_slots={
            1: SpellSlotLevel(total=2, used=1),
            2: SpellSlotLevel(total=1, used=0),
        },
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
    assert fetched.rules_package_id == "dnd5e_v1"
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


# ---------------------------------------------------------------------------
# Dnd5eCharacterSheet tests
# ---------------------------------------------------------------------------


def test_dnd5e_sheet_round_trip(session):  # type: ignore[no-untyped-def]
    """Round-trip Dnd5eCharacterSheet: verify all typed fields including HP."""
    story = make_story()
    create_story(session, story)
    sheet = _make_dnd5e_sheet(str(story.story_id))
    create_rpg_base_sheet(session, _make_base_sheet_from_dnd5e(sheet))
    created = create_dnd5e_sheet(session, sheet)
    session.commit()

    fetched = get_dnd5e_sheet(session, created.sheet_id)
    assert fetched is not None
    assert fetched.sheet_id == sheet.sheet_id
    assert fetched.character_class == "Fighter"
    assert fetched.background == "Soldier"
    assert fetched.level == 5
    assert fetched.ability_scores.strength == 18
    assert fetched.ability_scores.constitution == 16
    assert fetched.skills == {"athletics": 7, "perception": 3}
    assert fetched.equipment == ["longsword", "shield"]


def test_dnd5e_sheet_current_hp_max_hp_distinct(session):  # type: ignore[no-untyped-def]
    """current_hp and maximum_hp are stored as distinct integer columns."""
    story = make_story()
    create_story(session, story)
    sheet = _make_dnd5e_sheet(str(story.story_id))
    create_rpg_base_sheet(session, _make_base_sheet_from_dnd5e(sheet))
    create_dnd5e_sheet(session, sheet)
    session.commit()

    fetched = get_dnd5e_sheet(session, sheet.sheet_id)
    assert fetched is not None
    assert fetched.current_hp == 40
    assert fetched.maximum_hp == 52
    assert fetched.current_hp != fetched.maximum_hp


def test_dnd5e_sheet_spell_slots_round_trip(session):  # type: ignore[no-untyped-def]
    """spell_slots: dict[int, SpellSlotLevel] survives round-trip with used/total."""
    story = make_story()
    create_story(session, story)
    sheet = _make_dnd5e_sheet(str(story.story_id))
    create_rpg_base_sheet(session, _make_base_sheet_from_dnd5e(sheet))
    create_dnd5e_sheet(session, sheet)
    session.commit()

    fetched = get_dnd5e_sheet(session, sheet.sheet_id)
    assert fetched is not None
    assert 1 in fetched.spell_slots
    assert 2 in fetched.spell_slots
    assert fetched.spell_slots[1].total == 2
    assert fetched.spell_slots[1].used == 1
    assert fetched.spell_slots[2].total == 1
    assert fetched.spell_slots[2].used == 0


def test_dnd5e_sheet_base_fk_chain(session):  # type: ignore[no-untyped-def]
    """Dnd5e sheet FK → rpg_character_sheet_bases (not directly to stories)."""
    # The Dnd5e table FK is to rpg_character_sheet_bases.
    # If we try to insert a Dnd5eCharacterSheetORM row without the base row,
    # we should get an IntegrityError.
    from afterworlds.persistence.orm.character_sheet import Dnd5eCharacterSheetORM

    story = make_story()
    create_story(session, story)

    non_existent_base_id = str(uuid4())
    dnd_row = Dnd5eCharacterSheetORM(
        sheet_id=non_existent_base_id,
        character_class="Rogue",
        background="Criminal",
        level=1,
        ability_scores={
            "strength": 10,
            "dexterity": 16,
            "constitution": 12,
            "intelligence": 13,
            "wisdom": 10,
            "charisma": 8,
        },
        skills={},
        equipment=[],
        current_hp=8,
        maximum_hp=8,
        spell_slots={},
    )
    session.add(dnd_row)
    with pytest.raises(IntegrityError):
        session.flush()


def test_dnd5e_sheet_requires_base_row(session):  # type: ignore[no-untyped-def]
    """create_dnd5e_sheet raises ValueError when no base row exists."""
    sheet = _make_dnd5e_sheet(str(uuid4()))
    with pytest.raises(ValueError, match="create_rpg_base_sheet"):
        create_dnd5e_sheet(session, sheet)


def test_update_dnd5e_sheet(session):  # type: ignore[no-untyped-def]
    """update_dnd5e_sheet changes level, current_hp, and spell_slots."""
    story = make_story()
    create_story(session, story)
    sheet = _make_dnd5e_sheet(str(story.story_id))
    create_rpg_base_sheet(session, _make_base_sheet_from_dnd5e(sheet))
    create_dnd5e_sheet(session, sheet)
    session.commit()

    updated = sheet.model_copy(
        update={
            "level": 6,
            "current_hp": 30,
            "spell_slots": {1: SpellSlotLevel(total=3, used=2)},
        }
    )
    update_dnd5e_sheet(session, updated)
    session.commit()

    fetched = get_dnd5e_sheet(session, sheet.sheet_id)
    assert fetched is not None
    assert fetched.level == 6
    assert fetched.current_hp == 30
    assert fetched.spell_slots[1].total == 3
    assert fetched.spell_slots[1].used == 2


def test_delete_dnd5e_sheet(session):  # type: ignore[no-untyped-def]
    """delete_dnd5e_sheet removes both base and dnd5e rows."""
    story = make_story()
    create_story(session, story)
    sheet = _make_dnd5e_sheet(str(story.story_id))
    create_rpg_base_sheet(session, _make_base_sheet_from_dnd5e(sheet))
    create_dnd5e_sheet(session, sheet)
    session.commit()

    assert delete_dnd5e_sheet(session, sheet.sheet_id) is True
    session.commit()
    assert get_dnd5e_sheet(session, sheet.sheet_id) is None
    assert get_rpg_base_sheet(session, sheet.sheet_id) is None


# ---------------------------------------------------------------------------
# active_conditions round-trips (Fix 2b, CRD Issue 15 remediation)
# ---------------------------------------------------------------------------


def _make_condition(
    sheet_id: object,
    identifier: str = "poisoned",
    display_label: str = "Poisoned",
    visibility: ConditionVisibility = ConditionVisibility.VISIBLE,
) -> Dnd5eActiveCondition:
    from uuid import UUID

    return Dnd5eActiveCondition(
        sheet_id=sheet_id if isinstance(sheet_id, UUID) else UUID(str(sheet_id)),
        identifier=identifier,
        display_label=display_label,
        source="test",
        visibility=visibility,
    )


def _make_dnd5e_sheet_with_conditions(
    story_id: str,
    conditions: list[Dnd5eActiveCondition],
) -> Dnd5eCharacterSheet:

    sheet = _make_dnd5e_sheet(story_id)
    return sheet.model_copy(update={"active_conditions": conditions})


def test_active_conditions_empty_round_trip(session):  # type: ignore[no-untyped-def]
    """Sheet with no active_conditions persists and reloads as empty list."""
    story = make_story()
    create_story(session, story)
    sheet = _make_dnd5e_sheet(str(story.story_id))
    create_rpg_base_sheet(session, _make_base_sheet_from_dnd5e(sheet))
    create_dnd5e_sheet(session, sheet)
    session.commit()

    fetched = get_dnd5e_sheet(session, sheet.sheet_id)
    assert fetched is not None
    assert fetched.active_conditions == []


def test_active_conditions_create_round_trip(session):  # type: ignore[no-untyped-def]
    """Active conditions persist and reload via create_dnd5e_sheet."""
    story = make_story()
    create_story(session, story)
    base = _make_dnd5e_sheet(str(story.story_id))
    cond = _make_condition(base.sheet_id)
    sheet = _make_dnd5e_sheet_with_conditions(str(story.story_id), [cond])
    create_rpg_base_sheet(session, _make_base_sheet_from_dnd5e(sheet))
    create_dnd5e_sheet(session, sheet)
    session.commit()

    fetched = get_dnd5e_sheet(session, sheet.sheet_id)
    assert fetched is not None
    assert len(fetched.active_conditions) == 1
    assert fetched.active_conditions[0].identifier == "poisoned"
    assert fetched.active_conditions[0].display_label == "Poisoned"
    assert fetched.active_conditions[0].visibility == ConditionVisibility.VISIBLE


def test_active_conditions_update_round_trip(session):  # type: ignore[no-untyped-def]
    """update_dnd5e_sheet syncs active_conditions (delete-and-recreate)."""
    story = make_story()
    create_story(session, story)
    sheet = _make_dnd5e_sheet(str(story.story_id))
    create_rpg_base_sheet(session, _make_base_sheet_from_dnd5e(sheet))
    create_dnd5e_sheet(session, sheet)
    session.commit()

    # Add a condition on update
    cond = _make_condition(
        sheet.sheet_id, identifier="frightened", display_label="Frightened"
    )
    updated = sheet.model_copy(update={"active_conditions": [cond]})
    update_dnd5e_sheet(session, updated)
    session.commit()

    fetched = get_dnd5e_sheet(session, sheet.sheet_id)
    assert fetched is not None
    assert len(fetched.active_conditions) == 1
    assert fetched.active_conditions[0].identifier == "frightened"


def test_active_conditions_update_clears_old(session):  # type: ignore[no-untyped-def]
    """update_dnd5e_sheet replaces all conditions, removing old ones."""
    story = make_story()
    create_story(session, story)
    sheet = _make_dnd5e_sheet(str(story.story_id))
    old_cond2 = _make_condition(sheet.sheet_id, identifier="poisoned")
    sheet = sheet.model_copy(update={"active_conditions": [old_cond2]})
    create_rpg_base_sheet(session, _make_base_sheet_from_dnd5e(sheet))
    create_dnd5e_sheet(session, sheet)
    session.commit()

    # Replace with a different condition
    new_cond = _make_condition(
        sheet.sheet_id, identifier="blinded", display_label="Blinded"
    )
    updated = sheet.model_copy(update={"active_conditions": [new_cond]})
    update_dnd5e_sheet(session, updated)
    session.commit()

    fetched = get_dnd5e_sheet(session, sheet.sheet_id)
    assert fetched is not None
    assert len(fetched.active_conditions) == 1
    assert fetched.active_conditions[0].identifier == "blinded"


def test_active_conditions_hidden_persists(session):  # type: ignore[no-untyped-def]
    """HIDDEN conditions persist visibility correctly."""
    story = make_story()
    create_story(session, story)
    sheet = _make_dnd5e_sheet(str(story.story_id))
    cond = _make_condition(
        sheet.sheet_id,
        identifier="cursed",
        display_label="Cursed",
        visibility=ConditionVisibility.HIDDEN,
    )
    sheet = sheet.model_copy(update={"active_conditions": [cond]})
    create_rpg_base_sheet(session, _make_base_sheet_from_dnd5e(sheet))
    create_dnd5e_sheet(session, sheet)
    session.commit()

    fetched = get_dnd5e_sheet(session, sheet.sheet_id)
    assert fetched is not None
    assert fetched.active_conditions[0].visibility == ConditionVisibility.HIDDEN
