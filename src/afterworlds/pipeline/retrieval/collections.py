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

#: Collection-metadata key storing the embedding model a collection was
#: created for (ADR-018 D2/D4). Distinct from the per-chunk
#: ``embedding_model_id`` field on ``StoryMemoryChunkMetadata`` /
#: ``RulesCorpusChunkMetadata`` — this is the collection-level identity
#: check that lets ``_require_matching_embedding_model`` detect drift
#: *before* any chunk is written or queried.
_EMBEDDING_MODEL_ID_METADATA_KEY = "embedding_model_id"


class RetrievalCollectionReindexRequiredError(RuntimeError):
    """Raised when an existing Chroma collection's recorded embedding model
    does not match the configured one (ADR-018 D4: a model change forces a
    full reindex; mixed-model collections are a defect).

    This includes a collection created before this guard existed (no
    ``embedding_model_id`` in its metadata at all) — ADR-018 does not permit
    silently assuming a legacy collection is compatible, so a missing key is
    treated the same as a mismatch. Callers must run the manual reindex
    command (`scripts/retrieval_backfill.py --mode reindex`) rather than
    have this helper auto-wipe or auto-reindex on their behalf.
    """


def _require_matching_embedding_model(
    collection: Collection, config: RetrievalMemoryConfig, collection_name: str
) -> None:
    existing = (
        collection.metadata.get(_EMBEDDING_MODEL_ID_METADATA_KEY)
        if collection.metadata
        else None
    )
    if existing != config.embedding_model_id:
        raise RetrievalCollectionReindexRequiredError(
            f"Collection {collection_name!r} was created with embedding_model_id "
            f"{existing!r} but the configured embedding_model_id is "
            f"{config.embedding_model_id!r}. Mixed-model collections are a "
            "defect (ADR-018 D4) — run a full reindex for this "
            "story/rules-package before writing or querying again."
        )


def get_story_memory_collection(
    client: ClientAPI,
    config: RetrievalMemoryConfig,
    embedding_function: RetrievalEmbeddingFunction | None = None,
) -> Collection:
    """Return (creating if needed) the single shared story_memory collection.

    The distance metric and ``embedding_model_id`` are set once at creation
    time via collection metadata (ADR-018 D4/D5) and are a no-op on
    subsequent calls once the collection exists (Chroma ignores
    ``metadata=`` on an already-created collection) — which is exactly why
    ``embedding_model_id`` must be checked explicitly here rather than
    trusted to have been (re)applied.

    Raises:
        RetrievalCollectionReindexRequiredError: if an existing collection's
            recorded ``embedding_model_id`` does not match (or is absent,
            i.e. a pre-guard legacy collection) — never silently reused,
            never auto-wiped, never auto-reindexed.
    """
    ef = embedding_function or resolve_default_embedding_function()
    collection = client.get_or_create_collection(
        name=STORY_MEMORY_COLLECTION_NAME,
        metadata={
            "hnsw:space": config.distance_metric,
            _EMBEDDING_MODEL_ID_METADATA_KEY: config.embedding_model_id,
        },
        embedding_function=ef,  # type: ignore[arg-type]
    )
    _require_matching_embedding_model(collection, config, STORY_MEMORY_COLLECTION_NAME)
    return collection


def get_rules_corpus_collection(
    client: ClientAPI,
    collection_name: str,
    config: RetrievalMemoryConfig,
    embedding_function: RetrievalEmbeddingFunction | None = None,
) -> Collection:
    """Return (creating if needed) a per-Rules-Package rules_corpus collection.

    See :func:`get_story_memory_collection` for the ``embedding_model_id``
    guard rationale — applies identically here (Codex review, PR #119).

    Raises:
        RetrievalCollectionReindexRequiredError: if an existing collection's
            recorded ``embedding_model_id`` does not match (or is absent).
    """
    ef = embedding_function or resolve_default_embedding_function()
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={
            "hnsw:space": config.distance_metric,
            _EMBEDDING_MODEL_ID_METADATA_KEY: config.embedding_model_id,
        },
        embedding_function=ef,  # type: ignore[arg-type]
    )
    _require_matching_embedding_model(collection, config, collection_name)
    return collection
