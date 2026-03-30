"""Unit tests for RPG character sheet models.

Key invariants tested:
- Character sheet is a distinct Pydantic model (not dict / blob / freeform field)
- current_hp cannot exceed maximum_hp
- Ability scores are within valid D&D 5e range (1–30)
- Spell slot used cannot exceed total
- rules_package_id is required
- Character sheet is the source of truth for HP and spell slots
"""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import BaseModel, ValidationError

from afterworlds.models.character_sheet import (
    AbilityScores,
    Dnd5eCharacterSheet,
    RpgCharacterSheetBase,
    SpellSlotLevel,
)


def _make_scores(**overrides: int) -> AbilityScores:
    defaults = dict(
        strength=10,
        dexterity=12,
        constitution=14,
        intelligence=8,
        wisdom=13,
        charisma=11,
    )
    defaults.update(overrides)
    return AbilityScores(**defaults)


def _make_sheet(**overrides: object) -> Dnd5eCharacterSheet:
    now = datetime.now(UTC)
    defaults: dict[str, object] = {
        "story_id": uuid4(),
        "rules_package_id": "dnd5e-v1",
        "character_name": "Elowen Dusk",
        "character_class": "Rogue",
        "background": "Criminal",
        "ability_scores": _make_scores(),
        "current_hp": 10,
        "maximum_hp": 10,
        "created_at": now,
        "updated_at": now,
    }
    defaults.update(overrides)
    return Dnd5eCharacterSheet(**defaults)  # type: ignore[arg-type]


class TestAbilityScores:
    def test_valid_scores(self) -> None:
        scores = _make_scores()
        assert scores.strength == 10
        assert scores.dexterity == 12

    def test_minimum_valid_score(self) -> None:
        scores = _make_scores(strength=1)
        assert scores.strength == 1

    def test_maximum_valid_score(self) -> None:
        scores = _make_scores(charisma=30)
        assert scores.charisma == 30

    def test_score_below_minimum_raises(self) -> None:
        with pytest.raises(ValidationError, match="strength"):
            _make_scores(strength=0)

    def test_score_above_maximum_raises(self) -> None:
        with pytest.raises(ValidationError, match="charisma"):
            _make_scores(charisma=31)

    def test_all_six_scores_present(self) -> None:
        scores = _make_scores()
        assert hasattr(scores, "strength")
        assert hasattr(scores, "dexterity")
        assert hasattr(scores, "constitution")
        assert hasattr(scores, "intelligence")
        assert hasattr(scores, "wisdom")
        assert hasattr(scores, "charisma")

    def test_invalid_type_raises(self) -> None:
        with pytest.raises(ValidationError):
            AbilityScores(
                strength="high",  # type: ignore[arg-type]
                dexterity=10,
                constitution=10,
                intelligence=10,
                wisdom=10,
                charisma=10,
            )


class TestSpellSlotLevel:
    def test_valid_slot(self) -> None:
        slot = SpellSlotLevel(total=3, used=1)
        assert slot.total == 3
        assert slot.used == 1

    def test_fully_expended(self) -> None:
        slot = SpellSlotLevel(total=2, used=2)
        assert slot.used == slot.total

    def test_empty_slot(self) -> None:
        slot = SpellSlotLevel(total=0, used=0)
        assert slot.total == 0

    def test_used_exceeds_total_raises(self) -> None:
        with pytest.raises(ValidationError, match="used"):
            SpellSlotLevel(total=2, used=3)

    def test_negative_total_raises(self) -> None:
        with pytest.raises(ValidationError):
            SpellSlotLevel(total=-1, used=0)

    def test_negative_used_raises(self) -> None:
        with pytest.raises(ValidationError):
            SpellSlotLevel(total=2, used=-1)

    def test_invalid_type_raises(self) -> None:
        with pytest.raises(ValidationError):
            SpellSlotLevel(total="three", used=0)  # type: ignore[arg-type]


class TestRpgCharacterSheetBase:
    def test_instantiation_valid(self) -> None:
        now = datetime.now(UTC)
        base = RpgCharacterSheetBase(
            story_id=uuid4(),
            rules_package_id="dnd5e-v1",
            character_name="Elowen",
            created_at=now,
            updated_at=now,
        )
        assert base.character_name == "Elowen"
        assert base.rules_package_id == "dnd5e-v1"

    def test_rules_package_id_required(self) -> None:
        now = datetime.now(UTC)
        with pytest.raises(ValidationError):
            RpgCharacterSheetBase(
                story_id=uuid4(),
                character_name="X",
                created_at=now,
                updated_at=now,
            )  # type: ignore[call-arg]

    def test_sheet_id_auto_generated(self) -> None:
        now = datetime.now(UTC)
        b1 = RpgCharacterSheetBase(
            story_id=uuid4(),
            rules_package_id="dnd5e-v1",
            character_name="A",
            created_at=now,
            updated_at=now,
        )
        b2 = RpgCharacterSheetBase(
            story_id=uuid4(),
            rules_package_id="dnd5e-v1",
            character_name="B",
            created_at=now,
            updated_at=now,
        )
        assert b1.sheet_id != b2.sheet_id


