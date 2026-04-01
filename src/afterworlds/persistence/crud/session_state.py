"""CRUD operations for mode-specific session states."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from afterworlds.models.session import (
    BranchingSessionState,
    BranchTree,
    CombatContext,
    PlotThread,
    RpgSessionState,
    WritingSessionState,
)
from afterworlds.persistence.orm.session_state import (
    BranchingSessionStateORM,
    RpgSessionStateORM,
    WritingSessionStateORM,
)

# ---------------------------------------------------------------------------
# RpgSessionState
# ---------------------------------------------------------------------------


def _rpg_orm_to_model(row: RpgSessionStateORM) -> RpgSessionState:
    return RpgSessionState(
        session_id=UUID(row.session_id),
        story_id=UUID(row.story_id),
        character_sheet_id=UUID(row.character_sheet_id),
        dice_handling=row.dice_handling,  # type: ignore[arg-type]
        active_quests=list(row.active_quests),
        combat_context=CombatContext.model_validate(row.combat_context),
    )


def create_rpg_session_state(
    session: Session, state: RpgSessionState
) -> RpgSessionState:
    """Persist a new RpgSessionState and return it."""
    row = RpgSessionStateORM(
        session_id=str(state.session_id),
        story_id=str(state.story_id),
        character_sheet_id=str(state.character_sheet_id),
        dice_handling=state.dice_handling.value,
        active_quests=list(state.active_quests),
        combat_context=state.combat_context.model_dump(),
    )
    session.add(row)
    session.flush()
    return _rpg_orm_to_model(row)


def get_rpg_session_state(session: Session, session_id: UUID) -> RpgSessionState | None:
    """Return an RpgSessionState by primary key, or None."""
    row = session.get(RpgSessionStateORM, str(session_id))
    if row is None:
        return None
    return _rpg_orm_to_model(row)


def get_rpg_session_state_by_story(
    session: Session, story_id: UUID
) -> RpgSessionState | None:
    """Return the RpgSessionState for a story, or None."""
    row = (
        session.query(RpgSessionStateORM)
        .filter(RpgSessionStateORM.story_id == str(story_id))
        .first()
    )
    if row is None:
        return None
    return _rpg_orm_to_model(row)


def update_rpg_session_state(
    session: Session, state: RpgSessionState
) -> RpgSessionState | None:
    """Update mutable fields on an existing RpgSessionState."""
    row = session.get(RpgSessionStateORM, str(state.session_id))
    if row is None:
        return None
    row.dice_handling = state.dice_handling.value
    row.active_quests = list(state.active_quests)
    row.combat_context = state.combat_context.model_dump()
    session.flush()
    return _rpg_orm_to_model(row)


def delete_rpg_session_state(session: Session, session_id: UUID) -> bool:
    """Delete an RpgSessionState.  Returns True if deleted."""
    row = session.get(RpgSessionStateORM, str(session_id))
    if row is None:
        return False
    session.delete(row)
    session.flush()
    return True


# ---------------------------------------------------------------------------
# BranchingSessionState
# ---------------------------------------------------------------------------


def _branching_orm_to_model(row: BranchingSessionStateORM) -> BranchingSessionState:
    plot_threads: list[PlotThread] = [
        PlotThread.model_validate(pt) for pt in row.plot_thread_tracker
    ]
    return BranchingSessionState(
        session_id=UUID(row.session_id),
        story_id=UUID(row.story_id),
        pacing_stage=row.pacing_stage,  # type: ignore[arg-type]
        branch_tree=BranchTree.model_validate(row.branch_tree),
        plot_thread_tracker=plot_threads,
        current_node_id=(
            UUID(row.current_node_id) if row.current_node_id is not None else None
        ),
    )


def _branching_tree_to_dict(bt: BranchTree) -> dict[str, Any]:
    return bt.model_dump(mode="json")


def create_branching_session_state(
    session: Session, state: BranchingSessionState
) -> BranchingSessionState:
    """Persist a new BranchingSessionState and return it."""
    row = BranchingSessionStateORM(
        session_id=str(state.session_id),
        story_id=str(state.story_id),
        pacing_stage=state.pacing_stage.value,
        branch_tree=_branching_tree_to_dict(state.branch_tree),
        plot_thread_tracker=[
            pt.model_dump(mode="json") for pt in state.plot_thread_tracker
        ],
        current_node_id=(
            str(state.current_node_id) if state.current_node_id is not None else None
        ),
    )
    session.add(row)
    session.flush()
    return _branching_orm_to_model(row)


def get_branching_session_state(
    session: Session, session_id: UUID
) -> BranchingSessionState | None:
    """Return a BranchingSessionState by primary key, or None."""
    row = session.get(BranchingSessionStateORM, str(session_id))
    if row is None:
        return None
    return _branching_orm_to_model(row)


def get_branching_session_state_by_story(
    session: Session, story_id: UUID
) -> BranchingSessionState | None:
    """Return the BranchingSessionState for a story, or None."""
    row = (
        session.query(BranchingSessionStateORM)
        .filter(BranchingSessionStateORM.story_id == str(story_id))
        .first()
    )
    if row is None:
        return None
    return _branching_orm_to_model(row)


def update_branching_session_state(
    session: Session, state: BranchingSessionState
) -> BranchingSessionState | None:
    """Update mutable fields on an existing BranchingSessionState."""
    row = session.get(BranchingSessionStateORM, str(state.session_id))
    if row is None:
        return None
    row.pacing_stage = state.pacing_stage.value
    row.branch_tree = _branching_tree_to_dict(state.branch_tree)
    row.plot_thread_tracker = [
        pt.model_dump(mode="json") for pt in state.plot_thread_tracker
    ]
    row.current_node_id = (
        str(state.current_node_id) if state.current_node_id is not None else None
    )
    session.flush()
    return _branching_orm_to_model(row)


def delete_branching_session_state(session: Session, session_id: UUID) -> bool:
    """Delete a BranchingSessionState.  Returns True if deleted."""
    row = session.get(BranchingSessionStateORM, str(session_id))
    if row is None:
        return False
    session.delete(row)
    session.flush()
    return True


# ---------------------------------------------------------------------------
# WritingSessionState
# ---------------------------------------------------------------------------


def _writing_orm_to_model(row: WritingSessionStateORM) -> WritingSessionState:
    return WritingSessionState(
        session_id=UUID(row.session_id),
        story_id=UUID(row.story_id),
        beat_constraints=list(row.beat_constraints),
        version_history_pointers=[UUID(p) for p in row.version_history_pointers],
        persona=row.persona,  # type: ignore[arg-type]
    )


def create_writing_session_state(
    session: Session, state: WritingSessionState
) -> WritingSessionState:
    """Persist a new WritingSessionState and return it."""
    row = WritingSessionStateORM(
        session_id=str(state.session_id),
        story_id=str(state.story_id),
        beat_constraints=list(state.beat_constraints),
        version_history_pointers=[str(p) for p in state.version_history_pointers],
        persona=state.persona.value if state.persona is not None else None,
    )
    session.add(row)
    session.flush()
    return _writing_orm_to_model(row)


def get_writing_session_state(
    session: Session, session_id: UUID
) -> WritingSessionState | None:
    """Return a WritingSessionState by primary key, or None."""
    row = session.get(WritingSessionStateORM, str(session_id))
    if row is None:
        return None
    return _writing_orm_to_model(row)


def get_writing_session_state_by_story(
    session: Session, story_id: UUID
) -> WritingSessionState | None:
    """Return the WritingSessionState for a story, or None."""
    row = (
        session.query(WritingSessionStateORM)
        .filter(WritingSessionStateORM.story_id == str(story_id))
        .first()
    )
    if row is None:
        return None
    return _writing_orm_to_model(row)


def update_writing_session_state(
    session: Session, state: WritingSessionState
) -> WritingSessionState | None:
    """Update mutable fields on an existing WritingSessionState."""
    row = session.get(WritingSessionStateORM, str(state.session_id))
    if row is None:
        return None
    row.beat_constraints = list(state.beat_constraints)
    row.version_history_pointers = [str(p) for p in state.version_history_pointers]
    row.persona = state.persona.value if state.persona is not None else None
    session.flush()
    return _writing_orm_to_model(row)


def delete_writing_session_state(session: Session, session_id: UUID) -> bool:
    """Delete a WritingSessionState.  Returns True if deleted."""
    row = session.get(WritingSessionStateORM, str(session_id))
    if row is None:
        return False
    session.delete(row)
    session.flush()
    return True
