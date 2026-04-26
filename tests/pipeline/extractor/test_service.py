"""Unit tests for ExtractorService — CRD Issue 10.

Test classes
------------
TestLockedFactRouting       — locked_fact staging and DB row
TestSoftFactRouting         — soft_fact staging, field application, audit row
TestTransientStateRouting   — transient_state staging, field application, audit row
TestUnresolvedThreadRouting — thread row, audit row
TestEventRouting            — event bypass, event_kind column, event_id matching
TestUnresolvableCharacter   — fail-loud on unknown character name; no DB state
TestStoryIdGuard            — built_context / story_id mismatch guard
TestEmptyToolResponse       — empty proposals array handling
TestListPendingLockedFactProposals — list_pending_locked_fact_proposals contract
TestTokenMetrics            — all four token counts; None when omitted
TestErrorHandling           — provider exception, missing tool block, payload shape
TestRelationshipDomain      — RELATIONSHIP success; malformed-key variants;
                              unresolvable subject/object; no DB state on failure
TestWorldDomain             — world domain always raises; no DB state
TestTransactionBoundary     — all-or-nothing commit: partial failure → zero rows
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

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
    RelationshipType,
    StoryMode,
)
from afterworlds.models.intent_classification import IntentClassificationResult
from afterworlds.models.story import Arc, Chapter, Story
from afterworlds.models.story_bible import (
    CastEntry,
    RelationshipLedger,
    StoryBibleContext,
)
from afterworlds.persistence.crud.node import create_node
from afterworlds.persistence.crud.story import create_arc, create_chapter, create_story
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.persistence.orm.base import Base
from afterworlds.persistence.orm.story_bible import (
    SBEventORM,
    SBProvisionalStagingORM,
    SBRelationshipLedgerORM,
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
                input=tool_input if tool_input is not None else {"proposals": []},
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


def _turn_id() -> UUID:
    return uuid4()


# ---------------------------------------------------------------------------
# Classification routing — locked facts
# ---------------------------------------------------------------------------


class TestLockedFactRouting:
    def test_locked_fact_staged_pending(  # type: ignore[no-untyped-def]
        self, session, story_and_cast
    ) -> None:
        """A locked-fact proposal produces a staged_id and a PENDING staging row."""
        story_id, cast_id = story_and_cast
        fake = _make_fake_caller(
            _fake_tool_response(
                {
                    "proposals": [
                        {
                            "kind": "locked_fact",
                            "fact_text": "The king is assassinated.",
                        }
                    ]
                }
            )
        )
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config(), fake)

        result = service.extract(
            _make_assembled(story_id, cast_id),
            "The king falls dead.",
            story_id,
            _turn_id(),
        )

        assert len(result.routed.locked_fact_staged_ids) == 1
        assert result.routed.soft_fact_staged_ids == []
        assert result.routed.event_ids == []

        rows = (
            session.query(SBProvisionalStagingORM)
            .filter_by(
                proposal_type=ProposalType.LOCKED_FACT.value,
                status=ProposalStatus.PENDING.value,
            )
            .all()
        )
        assert len(rows) == 1
        assert rows[0].requires_confirmation is True
        assert "king" in rows[0].proposed_value.get("fact_text", "").lower()

    def test_locked_fact_staged_id_matches_db_row(  # type: ignore[no-untyped-def]
        self, session, story_and_cast
    ) -> None:
        """The staged_id returned matches the DB row's proposal_id."""
        story_id, cast_id = story_and_cast
        fake = _make_fake_caller(
            _fake_tool_response(
                {
                    "proposals": [
                        {"kind": "locked_fact", "fact_text": "The bridge is destroyed."}
                    ]
                }
            )
        )
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config(), fake)

        result = service.extract(
            _make_assembled(story_id, cast_id),
            "The bridge falls.",
            story_id,
            _turn_id(),
        )

        staged_id = result.routed.locked_fact_staged_ids[0]
        row = session.get(SBProvisionalStagingORM, str(staged_id))
        assert row is not None
        assert row.status == ProposalStatus.PENDING.value


# ---------------------------------------------------------------------------
# Classification routing — soft facts
# ---------------------------------------------------------------------------


