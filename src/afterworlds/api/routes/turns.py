"""POST /api/stories/{story_id}/turns -- turn submission (Binding Decisions 3-8).

Thin handler: acquire the per-story lock (non-blocking) -> run the gate ->
access-path selection -> orchestrate -> settle sequence in a worker thread
(so a slow/blocking turn on one story never serializes requests for other
stories against the single asyncio event loop) -> release the lock in a
``finally`` on every path.

POST .../rpg/sequences/{sequence_id}/resume (CRD Issue 15b) is the same flow
with the orchestrator's RPG resume entry in place of ``orchestrate_turn``.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session, sessionmaker

from afterworlds.api.access_path import probe_byok_readiness, select_access_path
from afterworlds.api.deps import (
    get_byok_readiness_provider,
    get_orchestrator,
    get_rpg_actions,
    get_session,
    get_sojourner_id,
    get_story_lock,
    run_under_story_lock,
)
from afterworlds.api.dto import (
    ProviderRefusalSummaryDTO,
    TranscriptResponse,
    TranscriptTurnDTO,
    TurnSubmissionRequest,
    TurnSubmissionResponse,
)
from afterworlds.api.errors import API_ERROR_RESPONSES, ApiErrorCode, ApiErrorResponse
from afterworlds.api.rpg_actions import RpgActions, raise_for_action_sequence_error
from afterworlds.api.story_bootstrap import (
    derive_writing_turn_request,
    ensure_story_turn_anchor_node,
)
from afterworlds.api.visible_state import build_visible_state
from afterworlds.entitlement.enums import RuntimeAccessPath
from afterworlds.entitlement.errors import (
    EntitlementConcurrencyError,
    EntitlementIdempotencyConflictError,
    EntitlementSettlementConflictError,
    EntitlementSettlementError,
)
from afterworlds.entitlement.policy import TurnCostPolicy
from afterworlds.entitlement.service import EntitlementService
from afterworlds.models.story import Story
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

# All settlement write failures that must survive a delivered/OOC turn
# (Binding Decision 5 / DoR-D). Deliberately not the AfterworldsError base --
# that would also swallow replay/payload-version errors that
# settle_hosted_turn_cost() cannot actually raise.
SETTLEMENT_WARNING_ERRORS = (
    EntitlementSettlementError,
    EntitlementSettlementConflictError,
    EntitlementIdempotencyConflictError,
    EntitlementConcurrencyError,
)


#: Runs the orchestrator for one turn: (session, story, current canonical
#: node, selected access path) -> result.
_Orchestrate = Callable[[Session, Story, UUID, RuntimeAccessPath], OrchestrationResult]


def _submit_turn_sync(
    session_factory: sessionmaker[Session],
    orchestrator: OrchestratorService,
    byok_readiness_provider: ByokCredentialReadinessProvider,
    story_id: UUID,
    sojourner_id: UUID,
    user_input: str,
) -> TurnSubmissionResponse:
    def orchestrate(
        session: Session, story: Story, node_id: UUID, access_path: RuntimeAccessPath
    ) -> OrchestrationResult:
        # PR #126 review round 5 (owner decision): the server, never the
        # client, derives Writing turn provenance -- TurnSubmissionRequest
        # has no work_product_kind/canon_eligibility fields (extra="forbid"
        # rejects them if a client sends them). See
        # ``derive_writing_turn_request`` for the fail-closed derivation
        # rule (routed through story_bootstrap.py, not imported directly
        # here, per Binding Decision 2).
        writing_turn_request = derive_writing_turn_request(
            session, story.story_id, story.mode
        )
        return orchestrator.orchestrate_turn(
            story.story_id,
            node_id,
            user_input,
            sojourner_id,
            access_path,
            writing_turn_request=writing_turn_request,
        )

    return _run_turn_sync(
        session_factory,
        byok_readiness_provider,
        story_id,
        sojourner_id,
        orchestrate,
    )


def _resume_sync(
    session_factory: sessionmaker[Session],
    orchestrator: OrchestratorService,
    byok_readiness_provider: ByokCredentialReadinessProvider,
    actions: RpgActions,
    story_id: UUID,
    sojourner_id: UUID,
    sequence_id: UUID,
) -> TurnSubmissionResponse:
    def classify_settled(session: Session, story: Story) -> None:
        # 15b-32 ordering: without a runnable access path, a sequence that is
        # no longer the story's unresolved one still gets the owning
        # service's typed classification (already completed, or not found),
        # so a replay after the narration that exhausted access stays
        # success-equivalent. The story's unresolved sequence keeps the block
        # and its facts. The anchor is only read here (an uncommitted
        # bootstrap is rolled back with this session).
        anchor = ensure_story_turn_anchor_node(session, story.story_id, story.mode)
        actions.refuse_settled_resume(story.story_id, sequence_id, anchor.node_id)

    def orchestrate(
        session: Session, story: Story, node_id: UUID, access_path: RuntimeAccessPath
    ) -> OrchestrationResult:
        # CRD Issue 15b (15b-21, 15b-23): the orchestrator's own resume entry,
        # given the current canonical node exactly as an ordinary turn is.
        # Its typed refusals (not found, not ready, another node, already
        # completed) come back before any provider call and are translated
        # into the error envelope; no Turn exists, so nothing is settled.
        result = orchestrator.orchestrate_rpg_resume(
            story.story_id,
            node_id,
            sequence_id,
            access_path=access_path,
            sojourner_id=sojourner_id,
        )
        if result.action_sequence_error is not None:
            raise_for_action_sequence_error(result.action_sequence_error)
        return result

    return _run_turn_sync(
        session_factory,
        byok_readiness_provider,
        story_id,
        sojourner_id,
        orchestrate,
        before_access_block=classify_settled,
    )


def _run_turn_sync(
    session_factory: sessionmaker[Session],
    byok_readiness_provider: ByokCredentialReadinessProvider,
    story_id: UUID,
    sojourner_id: UUID,
    orchestrate: _Orchestrate,
    before_access_block: Callable[[Session, Story], None] | None = None,
) -> TurnSubmissionResponse:
    """Runs entirely in one worker thread (Binding Decision 8): opens and
    closes its own session so a slow turn never pins the event loop or a
    session across threads. Shared by ordinary turn submission and RPG
    resume, so both use the one access-path and settlement flow.
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
        byok_ready = (
            probe_byok_readiness(
                byok_readiness_provider, sojourner_id, {"story_id": str(story_id)}
            )
            is True
        )
        selection = select_access_path(status, byok_ready)

        if selection.access_path is None:
            assert selection.blocked_error_code is not None
            if before_access_block is not None:
                before_access_block(session, story)
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

        anchor = ensure_story_turn_anchor_node(session, story.story_id, story.mode)
        if anchor.created:
            # Pre-turn commit for durable story-bootstrap state only (not
            # turn output/canon/settlement -- none exists yet). The
            # orchestrator opens its own session immediately below, and
            # WriterService validates node_belongs_to_story there; a
            # just-flushed anchor is invisible to that separate session
            # until this one commits. Without this commit, the first turn
            # for a legacy/pre-API story (created before this anchor
            # existed) fails as PIPELINE_ERROR and only then persists the
            # anchor on retry. The anchor is idempotent v1 bootstrap state,
            # not narrative output -- it may legitimately survive a later
            # PIPELINE_ERROR from this same request.
            session.commit()

        result = orchestrate(session, story, anchor.node_id, selection.access_path)

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
            except SETTLEMENT_WARNING_ERRORS as exc:
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

        # Round 16 remediation (PR #126 P2): orchestrate_turn() runs in its
        # own session/transaction and may commit mode-session-state changes
        # there (e.g. the Writing setup-confirmation turn promoting
        # play_status to IN_PLAY). This session's identity map can already
        # hold that same row from an earlier pre-turn read (e.g.
        # derive_writing_turn_request() above) -- if so, a plain re-query
        # would silently keep serving the pre-turn attributes instead of the
        # orchestrator's committed write, because the ORM does not overwrite
        # an already-loaded object's attributes from a fresh SELECT by
        # default. expire_all() forces the next read to reflect what the
        # orchestrator actually committed. Safe to call here: settlement
        # (receive_entitlement_event) and any anchor-creation write above
        # have already committed by this point, so there is nothing pending
        # in this session for expire_all() to discard, and the route's own
        # commit/rollback semantics are otherwise unchanged.
        session.expire_all()

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
    return await run_under_story_lock(
        lock,
        _submit_turn_sync,
        request.app.state.session_factory,
        orchestrator,
        byok_readiness_provider,
        story_id,
        sojourner_id,
        body.user_input,
    )


