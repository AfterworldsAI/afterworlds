"""/api/auth -- remote sign-in, enrollment, recovery (prerequisite #205 §1).

Thin handlers over ``IdentityService``. Enrollment and recovery requests
answer the same ``accepted`` body whatever the address's state, and every
credential failure is the one ``authentication_failed`` error, so no response
reveals whether an account exists. Codes arrive only through the notice
transport, never in a response.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request, Response

from afterworlds.api.deps import AdmittedWorkerRoute
from afterworlds.api.dto import (
    AcceptedResponse,
    CompleteEnrollmentRequest,
    CompleteRecoveryRequest,
    ContactAddressRequest,
    DeploymentKind,
    SessionStatusResponse,
    SignInRequest,
)
from afterworlds.api.errors import ApiError
from afterworlds.api.remote_access import (
    SESSION_COOKIE,
    clear_session_cookie,
    identity_call,
    identity_service,
    set_session_cookie,
)
from afterworlds.remote.identity import (
    SOJOURNER_SESSION_LIFETIME,
    IdentityError,
    IdentityService,
    SessionContext,
    SignInResult,
)

router = APIRouter(prefix="/api/auth", tags=["auth"], route_class=AdmittedWorkerRoute)

_RESPONSES: dict[int | str, dict[str, Any]] = {
    status: {"model": ApiError} for status in (401, 403, 404, 422, 503)
}


def _identity(request: Request) -> IdentityService:
    identity = identity_service(request)
    # enforce_access already refused every /api/auth route but /session locally.
    assert identity is not None
    return identity


@router.get("/session", response_model=SessionStatusResponse, responses=_RESPONSES)
async def get_session_status(request: Request) -> SessionStatusResponse:
    identity = identity_service(request)
    if identity is None:
        return SessionStatusResponse(deployment=DeploymentKind.LOCAL, signed_in=False)
    token = request.cookies.get(SESSION_COOKIE)

    def status() -> SessionStatusResponse:
        assert identity is not None
        try:
            actor = identity.resolve(token, SessionContext.SOJOURNER)
        except IdentityError:
            # A missing, expired or revoked session is a signed-out answer;
            # an unreachable store is not (identity_call: 503).
            return SessionStatusResponse(
                deployment=DeploymentKind.REMOTE, signed_in=False
            )
        return SessionStatusResponse(
            deployment=DeploymentKind.REMOTE,
            signed_in=True,
            account_id=actor.account_id,
            contact_address=identity.contact_address_for(actor),
        )

    return await identity_call(status)


@router.post(
    "/register", response_model=AcceptedResponse, status_code=202, responses=_RESPONSES
)
async def register(body: ContactAddressRequest, request: Request) -> AcceptedResponse:
    await identity_call(_identity(request).register, body.contact_address)
    return AcceptedResponse()


@router.post(
    "/register/complete", response_model=AcceptedResponse, responses=_RESPONSES
)
async def complete_registration(
    body: CompleteEnrollmentRequest, request: Request
) -> AcceptedResponse:
    await identity_call(
        _identity(request).complete_enrollment,
        body.contact_address,
        body.code.get_secret_value(),
        body.password.get_secret_value(),
    )
    return AcceptedResponse()


@router.post("/sign-in", response_model=SessionStatusResponse, responses=_RESPONSES)
async def sign_in(
    body: SignInRequest, request: Request, response: Response
) -> SessionStatusResponse:
    identity = _identity(request)

    def sign_in_and_address() -> tuple[SignInResult, str | None]:
        result = identity.sign_in(
            body.contact_address,
            body.password.get_secret_value(),
            SessionContext.SOJOURNER,
        )
        return result, identity.contact_address_for(result.actor)

    # Both reads finish before any cookie is set: a failure sets none.
    result, contact_address = await identity_call(sign_in_and_address)
    set_session_cookie(
        request,
        response,
        SESSION_COOKIE,
        result.token,
        int(SOJOURNER_SESSION_LIFETIME.total_seconds()),
    )
    return SessionStatusResponse(
        deployment=DeploymentKind.REMOTE,
        signed_in=True,
        account_id=result.actor.account_id,
        contact_address=contact_address,
    )


@router.post("/sign-out", response_model=SessionStatusResponse, responses=_RESPONSES)
async def sign_out(request: Request, response: Response) -> SessionStatusResponse:
    await identity_call(
        _identity(request).sign_out, request.cookies.get(SESSION_COOKIE)
    )
    clear_session_cookie(request, response, SESSION_COOKIE)
    return SessionStatusResponse(deployment=DeploymentKind.REMOTE, signed_in=False)


@router.post(
    "/recovery", response_model=AcceptedResponse, status_code=202, responses=_RESPONSES
)
async def begin_recovery(
    body: ContactAddressRequest, request: Request
) -> AcceptedResponse:
    await identity_call(_identity(request).begin_recovery, body.contact_address)
    return AcceptedResponse()


@router.post(
    "/recovery/complete", response_model=AcceptedResponse, responses=_RESPONSES
)
async def complete_recovery(
    body: CompleteRecoveryRequest, request: Request, response: Response
) -> AcceptedResponse:
    await identity_call(
        _identity(request).complete_recovery,
        body.contact_address,
        body.code.get_secret_value(),
        body.new_password.get_secret_value(),
    )
    # Any session this browser held was revoked with the rest.
    clear_session_cookie(request, response, SESSION_COOKIE)
    return AcceptedResponse()
