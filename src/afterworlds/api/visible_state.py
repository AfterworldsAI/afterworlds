"""Mode-discriminated visible-state dispatch (Issues 15/16/17).

Single shared function backing both `GET .../visible-state` and the
turn-submission envelope's `visible_state` field -- "single fetch" per the
spec means one shared call site within the same session/transaction, not
literally reusing OrchestrationResult's embedded visible-state fields (which
the disposition-invariant validator forbids on every non-DELIVERED
disposition, including OOC_HANDLED -- exactly the case where Branching/
Writing config most often changes).

Returns None when the owning mode's setup hasn't produced enough state yet
(no session state row, no persona selected, no recorded RPG character state) --
never raises, never invents partial/placeholder visible state.

The RPG snapshot is live display, so it reads through the character's exact
binding (CRD Issue 2b): a binding that is stale, unpublished, quarantined or
otherwise refused yields no snapshot (unavailable), never a display of state
as though its authority were current. Historical replay and recorded-binding
maintenance stay on their explicit paths in ``services.dnd5e_state.service``.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from afterworlds.api.story_bootstrap import find_story_turn_anchor_node
from afterworlds.models.enums import (
    BranchingPlayStatus,
    BranchPresentationState,
    InteractionStyle,
    StoryMode,
)
from afterworlds.models.node import BranchingNodeMetadata
from afterworlds.models.rpg import RpgVisibleState
from afterworlds.modes.personas.registry import get_default_registry
from afterworlds.persistence.crud.node import get_node
from afterworlds.persistence.crud.session_state import (
    get_branching_session_state_by_story,
    get_rpg_session_state_by_story,
    get_writing_session_state_by_story,
)
from afterworlds.pipeline.branching.models import BranchingVisibleState, BranchOption
from afterworlds.pipeline.branching.visible_state import BranchingVisibleStateService
from afterworlds.pipeline.rpg.visible_state import RpgVisibleStateService
from afterworlds.pipeline.writing.models import WritingVisibleState
from afterworlds.pipeline.writing.visible_state import WritingVisibleStateService
from afterworlds.services.dnd5e_state.authority import require_current
from afterworlds.services.dnd5e_state.errors import BindingRefusedError
from afterworlds.services.dnd5e_state.holdings import Holder, HolderKind, items_held_by
from afterworlds.services.dnd5e_state.store import get_character

VisibleStateUnion = RpgVisibleState | BranchingVisibleState | WritingVisibleState

logger = logging.getLogger(__name__)


def _with_committed_cards(
    session: Session, story_id: UUID, state: BranchingVisibleState
) -> BranchingVisibleState:
    """The current committed card set of an in-play card-style story
    (ADR-016b Decision 5), read from the anchor Node's
    ``BranchingNodeMetadata`` -- the surface the next selection is validated
    against. Read-only: never creates the anchor. Freeform-only and setup
    stories show no cards."""
    if (
        state.play_status is not BranchingPlayStatus.IN_PLAY
        or state.interaction_style
        not in (
            InteractionStyle.HYBRID,
            InteractionStyle.TRUE_CYOA,
        )
    ):
        return state
    anchor = find_story_turn_anchor_node(session, story_id)
    node = get_node(session, anchor) if anchor is not None else None
    metadata = node.mode_metadata if node is not None else None
    if not isinstance(metadata, BranchingNodeMetadata):
        return state
    try:
        presentation = (
            BranchPresentationState(metadata.branch_presentation_state)
            if metadata.branch_presentation_state
            else None
        )
    except ValueError:
        presentation = None
    return state.model_copy(
        update={
            "last_branch_options": [
                BranchOption(option_id=o.option_id, action_text=o.action_text)
                for o in metadata.branch_options
            ]
            or None,
            "last_presentation_state": presentation,
        }
    )


def build_visible_state(
    session: Session, story_id: UUID, mode: StoryMode
) -> VisibleStateUnion | None:
    if mode is StoryMode.RPG:
        rpg_state = get_rpg_session_state_by_story(session, story_id)
        if rpg_state is None:
            return None
        character = get_character(session, rpg_state.character_sheet_id)
        if character is None:
            return None
        try:
            require_current(
                session, character.binding, now=datetime.now(UTC).isoformat()
            )
        except BindingRefusedError as exc:
            logger.info("rpg visible state unavailable for story %s: %s", story_id, exc)
            return None
        items = items_held_by(session, Holder(HolderKind.CHARACTER, character.sheet_id))
        return RpgVisibleStateService().build(character, items)

    if mode is StoryMode.BRANCHING:
        branching_state = get_branching_session_state_by_story(session, story_id)
        if (
            branching_state is None
            or branching_state.interaction_style is None
            or branching_state.branching_cadence is None
        ):
            return None
        return _with_committed_cards(
            session, story_id, BranchingVisibleStateService().build(branching_state)
        )

    writing_state = get_writing_session_state_by_story(session, story_id)
    if writing_state is None or writing_state.persona_id is None:
        return None
    try:
        return WritingVisibleStateService(get_default_registry()).build(writing_state)
    except ValueError as exc:
        # persona_id is set but no longer resolves in the current registry
        # (e.g. the persona catalog changed after this story was set up).
        # This runs after orchestrate_turn() has already produced a
        # deliverable turn result, so a raise here would turn a valid
        # delivered turn into an unhandled 500 -- never expose visible-state
        # construction failures to the caller (module contract: "never
        # raises"). No sensitive content in the log -- ids and error class
        # only.
        logger.warning(
            "Writing visible-state build failed for story %s (mode=%s): %s",
            story_id,
            mode.value,
            type(exc).__name__,
        )
        return None
