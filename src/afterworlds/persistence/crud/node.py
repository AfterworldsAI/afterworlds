"""CRUD operations for Node and Turn."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from afterworlds.models.intent_classification import IntentClassificationResult
from afterworlds.models.node import (
    BranchingNodeMetadata,
    ModeMetadata,
    Node,
    NodeMetadata,
    RpgNodeMetadata,
    StateDelta,
    WritingNodeMetadata,
)
from afterworlds.models.turn import Turn
from afterworlds.persistence.orm.node import NodeORM, TurnORM

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mode_metadata_to_dict(mm: ModeMetadata) -> dict[str, Any]:
    return mm.model_dump(mode="json")


def _mode_metadata_from_dict(data: dict[str, Any]) -> ModeMetadata:
    mode = data.get("mode")
    if mode == "rpg":
        return RpgNodeMetadata.model_validate(data)
    if mode == "branching":
        return BranchingNodeMetadata.model_validate(data)
    if mode == "writing":
        return WritingNodeMetadata.model_validate(data)
    raise ValueError(f"Unknown mode_metadata mode: {mode!r}")


def _node_orm_to_model(row: NodeORM) -> Node:
    mm: ModeMetadata | None = None
    if row.mode_metadata is not None:
        mm = _mode_metadata_from_dict(row.mode_metadata)
    return Node(
        node_id=UUID(row.node_id),
        chapter_id=UUID(row.chapter_id),
        content=row.content,
        state_delta=StateDelta.model_validate(row.state_delta),
        branching_logic=[UUID(uid) for uid in row.branching_logic],
        intent_type=row.intent_type,  # type: ignore[arg-type]
        metadata=NodeMetadata.model_validate(row.metadata_),
        mode_metadata=mm,
    )


def _turn_orm_to_model(row: TurnORM) -> Turn:
    icr: IntentClassificationResult | None = None
    if row.intent_classification_result is not None:
        icr = IntentClassificationResult.model_validate(
            row.intent_classification_result
        )
    return Turn(
        turn_id=UUID(row.turn_id),
        node_id=UUID(row.node_id) if row.node_id is not None else None,
        user_input=row.user_input,
        assistant_output=row.assistant_output,
        timestamp=row.timestamp,  # type: ignore[arg-type]
        intent_classification=row.intent_classification,  # type: ignore[arg-type]
        intent_classification_result=icr,
    )


# ---------------------------------------------------------------------------
# Node CRUD
# ---------------------------------------------------------------------------


def create_node(session: Session, node: Node) -> Node:
    """Persist a new Node and return it."""
    mm_dict: dict[str, Any] | None = None
    if node.mode_metadata is not None:
        mm_dict = _mode_metadata_to_dict(node.mode_metadata)

    row = NodeORM(
        node_id=str(node.node_id),
        chapter_id=str(node.chapter_id),
        content=node.content,
        state_delta=node.state_delta.model_dump(),
        branching_logic=[str(uid) for uid in node.branching_logic],
        intent_type=node.intent_type.value,
        metadata_=node.metadata.model_dump(mode="json"),
        mode_metadata=mm_dict,
    )
    session.add(row)
    session.flush()
    return _node_orm_to_model(row)


def get_node(session: Session, node_id: UUID) -> Node | None:
    """Return a Node by primary key, or None if not found."""
    row = session.get(NodeORM, str(node_id))
    if row is None:
        return None
    return _node_orm_to_model(row)


def update_node(session: Session, node: Node) -> Node | None:
    """Update mutable fields on an existing Node."""
    row = session.get(NodeORM, str(node.node_id))
    if row is None:
        return None
    mm_dict: dict[str, Any] | None = None
    if node.mode_metadata is not None:
        mm_dict = _mode_metadata_to_dict(node.mode_metadata)
    row.content = node.content
    row.state_delta = node.state_delta.model_dump()
    row.branching_logic = [str(uid) for uid in node.branching_logic]
    row.intent_type = node.intent_type.value
    row.metadata_ = node.metadata.model_dump(mode="json")
    row.mode_metadata = mm_dict
    session.flush()
    return _node_orm_to_model(row)


def delete_node(session: Session, node_id: UUID) -> bool:
    """Delete a Node.  Returns True if deleted."""
    row = session.get(NodeORM, str(node_id))
    if row is None:
        return False
    session.delete(row)
    session.flush()
    return True


# ---------------------------------------------------------------------------
# Turn CRUD
# ---------------------------------------------------------------------------


def create_turn(session: Session, turn: Turn) -> Turn:
    """Persist a new Turn and return it."""
    icr_dict: dict[str, Any] | None = None
    if turn.intent_classification_result is not None:
        icr_dict = turn.intent_classification_result.model_dump(mode="json")
    row = TurnORM(
        turn_id=str(turn.turn_id),
        node_id=str(turn.node_id) if turn.node_id is not None else None,
        user_input=turn.user_input,
        assistant_output=turn.assistant_output,
        timestamp=turn.timestamp.isoformat(),
        intent_classification=turn.intent_classification.value,
        intent_classification_result=icr_dict,
    )
    session.add(row)
    session.flush()
    return _turn_orm_to_model(row)


def get_turn(session: Session, turn_id: UUID) -> Turn | None:
    """Return a Turn by primary key, or None if not found."""
    row = session.get(TurnORM, str(turn_id))
    if row is None:
        return None
    return _turn_orm_to_model(row)


def delete_turn(session: Session, turn_id: UUID) -> bool:
    """Delete a Turn.  Returns True if deleted."""
    row = session.get(TurnORM, str(turn_id))
    if row is None:
        return False
    session.delete(row)
    session.flush()
    return True


def node_belongs_to_story(session: Session, node_id: UUID, story_id: UUID) -> bool:
    """Return True if node_id exists and its lineage traces back to story_id.

    Walks Node → Chapter → Arc and checks Arc.story_id.  Returns False for a
    node that does not exist or belongs to a different story.
    """
    from afterworlds.persistence.orm.story import ArcORM, ChapterORM

    result = (
        session.query(NodeORM.node_id)
        .join(ChapterORM, NodeORM.chapter_id == ChapterORM.chapter_id)
        .join(ArcORM, ChapterORM.arc_id == ArcORM.arc_id)
        .filter(
            NodeORM.node_id == str(node_id),
            ArcORM.story_id == str(story_id),
        )
        .first()
    )
    return result is not None
