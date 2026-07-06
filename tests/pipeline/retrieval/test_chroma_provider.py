"""Integration tests for ChromaRetrievalMemoryProvider.

CRD Issue 18 / ADR-018 D1 (mandatory story_id query gate / cross-story
leakage) and D5 (inclusive threshold boundary).
"""

from __future__ import annotations

import math
from pathlib import Path
from uuid import uuid4

from afterworlds.pipeline.retrieval.chroma_provider import ChromaRetrievalMemoryProvider
from afterworlds.pipeline.retrieval.client import build_isolated_test_chroma_client
from afterworlds.pipeline.retrieval.config import RetrievalMemoryConfig
from afterworlds.pipeline.retrieval.embedding import DeterministicFakeEmbeddingFunction
from afterworlds.pipeline.retrieval.write_service import RetrievalMemoryWriteService


class _ControllableEmbeddingFunction:
    """Maps known text strings to exact 2D unit vectors for precise cosine control."""

    def __init__(self, vectors: dict[str, tuple[float, float]]) -> None:
        self._vectors = vectors

    def __call__(self, input: list[str]) -> list[list[float]]:
        return [list(self._vectors[text]) for text in input]

    def embed_query(self, input: list[str]) -> list[list[float]]:
        return self(input)

    def name(self) -> str:
        return "controllable-test-embedding"

    def is_legacy(self) -> bool:
        return True


def _unit_vector_at_similarity(similarity: float) -> tuple[float, float]:
    """Return a unit vector whose cosine similarity to (1, 0) is *similarity*."""
    return (similarity, math.sqrt(max(0.0, 1.0 - similarity**2)))


class TestMandatoryStoryIdFilter:
    def test_cross_story_leakage_never_occurs(self, tmp_path: Path) -> None:
        client = build_isolated_test_chroma_client(str(tmp_path))
        config = RetrievalMemoryConfig(minimum_similarity_threshold=0.0, top_k=10)
        ef = DeterministicFakeEmbeddingFunction()
        write_service = RetrievalMemoryWriteService(client, config, ef)
        provider = ChromaRetrievalMemoryProvider(client, config, ef)

        story_a, story_b = uuid4(), uuid4()
        # Identical/overlapping content across both stories.
        write_service.ingest_turn(
            story_a, uuid4(), None, "rpg", "The dragon roars overhead.", "t1"
        )
        write_service.ingest_turn(
            story_b, uuid4(), None, "rpg", "The dragon roars overhead.", "t2"
        )

        result_a = provider.retrieve(story_a, "The dragon roars overhead.")
        result_b = provider.retrieve(story_b, "The dragon roars overhead.")

        assert len(result_a.passages) == 1
        assert len(result_b.passages) == 1
        # Every read path is gated by story_id; a query for A never surfaces
        # B's chunk and vice versa, even with byte-identical content.
        assert result_a.passages[0] == "The dragon roars overhead."
        assert result_b.passages[0] == "The dragon roars overhead."

    def test_query_for_story_with_no_chunks_is_empty(self, tmp_path: Path) -> None:
        client = build_isolated_test_chroma_client(str(tmp_path))
        config = RetrievalMemoryConfig()
        ef = DeterministicFakeEmbeddingFunction()
        write_service = RetrievalMemoryWriteService(client, config, ef)
        provider = ChromaRetrievalMemoryProvider(client, config, ef)

        story_a, story_b = uuid4(), uuid4()
        write_service.ingest_turn(story_a, uuid4(), None, "rpg", "Some prose.", "t1")

        result = provider.retrieve(story_b, "Some prose.")
        assert result.passages == ()

    def test_empty_query_returns_empty_payload(self, tmp_path: Path) -> None:
        client = build_isolated_test_chroma_client(str(tmp_path))
        config = RetrievalMemoryConfig()
        provider = ChromaRetrievalMemoryProvider(
            client, config, DeterministicFakeEmbeddingFunction()
        )
        result = provider.retrieve(uuid4(), "")
        assert result.passages == ()


class TestThresholdBoundary:
    def test_below_threshold_excluded_and_at_threshold_included(
        self, tmp_path: Path
    ) -> None:
        """D5: must assert both the below-threshold exclusion AND the
        exact-boundary inclusion — "above survives" alone is insufficient."""
        threshold = 0.6
        query_text = "query"
        at_threshold_text = "at_threshold_chunk"
        below_threshold_text = "below_threshold_chunk"

        vectors = {
            query_text: (1.0, 0.0),
            at_threshold_text: _unit_vector_at_similarity(threshold),
            below_threshold_text: _unit_vector_at_similarity(threshold - 0.2),
        }
        ef = _ControllableEmbeddingFunction(vectors)

        client = build_isolated_test_chroma_client(str(tmp_path))
        config = RetrievalMemoryConfig(minimum_similarity_threshold=threshold, top_k=10)
        write_service = RetrievalMemoryWriteService(client, config, ef)
        provider = ChromaRetrievalMemoryProvider(client, config, ef)

        story_id = uuid4()
        write_service.ingest_turn(
            story_id, uuid4(), None, "rpg", at_threshold_text, "t1"
        )
        write_service.ingest_turn(
            story_id, uuid4(), None, "rpg", below_threshold_text, "t2"
        )

        result = provider.retrieve(story_id, query_text)

        assert at_threshold_text in result.passages
        assert below_threshold_text not in result.passages
