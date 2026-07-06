"""Integration tests for RetrievalMemoryWriteService against an isolated Chroma client.

CRD Issue 18 / ADR-018 D3/D7/D11.
"""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest

from afterworlds.pipeline.retrieval.client import build_isolated_test_chroma_client
from afterworlds.pipeline.retrieval.collections import (
    RetrievalCollectionReindexRequiredError,
)
from afterworlds.pipeline.retrieval.config import RetrievalMemoryConfig
from afterworlds.pipeline.retrieval.embedding import DeterministicFakeEmbeddingFunction
from afterworlds.pipeline.retrieval.write_service import RetrievalMemoryWriteService


def _make_service(
    tmp_path: Path, chunk_char_ceiling: int = 4000
) -> RetrievalMemoryWriteService:
    client = build_isolated_test_chroma_client(str(tmp_path))
    config = RetrievalMemoryConfig(chunk_char_ceiling=chunk_char_ceiling)
    return RetrievalMemoryWriteService(
        client, config, DeterministicFakeEmbeddingFunction()
    )


class TestIngestIdempotence:
    def test_reingesting_same_turn_is_byte_identical(self, tmp_path: Path) -> None:
        service = _make_service(tmp_path)
        story_id, turn_id = uuid4(), uuid4()
        service.ingest_turn(story_id, turn_id, None, "rpg", "Some prose.", "t1")
        count_after_first = service.count_for_story(story_id)

        service.ingest_turn(story_id, turn_id, None, "rpg", "Some prose.", "t1")
        count_after_second = service.count_for_story(story_id)

        assert count_after_first == count_after_second == 1

    def test_atomic_metadata_provenance(self, tmp_path: Path) -> None:
        """Every chunk's content_hash must describe its own document."""
        service = _make_service(tmp_path)
        story_id, turn_id = uuid4(), uuid4()
        service.ingest_turn(story_id, turn_id, None, "rpg", "Consistent prose.", "t1")
        collection = service._collection()  # noqa: SLF001 — test introspection
        result = collection.get(where={"story_id": str(story_id)})
        from afterworlds.pipeline.retrieval.embedding import content_hash

        for doc, meta in zip(result["documents"], result["metadatas"], strict=True):
            assert meta["content_hash"] == content_hash(doc)


class TestDeleteBeforeWrite:
    def test_shrinking_chunk_set_removes_stale_high_index_chunks(
        self, tmp_path: Path
    ) -> None:
        """ADR-018 D11: a shrunk re-ingestion must not leave stray old chunks."""
        service = _make_service(tmp_path, chunk_char_ceiling=20)
        story_id, turn_id = uuid4(), uuid4()

        long_text = "\n\n".join(["paragraph one is long enough"] * 5)
        service.ingest_turn(story_id, turn_id, None, "rpg", long_text, "t1")
        count_before = service.count_for_story(story_id)
        assert count_before > 1  # sanity: multiple chunks produced

        short_text = "short."
        service.ingest_turn(story_id, turn_id, None, "rpg", short_text, "t2")
        count_after = service.count_for_story(story_id)
        assert count_after == 1

    def test_unchanged_chunk_count_still_deletes_before_write(
        self, tmp_path: Path
    ) -> None:
        """Required even when new chunk count is unchanged (ADR-018 D11)."""
        service = _make_service(tmp_path)
        story_id, turn_id = uuid4(), uuid4()
        service.ingest_turn(story_id, turn_id, None, "rpg", "Version one.", "t1")
        service.ingest_turn(story_id, turn_id, None, "rpg", "Version two.", "t2")
        assert service.count_for_story(story_id) == 1
        collection = service._collection()  # noqa: SLF001
        result = collection.get(where={"story_id": str(story_id)})
        assert result["documents"] == ["Version two."]


