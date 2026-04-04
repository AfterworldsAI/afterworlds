"""Tests for mode-specific session state CRUD operations."""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from afterworlds.models.enums import DiceHandling, PacingStage, WritingPersona
from afterworlds.models.session import (
    BranchingSessionState,
    BranchNode,
    BranchTree,
    CombatContext,
    PlotThread,
    RpgSessionState,
    WritingSessionState,
)
from afterworlds.persistence.crud.character_sheet import create_rpg_base_sheet
from afterworlds.persistence.crud.session_state import (
    create_branching_session_state,
    create_rpg_session_state,
    create_writing_session_state,
    delete_branching_session_state,
    delete_rpg_session_state,
    delete_writing_session_state,
    get_branching_session_state,
    get_rpg_session_state,
    get_writing_session_state,
    update_rpg_session_state,
    update_writing_session_state,
)
from afterworlds.persistence.crud.story import create_story
from tests.persistence.conftest import make_base_sheet, make_story


def _make_rpg_state(story_id: str, sheet_id: UUID | None = None) -> RpgSessionState:
    return RpgSessionState(
        story_id=UUID(story_id),
        character_sheet_id=sheet_id if sheet_id is not None else uuid4(),
        dice_handling=DiceHandling.AI_ROLLS,
        active_quests=["Find the artifact"],
        combat_context=CombatContext(
            is_in_combat=True,
            initiative_order=["Aria", "goblin"],
            round_number=2,
        ),
    )


def _make_branching_state(
    story_id: str, current_node_id: UUID | None = None
) -> BranchingSessionState:
    node_id = uuid4()
    return BranchingSessionState(
        story_id=UUID(story_id),
        pacing_stage=PacingStage.ESCALATION,
        branch_tree=BranchTree(
            nodes={str(node_id): BranchNode(node_id=node_id)},
            root_node_id=node_id,
        ),
        plot_thread_tracker=[PlotThread(description="Mystery of the locked door")],
        current_node_id=current_node_id,
    )


def _make_writing_state(story_id: str) -> WritingSessionState:
    from uuid import UUID

    ptr = uuid4()
    return WritingSessionState(
        story_id=UUID(story_id),
        beat_constraints=["no exposition dumps"],
        version_history_pointers=[ptr],
        persona=WritingPersona.CHIRON,
    )


# ---------------------------------------------------------------------------
# RpgSessionState
# ---------------------------------------------------------------------------


def test_rpg_session_state_round_trip(session):  # type: ignore[no-untyped-def]
    """Round-trip RpgSessionState."""
    story = make_story()
    create_story(session, story)
    base_sheet = make_base_sheet(str(story.story_id))
    create_rpg_base_sheet(session, base_sheet)
    session.commit()

    state = _make_rpg_state(str(story.story_id), sheet_id=base_sheet.sheet_id)
    created = create_rpg_session_state(session, state)
    session.commit()

    fetched = get_rpg_session_state(session, created.session_id)
    assert fetched is not None
    assert fetched.session_id == state.session_id
    assert fetched.dice_handling == DiceHandling.AI_ROLLS
    assert fetched.active_quests == ["Find the artifact"]
    assert fetched.combat_context.is_in_combat is True
    assert fetched.combat_context.round_number == 2


def test_rpg_session_state_unique_story(session):  # type: ignore[no-untyped-def]
    """A second RpgSessionState for the same story_id raises IntegrityError."""
    story = make_story()
    create_story(session, story)
    base_sheet = make_base_sheet(str(story.story_id))
    create_rpg_base_sheet(session, base_sheet)
    session.commit()

    s1 = _make_rpg_state(str(story.story_id), sheet_id=base_sheet.sheet_id)
    create_rpg_session_state(session, s1)
    session.commit()

    s2 = _make_rpg_state(str(story.story_id), sheet_id=base_sheet.sheet_id)
    with pytest.raises(IntegrityError):
        create_rpg_session_state(session, s2)
        session.flush()


