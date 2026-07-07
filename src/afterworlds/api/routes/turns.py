"""POST /api/stories/{story_id}/turns -- turn submission (Binding Decisions 3-8).

Thin handler: acquire the per-story lock (non-blocking) -> run the gate ->
access-path selection -> orchestrate -> settle sequence in a worker thread
(so a slow/blocking turn on one story never serializes requests for other
stories against the single asyncio event loop) -> release the lock in a
``finally`` on every path.
"""

from __future__ import annotations

import asyncio
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session, sessionmaker

from afterworlds.api.access_path import select_access_path
from afterworlds.api.deps import (
    get_byok_readiness_provider,
    get_orchestrator,
    get_session,
    get_sojourner_id,
    get_story_lock,
)
from afterworlds.api.dto import (
    ProviderRefusalSummaryDTO,
    TranscriptResponse,
    TranscriptTurnDTO,
    TurnSubmissionRequest,
    TurnSubmissionResponse,
)
from afterworlds.api.errors import ApiErrorCode, ApiErrorResponse
from afterworlds.api.story_bootstrap import ensure_story_turn_anchor_node
from afterworlds.api.visible_state import build_visible_state
from afterworlds.entitlement.errors import EntitlementSettlementError
from afterworlds.entitlement.policy import TurnCostPolicy
from afterworlds.entitlement.service import EntitlementService
from afterworlds.persistence.crud.node import list_turns_by_story
from afterworlds.persistence.crud.story import get_story
from afterworlds.pipeline.orchestrator.models import (
    OrchestrationResult,
    PipelineDisposition,
)
from afterworlds.pipeline.orchestrator.service import OrchestratorService
from afterworlds.pipeline.provider import ByokCredentialReadinessProvider

logger = logging.getLogger("afterworlds.api.turns")

router = APIRouter(prefix="/api/stories", tags=["turns"])

_BILLABLE_DISPOSITIONS = (
    PipelineDisposition.DELIVERED,
    PipelineDisposition.OOC_HANDLED,
)


def _submit_turn_sync(
    session_factory: sessionmaker[Session],
    orchestrator: OrchestratorService,
    byok_readiness_provider: ByokCredentialReadinessProvider,
    story_id: UUID,
    sojourner_id: UUID,
    user_input: str,
) -> TurnSubmissionResponse:
    """Runs entirely in one worker thread (Binding Decision 8): opens and
    closes its own session so a slow turn never pins the event loop or a
    session across threads.
    """
    session = session_factory()
    try:
        story = get_story(session, story_id)
        if story is None:
            raise ApiErrorResponse(
                404, ApiErrorCode.NOT_FOUND, f"Story {story_id} not found"
            )

        entitlement_service = EntitlementService(session)
        status = entitlement_service.get_access_path_status(sojourner_id)
        byok_ready = byok_readiness_provider.is_byok_runnable(sojourner_id)
        selection = select_access_path(status, byok_ready)

        if selection.access_path is None:
            assert selection.blocked_error_code is not None
            raise ApiErrorResponse(
                403,
                selection.blocked_error_code,
                "No runnable access path for this Sojourner.",
                detail=(
                    {
                        "hosted_unavailable_reason": (
                            selection.hosted_unavailable_reason.value
                        )
                    }
                    if selection.hosted_unavailable_reason is not None
                    else None
                ),
            )

        node_id = ensure_story_turn_anchor_node(session, story.story_id, story.mode)

        result: OrchestrationResult = orchestrator.orchestrate_turn(
            story.story_id,
            node_id,
            user_input,
            sojourner_id,
            selection.access_path,
        )

        settlement_warning: str | None = None
        if (
            result.disposition in _BILLABLE_DISPOSITIONS
            and selection.access_path.value == "hosted"
        ):
            try:
                entitlement_service.settle_hosted_turn_cost(
                    sojourner_id,
                    result,
                    policy=TurnCostPolicy(),
                    access_path=selection.access_path,
                )
            except EntitlementSettlementError as exc:
                # Never rolls back or hides the delivered turn (Binding
                # Decision 5 / DoR-D) -- surfaced as a structured log entry
                # + non-blocking warning field, never silently swallowed.
                logger.error(
                    "entitlement settlement failed",
                    extra={
                        "sojourner_id": str(sojourner_id),
                        "story_id": str(story_id),
                        "turn_id": str(result.turn_id) if result.turn_id else None,
                        "error_class": type(exc).__name__,
                    },
                )
                settlement_warning = str(exc)

        provider_refusal_dto = (
            ProviderRefusalSummaryDTO(
                provider=result.provider_refusal.provider,
                coarse_reason=result.provider_refusal.coarse_reason,
            )
            if result.provider_refusal is not None
            else None
        )

        # Single fetch, same session, before commit -- avoids a client-side
        # read race after this turn's writes land (spec: "refreshed
        # visible-state payload ... single fetch, avoids a read race after
        # commit"). Not reused from OrchestrationResult's own visible-state
        # fields: those are forbidden on every non-DELIVERED disposition,
        # including OOC_HANDLED, which is exactly where config most often
        # changes.
        visible_state = build_visible_state(session, story.story_id, story.mode)

        session.commit()
        return TurnSubmissionResponse(
            disposition=result.disposition,
            turn_id=result.turn_id,
            delivered_output=result.delivered_output,
            stable_prefix_cache_warmed=result.stable_prefix_cache_warmed,
            interaction_rejection_reason=result.interaction_rejection_reason,
            interaction_rejection_message=result.interaction_rejection_message,
            pipeline_error_summary=result.pipeline_error_summary,
            provider_refusal=provider_refusal_dto,
            pending_roll_redirect_message=result.pending_roll_redirect_message,
            settlement_warning=settlement_warning,
            visible_state=visible_state,
        )
    finally:
        session.close()


