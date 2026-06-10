"""Unit tests for ExtractorService — CRD Issue 10 / 14a.

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
TestRendererVolatileSuffix  — ProviderCallRequest structure checks
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import pytest

import afterworlds.persistence.orm.character_sheet  # noqa: F401
import afterworlds.persistence.orm.node  # noqa: F401
import afterworlds.persistence.orm.rules_package  # noqa: F401
import afterworlds.persistence.orm.session_state  # noqa: F401
import afterworlds.persistence.orm.state  # noqa: F401
import afterworlds.persistence.orm.story  # noqa: F401
import afterworlds.persistence.orm.story_bible  # noqa: F401
from afterworlds.entitlement.enums import ModelTier, PipelinePassId
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
from afterworlds.pipeline.extractor.caller import EXTRACT_TOOL_NAME
from afterworlds.pipeline.extractor.config import ExtractorConfig
from afterworlds.pipeline.extractor.models import ExtractorPassError, ExtractorResult
from afterworlds.pipeline.extractor.service import ExtractorService
from afterworlds.pipeline.provider._models import (
    ProviderCallRequest,
    ProviderCallResult,
    ProviderTextPart,
    ProviderToolCallPart,
)
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


def _fake_tool_result(
    tool_input: dict[str, Any] | None = None,
    input_token_count: int = 100,
    output_token_count: int = 50,
    cache_read_token_count: int | None = None,
    cache_creation_token_count: int | None = None,
) -> ProviderCallResult:
    return ProviderCallResult(
        pass_id=PipelinePassId.EXTRACTOR,
        provider_name="anthropic",
        model_identifier="anthropic:claude-haiku-test",
        model_tier=ModelTier.HAIKU,
        content_parts=[
            ProviderToolCallPart(
                tool_name=EXTRACT_TOOL_NAME,
                tool_input=tool_input if tool_input is not None else {"proposals": []},
            )
        ],
        input_token_count=input_token_count,
        output_token_count=output_token_count,
        cache_read_token_count=cache_read_token_count,
        cache_creation_token_count=cache_creation_token_count,
        cache_warmed=bool(cache_read_token_count),
        latency_ms=1,
    )


class _FakeProviderAdapter:
    """Capturing fake ProviderAdapter for ExtractorService tests."""

    def __init__(
        self,
        result: ProviderCallResult | None = None,
        raise_exc: Exception | None = None,
    ) -> None:
        self._result = result
        self._raise_exc = raise_exc
        self.captured_requests: list[ProviderCallRequest] = []
        self.provider_name = "anthropic"

    def call(self, request: ProviderCallRequest) -> ProviderCallResult:
        self.captured_requests.append(request)
        if self._raise_exc is not None:
            raise self._raise_exc
        return self._result or _fake_tool_result()


def _make_fake_adapter(
    result: ProviderCallResult | None = None,
    raise_exc: Exception | None = None,
) -> _FakeProviderAdapter:
    return _FakeProviderAdapter(result=result, raise_exc=raise_exc)


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
        adapter = _make_fake_adapter(
            _fake_tool_result(
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
        service = ExtractorService(session, sbs, _make_config())

        result = service.extract(
            _make_assembled(story_id, cast_id),
            "The king falls dead.",
            story_id,
            _turn_id(),
            provider=adapter,  # type: ignore[arg-type]
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
        adapter = _make_fake_adapter(
            _fake_tool_result(
                {
                    "proposals": [
                        {"kind": "locked_fact", "fact_text": "The bridge is destroyed."}
                    ]
                }
            )
        )
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config())

        result = service.extract(
            _make_assembled(story_id, cast_id),
            "The bridge falls.",
            story_id,
            _turn_id(),
            provider=adapter,  # type: ignore[arg-type]
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
        adapter = _make_fake_adapter(
            _fake_tool_result(
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
        service = ExtractorService(session, sbs, _make_config())

        result = service.extract(
            _make_assembled(story_id, cast_id),
            "Aldric is cut.",
            story_id,
            _turn_id(),
            provider=adapter,  # type: ignore[arg-type]
        )

        assert len(result.routed.soft_fact_staged_ids) == 1
        assert result.routed.locked_fact_staged_ids == []

    def test_soft_fact_applied_to_cast_dynamic_field(  # type: ignore[no-untyped-def]
        self, session, story_and_cast
    ) -> None:
        """A soft-fact update is applied to the cast entry's dynamic field."""
        story_id, cast_id = story_and_cast
        adapter = _make_fake_adapter(
            _fake_tool_result(
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
        service = ExtractorService(session, sbs, _make_config())

        service.extract(
            _make_assembled(story_id, cast_id),
            "Aldric enters the tower.",
            story_id,
            _turn_id(),
            provider=adapter,  # type: ignore[arg-type]
        )

        entry = sbs.get_character(story_id, cast_id)
        assert entry is not None
        assert entry.current_location == "The Dark Tower"

    def test_soft_fact_has_ratified_staging_row(  # type: ignore[no-untyped-def]
        self, session, story_and_cast
    ) -> None:
        """A RATIFIED audit staging row exists for each soft-fact update."""
        story_id, cast_id = story_and_cast
        adapter = _make_fake_adapter(
            _fake_tool_result(
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
        service = ExtractorService(session, sbs, _make_config())

        service.extract(
            _make_assembled(story_id, cast_id),
            "Aldric collapses exhausted.",
            story_id,
            _turn_id(),
            provider=adapter,  # type: ignore[arg-type]
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
        adapter = _make_fake_adapter(
            _fake_tool_result(
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
        service = ExtractorService(session, sbs, _make_config())

        result = service.extract(
            _make_assembled(story_id, cast_id),
            "Aldric walks the forest path.",
            story_id,
            _turn_id(),
            provider=adapter,  # type: ignore[arg-type]
        )

        assert len(result.routed.transient_state_staged_ids) == 1

    def test_transient_state_applied_to_cast_dynamic_field(  # type: ignore[no-untyped-def]
        self, session, story_and_cast
    ) -> None:
        """A transient-state update is applied to the cast entry's dynamic field."""
        story_id, cast_id = story_and_cast
        adapter = _make_fake_adapter(
            _fake_tool_result(
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
        service = ExtractorService(session, sbs, _make_config())

        service.extract(
            _make_assembled(story_id, cast_id),
            "Aldric reaches the market.",
            story_id,
            _turn_id(),
            provider=adapter,  # type: ignore[arg-type]
        )

        entry = sbs.get_character(story_id, cast_id)
        assert entry is not None
        assert entry.current_location == "The Market Square"

    def test_transient_state_has_ratified_staging_row(  # type: ignore[no-untyped-def]
        self, session, story_and_cast
    ) -> None:
        """A RATIFIED audit staging row exists for each transient-state update."""
        story_id, cast_id = story_and_cast
        adapter = _make_fake_adapter(
            _fake_tool_result(
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
        service = ExtractorService(session, sbs, _make_config())

        service.extract(
            _make_assembled(story_id, cast_id),
            "Aldric enters the vault.",
            story_id,
            _turn_id(),
            provider=adapter,  # type: ignore[arg-type]
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
        adapter = _make_fake_adapter(
            _fake_tool_result(
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
        service = ExtractorService(session, sbs, _make_config())

        result = service.extract(
            _make_assembled(story_id, cast_id),
            "A hooded figure watches.",
            story_id,
            _turn_id(),
            provider=adapter,  # type: ignore[arg-type]
        )

        assert len(result.routed.unresolved_thread_staged_ids) == 1

    def test_unresolved_thread_creates_thread_row(  # type: ignore[no-untyped-def]
        self, session, story_and_cast
    ) -> None:
        """An unresolved-thread proposal creates a row in sb_unresolved_threads."""
        story_id, cast_id = story_and_cast
        adapter = _make_fake_adapter(
            _fake_tool_result(
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
        service = ExtractorService(session, sbs, _make_config())

        service.extract(
            _make_assembled(story_id, cast_id),
            "The artefact is gone.",
            story_id,
            _turn_id(),
            provider=adapter,  # type: ignore[arg-type]
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
        adapter = _make_fake_adapter(
            _fake_tool_result(
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
        service = ExtractorService(session, sbs, _make_config())

        service.extract(
            _make_assembled(story_id, cast_id),
            "The gate is open.",
            story_id,
            _turn_id(),
            provider=adapter,  # type: ignore[arg-type]
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
        adapter = _make_fake_adapter(
            _fake_tool_result(
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
        service = ExtractorService(session, sbs, _make_config())

        result = service.extract(
            _make_assembled(story_id, cast_id),
            "Aldric crosses the bridge.",
            story_id,
            _turn_id(),
            provider=adapter,  # type: ignore[arg-type]
        )

        assert len(result.routed.event_ids) == 1

    def test_event_creates_event_row_with_event_kind(  # type: ignore[no-untyped-def]
        self, session, story_and_cast
    ) -> None:
        """An event proposal creates a row in sb_events with the correct event_kind."""
        story_id, cast_id = story_and_cast
        adapter = _make_fake_adapter(
            _fake_tool_result(
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
        service = ExtractorService(session, sbs, _make_config())

        service.extract(
            _make_assembled(story_id, cast_id),
            "The Night Warden falls.",
            story_id,
            _turn_id(),
            provider=adapter,  # type: ignore[arg-type]
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
        adapter = _make_fake_adapter(
            _fake_tool_result(
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
        service = ExtractorService(session, sbs, _make_config())

        service.extract(
            _make_assembled(story_id, cast_id),
            "The prophecy becomes clear.",
            story_id,
            _turn_id(),
            provider=adapter,  # type: ignore[arg-type]
        )

        staging_rows = session.query(SBProvisionalStagingORM).all()
        assert staging_rows == [], "Event created a staging row — should bypass staging"

    def test_event_id_matches_db_row(  # type: ignore[no-untyped-def]
        self, session, story_and_cast
    ) -> None:
        """routed.event_ids[0] matches the event_id column in sb_events."""
        story_id, cast_id = story_and_cast
        adapter = _make_fake_adapter(
            _fake_tool_result(
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
        service = ExtractorService(session, sbs, _make_config())

        result = service.extract(
            _make_assembled(story_id, cast_id),
            "A stranger appears.",
            story_id,
            _turn_id(),
            provider=adapter,  # type: ignore[arg-type]
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
        adapter = _make_fake_adapter(
            _fake_tool_result(
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
        service = ExtractorService(session, sbs, _make_config())

        with pytest.raises(ExtractorPassError) as exc_info:
            service.extract(
                _make_assembled(story_id, cast_id),
                "The unknown hero walks.",
                story_id,
                _turn_id(),
                provider=adapter,  # type: ignore[arg-type]
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
        adapter = _make_fake_adapter(
            _fake_tool_result(
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
        service = ExtractorService(session, sbs, _make_config())

        with pytest.raises(ExtractorPassError):
            service.extract(
                _make_assembled(story_id, cast_id),
                "The ghost walks.",
                story_id,
                _turn_id(),
                provider=adapter,  # type: ignore[arg-type]
            )

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
        duplicate = CastEntry(
            story_id=story_id,
            name="aldric",
            role=CastRole.MINOR,
            created_at=now,
        )
        sbs.add_cast_entry(story_id, duplicate)
        session.commit()

        adapter = _make_fake_adapter(
            _fake_tool_result(
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
        service = ExtractorService(session, sbs, _make_config())

        with pytest.raises(ExtractorPassError):
            service.extract(
                _make_assembled(story_id, cast_id),
                "prose.",
                story_id,
                _turn_id(),
                provider=adapter,  # type: ignore[arg-type]
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
        adapter = _make_fake_adapter(_fake_tool_result())
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config())

        with pytest.raises(ExtractorPassError) as exc_info:
            service.extract(
                _make_assembled(story_id, cast_id),
                "prose.",
                wrong_story_id,
                _turn_id(),
                provider=adapter,  # type: ignore[arg-type]
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
        adapter = _make_fake_adapter(_fake_tool_result({"proposals": []}))
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config())

        result = service.extract(
            _make_assembled(story_id, cast_id),
            "Nothing changed.",
            story_id,
            _turn_id(),
            provider=adapter,  # type: ignore[arg-type]
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
        adapter = _make_fake_adapter(_fake_tool_result({"proposals": []}))
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config())

        result = service.extract(
            _make_assembled(story_id, cast_id),
            "Nothing changed.",
            story_id,
            _turn_id(),
            provider=adapter,  # type: ignore[arg-type]
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
        adapter = _make_fake_adapter(
            _fake_tool_result(
                {
                    "proposals": [
                        {"kind": "locked_fact", "fact_text": "The wall has fallen."}
                    ]
                }
            )
        )
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config())

        service.extract(
            _make_assembled(story_id, cast_id),
            "The wall falls.",
            story_id,
            _turn_id(),
            provider=adapter,  # type: ignore[arg-type]
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
        adapter = _make_fake_adapter(
            _fake_tool_result(
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
        service = ExtractorService(session, sbs, _make_config())

        service.extract(
            _make_assembled(story_id, cast_id),
            "A fight breaks out.",
            story_id,
            _turn_id(),
            provider=adapter,  # type: ignore[arg-type]
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
        adapter = _make_fake_adapter(
            _fake_tool_result(
                {"proposals": []},
                input_token_count=200,
                output_token_count=80,
                cache_read_token_count=150,
                cache_creation_token_count=50,
            )
        )
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config())

        result = service.extract(
            _make_assembled(story_id, cast_id),
            "prose.",
            story_id,
            _turn_id(),
            provider=adapter,  # type: ignore[arg-type]
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
        adapter = _make_fake_adapter(
            _fake_tool_result(
                {"proposals": []},
                input_token_count=100,
                output_token_count=40,
                cache_read_token_count=None,
                cache_creation_token_count=None,
            )
        )
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config())

        result = service.extract(
            _make_assembled(story_id, cast_id),
            "prose.",
            story_id,
            _turn_id(),
            provider=adapter,  # type: ignore[arg-type]
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
        adapter = _make_fake_adapter(raise_exc=original_exc)
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config())

        with pytest.raises(ExtractorPassError) as exc_info:
            service.extract(
                _make_assembled(story_id, cast_id),
                "prose.",
                story_id,
                _turn_id(),
                provider=adapter,  # type: ignore[arg-type]
            )

        assert exc_info.value.__cause__ is original_exc

    def test_no_tool_use_block_raises_extractor_pass_error(  # type: ignore[no-untyped-def]
        self, session, story_and_cast
    ) -> None:
        """Response with no tool-use block raises ExtractorPassError."""
        story_id, cast_id = story_and_cast

        text_only_result = ProviderCallResult(
            pass_id=PipelinePassId.EXTRACTOR,
            provider_name="anthropic",
            model_identifier="anthropic:claude-haiku-test",
            model_tier=ModelTier.HAIKU,
            content_parts=[ProviderTextPart(text="I extracted nothing.")],
            input_token_count=10,
            output_token_count=5,
            cache_read_token_count=None,
            cache_creation_token_count=None,
            cache_warmed=False,
            latency_ms=1,
        )
        adapter = _make_fake_adapter(text_only_result)
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config())

        with pytest.raises(ExtractorPassError):
            service.extract(
                _make_assembled(story_id, cast_id),
                "prose.",
                story_id,
                _turn_id(),
                provider=adapter,  # type: ignore[arg-type]
            )

    def test_fake_adapter_receives_tool_spec(  # type: ignore[no-untyped-def]
        self, session, story_and_cast
    ) -> None:
        """The injected adapter receives a ProviderCallRequest with the extractor
        tool."""
        story_id, cast_id = story_and_cast
        adapter = _make_fake_adapter(_fake_tool_result())
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config())

        service.extract(
            _make_assembled(story_id, cast_id),
            "prose.",
            story_id,
            _turn_id(),
            provider=adapter,  # type: ignore[arg-type]
        )

        assert len(adapter.captured_requests) == 1
        request = adapter.captured_requests[0]
        assert len(request.tool_definitions) == 1
        assert request.tool_definitions[0].name == EXTRACT_TOOL_NAME
        assert request.tool_definitions[0].name == "propose_canon_updates"

    def test_result_is_typed_extractor_result(  # type: ignore[no-untyped-def]
        self, session, story_and_cast
    ) -> None:
        """extract() returns a typed ExtractorResult."""
        story_id, cast_id = story_and_cast
        adapter = _make_fake_adapter(_fake_tool_result())
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config())

        result = service.extract(
            _make_assembled(story_id, cast_id),
            "prose.",
            story_id,
            _turn_id(),
            provider=adapter,  # type: ignore[arg-type]
        )

        assert isinstance(result, ExtractorResult)

    def test_missing_proposals_key_raises_extractor_pass_error(  # type: ignore[no-untyped-def]
        self, session, story_and_cast
    ) -> None:
        """Missing 'proposals' key in tool response raises ExtractorPassError."""
        story_id, cast_id = story_and_cast
        missing_proposals_result = ProviderCallResult(
            pass_id=PipelinePassId.EXTRACTOR,
            provider_name="anthropic",
            model_identifier="anthropic:claude-haiku-test",
            model_tier=ModelTier.HAIKU,
            content_parts=[
                ProviderToolCallPart(
                    tool_name=EXTRACT_TOOL_NAME,
                    tool_input={},
                )
            ],
            input_token_count=10,
            output_token_count=5,
            cache_read_token_count=None,
            cache_creation_token_count=None,
            cache_warmed=False,
            latency_ms=1,
        )
        adapter = _make_fake_adapter(missing_proposals_result)
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config())

        with pytest.raises(ExtractorPassError):
            service.extract(
                _make_assembled(story_id, cast_id),
                "prose.",
                story_id,
                _turn_id(),
                provider=adapter,  # type: ignore[arg-type]
            )

    def test_first_tool_part_used_when_multiple_present(  # type: ignore[no-untyped-def]
        self, session, story_and_cast
    ) -> None:
        """When multiple tool-call parts are present, the first is used (no error)."""
        story_id, cast_id = story_and_cast
        two_part_result = ProviderCallResult(
            pass_id=PipelinePassId.EXTRACTOR,
            provider_name="anthropic",
            model_identifier="anthropic:claude-haiku-test",
            model_tier=ModelTier.HAIKU,
            content_parts=[
                ProviderToolCallPart(
                    tool_name=EXTRACT_TOOL_NAME,
                    tool_input={"proposals": []},
                ),
                ProviderToolCallPart(
                    tool_name=EXTRACT_TOOL_NAME,
                    tool_input={"proposals": []},
                ),
            ],
            input_token_count=10,
            output_token_count=5,
            cache_read_token_count=None,
            cache_creation_token_count=None,
            cache_warmed=False,
            latency_ms=1,
        )
        adapter = _make_fake_adapter(two_part_result)
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config())

        result = service.extract(
            _make_assembled(story_id, cast_id),
            "prose.",
            story_id,
            _turn_id(),
            provider=adapter,  # type: ignore[arg-type]
        )

        assert isinstance(result, ExtractorResult)


# ---------------------------------------------------------------------------
# Boolean proposed_value (is_alive)
# ---------------------------------------------------------------------------


class TestBooleanProposedValue:
    def test_is_alive_false_routes_as_boolean(  # type: ignore[no-untyped-def]
        self, session, story_and_cast
    ) -> None:
        """soft_fact with is_alive=False (JSON boolean) writes False to cast row."""
        story_id, cast_id = story_and_cast
        adapter = _make_fake_adapter(
            _fake_tool_result(
                {
                    "proposals": [
                        {
                            "kind": "soft_fact",
                            "target_domain": "character",
                            "target_natural_key": "Aldric",
                            "target_field": "is_alive",
                            "proposed_value": False,
                        }
                    ]
                }
            )
        )
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config())

        result = service.extract(
            _make_assembled(story_id, cast_id),
            "Aldric falls dead.",
            story_id,
            _turn_id(),
            provider=adapter,  # type: ignore[arg-type]
        )

        assert len(result.routed.soft_fact_staged_ids) == 1
        entry = sbs.get_character(story_id, cast_id)
        assert entry is not None
        assert entry.is_alive is False

    def test_is_alive_true_routes_as_boolean(  # type: ignore[no-untyped-def]
        self, session, story_and_cast
    ) -> None:
        """transient_state with is_alive=True (JSON boolean) writes True to cast row."""
        story_id, cast_id = story_and_cast
        adapter = _make_fake_adapter(
            _fake_tool_result(
                {
                    "proposals": [
                        {
                            "kind": "transient_state",
                            "target_domain": "character",
                            "target_natural_key": "Aldric",
                            "target_field": "is_alive",
                            "proposed_value": True,
                        }
                    ]
                }
            )
        )
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config())

        result = service.extract(
            _make_assembled(story_id, cast_id),
            "Aldric lives.",
            story_id,
            _turn_id(),
            provider=adapter,  # type: ignore[arg-type]
        )

        assert len(result.routed.transient_state_staged_ids) == 1
        entry = sbs.get_character(story_id, cast_id)
        assert entry is not None
        assert entry.is_alive is True

    def test_boolean_for_string_field_raises(  # type: ignore[no-untyped-def]
        self, session, story_and_cast
    ) -> None:
        """Boolean proposed_value for current_location raises ExtractorPassError."""
        story_id, cast_id = story_and_cast
        adapter = _make_fake_adapter(
            _fake_tool_result(
                {
                    "proposals": [
                        {
                            "kind": "soft_fact",
                            "target_domain": "character",
                            "target_natural_key": "Aldric",
                            "target_field": "current_location",
                            "proposed_value": False,
                        }
                    ]
                }
            )
        )
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config())

        with pytest.raises(ExtractorPassError):
            service.extract(
                _make_assembled(story_id, cast_id),
                "prose.",
                story_id,
                _turn_id(),
                provider=adapter,  # type: ignore[arg-type]
            )

        session.rollback()
        assert session.query(SBProvisionalStagingORM).all() == []

    def test_boolean_for_notes_raises(  # type: ignore[no-untyped-def]
        self, session, story_and_cast
    ) -> None:
        """Boolean proposed_value for notes raises ExtractorPassError; no DB state."""
        story_id, cast_id = story_and_cast
        adapter = _make_fake_adapter(
            _fake_tool_result(
                {
                    "proposals": [
                        {
                            "kind": "transient_state",
                            "target_domain": "character",
                            "target_natural_key": "Aldric",
                            "target_field": "notes",
                            "proposed_value": False,
                        }
                    ]
                }
            )
        )
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config())

        with pytest.raises(ExtractorPassError):
            service.extract(
                _make_assembled(story_id, cast_id),
                "prose.",
                story_id,
                _turn_id(),
                provider=adapter,  # type: ignore[arg-type]
            )

        session.rollback()
        assert session.query(SBProvisionalStagingORM).all() == []

    def test_boolean_for_relationship_field_raises(  # type: ignore[no-untyped-def]
        self, session, story_with_relationship
    ) -> None:
        """Boolean for current_status_description raises ExtractorPassError."""
        story_id, aldric_cast_id, _mira_cast_id = story_with_relationship
        adapter = _make_fake_adapter(
            _fake_tool_result(
                {
                    "proposals": [
                        {
                            "kind": "soft_fact",
                            "target_domain": "relationship",
                            "target_natural_key": "Aldric -> Mira",
                            "target_field": "current_status_description",
                            "proposed_value": False,
                        }
                    ]
                }
            )
        )
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config())

        with pytest.raises(ExtractorPassError):
            service.extract(
                _make_assembled(story_id, aldric_cast_id),
                "prose.",
                story_id,
                _turn_id(),
                provider=adapter,  # type: ignore[arg-type]
            )

        session.rollback()
        assert session.query(SBProvisionalStagingORM).all() == []


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
        adapter = _make_fake_adapter(
            _fake_tool_result(
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
        service = ExtractorService(session, sbs, _make_config())

        result = service.extract(
            _make_assembled(story_id, aldric_cast_id),
            "Aldric eyes Mira with suspicion.",
            story_id,
            _turn_id(),
            provider=adapter,  # type: ignore[arg-type]
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
        adapter = _make_fake_adapter(
            _fake_tool_result(
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
        service = ExtractorService(session, sbs, _make_config())

        with pytest.raises(ExtractorPassError):
            service.extract(
                _make_assembled(story_id, aldric_cast_id),
                "prose.",
                story_id,
                _turn_id(),
                provider=adapter,  # type: ignore[arg-type]
            )

    def test_relationship_malformed_key_two_delimiters_raises(  # type: ignore[no-untyped-def]
        self, session, story_with_relationship
    ) -> None:
        """Relationship key with two ' -> ' delimiters raises ExtractorPassError."""
        story_id, aldric_cast_id, _mira_cast_id = story_with_relationship
        adapter = _make_fake_adapter(
            _fake_tool_result(
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
        service = ExtractorService(session, sbs, _make_config())

        with pytest.raises(ExtractorPassError):
            service.extract(
                _make_assembled(story_id, aldric_cast_id),
                "prose.",
                story_id,
                _turn_id(),
                provider=adapter,  # type: ignore[arg-type]
            )

    def test_relationship_unresolvable_subject_raises(  # type: ignore[no-untyped-def]
        self, session, story_with_relationship
    ) -> None:
        """Unresolvable subject name raises ExtractorPassError with no DB state."""
        story_id, aldric_cast_id, _mira_cast_id = story_with_relationship
        adapter = _make_fake_adapter(
            _fake_tool_result(
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
        service = ExtractorService(session, sbs, _make_config())

        with pytest.raises(ExtractorPassError):
            service.extract(
                _make_assembled(story_id, aldric_cast_id),
                "prose.",
                story_id,
                _turn_id(),
                provider=adapter,  # type: ignore[arg-type]
            )

        session.rollback()
        assert session.query(SBProvisionalStagingORM).all() == []

    def test_relationship_unresolvable_object_raises(  # type: ignore[no-untyped-def]
        self, session, story_with_relationship
    ) -> None:
        """Unresolvable object name raises ExtractorPassError with no DB state."""
        story_id, aldric_cast_id, _mira_cast_id = story_with_relationship
        adapter = _make_fake_adapter(
            _fake_tool_result(
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
        service = ExtractorService(session, sbs, _make_config())

        with pytest.raises(ExtractorPassError):
            service.extract(
                _make_assembled(story_id, aldric_cast_id),
                "prose.",
                story_id,
                _turn_id(),
                provider=adapter,  # type: ignore[arg-type]
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

        adapter = _make_fake_adapter(
            _fake_tool_result(
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
        service = ExtractorService(session, sbs, _make_config())

        with pytest.raises(ExtractorPassError):
            service.extract(
                _make_assembled(story_id, aldric_cast_id),
                "prose.",
                story_id,
                _turn_id(),
                provider=adapter,  # type: ignore[arg-type]
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
        adapter = _make_fake_adapter(
            _fake_tool_result(
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
        service = ExtractorService(session, sbs, _make_config())

        with pytest.raises(ExtractorPassError):
            service.extract(
                _make_assembled(story_id, cast_id),
                "prose.",
                story_id,
                _turn_id(),
                provider=adapter,  # type: ignore[arg-type]
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
        adapter = _make_fake_adapter(
            _fake_tool_result(
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
        service = ExtractorService(session, sbs, _make_config())

        with pytest.raises(ExtractorPassError):
            service.extract(
                _make_assembled(story_id, cast_id),
                "The gates seal. UnknownName walks away.",
                story_id,
                _turn_id(),
                provider=adapter,  # type: ignore[arg-type]
            )

        session.rollback()
        staging_rows = session.query(SBProvisionalStagingORM).all()
        assert (
            staging_rows == []
        ), "Partial DB state was committed — transaction boundary violated"


# ---------------------------------------------------------------------------
# Renderer — volatile suffix intent block (ProviderCallRequest checks)
# ---------------------------------------------------------------------------


class TestRendererVolatileSuffix:
    def test_intent_included_in_rendered_blocks(  # type: ignore[no-untyped-def]
        self, session, story_and_cast
    ) -> None:
        """_render() must include classified_intent after current_input.

        The volatile suffix block must contain both 'Player:' and '[Intent:'
        so the Extractor model sees the same intent annotation as the Writer.
        """
        story_id, cast_id = story_and_cast
        adapter = _make_fake_adapter(_fake_tool_result())
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config())

        service.extract(
            _make_assembled(story_id, cast_id),
            "prose.",
            story_id,
            _turn_id(),
            provider=adapter,  # type: ignore[arg-type]
        )

        assert len(adapter.captured_requests) == 1
        request = adapter.captured_requests[0]
        intent_blocks = [b for b in request.rendered_blocks if "[Intent:" in b.text]
        assert len(intent_blocks) == 1, "Expected exactly one block with [Intent:]"
        intent_block_text = intent_blocks[0].text
        assert "Player: I push open the door." in intent_block_text
        assert "[Intent: in_character_action]" in intent_block_text

    def test_intent_block_precedes_writer_output(  # type: ignore[no-untyped-def]
        self, session, story_and_cast
    ) -> None:
        """The intent block appears before [WRITER OUTPUT] in the rendered blocks."""
        story_id, cast_id = story_and_cast
        adapter = _make_fake_adapter(_fake_tool_result())
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config())

        service.extract(
            _make_assembled(story_id, cast_id),
            "prose.",
            story_id,
            _turn_id(),
            provider=adapter,  # type: ignore[arg-type]
        )

        request = adapter.captured_requests[0]
        texts = [b.text for b in request.rendered_blocks]
        intent_idx = next(i for i, t in enumerate(texts) if "[Intent:" in t)
        writer_idx = next(i for i, t in enumerate(texts) if "[WRITER OUTPUT]" in t)
        assert intent_idx < writer_idx, "Intent block must precede writer output"

    def test_system_blocks_contain_extractor_pass_prompt(  # type: ignore[no-untyped-def]
        self, session, story_and_cast
    ) -> None:
        """system_blocks[0] must be the Extractor pass prompt, not the mode contract."""
        story_id, cast_id = story_and_cast
        adapter = _make_fake_adapter(_fake_tool_result())
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config())

        service.extract(
            _make_assembled(story_id, cast_id),
            "prose.",
            story_id,
            _turn_id(),
            provider=adapter,  # type: ignore[arg-type]
        )

        request = adapter.captured_requests[0]
        assert "Extractor" in request.system_blocks[0].text

    def test_mode_contract_is_second_system_block(  # type: ignore[no-untyped-def]
        self, session, story_and_cast
    ) -> None:
        """Issue 12c: mode contract in system_blocks[1]."""
        story_id, cast_id = story_and_cast
        adapter = _make_fake_adapter(_fake_tool_result())
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config())

        ctx = _make_assembled(story_id, cast_id)
        service.extract(
            ctx,
            "prose.",
            story_id,
            _turn_id(),
            provider=adapter,  # type: ignore[arg-type]
        )

        request = adapter.captured_requests[0]
        assert len(request.system_blocks) == 2
        assert request.system_blocks[1].text == "You are the story architect."

    def test_mode_contract_absent_from_rendered_blocks(  # type: ignore[no-untyped-def]
        self, session, story_and_cast
    ) -> None:
        """Issue 12c: mode contract no longer duplicated into rendered_blocks."""
        story_id, cast_id = story_and_cast
        adapter = _make_fake_adapter(_fake_tool_result())
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config())

        ctx = _make_assembled(story_id, cast_id)
        service.extract(
            ctx,
            "prose.",
            story_id,
            _turn_id(),
            provider=adapter,  # type: ignore[arg-type]
        )

        request = adapter.captured_requests[0]
        assert not any(
            "You are the story architect." in b.text for b in request.rendered_blocks
        ), "Mode contract must not appear in rendered_blocks after 12c"

    def test_cache_breakpoint_precedes_writer_output_and_volatile(  # type: ignore[no-untyped-def]
        self, session, story_and_cast
    ) -> None:
        """Cache breakpoint on the final stable-prefix block, not writer/volatile."""
        story_id, cast_id = story_and_cast
        adapter = _make_fake_adapter(_fake_tool_result())
        sbs = StoryBibleService(session)
        service = ExtractorService(session, sbs, _make_config())

        service.extract(
            _make_assembled(story_id, cast_id),
            "prose.",
            story_id,
            _turn_id(),
            provider=adapter,  # type: ignore[arg-type]
        )

        request = adapter.captured_requests[0]
        blocks = request.rendered_blocks
        cache_idx = next(
            (i for i, b in enumerate(blocks) if b.has_cache_breakpoint),
            None,
        )
        writer_idx = next(
            (i for i, b in enumerate(blocks) if "[WRITER OUTPUT]" in b.text),
            None,
        )
        volatile_idx = next(
            (i for i, b in enumerate(blocks) if "[Intent:" in b.text),
            None,
        )
        assert cache_idx is not None, "No cache breakpoint block found"
        assert writer_idx is not None, "No writer output block found"
        assert volatile_idx is not None, "No volatile suffix block found"
        assert cache_idx < writer_idx, "Cache breakpoint must precede writer output"
        assert cache_idx < volatile_idx, "Cache breakpoint must precede volatile suffix"
