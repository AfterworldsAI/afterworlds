"""RetrievalMemoryWriteService — CRD Issue 18 / ADR-018 D3/D7/D11.

Writes story-memory chunks to the shared ``story_memory`` Chroma collection.
Called only after the ingestion gate (``pipeline/orchestrator/service.py``)
has confirmed a committed, delivery-cleared, D6-eligible narrative turn —
this service does not itself re-check eligibility.

Write-failure semantics (D7): a Chroma write failure here is logged and
swallowed by the caller (the ingestion gate) — delivery is never blocked,
reversed, or errored by a retrieval-write failure. This service raises on
failure; the ingestion gate is responsible for catching and swallowing.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping
from contextlib import suppress
from uuid import UUID

from chromadb.api import ClientAPI
from chromadb.api.models.Collection import Collection

from afterworlds.models.retrieval import (
    STORY_MEMORY_COLLECTION_NAME,
    StoryMemoryChunkMetadata,
    build_story_memory_chunk_id,
)
from afterworlds.pipeline.retrieval.chunking import chunk_turn_prose
from afterworlds.pipeline.retrieval.collections import (
    get_existing_story_memory_collection_for_delete,
    get_story_memory_collection,
)
from afterworlds.pipeline.retrieval.config import RetrievalMemoryConfig
from afterworlds.pipeline.retrieval.embedding import (
    RetrievalEmbeddingFunction,
    content_hash,
)

logger = logging.getLogger(__name__)


class RetrievalMemoryWriteService:
    """Write/delete path for the shared story_memory Chroma collection."""

    def __init__(
        self,
        client: ClientAPI,
        config: RetrievalMemoryConfig,
        embedding_function: RetrievalEmbeddingFunction | None = None,
    ) -> None:
        self._client = client
        self._config = config
        self._embedding_function = embedding_function

    def _collection(self) -> Collection:
        return get_story_memory_collection(
            self._client, self._config, self._embedding_function
        )

    def ingest_turn(
        self,
        story_id: UUID,
        turn_id: UUID,
        node_id: UUID | None,
        mode: str,
        delivered_output: str,
        created_at: str,
    ) -> None:
        """Chunk and upsert one delivered turn's prose.

        Delete-before-write (ADR-018 D11): existing chunks for this
        ``turn_id`` are deleted first, then the current chunk set is
        written. Required even when the new chunk count is unchanged —
        mandatory when it shrinks, since a deterministic-ID upsert alone
        cannot remove chunks whose index no longer exists in the new set.
        """
        collection = self._collection()
        self._delete_turn_chunks(collection, story_id, turn_id)

        chunks = chunk_turn_prose(delivered_output, self._config.chunk_char_ceiling)
        if not chunks or not delivered_output:
            return

        ids: list[str] = []
        documents: list[str] = []
        metadatas: list[Mapping[str, str | int | float | bool | None]] = []
        for index, chunk_text in enumerate(chunks):
            metadata = StoryMemoryChunkMetadata(
                story_id=story_id,
                node_id=node_id,
                turn_id=turn_id,
                mode=mode,
                chunk_index=index,
                chunk_count=len(chunks),
                created_at=created_at,
                content_hash=content_hash(chunk_text),
                embedding_model_id=self._config.embedding_model_id,
            )
            ids.append(build_story_memory_chunk_id(story_id, turn_id, index))
            documents.append(chunk_text)
            metadatas.append(metadata.model_dump(mode="json"))

        collection.upsert(
            documents=documents,
            metadatas=metadatas,  # type: ignore[arg-type]
            ids=ids,
        )

    def _delete_turn_chunks(
        self, collection: Collection, story_id: UUID, turn_id: UUID
    ) -> None:
        existing = collection.get(
            where={
                "$and": [
                    {"story_id": str(story_id)},
                    {"turn_id": str(turn_id)},
                ]
            }
        )
        ids = existing.get("ids") or []
        if ids:
            collection.delete(ids=ids)

    def delete_turn(self, story_id: UUID, turn_id: UUID) -> None:
        """Delete all chunks for *turn_id* (turn deletion).

        Uses the delete-only collection handle (Codex review, PR #119):
        deletion is metadata-filtered and never invokes the embedding
        function, so an operator must be able to scrub a mismatched/legacy
        collection's chunks even while it fails the strict
        ``embedding_model_id`` guard on every other path. A missing
        collection means nothing to delete — a no-op, never created here.
        """
        collection = get_existing_story_memory_collection_for_delete(self._client)
        if collection is None:
            return
        self._delete_turn_chunks(collection, story_id, turn_id)

    def delete_story(self, story_id: UUID) -> int:
        """Delete all chunks for *story_id*; returns remaining count (must be 0).

        Uses the delete-only collection handle for the same reason as
        :meth:`delete_turn`. A missing collection means zero chunks exist
        for any story — return 0 without creating one.
        """
        collection = get_existing_story_memory_collection_for_delete(self._client)
        if collection is None:
            return 0
        existing = collection.get(where={"story_id": str(story_id)})
        ids = existing.get("ids") or []
        if ids:
            collection.delete(ids=ids)
        remaining = collection.get(where={"story_id": str(story_id)})
        remaining_count = len(remaining.get("ids") or [])
        if remaining_count != 0:
            logger.error(
                "story-delete post-condition violated: %d chunks remain for"
                " story_id=%s",
                remaining_count,
                story_id,
            )
        return remaining_count

    def count_for_story(self, story_id: UUID) -> int:
        """Return the number of chunks currently indexed for *story_id*."""
        result = self._collection().get(where={"story_id": str(story_id)})
        return len(result.get("ids") or [])

    def wipe_collection(self) -> None:
        """Delete and recreate the entire story_memory collection (full reindex)."""
        with suppress(Exception):  # collection may not exist yet
            self._client.delete_collection(STORY_MEMORY_COLLECTION_NAME)
