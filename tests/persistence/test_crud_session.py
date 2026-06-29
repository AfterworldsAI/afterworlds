"""Tests for mode-specific session state CRUD operations."""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from afterworlds.models.enums import (
    BranchCountRange,
    DiceHandling,
    InteractionStyle,
    PacingStage,
    RpgPlayStatus,
    RpgSessionType,
    RpgSetupPhase,
    RpgTone,
    WritingPersona,
)
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
    apply_branching_config_update,
    create_branching_session_state,
    create_rpg_session_state,
    create_writing_session_state,
    delete_branching_session_state,
    delete_rpg_session_state,
    delete_writing_session_state,
    get_branching_session_state,
    get_branching_session_state_by_story,
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
# RpgSessionState — new field round-trips (Fix 2, CRD Issue 15 remediation)
# ---------------------------------------------------------------------------


def _make_full_rpg_state(story_id: str, sheet_id: UUID) -> RpgSessionState:
    return RpgSessionState(
        story_id=UUID(story_id),
        character_sheet_id=sheet_id,
        dice_handling=DiceHandling.AI_ROLLS,
        play_status=RpgPlayStatus.IN_PLAY,
        setup_phase=RpgSetupPhase.COMPLETE,
        gm_cheating=False,
        tone=RpgTone.GRITTY,
        session_type=RpgSessionType.CAMPAIGN,
        genre_flavor="dark fantasy",
        house_rules="no flanking bonus",
        acceptable_content="fade to black",
        active_quests=["Find the artifact"],
        combat_context=CombatContext(),
    )


def test_rpg_session_state_new_fields_create_round_trip(session):  # type: ignore[no-untyped-def]
    """New fields persist and reload via create_rpg_session_state."""
    story = make_story()
    create_story(session, story)
    base_sheet = make_base_sheet(str(story.story_id))
    create_rpg_base_sheet(session, base_sheet)
    session.commit()

    state = _make_full_rpg_state(str(story.story_id), base_sheet.sheet_id)
    create_rpg_session_state(session, state)
    session.commit()

    fetched = get_rpg_session_state(session, state.session_id)
    assert fetched is not None
    assert fetched.play_status == RpgPlayStatus.IN_PLAY
    assert fetched.setup_phase == RpgSetupPhase.COMPLETE
    assert fetched.gm_cheating is False
    assert fetched.tone == RpgTone.GRITTY
    assert fetched.session_type == RpgSessionType.CAMPAIGN
    assert fetched.genre_flavor == "dark fantasy"
    assert fetched.house_rules == "no flanking bonus"
    assert fetched.acceptable_content == "fade to black"


def test_rpg_session_state_new_fields_update_round_trip(session):  # type: ignore[no-untyped-def]
    """New fields persist and reload via update_rpg_session_state."""
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
            "play_status": RpgPlayStatus.IN_PLAY,
            "setup_phase": RpgSetupPhase.COMPLETE,
            "gm_cheating": False,
            "tone": RpgTone.FORGIVING,
            "session_type": RpgSessionType.SHORT_ADVENTURE,
            "genre_flavor": "high fantasy",
            "house_rules": "flanking gives advantage",
            "acceptable_content": "all content",
        }
    )
    update_rpg_session_state(session, updated)
    session.commit()

    fetched = get_rpg_session_state(session, state.session_id)
    assert fetched is not None
    assert fetched.play_status == RpgPlayStatus.IN_PLAY
    assert fetched.gm_cheating is False
    assert fetched.tone == RpgTone.FORGIVING
    assert fetched.session_type == RpgSessionType.SHORT_ADVENTURE
    assert fetched.genre_flavor == "high fantasy"
    assert fetched.house_rules == "flanking gives advantage"
    assert fetched.acceptable_content == "all content"


def test_rpg_session_state_defaults_persist(session):  # type: ignore[no-untyped-def]
    """Default values for new fields survive a create→reload round-trip."""
    story = make_story()
    create_story(session, story)
    base_sheet = make_base_sheet(str(story.story_id))
    create_rpg_base_sheet(session, base_sheet)
    session.commit()

    state = _make_rpg_state(str(story.story_id), sheet_id=base_sheet.sheet_id)
    create_rpg_session_state(session, state)
    session.commit()

    fetched = get_rpg_session_state(session, state.session_id)
    assert fetched is not None
    assert fetched.play_status == RpgPlayStatus.SETUP
    assert fetched.setup_phase == RpgSetupPhase.WORLD_SETUP
    assert fetched.gm_cheating is True
    assert fetched.tone == RpgTone.BALANCED
    assert fetched.session_type == RpgSessionType.OPEN_ENDED
    assert fetched.genre_flavor is None
    assert fetched.house_rules is None
    assert fetched.acceptable_content is None


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


