"""Account-to-Story authorization -- prerequisite #205 §2/§5 (ADR-021 D8).

One policy, consulted by the API Story guard, the owning-service seams
(orchestrator, RPG actions, Retrieval Memory) and delayed work. A local
deployment authorizes every Story to its single local owner (unchanged CRD
Issue 19 behavior); a remote one requires an active ownership row for an
active account and no active deletion suppression.

Remote effects run under a trusted :class:`DelayedWorkScope` carried in a
context variable (:func:`work_scope`): set by the request after the actor's
session is revalidated, or explicitly by a job. Owning-service seams refuse a
remote call with no scope or another account's scope. :class:`AccountFence`
orders effects against closure and suppression inside the one writer process
(ADR-021 D6): requests hold an account's fence shared for their whole
handler; closure and suppression take it exclusive, so no effect of a request
admitted before them can land after they complete.
"""

from __future__ import annotations

import threading
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, replace
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlalchemy.orm import Session, sessionmaker

from afterworlds.persistence.orm.ownership import AccountResourceORM
from afterworlds.remote.control_store import iso
from afterworlds.remote.identity import Actor, ActorKind, IdentityService
from afterworlds.remote.storage import is_suppressed

STORY = "story"


class StoryAccessDenied(Exception):
    """The Story is not accessible to this caller/job (no disclosure why)."""


@dataclass(frozen=True)
class DelayedWorkScope:
    """Trusted scope carried by a request or job and rechecked at each effect.

    ``story_id`` is None for an account-level request scope until the Story
    guard binds the request to one Story."""

    account_id: UUID
    story_id: UUID | None
    operation: str


_SCOPE: ContextVar[DelayedWorkScope | None] = ContextVar(
    "afterworlds_work_scope", default=None
)


def current_scope() -> DelayedWorkScope | None:
    return _SCOPE.get()


@contextmanager
def work_scope(scope: DelayedWorkScope) -> Iterator[DelayedWorkScope]:
    """Run the block (and threads it starts via ``asyncio.to_thread`` or
    anyio, which copy the context) under *scope*."""
    token = _SCOPE.set(scope)
    try:
        yield scope
    finally:
        _SCOPE.reset(token)


def bind_story(story_id: UUID) -> None:
    """Narrow the current request scope to one Story (request lifetime)."""
    scope = _SCOPE.get()
    if scope is not None:
        _SCOPE.set(replace(scope, story_id=story_id))


class FenceBusy(Exception):
    """An exclusive account operation holds, or could not obtain, the fence."""


class AccountFence:
    """Per-account shared/exclusive gate for the single writer process."""

    def __init__(self) -> None:
        self._cond = threading.Condition()
        self._shared: dict[UUID, int] = {}
        self._exclusive: set[UUID] = set()

    @contextmanager
    def shared(self, account_id: UUID) -> Iterator[None]:
        with self._cond:
            if account_id in self._exclusive:
                raise FenceBusy(str(account_id))
            self._shared[account_id] = self._shared.get(account_id, 0) + 1
        try:
            yield
        finally:
            with self._cond:
                self._shared[account_id] -= 1
                self._cond.notify_all()

    @contextmanager
    def exclusive(self, account_id: UUID, *, timeout: float) -> Iterator[None]:
        """Admit no new shared holder, wait (bounded) for current ones to
        finish, then run the block. On timeout nothing is changed."""
        with self._cond:
            if account_id in self._exclusive:
                raise FenceBusy(str(account_id))
            self._exclusive.add(account_id)
            drained = self._cond.wait_for(
                lambda: self._shared.get(account_id, 0) == 0, timeout
            )
            if not drained:
                self._exclusive.discard(account_id)
                self._cond.notify_all()
                raise FenceBusy(str(account_id))
        try:
            yield
        finally:
            with self._cond:
                self._exclusive.discard(account_id)
                self._cond.notify_all()


def record_story_owner(
    session: Session, account_id: UUID, story_id: UUID, *, now: datetime
) -> None:
    """Add the ownership row in the caller's transaction (commits with the Story)."""
    session.add(
        AccountResourceORM(
            mapping_id=str(uuid4()),
            account_id=str(account_id),
            resource_type=STORY,
            resource_id=str(story_id),
            ownership_revision=1,
            created_at=iso(now),
            source_operation_ref=str(uuid4()),
        )
    )


