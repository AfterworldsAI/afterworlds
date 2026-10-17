"""POST /api/stories/{story_id}/setup -- mode-discriminated structured setup.

Structured fields only. RPG conversational setup (world-building, character
creation) and Branching's confirmation pass are ordinary turns through
POST .../turns, not this route (ADR-016 Decision 3; Issue 15's own pipeline
owns setup_phase/play_status progression) -- this route never writes turns
or advances play_status/setup_phase itself. A Branching story starts only
through POST .../begin (ADR-016b).
"""

from __future__ import annotations

import asyncio
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session, sessionmaker

from afterworlds.api.deps import get_session, get_story_lock, run_under_story_lock
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
from afterworlds.api.story_bootstrap import (
    branching_configuration_problems,
    in_play_true_cyoa_problem,
    require_released_mode,
)
from afterworlds.api.visible_state import build_visible_state
from afterworlds.models.enums import (
    BranchingPlayStatus,
    InteractionStyle,
    RpgPlayStatus,
    StoryMode,
)
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
from afterworlds.services import rpg_setup

router = APIRouter(prefix="/api/stories", tags=["setup"])

_MODE_BY_REQUEST_TYPE = {
    RpgSetupRequest: StoryMode.RPG,
    BranchingSetupRequest: StoryMode.BRANCHING,
    WritingSetupRequest: StoryMode.WRITING,
}


_RPG_CONFIG_FIELDS = (
    "dice_handling",
    "gm_cheating",
    "tone",
    "session_type",
    "genre_flavor",
    "house_rules",
    "acceptable_content",
)
#: Optional settings an explicit ``null`` clears; omission leaves them as is.
_RPG_CLEARABLE_FIELDS = frozenset({"genre_flavor", "house_rules", "acceptable_content"})


def _apply_rpg_setup(session: Session, story_id: UUID, body: RpgSetupRequest) -> None:
    state = get_rpg_session_state_by_story(session, story_id)
    if state is None:
        raise ApiErrorResponse(
            404, ApiErrorCode.NOT_FOUND, f"No RPG session state for story {story_id}"
        )
    in_setup = state.play_status is RpgPlayStatus.SETUP
    if in_setup:
        # ADR-015c: a form edited from an older configuration must not
        # silently overwrite a newer save.
        expected = body.expected_configuration_revision
        if expected is None:
            raise ApiErrorResponse(
                422,
                ApiErrorCode.VALIDATION_FAILED,
                "expected_configuration_revision is required during RPG setup",
            )
        current = rpg_setup.configuration_revision(session, story_id)
        if expected != current:
            raise ApiErrorResponse(
                409,
                ApiErrorCode.SETUP_STATE_CONFLICT,
                f"the configuration changed (revision {current}, form based on "
                f"{expected}); reload it before saving",
            )
    updated = state.model_copy(
        update={
            k: getattr(body, k)
            for k in _RPG_CONFIG_FIELDS
            if getattr(body, k) is not None
            or (k in _RPG_CLEARABLE_FIELDS and k in body.model_fields_set)
        }
    )
    update_rpg_session_state(session, updated)
    if updated != state and in_setup:
        # ADR-015c: an edit invalidates any GM summary awaiting confirmation.
        rpg_setup.configuration_changed(session, story_id)


def _apply_branching_setup(
    session: Session, story_id: UUID, body: BranchingSetupRequest
) -> None:
    """Saves configuration only (ADR-016b Decision 1): never starts play --
    the separate Begin story operation does -- and never demotes a started
    story. Supersedes the PR #126 round 7 promotion on setup."""
    state = get_branching_session_state_by_story(session, story_id)
    if state is None:
        raise ApiErrorResponse(
            404,
            ApiErrorCode.NOT_FOUND,
            f"No Branching session state for story {story_id}",
        )
    style = body.interaction_style or state.interaction_style
    # Freeform-only carries no branch-count range.
    clear_range = body.clear_branch_count_range or (
        style is InteractionStyle.FREEFORM_ONLY
    )
    effective = state.model_copy(
        update={
            "interaction_style": style,
            "branching_cadence": body.branching_cadence or state.branching_cadence,
            "branch_count_range": (
                None
                if clear_range
                else body.branch_count_range or state.branch_count_range
            ),
        }
    )
    missing, invalid = branching_configuration_problems(effective)
    if state.play_status is BranchingPlayStatus.IN_PLAY:
        invalid += [f"an in-play story requires {field}" for field in missing]
        # ADR-016b: configuration cannot create cards, so an in-play story
        # may not become True CYOA without a committed card set that fits.
        unplayable = in_play_true_cyoa_problem(session, story_id, effective)
        if unplayable is not None:
            invalid.append(unplayable)
    if invalid:
        raise ApiErrorResponse(422, ApiErrorCode.VALIDATION_FAILED, "; ".join(invalid))
    apply_branching_config_update(
        session,
        story_id,
        interaction_style=body.interaction_style,
        branching_cadence=body.branching_cadence,
        branch_count_range=body.branch_count_range,
        length_preference=body.length_preference,
        clear_branch_count_range=clear_range,
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
async def submit_setup(
    story_id: UUID,
    body: SetupRequest,
    request: Request,
    lock: asyncio.Lock = Depends(get_story_lock),
) -> SetupResponse:
    """Setup shares the story's turn lock (CRD Issue 21 round 1, F3), so a
    configuration write cannot interleave with a Begin story opening or any
    other turn of the same story; a held lock is ``409 turn_in_flight``."""
    return await run_under_story_lock(
        lock, _submit_setup_sync, request.app.state.session_factory, story_id, body
    )


def _submit_setup_sync(
    session_factory: sessionmaker[Session], story_id: UUID, body: SetupRequest
) -> SetupResponse:
    with session_factory() as session:
        return _submit_setup(session, story_id, body)


def _submit_setup(
    session: Session, story_id: UUID, body: SetupRequest
) -> SetupResponse:
    # A story only accepts its own mode's request, so this also refuses
    # setup for any story of an unreleased mode (ADR-017b).
    expected_mode = _MODE_BY_REQUEST_TYPE[type(body)]
    require_released_mode(expected_mode)
    story = get_story(session, story_id)
    if story is None:
        raise ApiErrorResponse(
            404, ApiErrorCode.NOT_FOUND, f"Story {story_id} not found"
        )

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
