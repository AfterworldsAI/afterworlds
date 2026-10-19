"""Shared FastAPI dependencies — DB session and derived Sojourner identity.

Single choke points (Binding Decision 12): every route obtains its session
and sojourner id through these, never by constructing their own.
"""

from __future__ import annotations

import asyncio
import contextlib
import contextvars
import functools
import inspect
import threading
from collections.abc import Callable, Iterator
from concurrent.futures import ThreadPoolExecutor
from typing import Any, cast
from uuid import UUID

import anyio
from fastapi import Request
from fastapi.routing import APIRoute
from sqlalchemy.orm import Session

from afterworlds.api.errors import ApiErrorCode, ApiErrorResponse
from afterworlds.api.rpg_actions import RpgActions
from afterworlds.persistence.crud.identity import get_or_create_sojourner_identity
from afterworlds.pipeline.orchestrator.service import OrchestratorService
from afterworlds.pipeline.provider import (
    ByokCredentialReadinessProvider,
    ByokSettingsService,
)
from afterworlds.remote.fence import FenceBusy, admitted_lease


def get_session(request: Request) -> Iterator[Session]:
    session_factory = request.app.state.session_factory
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


def get_sojourner_id(request: Request) -> UUID:
    """Return the acting entitlement subject.

    Never derived from client input (DoR-A) -- callers must not accept a
    ``sojourner_id`` from request bodies/headers/query params. Locally it is
    the server-provisioned Sojourner id; remotely, the authenticated hosted
    account's stable id (prerequisite #205, ADR-021 D4), resolved by the
    app-level ``enforce_access`` dependency from the server-side session.
    """
    return request.state.actor.account_id  # type: ignore[no-any-return]


def get_orchestrator(request: Request) -> OrchestratorService:
    """Return the app-wide OrchestratorService singleton.

    Tests override this via ``app.dependency_overrides[get_orchestrator]``
    instead of routes constructing their own orchestrator.
    """
    return request.app.state.orchestrator  # type: ignore[no-any-return]


def get_byok_readiness_provider(request: Request) -> ByokCredentialReadinessProvider:
    """Return the app-wide BYOK readiness provider (Issue 14a seam, #122/#123).

    Consumed only inside the DoR-E access-path selection helper -- never in
    a route handler directly, and never re-constructed per request.
    """
    return request.app.state.byok_readiness_provider  # type: ignore[no-any-return]


def get_byok_settings(request: Request) -> ByokSettingsService:
    """Return the app-wide BYOK settings service (CRD Issue 20), which shares
    the readiness provider's credential store."""
    return request.app.state.byok_settings  # type: ignore[no-any-return]


def get_story_lock(story_id: UUID, request: Request) -> asyncio.Lock:
    """Return (creating on first use) the per-story turn-submission lock.

    Single choke point (Binding Decision 8): the registry itself lives on
    app.state, created once in create_app(); this dependency is the only
    place route code touches it. ``defaultdict.__getitem__`` here is safe
    without extra locking: under asyncio's single-threaded cooperative model,
    a lookup/insert with no ``await`` inside it cannot be interleaved with
    another coroutine's lookup for the same key.
    """
    locks: dict[UUID, asyncio.Lock] = request.app.state.story_locks
    return locks[story_id]


async def run_under_story_lock[**P, T](
    lock: asyncio.Lock, fn: Callable[P, T], *args: P.args, **kwargs: P.kwargs
) -> T:
    """Run *fn* in a worker thread while holding the story's lock.

    The one guard every story mutation shares (Binding Decision 8): ordinary
    turns and the CRD Issue 15b roll, adjustment, decision and resume
    operations. Non-blocking: a held lock is ``409 TURN_IN_FLIGHT``, reused
    deliberately for the deterministic RPG operations (15b-29). The worker
    thread keeps a slow story from serializing other stories on the event
    loop; the lock is released in ``finally`` on every path.
    """
    if lock.locked():
        raise ApiErrorResponse(
            409,
            ApiErrorCode.TURN_IN_FLIGHT,
            "A turn is already in flight for this story.",
        )
    await lock.acquire()
    return await run_admitted_worker(lock, fn, *args, **kwargs)


#: Worker threads for admitted request work. A thread is never abandoned by
#: cancelling the awaiting task; interpreter exit waits for running workers.
_WORKERS = ThreadPoolExecutor(thread_name_prefix="afterworlds-worker")


