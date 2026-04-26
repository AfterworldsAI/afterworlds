"""Unit tests for ExtractorService — CRD Issue 10.

Coverage targets (from the Issue 10 test requirements):

Classification routing — one test per proposal category:
  - test_locked_fact_staged_pending
  - test_soft_fact_auto_ratified
  - test_transient_state_auto_ratified
  - test_unresolved_thread_creates_thread_row
  - test_event_creates_event_row

Direct-write prevention (architectural invariant — CRD Item 12):
  - test_all_proposals_staged_before_canon_is_touched

Auto-commit behaviour:
  - test_soft_fact_applied_to_cast_dynamic_field
  - test_transient_state_applied_to_cast_dynamic_field
  - test_unresolvable_character_name_still_ratifies_proposal
  - test_empty_tool_response_produces_empty_result

Pass-forward content:
  - test_pass_forward_mentions_pending_locked_fact
  - test_pass_forward_mentions_auto_committed_event
  - test_pass_forward_empty_when_no_proposals

Token metrics:
  - test_token_metrics_propagated
  - test_cache_metrics_none_when_not_reported

Error handling:
  - test_provider_exception_raises_extractor_pass_error
  - test_no_tool_use_block_raises_extractor_pass_error
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import pytest
from anthropic.types import Message, TextBlock, ToolUseBlock, Usage

import afterworlds.persistence.orm.character_sheet  # noqa: F401
import afterworlds.persistence.orm.node  # noqa: F401
import afterworlds.persistence.orm.rules_package  # noqa: F401
import afterworlds.persistence.orm.session_state  # noqa: F401
import afterworlds.persistence.orm.state  # noqa: F401
import afterworlds.persistence.orm.story  # noqa: F401
import afterworlds.persistence.orm.story_bible  # noqa: F401
from afterworlds.models.context import (
    AssembledContext,
    PassForwardLedger,
    RetrievalMemoryPayload,
    StablePrefix,
    VolatileSuffix,
)
from afterworlds.models.enums import (
    CastRole,
    IntentType,
    ProposalStatus,
    ProposalType,
    StoryMode,
)
from afterworlds.models.intent_classification import IntentClassificationResult
from afterworlds.models.story import Arc, Chapter, Story
from afterworlds.models.story_bible import CastEntry, StoryBibleContext
from afterworlds.persistence.crud.node import create_node
from afterworlds.persistence.crud.story import create_arc, create_chapter, create_story
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.persistence.orm.base import Base
from afterworlds.persistence.orm.story_bible import (
    SBEventORM,
    SBProvisionalStagingORM,
    SBUnresolvedThreadORM,
)
from afterworlds.pipeline.extractor.caller import EXTRACT_TOOL_NAME, ExtractorPayload
from afterworlds.pipeline.extractor.config import ExtractorConfig
from afterworlds.pipeline.extractor.models import ExtractorPassError, ExtractorResult
from afterworlds.pipeline.extractor.service import ExtractorService
from afterworlds.services.story_bible import StoryBibleService

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


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
def story_and_cast(session):  # type: ignore[no-untyped-def]
    """Seed a Story + Arc + Chapter + Node + cast entry; return (story_id, cast_id)."""
    from afterworlds.models.node import Node

    now = datetime(2026, 1, 1, tzinfo=UTC)
    story = Story(
        title="Extractor Test Story",
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

    sbs = StoryBibleService(session)
    cast_entry = CastEntry(
        story_id=story.story_id,
        name="Aldric",
        role=CastRole.PROTAGONIST,
        current_location="The Crossroads Inn",
        created_at=now,
    )
    saved = sbs.add_cast_entry(story.story_id, cast_entry)
    session.commit()

    return story.story_id, saved.cast_id


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_config() -> ExtractorConfig:
    return ExtractorConfig(
        model="claude-haiku-test",
        api_key_env="ANTHROPIC_API_KEY",
        extended_ttl=True,
    )


def _make_assembled(story_id: UUID, cast_id: UUID | None = None) -> AssembledContext:
    cast: tuple[CastEntry, ...] = ()
    if cast_id is not None:
        cast = (
            CastEntry(
                cast_id=cast_id,
                story_id=story_id,
                name="Aldric",
                role=CastRole.PROTAGONIST,
                current_location="The Crossroads Inn",
                created_at=datetime(2026, 1, 1, tzinfo=UTC),
            ),
        )
    ctx = StoryBibleContext(
        story_id=story_id,
        setting=None,
        cast=cast,
        locked_facts=(),
        forbidden_facts=(),
        relationship_ledger=(),
        active_plot_threads=(),
        events=(),
    )
    sp = StablePrefix(
        system_prompt="You are the story architect.",
        story_bible_context=ctx,
        rolling_summary_text=None,
        rules_package_slice=None,
        retrieval_memory=RetrievalMemoryPayload(),
    )
    icr = IntentClassificationResult(
        intent_type=IntentType.IN_CHARACTER_ACTION,
        confidence=0.90,
        raw_input="I push open the door.",
        ambiguous=False,
    )
    vs = VolatileSuffix(
        recent_turns=[],
        current_input="I push open the door.",
        classified_intent=icr,
    )
    return AssembledContext(
        stable_prefix=sp,
        volatile_suffix=vs,
        pass_forward_ledger=PassForwardLedger(),
    )


def _fake_tool_response(
    tool_input: dict[str, Any] | None = None,
    input_tokens: int = 100,
    output_tokens: int = 50,
    cache_read_input_tokens: int | None = None,
    cache_creation_input_tokens: int | None = None,
) -> Message:
    return Message(
        id="msg_fake_extractor",
        type="message",
        role="assistant",
        content=[
            ToolUseBlock(
                type="tool_use",
                id="toolu_fake_01",
                name=EXTRACT_TOOL_NAME,
                input=tool_input if tool_input is not None else {},
            )
        ],
        model="claude-haiku-4-5-20251001",
        stop_reason="tool_use",
        stop_sequence=None,
        usage=Usage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_read_input_tokens=cache_read_input_tokens,
            cache_creation_input_tokens=cache_creation_input_tokens,
        ),
    )


def _make_fake_caller(  # type: ignore[no-untyped-def]
    response: Message | None = None,
    raise_exc: Exception | None = None,
):
    captured: list[ExtractorPayload] = []

    def caller(payload: ExtractorPayload) -> Message:
        captured.append(payload)
        if raise_exc is not None:
            raise raise_exc
        return response or _fake_tool_response()

    caller.captured = captured  # type: ignore[attr-defined]
    return caller


# ---------------------------------------------------------------------------
# Classification routing — locked facts
# ---------------------------------------------------------------------------


class TestLockedFactRouting:
    def test_locked_fact_staged_pending(  # type: ignore[no-untyped-def]
        self, session, story_and_cast
    ) -> None:
        """A locked-fact proposal is staged with PENDING status."""
        story_id, cast_id = story_and_cast
        fake = _make_fake_caller(
            _fake_tool_response(
                {"locked_facts": [{"fact_text": "The king has been assassinated."}]}
            )
        )
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config(), fake)

        result = service.extract(
            _make_assembled(story_id, cast_id), story_id, "The king falls dead."
        )

        assert len(result.pending_proposals) == 1
        proposal = result.pending_proposals[0]
        assert proposal.proposal_type == ProposalType.LOCKED_FACT
        assert proposal.status == ProposalStatus.PENDING
        assert proposal.requires_confirmation is True
        assert "king" in proposal.proposed_value.get("fact_text", "").lower()

    def test_locked_fact_not_in_auto_committed(  # type: ignore[no-untyped-def]
        self, session, story_and_cast
    ) -> None:
        """Locked-fact proposals are NOT in auto_committed."""
        story_id, cast_id = story_and_cast
        fake = _make_fake_caller(
            _fake_tool_response(
                {"locked_facts": [{"fact_text": "The keep is destroyed."}]}
            )
        )
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config(), fake)

        result = service.extract(
            _make_assembled(story_id, cast_id), story_id, "The keep crumbles."
        )

        assert not any(
            p.proposal_type == ProposalType.LOCKED_FACT for p in result.auto_committed
        )

    def test_locked_fact_remains_in_staging_area(  # type: ignore[no-untyped-def]
        self, session, story_and_cast
    ) -> None:
        """After extract(), a PENDING proposal row exists in the staging table."""
        story_id, cast_id = story_and_cast
        fake = _make_fake_caller(
            _fake_tool_response(
                {"locked_facts": [{"fact_text": "The bridge is destroyed."}]}
            )
        )
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config(), fake)

        service.extract(
            _make_assembled(story_id, cast_id), story_id, "The bridge falls."
        )

        rows = (
            session.query(SBProvisionalStagingORM)
            .filter_by(status=ProposalStatus.PENDING.value)
            .all()
        )
        assert len(rows) == 1
        assert rows[0].proposal_type == ProposalType.LOCKED_FACT.value


# ---------------------------------------------------------------------------
# Classification routing — soft facts
# ---------------------------------------------------------------------------


class TestSoftFactRouting:
    def test_soft_fact_auto_ratified(  # type: ignore[no-untyped-def]
        self, session, story_and_cast
    ) -> None:
        """A soft-fact proposal is RATIFIED."""
        story_id, cast_id = story_and_cast
        fake = _make_fake_caller(
            _fake_tool_response(
                {
                    "soft_facts": [
                        {
                            "character_name": "Aldric",
                            "field_name": "current_status",
                            "new_value": "injured",
                        }
                    ]
                }
            )
        )
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config(), fake)

        result = service.extract(
            _make_assembled(story_id, cast_id), story_id, "Aldric is cut by a blade."
        )

        assert len(result.auto_committed) == 1
        assert result.auto_committed[0].status == ProposalStatus.RATIFIED
        assert result.auto_committed[0].proposal_type == ProposalType.SOFT_FACT

    def test_soft_fact_applied_to_cast_dynamic_field(  # type: ignore[no-untyped-def]
        self, session, story_and_cast
    ) -> None:
        """A soft-fact update is applied to the cast entry's dynamic field."""
        story_id, cast_id = story_and_cast
        fake = _make_fake_caller(
            _fake_tool_response(
                {
                    "soft_facts": [
                        {
                            "character_name": "Aldric",
                            "field_name": "current_location",
                            "new_value": "The Dark Tower",
                        }
                    ]
                }
            )
        )
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config(), fake)

        service.extract(
            _make_assembled(story_id, cast_id), story_id, "Aldric enters the tower."
        )

        entry = sbs.get_character(story_id, cast_id)
        assert entry is not None
        assert entry.current_location == "The Dark Tower"

    def test_soft_fact_staged_before_field_applied(  # type: ignore[no-untyped-def]
        self, session, story_and_cast
    ) -> None:
        """Staging row exists for the soft fact (direct-write prevention invariant)."""
        story_id, cast_id = story_and_cast
        fake = _make_fake_caller(
            _fake_tool_response(
                {
                    "soft_facts": [
                        {
                            "character_name": "Aldric",
                            "field_name": "current_status",
                            "new_value": "exhausted",
                        }
                    ]
                }
            )
        )
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config(), fake)

        service.extract(
            _make_assembled(story_id, cast_id),
            story_id,
            "Aldric collapses exhausted.",
        )

        rows = (
            session.query(SBProvisionalStagingORM)
            .filter_by(
                proposal_type=ProposalType.SOFT_FACT.value,
                status=ProposalStatus.RATIFIED.value,
            )
            .all()
        )
        assert len(rows) == 1, "No staging row found — direct-write invariant violated"


