"""Default-CI integration test for the Writer pass — CRD Issue 9 / 14a.

Uses a high-fidelity fake ProviderAdapter to exercise the full round-trip
without a network call:

  1. Seed a Story + minimal Arc/Chapter/Node chain in SQLite.
  2. Seed a minimal Story Bible for Branching mode.
  3. Build an IntentClassificationResult for a Branching-mode input.
  4. Call ContextBuilderService.build_stable_prefix and build_volatile_suffix
     to produce an AssembledContext.
  5. Hand the AssembledContext, story_id, and node_id to WriterService,
     configured with a high-fidelity fake ProviderAdapter.
  6. Assert: Turn row persisted in SQLite linked to the seeded Node, with
     non-empty assistant_output, correct user_input, round-tripping ICR,
     and WriterResult surfacing usage metrics from the fake.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

import afterworlds.persistence.orm.character_sheet  # noqa: F401
import afterworlds.persistence.orm.node  # noqa: F401
import afterworlds.persistence.orm.rolling_summary  # noqa: F401
import afterworlds.persistence.orm.rules_package  # noqa: F401
import afterworlds.persistence.orm.session_state  # noqa: F401
import afterworlds.persistence.orm.state  # noqa: F401
import afterworlds.persistence.orm.story  # noqa: F401
import afterworlds.persistence.orm.story_bible  # noqa: F401
from afterworlds.entitlement.enums import ModelTier, PipelinePassId
from afterworlds.models.enums import CastRole, IntentType, StoryMode
from afterworlds.models.intent_classification import IntentClassificationResult
from afterworlds.models.node import Node
from afterworlds.models.story import Arc, Chapter, Story
from afterworlds.models.story_bible import (
    CastEntry,
    StoryBibleSetting,
)
from afterworlds.persistence.crud.node import create_node, get_turn
from afterworlds.persistence.crud.story import create_arc, create_chapter, create_story
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.persistence.orm.base import Base
from afterworlds.pipeline.provider._models import (
    ProviderCallRequest,
    ProviderCallResult,
    ProviderTextPart,
)
from afterworlds.pipeline.writer.config import WriterConfig
from afterworlds.pipeline.writer.models import WriterResult
from afterworlds.pipeline.writer.service import WriterService
from afterworlds.services.context_builder import (
    ContextBuilderService,
    NullRetrievalMemoryProvider,
    SQLiteRecentTurnsProvider,
)
from afterworlds.services.rolling_summary import RollingSummaryService
from afterworlds.services.story_bible import StoryBibleService


@pytest.fixture()
def engine():  # type: ignore[no-untyped-def]
    eng = create_engine("sqlite://")
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)
    eng.dispose()


@pytest.fixture()
def session(engine):  # type: ignore[no-untyped-def]
    factory = create_session_factory(engine)
    sess = factory()
    try:
        yield sess
    finally:
        sess.close()


@pytest.fixture()
def seeded_story(session):  # type: ignore[no-untyped-def]
    now = datetime(2026, 1, 1, tzinfo=UTC)
    story = Story(
        title="The Obsidian Vale",
        mode=StoryMode.BRANCHING,
        created_at=now,
        updated_at=now,
    )
    create_story(session, story)
    arc = Arc(story_id=story.story_id, title="Arc One", order=1)
    create_arc(session, arc)
    chapter = Chapter(arc_id=arc.arc_id, title="Chapter One", order=1)
    create_chapter(session, chapter)
    node = Node(
        chapter_id=chapter.chapter_id,
        content="",
        intent_type=IntentType.IN_CHARACTER_ACTION,
    )
    create_node(session, node)
    session.commit()
    return story, node


@pytest.fixture()
def seeded_bible(session, seeded_story):  # type: ignore[no-untyped-def]
    story, _ = seeded_story
    bible_service = StoryBibleService(session)
    setting = StoryBibleSetting(
        story_id=story.story_id,
        summary="A shadowed valley ruled by an ancient curse.",
        world_rules=("The dead walk at night",),
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    bible_service.create_setting(story.story_id, setting)
    cast_entry = CastEntry(
        story_id=story.story_id,
        name="Eryndor",
        role=CastRole.PROTAGONIST,
        background="A wandering scholar seeking the source of the curse.",
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    bible_service.add_cast_entry(story.story_id, cast_entry)
    session.commit()
    return bible_service


@pytest.fixture()
def context_builder(session):  # type: ignore[no-untyped-def]
    bible_service = StoryBibleService(session)
    rolling_service = RollingSummaryService(session, lambda _existing, _turns: "")
    recent_turns_provider = SQLiteRecentTurnsProvider(session)
    retrieval_memory = NullRetrievalMemoryProvider()
    return ContextBuilderService(
        story_bible_service=bible_service,
        rolling_summary_service=rolling_service,
        recent_turns_provider=recent_turns_provider,
        retrieval_memory=retrieval_memory,
    )


def _make_branching_icr(
    raw_input: str = "I follow the path into the vale.",
) -> IntentClassificationResult:
    return IntentClassificationResult(
        intent_type=IntentType.IN_CHARACTER_ACTION,
        confidence=0.93,
        raw_input=raw_input,
        ambiguous=False,
    )


_DEFAULT_PROSE = (
    "The path winds deeper into the Obsidian Vale, shadows lengthening around you."
)


class _FakeAdapter:
    """High-fidelity fake ProviderAdapter capturing ProviderCallRequest."""

    def __init__(self, prose: str = _DEFAULT_PROSE) -> None:
        self._prose = prose
        self.captured: list[ProviderCallRequest] = []
        self.provider_name = "anthropic"

    def call(self, request: ProviderCallRequest) -> ProviderCallResult:
        self.captured.append(request)
        return ProviderCallResult(
            pass_id=PipelinePassId.WRITER,
            provider_name="anthropic",
            model_identifier="anthropic:claude-sonnet-4-5",
            model_tier=ModelTier.SONNET,
            content_parts=[ProviderTextPart(text=self._prose)],
            input_token_count=350,
            output_token_count=42,
            cache_read_token_count=280,
            cache_creation_token_count=70,
            cache_warmed=True,
            latency_ms=10,
        )


class TestWriterIntegration:
    def test_full_round_trip_branching_mode(
        self,
        session,
        seeded_story,
        seeded_bible,
        context_builder,
    ) -> None:
        """Full round-trip: Branching mode, real context stack, fake provider."""
        story, node = seeded_story
        raw_input = "I follow the path into the vale."
        icr = _make_branching_icr(raw_input)

        stable_prefix = context_builder.build_stable_prefix(
            story_id=story.story_id,
            mode=StoryMode.BRANCHING,
            intent_classification=icr,
        )
        volatile_suffix = context_builder.build_volatile_suffix(
            story_id=story.story_id,
            raw_input=raw_input,
            intent_classification=icr,
        )

        from afterworlds.models.context import AssembledContext, PassForwardLedger

        assembled = AssembledContext(
            stable_prefix=stable_prefix,
            volatile_suffix=volatile_suffix,
            pass_forward_ledger=PassForwardLedger(),
        )

        fake_prose = "The path winds deeper into the Obsidian Vale."
        adapter = _FakeAdapter(prose=fake_prose)
        config = WriterConfig(
            model="claude-sonnet-4-5",
            api_key_env="ANTHROPIC_API_KEY",
            extended_ttl=True,
        )
        service = WriterService(session, config)

        result = service.write(
            built_context=assembled,
            story_id=story.story_id,
            node_id=node.node_id,
            provider=adapter,  # type: ignore[arg-type]
        )

        assert isinstance(result, WriterResult)
        assert result.assistant_output == fake_prose
        assert result.turn_id is not None
        assert result.model_identifier.startswith("anthropic:")
        assert result.latency_ms >= 0

        assert result.input_token_count == 350
        assert result.output_token_count == 42
        assert result.cache_read_token_count == 280
        assert result.cache_creation_token_count == 70

        fetched = get_turn(session, result.turn_id)
        assert fetched is not None
        assert fetched.node_id == node.node_id
        assert fetched.user_input == raw_input
        assert fetched.assistant_output == fake_prose
        assert fetched.intent_classification == IntentType.IN_CHARACTER_ACTION
        assert fetched.timestamp is not None

        assert fetched.intent_classification_result is not None
        assert isinstance(
            fetched.intent_classification_result, IntentClassificationResult
        )
        assert (
            fetched.intent_classification_result.intent_type
            == IntentType.IN_CHARACTER_ACTION
        )
        assert abs(fetched.intent_classification_result.confidence - 0.93) < 1e-6
        assert fetched.intent_classification_result.raw_input == raw_input

    def test_fake_caller_received_rendered_payload(
        self,
        session,
        seeded_story,
        seeded_bible,
        context_builder,
    ) -> None:
        """The fake adapter receives a properly structured ProviderCallRequest."""
        story, node = seeded_story
        raw_input = "Look around."
        icr = _make_branching_icr(raw_input)

        stable_prefix = context_builder.build_stable_prefix(
            story_id=story.story_id,
            mode=StoryMode.BRANCHING,
            intent_classification=icr,
        )
        volatile_suffix = context_builder.build_volatile_suffix(
            story_id=story.story_id,
            raw_input=raw_input,
            intent_classification=icr,
        )

        from afterworlds.models.context import AssembledContext, PassForwardLedger

        assembled = AssembledContext(
            stable_prefix=stable_prefix,
            volatile_suffix=volatile_suffix,
            pass_forward_ledger=PassForwardLedger(),
        )

        adapter = _FakeAdapter()
        config = WriterConfig(
            model="claude-sonnet-4-5",
            api_key_env="ANTHROPIC_API_KEY",
            extended_ttl=True,
        )
        service = WriterService(session, config)
        service.write(assembled, story.story_id, node.node_id, provider=adapter)  # type: ignore[arg-type]

        assert len(adapter.captured) == 1
        request = adapter.captured[0]

        assert request.pass_id == PipelinePassId.WRITER
        assert len(request.system_blocks) >= 1

        cached_blocks = [b for b in request.rendered_blocks if b.has_cache_breakpoint]
        assert len(cached_blocks) == 1
        assert cached_blocks[0].ttl == "1h"
