"""Integration tests for RetrievalMemoryWriteService against an isolated Chroma client.

CRD Issue 18 / ADR-018 D3/D7/D11.
"""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from afterworlds.pipeline.retrieval.client import build_isolated_test_chroma_client
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
