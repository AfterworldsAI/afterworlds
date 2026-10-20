"""/api/admin -- Owner-administrator staff context (prerequisite #205 §1/§2).

Staff authority comes only from a staff session for the principal holding the
active Owner-administrator binding (``python -m afterworlds.remote.bootstrap``
is the only way to create one). ``enforce_access`` rejects ordinary sessions,
the Owner's included, on every ``/api/admin/*`` route except staff sign-in.
Targets are explicit path parameters; the actor always comes from the
session. Support workflows themselves are CRD Issue 22's.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from afterworlds.api.account import (
    build_admin_account_view,
    hosted_credits,
    replay_dto,
)
from afterworlds.api.deps import AdmittedWorkerRoute, get_session
from afterworlds.api.dto import (
    AdminAccountViewResponse,
    AnomalyDTO,
    AnomalyNoteDTO,
    AnomalyNoteRequest,
    AnomalyReportResponse,
    CreditAdjustmentPreviewRequest,
    CreditAdjustmentPreviewResponse,
    CreditAdjustmentRequest,
    DataRequestDTO,
    DataRequestListResponse,
    DataRequestStepRequest,
    EntitlementHistoryResponse,
    RejectDataRequest,
    RetentionSweepResponse,
    RevokeSessionsRequest,
    RevokeSessionsResponse,
    SignInRequest,
    StaffSessionResponse,
    SupportHistoryResponse,
    SupportOperationResponse,
)
from afterworlds.api.errors import ApiError, ApiErrorCode, ApiErrorResponse
from afterworlds.api.operations import (
    history_item,
    request_dto,
    run_operation,
    support_event,
)
from afterworlds.api.remote_access import (
    STAFF_COOKIE,
    clear_session_cookie,
    get_actor,
    identity_call,
    identity_service,
    run_identity,
    set_session_cookie,
)
from afterworlds.entitlement.inspection import list_events, replay_check
from afterworlds.entitlement.service import EntitlementService
from afterworlds.operations.anomalies import Anomaly
from afterworlds.operations.retention import sweep
from afterworlds.operations.service import DataRequestService
from afterworlds.operations.support import (
    AdjustmentRequest,
    OperationStatus,
    SupportService,
    parse_delta,
)
from afterworlds.remote.control_store import utc_now
from afterworlds.remote.identity import (
    STAFF_SESSION_LIFETIME,
    Actor,
    IdentityService,
    SessionContext,
)

router = APIRouter(prefix="/api/admin", tags=["admin"], route_class=AdmittedWorkerRoute)

_RESPONSES: dict[int | str, dict[str, Any]] = {
    status: {"model": ApiError} for status in (401, 403, 404, 422, 503)
}
_OP_RESPONSES: dict[int | str, dict[str, Any]] = {
    status: {"model": ApiError} for status in (401, 403, 404, 409, 422, 503)
}


def _identity(request: Request) -> IdentityService:
    identity = identity_service(request)
    assert identity is not None  # enforce_access refuses /api/admin locally
    return identity


@router.post("/session", response_model=StaffSessionResponse, responses=_RESPONSES)
async def staff_sign_in(
    body: SignInRequest, request: Request, response: Response
) -> StaffSessionResponse:
    result = await identity_call(
        _identity(request).sign_in,
        body.contact_address,
        body.password.get_secret_value(),
        SessionContext.STAFF,
    )
    set_session_cookie(
        request,
        response,
        STAFF_COOKIE,
        result.token,
        int(STAFF_SESSION_LIFETIME.total_seconds()),
    )
    return StaffSessionResponse(signed_in=True, expires_at=result.expires_at)


@router.delete("/session", response_model=StaffSessionResponse, responses=_RESPONSES)
async def staff_sign_out(request: Request, response: Response) -> StaffSessionResponse:
    await identity_call(_identity(request).sign_out, request.cookies.get(STAFF_COOKIE))
    clear_session_cookie(request, response, STAFF_COOKIE)
    return StaffSessionResponse(signed_in=False)


@router.get(
    "/accounts/{account_id}",
    response_model=AdminAccountViewResponse,
    responses=_RESPONSES,
)
def get_account_view(
    account_id: UUID,
    request: Request,
    session: Session = Depends(get_session),
) -> AdminAccountViewResponse:
    record = run_identity(_identity(request).get_account, account_id)
    if record is None:
        raise ApiErrorResponse(404, ApiErrorCode.NOT_FOUND, "Account not found.")
    return build_admin_account_view(session, record)


@router.post(
    "/accounts/{account_id}/sessions/revoke",
    response_model=RevokeSessionsResponse,
    responses=_RESPONSES,
)
async def revoke_account_sessions(
    account_id: UUID,
    body: RevokeSessionsRequest,
    request: Request,
    actor: Actor = Depends(get_actor),
) -> RevokeSessionsResponse:
    revoked = await identity_call(
        _identity(request).revoke_account_sessions, actor, account_id, body.reason
    )
    return RevokeSessionsResponse(account_id=account_id, revoked_sessions=revoked)


# ---------------------------------------------------------------------------
# CRD Issue 22: support lookup, ordered history and controlled remediation.
# ---------------------------------------------------------------------------

_HISTORY_MAX = 200


def _support(request: Request) -> SupportService:
    return request.app.state.support  # type: ignore[no-any-return]


def _require_account(request: Request, account_id: UUID) -> None:
    if run_identity(_identity(request).get_account, account_id) is None:
        raise ApiErrorResponse(404, ApiErrorCode.NOT_FOUND, "Account not found.")


@router.get(
    "/accounts/{account_id}/entitlement-history",
    response_model=EntitlementHistoryResponse,
    responses=_OP_RESPONSES,
)
def get_entitlement_history(
    account_id: UUID,
    request: Request,
    after_sequence: int = 0,
    limit: int = 50,
    session: Session = Depends(get_session),
) -> EntitlementHistoryResponse:
    if not 1 <= limit <= _HISTORY_MAX or after_sequence < 0:
        raise ApiErrorResponse(
            422,
            ApiErrorCode.VALIDATION_FAILED,
            f"limit must be 1-{_HISTORY_MAX} and after_sequence >= 0",
        )
    _require_account(request, account_id)
    page = run_operation(
        lambda: list_events(
            session, account_id, after_sequence=after_sequence, limit=limit
        )
    )
    return EntitlementHistoryResponse(
        account_id=account_id,
        after_sequence=after_sequence,
        events=[history_item(e) for e in page.events],
        total_events=page.total_events,
        next_after_sequence=page.next_after_sequence,
        replay=replay_dto(run_operation(lambda: replay_check(session, account_id))),
    )


@router.get(
    "/accounts/{account_id}/support-actions",
    response_model=SupportHistoryResponse,
    responses=_OP_RESPONSES,
)
def get_support_actions(account_id: UUID, request: Request) -> SupportHistoryResponse:
    _require_account(request, account_id)
    events = run_operation(lambda: _support(request).history(account_id))
    return SupportHistoryResponse(
        account_id=account_id, events=[support_event(e) for e in events]
    )


@router.post(
    "/accounts/{account_id}/credit-adjustments/preview",
    response_model=CreditAdjustmentPreviewResponse,
    responses=_OP_RESPONSES,
)
def preview_credit_adjustment(
    account_id: UUID,
    body: CreditAdjustmentPreviewRequest,
    request: Request,
    session: Session = Depends(get_session),
) -> CreditAdjustmentPreviewResponse:
    _require_account(request, account_id)
    preview = run_operation(
        lambda: _support(request).preview_adjustment(
            account_id,
            parse_delta(body.hosted_credit_delta),
            parse_delta(body.top_up_credit_delta),
        )
    )
    status = EntitlementService(session).get_access_path_status(account_id)
    projection = preview.projection
    return CreditAdjustmentPreviewResponse(
        account_id=account_id,
        current=hosted_credits(status),
        hosted_credit_delta=f"{preview.hosted_credit_delta:.4f}",
        top_up_credit_delta=f"{preview.top_up_credit_delta:.4f}",
        resulting_included=(
            f"{preview.resulting_hosted:.4f}"
            if preview.resulting_hosted is not None
            else None
        ),
        resulting_top_up=(
            f"{preview.resulting_top_up:.4f}"
            if preview.resulting_top_up is not None
            else None
        ),
        last_entitlement_event_id=(
            projection.last_entitlement_event_id if projection else None
        ),
        refusal_code=preview.refusal_code,
    )


def _operation_response(
    request: Request, session: Session, status: OperationStatus, account_id: UUID
) -> SupportOperationResponse:
    record = run_identity(_identity(request).get_account, account_id)
    session.expire_all()
    return SupportOperationResponse(
        operation_id=status.operation_id,
        outcome_code=status.outcome_code,
        source_entitlement_event_id=(
            UUID(status.source_entitlement_event_id)
            if status.source_entitlement_event_id
            else None
        ),
        events=[support_event(e) for e in status.events],
        account=build_admin_account_view(session, record) if record else None,
    )


@router.post(
    "/accounts/{account_id}/credit-adjustments",
    response_model=SupportOperationResponse,
    responses=_OP_RESPONSES,
)
def adjust_credits(
    account_id: UUID,
    body: CreditAdjustmentRequest,
    request: Request,
    actor: Actor = Depends(get_actor),
    session: Session = Depends(get_session),
) -> SupportOperationResponse:
    status = run_operation(
        lambda: _support(request).adjust_credits(
            actor,
            AdjustmentRequest(
                operation_id=body.operation_id,
                account_id=account_id,
                hosted_credit_delta=parse_delta(body.hosted_credit_delta),
                top_up_credit_delta=parse_delta(body.top_up_credit_delta),
                reason=body.reason,
                expected_last_event_id=body.expected_last_entitlement_event_id,
            ),
        )
    )
    if status.outcome_code != "committed":
        # Rejection and failure stay distinguishable from success, carrying the
        # operation identity for a status read.
        status_code, code = _REJECTIONS.get(
            status.outcome_code, (503, ApiErrorCode.OPERATION_OUTCOME_UNKNOWN)
        )
        raise ApiErrorResponse(
            status_code,
            code,
            f"The adjustment was not applied ({status.outcome_code}).",
            detail={
                "operation_id": str(status.operation_id),
                "outcome_code": status.outcome_code,
            },
        )
    return _operation_response(request, session, status, account_id)


_REJECTIONS: dict[str, tuple[int, ApiErrorCode]] = {
    "rejected_stale": (409, ApiErrorCode.OPERATION_STALE),
    "rejected_precondition": (409, ApiErrorCode.OPERATION_PRECONDITION_FAILED),
    "conflict": (409, ApiErrorCode.OPERATION_CONFLICT),
    "failed": (503, ApiErrorCode.OPERATION_UNAVAILABLE),
}


@router.get(
    "/support-operations/{operation_id}",
    response_model=SupportOperationResponse,
    responses=_OP_RESPONSES,
)
def get_support_operation(
    operation_id: UUID,
    request: Request,
    session: Session = Depends(get_session),
) -> SupportOperationResponse:
    status = run_operation(lambda: _support(request).status(operation_id))
    return _operation_response(
        request, session, status, UUID(status.events[0].target_ref)
    )


# -- CRD Issue 22: administrator review and fulfillment of data requests ----


def _requests(request: Request) -> DataRequestService:
    return request.app.state.data_requests  # type: ignore[no-any-return]


@router.get(
    "/data-requests", response_model=DataRequestListResponse, responses=_OP_RESPONSES
)
def list_all_data_requests(request: Request) -> DataRequestListResponse:
    views = run_operation(lambda: _requests(request).list_all())
    return DataRequestListResponse(
        requests=[request_dto(v, administrator=True) for v in views]
    )


@router.get(
    "/data-requests/{request_id}",
    response_model=DataRequestDTO,
    responses=_OP_RESPONSES,
)
def get_any_data_request(request_id: UUID, request: Request) -> DataRequestDTO:
    view = run_operation(lambda: _requests(request).get(str(request_id)))
    return request_dto(view, administrator=True)


@router.post(
    "/data-requests/{request_id}/approve",
    response_model=DataRequestDTO,
    responses=_OP_RESPONSES,
)
def approve_data_request(
    request_id: UUID,
    body: DataRequestStepRequest,
    request: Request,
    actor: Actor = Depends(get_actor),
) -> DataRequestDTO:
    view = run_operation(
        lambda: _requests(request).approve(
            actor,
            str(request_id),
            expected_revision=body.expected_revision,
            reason=body.reason,
        )
    )
    return request_dto(view, administrator=True)


@router.post(
    "/data-requests/{request_id}/reject",
    response_model=DataRequestDTO,
    responses=_OP_RESPONSES,
)
def reject_data_request(
    request_id: UUID,
    body: RejectDataRequest,
    request: Request,
    actor: Actor = Depends(get_actor),
) -> DataRequestDTO:
    view = run_operation(
        lambda: _requests(request).reject(
            actor,
            str(request_id),
            expected_revision=body.expected_revision,
            reason_code=body.reason_code,
            reason=body.reason,
        )
    )
    return request_dto(view, administrator=True)


@router.post(
    "/data-requests/{request_id}/execute",
    response_model=DataRequestDTO,
    responses=_OP_RESPONSES,
)
def execute_data_request(
    request_id: UUID,
    body: DataRequestStepRequest,
    request: Request,
    actor: Actor = Depends(get_actor),
) -> DataRequestDTO:
    """Run (or retry/resume) fulfillment as a new attempt. The response is
    the recorded outcome: completed, failed, or in progress with its pending
    phases."""
    view = run_operation(
        lambda: _requests(request).execute(
            actor, str(request_id), expected_revision=body.expected_revision
        )
    )
    return request_dto(view, administrator=True)


@router.post(
    "/data-requests/{request_id}/finalize",
    response_model=DataRequestDTO,
    responses=_OP_RESPONSES,
)
def finalize_data_request(
    request_id: UUID, request: Request, actor: Actor = Depends(get_actor)
) -> DataRequestDTO:
    view = run_operation(lambda: _requests(request).finalize(actor, str(request_id)))
    return request_dto(view, administrator=True)


# -- CRD Issue 22: anomaly visibility and retention maintenance -------------


def _anomaly_dto(a: Anomaly) -> AnomalyDTO:
    return AnomalyDTO(
        anomaly_id=a.anomaly_id,
        source_kind=a.source_kind,
        source_id=a.source_id,
        subject_ref=UUID(a.subject_ref) if a.subject_ref else None,
        observed_at=a.observed_at,
        signal_code=a.signal_code,
        explanation=a.explanation,
        investigation_state=a.investigation_state,
        notes=[
            AnomalyNoteDTO(
                state=str(n["state"]),
                note_code=n["note_code"],
                note_text=n["note_text"],
                actor=str(n["actor"]),
                recorded_at=datetime.fromisoformat(str(n["recorded_at"])),
            )
            for n in a.notes
        ],
    )


@router.get("/anomalies", response_model=AnomalyReportResponse, responses=_OP_RESPONSES)
def get_anomalies(request: Request) -> AnomalyReportResponse:
    report = run_operation(lambda: request.app.state.anomalies.report())
    return AnomalyReportResponse(
        anomalies=[_anomaly_dto(a) for a in report.anomalies],
        sources=report.sources,
        generated_at=report.generated_at,
    )


@router.post(
    "/anomalies/{anomaly_id}/notes", response_model=AnomalyDTO, responses=_OP_RESPONSES
)
def note_anomaly(
    anomaly_id: str,
    body: AnomalyNoteRequest,
    request: Request,
    actor: Actor = Depends(get_actor),
) -> AnomalyDTO:
    if not run_identity(_identity(request).actor_is_current, actor):
        raise ApiErrorResponse(
            401, ApiErrorCode.AUTHENTICATION_REQUIRED, "Authentication required."
        )
    assert actor.principal_ref is not None
    anomaly = run_operation(
        lambda: request.app.state.anomalies.add_note(
            actor.principal_ref,
            anomaly_id,
            state=body.state,
            note_code=body.note_code,
            note_text=body.note_text,
        )
    )
    return _anomaly_dto(anomaly)


@router.post(
    "/maintenance/retention-sweep",
    response_model=RetentionSweepResponse,
    responses=_OP_RESPONSES,
)
def run_retention_sweep(
    request: Request, actor: Actor = Depends(get_actor)
) -> RetentionSweepResponse:
    """Apply the approved D4 expiries now, inside the serving process (the
    single writer). Physical compaction stays an offline command."""
    if not run_identity(_identity(request).actor_is_current, actor):
        raise ApiErrorResponse(
            401, ApiErrorCode.AUTHENTICATION_REQUIRED, "Authentication required."
        )
    now = utc_now()
    result = run_operation(
        lambda: sweep(
            ops=request.app.state.control_factory,
            content=request.app.state.session_factory,
            control=request.app.state.control_factory,
            now=now,
        )
    )
    return RetentionSweepResponse(counts=result.as_dict(), swept_at=now)