@router.post(
    "/{story_id}/rpg/sequences/{sequence_id}/resume",
    response_model=TurnSubmissionResponse,
    responses=API_ERROR_RESPONSES,
)
async def resume_rpg_sequence(
    story_id: UUID,
    sequence_id: UUID,
    request: Request,
    orchestrator: OrchestratorService = Depends(get_orchestrator),
    byok_readiness_provider: ByokCredentialReadinessProvider = Depends(
        get_byok_readiness_provider
    ),
    sojourner_id: UUID = Depends(get_sojourner_id),
    lock: asyncio.Lock = Depends(get_story_lock),
    actions: RpgActions = Depends(get_rpg_actions),
) -> TurnSubmissionResponse:
    """Narrate a ``ready_for_narration`` action sequence (CRD Issue 15b).

    The client calls this as soon as an advancement returns
    ``ready_for_narration``, and again from the same affordance after a
    reload (15b-31). It is a turn: the ordinary access-path selection, the
    orchestrator's resume entry and the ordinary settlement. With no runnable
    access path, or after a failed, refused or blocked narration, the ready
    sequence and its validated results stay as they were, and a retry
    narrates the identical facts.

    ``409 action_sequence_already_completed`` means this sequence was already
    narrated: success-equivalent (15b-32). The client refetches the
    transcript and the pending interaction instead of presenting an error.
    """
    return await run_under_story_lock(
        lock,
        _resume_sync,
        request.app.state.session_factory,
        orchestrator,
        byok_readiness_provider,
        actions,
        story_id,
        sojourner_id,
        sequence_id,
    )


_MAX_PAGE_SIZE = 200


@router.get("/{story_id}/turns", response_model=TranscriptResponse)
def get_transcript(
    story_id: UUID,
    session: Session = Depends(get_session),
    limit: int = 50,
    offset: int = 0,
    latest: bool = False,
) -> TranscriptResponse:
    """Round 11 remediation (PR #126 P2): ``latest=true`` returns the most
    recent ``limit`` turns (still in chronological order within the page)
    instead of the first ``limit`` -- without it, a story past the default
    page size always re-showed its oldest turns on refresh, hiding newly
    delivered output that was correctly persisted. ``limit``/``offset``
    without ``latest`` are unchanged, for explicit oldest-first
    pagination/backfill.
    """
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
    if latest and offset != 0:
        raise ApiErrorResponse(
            422,
            ApiErrorCode.VALIDATION_FAILED,
            "offset is not supported together with latest=true",
        )

    turns = list_turns_by_story(
        session, story_id, limit=limit, offset=offset, newest_first=latest
    )
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