class TestDeletion:
    def test_delete_turn_removes_only_that_turns_chunks(self, tmp_path: Path) -> None:
        service = _make_service(tmp_path)
        story_id = uuid4()
        turn_a, turn_b = uuid4(), uuid4()
        service.ingest_turn(story_id, turn_a, None, "rpg", "Turn A prose.", "t1")
        service.ingest_turn(story_id, turn_b, None, "rpg", "Turn B prose.", "t2")

        service.delete_turn(story_id, turn_a)

        collection = service._collection()  # noqa: SLF001
        result = collection.get(where={"story_id": str(story_id)})
        assert result["documents"] == ["Turn B prose."]

    def test_delete_story_removes_all_and_reports_zero_remaining(
        self, tmp_path: Path
    ) -> None:
        service = _make_service(tmp_path)
        story_a, story_b = uuid4(), uuid4()
        service.ingest_turn(story_a, uuid4(), None, "rpg", "Story A prose.", "t1")
        service.ingest_turn(story_a, uuid4(), None, "rpg", "More A prose.", "t2")
        service.ingest_turn(story_b, uuid4(), None, "rpg", "Story B prose.", "t3")

        remaining = service.delete_story(story_a)

        assert remaining == 0
        assert service.count_for_story(story_a) == 0
        assert service.count_for_story(story_b) == 1


class TestEmbeddingModelMismatchSurfaces:
    """Codex review (PR #119) round 3: the write service must surface the
    typed reindex-required error clearly rather than continuing to upsert
    into a collection whose recorded embedding model differs from config."""

    def test_ingest_turn_raises_on_embedding_model_mismatch(
        self, tmp_path: Path
    ) -> None:
        client = build_isolated_test_chroma_client(str(tmp_path))
        ef = DeterministicFakeEmbeddingFunction()
        service_a = RetrievalMemoryWriteService(
            client, RetrievalMemoryConfig(embedding_model_id="model-a"), ef
        )
        service_a.ingest_turn(uuid4(), uuid4(), None, "rpg", "Some prose.", "t1")

        service_b = RetrievalMemoryWriteService(
            client, RetrievalMemoryConfig(embedding_model_id="model-b"), ef
        )

        with pytest.raises(RetrievalCollectionReindexRequiredError):
            service_b.ingest_turn(uuid4(), uuid4(), None, "rpg", "More prose.", "t2")


