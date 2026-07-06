"""Tests for RetrievalQueryBuilder — CRD Issue 18 / ADR-018 D8.

The critical obligation: a test must fail if ``exclude_ooc=True`` alone is
treated as sufficient for the retrieval-query tail. A fixture with a
non-OOC, D6-ineligible support turn in the recent window must prove that
turn's text is absent from the composed query.

Turns are persisted (not just held in-memory) because the query builder
reloads full committed turn state before deciding Writing eligibility
(Codex #119 P2: a production recent-turn provider may return a lean Turn
projection without ``mode_metadata``, which must not be mistaken for a
missing/malformed-metadata turn).
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from afterworlds.models.enums import IntentType, StoryMode, WritingCanonEligibility
from afterworlds.models.intent_classification import IntentClassificationResult
from afterworlds.models.node import (
    BranchingNodeMetadata,
    Node,
    NodeMetadata,
    StateDelta,
    WritingNodeMetadata,
)
from afterworlds.models.turn import Turn
from afterworlds.persistence.crud.node import create_node, create_turn
from afterworlds.persistence.crud.story import create_arc, create_chapter, create_story
from afterworlds.persistence.database import create_session_factory
from afterworlds.pipeline.retrieval.query_builder import RetrievalQueryBuilder
from afterworlds.services.context_builder import SQLiteRecentTurnsProvider
from tests.persistence.conftest import make_arc, make_chapter, make_story

_NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _make_classified_intent(
    intent: IntentType = IntentType.IN_CHARACTER_ACTION,
    raw_input: str = "test input",
) -> IntentClassificationResult:
    return IntentClassificationResult(
        intent_type=intent,
        confidence=0.95,
        raw_input=raw_input,
        ambiguous=False,
        secondary_intent=None,
    )


class _FakeRecentTurnsProvider:
    """Mimics RecentTurnsProvider: already excludes OOC via exclude_ooc=True."""

    def __init__(self, turns: list[Turn]) -> None:
        self._turns = turns

    def get_recent_turns(
        self, story_id: object, limit: int, *, exclude_ooc: bool = True
    ) -> list[Turn]:
        turns = self._turns
        if exclude_ooc:
            turns = [t for t in turns if t.intent_classification is not IntentType.OOC]
        return turns[-limit:]


def _persist_turn(
    session: Session, assistant_output: str, mode_metadata: object = None
) -> Turn:
    """Persist a committed Turn (node_id omitted — nullable, no FK needed
    for these tests) so eligibility reload sees real SQLite state."""
    turn = Turn(
        user_input="prior input",
        assistant_output=assistant_output,
        timestamp=_NOW,
        intent_classification=IntentType.DIALOGUE,
        mode_metadata=mode_metadata,  # type: ignore[arg-type]
    )
    return create_turn(session, turn)  # type: ignore[arg-type]


@pytest.fixture()
def session_factory(engine):  # type: ignore[no-untyped-def]
    return create_session_factory(engine)


class TestQueryTailEligibilityFiltering:
    def test_exclude_ooc_alone_is_not_sufficient(self, session_factory) -> None:  # type: ignore[no-untyped-def]
        session = session_factory()
        non_canon_metadata = WritingNodeMetadata(
            canon_eligibility=WritingCanonEligibility.NON_CANON_SUPPORT.value
        )
        extractor_eligible_metadata = WritingNodeMetadata(
            canon_eligibility=WritingCanonEligibility.EXTRACTOR_ELIGIBLE.value
        )
        support_turn = _persist_turn(
            session,
            "Let's brainstorm some names for the antagonist.",
            non_canon_metadata,
        )
        canon_turn = _persist_turn(
            session,
            "Kestrel drew her blade in the moonlight.",
            extractor_eligible_metadata,
        )
        session.commit()
        provider = _FakeRecentTurnsProvider([support_turn, canon_turn])
        builder = RetrievalQueryBuilder(provider, session_factory, tail_window=3)

        request = builder.build_query_request(
            uuid4(), "What happens next?", StoryMode.WRITING, _make_classified_intent()
        )

        assert "brainstorm" not in request.query_text
        assert "Kestrel drew her blade" in request.query_text
        assert "What happens next?" in request.query_text

    def test_no_eligible_tail_turns_falls_back_to_current_input_only(
        self, session_factory
    ) -> None:  # type: ignore[no-untyped-def]
        session = session_factory()
        non_canon_metadata = WritingNodeMetadata(
            canon_eligibility=WritingCanonEligibility.NON_CANON_SUPPORT.value
        )
        support_turn = _persist_turn(session, "config chatter", non_canon_metadata)
        session.commit()
        provider = _FakeRecentTurnsProvider([support_turn])
        builder = RetrievalQueryBuilder(provider, session_factory)

        request = builder.build_query_request(
            uuid4(), "current input", StoryMode.WRITING, _make_classified_intent()
        )

        assert request.query_text == "current input\n\nintent_type=in_character_action"

    def test_empty_tail_uses_current_input_only(
        self, session_factory
    ) -> None:  # type: ignore[no-untyped-def]
        provider = _FakeRecentTurnsProvider([])
        builder = RetrievalQueryBuilder(provider, session_factory)

        request = builder.build_query_request(
            uuid4(), "current input", StoryMode.BRANCHING, _make_classified_intent()
        )

        assert request.query_text == "current input\n\nintent_type=in_character_action"

    def test_branching_tail_turns_are_eligible_by_default(
        self, session_factory
    ) -> None:  # type: ignore[no-untyped-def]
        session = session_factory()
        turn = _persist_turn(session, "The party chooses the left path.")
        session.commit()
        provider = _FakeRecentTurnsProvider([turn])
        builder = RetrievalQueryBuilder(provider, session_factory)

        request = builder.build_query_request(
            uuid4(), "current input", StoryMode.BRANCHING, _make_classified_intent()
        )

        assert "The party chooses the left path." in request.query_text


class TestQueryTailWithProductionRecentTurnsProvider:
    """Codex #119 P2: the fake provider above always carries in-memory
    mode_metadata, which masked a bug that only shows up with a real
    projection. ``SQLiteRecentTurnsProvider`` returns a lean ``Turn`` with no
    ``mode_metadata`` set (see ``_orm_turn_to_model``); the query builder
    must reload full committed state before deciding Writing eligibility
    rather than trusting that projection."""

    def _seed_writing_story(
        self, session: Session
    ) -> tuple[object, object]:  # -> (story_id, node_id)
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
        return story.story_id, node.node_id

    def _persist_writing_turn(
        self,
        session: Session,
        node_id: object,
        assistant_output: str,
        mode_metadata: object,
        intent: IntentType = IntentType.DIALOGUE,
    ) -> None:
        turn = Turn(
            user_input="prior input",
            assistant_output=assistant_output,
            timestamp=_NOW,
            intent_classification=intent,
            node_id=node_id,  # type: ignore[arg-type]
            mode_metadata=mode_metadata,  # type: ignore[arg-type]
        )
        create_turn(session, turn)  # type: ignore[arg-type]

    def _persist_malformed_writing_turn(
        self, session: Session, node_id: object, assistant_output: str
    ) -> None:
        """Insert a Turn row whose mode_metadata JSON fails ModeMetadata
        validation -- bypasses create_turn()'s pydantic validation to
        simulate a corrupted/schema-drifted committed row (Codex #119 P2)."""
        from afterworlds.persistence.orm.node import TurnORM

        session.add(
            TurnORM(
                turn_id=str(uuid4()),
                node_id=str(node_id),
                user_input="prior input",
                assistant_output=assistant_output,
                timestamp=_NOW.isoformat(),
                intent_classification=IntentType.DIALOGUE.value,
                mode_metadata={"mode": "writing", "persona_registry_version": "bad"},
            )
        )

    def test_extractor_eligible_prose_turn_appears_in_query_tail(
        self, session_factory
    ) -> None:  # type: ignore[no-untyped-def]
        session = session_factory()
        story_id, node_id = self._seed_writing_story(session)
        extractor_eligible_metadata = WritingNodeMetadata(
            canon_eligibility=WritingCanonEligibility.EXTRACTOR_ELIGIBLE.value
        )
        self._persist_writing_turn(
            session,
            node_id,
            "Kestrel drew her blade in the moonlight.",
            extractor_eligible_metadata,
        )
        session.commit()

        provider = SQLiteRecentTurnsProvider(session)
        builder = RetrievalQueryBuilder(provider, session_factory, tail_window=3)

        request = builder.build_query_request(
            story_id,  # type: ignore[arg-type]
            "What happens next?",
            StoryMode.WRITING,
            _make_classified_intent(),
        )

        assert "Kestrel drew her blade" in request.query_text

    def test_non_canon_support_turn_does_not_appear_in_query_tail(
        self, session_factory
    ) -> None:  # type: ignore[no-untyped-def]
        session = session_factory()
        story_id, node_id = self._seed_writing_story(session)
        non_canon_metadata = WritingNodeMetadata(
            canon_eligibility=WritingCanonEligibility.NON_CANON_SUPPORT.value
        )
        self._persist_writing_turn(
            session,
            node_id,
            "Let's brainstorm some antagonist names.",
            non_canon_metadata,
        )
        session.commit()

        provider = SQLiteRecentTurnsProvider(session)
        builder = RetrievalQueryBuilder(provider, session_factory, tail_window=3)

        request = builder.build_query_request(
            story_id,  # type: ignore[arg-type]
            "What happens next?",
            StoryMode.WRITING,
            _make_classified_intent(),
        )

        assert "brainstorm" not in request.query_text
        assert (
            request.query_text
            == "What happens next?\n\nintent_type=in_character_action"
        )

    def test_ooc_turn_does_not_leak_into_query_tail(
        self, session_factory
    ) -> None:  # type: ignore[no-untyped-def]
        session = session_factory()
        story_id, node_id = self._seed_writing_story(session)
        extractor_eligible_metadata = WritingNodeMetadata(
            canon_eligibility=WritingCanonEligibility.EXTRACTOR_ELIGIBLE.value
        )
        self._persist_writing_turn(
            session,
            node_id,
            "Is this story going to have a sequel?",
            extractor_eligible_metadata,
            intent=IntentType.OOC,
        )
        session.commit()

        provider = SQLiteRecentTurnsProvider(session)
        builder = RetrievalQueryBuilder(provider, session_factory, tail_window=3)

        request = builder.build_query_request(
            story_id,  # type: ignore[arg-type]
            "What happens next?",
            StoryMode.WRITING,
            _make_classified_intent(),
        )

        assert "sequel" not in request.query_text
        assert (
            request.query_text
            == "What happens next?\n\nintent_type=in_character_action"
        )

    def test_mixed_tail_only_extractor_eligible_survives(
        self, session_factory
    ) -> None:  # type: ignore[no-untyped-def]
        """Regression proof for the exact Codex #119 defect: with the real
        SQLite-backed provider, an EXTRACTOR_ELIGIBLE turn must survive
        alongside an excluded NON_CANON_SUPPORT turn and an excluded OOC
        turn in the same tail window."""
        session = session_factory()
        story_id, node_id = self._seed_writing_story(session)
        extractor_eligible_metadata = WritingNodeMetadata(
            canon_eligibility=WritingCanonEligibility.EXTRACTOR_ELIGIBLE.value
        )
        non_canon_metadata = WritingNodeMetadata(
            canon_eligibility=WritingCanonEligibility.NON_CANON_SUPPORT.value
        )
        self._persist_writing_turn(
            session,
            node_id,
            "Let's brainstorm some antagonist names.",
            non_canon_metadata,
        )
        self._persist_writing_turn(
            session,
            node_id,
            "Is this story going to have a sequel?",
            extractor_eligible_metadata,
            intent=IntentType.OOC,
        )
        self._persist_writing_turn(
            session,
            node_id,
            "Kestrel drew her blade in the moonlight.",
            extractor_eligible_metadata,
        )
        session.commit()

        provider = SQLiteRecentTurnsProvider(session)
        builder = RetrievalQueryBuilder(provider, session_factory, tail_window=3)

        request = builder.build_query_request(
            story_id,  # type: ignore[arg-type]
            "What happens next?",
            StoryMode.WRITING,
            _make_classified_intent(),
        )

        assert "Kestrel drew her blade" in request.query_text
        assert "brainstorm" not in request.query_text
        assert "sequel" not in request.query_text

    def test_malformed_writing_metadata_turn_is_skipped_not_aborting(
        self, session_factory
    ) -> None:  # type: ignore[no-untyped-def]
        """Codex review (PR #119): a malformed-metadata Writing turn in the
        tail window must not abort query composition -- it is simply
        excluded, and the query still builds from the other eligible tail
        turn plus current input."""
        session = session_factory()
        story_id, node_id = self._seed_writing_story(session)
        extractor_eligible_metadata = WritingNodeMetadata(
            canon_eligibility=WritingCanonEligibility.EXTRACTOR_ELIGIBLE.value
        )
        self._persist_malformed_writing_turn(
            session, node_id, "This turn has corrupted metadata."
        )
        self._persist_writing_turn(
            session,
            node_id,
            "Kestrel drew her blade in the moonlight.",
            extractor_eligible_metadata,
        )
        session.commit()

        provider = SQLiteRecentTurnsProvider(session)
        builder = RetrievalQueryBuilder(provider, session_factory, tail_window=3)

        request = builder.build_query_request(
            story_id,  # type: ignore[arg-type]
            "What happens next?",
            StoryMode.WRITING,
            _make_classified_intent(),
        )

        assert "Kestrel drew her blade" in request.query_text
        assert "corrupted metadata" not in request.query_text
        assert "What happens next?" in request.query_text


class TestClassifiedIntentInQueryText:
    """Codex review (PR #119) round 4: ADR-018 D8 requires query text to be
    composed from current input AND classified intent, not current input
    alone. RetrievalQueryBuilder previously never received/used intent at
    all."""

    def test_build_query_request_includes_classified_intent(
        self, session_factory
    ) -> None:  # type: ignore[no-untyped-def]
        provider = _FakeRecentTurnsProvider([])
        builder = RetrievalQueryBuilder(provider, session_factory)

        request = builder.build_query_request(
            uuid4(),
            "current input",
            StoryMode.BRANCHING,
            _make_classified_intent(intent=IntentType.DIALOGUE),
        )

        assert "intent_type=dialogue" in request.query_text

    def test_different_intents_produce_distinguishable_query_text(
        self, session_factory
    ) -> None:  # type: ignore[no-untyped-def]
        provider = _FakeRecentTurnsProvider([])
        builder = RetrievalQueryBuilder(provider, session_factory)

        request_a = builder.build_query_request(
            uuid4(),
            "current input",
            StoryMode.BRANCHING,
            _make_classified_intent(intent=IntentType.DIALOGUE),
        )
        request_b = builder.build_query_request(
            uuid4(),
            "current input",
            StoryMode.BRANCHING,
            _make_classified_intent(intent=IntentType.IN_CHARACTER_ACTION),
        )

        assert request_a.query_text != request_b.query_text
        assert "intent_type=dialogue" in request_a.query_text
        assert "intent_type=in_character_action" in request_b.query_text

    def test_tail_eligibility_behavior_unaffected_by_intent_fragment(
        self, session_factory
    ) -> None:  # type: ignore[no-untyped-def]
        """The intent fragment is additive -- D6/D8 tail-eligibility
        filtering (eligible tail included, OOC/support tail excluded) must
        keep working exactly as before."""
        session = session_factory()
        non_canon_metadata = WritingNodeMetadata(
            canon_eligibility=WritingCanonEligibility.NON_CANON_SUPPORT.value
        )
        extractor_eligible_metadata = WritingNodeMetadata(
            canon_eligibility=WritingCanonEligibility.EXTRACTOR_ELIGIBLE.value
        )
        support_turn = _persist_turn(
            session, "Let's brainstorm names.", non_canon_metadata
        )
        canon_turn = _persist_turn(
            session, "Kestrel drew her blade.", extractor_eligible_metadata
        )
        session.commit()
        provider = _FakeRecentTurnsProvider([support_turn, canon_turn])
        builder = RetrievalQueryBuilder(provider, session_factory, tail_window=3)

        request = builder.build_query_request(
            uuid4(), "What happens next?", StoryMode.WRITING, _make_classified_intent()
        )

        assert "brainstorm" not in request.query_text
        assert "Kestrel drew her blade" in request.query_text
        assert "intent_type=in_character_action" in request.query_text