# ---------------------------------------------------------------------------
# Classification routing — transient states
# ---------------------------------------------------------------------------


class TestTransientStateRouting:
    def test_transient_state_auto_ratified(  # type: ignore[no-untyped-def]
        self, session, story_and_cast
    ) -> None:
        """A transient-state proposal is RATIFIED."""
        story_id, cast_id = story_and_cast
        fake = _make_fake_caller(
            _fake_tool_response(
                {
                    "transient_states": [
                        {
                            "character_name": "Aldric",
                            "field_name": "current_location",
                            "new_value": "Forest Path",
                        }
                    ]
                }
            )
        )
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config(), fake)

        result = service.extract(
            _make_assembled(story_id, cast_id),
            story_id,
            "Aldric walks the forest path.",
        )

        assert len(result.auto_committed) == 1
        assert result.auto_committed[0].status == ProposalStatus.RATIFIED
        assert result.auto_committed[0].proposal_type == ProposalType.TRANSIENT_STATE

    def test_transient_state_applied_to_cast_dynamic_field(  # type: ignore[no-untyped-def]
        self, session, story_and_cast
    ) -> None:
        """A transient-state update is applied to the cast entry's dynamic field."""
        story_id, cast_id = story_and_cast
        fake = _make_fake_caller(
            _fake_tool_response(
                {
                    "transient_states": [
                        {
                            "character_name": "Aldric",
                            "field_name": "current_location",
                            "new_value": "The Market Square",
                        }
                    ]
                }
            )
        )
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config(), fake)

        service.extract(
            _make_assembled(story_id, cast_id),
            story_id,
            "Aldric reaches the market.",
        )

        entry = sbs.get_character(story_id, cast_id)
        assert entry is not None
        assert entry.current_location == "The Market Square"