class TestDeleteBypassesEmbeddingModelGuard:
    """Codex review (PR #119) round 5: delete_turn()/delete_story() are
    metadata-filtered operations that never invoke the embedding function,
    so they must still work against a collection whose recorded
    embedding_model_id no longer matches config -- an operator must be able
    to scrub stale/mismatched chunks ahead of a full reindex. Normal
    ingest/query paths must stay strict (proved above)."""

    def test_delete_story_removes_chunks_from_mismatched_collection(
        self, tmp_path: Path
    ) -> None:
        client = build_isolated_test_chroma_client(str(tmp_path))
        ef = DeterministicFakeEmbeddingFunction()
        story_id = uuid4()
        service_a = RetrievalMemoryWriteService(
            client, RetrievalMemoryConfig(embedding_model_id="model-a"), ef
        )
        service_a.ingest_turn(story_id, uuid4(), None, "rpg", "Stale prose.", "t1")

        service_b = RetrievalMemoryWriteService(
            client, RetrievalMemoryConfig(embedding_model_id="model-b"), ef
        )

        remaining = service_b.delete_story(story_id)

        assert remaining == 0

    def test_delete_turn_removes_chunks_from_mismatched_collection(
        self, tmp_path: Path
    ) -> None:
        client = build_isolated_test_chroma_client(str(tmp_path))
        ef = DeterministicFakeEmbeddingFunction()
        story_id, turn_id = uuid4(), uuid4()
        service_a = RetrievalMemoryWriteService(
            client, RetrievalMemoryConfig(embedding_model_id="model-a"), ef
        )
        service_a.ingest_turn(story_id, turn_id, None, "rpg", "Stale prose.", "t1")

        service_b = RetrievalMemoryWriteService(
            client, RetrievalMemoryConfig(embedding_model_id="model-b"), ef
        )
        # Must not raise despite the mismatch.
        service_b.delete_turn(story_id, turn_id)

        # Verify via the delete-only accessor directly (avoids re-raising
        # the guard through a strict collection fetch).
        from afterworlds.pipeline.retrieval.collections import (
            get_existing_story_memory_collection_for_delete,
        )

        collection = get_existing_story_memory_collection_for_delete(client)
        assert collection is not None
        result = collection.get(where={"story_id": str(story_id)})
        assert result["ids"] == []

    def test_delete_works_on_legacy_collection_missing_embedding_model_id(
        self, tmp_path: Path
    ) -> None:
        """A collection created before the embedding-model guard existed has
        no embedding_model_id key at all -- delete must still work."""
        client = build_isolated_test_chroma_client(str(tmp_path))
        ef = DeterministicFakeEmbeddingFunction()
        story_id = uuid4()
        # Simulate a legacy pre-guard collection directly against the raw
        # client, bypassing get_story_memory_collection entirely.
        legacy_collection = client.get_or_create_collection(
            name="story_memory",
            metadata={"hnsw:space": "cosine"},
            embedding_function=ef,  # type: ignore[arg-type]
        )
        legacy_collection.upsert(
            documents=["Legacy prose."],
            metadatas=[{"story_id": str(story_id)}],
            ids=["legacy-chunk-1"],
        )

        service = RetrievalMemoryWriteService(client, RetrievalMemoryConfig(), ef)
        remaining = service.delete_story(story_id)

        assert remaining == 0

    def test_delete_on_missing_collection_is_noop_and_creates_nothing(
        self, tmp_path: Path
    ) -> None:
        client = build_isolated_test_chroma_client(str(tmp_path))
        ef = DeterministicFakeEmbeddingFunction()
        service = RetrievalMemoryWriteService(client, RetrievalMemoryConfig(), ef)

        remaining = service.delete_story(uuid4())
        service.delete_turn(uuid4(), uuid4())

        assert remaining == 0
        assert client.list_collections() == []

    def test_delete_story_never_calls_upsert(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        client = build_isolated_test_chroma_client(str(tmp_path))
        ef = DeterministicFakeEmbeddingFunction()
        story_id = uuid4()
        service_a = RetrievalMemoryWriteService(
            client, RetrievalMemoryConfig(embedding_model_id="model-a"), ef
        )
        service_a.ingest_turn(story_id, uuid4(), None, "rpg", "Stale prose.", "t1")

        from afterworlds.pipeline.retrieval.collections import (
            get_existing_story_memory_collection_for_delete as real_getter,
        )

        class _UpsertSpyCollectionWrapper:
            def __init__(self, wrapped: object) -> None:
                self._wrapped = wrapped
                self.upsert_called = False

            def __getattr__(self, name: str) -> object:
                return getattr(self._wrapped, name)

            def upsert(self, *args: object, **kwargs: object) -> None:
                self.upsert_called = True
                raise AssertionError("delete-only path must never call upsert()")

        spy_holder: dict[str, _UpsertSpyCollectionWrapper] = {}

        def _spy_getter(client_arg: object):  # type: ignore[no-untyped-def]
            real = real_getter(client_arg)
            if real is None:
                return None
            wrapper = _UpsertSpyCollectionWrapper(real)
            spy_holder["wrapper"] = wrapper
            return wrapper

        monkeypatch.setattr(
            "afterworlds.pipeline.retrieval.write_service."
            "get_existing_story_memory_collection_for_delete",
            _spy_getter,
        )

        service_b = RetrievalMemoryWriteService(
            client, RetrievalMemoryConfig(embedding_model_id="model-b"), ef
        )
        service_b.delete_story(story_id)

        assert spy_holder["wrapper"].upsert_called is False

    def test_delete_story_propagates_operational_error_not_remaining_zero(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Codex review (PR #119) round 6: an operational failure opening the
        collection (locked store, permission error, etc.) must propagate --
        delete_story() must never report remaining=0 in that case, since
        that would look like a successful (empty) delete."""
        client = build_isolated_test_chroma_client(str(tmp_path))
        ef = DeterministicFakeEmbeddingFunction()
        service = RetrievalMemoryWriteService(client, RetrievalMemoryConfig(), ef)

        def _boom(client_arg: object) -> None:
            raise RuntimeError("store locked")

        monkeypatch.setattr(
            "afterworlds.pipeline.retrieval.write_service."
            "get_existing_story_memory_collection_for_delete",
            _boom,
        )

        with pytest.raises(RuntimeError, match="store locked"):
            service.delete_story(uuid4())