class TestSoftFactRouting:
    def test_soft_fact_staged_id_returned(  # type: ignore[no-untyped-def]
        self, session, story_and_cast
    ) -> None:
        """A soft-fact proposal returns a staged_id."""
        story_id, cast_id = story_and_cast
        fake = _make_fake_caller(
            _fake_tool_response(
                {
                    "proposals": [
                        {
                            "kind": "soft_fact",
                            "target_domain": "character",
                            "target_natural_key": "Aldric",
                            "target_field": "current_status",
                            "proposed_value": "injured",
                        }
                    ]
                }
            )
        )
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config(), fake)

        result = service.extract(
            _make_assembled(story_id, cast_id), "Aldric is cut.", story_id, _turn_id()
        )

        assert len(result.routed.soft_fact_staged_ids) == 1
        assert result.routed.locked_fact_staged_ids == []

    def test_soft_fact_applied_to_cast_dynamic_field(  # type: ignore[no-untyped-def]
        self, session, story_and_cast
    ) -> None:
        """A soft-fact update is applied to the cast entry's dynamic field."""
        story_id, cast_id = story_and_cast
        fake = _make_fake_caller(
            _fake_tool_response(
                {
                    "proposals": [
                        {
                            "kind": "soft_fact",
                            "target_domain": "character",
                            "target_natural_key": "Aldric",
                            "target_field": "current_location",
                            "proposed_value": "The Dark Tower",
                        }
                    ]
                }
            )
        )
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config(), fake)

        service.extract(
            _make_assembled(story_id, cast_id),
            "Aldric enters the tower.",
            story_id,
            _turn_id(),
        )

        entry = sbs.get_character(story_id, cast_id)
        assert entry is not None
        assert entry.current_location == "The Dark Tower"

    def test_soft_fact_has_ratified_staging_row(  # type: ignore[no-untyped-def]
        self, session, story_and_cast
    ) -> None:
        """A RATIFIED audit staging row exists for each soft-fact update."""
        story_id, cast_id = story_and_cast
        fake = _make_fake_caller(
            _fake_tool_response(
                {
                    "proposals": [
                        {
                            "kind": "soft_fact",
                            "target_domain": "character",
                            "target_natural_key": "Aldric",
                            "target_field": "current_status",
                            "proposed_value": "exhausted",
                        }
                    ]
                }
            )
        )
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config(), fake)

        service.extract(
            _make_assembled(story_id, cast_id),
            "Aldric collapses exhausted.",
            story_id,
            _turn_id(),
        )

        rows = (
            session.query(SBProvisionalStagingORM)
            .filter_by(
                proposal_type=ProposalType.SOFT_FACT.value,
                status=ProposalStatus.RATIFIED.value,
            )
            .all()
        )
        assert len(rows) == 1, "No audit staging row — direct-write invariant violated"


# ---------------------------------------------------------------------------
# Classification routing — transient states
# ---------------------------------------------------------------------------


class TestTransientStateRouting:
    def test_transient_state_staged_id_returned(  # type: ignore[no-untyped-def]
        self, session, story_and_cast
    ) -> None:
        """A transient-state proposal returns a staged_id."""
        story_id, cast_id = story_and_cast
        fake = _make_fake_caller(
            _fake_tool_response(
                {
                    "proposals": [
                        {
                            "kind": "transient_state",
                            "target_domain": "character",
                            "target_natural_key": "Aldric",
                            "target_field": "current_location",
                            "proposed_value": "Forest Path",
                        }
                    ]
                }
            )
        )
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config(), fake)

        result = service.extract(
            _make_assembled(story_id, cast_id),
            "Aldric walks the forest path.",
            story_id,
            _turn_id(),
        )

        assert len(result.routed.transient_state_staged_ids) == 1

    def test_transient_state_applied_to_cast_dynamic_field(  # type: ignore[no-untyped-def]
        self, session, story_and_cast
    ) -> None:
        """A transient-state update is applied to the cast entry's dynamic field."""
        story_id, cast_id = story_and_cast
        fake = _make_fake_caller(
            _fake_tool_response(
                {
                    "proposals": [
                        {
                            "kind": "transient_state",
                            "target_domain": "character",
                            "target_natural_key": "Aldric",
                            "target_field": "current_location",
                            "proposed_value": "The Market Square",
                        }
                    ]
                }
            )
        )
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config(), fake)

        service.extract(
            _make_assembled(story_id, cast_id),
            "Aldric reaches the market.",
            story_id,
            _turn_id(),
        )

        entry = sbs.get_character(story_id, cast_id)
        assert entry is not None
        assert entry.current_location == "The Market Square"

    def test_transient_state_has_ratified_staging_row(  # type: ignore[no-untyped-def]
        self, session, story_and_cast
    ) -> None:
        """A RATIFIED audit staging row exists for each transient-state update."""
        story_id, cast_id = story_and_cast
        fake = _make_fake_caller(
            _fake_tool_response(
                {
                    "proposals": [
                        {
                            "kind": "transient_state",
                            "target_domain": "character",
                            "target_natural_key": "Aldric",
                            "target_field": "current_location",
                            "proposed_value": "The Vault",
                        }
                    ]
                }
            )
        )
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config(), fake)

        service.extract(
            _make_assembled(story_id, cast_id),
            "Aldric enters the vault.",
            story_id,
            _turn_id(),
        )

        rows = (
            session.query(SBProvisionalStagingORM)
            .filter_by(
                proposal_type=ProposalType.TRANSIENT_STATE.value,
                status=ProposalStatus.RATIFIED.value,
            )
            .all()
        )
        assert len(rows) == 1