# ---------------------------------------------------------------------------
# Fix 3: apply_branching_config_update — clear_branch_count_range semantics
# ---------------------------------------------------------------------------


def _make_branching_state_with_range(
    story_id: str,
    interaction_style: InteractionStyle = InteractionStyle.HYBRID,
    branch_count_range: BranchCountRange = BranchCountRange.TWO_TO_THREE,
) -> BranchingSessionState:
    return BranchingSessionState(
        story_id=UUID(story_id),
        pacing_stage=PacingStage.ESCALATION,
        interaction_style=interaction_style,
        branch_count_range=branch_count_range,
    )


def test_clear_branch_count_range_sets_null(session):  # type: ignore[no-untyped-def]
    """clear_branch_count_range=True sets branch_count_range to NULL."""
    from afterworlds.models.enums import StoryMode

    story = make_story(mode=StoryMode.BRANCHING)
    create_story(session, story)
    state = _make_branching_state_with_range(str(story.story_id))
    create_branching_session_state(session, state)
    session.commit()

    # Confirm it has a range before clearing.
    before = get_branching_session_state_by_story(session, story.story_id)
    assert before is not None
    assert before.branch_count_range is BranchCountRange.TWO_TO_THREE

    apply_branching_config_update(
        session,
        story.story_id,
        clear_branch_count_range=True,
    )
    session.commit()

    after = get_branching_session_state_by_story(session, story.story_id)
    assert after is not None
    assert after.branch_count_range is None


def test_clear_branch_count_range_overrides_value_arg(session):  # type: ignore[no-untyped-def]
    """clear_branch_count_range=True → NULL even when branch_count_range is also set."""
    from afterworlds.models.enums import StoryMode

    story = make_story(mode=StoryMode.BRANCHING)
    create_story(session, story)
    state = _make_branching_state_with_range(str(story.story_id))
    create_branching_session_state(session, state)
    session.commit()

    apply_branching_config_update(
        session,
        story.story_id,
        branch_count_range=BranchCountRange.THREE_TO_FOUR,
        clear_branch_count_range=True,
    )
    session.commit()

    after = get_branching_session_state_by_story(session, story.story_id)
    assert after is not None
    assert after.branch_count_range is None


def test_default_false_leaves_none_unchanged(session):  # type: ignore[no-untyped-def]
    """clear_branch_count_range=False (default): None branch_count_range → no change."""
    from afterworlds.models.enums import StoryMode

    story = make_story(mode=StoryMode.BRANCHING)
    create_story(session, story)
    state = _make_branching_state_with_range(str(story.story_id))
    create_branching_session_state(session, state)
    session.commit()

    apply_branching_config_update(
        session,
        story.story_id,
        # branch_count_range omitted → no change
    )
    session.commit()

    after = get_branching_session_state_by_story(session, story.story_id)
    assert after is not None
    assert after.branch_count_range is BranchCountRange.TWO_TO_THREE


def test_apply_style_with_range(session):  # type: ignore[no-untyped-def]
    """Setting style + range together works; row is not left in mismatched config."""
    from afterworlds.models.enums import StoryMode

    story = make_story(mode=StoryMode.BRANCHING)
    create_story(session, story)
    state = _make_branching_state_with_range(str(story.story_id))
    create_branching_session_state(session, state)
    session.commit()

    apply_branching_config_update(
        session,
        story.story_id,
        interaction_style=InteractionStyle.TRUE_CYOA,
        branch_count_range=BranchCountRange.THREE_TO_FOUR,
    )
    session.commit()

    after = get_branching_session_state_by_story(session, story.story_id)
    assert after is not None
    assert after.interaction_style is InteractionStyle.TRUE_CYOA
    assert after.branch_count_range is BranchCountRange.THREE_TO_FOUR