async def run_admitted_worker[**P, T](
    story_lock: asyncio.Lock | None,
    fn: Callable[P, T],
    *args: P.args,
    **kwargs: P.kwargs,
) -> T:
    """Run *fn* in a worker thread whose protections and resources last as
    long as the synchronous worker itself (#205 §5).

    The worker owns a counted lease on the request's admitted account fence
    and, when given, the (already acquired) Story lock; both are released by
    the worker's own completion, never by a cancelled awaiting task. A
    cancelled request also keeps awaiting the worker before unwinding, so
    request-owned resources it uses (its Session, the dependency stack) are
    not closed under it. Closure, suppression or another same-Story mutation
    cannot start while its effects can still land; a failure to submit the
    work releases everything at once."""
    loop = asyncio.get_running_loop()
    try:
        release_lease = admitted_lease()
    except FenceBusy:
        if story_lock is not None:
            story_lock.release()
        raise ApiErrorResponse(
            409,
            ApiErrorCode.ACCOUNT_OPERATION_IN_PROGRESS,
            "An account operation is in progress; try again shortly.",
        ) from None

    def release() -> None:
        if release_lease is not None:
            release_lease()
        if story_lock is not None:
            with contextlib.suppress(RuntimeError):  # loop already closed
                loop.call_soon_threadsafe(story_lock.release)

    context = contextvars.copy_context()
    call = functools.partial(fn, *args, **kwargs)
    # Admission gate: ThreadPoolExecutor.submit can enqueue the work and then
    # fail starting a thread, leaving the item for a later worker. *fn* runs
    # only once submission has returned; rejected work never runs.
    decided, admitted = threading.Event(), [False]

    def gated() -> T:
        decided.wait()
        if not admitted[0]:
            return cast(T, None)  # never awaited: submission failed
        return context.run(call)

    try:
        worker = _WORKERS.submit(gated)
    except BaseException:
        decided.set()  # rejected: a queued item returns without running fn
        release()
        raise
    admitted[0] = True
    decided.set()
    # Runs when the thread finishes (or if it never started).
    worker.add_done_callback(lambda _: release())
    outcome = asyncio.wrap_future(worker)
    try:
        return await asyncio.shield(outcome)
    except asyncio.CancelledError:
        # The request owns resources the worker is using (its Session, the
        # dependency stack): keep this operation alive until the worker
        # actually ends, then let the cancellation unwind them.
        await _drain(outcome)
        raise


async def _drain(outcome: asyncio.Future[Any]) -> None:
    """Wait for *outcome* despite further cancellation (raw or AnyIO)."""
    while not outcome.done():
        try:
            with anyio.CancelScope(shield=True):
                await asyncio.shield(outcome)
        except asyncio.CancelledError:
            continue
        except Exception:  # the worker's own error; the request is gone
            return
    if not outcome.cancelled():
        outcome.exception()  # retrieved


class AdmittedWorkerRoute(APIRoute):
    """Route class for every API router: a synchronous handler runs as an
    admitted worker (:func:`run_admitted_worker`) instead of Starlette's
    threadpool, so a cancelled request neither releases the account fence
    nor closes the handler's Session while its effects can still land."""

    def __init__(self, path: str, endpoint: Callable[..., Any], **kwargs: Any) -> None:
        if not inspect.iscoroutinefunction(endpoint):
            endpoint = _as_admitted_worker(endpoint)
        super().__init__(path, endpoint, **kwargs)


def _as_admitted_worker(sync: Callable[..., Any]) -> Callable[..., Any]:
    @functools.wraps(sync)
    async def endpoint(*args: Any, **kwargs: Any) -> Any:
        return await run_admitted_worker(None, sync, *args, **kwargs)

    # The handler's signature with its annotations already resolved in its
    # own module: FastAPI versions that evaluate string annotations in the
    # *wrapper's* globals (0.115 does) then see real types, not names this
    # module lacks.
    endpoint.__signature__ = inspect.signature(  # type: ignore[attr-defined]
        sync, eval_str=True
    )
    return endpoint


def get_rpg_actions(request: Request) -> RpgActions:
    """Return the app-wide RPG action seam over the one
    ActionResolutionService the orchestrator also owns (CRD Issue 15b)."""
    return request.app.state.rpg_actions  # type: ignore[no-any-return]


def provision_sojourner_id(session_factory: object) -> UUID:
    """Resolve (creating on first run) the single local Sojourner id.

    Called once at ``create_app()`` construction time -- single uvicorn
    worker (Binding Decision 8) means no startup race to guard against.
    """
    factory = session_factory
    assert callable(factory)
    session = factory()
    try:
        identity = get_or_create_sojourner_identity(session)
        session.commit()
        return identity.sojourner_id
    finally:
        session.close()
