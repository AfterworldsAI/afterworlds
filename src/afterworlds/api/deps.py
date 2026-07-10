"""Shared FastAPI dependencies — DB session and derived Sojourner identity.

Single choke points (Binding Decision 12): every route obtains its session
and sojourner id through these, never by constructing their own.
"""

from __future__ import annotations

import asyncio
from collections.abc import Iterator
from uuid import UUID

from fastapi import Request
from sqlalchemy.orm import Session

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