# ---------------------------------------------------------------------------
# Classification routing — unresolved threads
# ---------------------------------------------------------------------------


class TestUnresolvedThreadRouting:
    def test_unresolved_thread_auto_ratified(  # type: ignore[no-untyped-def]
        self, session, story_and_cast
    ) -> None:
        """An unresolved-thread proposal is RATIFIED."""
        story_id, cast_id = story_and_cast
        fake = _make_fake_caller(
            _fake_tool_response(
                {
                    "unresolved_threads": [
                        {"description": "Who left the hooded figure at the inn?"}
                    ]
                }
            )
        )
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config(), fake)

        result = service.extract(
            _make_assembled(story_id, cast_id), story_id, "A hooded figure watches."
        )

        assert len(result.auto_committed) == 1
        assert result.auto_committed[0].status == ProposalStatus.RATIFIED
        assert result.auto_committed[0].proposal_type == ProposalType.UNRESOLVED_THREAD

    def test_unresolved_thread_creates_thread_row(  # type: ignore[no-untyped-def]
        self, session, story_and_cast
    ) -> None:
        """Ratifying an unresolved-thread proposal creates a thread row."""
        story_id, cast_id = story_and_cast
        fake = _make_fake_caller(
            _fake_tool_response(
                {
                    "unresolved_threads": [
                        {"description": "Where is the missing artefact hidden?"}
                    ]
                }
            )
        )
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config(), fake)

        service.extract(
            _make_assembled(story_id, cast_id), story_id, "The artefact is gone."
        )

        rows = (
            session.query(SBUnresolvedThreadORM).filter_by(story_id=str(story_id)).all()
        )
        assert len(rows) == 1
        assert "artefact" in rows[0].description.lower()


