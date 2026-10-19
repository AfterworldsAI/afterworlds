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

import inspect
from collections.abc import Iterable, Iterator
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
from afterworlds.remote.fence import AccountFence, FenceBusy
from afterworlds.remote.identity import Actor, ActorKind, IdentityService
from afterworlds.remote.storage import (
    active_suppressions,
    is_suppressed,
    record_suppression,
)

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
    def fence(self) -> AccountFence:
        """The process's account fence (the identity service owns it)."""
        assert self._identity is not None
        return self._identity.fence

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

    def account_suppressed(self, account_id: UUID) -> bool:
        """An account-scope deletion suppression is in force for *account_id*:
        no new account-owned effect may be admitted."""
        if not self.remote:
            return False
        assert self._control is not None
        return any(
            sup.scope == "account" and sup.subject_ref == str(account_id)
            for sup in active_suppressions(self._control)
        )

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
        fence: AccountFence,
    ) -> None:
        self._inner = inner
        self._policy = policy
        self._factory = session_factory
        self._methods = methods
        self._fence = fence

    def __getattr__(self, name: str) -> Any:
        attr = getattr(self._inner, name)
        if name not in self._methods:
            return attr
        signature = inspect.signature(attr)

        def guarded(*args: Any, **kwargs: Any) -> Any:
            # Bind exactly as Python will, so positional and keyword calling
            # conventions are checked identically.
            try:
                bound = signature.bind(*args, **kwargs)
            except TypeError:
                raise StoryAccessDenied(name) from None
            story_id = bound.arguments.get("story_id")
            scope = current_scope()
            if not isinstance(story_id, UUID) or scope is None:
                raise StoryAccessDenied(name)
            sojourner = bound.arguments.get("sojourner_id", scope.account_id)
            if sojourner != scope.account_id:
                raise StoryAccessDenied(name)
            # The fence is held for the call's whole lifetime: closure or
            # suppression of the account waits for it (or refuses it).
            try:
                with self._fence.held(scope.account_id):
                    with self._factory() as session:
                        self._policy.check_current(session, story_id)
                    return attr(*args, **kwargs)
            except FenceBusy:
                raise StoryAccessDenied(name) from None

        return guarded


def record_suppression_fenced(
    fence: AccountFence,
    control: sessionmaker[Session],
    *,
    account_id: UUID,
    story_refs: Iterable[str],
    request_id: str,
    scope: str,
    effective_boundary_at: datetime,
    now: datetime,
    timeout: float,
) -> str:
    """The supported way for CRD Issue 22 to record a deletion suppression.

    Holds the owning account's fence exclusive while recording, so every
    request admitted earlier has finished and no later one is admitted until
    the instruction is durable: no effect lands after this returns. Raises
    :class:`FenceBusy` (nothing recorded) if in-flight work does not finish
    within *timeout*."""
    with fence.exclusive(account_id, timeout=timeout):
        return record_suppression(
            control,
            subject_ref=str(account_id),
            story_refs=story_refs,
            request_id=request_id,
            scope=scope,
            effective_boundary_at=effective_boundary_at,
            now=now,
        )
