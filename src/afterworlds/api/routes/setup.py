"""POST /api/stories/{story_id}/setup -- mode-discriminated structured setup.

Structured fields only. RPG conversational setup (world-building, character
creation) and Branching's confirmation pass are ordinary turns through
POST .../turns, not this route (ADR-016 Decision 3; Issue 15's own pipeline
owns setup_phase/play_status progression) -- this route never writes turns
or advances play_status/setup_phase itself.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from afterworlds.api.deps import get_session
from afterworlds.api.dto import (
    BranchingSetupRequest,
    RpgSetupRequest,
    SetupRequest,
    SetupResponse,
    WritingSetupRequest,
)
from afterworlds.api.errors import ApiErrorCode, ApiErrorResponse
from afterworlds.api.visible_state import build_visible_state
from afterworlds.models.enums import StoryMode
from afterworlds.modes.personas.registry import SupportedMode, get_default_registry
from afterworlds.persistence.crud.session_state import (
    apply_branching_config_update,
    apply_writing_config_update,
    get_rpg_session_state_by_story,
    update_rpg_session_state,
)
from afterworlds.persistence.crud.story import get_story

router = APIRouter(prefix="/api/stories", tags=["setup"])

_MODE_BY_REQUEST_TYPE = {
    RpgSetupRequest: StoryMode.RPG,
    BranchingSetupRequest: StoryMode.BRANCHING,
    WritingSetupRequest: StoryMode.WRITING,
}


def _apply_rpg_setup(session: Session, story_id: UUID, body: RpgSetupRequest) -> None:
    state = get_rpg_session_state_by_story(session, story_id)
    if state is None:
        raise ApiErrorResponse(
            404, ApiErrorCode.NOT_FOUND, f"No RPG session state for story {story_id}"
        )
    updated = state.model_copy(
        update={
            k: v
            for k, v in {
                "dice_handling": body.dice_handling,
                "gm_cheating": body.gm_cheating,
                "tone": body.tone,
                "session_type": body.session_type,
                "genre_flavor": body.genre_flavor,
                "house_rules": body.house_rules,
                "acceptable_content": body.acceptable_content,
            }.items()
            if v is not None
        }
    )
    update_rpg_session_state(session, updated)


def _apply_branching_setup(
    session: Session, story_id: UUID, body: BranchingSetupRequest
) -> None:
    found = apply_branching_config_update(
        session,
        story_id,
        interaction_style=body.interaction_style,
        branching_cadence=body.branching_cadence,
        branch_count_range=body.branch_count_range,
        length_preference=body.length_preference,
        clear_branch_count_range=body.clear_branch_count_range,
    )
    if not found:
        raise ApiErrorResponse(
            404,
            ApiErrorCode.NOT_FOUND,
            f"No Branching session state for story {story_id}",
        )


def _apply_writing_setup(
    session: Session, story_id: UUID, body: WritingSetupRequest
) -> None:
    registry = get_default_registry()
    try:
        profile = registry.get_profile(body.persona_id, SupportedMode.WRITING)
    except KeyError as exc:
        raise ApiErrorResponse(422, ApiErrorCode.VALIDATION_FAILED, str(exc)) from exc

    found = apply_writing_config_update(
        session,
        story_id,
        persona_id=profile.persona_id,
        persona_registry_version=registry.registry_version,
        persona_profile_version=profile.profile_version,
        persona_prompt_fingerprint=profile.prompt_fingerprint,
        critique_intensity=body.critique_intensity,
        form=body.form,
        form_other=body.form_other,
        tense=body.tense,
        pov=body.pov,
        style_density=body.style_density,
        dialogue_narration_ratio=body.dialogue_narration_ratio,
        genre_conventions=body.genre_conventions,
        specific_goals=body.specific_goals,
        acceptable_content=body.acceptable_content,
        beat_constraints=body.beat_constraints,
        beat_constraints_mode="replace" if body.beat_constraints is not None else None,
    )
    if not found:
        raise ApiErrorResponse(
            404,
            ApiErrorCode.NOT_FOUND,
            f"No Writing session state for story {story_id}",
        )


@router.post("/{story_id}/setup", response_model=SetupResponse)
def submit_setup(
    story_id: UUID, body: SetupRequest, session: Session = Depends(get_session)
) -> SetupResponse:
    story = get_story(session, story_id)
    if story is None:
        raise ApiErrorResponse(
            404, ApiErrorCode.NOT_FOUND, f"Story {story_id} not found"
        )

    expected_mode = _MODE_BY_REQUEST_TYPE[type(body)]
    if story.mode is not expected_mode:
        raise ApiErrorResponse(
            409,
            ApiErrorCode.SETUP_STATE_CONFLICT,
            f"Story {story_id} is mode {story.mode.value}, not {expected_mode.value}",
        )

    if isinstance(body, RpgSetupRequest):
        _apply_rpg_setup(session, story_id, body)
    elif isinstance(body, BranchingSetupRequest):
        _apply_branching_setup(session, story_id, body)
    else:
        _apply_writing_setup(session, story_id, body)

    visible_state = build_visible_state(session, story_id, story.mode)
    session.commit()
    return SetupResponse(visible_state=visible_state)
