"""Story-creation-time bootstrap seams — CRD Issue 19.

Two owner-approved, stop-and-flag-resolved bootstrap concerns, both
implemented with existing Issue 3/15/16/17 typed CRUD only. Neither is a
node-advancement policy, a story-graph engine, or new mode behavior:

1. Turn-anchor node: ``orchestrate_turn`` requires a real ``node_id`` and
   ``WriterService.write`` requires that node to belong to the story. No
   seam anywhere creates or advances nodes, so Issue 19 creates exactly one
   Arc -> Chapter -> Node chain per story and reuses it as the turn-submission
   anchor for the story's whole v1 lifetime. Many Turns share this one Node
   (Turn.node_id is only a link). ``ensure_story_turn_anchor_node`` is
   idempotent: it reuses an existing anchor rather than creating a duplicate.

2. Per-mode session-state bootstrap: RPG session state has a required
   ``character_sheet_id`` FK, so a minimal ``RpgCharacterSheetBase`` row is
   created first (character_name/rules_package_id only -- no ability scores
   or adjudicable mechanics; the RPG conversational setup pipeline, already
   built in Issue 15, fills those in). Branching and Writing session state
   have no such precondition and are created with setup fields empty/None.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from afterworlds.models.character_sheet import RpgCharacterSheetBase
from afterworlds.models.enums import DiceHandling, IntentType, PacingStage, StoryMode
from afterworlds.models.node import (
    BranchingNodeMetadata,
    Node,
    NodeMetadata,
    RpgNodeMetadata,
    StateDelta,
    WritingNodeMetadata,
)
from afterworlds.models.session import (
    BranchingSessionState,
    RpgSessionState,
    WritingSessionState,
)
from afterworlds.models.story import Arc, Chapter
from afterworlds.persistence.crud.character_sheet import create_rpg_base_sheet
from afterworlds.persistence.crud.node import (
    create_node,
    node_belongs_to_story,
)
from afterworlds.persistence.crud.session_state import (
    create_branching_session_state,
    create_rpg_session_state,
    create_writing_session_state,
    get_branching_session_state_by_story,
    get_rpg_session_state_by_story,
    get_writing_session_state_by_story,
)
from afterworlds.persistence.crud.story import create_arc, create_chapter

_ANCHOR_ARC_TITLE = "Main"
_ANCHOR_CHAPTER_TITLE = "Turn Anchor"

_MODE_METADATA_FACTORY = {
    StoryMode.RPG: RpgNodeMetadata,
    StoryMode.BRANCHING: BranchingNodeMetadata,
    StoryMode.WRITING: WritingNodeMetadata,
}


def ensure_story_turn_anchor_node(
    session: Session, story_id: UUID, mode: StoryMode
) -> UUID:
    """Return the story's turn-anchor node id, creating it if absent.

    Idempotent: if the story already has an anchor (any node belonging to
    it), that node is reused rather than creating a duplicate.
    """
    from afterworlds.persistence.orm.node import NodeORM
    from afterworlds.persistence.orm.story import ArcORM, ChapterORM

    existing = (
        session.query(NodeORM.node_id)
        .join(ChapterORM, NodeORM.chapter_id == ChapterORM.chapter_id)
        .join(ArcORM, ChapterORM.arc_id == ArcORM.arc_id)
        .filter(ArcORM.story_id == str(story_id))
        .first()
    )
    if existing is not None:
        return UUID(existing[0])

    now = datetime.now(UTC)
    arc = create_arc(session, Arc(story_id=story_id, title=_ANCHOR_ARC_TITLE, order=0))
    chapter = create_chapter(
        session, Chapter(arc_id=arc.arc_id, title=_ANCHOR_CHAPTER_TITLE, order=0)
    )
    node = create_node(
        session,
        Node(
            chapter_id=chapter.chapter_id,
            content="",
            state_delta=StateDelta(),
            branching_logic=[],
            intent_type=IntentType.BEAT_MILESTONE,
            metadata=NodeMetadata(timestamp=now),
            mode_metadata=_MODE_METADATA_FACTORY[mode](),
        ),
    )
    assert node_belongs_to_story(session, node.node_id, story_id)
    return node.node_id


def ensure_mode_session_state(
    session: Session,
    story_id: UUID,
    mode: StoryMode,
    *,
    character_name: str | None = None,
) -> None:
    """Create the owning mode's session state for a new story, if absent."""
    now = datetime.now(UTC)
    if mode is StoryMode.RPG:
        if get_rpg_session_state_by_story(session, story_id) is not None:
            return
        sheet = create_rpg_base_sheet(
            session,
            RpgCharacterSheetBase(
                story_id=story_id,
                rules_package_id="dnd5e",
                character_name=character_name or "Unnamed",
                created_at=now,
                updated_at=now,
            ),
        )
        create_rpg_session_state(
            session,
            RpgSessionState(
                story_id=story_id,
                character_sheet_id=sheet.sheet_id,
                dice_handling=DiceHandling.AI_ROLLS,
            ),
        )
    elif mode is StoryMode.BRANCHING:
        if get_branching_session_state_by_story(session, story_id) is not None:
            return
        create_branching_session_state(
            session,
            BranchingSessionState(story_id=story_id, pacing_stage=PacingStage.SETUP),
        )
    elif mode is StoryMode.WRITING:
        if get_writing_session_state_by_story(session, story_id) is not None:
            return
        create_writing_session_state(session, WritingSessionState(story_id=story_id))


def resolve_play_status(session: Session, story_id: UUID, mode: StoryMode) -> str:
    """Return the owning mode's play_status value ("setup"/"in_play") for a story.

    Falls back to "setup" if session state has not been created yet (should
    not happen for stories created via this API, but read paths fail closed
    rather than raising on legacy/partial rows).
    """
    state: RpgSessionState | BranchingSessionState | WritingSessionState | None
    if mode is StoryMode.RPG:
        state = get_rpg_session_state_by_story(session, story_id)
    elif mode is StoryMode.BRANCHING:
        state = get_branching_session_state_by_story(session, story_id)
    else:
        state = get_writing_session_state_by_story(session, story_id)
    if state is None:
        return "setup"
    return state.play_status.value
