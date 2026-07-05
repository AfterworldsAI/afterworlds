"""Unit tests for Retrieval Memory DTOs and the deterministic ID scheme.

CRD Issue 18 / ADR-018 D2/D11.
"""

from __future__ import annotations

from uuid import uuid4

from afterworlds.models.enums import (
    RetrievalChunkKind,
    RetrievalSourceType,
    SourceLocatorTypeEnum,
)
from afterworlds.models.retrieval import (
    RulesCorpusChunkMetadata,
    StoryMemoryChunkMetadata,
    build_rules_corpus_chunk_id,
    build_story_memory_chunk_id,
    build_story_memory_chunk_id_prefix,
    rules_corpus_collection_name,
)


class TestStoryMemoryChunkId:
    def test_deterministic_same_inputs(self) -> None:
        story_id = uuid4()
        turn_id = uuid4()
        assert build_story_memory_chunk_id(
            story_id, turn_id, 0
        ) == build_story_memory_chunk_id(story_id, turn_id, 0)

    def test_distinct_per_index(self) -> None:
        story_id = uuid4()
        turn_id = uuid4()
        assert build_story_memory_chunk_id(
            story_id, turn_id, 0
        ) != build_story_memory_chunk_id(story_id, turn_id, 1)

    def test_distinct_per_turn(self) -> None:
        story_id = uuid4()
        assert build_story_memory_chunk_id(
            story_id, uuid4(), 0
        ) != build_story_memory_chunk_id(story_id, uuid4(), 0)

    def test_not_a_random_uuid(self) -> None:
        """ADR-018 D11: random UUIDs are prohibited as dedupe keys."""
        story_id = uuid4()
        turn_id = uuid4()
        chunk_id = build_story_memory_chunk_id(story_id, turn_id, 0)
        assert str(story_id) in chunk_id
        assert str(turn_id) in chunk_id

    def test_prefix_is_shared_across_indices(self) -> None:
        story_id = uuid4()
        turn_id = uuid4()
        prefix = build_story_memory_chunk_id_prefix(story_id, turn_id)
        assert build_story_memory_chunk_id(story_id, turn_id, 0).startswith(prefix)
        assert build_story_memory_chunk_id(story_id, turn_id, 5).startswith(prefix)

    def test_prefix_distinct_across_turns(self) -> None:
        story_id = uuid4()
        assert build_story_memory_chunk_id_prefix(
            story_id, uuid4()
        ) != build_story_memory_chunk_id_prefix(story_id, uuid4())


class TestRulesCorpusChunkId:
    def test_deterministic(self) -> None:
        package_id = uuid4()
        args = (package_id, SourceLocatorTypeEnum.PAGE, "p. 72", 0)
        assert build_rules_corpus_chunk_id(*args) == build_rules_corpus_chunk_id(*args)

    def test_distinct_per_locator_value(self) -> None:
        package_id = uuid4()
        a = build_rules_corpus_chunk_id(
            package_id, SourceLocatorTypeEnum.PAGE, "p. 72", 0
        )
        b = build_rules_corpus_chunk_id(
            package_id, SourceLocatorTypeEnum.PAGE, "p. 73", 0
        )
        assert a != b

    def test_collection_name_derives_from_package_id(self) -> None:
        package_id = uuid4()
        name = rules_corpus_collection_name(package_id)
        assert package_id.hex in name
        assert name == rules_corpus_collection_name(package_id)


class TestStoryMemoryChunkMetadata:
    def test_defaults(self) -> None:
        metadata = StoryMemoryChunkMetadata(
            story_id=uuid4(),
            node_id=uuid4(),
            turn_id=uuid4(),
            mode="rpg",
            chunk_index=0,
            chunk_count=1,
            created_at="2026-01-01T00:00:00+00:00",
            content_hash="abc",
            embedding_model_id="test-model",
        )
        assert metadata.source_type is RetrievalSourceType.DELIVERED_TURN_PROSE
        assert metadata.chunk_kind is RetrievalChunkKind.SCENE_PROSE
        assert metadata.schema_version == 1

    def test_source_type_and_chunk_kind_are_distinct_fields(self) -> None:
        """ADR-018 D2 (Codex round-3 correction): must not be collapsed."""
        metadata = StoryMemoryChunkMetadata(
            story_id=uuid4(),
            node_id=None,
            turn_id=uuid4(),
            mode="writing",
            chunk_index=0,
            chunk_count=1,
            created_at="2026-01-01T00:00:00+00:00",
            content_hash="abc",
            embedding_model_id="test-model",
        )
        dumped = metadata.model_dump(mode="json")
        assert "source_type" in dumped
        assert "chunk_kind" in dumped
        assert dumped["source_type"] != dumped["chunk_kind"]


class TestRulesCorpusChunkMetadata:
    def test_round_trip(self) -> None:
        metadata = RulesCorpusChunkMetadata(
            rules_package_id=uuid4(),
            subsystem="combat",
            source_document="srd_5e.json",
            source_locator_type=SourceLocatorTypeEnum.PAGE,
            source_locator_value="p. 72",
            embedding_model_id="test-model",
        )
        dumped = metadata.model_dump(mode="json")
        restored = RulesCorpusChunkMetadata.model_validate(dumped)
        assert restored == metadata
