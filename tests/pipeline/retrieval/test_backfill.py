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

from afterworlds.models.character_sheet import RpgCharacterSheetBase
from afterworlds.models.enums import (
    IntentType,
    RollVisibility,
    RpgTurnRetrievalCategory,
    StoryMode,
    WritingCanonEligibility,
)
from afterworlds.models.node import WritingNodeMetadata
from afterworlds.models.turn import Turn
from afterworlds.persistence.crud.character_sheet import create_rpg_base_sheet
from afterworlds.persistence.crud.node import create_node, create_turn
from afterworlds.persistence.crud.retrieval import create_rpg_turn_retrieval_marker
from afterworlds.persistence.crud.story import create_arc, create_chapter, create_story
from afterworlds.persistence.database import create_session_factory
from afterworlds.persistence.orm.node import TurnORM
from afterworlds.persistence.orm.rpg import PendingRollRequestORM
from afterworlds.pipeline.retrieval.backfill import (
    RetrievalReindexWipeIncompleteError,
    backfill_story,
    reindex_story,
)
from afterworlds.pipeline.retrieval.client import build_isolated_test_chroma_client
from afterworlds.pipeline.retrieval.collections import (
    RetrievalCollectionReindexRequiredError,
)
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


def _seed_writing_story_with_malformed_and_valid_turn(session):  # type: ignore[no-untyped-def]
    """One valid EXTRACTOR_ELIGIBLE turn + one turn with malformed
    persisted mode_metadata (inserted directly, bypassing the Turn pydantic
    model's validation, to simulate a corrupted/schema-drifted row).

    Both turns are attached to a real Node -- _all_turn_ids_for_story joins
    Turn -> Node -> Chapter -> Arc -> Story, so a null node_id would make
    the turn invisible to backfill regardless of this test's intent.
    """
    from afterworlds.models.node import (
        BranchingNodeMetadata,
        Node,
        NodeMetadata,
        StateDelta,
    )

    story = make_story(mode=StoryMode.WRITING)
    create_story(session, story)  # type: ignore[arg-type]
    arc = make_arc(str(story.story_id))
    create_arc(session, arc)  # type: ignore[arg-type]
    chapter = make_chapter(str(arc.arc_id))
    create_chapter(session, chapter)  # type: ignore[arg-type]
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

    valid_metadata = WritingNodeMetadata(
        canon_eligibility=WritingCanonEligibility.EXTRACTOR_ELIGIBLE.value
    )
    valid_turn = Turn(
        user_input="prior input",
        assistant_output="Kestrel drew her blade in the moonlight.",
        timestamp=_NOW,
        intent_classification=IntentType.DIALOGUE,
        node_id=node.node_id,
        mode_metadata=valid_metadata,
    )
    create_turn(session, valid_turn)  # type: ignore[arg-type]

    malformed_turn_id = uuid4()
    session.add(
        TurnORM(
            turn_id=str(malformed_turn_id),
            node_id=str(node.node_id),
            user_input="prior input",
            assistant_output="This turn has corrupted metadata.",
            timestamp=_NOW.isoformat(),
            intent_classification=IntentType.DIALOGUE.value,
            mode_metadata={"mode": "writing", "persona_registry_version": "bad"},
        )
    )
    session.commit()
    return story.story_id, valid_turn.turn_id, malformed_turn_id