def test_rpg_session_state_fk_enforced(session):  # type: ignore[no-untyped-def]
    """RpgSessionState with non-existent story_id raises IntegrityError."""
    state = _make_rpg_state(str(uuid4()))
    with pytest.raises(IntegrityError):
        create_rpg_session_state(session, state)
        session.flush()


def test_update_rpg_session_state(session):  # type: ignore[no-untyped-def]
    """update_rpg_session_state changes dice_handling and combat_context."""
    story = make_story()
    create_story(session, story)
    base_sheet = make_base_sheet(str(story.story_id))
    create_rpg_base_sheet(session, base_sheet)
    session.commit()

    state = _make_rpg_state(str(story.story_id), sheet_id=base_sheet.sheet_id)
    create_rpg_session_state(session, state)
    session.commit()

    updated = state.model_copy(
        update={
            "dice_handling": DiceHandling.PLAYER_ROLLS,
            "combat_context": CombatContext(is_in_combat=False),
        }
    )
    update_rpg_session_state(session, updated)
    session.commit()

    fetched = get_rpg_session_state(session, state.session_id)
    assert fetched is not None
    assert fetched.dice_handling == DiceHandling.PLAYER_ROLLS
    assert fetched.combat_context.is_in_combat is False


def test_delete_rpg_session_state(session):  # type: ignore[no-untyped-def]
    """delete_rpg_session_state removes the row."""
    story = make_story()
    create_story(session, story)
    base_sheet = make_base_sheet(str(story.story_id))
    create_rpg_base_sheet(session, base_sheet)
    session.commit()

    state = _make_rpg_state(str(story.story_id), sheet_id=base_sheet.sheet_id)
    create_rpg_session_state(session, state)
    session.commit()

    assert delete_rpg_session_state(session, state.session_id) is True
    session.commit()
    assert get_rpg_session_state(session, state.session_id) is None


# ---------------------------------------------------------------------------
# BranchingSessionState
# ---------------------------------------------------------------------------


def test_branching_session_state_round_trip(session):  # type: ignore[no-untyped-def]
    """Round-trip BranchingSessionState including BranchTree and PlotThreads."""
    story = make_story()
    create_story(session, story)
    state = _make_branching_state(str(story.story_id))
    created = create_branching_session_state(session, state)
    session.commit()

    fetched = get_branching_session_state(session, created.session_id)
    assert fetched is not None
    assert fetched.pacing_stage == PacingStage.ESCALATION
    assert fetched.current_node_id is None
    assert len(fetched.branch_tree.nodes) == 1
    assert len(fetched.plot_thread_tracker) == 1
    assert fetched.plot_thread_tracker[0].description == "Mystery of the locked door"


def test_branching_session_state_unique_story(session):  # type: ignore[no-untyped-def]
    """A second BranchingSessionState for the same story_id raises IntegrityError."""
    story = make_story()
    create_story(session, story)
    s1 = _make_branching_state(str(story.story_id))
    create_branching_session_state(session, s1)
    session.commit()

    s2 = _make_branching_state(str(story.story_id))
    with pytest.raises(IntegrityError):
        create_branching_session_state(session, s2)
        session.flush()


def test_branching_current_node_id_nullable(session):  # type: ignore[no-untyped-def]
    """BranchingSessionState with current_node_id=None persists correctly."""

    story = make_story()
    create_story(session, story)
    state = BranchingSessionState(
        story_id=story.story_id,
        pacing_stage=PacingStage.SETUP,
        current_node_id=None,
    )
    create_branching_session_state(session, state)
    session.commit()

    fetched = get_branching_session_state(session, state.session_id)
    assert fetched is not None
    assert fetched.current_node_id is None


def test_delete_branching_session_state(session):  # type: ignore[no-untyped-def]
    """delete_branching_session_state removes the row."""
    story = make_story()
    create_story(session, story)
    state = _make_branching_state(str(story.story_id))
    create_branching_session_state(session, state)
    session.commit()

    assert delete_branching_session_state(session, state.session_id) is True
    session.commit()
    assert get_branching_session_state(session, state.session_id) is None