class TestDnd5eCharacterSheet:
    def test_instantiation_valid(self) -> None:
        sheet = _make_sheet()
        assert sheet.character_name == "Elowen Dusk"
        assert sheet.character_class == "Rogue"
        assert sheet.background == "Criminal"
        assert sheet.rules_package_id == "dnd5e-v1"
        assert sheet.current_hp == 10
        assert sheet.maximum_hp == 10

    def test_is_pydantic_base_model(self) -> None:
        """Character sheet is a Pydantic model — not a dict or blob."""
        sheet = _make_sheet()
        assert isinstance(sheet, BaseModel)
        assert isinstance(sheet, Dnd5eCharacterSheet)

    def test_is_not_dict(self) -> None:
        sheet = _make_sheet()
        assert not isinstance(sheet, dict)
        assert not isinstance(sheet, str)

    def test_required_fields_all_present(self) -> None:
        sheet = _make_sheet()
        assert hasattr(sheet, "character_name")
        assert hasattr(sheet, "character_class")
        assert hasattr(sheet, "background")
        assert hasattr(sheet, "ability_scores")
        assert hasattr(sheet, "skills")
        assert hasattr(sheet, "equipment")
        assert hasattr(sheet, "current_hp")
        assert hasattr(sheet, "maximum_hp")
        assert hasattr(sheet, "spell_slots")
        assert hasattr(sheet, "rules_package_id")

    def test_current_hp_below_maximum_valid(self) -> None:
        sheet = _make_sheet(current_hp=5, maximum_hp=10)
        assert sheet.current_hp == 5
        assert sheet.maximum_hp == 10

    def test_current_hp_equals_maximum_valid(self) -> None:
        sheet = _make_sheet(current_hp=10, maximum_hp=10)
        assert sheet.current_hp == sheet.maximum_hp

    def test_current_hp_exceeds_maximum_raises(self) -> None:
        with pytest.raises(ValidationError, match="current_hp"):
            _make_sheet(current_hp=11, maximum_hp=10)

    def test_mutable_current_hp(self) -> None:
        """current_hp can differ from maximum_hp — supports damage tracking."""
        sheet = _make_sheet(current_hp=3, maximum_hp=12)
        assert sheet.current_hp != sheet.maximum_hp

    def test_spell_slots_empty_by_default(self) -> None:
        sheet = _make_sheet()
        assert sheet.spell_slots == {}

    def test_spell_slots_populated(self) -> None:
        slots = {1: SpellSlotLevel(total=4, used=2), 2: SpellSlotLevel(total=3, used=0)}
        sheet = _make_sheet(spell_slots=slots)
        assert sheet.spell_slots[1].total == 4
        assert sheet.spell_slots[1].used == 2

    def test_spell_slots_with_expended_slot(self) -> None:
        slots = {1: SpellSlotLevel(total=2, used=2)}
        sheet = _make_sheet(spell_slots=slots)
        assert sheet.spell_slots[1].used == sheet.spell_slots[1].total

    def test_skills_empty_by_default(self) -> None:
        sheet = _make_sheet()
        assert sheet.skills == {}

    def test_skills_populated(self) -> None:
        sheet = _make_sheet(skills={"Stealth": 5, "Perception": 3})
        assert sheet.skills["Stealth"] == 5

    def test_equipment_empty_by_default(self) -> None:
        sheet = _make_sheet()
        assert sheet.equipment == []

    def test_equipment_populated(self) -> None:
        sheet = _make_sheet(equipment=["shortsword", "thieves tools"])
        assert "shortsword" in sheet.equipment

    def test_level_default(self) -> None:
        sheet = _make_sheet()
        assert sheet.level == 1

    def test_level_valid_range(self) -> None:
        sheet = _make_sheet(level=20)
        assert sheet.level == 20

    def test_level_above_max_raises(self) -> None:
        with pytest.raises(ValidationError):
            _make_sheet(level=21)

    def test_level_below_min_raises(self) -> None:
        with pytest.raises(ValidationError):
            _make_sheet(level=0)

    def test_invalid_character_class_type(self) -> None:
        with pytest.raises(ValidationError):
            _make_sheet(character_class=42)  # type: ignore[arg-type]

    def test_ability_scores_are_typed_model(self) -> None:
        sheet = _make_sheet()
        assert isinstance(sheet.ability_scores, AbilityScores)

    def test_sheet_is_source_of_truth_for_hp_not_session_state(self) -> None:
        """HP must live on the sheet.  RPG session state must not own HP."""
        from afterworlds.models.enums import DiceHandling
        from afterworlds.models.session import RpgSessionState

        sheet = _make_sheet(current_hp=7, maximum_hp=10)
        session = RpgSessionState(
            story_id=sheet.story_id,
            character_sheet_id=sheet.sheet_id,
            dice_handling=DiceHandling.PLAYER_ROLLS,
        )
        # HP is on the sheet
        assert sheet.current_hp == 7
        # Session state has no competing HP fields
        assert not hasattr(session, "current_hp")
        assert not hasattr(session, "maximum_hp")

    def test_sheet_is_source_of_truth_for_spell_slots_not_session_state(self) -> None:
        """Spell slots must live on the sheet.  RPG session state must not own them."""
        from afterworlds.models.enums import DiceHandling
        from afterworlds.models.session import RpgSessionState

        slots = {1: SpellSlotLevel(total=3, used=1)}
        sheet = _make_sheet(spell_slots=slots)
        session = RpgSessionState(
            story_id=sheet.story_id,
            character_sheet_id=sheet.sheet_id,
            dice_handling=DiceHandling.AI_ROLLS,
        )
        # Spell slots are on the sheet
        assert 1 in sheet.spell_slots
        # Session state has no spell slots
        assert not hasattr(session, "spell_slots")
