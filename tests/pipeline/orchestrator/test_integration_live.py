"""Opt-in live-provider end-to-end orchestrator test — CRD Issue 12c.

Confirms one real Branching-mode turn travels through every pass and
returns ``DELIVERED``.  Provider/platform cache-hit verification is
explicitly NOT a 12c acceptance gate — Issue 14 owns adapter-level
checks.  This test only proves the wiring works end-to-end against the
real providers each pass currently selects:

  - Planner / Contradiction / Safety — Haiku
  - Writer / Extractor — Sonnet

Requires ``AFTERWORLDS_LIVE_TESTS=1`` and a valid ``ANTHROPIC_API_KEY``.
Not run in default CI.  Run manually or in a dedicated live-test job::

    AFTERWORLDS_LIVE_TESTS=1 pytest tests/pipeline/orchestrator/
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import pytest

# Ensure ORM models register before the in-memory engine creates tables.
import afterworlds.persistence.orm.character_sheet  # noqa: F401
import afterworlds.persistence.orm.node  # noqa: F401
import afterworlds.persistence.orm.rules_package  # noqa: F401
import afterworlds.persistence.orm.session_state  # noqa: F401
import afterworlds.persistence.orm.state  # noqa: F401
import afterworlds.persistence.orm.story  # noqa: F401
import afterworlds.persistence.orm.story_bible  # noqa: F401
from afterworlds.models.enums import IntentType, StoryMode
from afterworlds.models.node import (
    BranchingNodeMetadata,
    Node,
    NodeMetadata,
    StateDelta,
)
from afterworlds.models.story import Arc, Chapter, Story
from afterworlds.persistence.crud.node import create_node
from afterworlds.persistence.crud.story import create_arc, create_chapter, create_story
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.persistence.orm.base import Base
from afterworlds.pipeline.contradiction.service import ContradictionService
from afterworlds.pipeline.extractor.service import ExtractorService
from afterworlds.pipeline.orchestrator import (
    OrchestratorService,
    PipelineDisposition,
    SafetyPolicy,
)
from afterworlds.pipeline.planner.service import PlannerService
from afterworlds.pipeline.safety.service import SafetyService
from afterworlds.pipeline.writer.service import WriterService
from afterworlds.services.context_builder import (
    ContextBuilderService,
    NullRetrievalMemoryProvider,
    SQLiteRecentTurnsProvider,
)
from afterworlds.services.intent_classifier import IntentClassifierService
from afterworlds.services.rolling_summary import RollingSummaryService
from afterworlds.services.story_bible import StoryBibleService

pytestmark = pytest.mark.skipif(
    os.environ.get("AFTERWORLDS_LIVE_TESTS") != "1",
    reason="Set AFTERWORLDS_LIVE_TESTS=1 to run live provider tests",
)


def _seed(session_factory) -> tuple[UUID, UUID, Any]:  # type: ignore[no-untyped-def]
    session = session_factory()
    now = datetime(2026, 1, 1, tzinfo=UTC)
    story = Story(
        title="Live orchestrator test",
        mode=StoryMode.BRANCHING,
        created_at=now,
        updated_at=now,
    )
    create_story(session, story)
    arc = Arc(story_id=story.story_id, title="Arc 1", order=0)
    create_arc(session, arc)
    chapter = Chapter(arc_id=arc.arc_id, title="Chapter 1", order=0)
    create_chapter(session, chapter)
    node = Node(
        chapter_id=chapter.chapter_id,
        content="",
        state_delta=StateDelta(),
        branching_logic=[],
        intent_type=IntentType.IN_CHARACTER_ACTION,
        metadata=NodeMetadata(timestamp=now),
        mode_metadata=BranchingNodeMetadata(),
    )
    create_node(session, node)
    session.commit()
    return story.story_id, node.node_id, session


def _stub_intent_classifier() -> IntentClassifierService:
    def classifier(prompt: str) -> str:
        # The orchestrator's intent classifier expects a JSON object as a
        # string.  Use a deterministic neutral classification so we are not
        # exercising the live classifier API; that path is covered by the
        # Issue 7 live tests.
        return (
            '{"intent_type": "in_character_action", "confidence": 0.95,'
            ' "ambiguous": false, "secondary_intent": null}'
        )

    return IntentClassifierService(classifier)


def test_live_branching_orchestration_returns_delivered() -> None:
    assert os.environ.get("ANTHROPIC_API_KEY"), "ANTHROPIC_API_KEY required"

    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    session_factory = create_session_factory(engine)

    story_id, node_id, seed_session = _seed(session_factory)

    sbs_session = session_factory()
    story_bible = StoryBibleService(sbs_session)
    rolling = RollingSummaryService(sbs_session, lambda prompt: "stub summary")
    context_builder = ContextBuilderService(
        story_bible_service=story_bible,
        rolling_summary_service=rolling,
        recent_turns_provider=SQLiteRecentTurnsProvider(sbs_session),
        retrieval_memory=NullRetrievalMemoryProvider(),
    )

    writer_session = session_factory()
    extractor_session = session_factory()
    extractor_sbs = StoryBibleService(extractor_session)

    orch = OrchestratorService(
        intent_classifier=_stub_intent_classifier(),
        context_builder=context_builder,
        safety_service=SafetyService(),
        planner_service=PlannerService(),
        writer_service=WriterService(session=writer_session),
        extractor_service=ExtractorService(extractor_session, extractor_sbs),
        contradiction_service=ContradictionService(),
        session_factory=session_factory,
        safety_policy=SafetyPolicy(),
    )

    result = orch.orchestrate_turn(
        story_id,
        node_id,
        "I push the heavy oak door open and step into the courtyard.",
    )

    # Acceptance criterion #21: opt-in live-provider test passes on its
    # gate.  Provider/platform cache-hit metrics may be observed via the
    # embedded pass results but are NOT asserted here — Issue 14 owns
    # adapter-level cache verification.
    assert result.disposition is PipelineDisposition.DELIVERED, (
        f"Unexpected disposition: {result.disposition}; "
        f"summary={result.pipeline_error_summary}; refusal={result.provider_refusal}"
    )
    assert result.delivered_output
    assert result.turn_id is not None
    assert result.planner_result is not None
    assert result.writer_result is not None
    assert result.extractor_result is not None
    assert result.contradiction_result is not None

    # Cleanup
    for s in (seed_session, sbs_session, writer_session, extractor_session):
        s.close()
    Base.metadata.drop_all(engine)
    engine.dispose()
