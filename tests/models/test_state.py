"""Unit tests for WorldState and CharacterState.

Key invariants tested:
- Static / dynamic partition is structural (nested sub-models, not comments)
- CharacterState scope is limited to runtime/mechanical data
- Narrative canon / profile / relationship facts are not modeled here
"""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from afterworlds.models.state import (
    CharacterState,
    CharacterStateDynamicPartition,
    CharacterStateStaticPartition,
    WorldState,
    WorldStateDynamicPartition,
    WorldStateStaticPartition,
)
from tests.models.factories import make_datetime


class TestWorldStateStaticPartition:
    def test_instantiation_valid(self) -> None:
        static = WorldStateStaticPartition(setting_name="The Shattered Realms")
        assert static.setting_name == "The Shattered Realms"
        assert static.world_rules == []
        assert static.geography is None
        assert static.time_period is None

    def test_all_optional_fields(self) -> None:
        static = WorldStateStaticPartition(
            setting_name="X",
            world_rules=["Magic is rare"],
            geography="Archipelago",
            time_period="Medieval",
        )
        assert "Magic is rare" in static.world_rules
        assert static.geography == "Archipelago"

    def test_missing_required_field(self) -> None:
        with pytest.raises(ValidationError):
            WorldStateStaticPartition()  # type: ignore[call-arg]


class TestWorldStateDynamicPartition:
    def test_all_fields_optional(self) -> None:
        dynamic = WorldStateDynamicPartition()
        assert dynamic.current_location is None
        assert dynamic.time_of_day is None
        assert dynamic.weather is None
        assert dynamic.faction_standings == {}

    def test_populated(self) -> None:
        dynamic = WorldStateDynamicPartition(
            current_location="The Docks",
            faction_standings={"Thieves Guild": "neutral"},
        )
        assert dynamic.current_location == "The Docks"
        assert dynamic.faction_standings["Thieves Guild"] == "neutral"


class TestWorldState:
    def test_instantiation_valid(self) -> None:
        state = WorldState(
            story_id=uuid4(),
            static=WorldStateStaticPartition(setting_name="Ash Plains"),
            updated_at=make_datetime(),
        )
        assert state.static.setting_name == "Ash Plains"
        assert isinstance(state.dynamic, WorldStateDynamicPartition)

    def test_static_dynamic_partition_is_structural(self) -> None:
        """The partition must be represented as distinct sub-model fields."""
        state = WorldState(
            story_id=uuid4(),
            static=WorldStateStaticPartition(setting_name="X"),
            updated_at=make_datetime(),
        )
        assert hasattr(state, "static")
        assert hasattr(state, "dynamic")
        assert isinstance(state.static, WorldStateStaticPartition)
        assert isinstance(state.dynamic, WorldStateDynamicPartition)

    def test_static_and_dynamic_are_separate_types(self) -> None:
        """Static and dynamic partitions are distinct model types."""
        assert WorldStateStaticPartition is not WorldStateDynamicPartition

    def test_world_state_id_auto_generated(self) -> None:
        s1 = WorldState(
            story_id=uuid4(),
            static=WorldStateStaticPartition(setting_name="A"),
            updated_at=make_datetime(),
        )
        s2 = WorldState(
            story_id=uuid4(),
            static=WorldStateStaticPartition(setting_name="B"),
            updated_at=make_datetime(),
        )
        assert s1.world_state_id != s2.world_state_id

    def test_missing_static_raises(self) -> None:
        with pytest.raises(ValidationError):
            WorldState(
                story_id=uuid4(),
                updated_at=make_datetime(),
            )  # type: ignore[call-arg]


class TestCharacterStateStaticPartition:
    def test_instantiation_valid(self) -> None:
        static = CharacterStateStaticPartition(character_name="Elowen Dusk")
        assert static.character_name == "Elowen Dusk"

    def test_missing_name_raises(self) -> None:
        with pytest.raises(ValidationError):
            CharacterStateStaticPartition()  # type: ignore[call-arg]


class TestCharacterStateDynamicPartition:
    def test_all_fields_optional(self) -> None:
        dynamic = CharacterStateDynamicPartition()
        assert dynamic.current_location is None
        assert dynamic.status_effects == []
        assert dynamic.relationship_meters == {}
        assert dynamic.inventory == []

    def test_populated(self) -> None:
        dynamic = CharacterStateDynamicPartition(
            current_location="Tavern",
            status_effects=["poisoned"],
            inventory=["torch", "rope"],
        )
        assert dynamic.current_location == "Tavern"
        assert "poisoned" in dynamic.status_effects

    def test_no_story_bible_narrative_fields(self) -> None:
        """CharacterState dynamic partition must not carry narrative canon."""
        dynamic = CharacterStateDynamicPartition()
        # Story Bible fields like backstory, personality, and goals
        # do NOT belong in CharacterState
        assert not hasattr(dynamic, "backstory")
        assert not hasattr(dynamic, "personality_traits")
        assert not hasattr(dynamic, "goals")
        assert not hasattr(dynamic, "secrets")
        assert not hasattr(dynamic, "alignment")


class TestCharacterState:
    def test_instantiation_valid(self) -> None:
        state = CharacterState(
            story_id=uuid4(),
            static=CharacterStateStaticPartition(character_name="Elowen"),
            updated_at=make_datetime(),
        )
        assert state.static.character_name == "Elowen"
        assert isinstance(state.dynamic, CharacterStateDynamicPartition)

    def test_static_dynamic_partition_is_structural(self) -> None:
        """The partition must be represented as distinct sub-model fields."""
        state = CharacterState(
            story_id=uuid4(),
            static=CharacterStateStaticPartition(character_name="X"),
            updated_at=make_datetime(),
        )
        assert hasattr(state, "static")
        assert hasattr(state, "dynamic")
        assert isinstance(state.static, CharacterStateStaticPartition)
        assert isinstance(state.dynamic, CharacterStateDynamicPartition)

    def test_character_state_scope_boundary(self) -> None:
        """CharacterState must not absorb Story Bible responsibilities."""
        state = CharacterState(
            story_id=uuid4(),
            static=CharacterStateStaticPartition(character_name="X"),
            updated_at=make_datetime(),
        )
        # Story Bible character entry fields — must NOT be on CharacterState
        assert not hasattr(state, "backstory")
        assert not hasattr(state, "goals")
        assert not hasattr(state, "secrets")
        assert not hasattr(state, "relationship_history")
        assert not hasattr(state, "personality_traits")

    def test_character_state_id_auto_generated(self) -> None:
        c1 = CharacterState(
            story_id=uuid4(),
            static=CharacterStateStaticPartition(character_name="A"),
            updated_at=make_datetime(),
        )
        c2 = CharacterState(
            story_id=uuid4(),
            static=CharacterStateStaticPartition(character_name="B"),
            updated_at=make_datetime(),
        )
        assert c1.character_state_id != c2.character_state_id
