"""/api/admin -- Owner-administrator staff context (prerequisite #205 §1/§2).

Staff authority comes only from a staff session for the principal holding the
active Owner-administrator binding (``python -m afterworlds.remote.bootstrap``
is the only way to create one). ``enforce_access`` rejects ordinary sessions,
the Owner's included, on every ``/api/admin/*`` route except staff sign-in.
Targets are explicit path parameters; the actor always comes from the
session. Support workflows themselves are CRD Issue 22's.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from afterworlds.api.account import build_admin_account_view
from afterworlds.api.deps import AdmittedWorkerRoute, get_session
from afterworlds.api.dto import (
    AdminAccountViewResponse,
    RevokeSessionsRequest,
    RevokeSessionsResponse,
    SignInRequest,
    StaffSessionResponse,
)
from afterworlds.api.errors import ApiError, ApiErrorCode, ApiErrorResponse
from afterworlds.api.remote_access import (
    STAFF_COOKIE,
    clear_session_cookie,
    get_actor,
    identity_call,
    identity_service,
    run_identity,
    set_session_cookie,
)
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
