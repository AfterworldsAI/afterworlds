"""Chroma collection access helpers shared by write and query paths.

CRD Issue 18 / ADR-018 D1. One shared ``story_memory`` collection across all
stories (mandatory ``story_id`` metadata filter enforced by every caller —
see ``eligibility.py`` and the query/write services, never bypassed here).
"""

from __future__ import annotations

from chromadb.api import ClientAPI
from chromadb.api.models.Collection import Collection

from afterworlds.models.retrieval import STORY_MEMORY_COLLECTION_NAME
from afterworlds.pipeline.retrieval.config import RetrievalMemoryConfig
from afterworlds.pipeline.retrieval.embedding import (
    RetrievalEmbeddingFunction,
    resolve_default_embedding_function,
)


def get_story_memory_collection(
    client: ClientAPI,
    config: RetrievalMemoryConfig,
    embedding_function: RetrievalEmbeddingFunction | None = None,
) -> Collection:
    """Return (creating if needed) the single shared story_memory collection.

    The distance metric is set once at creation time via collection metadata
    (ADR-018 D5) and is a no-op on subsequent calls once the collection
    exists (Chroma ignores ``metadata=`` on an already-created collection).
    """
    ef = embedding_function or resolve_default_embedding_function()
    return client.get_or_create_collection(
        name=STORY_MEMORY_COLLECTION_NAME,
        metadata={"hnsw:space": config.distance_metric},
        embedding_function=ef,  # type: ignore[arg-type]
    )


def get_rules_corpus_collection(
    client: ClientAPI,
    collection_name: str,
    config: RetrievalMemoryConfig,
    embedding_function: RetrievalEmbeddingFunction | None = None,
) -> Collection:
    """Return (creating if needed) a per-Rules-Package rules_corpus collection."""
    ef = embedding_function or resolve_default_embedding_function()
    return client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": config.distance_metric},
        embedding_function=ef,  # type: ignore[arg-type]
    )