# ---------------------------------------------------------------------------
# WritingSessionState
# ---------------------------------------------------------------------------


def test_writing_session_state_round_trip(session):  # type: ignore[no-untyped-def]
    """Round-trip WritingSessionState including version_history_pointers."""
    story = make_story()
    create_story(session, story)
    state = _make_writing_state(str(story.story_id))
    created = create_writing_session_state(session, state)
    session.commit()

    fetched = get_writing_session_state(session, created.session_id)
    assert fetched is not None
    assert fetched.persona == WritingPersona.CHIRON
    assert len(fetched.version_history_pointers) == 1
    assert fetched.version_history_pointers[0] == state.version_history_pointers[0]
    assert fetched.beat_constraints == ["no exposition dumps"]


def test_writing_session_state_unique_story(session):  # type: ignore[no-untyped-def]
    """A second WritingSessionState for the same story_id raises IntegrityError."""
    story = make_story()
    create_story(session, story)
    s1 = _make_writing_state(str(story.story_id))
    create_writing_session_state(session, s1)
    session.commit()

    s2 = _make_writing_state(str(story.story_id))
    with pytest.raises(IntegrityError):
        create_writing_session_state(session, s2)
        session.flush()


def test_writing_persona_nullable(session):  # type: ignore[no-untyped-def]
    """WritingSessionState with persona=None persists correctly."""
    story = make_story()
    create_story(session, story)
    state = WritingSessionState(story_id=story.story_id, persona=None)
    create_writing_session_state(session, state)
    session.commit()

    fetched = get_writing_session_state(session, state.session_id)
    assert fetched is not None
    assert fetched.persona is None


def test_update_writing_session_state(session):  # type: ignore[no-untyped-def]
    """update_writing_session_state changes persona."""
    story = make_story()
    create_story(session, story)
    state = _make_writing_state(str(story.story_id))
    create_writing_session_state(session, state)
    session.commit()

    updated = state.model_copy(update={"persona": WritingPersona.ODIN})
    update_writing_session_state(session, updated)
    session.commit()

    fetched = get_writing_session_state(session, state.session_id)
    assert fetched is not None
    assert fetched.persona == WritingPersona.ODIN


def test_delete_writing_session_state(session):  # type: ignore[no-untyped-def]
    """delete_writing_session_state removes the row."""
    story = make_story()
    create_story(session, story)
    state = _make_writing_state(str(story.story_id))
    create_writing_session_state(session, state)
    session.commit()

    assert delete_writing_session_state(session, state.session_id) is True
    session.commit()
    assert get_writing_session_state(session, state.session_id) is None


# ---------------------------------------------------------------------------
# FK enforcement — new constraints added in review fixes
# ---------------------------------------------------------------------------


def test_rpg_session_character_sheet_fk_enforced(session):  # type: ignore[no-untyped-def]
    """RpgSessionState with non-existent character_sheet_id raises IntegrityError."""
    story = make_story()
    create_story(session, story)
    session.commit()

    # sheet_id not in rpg_character_sheet_bases → FK violation
    state = _make_rpg_state(str(story.story_id), sheet_id=None)
    with pytest.raises(IntegrityError):
        create_rpg_session_state(session, state)
        session.flush()


def test_branching_current_node_id_fk_enforced(session):  # type: ignore[no-untyped-def]
    """BranchingSessionState with non-existent current_node_id raises IntegrityError."""
    from afterworlds.persistence.orm.session_state import BranchingSessionStateORM

    story = make_story()
    create_story(session, story)
    session.commit()

    # Insert directly to bypass Pydantic UUID validation;
    # non-existent node_id → FK violation
    row = BranchingSessionStateORM(
        session_id=str(uuid4()),
        story_id=str(story.story_id),
        pacing_stage="setup",
        branch_tree={},
        plot_thread_tracker=[],
        current_node_id=str(uuid4()),
    )
    session.add(row)
    with pytest.raises(IntegrityError):
        session.flush()
