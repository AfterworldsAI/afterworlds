"""Request-level identity and ownership enforcement -- prerequisite #205.

``enforce_access`` is installed once as an app-level dependency, so it runs
before every route's own dependencies and body handling:

* local deployment: the actor is the single local owner (CRD Issue 19
  DoR-A); remote-only routes answer ``deployment_route_unavailable``;
* remote deployment: default deny. Only ``PUBLIC_PATHS`` run without a
  session; ``/api/admin/*`` needs a staff session; everything else needs an
  ordinary Sojourner session. Unsafe methods must carry ``CSRF_HEADER``. The
  local BYOK key/settings routes are refused before their body is used.

``authorize_story`` is the one Story guard, attached to every
``/api/stories/{story_id}`` route: a foreign, unowned or suppressed Story is
the same ``404`` as a missing one.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from typing import NoReturn
from uuid import UUID

from fastapi import Request, Response
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.exc import SQLAlchemyError

from afterworlds.api.errors import ApiErrorCode, ApiErrorResponse
from afterworlds.remote.access import (
    AccessPolicy,
    DelayedWorkScope,
    bind_story,
    work_scope,
)
from afterworlds.remote.fence import AccountFence, FenceBusy, mark_fence_held
from afterworlds.remote.identity import (
    Actor,
    ActorKind,
    IdentityError,
    IdentityErrorKind,
    IdentityService,
    SessionContext,
)

SESSION_COOKIE = "aw_session"
STAFF_COOKIE = "aw_staff_session"
CSRF_HEADER = "X-Afterworlds-Request"

#: Remote routes reachable without a session. Everything else is denied.
PUBLIC_PATHS = frozenset(
    {
        "/api/health",
        "/api/auth/session",
        "/api/auth/register",
        "/api/auth/register/complete",
        "/api/auth/sign-in",
        "/api/auth/sign-out",
        "/api/auth/recovery",
        "/api/auth/recovery/complete",
        "/api/admin/session",
    }
)
_REMOTE_ONLY_PREFIXES = ("/api/admin", "/api/auth/", "/api/account/close")
_LOCAL_ONLY_PREFIX = "/api/account/byok/"
CLOSE_PATH = "/api/account/close"
_SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})

_IDENTITY_ERRORS: dict[IdentityErrorKind, tuple[int, ApiErrorCode]] = {
    IdentityErrorKind.AUTHENTICATION_FAILED: (401, ApiErrorCode.AUTHENTICATION_FAILED),
    IdentityErrorKind.AUTHENTICATION_REQUIRED: (
        401,
        ApiErrorCode.AUTHENTICATION_REQUIRED,
    ),
    IdentityErrorKind.STAFF_AUTHORITY_REQUIRED: (
        403,
        ApiErrorCode.STAFF_AUTHORITY_REQUIRED,
    ),
    IdentityErrorKind.INVALID_INPUT: (422, ApiErrorCode.VALIDATION_FAILED),
    IdentityErrorKind.TARGET_NOT_FOUND: (404, ApiErrorCode.NOT_FOUND),
    IdentityErrorKind.BOOTSTRAP_REFUSED: (403, ApiErrorCode.STAFF_AUTHORITY_REQUIRED),
}


def raise_identity_error(exc: IdentityError) -> NoReturn:
    status_code, code = _IDENTITY_ERRORS[exc.kind]
    raise ApiErrorResponse(status_code, code, str(exc)) from None


def identity_service(request: Request) -> IdentityService | None:
    return request.app.state.identity  # type: ignore[no-any-return]


async def enforce_access(request: Request) -> AsyncIterator[None]:
    """App-level dependency: resolve the trusted actor or refuse the request.

    A remote Sojourner request then holds its account's fence shared for the
    whole handler, revalidates its session under that fence, and runs under a
    trusted :class:`DelayedWorkScope` that owning services check before any
    effect. Closure (and CRD Issue 22 suppression) take the fence exclusive.
    """
    path = request.url.path
    identity = identity_service(request)
    if identity is None:
        if path.startswith(_REMOTE_ONLY_PREFIXES) and path != "/api/auth/session":
            raise ApiErrorResponse(
                404,
                ApiErrorCode.DEPLOYMENT_ROUTE_UNAVAILABLE,
                "This route is available only in the remote deployment.",
            )
        request.state.actor = Actor(
            kind=ActorKind.LOCAL, account_id=request.app.state.sojourner_id
        )
        yield
        return
    if request.method not in _SAFE_METHODS and request.headers.get(CSRF_HEADER) != "1":
        raise ApiErrorResponse(
            403,
            ApiErrorCode.REQUEST_ORIGIN_REJECTED,
            "State-changing requests must come from the Afterworlds client.",
        )
    if path.startswith(_LOCAL_ONLY_PREFIX):
        raise ApiErrorResponse(
            409,
            ApiErrorCode.BYOK_LOCAL_ONLY,
            "BYOK credentials are managed only by a local installation; the "
            "remote service never accepts or stores provider keys.",
        )
    if path in PUBLIC_PATHS:
        yield
        return
    if path.startswith("/api/admin/"):
        # Staff effects revalidate the staff session inside their own
        # control-store transaction (IdentityService._require_current).
        request.state.actor = await identity_call(_resolve_staff, request, identity)
        yield
        return
    actor = await identity_call(
        identity.resolve, request.cookies.get(SESSION_COOKIE), SessionContext.SOJOURNER
    )
    request.state.actor = actor
    if path == CLOSE_PATH:
        # Closure takes this account's fence exclusive itself.
        yield
        return
    fence: AccountFence = request.app.state.account_fence
    try:
        shared = fence.shared(actor.account_id)
        shared.__enter__()
    except FenceBusy:
        raise ApiErrorResponse(
            409,
            ApiErrorCode.ACCOUNT_OPERATION_IN_PROGRESS,
            "An account operation is in progress; try again shortly.",
        ) from None
    try:
        # Admitted under the fence: the session must still be current, so a
        # closure that completed before admission is never outrun.
        if not await identity_call(identity.actor_is_current, actor):
            raise ApiErrorResponse(
                401, ApiErrorCode.AUTHENTICATION_REQUIRED, "Authentication required."
            )
        # An account under deletion admits no new account-owned effect.
        if request.method not in _SAFE_METHODS and await run_in_threadpool(
            access_policy(request).account_suppressed, actor.account_id
        ):
            raise ApiErrorResponse(
                409,
                ApiErrorCode.ACCOUNT_OPERATION_IN_PROGRESS,
                "This account is being deleted; no changes are accepted.",
            )
        mark_fence_held(actor.account_id)
        with work_scope(DelayedWorkScope(actor.account_id, None, "request")):
            yield
    finally:
        shared.__exit__(None, None, None)


async def identity_call[**P, T](
    fn: Callable[P, T], *args: P.args, **kwargs: P.kwargs
) -> T:
    """Run an identity-store call off the event loop with typed failures.

    Every HTTP identity operation goes through this (or ``run_identity`` from
    a sync handler), so an unreachable identity store is the same sanitized
    ``503 identity_unavailable`` on public, staff and admitted routes."""
    return await run_in_threadpool(lambda: run_identity(fn, *args, **kwargs))


def run_identity[**P, T](fn: Callable[P, T], *args: P.args, **kwargs: P.kwargs) -> T:
    """Call *fn* (identity-store work only) with typed failures."""
    try:
        return fn(*args, **kwargs)
    except IdentityError as exc:
        raise_identity_error(exc)
    except SQLAlchemyError:
        # The identity authority is unreachable: fail closed, typed, and
        # without the driver's text.
        raise ApiErrorResponse(
            503,
            ApiErrorCode.IDENTITY_UNAVAILABLE,
            "Sign-in is temporarily unavailable.",
        ) from None


def _resolve_staff(request: Request, identity: IdentityService) -> Actor:
    try:
        return identity.resolve(request.cookies.get(STAFF_COOKIE), SessionContext.STAFF)
    except IdentityError:
        # A valid ordinary session -- even the Owner's -- carries no staff
        # authority: say so instead of asking it to sign in again.
        try:
            identity.resolve(
                request.cookies.get(SESSION_COOKIE), SessionContext.SOJOURNER
            )
        except IdentityError:
            raise
        raise IdentityError(
            IdentityErrorKind.STAFF_AUTHORITY_REQUIRED, "Staff authority is required."
        ) from None


def get_actor(request: Request) -> Actor:
    return request.state.actor  # type: ignore[no-any-return]


def access_policy(request: Request) -> AccessPolicy:
    return request.app.state.access_policy  # type: ignore[no-any-return]


async def authorize_story(story_id: UUID, request: Request) -> None:
    """The one Story guard (router-level dependency on Story routes). Runs
    after ``enforce_access`` has admitted the request under the fence, then
    narrows the request's trusted scope to this Story."""
    policy = access_policy(request)
    if not policy.remote:
        return

    def allowed() -> bool:
        with request.app.state.session_factory() as session:
            return policy.actor_may_access(session, get_actor(request), story_id)

    if not await run_in_threadpool(allowed):
        raise ApiErrorResponse(
            404, ApiErrorCode.NOT_FOUND, f"Story {story_id} not found"
        )
    bind_story(story_id)


def set_session_cookie(
    request: Request, response: Response, name: str, token: str, max_age: int
) -> None:
    response.set_cookie(
        name,
        token,
        max_age=max_age,
        httponly=True,
        secure=request.app.state.settings.cookie_secure,
        samesite="strict",
        path="/",
    )


def clear_session_cookie(request: Request, response: Response, name: str) -> None:
    response.delete_cookie(
        name,
        httponly=True,
        secure=request.app.state.settings.cookie_secure,
        samesite="strict",
        path="/",
    )
