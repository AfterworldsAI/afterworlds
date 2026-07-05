"""Tests for RetrievalQueryBuilder — CRD Issue 18 / ADR-018 D8.

The critical obligation: a test must fail if ``exclude_ooc=True`` alone is
treated as sufficient for the retrieval-query tail. A fixture with a
non-OOC, D6-ineligible support turn in the recent window must prove that
turn's text is absent from the composed query.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from afterworlds.models.enums import IntentType, StoryMode, WritingCanonEligibility
from afterworlds.models.node import WritingNodeMetadata
from afterworlds.models.turn import Turn
from afterworlds.persistence.database import create_session_factory
from afterworlds.pipeline.retrieval.query_builder import RetrievalQueryBuilder

_NOW = datetime(2026, 1, 1, tzinfo=UTC)


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


def _make_turn(assistant_output: str, mode_metadata: object = None) -> Turn:
    return Turn(
        user_input="prior input",
        assistant_output=assistant_output,
        timestamp=_NOW,
        intent_classification=IntentType.DIALOGUE,
        mode_metadata=mode_metadata,  # type: ignore[arg-type]
    )


@pytest.fixture()
def session_factory(engine):  # type: ignore[no-untyped-def]
    return create_session_factory(engine)


class TestQueryTailEligibilityFiltering:
    def test_exclude_ooc_alone_is_not_sufficient(self, session_factory) -> None:  # type: ignore[no-untyped-def]
        non_canon_metadata = WritingNodeMetadata(
            canon_eligibility=WritingCanonEligibility.NON_CANON_SUPPORT.value
        )
        extractor_eligible_metadata = WritingNodeMetadata(
            canon_eligibility=WritingCanonEligibility.EXTRACTOR_ELIGIBLE.value
        )
        support_turn = _make_turn(
            "Let's brainstorm some names for the antagonist.", non_canon_metadata
        )
        canon_turn = _make_turn(
            "Kestrel drew her blade in the moonlight.", extractor_eligible_metadata
        )
        provider = _FakeRecentTurnsProvider([support_turn, canon_turn])
        builder = RetrievalQueryBuilder(provider, session_factory, tail_window=3)

        request = builder.build_query_request(
            uuid4(), "What happens next?", StoryMode.WRITING
        )

        assert "brainstorm" not in request.query_text
        assert "Kestrel drew her blade" in request.query_text
        assert "What happens next?" in request.query_text

    def test_no_eligible_tail_turns_falls_back_to_current_input_only(
        self, session_factory
    ) -> None:  # type: ignore[no-untyped-def]
        non_canon_metadata = WritingNodeMetadata(
            canon_eligibility=WritingCanonEligibility.NON_CANON_SUPPORT.value
        )
        support_turn = _make_turn("config chatter", non_canon_metadata)
        provider = _FakeRecentTurnsProvider([support_turn])
        builder = RetrievalQueryBuilder(provider, session_factory)

        request = builder.build_query_request(
            uuid4(), "current input", StoryMode.WRITING
        )

        assert request.query_text == "current input"

    def test_empty_tail_uses_current_input_only(
        self, session_factory
    ) -> None:  # type: ignore[no-untyped-def]
        provider = _FakeRecentTurnsProvider([])
        builder = RetrievalQueryBuilder(provider, session_factory)

        request = builder.build_query_request(
            uuid4(), "current input", StoryMode.WRITING
        )

        assert request.query_text == "current input"

    def test_branching_tail_turns_are_eligible_by_default(
        self, session_factory
    ) -> None:  # type: ignore[no-untyped-def]
        turn = _make_turn("The party chooses the left path.")
        provider = _FakeRecentTurnsProvider([turn])
        builder = RetrievalQueryBuilder(provider, session_factory)

        request = builder.build_query_request(
            uuid4(), "current input", StoryMode.BRANCHING
        )

        assert "The party chooses the left path." in request.query_text