# ---------------------------------------------------------------------------
# Classification routing — events
# ---------------------------------------------------------------------------


class TestEventRouting:
    def test_event_auto_ratified(  # type: ignore[no-untyped-def]
        self, session, story_and_cast
    ) -> None:
        """An event proposal is RATIFIED."""
        story_id, cast_id = story_and_cast
        fake = _make_fake_caller(
            _fake_tool_response(
                {
                    "events": [
                        {
                            "description": "Aldric crossed the Thornbridge.",
                            "significance": "routine",
                        }
                    ]
                }
            )
        )
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config(), fake)

        result = service.extract(
            _make_assembled(story_id, cast_id),
            story_id,
            "Aldric crosses the bridge.",
        )

        assert len(result.auto_committed) == 1
        assert result.auto_committed[0].status == ProposalStatus.RATIFIED
        assert result.auto_committed[0].proposal_type == ProposalType.EVENT

    def test_event_creates_event_row(  # type: ignore[no-untyped-def]
        self, session, story_and_cast
    ) -> None:
        """Ratifying an event proposal creates a row in sb_events."""
        story_id, cast_id = story_and_cast
        fake = _make_fake_caller(
            _fake_tool_response(
                {
                    "events": [
                        {
                            "description": "Aldric slew the Night Warden.",
                            "significance": "major_plot_turn",
                        }
                    ]
                }
            )
        )
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config(), fake)

        service.extract(
            _make_assembled(story_id, cast_id),
            story_id,
            "The Night Warden falls.",
        )

        rows = session.query(SBEventORM).filter_by(story_id=str(story_id)).all()
        assert len(rows) == 1
        assert "night warden" in rows[0].description.lower()
        assert rows[0].significance == "major_plot_turn"

    def test_event_with_character_death_significance(  # type: ignore[no-untyped-def]
        self, session, story_and_cast
    ) -> None:
        """character_death significance is stored correctly."""
        story_id, cast_id = story_and_cast
        fake = _make_fake_caller(
            _fake_tool_response(
                {
                    "events": [
                        {
                            "description": "Aldric is slain.",
                            "significance": "character_death",
                        }
                    ]
                }
            )
        )
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config(), fake)

        service.extract(_make_assembled(story_id, cast_id), story_id, "Aldric falls.")

        rows = session.query(SBEventORM).filter_by(story_id=str(story_id)).all()
        assert len(rows) == 1
        assert rows[0].significance == "character_death"


