"""RPG pending interaction and its deterministic operations (CRD Issue 15b).

Thin handlers (15b-29): validate the HTTP shape, take the story's shared lock
for a mutation, delegate to the typed seam (``api/rpg_actions.py``) and
return its player view. None of these is a narrative Turn: no provider call,
access-path selection or settlement (15b-20, 15b-27, 15b-28). Narration of a
``ready_for_narration`` sequence is the resume route in ``turns.py``.
"""

from __future__ import annotations

import asyncio
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from afterworlds.api.deps import (
    get_rpg_actions,
    get_session,
    get_story_lock,
    run_under_story_lock,
)
from afterworlds.api.dto import PendingInteractionResponse, RollAdjustmentRequest
from afterworlds.api.errors import API_ERROR_RESPONSES, ApiErrorCode, ApiErrorResponse
from afterworlds.api.rpg_actions import RpgActions
from afterworlds.models.rpg import (
    ActionResolutionAdvanceResult,
    MechanicalDecisionSubmission,
    RollSubmission,
)
from afterworlds.persistence.crud.story import get_story

router = APIRouter(prefix="/api/stories", tags=["rpg"])


@router.get(
    "/{story_id}/rpg/pending-interaction",
    response_model=PendingInteractionResponse,
    responses=API_ERROR_RESPONSES,
)
def get_pending_interaction(
    story_id: UUID,
    session: Session = Depends(get_session),
    actions: RpgActions = Depends(get_rpg_actions),
) -> PendingInteractionResponse:
    """None, a pending roll, a pending decision, or ``ready_for_narration``.
    Reloading returns the same affordance (15b-31)."""
    if get_story(session, story_id) is None:
        raise ApiErrorResponse(
            404, ApiErrorCode.NOT_FOUND, f"Story {story_id} not found"
        )
    return PendingInteractionResponse(interaction=actions.current(story_id))


@router.post(
    "/{story_id}/rpg/rolls",
    response_model=ActionResolutionAdvanceResult,
    responses=API_ERROR_RESPONSES,
)
async def submit_roll(
    story_id: UUID,
    body: RollSubmission,
    actions: RpgActions = Depends(get_rpg_actions),
    lock: asyncio.Lock = Depends(get_story_lock),
) -> ActionResolutionAdvanceResult:
    """Raw values by ``term_id`` (inline or physical) or a physical
    aggregate for the pending roll (15b-14, 15b-15)."""
    return await run_under_story_lock(lock, actions.submit_roll, story_id, body)


@router.post(
    "/{story_id}/rpg/adjustments",
    response_model=ActionResolutionAdvanceResult,
    responses=API_ERROR_RESPONSES,
)
async def apply_adjustment(
    story_id: UUID,
    body: RollAdjustmentRequest,
    actions: RpgActions = Depends(get_rpg_actions),
    lock: asyncio.Lock = Depends(get_story_lock),
) -> ActionResolutionAdvanceResult:
    """One offered adjustment option of the pending roll; the revised roll
    is returned in the same pending-roll phase (15b-9, 15b-13)."""
    return await run_under_story_lock(
        lock,
        actions.adjust,
        story_id,
        body.pending_roll_request_id,
        body.expected_instruction_revision,
        body.option_id,
    )


@router.post(
    "/{story_id}/rpg/decisions",
    response_model=ActionResolutionAdvanceResult,
    responses=API_ERROR_RESPONSES,
)
async def submit_decision(
    story_id: UUID,
    body: MechanicalDecisionSubmission,
    actions: RpgActions = Depends(get_rpg_actions),
    lock: asyncio.Lock = Depends(get_story_lock),
) -> ActionResolutionAdvanceResult:
    """An option of the pending mechanical decision, judged against its
    stored snapshot (15b-35)."""
    return await run_under_story_lock(lock, actions.decide, story_id, body)
