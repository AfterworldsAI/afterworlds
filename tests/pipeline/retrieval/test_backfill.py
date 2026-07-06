"""Tests for backfill/reindex — CRD Issue 18 / ADR-018 D7.

Recovery for a Chroma write failure is a re-run: these are the idempotent
manual backfill/reindex operations. Both consult the single shared
eligibility predicate, so live ingestion and offline backfill never disagree.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest

from afterworlds.models.enums import IntentType, StoryMode
from afterworlds.models.turn import Turn
from afterworlds.persistence.crud.node import create_node, create_turn
from afterworlds.persistence.crud.story import create_arc, create_chapter, create_story
from afterworlds.persistence.database import create_session_factory
from afterworlds.pipeline.retrieval.backfill import backfill_story, reindex_story
from afterworlds.pipeline.retrieval.client import build_isolated_test_chroma_client
from afterworlds.pipeline.retrieval.config import RetrievalMemoryConfig
from afterworlds.pipeline.retrieval.embedding import DeterministicFakeEmbeddingFunction
from afterworlds.pipeline.retrieval.write_service import RetrievalMemoryWriteService
from tests.persistence.conftest import make_arc, make_chapter, make_story

_NOW = datetime(2026, 1, 1, tzinfo=UTC)


@pytest.fixture()
def session_factory(engine):  # type: ignore[no-untyped-def]
    return create_session_factory(engine)


def _seed_story_with_turns(session, mode: StoryMode, count: int):  # type: ignore[no-untyped-def]
    story = make_story(mode=mode)
    create_story(session, story)  # type: ignore[arg-type]
    arc = make_arc(str(story.story_id))
    create_arc(session, arc)  # type: ignore[arg-type]
    chapter = make_chapter(str(arc.arc_id))
    create_chapter(session, chapter)  # type: ignore[arg-type]
    from afterworlds.models.node import (
        BranchingNodeMetadata,
        Node,
        NodeMetadata,
        StateDelta,
    )

    node = Node(
        chapter_id=chapter.chapter_id,
        content="",
        state_delta=StateDelta(),
        branching_logic=[],
        intent_type=IntentType.IN_CHARACTER_ACTION,
        metadata=NodeMetadata(timestamp=_NOW),
        mode_metadata=BranchingNodeMetadata(),
    )
    create_node(session, node)  # type: ignore[arg-type]
    turn_ids = []
    for i in range(count):
        turn = Turn(
            user_input=f"input {i}",
            assistant_output=f"Delivered prose number {i}.",
            timestamp=_NOW,
            intent_classification=IntentType.IN_CHARACTER_ACTION,
            node_id=node.node_id,
        )
        create_turn(session, turn)  # type: ignore[arg-type]
        turn_ids.append(turn.turn_id)
    session.commit()
    return story.story_id, turn_ids


class TestBackfillStory:
    def test_backfill_ingests_eligible_turns(
        self, session_factory, tmp_path: Path
    ) -> None:  # type: ignore[no-untyped-def]
        session = session_factory()
        story_id, turn_ids = _seed_story_with_turns(session, StoryMode.BRANCHING, 3)

        client = build_isolated_test_chroma_client(str(tmp_path))
        config = RetrievalMemoryConfig()
        write_service = RetrievalMemoryWriteService(
            client, config, DeterministicFakeEmbeddingFunction()
        )

        report = backfill_story(session, write_service, story_id, StoryMode.BRANCHING)

        assert report.turns_scanned == 3
        assert report.turns_ingested == 3
        assert report.turns_skipped_ineligible == 0
        assert report.data_integrity_errors == ()
        assert write_service.count_for_story(story_id) == 3

    def test_backfill_is_idempotent(
        self, session_factory, tmp_path: Path
    ) -> None:  # type: ignore[no-untyped-def]
        session = session_factory()
        story_id, _turn_ids = _seed_story_with_turns(session, StoryMode.BRANCHING, 2)

        client = build_isolated_test_chroma_client(str(tmp_path))
        config = RetrievalMemoryConfig()
        write_service = RetrievalMemoryWriteService(
            client, config, DeterministicFakeEmbeddingFunction()
        )

        backfill_story(session, write_service, story_id, StoryMode.BRANCHING)
        count_after_first = write_service.count_for_story(story_id)

        backfill_story(session, write_service, story_id, StoryMode.BRANCHING)
        count_after_second = write_service.count_for_story(story_id)

        assert count_after_first == count_after_second == 2


class TestReindexStory:
    def test_reindex_wipes_then_rebuilds(
        self, session_factory, tmp_path: Path
    ) -> None:  # type: ignore[no-untyped-def]
        session = session_factory()
        story_id, turn_ids = _seed_story_with_turns(session, StoryMode.BRANCHING, 2)

        client = build_isolated_test_chroma_client(str(tmp_path))
        config = RetrievalMemoryConfig()
        write_service = RetrievalMemoryWriteService(
            client, config, DeterministicFakeEmbeddingFunction()
        )
        backfill_story(session, write_service, story_id, StoryMode.BRANCHING)

        # Simulate stray drift: an extra chunk not backed by SQL ground truth.
        write_service.ingest_turn(
            story_id, uuid4(), None, "branching", "Orphaned drift chunk.", "t-drift"
        )
        assert write_service.count_for_story(story_id) == 3

        report = reindex_story(session, write_service, story_id, StoryMode.BRANCHING)

        assert report.turns_ingested == 2
        assert write_service.count_for_story(story_id) == 2
