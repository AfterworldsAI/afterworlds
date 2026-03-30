"""Unit tests for Turn model.

Key invariants tested:
- Turn has its own identity (turn_id) distinct from node_id
- Minimal field contract is present and sufficient
- Turn and Node are distinct types (no conflation)
"""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from afterworlds.models.enums import IntentType
from afterworlds.models.node import Node
from afterworlds.models.turn import Turn
from tests.models.factories import make_datetime


def _make_turn(**kwargs: object) -> Turn:
    defaults: dict[str, object] = {
        "user_input": "I try the door.",
        "assistant_output": "The door swings open with a groan.",
        "timestamp": make_datetime(),
        "intent_classification": IntentType.ACTION,
    }
    defaults.update(kwargs)
    return Turn(**defaults)  # type: ignore[arg-type]


class TestTurn:
    def test_instantiation_valid(self) -> None:
        turn = _make_turn()
        assert turn.user_input == "I try the door."
        assert turn.assistant_output == "The door swings open with a groan."
        assert turn.intent_classification == IntentType.ACTION
        assert turn.node_id is None

    def test_turn_id_auto_generated(self) -> None:
        t1 = _make_turn()
        t2 = _make_turn()
        assert t1.turn_id != t2.turn_id

    def test_node_id_optional_absent(self) -> None:
        turn = _make_turn()
        assert turn.node_id is None

    def test_node_id_optional_none_explicit(self) -> None:
        turn = _make_turn(node_id=None)
        assert turn.node_id is None

    def test_node_id_populated(self) -> None:
        uid = uuid4()
        turn = _make_turn(node_id=uid)
        assert turn.node_id == uid

    def test_invalid_intent_type(self) -> None:
        with pytest.raises(ValidationError):
            _make_turn(intent_classification="invalid")  # type: ignore[arg-type]

    def test_invalid_timestamp_type(self) -> None:
        with pytest.raises(ValidationError):
            _make_turn(timestamp="not-a-datetime")  # type: ignore[arg-type]

    def test_turn_distinct_from_node(self) -> None:
        """Turn and Node are distinct types — not the same concept."""
        turn = _make_turn()
        assert type(turn) is not Node
        assert not isinstance(turn, Node)

    def test_turn_has_minimal_field_contract(self) -> None:
        """All minimal contract fields must be present on a Turn instance."""
        turn = _make_turn(node_id=uuid4())
        assert hasattr(turn, "turn_id")
        assert hasattr(turn, "user_input")
        assert hasattr(turn, "assistant_output")
        assert hasattr(turn, "timestamp")
        assert hasattr(turn, "intent_classification")
        assert hasattr(turn, "node_id")

    def test_turn_does_not_have_node_fields(self) -> None:
        """Turn must not absorb Node fields — they remain distinct."""
        turn = _make_turn()
        assert not hasattr(turn, "content")
        assert not hasattr(turn, "state_delta")
        assert not hasattr(turn, "branching_logic")
        assert not hasattr(turn, "mode_metadata")
        assert not hasattr(turn, "chapter_id")

    def test_all_intent_types_valid(self) -> None:
        for intent in IntentType:
            turn = _make_turn(intent_classification=intent)
            assert turn.intent_classification == intent