def _seed_rpg_story_with_marker_mismatch_turn(session):  # type: ignore[no-untyped-def]
    """One RPG turn with a PendingRollRequest row but an ORDINARY_NARRATIVE
    marker -- a coverage-invariant violation (ADR-018 D6) that backfill must
    report as a data-integrity error, not silently ingest or skip."""
    from afterworlds.models.node import (
        BranchingNodeMetadata,
        Node,
        NodeMetadata,
        StateDelta,
    )

    story = make_story(mode=StoryMode.RPG)
    create_story(session, story)  # type: ignore[arg-type]
    arc = make_arc(str(story.story_id))
    create_arc(session, arc)  # type: ignore[arg-type]
    chapter = make_chapter(str(arc.arc_id))
    create_chapter(session, chapter)  # type: ignore[arg-type]
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
    turn = Turn(
        user_input="swing my sword",
        assistant_output="The blade connects.",
        timestamp=_NOW,
        intent_classification=IntentType.IN_CHARACTER_ACTION,
        node_id=node.node_id,
    )
    create_turn(session, turn)  # type: ignore[arg-type]
    create_rpg_turn_retrieval_marker(
        session,
        turn_id=turn.turn_id,
        story_id=story.story_id,
        category=RpgTurnRetrievalCategory.ORDINARY_NARRATIVE,
        created_at=_NOW.isoformat(),
    )
    sheet = RpgCharacterSheetBase(
        story_id=story.story_id,
        rules_package_id="dnd5e-v1",
        character_name="Test Character",
        created_at=_NOW,
        updated_at=_NOW,
    )
    create_rpg_base_sheet(session, sheet)
    session.add(
        PendingRollRequestORM(
            request_id=str(uuid4()),
            story_id=str(story.story_id),
            session_id=str(uuid4()),
            character_id=str(sheet.sheet_id),
            originating_turn_id=str(turn.turn_id),
            visibility=RollVisibility.PLAYER.value,
            source_proposal_ref="roll_0",
            status="pending",
            created_at=_NOW.isoformat(),
            schema_version=1,
        )
    )
    session.commit()
    return story.story_id, turn.turn_id


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

    def test_malformed_writing_metadata_is_skipped_not_aborting(
        self, session_factory, tmp_path: Path
    ) -> None:  # type: ignore[no-untyped-def]
        """Codex review (PR #119): a single Writing turn with malformed
        persisted mode_metadata must not abort the whole story's backfill --
        the valid EXTRACTOR_ELIGIBLE turn must still be ingested."""
        session = session_factory()
        story_id, valid_turn_id, malformed_turn_id = (
            _seed_writing_story_with_malformed_and_valid_turn(session)
        )

        client = build_isolated_test_chroma_client(str(tmp_path))
        config = RetrievalMemoryConfig()
        write_service = RetrievalMemoryWriteService(
            client, config, DeterministicFakeEmbeddingFunction()
        )

        report = backfill_story(session, write_service, story_id, StoryMode.WRITING)

        assert report.turns_scanned == 2
        assert report.turns_ingested == 1
        assert report.turns_skipped_ineligible == 1
        assert report.data_integrity_errors == ()
        assert write_service.count_for_story(story_id) == 1

    def test_rpg_marker_pending_roll_mismatch_is_reported_as_data_integrity_error(
        self, session_factory, tmp_path: Path
    ) -> None:  # type: ignore[no-untyped-def]
        """Codex review (PR #119) round 6: backfill must report the turn ID
        of a post-boundary marker/PendingRollRequest mismatch as a
        data-integrity error, not ingest it and not silently skip it."""
        session = session_factory()
        story_id, turn_id = _seed_rpg_story_with_marker_mismatch_turn(session)

        client = build_isolated_test_chroma_client(str(tmp_path))
        config = RetrievalMemoryConfig()
        write_service = RetrievalMemoryWriteService(
            client, config, DeterministicFakeEmbeddingFunction()
        )

        report = backfill_story(session, write_service, story_id, StoryMode.RPG)

        assert report.turns_scanned == 1
        assert report.turns_ingested == 0
        assert report.data_integrity_errors == (turn_id,)
        assert write_service.count_for_story(story_id) == 0


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


