"""Opt-in live-provider integration test — CRD Issue 9.

Targets the real Anthropic Messages API.  This test is gated behind an
explicit environment variable (``AFTERWORLDS_LIVE_PROVIDER_TESTS=1``) and
requires a valid Anthropic API key in ``ANTHROPIC_API_KEY``.

Gate mechanism
--------------
Set ``AFTERWORLDS_LIVE_PROVIDER_TESTS=1`` and ``ANTHROPIC_API_KEY=<key>``
before running:

    AFTERWORLDS_LIVE_PROVIDER_TESTS=1 ANTHROPIC_API_KEY=sk-... \
        pytest tests/pipeline/writer/test_integration_live.py -v

This test is intentionally excluded from the default CI path because:
  - It makes real API calls that cost real money.
  - Provider availability may introduce flakes into every-commit CI.

Intended use cases:
  - Local runs during development to validate the live path.
  - Periodic scheduled CI runs (not on every commit).
"""

from __future__ import annotations

import os
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
from afterworlds.models.context import AssembledContext, PassForwardLedger
from afterworlds.models.enums import CastRole, IntentType, StoryMode
from afterworlds.models.intent_classification import IntentClassificationResult
from afterworlds.models.node import Node
from afterworlds.models.story import Arc, Chapter, Story
from afterworlds.models.story_bible import CastEntry, StoryBibleSetting
from afterworlds.persistence.crud.node import create_node, get_turn
from afterworlds.persistence.crud.story import create_arc, create_chapter, create_story
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.persistence.orm.base import Base
from afterworlds.pipeline.provider.adapters._anthropic import AnthropicDirectAdapter
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

# ---------------------------------------------------------------------------
# Gate: skip unless opt-in flag is set
# ---------------------------------------------------------------------------

pytestmark = pytest.mark.skipif(
    os.environ.get("AFTERWORLDS_LIVE_PROVIDER_TESTS", "0") != "1",
    reason=(
        "Live provider tests are opt-in.  "
        "Set AFTERWORLDS_LIVE_PROVIDER_TESTS=1 and ANTHROPIC_API_KEY=<key> to run."
    ),
)


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


class TestLiveProviderIntegration:
    def test_write_real_provider_round_trip(self, session) -> None:  # type: ignore[no-untyped-def]
        """Full round-trip against the real Anthropic API.

        Requires AFTERWORLDS_LIVE_PROVIDER_TESTS=1 and ANTHROPIC_API_KEY.
        """
        now = datetime(2026, 1, 1, tzinfo=UTC)
        story = Story(
            title="Live Test Story",
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

        bible_service = StoryBibleService(session)
        bible_service.create_setting(
            story.story_id,
            StoryBibleSetting(
                story_id=story.story_id,
                summary="A mysterious forest at the edge of the world.",
                world_rules=("Time moves strangely here",),
                created_at=now,
            ),
        )
        bible_service.add_cast_entry(
            story.story_id,
            CastEntry(
                story_id=story.story_id,
                name="Lyra",
                role=CastRole.PROTAGONIST,
                background="A traveller seeking answers.",
                created_at=now,
            ),
        )
        session.commit()

        rolling_service = RollingSummaryService(session, lambda _existing, _turns: "")
        context_builder = ContextBuilderService(
            story_bible_service=bible_service,
            rolling_summary_service=rolling_service,
            recent_turns_provider=SQLiteRecentTurnsProvider(session),
            retrieval_memory=NullRetrievalMemoryProvider(),
        )

        raw_input = "Lyra steps into the forest, lantern raised."
        icr = IntentClassificationResult(
            intent_type=IntentType.IN_CHARACTER_ACTION,
            confidence=0.95,
            raw_input=raw_input,
            ambiguous=False,
        )

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
        assembled = AssembledContext(
            stable_prefix=stable_prefix,
            volatile_suffix=volatile_suffix,
            pass_forward_ledger=PassForwardLedger(),
        )

        config = WriterConfig.from_env()
        service = WriterService(session, config)
        adapter = AnthropicDirectAdapter(api_key=os.environ["ANTHROPIC_API_KEY"])

        result = service.write(
            built_context=assembled,
            story_id=story.story_id,
            node_id=node.node_id,
            provider=adapter,
        )

        assert isinstance(result, WriterResult)
        assert len(result.assistant_output) > 0
        assert result.turn_id is not None

        fetched = get_turn(session, result.turn_id)
        assert fetched is not None
        assert fetched.node_id == node.node_id
        assert len(fetched.assistant_output) > 0
        assert fetched.user_input == raw_input
        assert fetched.intent_classification_result is not None
