"""Embedding function seam for Retrieval Memory — CRD Issue 18 / ADR-018 D4.

Local deterministic embedding (ChromaDB's default ONNX MiniLM path) behind an
injectable ``EmbeddingFunction`` seam. No hosted/provider credentials
required — BYOK and local-first embed identically (CLAUDE.md Business
invariant: BYOK preserves full pipeline parity). The real embedding function
is the production default; the deterministic fake below exists solely for
tests/CI to run offline and must always be injected explicitly by the
caller — it is never selected implicitly by omission.
"""

from __future__ import annotations

import hashlib
from typing import Protocol, runtime_checkable

#: Fixed vector dimensionality for the deterministic fake embedding function.
#: Arbitrary but stable — the value only needs to be internally consistent
#: within one Chroma collection.
_FAKE_EMBEDDING_DIM = 32


class RetrievalEmbeddingUnavailableError(RuntimeError):
    """Raised when the real default embedding function cannot initialize.

    Production/default code must fail clearly here rather than silently
    substituting the deterministic fake — a fake-embedding fallback would
    mean indexing/querying arbitrary hash vectors instead of semantic
    embeddings (ADR-018 D4).
    """


@runtime_checkable
class RetrievalEmbeddingFunction(Protocol):
    """Narrow protocol Afterworlds code depends on (subset of chromadb's)."""

    def __call__(self, input: list[str]) -> list[list[float]]: ...

    def name(self) -> str: ...

    def embed_query(self, input: list[str]) -> list[list[float]]: ...


class DeterministicFakeEmbeddingFunction:
    """Deterministic, dependency-free embedding function for tests and CI.

    Hashes each input string to a fixed-dimension float vector. Same input
    always produces the same vector; no model download, no network access.
    Never selected by default — callers (tests, offline fixtures) must
    construct and inject this explicitly. See
    ``resolve_default_embedding_function`` for the production default.
    """

    def __call__(self, input: list[str]) -> list[list[float]]:
        return [self._embed_one(text) for text in input]

    def _embed_one(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        # Repeat/trim the digest to the fixed dimension, unpack as floats
        # scaled into [-1, 1] so cosine distance is meaningful.
        raw = (digest * ((_FAKE_EMBEDDING_DIM // len(digest)) + 1))[
            :_FAKE_EMBEDDING_DIM
        ]
        return [((b / 255.0) * 2.0) - 1.0 for b in raw]

    def embed_query(self, input: list[str]) -> list[list[float]]:
        return self(input)

    def name(self) -> str:
        return "afterworlds-deterministic-fake-v1"

    def is_legacy(self) -> bool:
        return True


def resolve_default_embedding_function() -> RetrievalEmbeddingFunction:
    """Return the embedding function to use when none is injected.

    Always the real local ONNX MiniLM default (ADR-018 D4) — this is the
    production default, not an opt-in. The deterministic fake is never
    selected here; tests that need to run offline must construct
    ``DeterministicFakeEmbeddingFunction()`` and inject it explicitly via
    each call site's ``embedding_function`` parameter.

    Security note (ADR-018 CVE-2026-45829 resolution): whichever function is
    returned, callers must construct the Chroma client as an embedded
    ``PersistentClient``/``EphemeralClient`` — never ``HttpClient`` — and
    must never set ``trust_remote_code=True``. See
    ``pipeline/retrieval/config.py`` and this PR's Architecture Notes.

    Raises:
        RetrievalEmbeddingUnavailableError: if the real embedding function
            cannot be constructed (e.g. the optional ONNX model dependency
            failed to initialize). Callers must not fall back to the fake.
    """
    try:
        from chromadb.utils.embedding_functions import (  # noqa: PLC0415
            DefaultEmbeddingFunction,
        )

        return DefaultEmbeddingFunction()  # type: ignore[return-value]
    except Exception as exc:  # noqa: BLE001
        raise RetrievalEmbeddingUnavailableError(
            "Failed to initialize the real default embedding function "
            "(ADR-018 D4 local ONNX MiniLM path). Retrieval Memory requires "
            "a real embedding function in production; inject "
            "DeterministicFakeEmbeddingFunction() explicitly only for "
            "offline tests."
        ) from exc


def content_hash(text: str) -> str:
    """Stable content hash used in StoryMemoryChunkMetadata.content_hash."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