# ---------------------------------------------------------------------------
# Classification routing — unresolved threads
# ---------------------------------------------------------------------------


class TestUnresolvedThreadRouting:
    def test_unresolved_thread_staged_id_returned(  # type: ignore[no-untyped-def]
        self, session, story_and_cast
    ) -> None:
        """An unresolved-thread proposal returns a staged_id."""
        story_id, cast_id = story_and_cast
        fake = _make_fake_caller(
            _fake_tool_response(
                {
                    "proposals": [
                        {
                            "kind": "unresolved_thread",
                            "description": "Who left the hooded figure at the inn?",
                        }
                    ]
                }
            )
        )
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config(), fake)

        result = service.extract(
            _make_assembled(story_id, cast_id),
            "A hooded figure watches.",
            story_id,
            _turn_id(),
        )

        assert len(result.routed.unresolved_thread_staged_ids) == 1

    def test_unresolved_thread_creates_thread_row(  # type: ignore[no-untyped-def]
        self, session, story_and_cast
    ) -> None:
        """An unresolved-thread proposal creates a row in sb_unresolved_threads."""
        story_id, cast_id = story_and_cast
        fake = _make_fake_caller(
            _fake_tool_response(
                {
                    "proposals": [
                        {
                            "kind": "unresolved_thread",
                            "description": "Where is the missing artefact hidden?",
                        }
                    ]
                }
            )
        )
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config(), fake)

        service.extract(
            _make_assembled(story_id, cast_id),
            "The artefact is gone.",
            story_id,
            _turn_id(),
        )

        rows = (
            session.query(SBUnresolvedThreadORM).filter_by(story_id=str(story_id)).all()
        )
        assert len(rows) == 1
        assert "artefact" in rows[0].description.lower()

    def test_unresolved_thread_has_ratified_staging_row(  # type: ignore[no-untyped-def]
        self, session, story_and_cast
    ) -> None:
        """A RATIFIED audit staging row exists for each unresolved-thread proposal."""
        story_id, cast_id = story_and_cast
        fake = _make_fake_caller(
            _fake_tool_response(
                {
                    "proposals": [
                        {
                            "kind": "unresolved_thread",
                            "description": "Who opened the gate?",
                        }
                    ]
                }
            )
        )
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config(), fake)

        service.extract(
            _make_assembled(story_id, cast_id),
            "The gate is open.",
            story_id,
            _turn_id(),
        )

        rows = (
            session.query(SBProvisionalStagingORM)
            .filter_by(
                proposal_type=ProposalType.UNRESOLVED_THREAD.value,
                status=ProposalStatus.RATIFIED.value,
            )
            .all()
        )
        assert len(rows) == 1


# ---------------------------------------------------------------------------
# Classification routing — events
# ---------------------------------------------------------------------------


