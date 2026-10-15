"""Shared FastAPI dependencies — DB session and derived Sojourner identity.

Single choke points (Binding Decision 12): every route obtains its session
and sojourner id through these, never by constructing their own.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Iterator
from uuid import UUID

from fastapi import Request
from sqlalchemy.orm import Session

from afterworlds.api.errors import ApiErrorCode, ApiErrorResponse
from afterworlds.api.rpg_actions import RpgActions
from afterworlds.persistence.crud.identity import get_or_create_sojourner_identity
from afterworlds.pipeline.orchestrator.service import OrchestratorService
from afterworlds.pipeline.provider import ByokCredentialReadinessProvider


def get_session(request: Request) -> Iterator[Session]:
    session_factory = request.app.state.session_factory
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


def get_sojourner_id(request: Request) -> UUID:
    """Return the server-provisioned Sojourner id.

    Never derived from client input (DoR-A) -- callers must not accept a
    ``sojourner_id`` from request bodies/headers/query params.
    """
    return request.app.state.sojourner_id  # type: ignore[no-any-return]


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
    try:
        return await asyncio.to_thread(fn, *args, **kwargs)
    finally:
        lock.release()


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
