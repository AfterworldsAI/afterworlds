"""Embedding function seam for Retrieval Memory — CRD Issue 18 / ADR-018 D4.

Local deterministic embedding behind an injectable ``EmbeddingFunction`` seam.
No hosted/provider credentials required — BYOK and local-first embed
identically (CLAUDE.md Business invariant: BYOK preserves full pipeline
parity). Real-model CI runs stay behind an opt-in integration flag so the
default test suite never needs network access or a downloaded model.
"""

from __future__ import annotations

import hashlib
import os
from typing import Protocol, runtime_checkable

#: Fixed vector dimensionality for the deterministic fake embedding function.
#: Arbitrary but stable — the value only needs to be internally consistent
#: within one Chroma collection.
_FAKE_EMBEDDING_DIM = 32

#: Opt-in flag gating the real ONNX MiniLM embedding function. Off by
#: default so the standard test suite and CI run fully offline.
REAL_EMBEDDING_FUNCTION_ENV = "AFTERWORLDS_RETRIEVAL_REAL_EMBEDDINGS"


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
    Never used in production — see ``resolve_default_embedding_function``.
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

    Defaults to the deterministic fake unless the opt-in real-embeddings
    integration flag is set, matching the existing pattern for other
    provider-backed integration tests in this repo.

    Security note (ADR-018 CVE-2026-45829 resolution): whichever function is
    returned, callers must construct the Chroma client as an embedded
    ``PersistentClient``/``EphemeralClient`` — never ``HttpClient`` — and
    must never set ``trust_remote_code=True``. See
    ``pipeline/retrieval/config.py`` and this PR's Architecture Notes.
    """
    if os.environ.get(REAL_EMBEDDING_FUNCTION_ENV, "").lower() in ("1", "true", "yes"):
        from chromadb.utils.embedding_functions import (  # noqa: PLC0415
            DefaultEmbeddingFunction,
        )

        return DefaultEmbeddingFunction()  # type: ignore[return-value]
    return DeterministicFakeEmbeddingFunction()


def content_hash(text: str) -> str:
    """Stable content hash used in StoryMemoryChunkMetadata.content_hash."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
