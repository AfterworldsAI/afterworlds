"""Mode-discriminated visible-state dispatch (Issues 15/16/17).

Single shared function backing both `GET .../visible-state` and the
turn-submission envelope's `visible_state` field -- "single fetch" per the
spec means one shared call site within the same session/transaction, not
literally reusing OrchestrationResult's embedded visible-state fields (which
the disposition-invariant validator forbids on every non-DELIVERED
disposition, including OOC_HANDLED -- exactly the case where Branching/
Writing config most often changes).

Returns None when the owning mode's setup hasn't produced enough state yet
(no session state row, no persona selected, no full RPG character sheet) --
never raises, never invents partial/placeholder visible state.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from afterworlds.models.enums import StoryMode
from afterworlds.models.rpg import RpgVisibleState
from afterworlds.modes.personas.registry import get_default_registry
from afterworlds.persistence.crud.character_sheet import get_dnd5e_sheet
from afterworlds.persistence.crud.session_state import (
    get_branching_session_state_by_story,
    get_rpg_session_state_by_story,
    get_writing_session_state_by_story,
)
from afterworlds.pipeline.branching.models import BranchingVisibleState
from afterworlds.pipeline.branching.visible_state import BranchingVisibleStateService
from afterworlds.pipeline.rpg.visible_state import RpgVisibleStateService
from afterworlds.pipeline.writing.models import WritingVisibleState
from afterworlds.pipeline.writing.visible_state import WritingVisibleStateService

VisibleStateUnion = RpgVisibleState | BranchingVisibleState | WritingVisibleState


def build_visible_state(
    session: Session, story_id: UUID, mode: StoryMode
) -> VisibleStateUnion | None:
    if mode is StoryMode.RPG:
        rpg_state = get_rpg_session_state_by_story(session, story_id)
        if rpg_state is None:
            return None
        sheet = get_dnd5e_sheet(session, rpg_state.character_sheet_id)
        if sheet is None:
            return None
        return RpgVisibleStateService().build(sheet)

    if mode is StoryMode.BRANCHING:
        branching_state = get_branching_session_state_by_story(session, story_id)
        if (
            branching_state is None
            or branching_state.interaction_style is None
            or branching_state.branching_cadence is None
        ):
            return None
        return BranchingVisibleStateService().build(branching_state)

    writing_state = get_writing_session_state_by_story(session, story_id)
    if writing_state is None or writing_state.persona_id is None:
        return None
    return WritingVisibleStateService(get_default_registry()).build(writing_state)
