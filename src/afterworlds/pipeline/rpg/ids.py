"""Identities the adapter mints for effects and instructions — CRD Issue 15b.

Outside an action-resolution sequence every id is a fresh ``uuid4`` (the 15c
behaviour). Inside one, an operation can be computed again on reload or when
the next input arrives, and its pending instruction, decision options and
effects must come out identical each time: ids are then ``uuid5`` over the
operation's namespace and a running ordinal, so the same computation gives
the same ids (:func:`scoped`).
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from uuid import UUID, uuid4, uuid5

_SCOPE: ContextVar[tuple[UUID, list[int]] | None] = ContextVar("rpg_ids", default=None)


def new_uuid() -> UUID:
    scope = _SCOPE.get()
    if scope is None:
        return uuid4()
    namespace, counter = scope
    counter[0] += 1
    return uuid5(namespace, str(counter[0]))


def new_id() -> str:
    return str(new_uuid())


def derived(namespace: UUID, name: str) -> UUID:
    """A stable id for a named thing in a namespace (a step, an instruction)."""
    return uuid5(namespace, name)


@contextmanager
def scoped(namespace: UUID) -> Iterator[None]:
    """Mint deterministic ids under *namespace* for the duration."""
    token = _SCOPE.set((namespace, [0]))
    try:
        yield
    finally:
        _SCOPE.reset(token)


__all__ = ["derived", "new_id", "new_uuid", "scoped"]
