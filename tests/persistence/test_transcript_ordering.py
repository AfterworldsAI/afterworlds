"""Round 17 remediation (PR #126 P2): list_turns_by_story() must order
deterministically even when multiple Turns share the same stored
``timestamp`` -- ``timestamp`` alone is not a unique key, so SQLite's tie
order is otherwise unspecified and a repeated read could shuffle or drop a
turn at a page boundary.
"""

from __future__ import annotations

from datetime import UTC, datetime

from afterworlds.models.enums import IntentType
from afterworlds.models.node import Node
from afterworlds.models.turn import Turn
from afterworlds.persistence.crud.node import (
    create_node,
    create_turn,
    list_turns_by_story,
)
from afterworlds.persistence.crud.story import create_arc, create_chapter, create_story
from tests.persistence.conftest import make_arc, make_chapter, make_story


def _setup_story_and_node(session):  # type: ignore[no-untyped-def]
    """Create Story -> Arc -> Chapter -> Node and return (story_id, node_id)."""
    story = make_story()
    create_story(session, story)
    arc = make_arc(str(story.story_id))
    create_arc(session, arc)
    chapter = make_chapter(str(arc.arc_id))
    create_chapter(session, chapter)
    node = Node(
        chapter_id=chapter.chapter_id,
        content="A dark forest path diverges before you.",
        intent_type=IntentType.IN_CHARACTER_ACTION,
    )
    create_node(session, node)
    session.commit()
    return story.story_id, node.node_id


def _seed_turns_same_timestamp(session, node_id, count: int):  # type: ignore[no-untyped-def]
    """Create *count* Turns sharing one identical timestamp; return their
    turn_ids in creation order (not necessarily the persisted read order)."""
    when = datetime(2026, 1, 1, tzinfo=UTC)
    turn_ids = []
    for i in range(count):
        turn = Turn(
            user_input=f"input {i}",
            assistant_output=f"output {i}",
            timestamp=when,
            intent_classification=IntentType.IN_CHARACTER_ACTION,
            node_id=node_id,
        )
        create_turn(session, turn)
        turn_ids.append(turn.turn_id)
    session.commit()
    return turn_ids


def test_list_turns_by_story_orders_by_timestamp_then_turn_id_ascending(
    session,  # type: ignore[no-untyped-def]
) -> None:
    story_id, node_id = _setup_story_and_node(session)
    turn_ids = _seed_turns_same_timestamp(session, node_id, 4)

    turns = list_turns_by_story(session, story_id, limit=50)

    expected_order = sorted(turn_ids, key=str)
    assert [t.turn_id for t in turns] == expected_order

    # Repeated read is stable -- not just "some" order, the same order.
    turns_again = list_turns_by_story(session, story_id, limit=50)
    assert [t.turn_id for t in turns_again] == expected_order


def test_list_turns_by_story_newest_first_returns_deterministic_subset_oldest_first(
    session,  # type: ignore[no-untyped-def]
) -> None:
    story_id, node_id = _setup_story_and_node(session)
    turn_ids = _seed_turns_same_timestamp(session, node_id, 5)

    turns = list_turns_by_story(session, story_id, limit=3, newest_first=True)

    # ORDER BY timestamp DESC, turn_id DESC selects the 3 largest turn_ids
    # (ties broken descending), then the page is reversed back to
    # chronological order -- for identical timestamps that means ascending
    # turn_id order among just that top-3 subset.
    top_three_desc = sorted(turn_ids, key=str, reverse=True)[:3]
    expected_page = list(reversed(top_three_desc))
    assert [t.turn_id for t in turns] == expected_page


def test_list_turns_by_story_page_boundary_stable_across_repeated_calls(
    session,  # type: ignore[no-untyped-def]
) -> None:
    """Same timestamp, a limit/offset page boundary must not drop or
    shuffle rows between repeated calls."""
    story_id, node_id = _setup_story_and_node(session)
    turn_ids = _seed_turns_same_timestamp(session, node_id, 6)
    expected_order = sorted(turn_ids, key=str)

    page_1 = list_turns_by_story(session, story_id, limit=2, offset=1)
    page_2 = list_turns_by_story(session, story_id, limit=2, offset=1)
    assert [t.turn_id for t in page_1] == expected_order[1:3]
    assert [t.turn_id for t in page_2] == expected_order[1:3]

    latest_1 = list_turns_by_story(session, story_id, limit=2, newest_first=True)
    latest_2 = list_turns_by_story(session, story_id, limit=2, newest_first=True)
    assert [t.turn_id for t in latest_1] == [t.turn_id for t in latest_2]