@router.post("/{story_id}/turns", response_model=TurnSubmissionResponse)
async def submit_turn(
    story_id: UUID,
    body: TurnSubmissionRequest,
    request: Request,
    orchestrator: OrchestratorService = Depends(get_orchestrator),
    byok_readiness_provider: ByokCredentialReadinessProvider = Depends(
        get_byok_readiness_provider
    ),
    sojourner_id: UUID = Depends(get_sojourner_id),
    lock: asyncio.Lock = Depends(get_story_lock),
) -> TurnSubmissionResponse:
    if lock.locked():
        raise ApiErrorResponse(
            409,
            ApiErrorCode.TURN_IN_FLIGHT,
            "A turn is already in flight for this story.",
        )
    await lock.acquire()
    try:
        return await asyncio.to_thread(
            _submit_turn_sync,
            request.app.state.session_factory,
            orchestrator,
            byok_readiness_provider,
            story_id,
            sojourner_id,
            body.user_input,
        )
    finally:
        lock.release()


_MAX_PAGE_SIZE = 200


@router.get("/{story_id}/turns", response_model=TranscriptResponse)
def get_transcript(
    story_id: UUID,
    session: Session = Depends(get_session),
    limit: int = 50,
    offset: int = 0,
) -> TranscriptResponse:
    story = get_story(session, story_id)
    if story is None:
        raise ApiErrorResponse(
            404, ApiErrorCode.NOT_FOUND, f"Story {story_id} not found"
        )
    if not 1 <= limit <= _MAX_PAGE_SIZE:
        raise ApiErrorResponse(
            422,
            ApiErrorCode.VALIDATION_FAILED,
            f"limit must be between 1 and {_MAX_PAGE_SIZE}",
        )
    if offset < 0:
        raise ApiErrorResponse(
            422, ApiErrorCode.VALIDATION_FAILED, "offset must be >= 0"
        )

    turns = list_turns_by_story(session, story_id, limit=limit, offset=offset)
    return TranscriptResponse(
        turns=[
            TranscriptTurnDTO(
                turn_id=t.turn_id,
                user_input=t.user_input,
                assistant_output=t.assistant_output,
                timestamp=t.timestamp,
                intent_classification=t.intent_classification,
            )
            for t in turns
        ]
    )
