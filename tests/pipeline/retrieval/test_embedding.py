"""Tests for the embedding function seam — CRD Issue 18 / ADR-018 D4.

Codex review (PR #119): the real local ONNX MiniLM embedding function must
be the production default; the deterministic fake must only ever be used
via explicit caller injection, never selected implicitly on omission.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from afterworlds.pipeline.retrieval import collections as collections_module
from afterworlds.pipeline.retrieval.client import build_isolated_test_chroma_client
from afterworlds.pipeline.retrieval.config import RetrievalMemoryConfig
from afterworlds.pipeline.retrieval.embedding import (
    DeterministicFakeEmbeddingFunction,
    RetrievalEmbeddingUnavailableError,
    resolve_default_embedding_function,
)


class _StubRealEmbeddingFunction:
    """Stands in for chromadb's real DefaultEmbeddingFunction in tests, so
    resolution can be proven without a network call / model download.

    Fully duck-types ``RetrievalEmbeddingFunction`` so chromadb's own
    collection-creation validation accepts it like any real function.
    """

    def __call__(self, input: list[str]) -> list[list[float]]:
        return [[0.0, 1.0] for _ in input]

    def embed_query(self, input: list[str]) -> list[list[float]]:
        return self(input)

    def name(self) -> str:
        return "stub-real-embedding-function"

    def is_legacy(self) -> bool:
        return True


class TestResolveDefaultEmbeddingFunction:
    def test_omitted_embedding_function_resolves_to_real_not_fake(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Omitting an embedding function must resolve to the real ADR-018
        D4 default, never the deterministic fake."""
        monkeypatch.setattr(
            "chromadb.utils.embedding_functions.DefaultEmbeddingFunction",
            _StubRealEmbeddingFunction,
        )

        ef = resolve_default_embedding_function()

        assert isinstance(ef, _StubRealEmbeddingFunction)
        assert not isinstance(ef, DeterministicFakeEmbeddingFunction)

    def test_real_embedding_unavailable_raises_typed_error_not_fake_fallback(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """If the real embedding function cannot initialize, resolution must
        fail loudly with a typed error — never silently fall back to the
        deterministic fake in production/default code."""

        def _raise(*args: object, **kwargs: object) -> None:
            raise RuntimeError("synthetic ONNX model load failure")

        monkeypatch.setattr(
            "chromadb.utils.embedding_functions.DefaultEmbeddingFunction", _raise
        )

        with pytest.raises(RetrievalEmbeddingUnavailableError):
            resolve_default_embedding_function()

    def test_explicit_fake_injection_still_runs_fully_offline(self) -> None:
        """Tests/offline fixtures must still be able to opt into the fake by
        constructing it explicitly — no network, no model download."""
        fake = DeterministicFakeEmbeddingFunction()

        vectors = fake(["some prose"])

        assert len(vectors) == 1
        assert len(vectors[0]) > 0
        # Deterministic: identical input always yields identical output.
        assert fake(["some prose"]) == vectors


class TestCollectionHelpersNeverSilentlyFake:
    """Sibling audit: no shared collection helper may substitute the fake
    when the caller omits an embedding function — every fake usage must be
    an explicit injection at the call site, not an implicit default here."""

    def test_story_memory_collection_uses_resolved_default_when_omitted(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        calls: list[object] = []
        real_resolve = resolve_default_embedding_function

        def _spy_resolve() -> object:
            calls.append(object())
            monkeypatch.setattr(
                "chromadb.utils.embedding_functions.DefaultEmbeddingFunction",
                _StubRealEmbeddingFunction,
            )
            return real_resolve()

        monkeypatch.setattr(
            collections_module, "resolve_default_embedding_function", _spy_resolve
        )
        client = build_isolated_test_chroma_client(str(tmp_path))
        config = RetrievalMemoryConfig()

        collections_module.get_story_memory_collection(client, config)

        assert len(calls) == 1

    def test_rules_corpus_collection_uses_resolved_default_when_omitted(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        calls: list[object] = []
        real_resolve = resolve_default_embedding_function

        def _spy_resolve() -> object:
            calls.append(object())
            monkeypatch.setattr(
                "chromadb.utils.embedding_functions.DefaultEmbeddingFunction",
                _StubRealEmbeddingFunction,
            )
            return real_resolve()

        monkeypatch.setattr(
            collections_module, "resolve_default_embedding_function", _spy_resolve
        )
        client = build_isolated_test_chroma_client(str(tmp_path))
        config = RetrievalMemoryConfig()

        collections_module.get_rules_corpus_collection(
            client, "rules_corpus_test", config
        )

        assert len(calls) == 1
