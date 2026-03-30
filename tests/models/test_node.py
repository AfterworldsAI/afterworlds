"""Unit tests for Node, StateDelta, NodeMetadata, and mode metadata models.

Key invariants tested:
- ``branching_logic`` exists on the base Node schema
- Mode metadata does not replace ``branching_logic``
- RPG session state fields are not present on Node
- Discriminated union selects the correct metadata type
"""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from afterworlds.models.enums import IntentType
from afterworlds.models.node import (
    BranchingNodeMetadata,
    Node,
    NodeMetadata,
    RpgNodeMetadata,
    StateDelta,
    WritingNodeMetadata,
)
from tests.models.factories import make_datetime


def _make_node(**kwargs: object) -> Node:
    defaults: dict[str, object] = {
        "chapter_id": uuid4(),
        "content": "The door creaks open.",
        "intent_type": IntentType.ACTION,
    }
    defaults.update(kwargs)
    return Node(**defaults)  # type: ignore[arg-type]


class TestStateDelta:
    def test_instantiation_empty(self) -> None:
        delta = StateDelta()
        assert delta.world_changes == {}
        assert delta.character_changes == {}
        assert delta.inventory_gains == []
        assert delta.inventory_losses == []

    def test_instantiation_with_values(self) -> None:
        delta = StateDelta(
            world_changes={"king_trust": "hostile → neutral"},
            inventory_gains=["iron key"],
            inventory_losses=["50 gold"],
        )
        assert delta.world_changes["king_trust"] == "hostile → neutral"
        assert "iron key" in delta.inventory_gains
        assert "50 gold" in delta.inventory_losses

    def test_invalid_world_changes_value_type(self) -> None:
        with pytest.raises(ValidationError):
            StateDelta(world_changes={"key": 123})  # type: ignore[dict-item]


class TestNodeMetadata:
    def test_all_fields_optional(self) -> None:
        meta = NodeMetadata()
        assert meta.pov is None
        assert meta.location is None
        assert meta.mood is None
        assert meta.tense is None
        assert meta.timestamp is None

    def test_populated(self) -> None:
        meta = NodeMetadata(
            pov="third-person limited",
            location="The Docks",
            mood="tense",
            tense="past",
            timestamp=make_datetime(),
        )
        assert meta.location == "The Docks"

    def test_invalid_timestamp_type(self) -> None:
        with pytest.raises(ValidationError):
            NodeMetadata(timestamp="not-a-datetime")  # type: ignore[arg-type]


class TestNode:
    def test_instantiation_minimal(self) -> None:
        node = _make_node()
        assert node.content == "The door creaks open."
        assert node.branching_logic == []
        assert node.mode_metadata is None
        assert isinstance(node.state_delta, StateDelta)
        assert isinstance(node.metadata, NodeMetadata)

    def test_branching_logic_is_base_field(self) -> None:
        """branching_logic must exist on the base Node — not only on mode metadata."""
        node = _make_node()
        assert hasattr(node, "branching_logic")
        assert isinstance(node.branching_logic, list)

    def test_branching_logic_with_next_nodes(self) -> None:
        next1, next2 = uuid4(), uuid4()
        node = _make_node(branching_logic=[next1, next2])
        assert next1 in node.branching_logic
        assert next2 in node.branching_logic

    def test_invalid_intent_type(self) -> None:
        with pytest.raises(ValidationError):
            _make_node(intent_type="invalid")  # type: ignore[arg-type]

    def test_mode_metadata_none(self) -> None:
        node = _make_node(mode_metadata=None)
        assert node.mode_metadata is None

    def test_rpg_mode_metadata(self) -> None:
        meta = RpgNodeMetadata(
            mechanical_notes="Stealth check DC 15", dice_results=[12]
        )
        node = _make_node(mode_metadata=meta)
        assert node.mode_metadata is not None
        assert isinstance(node.mode_metadata, RpgNodeMetadata)
        assert node.mode_metadata.mode == "rpg"

    def test_branching_mode_metadata(self) -> None:
        meta = BranchingNodeMetadata(
            pacing_stage_at_beat="escalation",
            extra_branch_options=["flee", "negotiate"],
        )
        node = _make_node(mode_metadata=meta)
        assert isinstance(node.mode_metadata, BranchingNodeMetadata)

    def test_writing_mode_metadata(self) -> None:
        meta = WritingNodeMetadata(
            beat_constraints=["protagonist must learn the truth"],
            version_pointer=uuid4(),
        )
        node = _make_node(mode_metadata=meta)
        assert isinstance(node.mode_metadata, WritingNodeMetadata)

    def test_branching_metadata_does_not_replace_base_branching_logic(self) -> None:
        """Branching mode metadata extends branch detail but does not replace
        the base branching_logic field."""
        next_id = uuid4()
        meta = BranchingNodeMetadata(extra_branch_options=["run", "hide"])
        node = _make_node(
            branching_logic=[next_id],
            mode_metadata=meta,
        )
        # Base field still present with its value
        assert next_id in node.branching_logic
        # Mode metadata has its own extension fields
        assert isinstance(node.mode_metadata, BranchingNodeMetadata)
        assert "run" in node.mode_metadata.extra_branch_options

    def test_rpg_session_fields_not_on_node(self) -> None:
        """RPG session state (dice state, quests, combat) must not appear on Node."""
        node = _make_node()
        assert not hasattr(node, "active_quests")
        assert not hasattr(node, "dice_handling")
        assert not hasattr(node, "combat_context")
        assert not hasattr(node, "current_hp")
        assert not hasattr(node, "spell_slots")

    def test_invalid_chapter_id_type(self) -> None:
        with pytest.raises(ValidationError):
            Node(
                chapter_id="not-a-uuid",  # type: ignore[arg-type]
                content="x",
                intent_type=IntentType.ACTION,
            )