class TestEventRouting:
    def test_event_id_returned(  # type: ignore[no-untyped-def]
        self, session, story_and_cast
    ) -> None:
        """An event proposal returns an event_id in routed.event_ids."""
        story_id, cast_id = story_and_cast
        fake = _make_fake_caller(
            _fake_tool_response(
                {
                    "proposals": [
                        {
                            "kind": "event",
                            "event_kind": "scene_transition",
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
            "Aldric crosses the bridge.",
            story_id,
            _turn_id(),
        )

        assert len(result.routed.event_ids) == 1

    def test_event_creates_event_row_with_event_kind(  # type: ignore[no-untyped-def]
        self, session, story_and_cast
    ) -> None:
        """An event proposal creates a row in sb_events with the correct event_kind."""
        story_id, cast_id = story_and_cast
        fake = _make_fake_caller(
            _fake_tool_response(
                {
                    "proposals": [
                        {
                            "kind": "event",
                            "event_kind": "death",
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
            "The Night Warden falls.",
            story_id,
            _turn_id(),
        )

        rows = session.query(SBEventORM).filter_by(story_id=str(story_id)).all()
        assert len(rows) == 1
        assert "night warden" in rows[0].description.lower()
        assert rows[0].significance == "major_plot_turn"
        assert rows[0].event_kind == "death"

    def test_event_bypasses_staging_table(  # type: ignore[no-untyped-def]
        self, session, story_and_cast
    ) -> None:
        """Events go directly to sb_events — no staging row is created."""
        story_id, cast_id = story_and_cast
        fake = _make_fake_caller(
            _fake_tool_response(
                {
                    "proposals": [
                        {
                            "kind": "event",
                            "event_kind": "plot_reveal",
                            "description": "The prophecy is revealed.",
                            "significance": "locked_fact_established",
                        }
                    ]
                }
            )
        )
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config(), fake)

        service.extract(
            _make_assembled(story_id, cast_id),
            "The prophecy becomes clear.",
            story_id,
            _turn_id(),
        )

        staging_rows = session.query(SBProvisionalStagingORM).all()
        assert staging_rows == [], "Event created a staging row — should bypass staging"

    def test_event_id_matches_db_row(  # type: ignore[no-untyped-def]
        self, session, story_and_cast
    ) -> None:
        """routed.event_ids[0] matches the event_id column in sb_events."""
        story_id, cast_id = story_and_cast
        fake = _make_fake_caller(
            _fake_tool_response(
                {
                    "proposals": [
                        {
                            "kind": "event",
                            "event_kind": "npc_introduction",
                            "description": "A stranger arrived.",
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
            "A stranger appears.",
            story_id,
            _turn_id(),
        )

        event_id = result.routed.event_ids[0]
        row = session.get(SBEventORM, str(event_id))
        assert row is not None
        assert "stranger" in row.description.lower()


# ---------------------------------------------------------------------------
# Fail-loud unresolvable character name
# ---------------------------------------------------------------------------


class TestUnresolvableCharacter:
    def test_unresolvable_character_name_raises_extractor_pass_error(  # type: ignore[no-untyped-def]
        self, session, story_and_cast
    ) -> None:
        """Soft-fact for unknown character name raises ExtractorPassError."""
        story_id, cast_id = story_and_cast
        fake = _make_fake_caller(
            _fake_tool_response(
                {
                    "proposals": [
                        {
                            "kind": "soft_fact",
                            "target_domain": "character",
                            "target_natural_key": "UnknownHero",
                            "target_field": "current_location",
                            "proposed_value": "Somewhere",
                        }
                    ]
                }
            )
        )
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config(), fake)

        with pytest.raises(ExtractorPassError) as exc_info:
            service.extract(
                _make_assembled(story_id, cast_id),
                "The unknown hero walks.",
                story_id,
                _turn_id(),
            )

        assert (
            "UnknownHero" in str(exc_info.value)
            or "routing failed" in str(exc_info.value).lower()
        )

    def test_unresolvable_name_leaves_no_db_state(  # type: ignore[no-untyped-def]
        self, session, story_and_cast
    ) -> None:
        """When routing fails, no staging rows or event rows are committed."""
        story_id, cast_id = story_and_cast
        fake = _make_fake_caller(
            _fake_tool_response(
                {
                    "proposals": [
                        {
                            "kind": "transient_state",
                            "target_domain": "character",
                            "target_natural_key": "GhostCharacter",
                            "target_field": "current_location",
                            "proposed_value": "Nowhere",
                        }
                    ]
                }
            )
        )
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config(), fake)

        with pytest.raises(ExtractorPassError):
            service.extract(
                _make_assembled(story_id, cast_id),
                "The ghost walks.",
                story_id,
                _turn_id(),
            )

        # Session is dirty (not committed) — re-open to see committed state.
        session.rollback()
        staging_rows = session.query(SBProvisionalStagingORM).all()
        assert staging_rows == []

    def test_ambiguous_character_name_raises_extractor_pass_error(  # type: ignore[no-untyped-def]
        self, session, story_and_cast
    ) -> None:
        """Ambiguous case-insensitive name match raises ExtractorPassError."""
        story_id, cast_id = story_and_cast
        now = datetime(2026, 1, 1, tzinfo=UTC)
        sbs = StoryBibleService(session)
        # Seed a second "Aldric" entry (schema has no uniqueness constraint).
        duplicate = CastEntry(
            story_id=story_id,
            name="aldric",  # same name, different casing — still matches
            role=CastRole.MINOR,
            created_at=now,
        )
        sbs.add_cast_entry(story_id, duplicate)
        session.commit()

        fake = _make_fake_caller(
            _fake_tool_response(
                {
                    "proposals": [
                        {
                            "kind": "soft_fact",
                            "target_domain": "character",
                            "target_natural_key": "Aldric",
                            "target_field": "current_location",
                            "proposed_value": "Somewhere",
                        }
                    ]
                }
            )
        )
        service = ExtractorService(session, sbs, _make_config(), fake)

        with pytest.raises(ExtractorPassError):
            service.extract(
                _make_assembled(story_id, cast_id),
                "prose.",
                story_id,
                _turn_id(),
            )

        session.rollback()
        assert session.query(SBProvisionalStagingORM).all() == []


# ---------------------------------------------------------------------------
# Story-id guard
# ---------------------------------------------------------------------------


class TestStoryIdGuard:
    def test_story_id_mismatch_raises_extractor_pass_error(  # type: ignore[no-untyped-def]
        self, session, story_and_cast
    ) -> None:
        """built_context.story_id != story_id raises ExtractorPassError immediately."""
        story_id, cast_id = story_and_cast
        wrong_story_id = uuid4()
        fake = _make_fake_caller(_fake_tool_response())
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config(), fake)

        # _make_assembled uses story_id, but we pass wrong_story_id as story_id arg
        with pytest.raises(ExtractorPassError) as exc_info:
            service.extract(
                _make_assembled(story_id, cast_id),
                "prose.",
                wrong_story_id,
                _turn_id(),
            )

        assert "story_id" in str(exc_info.value).lower()


# ---------------------------------------------------------------------------
# Empty tool response
# ---------------------------------------------------------------------------


class TestEmptyToolResponse:
    def test_empty_proposals_produces_empty_routed(  # type: ignore[no-untyped-def]
        self, session, story_and_cast
    ) -> None:
        """When the model proposes nothing, all routed ID lists are empty."""
        story_id, cast_id = story_and_cast
        fake = _make_fake_caller(_fake_tool_response({"proposals": []}))
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config(), fake)

        result = service.extract(
            _make_assembled(story_id, cast_id), "Nothing changed.", story_id, _turn_id()
        )

        assert result.routed.locked_fact_staged_ids == []
        assert result.routed.soft_fact_staged_ids == []
        assert result.routed.transient_state_staged_ids == []
        assert result.routed.unresolved_thread_staged_ids == []
        assert result.routed.event_ids == []

    def test_empty_proposal_set_is_valid(  # type: ignore[no-untyped-def]
        self, session, story_and_cast
    ) -> None:
        """An empty proposals array is valid and produces a non-None proposal_set."""
        story_id, cast_id = story_and_cast
        fake = _make_fake_caller(_fake_tool_response({"proposals": []}))
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config(), fake)

        result = service.extract(
            _make_assembled(story_id, cast_id), "Nothing changed.", story_id, _turn_id()
        )

        assert result.proposal_set is not None
        assert result.proposal_set.proposals == []


# ---------------------------------------------------------------------------
# list_pending_locked_fact_proposals
# ---------------------------------------------------------------------------


class TestListPendingLockedFactProposals:
    def test_list_pending_locked_fact_proposals_returns_locked_facts(  # type: ignore[no-untyped-def]
        self, session, story_and_cast
    ) -> None:
        """list_pending_locked_fact_proposals returns PENDING LOCKED_FACT rows."""
        story_id, cast_id = story_and_cast
        fake = _make_fake_caller(
            _fake_tool_response(
                {
                    "proposals": [
                        {"kind": "locked_fact", "fact_text": "The wall has fallen."}
                    ]
                }
            )
        )
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config(), fake)

        service.extract(
            _make_assembled(story_id, cast_id), "The wall falls.", story_id, _turn_id()
        )

        pending = sbs.list_pending_locked_fact_proposals(story_id)
        assert len(pending) == 1
        assert pending[0].proposal_type == ProposalType.LOCKED_FACT
        assert pending[0].status == ProposalStatus.PENDING

    def test_list_pending_excludes_auto_committed_proposals(  # type: ignore[no-untyped-def]
        self, session, story_and_cast
    ) -> None:
        """list_pending_locked_fact_proposals excludes RATIFIED proposals."""
        story_id, cast_id = story_and_cast
        fake = _make_fake_caller(
            _fake_tool_response(
                {
                    "proposals": [
                        {
                            "kind": "event",
                            "event_kind": "routine",
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
            _make_assembled(story_id, cast_id),
            "A fight breaks out.",
            story_id,
            _turn_id(),
        )

        pending = sbs.list_pending_locked_fact_proposals(story_id)
        assert pending == []


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
                {"proposals": []},
                input_tokens=200,
                output_tokens=80,
                cache_read_input_tokens=150,
                cache_creation_input_tokens=50,
            )
        )
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config(), fake)

        result = service.extract(
            _make_assembled(story_id, cast_id), "prose.", story_id, _turn_id()
        )

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
                {"proposals": []},
                input_tokens=100,
                output_tokens=40,
                cache_read_input_tokens=None,
                cache_creation_input_tokens=None,
            )
        )
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config(), fake)

        result = service.extract(
            _make_assembled(story_id, cast_id), "prose.", story_id, _turn_id()
        )

        assert result.cache_read_token_count is None
        assert result.cache_creation_token_count is None


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
            service.extract(
                _make_assembled(story_id, cast_id), "prose.", story_id, _turn_id()
            )

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
            service.extract(
                _make_assembled(story_id, cast_id), "prose.", story_id, _turn_id()
            )

    def test_fake_caller_receives_tool_spec_with_new_name(  # type: ignore[no-untyped-def]
        self, session, story_and_cast
    ) -> None:
        """The injected caller receives a payload with 'propose_canon_updates' tool."""
        story_id, cast_id = story_and_cast
        fake = _make_fake_caller(_fake_tool_response())
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config(), fake)

        service.extract(
            _make_assembled(story_id, cast_id), "prose.", story_id, _turn_id()
        )

        assert len(fake.captured) == 1  # type: ignore[attr-defined]
        payload = fake.captured[0]  # type: ignore[attr-defined]
        assert "tools" in payload
        tools = payload["tools"]
        assert isinstance(tools, list)
        assert len(tools) == 1
        assert tools[0]["name"] == "propose_canon_updates"
        assert tools[0]["name"] == EXTRACT_TOOL_NAME

    def test_result_is_typed_extractor_result(  # type: ignore[no-untyped-def]
        self, session, story_and_cast
    ) -> None:
        """extract() returns a typed ExtractorResult."""
        story_id, cast_id = story_and_cast
        fake = _make_fake_caller(_fake_tool_response())
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config(), fake)

        result = service.extract(
            _make_assembled(story_id, cast_id), "prose.", story_id, _turn_id()
        )

        assert isinstance(result, ExtractorResult)


# ---------------------------------------------------------------------------
# Shared fixture — relationship seeding
# ---------------------------------------------------------------------------


@pytest.fixture()
def story_with_relationship(session, story_and_cast):  # type: ignore[no-untyped-def]
    """Extend story_and_cast with a second cast entry 'Mira' and 'Aldric -> Mira'."""
    story_id, aldric_cast_id = story_and_cast
    now = datetime(2026, 1, 1, tzinfo=UTC)

    sbs = StoryBibleService(session)
    mira_entry = CastEntry(
        story_id=story_id,
        name="Mira",
        role=CastRole.SUPPORTING,
        created_at=now,
    )
    mira_saved = sbs.add_cast_entry(story_id, mira_entry)

    relationship = RelationshipLedger(
        story_id=story_id,
        subject_cast_id=aldric_cast_id,
        object_cast_id=mira_saved.cast_id,
        relationship_type=RelationshipType.ALLY,
        current_status_description="Cautious allies",
        created_at=now,
        updated_at=now,
    )
    sbs.add_relationship(story_id, relationship)
    session.commit()

    return story_id, aldric_cast_id, mira_saved.cast_id


# ---------------------------------------------------------------------------
# Relationship domain
# ---------------------------------------------------------------------------


class TestRelationshipDomain:
    def test_relationship_soft_fact_updates_status_description(  # type: ignore[no-untyped-def]
        self, session, story_with_relationship
    ) -> None:
        """RELATIONSHIP soft_fact updates current_status_description and leaves a
        RATIFIED audit row."""
        story_id, aldric_cast_id, mira_cast_id = story_with_relationship
        fake = _make_fake_caller(
            _fake_tool_response(
                {
                    "proposals": [
                        {
                            "kind": "soft_fact",
                            "target_domain": "relationship",
                            "target_natural_key": "Aldric -> Mira",
                            "target_field": "current_status_description",
                            "proposed_value": "tense allies",
                        }
                    ]
                }
            )
        )
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config(), fake)

        result = service.extract(
            _make_assembled(story_id, aldric_cast_id),
            "Aldric eyes Mira with suspicion.",
            story_id,
            _turn_id(),
        )

        assert len(result.routed.soft_fact_staged_ids) == 1

        rel_row = (
            session.query(SBRelationshipLedgerORM)
            .filter_by(
                story_id=str(story_id),
                subject_cast_id=str(aldric_cast_id),
                object_cast_id=str(mira_cast_id),
                is_active=True,
            )
            .one()
        )
        assert rel_row.current_status_description == "tense allies"

        audit_rows = (
            session.query(SBProvisionalStagingORM)
            .filter_by(
                proposal_type=ProposalType.SOFT_FACT.value,
                status=ProposalStatus.RATIFIED.value,
            )
            .all()
        )
        assert len(audit_rows) == 1

    def test_relationship_malformed_key_no_delimiter_raises(  # type: ignore[no-untyped-def]
        self, session, story_with_relationship
    ) -> None:
        """Relationship key with no ' -> ' delimiter raises ExtractorPassError."""
        story_id, aldric_cast_id, _mira_cast_id = story_with_relationship
        fake = _make_fake_caller(
            _fake_tool_response(
                {
                    "proposals": [
                        {
                            "kind": "soft_fact",
                            "target_domain": "relationship",
                            "target_natural_key": "AldricMira",
                            "target_field": "current_status_description",
                            "proposed_value": "allies",
                        }
                    ]
                }
            )
        )
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config(), fake)

        with pytest.raises(ExtractorPassError):
            service.extract(
                _make_assembled(story_id, aldric_cast_id),
                "prose.",
                story_id,
                _turn_id(),
            )

    def test_relationship_malformed_key_two_delimiters_raises(  # type: ignore[no-untyped-def]
        self, session, story_with_relationship
    ) -> None:
        """Relationship key with two ' -> ' delimiters raises ExtractorPassError."""
        story_id, aldric_cast_id, _mira_cast_id = story_with_relationship
        fake = _make_fake_caller(
            _fake_tool_response(
                {
                    "proposals": [
                        {
                            "kind": "soft_fact",
                            "target_domain": "relationship",
                            "target_natural_key": "Aldric -> Mira -> Vex",
                            "target_field": "current_status_description",
                            "proposed_value": "allies",
                        }
                    ]
                }
            )
        )
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config(), fake)

        with pytest.raises(ExtractorPassError):
            service.extract(
                _make_assembled(story_id, aldric_cast_id),
                "prose.",
                story_id,
                _turn_id(),
            )

    def test_relationship_unresolvable_subject_raises(  # type: ignore[no-untyped-def]
        self, session, story_with_relationship
    ) -> None:
        """Unresolvable subject name raises ExtractorPassError with no DB state."""
        story_id, aldric_cast_id, _mira_cast_id = story_with_relationship
        fake = _make_fake_caller(
            _fake_tool_response(
                {
                    "proposals": [
                        {
                            "kind": "soft_fact",
                            "target_domain": "relationship",
                            "target_natural_key": "UnknownPerson -> Mira",
                            "target_field": "current_status_description",
                            "proposed_value": "allies",
                        }
                    ]
                }
            )
        )
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config(), fake)

        with pytest.raises(ExtractorPassError):
            service.extract(
                _make_assembled(story_id, aldric_cast_id),
                "prose.",
                story_id,
                _turn_id(),
            )

        session.rollback()
        assert session.query(SBProvisionalStagingORM).all() == []

    def test_relationship_unresolvable_object_raises(  # type: ignore[no-untyped-def]
        self, session, story_with_relationship
    ) -> None:
        """Unresolvable object name raises ExtractorPassError with no DB state."""
        story_id, aldric_cast_id, _mira_cast_id = story_with_relationship
        fake = _make_fake_caller(
            _fake_tool_response(
                {
                    "proposals": [
                        {
                            "kind": "soft_fact",
                            "target_domain": "relationship",
                            "target_natural_key": "Aldric -> UnknownPerson",
                            "target_field": "current_status_description",
                            "proposed_value": "allies",
                        }
                    ]
                }
            )
        )
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config(), fake)

        with pytest.raises(ExtractorPassError):
            service.extract(
                _make_assembled(story_id, aldric_cast_id),
                "prose.",
                story_id,
                _turn_id(),
            )

        session.rollback()
        assert session.query(SBProvisionalStagingORM).all() == []

    def test_duplicate_active_relationship_rows_raises(  # type: ignore[no-untyped-def]
        self, session, story_with_relationship
    ) -> None:
        """Two active relationship rows for the same pair raises ExtractorPassError."""
        story_id, aldric_cast_id, mira_cast_id = story_with_relationship
        now = datetime(2026, 1, 1, tzinfo=UTC)
        sbs = StoryBibleService(session)
        # Seed a second active row for the same (subject, object) pair.
        duplicate_rel = RelationshipLedger(
            story_id=story_id,
            subject_cast_id=aldric_cast_id,
            object_cast_id=mira_cast_id,
            relationship_type=RelationshipType.ENEMY,
            current_status_description="Duplicate row",
            created_at=now,
            updated_at=now,
        )
        sbs.add_relationship(story_id, duplicate_rel)
        session.commit()

        fake = _make_fake_caller(
            _fake_tool_response(
                {
                    "proposals": [
                        {
                            "kind": "soft_fact",
                            "target_domain": "relationship",
                            "target_natural_key": "Aldric -> Mira",
                            "target_field": "current_status_description",
                            "proposed_value": "enemies now",
                        }
                    ]
                }
            )
        )
        service = ExtractorService(session, sbs, _make_config(), fake)

        with pytest.raises(ExtractorPassError):
            service.extract(
                _make_assembled(story_id, aldric_cast_id),
                "prose.",
                story_id,
                _turn_id(),
            )

        session.rollback()
        assert session.query(SBProvisionalStagingORM).all() == []


