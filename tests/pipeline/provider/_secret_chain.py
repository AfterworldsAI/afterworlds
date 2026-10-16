"""Exception-chain secrecy check shared by the CRD Issue 20 credential tests."""

from __future__ import annotations


def assert_chain_free_of(exc: BaseException, *secrets: str) -> None:
    """Walk ``__cause__`` and ``__context__`` recursively -- regardless of
    ``__suppress_context__`` -- and fail if any linked exception's message or
    args mention a secret."""
    seen: set[int] = set()
    pending: list[BaseException | None] = [exc]
    while pending:
        current = pending.pop()
        if current is None or id(current) in seen:
            continue
        seen.add(id(current))
        text = f"{current!s} {current.args!r}"
        for secret in secrets:
            assert secret not in text, f"{type(current).__name__} carries a secret"
        pending += [current.__cause__, current.__context__]