# ---------------------------------------------------------------------------
# Direct-write prevention — architectural invariant
# ---------------------------------------------------------------------------


class TestDirectWritePrevention:
    def test_all_auto_committed_proposals_have_staging_row(  # type: ignore[no-untyped-def]
        self, session, story_and_cast
    ) -> None:
        """Every auto-committed update has a corresponding RATIFIED staging row.

        This is the architectural invariant: the Extractor CANNOT write to canon
        without first staging a proposal.  We verify it by confirming that for
        each auto-committed proposal returned in ExtractorResult, a matching row
        exists in the provisional staging table with RATIFIED status.
        """
        story_id, cast_id = story_and_cast
        fake = _make_fake_caller(
            _fake_tool_response(
                {
                    "transient_states": [
                        {
                            "character_name": "Aldric",
                            "field_name": "current_location",
                            "new_value": "The Vault",
                        }
                    ],
                    "events": [
                        {
                            "description": "Aldric found the vault.",
                            "significance": "routine",
                        }
                    ],
                }
            )
        )
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config(), fake)

        result = service.extract(
            _make_assembled(story_id, cast_id), story_id, "Aldric enters the vault."
        )

        # For every auto-committed proposal, a RATIFIED staging row must exist.
        ratified_ids = {
            str(row.proposal_id)
            for row in session.query(SBProvisionalStagingORM)
            .filter_by(status=ProposalStatus.RATIFIED.value)
            .all()
        }
        for p in result.auto_committed:
            assert str(p.proposal_id) in ratified_ids, (
                f"Proposal {p.proposal_id} ({p.proposal_type.value}) was "
                "auto-committed without a staging row — direct-write invariant violated"
            )

    def test_no_auto_committed_proposals_without_staging_for_locked_facts(  # type: ignore[no-untyped-def]
        self, session, story_and_cast
    ) -> None:
        """Locked facts are NOT in auto_committed — they require confirmation."""
        story_id, cast_id = story_and_cast
        fake = _make_fake_caller(
            _fake_tool_response(
                {"locked_facts": [{"fact_text": "The throne is vacant forever."}]}
            )
        )
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config(), fake)

        result = service.extract(
            _make_assembled(story_id, cast_id), story_id, "The throne stands empty."
        )

        # Locked facts must be PENDING, not auto-committed.
        assert all(p.status == ProposalStatus.PENDING for p in result.pending_proposals)
        assert len(result.auto_committed) == 0


# ---------------------------------------------------------------------------
# Unresolvable character name
# ---------------------------------------------------------------------------


class TestUnresolvableCharacter:
    def test_unresolvable_name_still_ratifies_proposal(  # type: ignore[no-untyped-def]
        self, session, story_and_cast
    ) -> None:
        """Soft-fact for unknown character name is RATIFIED without error."""
        story_id, cast_id = story_and_cast
        fake = _make_fake_caller(
            _fake_tool_response(
                {
                    "soft_facts": [
                        {
                            "character_name": "UnknownHero",
                            "field_name": "current_location",
                            "new_value": "Somewhere",
                        }
                    ]
                }
            )
        )
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config(), fake)

        result = service.extract(
            _make_assembled(story_id, cast_id), story_id, "The unknown hero walks."
        )

        # Proposal is staged and ratified even without a resolvable cast entry.
        assert len(result.auto_committed) == 1
        assert result.auto_committed[0].status == ProposalStatus.RATIFIED
        # The real cast entry is unchanged.
        entry = sbs.get_character(story_id, cast_id)
        assert entry is not None
        assert entry.current_location == "The Crossroads Inn"


# ---------------------------------------------------------------------------
# Empty tool response
# ---------------------------------------------------------------------------


