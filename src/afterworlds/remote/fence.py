"""Per-account effect fence for the single writer process (ADR-021 D6).

Requests and owning-service calls hold an account's fence *shared* for the
whole lifetime of their effects; closure and deletion suppression take it
*exclusive* with a bounded wait. No effect admitted before an exclusive
operation can land after that operation returns, and none is admitted while
it runs. A holder records itself in a context variable, so a nested call in
the same request or job does not acquire the fence again (re-entrancy).
"""

from __future__ import annotations

import threading
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from uuid import UUID

_HELD: ContextVar[frozenset[UUID]] = ContextVar(
    "afterworlds_fence_held", default=frozenset()
)


def fence_held(account_id: UUID) -> bool:
    """Whether the current context already holds *account_id*'s fence."""
    return account_id in _HELD.get()


def mark_fence_held(account_id: UUID) -> None:
    """Record, for the rest of the current context (a request), that it holds
    *account_id*'s fence. Only a holder of :meth:`AccountFence.shared` may
    call this."""
    _HELD.set(_HELD.get() | {account_id})


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

    @contextmanager
    def held(self, account_id: UUID) -> Iterator[None]:
        """Hold the fence shared for the block unless this context already
        does; marks it held for nested calls within the block."""
        if fence_held(account_id):
            yield
            return
        with self.shared(account_id):
            token = _HELD.set(_HELD.get() | {account_id})
            try:
                yield
            finally:
                _HELD.reset(token)
