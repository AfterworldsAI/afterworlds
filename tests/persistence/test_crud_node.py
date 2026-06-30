"""Tests for Node and Turn CRUD operations."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from afterworlds.models.enums import IntentType
from afterworlds.models.node import (
    BranchingNodeMetadata,
    Node,
    NodeMetadata,
    RpgNodeMetadata,
    StateDelta,
    WritingNodeMetadata,
)
from afterworlds.models.turn import Turn
from afterworlds.persistence.crud.node import (
    create_node,
    create_turn,
    delete_node,
    delete_turn,
    get_node,
    get_turn,
    update_node,
)
from afterworlds.persistence.crud.story import (
    create_arc,
    create_chapter,
    create_story,
)
from tests.persistence.conftest import make_arc, make_chapter, make_story


def _make_node(chapter_id: str) -> Node:
    from uuid import UUID

    return Node(
        chapter_id=UUID(chapter_id),
        content="A dark forest path diverges before you.",
        intent_type=IntentType.IN_CHARACTER_ACTION,
    )


def _setup_chapter(session):  # type: ignore[no-untyped-def]
    """Create Story → Arc → Chapter and return the Chapter."""
    story = make_story()
    create_story(session, story)
    arc = make_arc(str(story.story_id))
    create_arc(session, arc)
    chapter = make_chapter(str(arc.arc_id))
    create_chapter(session, chapter)
    session.commit()
    return chapter


def test_node_round_trip_basic(session):  # type: ignore[no-untyped-def]
    """Round-trip a basic Node with no mode_metadata."""
    chapter = _setup_chapter(session)
    node = _make_node(str(chapter.chapter_id))
    created = create_node(session, node)
    session.commit()

    fetched = get_node(session, created.node_id)
    assert fetched is not None
    assert fetched.node_id == node.node_id
    assert fetched.chapter_id == chapter.chapter_id
    assert fetched.content == node.content
    assert fetched.intent_type == IntentType.IN_CHARACTER_ACTION
    assert fetched.mode_metadata is None
    assert fetched.branching_logic == []


def test_node_branching_logic_is_distinct_column(session):  # type: ignore[no-untyped-def]
    """branching_logic is stored as its own column, independent of mode_metadata."""
    chapter = _setup_chapter(session)
    next_id = uuid4()
    node = Node(
        chapter_id=chapter.chapter_id,
        content="A fork in the road.",
        intent_type=IntentType.BRANCH_CHOICE,
        branching_logic=[next_id],
        mode_metadata=BranchingNodeMetadata(
            pacing_stage_at_beat="escalation",
            extra_branch_options=["Go left", "Go right"],
        ),
    )
    created = create_node(session, node)
    session.commit()

    fetched = get_node(session, created.node_id)
    assert fetched is not None
    assert fetched.branching_logic == [next_id]
    assert fetched.mode_metadata is not None
    assert isinstance(fetched.mode_metadata, BranchingNodeMetadata)


def test_node_mode_metadata_rpg_round_trip(session):  # type: ignore[no-untyped-def]
    """RpgNodeMetadata serialises/deserialises correctly."""
    chapter = _setup_chapter(session)
    node = Node(
        chapter_id=chapter.chapter_id,
        content="You roll for initiative.",
        intent_type=IntentType.IN_CHARACTER_ACTION,
        mode_metadata=RpgNodeMetadata(
            mechanical_notes="DC 15 Athletics check",
            dice_results=[12, 8],
        ),
    )
    create_node(session, node)
    session.commit()

    fetched = get_node(session, node.node_id)
    assert fetched is not None
    assert isinstance(fetched.mode_metadata, RpgNodeMetadata)
    assert fetched.mode_metadata.dice_results == [12, 8]
    assert fetched.mode_metadata.mechanical_notes == "DC 15 Athletics check"


def test_node_mode_metadata_writing_round_trip(session):  # type: ignore[no-untyped-def]
    """WritingNodeMetadata serialises/deserialises correctly."""
    chapter = _setup_chapter(session)
    ptr = uuid4()
    node = Node(
        chapter_id=chapter.chapter_id,
        content="The scene opens on a rainy night.",
        intent_type=IntentType.AUTHOR_INSTRUCTION,
        mode_metadata=WritingNodeMetadata(
            beat_constraints_snapshot=["keep it atmospheric"],
            version_pointer_refs=[ptr],
            persona_id="chiron",
            work_product_kind="prose_continuation",
        ),
    )
    create_node(session, node)
    session.commit()

    fetched = get_node(session, node.node_id)
    assert fetched is not None
    assert isinstance(fetched.mode_metadata, WritingNodeMetadata)
    assert ptr in fetched.mode_metadata.version_pointer_refs
    assert "keep it atmospheric" in fetched.mode_metadata.beat_constraints_snapshot
    assert fetched.mode_metadata.persona_id == "chiron"


def test_node_state_delta_round_trip(session):  # type: ignore[no-untyped-def]
    """StateDelta fields survive round-trip."""
    chapter = _setup_chapter(session)
    delta = StateDelta(
        world_changes={"time": "dusk"},
        inventory_gains=["rusty sword"],
    )
    node = Node(
        chapter_id=chapter.chapter_id,
        content="You find a sword.",
        intent_type=IntentType.IN_CHARACTER_ACTION,
        state_delta=delta,
    )
    create_node(session, node)
    session.commit()

    fetched = get_node(session, node.node_id)
    assert fetched is not None
    assert fetched.state_delta.world_changes == {"time": "dusk"}
    assert fetched.state_delta.inventory_gains == ["rusty sword"]


def test_node_fk_enforced(session):  # type: ignore[no-untyped-def]
    """Creating a Node with a non-existent chapter_id raises IntegrityError."""
    node = _make_node(str(uuid4()))
    with pytest.raises(IntegrityError):
        create_node(session, node)
        session.flush()


def test_update_node(session):  # type: ignore[no-untyped-def]
    """update_node changes content and mode_metadata."""
    chapter = _setup_chapter(session)
    node = _make_node(str(chapter.chapter_id))
    create_node(session, node)
    session.commit()

    updated = node.model_copy(
        update={
            "content": "Updated content",
            "mode_metadata": RpgNodeMetadata(dice_results=[20]),
        }
    )
    result = update_node(session, updated)
    session.commit()

    assert result is not None
    fetched = get_node(session, node.node_id)
    assert fetched is not None
    assert fetched.content == "Updated content"
    assert isinstance(fetched.mode_metadata, RpgNodeMetadata)
    assert fetched.mode_metadata.dice_results == [20]


def test_delete_node(session):  # type: ignore[no-untyped-def]
    """delete_node removes the row."""
    chapter = _setup_chapter(session)
    node = _make_node(str(chapter.chapter_id))
    create_node(session, node)
    session.commit()

    assert delete_node(session, node.node_id) is True
    session.commit()
    assert get_node(session, node.node_id) is None


def test_turn_round_trip_with_node(session):  # type: ignore[no-untyped-def]
    """Round-trip a Turn with a linked Node."""
    chapter = _setup_chapter(session)
    node = _make_node(str(chapter.chapter_id))
    create_node(session, node)
    session.commit()

    turn = Turn(
        user_input="Go north",
        assistant_output="You head north into the forest.",
        timestamp=datetime(2026, 1, 1, tzinfo=UTC),
        intent_classification=IntentType.IN_CHARACTER_ACTION,
        node_id=node.node_id,
    )
    created = create_turn(session, turn)
    session.commit()

    fetched = get_turn(session, created.turn_id)
    assert fetched is not None
    assert fetched.turn_id == turn.turn_id
    assert fetched.node_id == node.node_id
    assert fetched.user_input == "Go north"


def test_turn_nullable_node_id(session):  # type: ignore[no-untyped-def]
    """Turn with node_id=None persists correctly (minimal field contract)."""
    turn = Turn(
        user_input="Hello",
        assistant_output="Welcome.",
        timestamp=datetime(2026, 1, 1, tzinfo=UTC),
        intent_classification=IntentType.DIALOGUE,
        node_id=None,
    )
    create_turn(session, turn)
    session.commit()

    fetched = get_turn(session, turn.turn_id)
    assert fetched is not None
    assert fetched.node_id is None
    assert fetched.user_input == "Hello"


def test_delete_turn(session):  # type: ignore[no-untyped-def]
    """delete_turn removes the row."""
    turn = Turn(
        user_input="x",
        assistant_output="y",
        timestamp=datetime(2026, 1, 1, tzinfo=UTC),
        intent_classification=IntentType.LORE_QUESTION,
    )
    create_turn(session, turn)
    session.commit()

    assert delete_turn(session, turn.turn_id) is True
    session.commit()
    assert get_turn(session, turn.turn_id) is None


def test_delete_node_preserves_turns_with_null_node_id(session):  # type: ignore[no-untyped-def]
    """Deleting a Node must set Turn.node_id to NULL, not delete the Turn."""
    chapter = _setup_chapter(session)
    node = _make_node(str(chapter.chapter_id))
    create_node(session, node)
    session.commit()

    turn = Turn(
        user_input="Describe the forest",
        assistant_output="Tall oaks surround you.",
        timestamp=datetime(2026, 1, 1, tzinfo=UTC),
        intent_classification=IntentType.LORE_QUESTION,
        node_id=node.node_id,
    )
    create_turn(session, turn)
    session.commit()

    # Deleting the node must NOT delete the turn
    assert delete_node(session, node.node_id) is True
    session.commit()

    fetched_turn = get_turn(session, turn.turn_id)
    assert (
        fetched_turn is not None
    ), "Turn was deleted when node was deleted — cascade is wrong"
    assert (
        fetched_turn.node_id is None
    ), "Turn.node_id should be NULL after node deletion"


def test_node_metadata_timestamp_round_trip(session):  # type: ignore[no-untyped-def]
    """NodeMetadata with a datetime timestamp serialises to JSON without error."""
    chapter = _setup_chapter(session)
    node = Node(
        chapter_id=chapter.chapter_id,
        content="A moonlit clearing.",
        intent_type=IntentType.IN_CHARACTER_ACTION,
        metadata=NodeMetadata(
            pov="third_person",
            timestamp=datetime(2026, 3, 15, 21, 0, 0, tzinfo=UTC),
        ),
    )
    create_node(session, node)
    session.commit()

    fetched = get_node(session, node.node_id)
    assert fetched is not None
    assert fetched.metadata.timestamp is not None
    assert fetched.metadata.timestamp.year == 2026
    assert fetched.metadata.pov == "third_person"


def test_legacy_intent_type_action_loads_as_in_character_action(  # type: ignore[no-untyped-def]
    session,
) -> None:
    """Legacy 'action' string persisted in nodes.intent_type loads correctly.

    Rows written before the Issue 7 taxonomy rename stored 'action' as the
    wire value.  The Node field_validator must coerce it to IN_CHARACTER_ACTION
    so ORM→model conversion does not raise a validation error.
    """
    from afterworlds.persistence.orm.node import NodeORM

    chapter = _setup_chapter(session)
    row = NodeORM(
        node_id=str(uuid4()),
        chapter_id=str(chapter.chapter_id),
        content="Legacy node",
        state_delta={},
        branching_logic=[],
        intent_type="action",  # pre-Issue-7 legacy value
        metadata_={},
    )
    session.add(row)
    session.flush()

    fetched = get_node(session, chapter.chapter_id.__class__(row.node_id))
    assert fetched is not None
    assert fetched.intent_type == IntentType.IN_CHARACTER_ACTION


def test_legacy_intent_type_milestone_loads_as_beat_milestone(  # type: ignore[no-untyped-def]
    session,
) -> None:
    """Legacy 'milestone' string persisted in nodes.intent_type loads correctly."""
    from afterworlds.persistence.orm.node import NodeORM

    chapter = _setup_chapter(session)
    row = NodeORM(
        node_id=str(uuid4()),
        chapter_id=str(chapter.chapter_id),
        content="Legacy milestone node",
        state_delta={},
        branching_logic=[],
        intent_type="milestone",  # pre-Issue-7 legacy value
        metadata_={},
    )
    session.add(row)
    session.flush()

    fetched = get_node(session, chapter.chapter_id.__class__(row.node_id))
    assert fetched is not None
    assert fetched.intent_type == IntentType.BEAT_MILESTONE


def test_legacy_intent_classification_action_loads_as_in_character_action(  # type: ignore[no-untyped-def]
    session,
) -> None:
    """Legacy 'action' string in turns.intent_classification loads correctly."""
    from datetime import UTC, datetime

    from afterworlds.persistence.orm.node import NodeORM, TurnORM

    chapter = _setup_chapter(session)
    node_id = str(uuid4())
    session.add(
        NodeORM(
            node_id=node_id,
            chapter_id=str(chapter.chapter_id),
            content="Node for turn",
            state_delta={},
            branching_logic=[],
            intent_type="in_character_action",
            metadata_={},
        )
    )
    turn_id = str(uuid4())
    session.add(
        TurnORM(
            turn_id=turn_id,
            node_id=node_id,
            user_input="legacy input",
            assistant_output="legacy output",
            timestamp=datetime.now(UTC).isoformat(),
            intent_classification="action",  # pre-Issue-7 legacy value
        )
    )
    session.flush()

    fetched = get_turn(session, chapter.chapter_id.__class__(turn_id))
    assert fetched is not None
    assert fetched.intent_classification == IntentType.IN_CHARACTER_ACTION


def test_canonical_intent_values_still_load_correctly(  # type: ignore[no-untyped-def]
    session,
) -> None:
    """Canonical Issue 7 values are unaffected by the legacy coercion."""
    chapter = _setup_chapter(session)
    node = Node(
        chapter_id=chapter.chapter_id,
        content="Canonical node",
        intent_type=IntentType.BEAT_MILESTONE,
    )
    create_node(session, node)
    session.commit()

    fetched = get_node(session, node.node_id)
    assert fetched is not None
    assert fetched.intent_type == IntentType.BEAT_MILESTONE


def test_chapter_node_ids_populated(session):  # type: ignore[no-untyped-def]
    """Chapter.node_ids is populated after adding nodes."""
    from afterworlds.persistence.crud.story import get_chapter

    chapter = _setup_chapter(session)
    node1 = _make_node(str(chapter.chapter_id))
    node2 = _make_node(str(chapter.chapter_id))
    create_node(session, node1)
    create_node(session, node2)
    session.commit()

    fetched = get_chapter(session, chapter.chapter_id)
    assert fetched is not None
    assert len(fetched.node_ids) == 2
    assert node1.node_id in fetched.node_ids
    assert node2.node_id in fetched.node_ids
