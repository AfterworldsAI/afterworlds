"""Seam between the RPG setup routes and the setup owner (ADR-015c).

Builds the authoritative setup view and translates the owner's typed refusals
into the single API error envelope. Routes stay thin (Binding Decision 2).
"""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session, sessionmaker

from afterworlds.api.dto import (
    RpgCharacterCandidateDTO,
    RpgConfigurationTargetDTO,
    RpgRulesPackageOptionDTO,
    RpgSetupConfigurationDTO,
    RpgSetupViewDTO,
    RpgSheetRowDTO,
    RpgWorldTargetDTO,
)
from afterworlds.api.errors import ApiErrorCode, ApiErrorResponse
from afterworlds.api.story_bootstrap import require_released_mode
from afterworlds.models.enums import RpgSetupPhase, StoryMode
from afterworlds.persistence.crud.session_state import get_rpg_session_state_by_story
from afterworlds.persistence.crud.story import get_story
from afterworlds.services import rpg_setup
from afterworlds.services.dnd5e_state import store as character_store

_SHEET_LABELS = (
    ("species", "Species"),
    ("background", "Background"),
    ("classes", "Classes"),
    ("ability_scores", "Ability scores"),
    ("hit_points", "Hit points"),
    ("alignment", "Alignment"),
    ("skill_proficiencies", "Skills"),
    ("languages", "Languages"),
    ("feats", "Feats"),
    ("currency", "Currency"),
)


def now() -> str:
    return datetime.now(UTC).isoformat()


def _sheet_rows(proposal: dict[str, Any]) -> list[RpgSheetRowDTO]:
    """Every populated field of the candidate, in full, before acceptance.

    The candidate is the Sojourner's own proposed character -- it carries no
    hidden adjudication state -- so nothing that acceptance would make
    authoritative is withheld or truncated. Common fields come first; nested
    values are shown as complete JSON.
    """
    order = [key for key, _ in _SHEET_LABELS]
    labels = dict(_SHEET_LABELS)
    keys = [k for k in order if proposal.get(k) is not None] + sorted(
        k for k, v in proposal.items() if v is not None and k not in labels
    )
    return [
        RpgSheetRowDTO(
            label=labels.get(key, key.replace("_", " ").capitalize()),
            value=json.dumps(proposal[key], sort_keys=True, ensure_ascii=False),
        )
        for key in keys
    ]


def build_setup_view(session: Session, story_id: UUID) -> RpgSetupViewDTO:
    state = get_rpg_session_state_by_story(session, story_id)
    if state is None:
        raise ApiErrorResponse(
            404, ApiErrorCode.NOT_FOUND, f"No RPG session state for story {story_id}"
        )
    setup = rpg_setup.load_setup(session, rpg_setup.anchor_node_id(session, story_id))
    packages = (
        rpg_setup.available_packages(session, now=now())
        if state.setup_phase is RpgSetupPhase.CHARACTER_CREATION
        else []
    )
    candidate = setup.candidate
    return RpgSetupViewDTO(
        phase=state.setup_phase.value,
        play_status=state.play_status.value,
        world_revision=setup.world_revision,
        world_target=(
            RpgWorldTargetDTO(**setup.world_target.model_dump())
            if setup.world_target is not None
            and state.setup_phase is RpgSetupPhase.WORLD_SETUP
            else None
        ),
        packages=[RpgRulesPackageOptionDTO(**vars(p)) for p in packages],
        selected_package_uuid=setup.selected_package_uuid,
        candidate=(
            RpgCharacterCandidateDTO(
                revision=candidate.revision,
                path=candidate.path,
                sheet=_sheet_rows(candidate.proposal),
                unresolved=candidate.unresolved,
                problems=candidate.problems,
            )
            if candidate is not None
            else None
        ),
        character_accepted=(
            character_store.get_character(session, state.character_sheet_id) is not None
        ),
        configuration=RpgSetupConfigurationDTO(
            dice_handling=state.dice_handling,
            gm_cheating=state.gm_cheating,
            tone=state.tone,
            session_type=state.session_type,
            genre_flavor=state.genre_flavor,
            house_rules=state.house_rules,
            acceptable_content=state.acceptable_content,
        ),
        configuration_revision=setup.configuration_revision,
        configuration_target=(
            RpgConfigurationTargetDTO(
                turn_id=setup.configuration_target.turn_id,
                configuration_revision=setup.configuration_target.configuration_revision,
                configuration=RpgSetupConfigurationDTO(
                    **setup.configuration_target.configuration
                ),
                summary=setup.configuration_target.summary,
            )
            if setup.configuration_target is not None
            and state.setup_phase is RpgSetupPhase.PLAY_CONFIGURATION
            else None
        ),
    )


def require_rpg_story(session: Session, story_id: UUID) -> None:
    story = get_story(session, story_id)
    if story is None:
        raise ApiErrorResponse(
            404, ApiErrorCode.NOT_FOUND, f"Story {story_id} not found"
        )
    require_released_mode(story.mode)
    if story.mode is not StoryMode.RPG:
        raise ApiErrorResponse(
            409,
            ApiErrorCode.SETUP_STATE_CONFLICT,
            f"Story {story_id} is mode {story.mode.value}, not rpg",
        )


def run_setup_operation(
    session_factory: sessionmaker[Session],
    story_id: UUID,
    operation: Callable[[Session], None],
) -> RpgSetupViewDTO:
    """Apply one typed setup operation in its own transaction: commit with
    the advancement, or roll back and translate the typed refusal."""
    with session_factory() as session:
        require_rpg_story(session, story_id)
        try:
            operation(session)
        except rpg_setup.SetupConflictError as exc:
            session.rollback()
            raise ApiErrorResponse(
                409, ApiErrorCode.SETUP_STATE_CONFLICT, str(exc)
            ) from exc
        except rpg_setup.SetupInvalidError as exc:
            session.rollback()
            raise ApiErrorResponse(
                422,
                ApiErrorCode.VALIDATION_FAILED,
                str(exc),
                detail={"problems": "; ".join(exc.problems)} if exc.problems else None,
            ) from exc
        except Exception:
            session.rollback()
            raise
        session.commit()
        return build_setup_view(session, story_id)


def read_setup_view(
    session_factory: sessionmaker[Session], story_id: UUID
) -> RpgSetupViewDTO:
    with session_factory() as session:
        require_rpg_story(session, story_id)
        view = build_setup_view(session, story_id)
        # Resolving a binding may retain its override-set version (ADR-005d
        # Decision 9: the caller owns that commit).
        session.commit()
        return view