class TestReindexAbortsOnIncompleteWipe:
    """Codex review (PR #119) round 6: reindex_story() must never rebuild on
    top of an incomplete delete_story() wipe -- that would leave stale
    chunks alongside the freshly rebuilt set."""

    def test_reindex_aborts_and_skips_backfill_when_delete_leaves_chunks(
        self, session_factory, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:  # type: ignore[no-untyped-def]
        session = session_factory()
        story_id, _turn_ids = _seed_story_with_turns(session, StoryMode.BRANCHING, 2)

        client = build_isolated_test_chroma_client(str(tmp_path))
        config = RetrievalMemoryConfig()
        write_service = RetrievalMemoryWriteService(
            client, config, DeterministicFakeEmbeddingFunction()
        )
        monkeypatch.setattr(write_service, "delete_story", lambda story_id: 3)

        backfill_calls = []
        monkeypatch.setattr(
            "afterworlds.pipeline.retrieval.backfill.backfill_story",
            lambda *a, **k: backfill_calls.append((a, k)),
        )

        with pytest.raises(RetrievalReindexWipeIncompleteError):
            reindex_story(session, write_service, story_id, StoryMode.BRANCHING)

        assert backfill_calls == []

    def test_reindex_rebuilds_when_delete_returns_zero(
        self, session_factory, tmp_path: Path
    ) -> None:  # type: ignore[no-untyped-def]
        session = session_factory()
        story_id, _turn_ids = _seed_story_with_turns(session, StoryMode.BRANCHING, 2)

        client = build_isolated_test_chroma_client(str(tmp_path))
        config = RetrievalMemoryConfig()
        write_service = RetrievalMemoryWriteService(
            client, config, DeterministicFakeEmbeddingFunction()
        )

        report = reindex_story(session, write_service, story_id, StoryMode.BRANCHING)

        assert report.turns_ingested == 2


class TestEmbeddingModelMismatchSurfacesThroughBackfill:
    """Codex review (PR #119) round 3: backfill/reindex must surface the
    typed reindex-required error clearly rather than continuing to upsert
    into a collection whose recorded embedding model differs from config."""

    def test_backfill_raises_on_embedding_model_mismatch(
        self, session_factory, tmp_path: Path
    ) -> None:  # type: ignore[no-untyped-def]
        session = session_factory()
        story_id, _turn_ids = _seed_story_with_turns(session, StoryMode.BRANCHING, 2)

        client = build_isolated_test_chroma_client(str(tmp_path))
        ef = DeterministicFakeEmbeddingFunction()
        # Create the shared collection under model-a first.
        RetrievalMemoryWriteService(
            client, RetrievalMemoryConfig(embedding_model_id="model-a"), ef
        ).ingest_turn(uuid4(), uuid4(), None, "branching", "Unrelated seed.", "t0")

        mismatched_write_service = RetrievalMemoryWriteService(
            client, RetrievalMemoryConfig(embedding_model_id="model-b"), ef
        )

        with pytest.raises(RetrievalCollectionReindexRequiredError):
            backfill_story(
                session, mismatched_write_service, story_id, StoryMode.BRANCHING
            )

    def test_reindex_story_deletes_stale_entries_then_fails_clearly_on_mismatch(
        self, session_factory, tmp_path: Path
    ) -> None:  # type: ignore[no-untyped-def]
        """Codex review (PR #119) round 5: story_memory is shared across all
        stories (ADR-018 D1), so a single story's reindex_story() cannot
        repair a collection-level embedding-model mismatch on its own. It
        may safely delete this story's stale entries (metadata-only, never
        gated by the model guard) but must fail with the same clear typed
        error rather than silently upserting into the still-incompatible
        collection -- never "pretend" the story-level reindex fixed it."""
        session = session_factory()
        story_id, _turn_ids = _seed_story_with_turns(session, StoryMode.BRANCHING, 2)

        client = build_isolated_test_chroma_client(str(tmp_path))
        ef = DeterministicFakeEmbeddingFunction()
        # Create the shared collection under model-a, ingest this story's
        # own (now-stale) chunks under that model too.
        write_service_a = RetrievalMemoryWriteService(
            client, RetrievalMemoryConfig(embedding_model_id="model-a"), ef
        )
        for turn_id in _turn_ids:
            write_service_a.ingest_turn(
                story_id, turn_id, None, "branching", "Stale prose.", "t"
            )
        assert write_service_a.count_for_story(story_id) == 2

        mismatched_write_service = RetrievalMemoryWriteService(
            client, RetrievalMemoryConfig(embedding_model_id="model-b"), ef
        )

        with pytest.raises(RetrievalCollectionReindexRequiredError, match="shared"):
            reindex_story(
                session, mismatched_write_service, story_id, StoryMode.BRANCHING
            )

        # The delete-only phase ran safely (metadata delete never gated by
        # the model guard) -- this story's stale entries are gone even
        # though the collection-level mismatch blocked the rebuild.
        assert write_service_a.count_for_story(story_id) == 0
