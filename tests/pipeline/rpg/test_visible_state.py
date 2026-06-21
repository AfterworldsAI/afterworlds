"""Unit tests for RpgVisibleStateService — CRD Issue 15 Phase 7."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from afterworlds.models.character_sheet import (
    Dnd5eAbilityScores,
    Dnd5eActiveCondition,
    Dnd5eCharacterSheet,
)
from afterworlds.models.enums import ConditionVisibility
from afterworlds.pipeline.rpg.visible_state import RpgVisibleStateService

_NOW = datetime(2026, 1, 1, tzinfo=UTC)
_STORY_ID = uuid4()

_ABILITY_SCORES = Dnd5eAbilityScores(
    strength=10,
    dexterity=18,
    constitution=14,
    intelligence=12,
    wisdom=11,
    charisma=13,
)


def _make_sheet(
    *,
    name: str = "Thalindra",
    character_class: str = "Rogue",
    level: int = 5,
    current_hp: int = 30,
    maximum_hp: int = 38,
    equipment: list[str] | None = None,
    conditions: list[Dnd5eActiveCondition] | None = None,
) -> Dnd5eCharacterSheet:
    return Dnd5eCharacterSheet(
        story_id=_STORY_ID,
        rules_package_id="dnd5e-v1",
        character_name=name,
        character_class=character_class,
        background="Criminal",
        level=level,
        ability_scores=_ABILITY_SCORES,
        equipment=equipment or [],
        current_hp=current_hp,
        maximum_hp=maximum_hp,
        active_conditions=conditions or [],
        created_at=_NOW,
        updated_at=_NOW,
    )


def _make_condition(
    display_label: str,
    visibility: ConditionVisibility,
    sheet_id: UUID | None = None,
) -> Dnd5eActiveCondition:
    return Dnd5eActiveCondition(
        sheet_id=sheet_id or uuid4(),
        identifier="test_condition",
        display_label=display_label,
        source="test",
        visibility=visibility,
    )


# ---------------------------------------------------------------------------
# Character field mapping
# ---------------------------------------------------------------------------


def test_build_maps_character_fields() -> None:
    svc = RpgVisibleStateService()
    sheet = _make_sheet(
        name="Aldric",
        character_class="Fighter",
        level=7,
        current_hp=42,
        maximum_hp=58,
    )
    state = svc.build(sheet)
    char = state.character
    assert char.character_name == "Aldric"
    assert char.character_class == "Fighter"
    assert char.level == 7
    assert char.current_hp == 42
    assert char.maximum_hp == 58


def test_build_empty_conditions_produces_empty_tuple() -> None:
    svc = RpgVisibleStateService()
    sheet = _make_sheet(conditions=[])
    state = svc.build(sheet)
    assert state.character.active_conditions == ()


# ---------------------------------------------------------------------------
# Condition visibility filtering
# ---------------------------------------------------------------------------


def test_build_includes_visible_conditions() -> None:
    svc = RpgVisibleStateService()
    cond = _make_condition("Poisoned", ConditionVisibility.VISIBLE)
    sheet = _make_sheet(conditions=[cond])
    state = svc.build(sheet)
    assert state.character.active_conditions == ("Poisoned",)


def test_build_excludes_hidden_conditions() -> None:
    svc = RpgVisibleStateService()
    cond = _make_condition("Cursed", ConditionVisibility.HIDDEN)
    sheet = _make_sheet(conditions=[cond])
    state = svc.build(sheet)
    assert state.character.active_conditions == ()


def test_build_filters_mixed_conditions() -> None:
    svc = RpgVisibleStateService()
    visible = _make_condition("Frightened", ConditionVisibility.VISIBLE)
    hidden = _make_condition("Tracking Mark", ConditionVisibility.HIDDEN)
    sheet = _make_sheet(conditions=[visible, hidden])
    state = svc.build(sheet)
    assert state.character.active_conditions == ("Frightened",)


# ---------------------------------------------------------------------------
# Inventory mapping
# ---------------------------------------------------------------------------


def test_build_maps_equipment_to_inventory() -> None:
    svc = RpgVisibleStateService()
    sheet = _make_sheet(equipment=["Short Sword", "Leather Armor", "Thieves' Tools"])
    state = svc.build(sheet)
    names = [item.name for item in state.inventory]
    assert names == ["Short Sword", "Leather Armor", "Thieves' Tools"]


def test_build_empty_equipment_produces_empty_inventory() -> None:
    svc = RpgVisibleStateService()
    sheet = _make_sheet(equipment=[])
    state = svc.build(sheet)
    assert state.inventory == ()


# ---------------------------------------------------------------------------
# v1 deferred fields
# ---------------------------------------------------------------------------


def test_build_location_is_none() -> None:
    svc = RpgVisibleStateService()
    state = svc.build(_make_sheet())
    assert state.location is None


def test_build_relationship_meters_and_objectives_empty() -> None:
    svc = RpgVisibleStateService()
    state = svc.build(_make_sheet())
    assert state.relationship_meters == ()
    assert state.known_objectives == ()
