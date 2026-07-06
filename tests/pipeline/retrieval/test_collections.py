"""Tests for the Chroma collection-access helpers — CRD Issue 18 / ADR-018 D4.

Codex review (PR #119) round 3: an existing persistent collection's
recorded embedding_model_id must be checked against config before reuse —
mixed-model collections are a defect (D4), and the collection-level
metadata dict is silently ignored by Chroma on an already-created
collection, so this check must be explicit, not inferred from the
``metadata=`` kwarg alone.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from afterworlds.pipeline.retrieval.client import build_isolated_test_chroma_client
from afterworlds.pipeline.retrieval.collections import (
    RetrievalCollectionReindexRequiredError,
    get_rules_corpus_collection,
    get_story_memory_collection,
)
from afterworlds.pipeline.retrieval.config import RetrievalMemoryConfig
from afterworlds.pipeline.retrieval.embedding import DeterministicFakeEmbeddingFunction


class TestStoryMemoryCollectionEmbeddingModelGuard:
    def test_new_collection_stores_embedding_model_id(self, tmp_path: Path) -> None:
        client = build_isolated_test_chroma_client(str(tmp_path))
        config = RetrievalMemoryConfig(embedding_model_id="model-a")

        collection = get_story_memory_collection(
            client, config, DeterministicFakeEmbeddingFunction()
        )

        assert collection.metadata is not None
        assert collection.metadata.get("embedding_model_id") == "model-a"

    def test_matching_existing_collection_reuses_cleanly(self, tmp_path: Path) -> None:
        client = build_isolated_test_chroma_client(str(tmp_path))
        config = RetrievalMemoryConfig(embedding_model_id="model-a")
        ef = DeterministicFakeEmbeddingFunction()

        first = get_story_memory_collection(client, config, ef)
        second = get_story_memory_collection(client, config, ef)

        assert first.name == second.name
        assert second.metadata.get("embedding_model_id") == "model-a"

    def test_mismatched_existing_collection_raises(self, tmp_path: Path) -> None:
        client = build_isolated_test_chroma_client(str(tmp_path))
        ef = DeterministicFakeEmbeddingFunction()
        get_story_memory_collection(
            client, RetrievalMemoryConfig(embedding_model_id="model-a"), ef
        )

        with pytest.raises(RetrievalCollectionReindexRequiredError, match="reindex"):
            get_story_memory_collection(
                client, RetrievalMemoryConfig(embedding_model_id="model-b"), ef
            )

    def test_legacy_collection_missing_embedding_model_id_raises(
        self, tmp_path: Path
    ) -> None:
        """A collection created before this guard existed has no
        embedding_model_id key at all -- ADR-018 does not permit silently
        assuming that shape is compatible with the configured model."""
        client = build_isolated_test_chroma_client(str(tmp_path))
        ef = DeterministicFakeEmbeddingFunction()
        # Simulate a pre-guard collection: only hnsw:space, no
        # embedding_model_id, created directly against the raw client
        # (bypassing get_story_memory_collection entirely).
        client.get_or_create_collection(
            name="story_memory",
            metadata={"hnsw:space": "cosine"},
            embedding_function=ef,  # type: ignore[arg-type]
        )

        with pytest.raises(RetrievalCollectionReindexRequiredError, match="reindex"):
            get_story_memory_collection(
                client, RetrievalMemoryConfig(embedding_model_id="model-a"), ef
            )


class TestRulesCorpusCollectionEmbeddingModelGuard:
    def test_new_collection_stores_embedding_model_id(self, tmp_path: Path) -> None:
        client = build_isolated_test_chroma_client(str(tmp_path))
        config = RetrievalMemoryConfig(embedding_model_id="model-a")

        collection = get_rules_corpus_collection(
            client, "rules_corpus_test", config, DeterministicFakeEmbeddingFunction()
        )

        assert collection.metadata is not None
        assert collection.metadata.get("embedding_model_id") == "model-a"

    def test_mismatched_existing_collection_raises(self, tmp_path: Path) -> None:
        client = build_isolated_test_chroma_client(str(tmp_path))
        ef = DeterministicFakeEmbeddingFunction()
        get_rules_corpus_collection(
            client,
            "rules_corpus_test",
            RetrievalMemoryConfig(embedding_model_id="model-a"),
            ef,
        )

        with pytest.raises(RetrievalCollectionReindexRequiredError, match="reindex"):
            get_rules_corpus_collection(
                client,
                "rules_corpus_test",
                RetrievalMemoryConfig(embedding_model_id="model-b"),
                ef,
            )

    def test_legacy_collection_missing_embedding_model_id_raises(
        self, tmp_path: Path
    ) -> None:
        client = build_isolated_test_chroma_client(str(tmp_path))
        ef = DeterministicFakeEmbeddingFunction()
        client.get_or_create_collection(
            name="rules_corpus_test",
            metadata={"hnsw:space": "cosine"},
            embedding_function=ef,  # type: ignore[arg-type]
        )

        with pytest.raises(RetrievalCollectionReindexRequiredError, match="reindex"):
            get_rules_corpus_collection(
                client,
                "rules_corpus_test",
                RetrievalMemoryConfig(embedding_model_id="model-a"),
                ef,
            )
