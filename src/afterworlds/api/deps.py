"""Shared FastAPI dependencies — DB session and derived Sojourner identity.

Single choke points (Binding Decision 12): every route obtains its session
and sojourner id through these, never by constructing their own.
"""

from __future__ import annotations

from collections.abc import Iterator
from uuid import UUID

from fastapi import Request
from sqlalchemy.orm import Session

from afterworlds.persistence.crud.identity import get_or_create_sojourner_identity


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
