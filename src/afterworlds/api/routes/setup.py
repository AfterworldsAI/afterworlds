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
    BranchingSetupStateDTO,
    RpgSetupRequest,
    RpgSetupStateDTO,
    SetupRequest,
    SetupResponse,
    SetupStateResponse,
    WritingSetupRequest,
    WritingSetupStateDTO,
)
from afterworlds.api.errors import ApiErrorCode, ApiErrorResponse
from afterworlds.api.visible_state import build_visible_state
from afterworlds.models.enums import BranchingPlayStatus, StoryMode
from afterworlds.modes.personas.registry import (
    PersonaAvailability,
    SupportedMode,
    get_default_registry,
)
from afterworlds.persistence.crud.session_state import (
    apply_branching_config_update,
    apply_writing_config_update,
    get_branching_session_state_by_story,
    get_rpg_session_state_by_story,
    get_writing_session_state_by_story,
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
        # Round 7 remediation (PR #126 P1): mirrors the Writing setup route
        # below -- requested on every call, but apply_branching_config_update
        # only actually promotes once the persisted (post-update) row has
        # both interaction_style and branching_cadence, whether supplied on
        # this call or an earlier partial one. Idempotent: an already
        # IN_PLAY story is simply reassigned the same status.
        play_status=BranchingPlayStatus.IN_PLAY,
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

    # Round 16 remediation (PR #126 P2): GET /api/personas only ever lists
    # ACTIVE profiles (list_active()), but get_profile() above resolves any
    # profile that supports the mode, regardless of availability -- by
    # design, so already-persisted stories can still resolve a HIDDEN/
    # DEPRECATED persona_id they were set up with. A *new* setup call must
    # not be allowed to pick one just because a direct API client can name
    # it by id; get_profile() itself stays unrestricted for that reason, so
    # this is enforced here instead, before any config write.
    if profile.availability is not PersonaAvailability.ACTIVE:
        raise ApiErrorResponse(
            422,
            ApiErrorCode.VALIDATION_FAILED,
            f"Persona {profile.persona_id!r} is not available for new setup.",
        )

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
        # PR #126 round 13 (owner-approved boundary decision, superseding
        # round 5): this route no longer promotes play_status to IN_PLAY.
        # Round 5's promotion-in-/setup made every turn after structured
        # setup classify as PROSE_CONTINUATION/EXTRACTOR_ELIGIBLE
        # (derive_writing_turn_request), but ADR-017 Decision 9 / ADR-018 D6
        # require the *next* turn after setup -- while play_status is still
        # SETUP -- to be a setup-confirmation turn
        # (SETUP_CONFIRMATION/NON_CANON_SUPPORT), not ordinary prose. The
        # story now stays in SETUP here; the orchestrator's own
        # `_narrative_persist` promotes to IN_PLAY once that
        # setup-confirmation turn genuinely lands (see the play_status ==
        # SETUP branch there), never in React and never speculatively.
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


def _build_setup_state(
    session: Session, story_id: UUID, mode: StoryMode
) -> RpgSetupStateDTO | BranchingSetupStateDTO | WritingSetupStateDTO | None:
    """Currently-persisted setup/config fields for a story (PR #126 review
    round 5, P2). Unlike ``build_visible_state``, this never depends on a
    concrete RPG character sheet -- RPG session state (dice_handling, tone,
    etc.) exists from story creation, independent of sheet completeness.
    """
    if mode is StoryMode.RPG:
        rpg_state = get_rpg_session_state_by_story(session, story_id)
        if rpg_state is None:
            return None
        return RpgSetupStateDTO(
            mode="rpg",
            dice_handling=rpg_state.dice_handling,
            gm_cheating=rpg_state.gm_cheating,
            tone=rpg_state.tone,
            session_type=rpg_state.session_type,
            genre_flavor=rpg_state.genre_flavor,
            house_rules=rpg_state.house_rules,
            acceptable_content=rpg_state.acceptable_content,
        )
    if mode is StoryMode.BRANCHING:
        branching_state = get_branching_session_state_by_story(session, story_id)
        if branching_state is None:
            return None
        return BranchingSetupStateDTO(
            mode="branching",
            interaction_style=branching_state.interaction_style,
            branching_cadence=branching_state.branching_cadence,
            branch_count_range=branching_state.branch_count_range,
            length_preference=branching_state.length_preference,
        )
    writing_state = get_writing_session_state_by_story(session, story_id)
    if writing_state is None:
        return None
    return WritingSetupStateDTO(
        mode="writing",
        persona_id=writing_state.persona_id,
        critique_intensity=writing_state.critique_intensity,
        form=writing_state.form,
        form_other=writing_state.form_other,
        tense=writing_state.tense,
        pov=writing_state.pov,
        style_density=writing_state.style_density,
        dialogue_narration_ratio=writing_state.dialogue_narration_ratio,
        genre_conventions=writing_state.genre_conventions,
        specific_goals=writing_state.specific_goals or None,
        acceptable_content=writing_state.acceptable_content,
        beat_constraints=writing_state.beat_constraints,
    )


@router.get("/{story_id}/setup", response_model=SetupStateResponse)
def get_setup_state(
    story_id: UUID, session: Session = Depends(get_session)
) -> SetupStateResponse:
    story = get_story(session, story_id)
    if story is None:
        raise ApiErrorResponse(
            404, ApiErrorCode.NOT_FOUND, f"Story {story_id} not found"
        )
    setup_state = _build_setup_state(session, story_id, story.mode)
    return SetupStateResponse(setup_state=setup_state)
