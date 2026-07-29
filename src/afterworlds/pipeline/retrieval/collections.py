"""Chroma collection access helpers shared by write and query paths.

CRD Issue 18 / ADR-018 D1. One shared ``story_memory`` collection across all
stories (mandatory ``story_id`` metadata filter enforced by every caller —
see ``eligibility.py`` and the query/write services, never bypassed here).
"""

from __future__ import annotations

from contextlib import suppress

from chromadb.api import ClientAPI
from chromadb.api.models.Collection import Collection
from chromadb.errors import NotFoundError

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
    if existing == config.embedding_model_id:
        return

    if collection_name == STORY_MEMORY_COLLECTION_NAME:
        # Shared across every story (ADR-018 D1) -- a single story's
        # reindex_story() cannot repair a collection-level mismatch, since
        # other stories' chunks in this same collection are still recorded
        # under the old model. Do not let a caller believe a story-scoped
        # operation fixed this; direct them to the explicit full-collection
        # wipe (Codex review, PR #119).
        guidance = (
            "story_memory is shared across all stories -- a single story's "
            "reindex cannot repair this collection-level mismatch. Wipe and "
            "rebuild the entire collection "
            "(RetrievalMemoryWriteService.wipe_collection(), then backfill "
            "every story) before writing or querying again."
        )
    else:
        guidance = (
            "run a full reindex for this rules package "
            "(RulesCorpusService.reindex_from_sql) before writing or "
            "querying again."
        )
    raise RetrievalCollectionReindexRequiredError(
        f"Collection {collection_name!r} was created with embedding_model_id "
        f"{existing!r} but the configured embedding_model_id is "
        f"{config.embedding_model_id!r}. Mixed-model collections are a "
        f"defect (ADR-018 D4) — {guidance}"
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


def get_existing_story_memory_collection_for_delete(
    client: ClientAPI,
) -> Collection | None:
    """Open the existing ``story_memory`` collection for a metadata-only
    delete operation, bypassing the ``embedding_model_id`` compatibility
    guard entirely.

    Returns ``None`` if the collection does not exist — callers must treat
    "nothing to delete" as a no-op and must never create a collection as a
    side effect of a delete-only operation (unlike
    :func:`get_story_memory_collection`, which creates on first use).

    This handle must only be used for metadata-filtered ``.get()``/
    ``.delete()`` calls — never ``.upsert()`` or a semantic ``.query()``.
    Deletion by ``story_id``/``turn_id`` metadata filter never invokes the
    embedding function at all (verified against chromadb: ``.get()``/
    ``.delete()`` with a ``where=`` filter and no embedding function bound
    both work), so embedding-model compatibility is irrelevant to a delete
    and must not block an operator from scrubbing a mismatched collection's
    story-scoped chunks ahead of a full reindex (Codex review, PR #119).

    Only ``chromadb.errors.NotFoundError`` (collection genuinely absent) is
    treated as "nothing to delete" — a locked store, corrupt store,
    permission failure, or other operational error must propagate rather
    than being silently reported as a missing collection (Codex review, PR
    #119 round 6).
    """
    try:
        return client.get_collection(name=STORY_MEMORY_COLLECTION_NAME)
    except NotFoundError:
        return None


def delete_collection_ignoring_absence(client: ClientAPI, collection_name: str) -> None:
    """Delete *collection_name* if it exists; a genuinely absent collection is
    a no-op.

    Only ``chromadb.errors.NotFoundError`` is swallowed — the same narrow
    exception type used by :func:`get_existing_story_memory_collection_for_delete`.
    Any other Chroma/operational failure (locked store, corrupt store,
    permission failure, client failure) propagates: a wipe-then-rebuild
    caller must never proceed to recreate the collection or upsert on top of
    a delete that may not have actually happened, since stale chunks would
    then remain silently retrievable (Codex review, PR #119 round 7).
    """
    with suppress(NotFoundError):
        client.delete_collection(collection_name)


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


def get_existing_rules_corpus_collection(
    client: ClientAPI,
    collection_name: str,
    config: RetrievalMemoryConfig,
    embedding_function: RetrievalEmbeddingFunction | None = None,
) -> Collection | None:
    """Open an **existing** rules_corpus collection WITHOUT creating it.

    The read-only counterpart to :func:`get_rules_corpus_collection` for the
    verify-only reuse and diagnostic-query paths, which must never create a
    canonical collection as a side effect (PR #134). Uses the non-creating
    ``client.get_collection`` — never ``get_or_create_collection``.

    Returns ``None`` only for a genuinely absent collection
    (``chromadb.errors.NotFoundError``); a locked/corrupt/permission or any other
    operational error propagates rather than being reported as absence. An
    embedding-model mismatch raises
    :class:`RetrievalCollectionReindexRequiredError` (an explicit
    verification/publication failure) and creates, wipes, or rewrites nothing.
    """
    ef = embedding_function or resolve_default_embedding_function()
    try:
        collection = client.get_collection(
            name=collection_name,
            embedding_function=ef,  # type: ignore[arg-type]
        )
    except NotFoundError:
        return None
    _require_matching_embedding_model(collection, config, collection_name)
    return collection
