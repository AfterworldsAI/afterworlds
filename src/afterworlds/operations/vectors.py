"""Story-memory deletion for the lifecycle executor (ADR-018 D11).

Metadata-filtered delete through the delete-only collection handle, then a
count read; a missing collection is zero (the supported delete-only path),
any other failure propagates -- an unavailable read is never zero.
"""

from __future__ import annotations

from collections.abc import Callable

from chromadb.api import ClientAPI

from afterworlds.pipeline.retrieval.collections import (
    get_existing_story_memory_collection_for_delete,
)


def story_chunk_deleter(
    client_factory: Callable[[], ClientAPI],
) -> Callable[[str], int]:
    def delete(story_id: str) -> int:
        collection = get_existing_story_memory_collection_for_delete(client_factory())
        if collection is None:
            return 0
        ids = collection.get(where={"story_id": story_id}).get("ids") or []
        if ids:
            collection.delete(ids=ids)
        return len(collection.get(where={"story_id": story_id}).get("ids") or [])

    return delete


def story_chunk_counter(
    client_factory: Callable[[], ClientAPI],
) -> Callable[[str], int]:
    def count(story_id: str) -> int:
        collection = get_existing_story_memory_collection_for_delete(client_factory())
        if collection is None:
            return 0
        return len(collection.get(where={"story_id": story_id}).get("ids") or [])

    return count