class TestEmptyToolResponse:
    def test_empty_tool_response_produces_empty_result(  # type: ignore[no-untyped-def]
        self, session, story_and_cast
    ) -> None:
        """When the model proposes nothing, all lists are empty."""
        story_id, cast_id = story_and_cast
        fake = _make_fake_caller(_fake_tool_response({}))
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config(), fake)

        result = service.extract(
            _make_assembled(story_id, cast_id), story_id, "Nothing changed."
        )

        assert result.proposals == []
        assert result.pending_proposals == []
        assert result.auto_committed == []

    def test_empty_result_pass_forward_says_no_updates(  # type: ignore[no-untyped-def]
        self, session, story_and_cast
    ) -> None:
        """Pass-forward content says no updates when the model finds nothing."""
        story_id, cast_id = story_and_cast
        fake = _make_fake_caller(_fake_tool_response({}))
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config(), fake)

        result = service.extract(
            _make_assembled(story_id, cast_id), story_id, "Nothing changed."
        )

        assert "no narrative updates" in result.pass_forward_content.lower()


# ---------------------------------------------------------------------------
# Pass-forward content
# ---------------------------------------------------------------------------


class TestPassForwardContent:
    def test_pass_forward_mentions_pending_locked_fact(  # type: ignore[no-untyped-def]
        self, session, story_and_cast
    ) -> None:
        """Pass-forward content references pending locked-fact proposals."""
        story_id, cast_id = story_and_cast
        fake = _make_fake_caller(
            _fake_tool_response(
                {"locked_facts": [{"fact_text": "The emperor is dead."}]}
            )
        )
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config(), fake)

        result = service.extract(
            _make_assembled(story_id, cast_id), story_id, "The emperor falls."
        )

        assert "emperor" in result.pass_forward_content.lower()
        assert "pending" in result.pass_forward_content.lower()

    def test_pass_forward_mentions_auto_committed_event(  # type: ignore[no-untyped-def]
        self, session, story_and_cast
    ) -> None:
        """Pass-forward content references auto-committed events."""
        story_id, cast_id = story_and_cast
        fake = _make_fake_caller(
            _fake_tool_response(
                {
                    "events": [
                        {
                            "description": "Aldric found the hidden door.",
                            "significance": "routine",
                        }
                    ]
                }
            )
        )
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config(), fake)

        result = service.extract(
            _make_assembled(story_id, cast_id), story_id, "A door appears."
        )

        assert "event" in result.pass_forward_content.lower()


# ---------------------------------------------------------------------------
# Token metrics
# ---------------------------------------------------------------------------


class TestTokenMetrics:
    def test_token_metrics_propagated(  # type: ignore[no-untyped-def]
        self, session, story_and_cast
    ) -> None:
        """ExtractorResult surfaces all four token counts when reported."""
        story_id, cast_id = story_and_cast
        fake = _make_fake_caller(
            _fake_tool_response(
                {},
                input_tokens=200,
                output_tokens=80,
                cache_read_input_tokens=150,
                cache_creation_input_tokens=50,
            )
        )
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config(), fake)

        result = service.extract(_make_assembled(story_id, cast_id), story_id, "prose.")

        assert result.input_token_count == 200
        assert result.output_token_count == 80
        assert result.cache_read_token_count == 150
        assert result.cache_creation_token_count == 50

    def test_cache_metrics_none_when_not_reported(  # type: ignore[no-untyped-def]
        self, session, story_and_cast
    ) -> None:
        """Cache token fields are None when the provider omits them."""
        story_id, cast_id = story_and_cast
        fake = _make_fake_caller(
            _fake_tool_response(
                {},
                input_tokens=100,
                output_tokens=40,
                cache_read_input_tokens=None,
                cache_creation_input_tokens=None,
            )
        )
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config(), fake)

        result = service.extract(_make_assembled(story_id, cast_id), story_id, "prose.")

        assert result.cache_read_token_count is None
        assert result.cache_creation_token_count is None

    def test_model_identifier_format(  # type: ignore[no-untyped-def]
        self, session, story_and_cast
    ) -> None:
        """model_identifier is formatted as 'anthropic:<model_string>'."""
        story_id, cast_id = story_and_cast
        fake = _make_fake_caller(_fake_tool_response())
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config(), fake)

        result = service.extract(_make_assembled(story_id, cast_id), story_id, "prose.")

        assert result.model_identifier.startswith("anthropic:")
        assert "haiku" in result.model_identifier


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