# ---------------------------------------------------------------------------
# World domain
# ---------------------------------------------------------------------------


class TestWorldDomain:
    def test_world_domain_raises_extractor_pass_error(  # type: ignore[no-untyped-def]
        self, session, story_and_cast
    ) -> None:
        """world domain raises ExtractorPassError; no DB state committed."""
        story_id, cast_id = story_and_cast
        fake = _make_fake_caller(
            _fake_tool_response(
                {
                    "proposals": [
                        {
                            "kind": "soft_fact",
                            "target_domain": "world",
                            "target_natural_key": "some_key",
                            "target_field": "any_field",
                            "proposed_value": "whatever",
                        }
                    ]
                }
            )
        )
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config(), fake)

        with pytest.raises(ExtractorPassError):
            service.extract(
                _make_assembled(story_id, cast_id),
                "prose.",
                story_id,
                _turn_id(),
            )

        session.rollback()
        assert session.query(SBProvisionalStagingORM).all() == []


# ---------------------------------------------------------------------------
# Transaction boundary (all-or-nothing invariant)
# ---------------------------------------------------------------------------


class TestTransactionBoundary:
    def test_partial_failure_leaves_no_db_state(  # type: ignore[no-untyped-def]
        self, session, story_and_cast
    ) -> None:
        """locked_fact (succeeds flush) + soft_fact with unknown name (fails) →
        zero rows after rollback; proves the all-or-nothing transaction boundary."""
        story_id, cast_id = story_and_cast
        fake = _make_fake_caller(
            _fake_tool_response(
                {
                    "proposals": [
                        {
                            "kind": "locked_fact",
                            "fact_text": "The fortress gates are sealed forever.",
                        },
                        {
                            "kind": "soft_fact",
                            "target_domain": "character",
                            "target_natural_key": "UnknownName",
                            "target_field": "current_location",
                            "proposed_value": "Somewhere",
                        },
                    ]
                }
            )
        )
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config(), fake)

        with pytest.raises(ExtractorPassError):
            service.extract(
                _make_assembled(story_id, cast_id),
                "The gates seal. UnknownName walks away.",
                story_id,
                _turn_id(),
            )

        # After rollback the locked_fact's flush must not have been committed.
        session.rollback()
        staging_rows = session.query(SBProvisionalStagingORM).all()
        assert (
            staging_rows == []
        ), "Partial DB state was committed — transaction boundary violated"
