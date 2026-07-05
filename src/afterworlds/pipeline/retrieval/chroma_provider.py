"""ChromaRetrievalMemoryProvider — CRD Issue 18 / ADR-018 D1/D5.

Implements ``services.context_builder.RetrievalMemoryProvider`` (the
existing Issue 8 protocol seam — shape unchanged per ADR-018 D8). Every
query is gated by a mandatory ``story_id`` metadata filter (D1); results are
normalized to a similarity score and filtered by the configured inclusive
threshold (D5) before being wrapped into the existing typed
``RetrievalMemoryPayload``.
"""

from __future__ import annotations

from uuid import UUID

from chromadb.api import ClientAPI

from afterworlds.models.context import RetrievalMemoryPayload
from afterworlds.pipeline.retrieval.collections import get_story_memory_collection
from afterworlds.pipeline.retrieval.config import RetrievalMemoryConfig
from afterworlds.pipeline.retrieval.embedding import RetrievalEmbeddingFunction
from afterworlds.pipeline.retrieval.scoring import normalize_similarity


class ChromaRetrievalMemoryProvider:
    """Chroma-backed RetrievalMemoryProvider for the shared story_memory collection."""

    def __init__(
        self,
        client: ClientAPI,
        config: RetrievalMemoryConfig,
        embedding_function: RetrievalEmbeddingFunction | None = None,
    ) -> None:
        self._client = client
        self._config = config
        self._embedding_function = embedding_function

    def retrieve(self, story_id: UUID, query: str) -> RetrievalMemoryPayload:
        if not query:
            return RetrievalMemoryPayload()

        collection = get_story_memory_collection(
            self._client, self._config, self._embedding_function
        )
        count = collection.count()
        if count == 0:
            return RetrievalMemoryPayload()

        n_results = min(self._config.top_k, count)
        results = collection.query(
            query_texts=[query],
            n_results=n_results,
            # Mandatory story_id filter (ADR-018 D1) — the single query gate
            # every read path traverses. Never omitted, never bypassed.
            where={"story_id": str(story_id)},
        )

        documents_lists = results.get("documents") or []
        distances_lists = results.get("distances") or []
        if not documents_lists or not documents_lists[0]:
            return RetrievalMemoryPayload()

        documents = documents_lists[0]
        distances = distances_lists[0] if distances_lists else []

        passages: list[str] = []
        for i, document in enumerate(documents):
            distance = distances[i] if i < len(distances) else 1.0
            similarity = normalize_similarity(
                float(distance), self._config.distance_metric
            )
            if similarity >= self._config.minimum_similarity_threshold:
                passages.append(str(document))

        return RetrievalMemoryPayload(passages=tuple(passages))