class TestErrorHandling:
    def test_provider_exception_raises_extractor_pass_error(  # type: ignore[no-untyped-def]
        self, session, story_and_cast
    ) -> None:
        """A provider exception is wrapped in ExtractorPassError."""
        story_id, cast_id = story_and_cast
        original_exc = ConnectionError("network failure")
        fake = _make_fake_caller(raise_exc=original_exc)
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config(), fake)

        with pytest.raises(ExtractorPassError) as exc_info:
            service.extract(_make_assembled(story_id, cast_id), story_id, "prose.")

        assert exc_info.value.__cause__ is original_exc

    def test_no_tool_use_block_raises_extractor_pass_error(  # type: ignore[no-untyped-def]
        self, session, story_and_cast
    ) -> None:
        """Response with no tool-use block raises ExtractorPassError."""
        story_id, cast_id = story_and_cast

        text_only_response = Message(
            id="msg_text",
            type="message",
            role="assistant",
            content=[TextBlock(type="text", text="I extracted nothing.")],
            model="claude-haiku-4-5-20251001",
            stop_reason="end_turn",
            stop_sequence=None,
            usage=Usage(input_tokens=10, output_tokens=5),
        )
        fake = _make_fake_caller(text_only_response)
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config(), fake)

        with pytest.raises(ExtractorPassError):
            service.extract(_make_assembled(story_id, cast_id), story_id, "prose.")

    def test_fake_caller_receives_tool_spec(  # type: ignore[no-untyped-def]
        self, session, story_and_cast
    ) -> None:
        """The injected caller receives a payload with the extraction tool spec."""
        story_id, cast_id = story_and_cast
        fake = _make_fake_caller(_fake_tool_response())
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config(), fake)

        service.extract(_make_assembled(story_id, cast_id), story_id, "prose.")

        assert len(fake.captured) == 1  # type: ignore[attr-defined]
        payload = fake.captured[0]  # type: ignore[attr-defined]
        assert "tools" in payload
        tools = payload["tools"]
        assert isinstance(tools, list)
        assert len(tools) == 1
        assert tools[0]["name"] == EXTRACT_TOOL_NAME

    def test_result_is_typed_extractor_result(  # type: ignore[no-untyped-def]
        self, session, story_and_cast
    ) -> None:
        """extract() returns a typed ExtractorResult, not a raw dict."""
        story_id, cast_id = story_and_cast
        fake = _make_fake_caller(_fake_tool_response())
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config(), fake)

        result = service.extract(_make_assembled(story_id, cast_id), story_id, "prose.")

        assert isinstance(result, ExtractorResult)


# ---------------------------------------------------------------------------
# StoryBibleService.get_pending_proposals
# ---------------------------------------------------------------------------


class TestGetPendingProposals:
    def test_get_pending_proposals_returns_locked_facts(  # type: ignore[no-untyped-def]
        self, session, story_and_cast
    ) -> None:
        """get_pending_proposals() returns the staged locked-fact proposals."""
        story_id, cast_id = story_and_cast
        fake = _make_fake_caller(
            _fake_tool_response(
                {"locked_facts": [{"fact_text": "The wall has fallen."}]}
            )
        )
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config(), fake)

        service.extract(_make_assembled(story_id, cast_id), story_id, "The wall falls.")

        pending = sbs.get_pending_proposals(story_id)
        assert len(pending) == 1
        assert pending[0].proposal_type == ProposalType.LOCKED_FACT

    def test_get_pending_proposals_empty_after_all_auto_committed(  # type: ignore[no-untyped-def]
        self, session, story_and_cast
    ) -> None:
        """get_pending_proposals() is empty when only auto-committed proposals exist."""
        story_id, cast_id = story_and_cast
        fake = _make_fake_caller(
            _fake_tool_response(
                {
                    "events": [
                        {
                            "description": "A small skirmish occurred.",
                            "significance": "routine",
                        }
                    ]
                }
            )
        )
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config(), fake)

        service.extract(
            _make_assembled(story_id, cast_id), story_id, "A fight breaks out."
        )

        pending = sbs.get_pending_proposals(story_id)
        assert pending == []