def story_owner(session: Session, story_id: UUID) -> str | None:
    return session.scalar(
        sa.select(AccountResourceORM.account_id).where(
            AccountResourceORM.resource_type == STORY,
            AccountResourceORM.resource_id == str(story_id),
            AccountResourceORM.retired_at.is_(None),
        )
    )


def owned_story_ids(session: Session, account_id: UUID) -> list[str]:
    """Every Story the account actively owns (independent of Story rows)."""
    return list(
        session.scalars(
            sa.select(AccountResourceORM.resource_id).where(
                AccountResourceORM.account_id == str(account_id),
                AccountResourceORM.resource_type == STORY,
                AccountResourceORM.retired_at.is_(None),
            )
        )
    )


class AccessPolicy:
    """Remote ownership policy; ``identity is None`` means a local deployment."""

    def __init__(
        self,
        identity: IdentityService | None = None,
        control: sessionmaker[Session] | None = None,
    ) -> None:
        self._identity = identity
        self._control = control

    @property
    def remote(self) -> bool:
        return self._identity is not None

    def actor_may_access(self, session: Session, actor: Actor, story_id: UUID) -> bool:
        if actor.kind is ActorKind.LOCAL:
            return not self.remote
        if actor.kind is not ActorKind.SOJOURNER:
            return False
        owner = story_owner(session, story_id)
        return owner == str(actor.account_id) and self._servable(owner, story_id)

    def check_delayed_work(self, session: Session, scope: DelayedWorkScope) -> None:
        """Recheck a trusted scope at the moment of an effect."""
        if not self.remote:
            return
        if scope.story_id is None:
            raise StoryAccessDenied(scope.operation)
        owner = story_owner(session, scope.story_id)
        if owner != str(scope.account_id) or not self._servable(owner, scope.story_id):
            raise StoryAccessDenied(scope.operation)

    def check_current(self, session: Session, story_id: UUID) -> None:
        """Owning-service check: the current trusted scope must cover
        *story_id* and still hold. A remote call with no scope, another
        account's scope or another Story's scope is refused."""
        if not self.remote:
            return
        scope = current_scope()
        if scope is None or scope.story_id not in (None, story_id):
            raise StoryAccessDenied("unscoped")
        self.check_delayed_work(session, replace(scope, story_id=story_id))

    def _servable(self, owner: str, story_id: UUID) -> bool:
        assert self._identity is not None and self._control is not None
        if not self._identity.active_account_ids({owner}):
            return False
        return not is_suppressed(
            self._control, story_id=str(story_id), account_id=owner
        )


class ScopedSeam:
    """Owning-service seam for a remote deployment (#205 §1/§2).

    Wraps a service whose named entry points take ``story_id`` first: each
    call must run under a current trusted scope that covers the Story (and,
    when passed, the same ``sojourner_id``), rechecked at the call. Direct,
    unscoped or cross-account calls raise :class:`StoryAccessDenied` before
    the service runs. Other attributes pass through unchanged.
    """

    def __init__(
        self,
        inner: object,
        policy: AccessPolicy,
        session_factory: sessionmaker[Session],
        methods: frozenset[str],
    ) -> None:
        self._inner = inner
        self._policy = policy
        self._factory = session_factory
        self._methods = methods

    def __getattr__(self, name: str) -> Any:
        attr = getattr(self._inner, name)
        if name not in self._methods:
            return attr

        def guarded(*args: Any, **kwargs: Any) -> Any:
            story_id = kwargs.get("story_id", args[0] if args else None)
            if not isinstance(story_id, UUID):
                raise StoryAccessDenied(name)
            scope = current_scope()
            sojourner = kwargs.get("sojourner_id")
            if scope is not None and sojourner not in (None, scope.account_id):
                raise StoryAccessDenied(name)
            with self._factory() as session:
                self._policy.check_current(session, story_id)
            return attr(*args, **kwargs)

        return guarded
