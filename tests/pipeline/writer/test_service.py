"""Unit tests for WriterService — CRD Issue 9.

Coverage targets (from the Issue 9 test requirements):
  - Happy path: valid context + fake caller → WriterResult with populated output
    and a persisted Turn linked to the supplied node_id
  - Text concatenation: multiple text blocks concatenated in order
  - Whitespace trimming: leading/trailing whitespace trimmed
  - Empty-after-trim: whitespace-only blocks raise WriterPassError, no Turn
  - Malformed envelope: non-Message response raises WriterPassError, no Turn
  - Provider exception: caller raises → WriterPassError wrapping original, no Turn
  - Model caller injection: fake is invoked; no real network call
  - Cache metrics propagation: usage fields surface correctly; None when absent
  - Turn persistence round-trip: ICR, user_input, assistant_output, node_id
  - Lineage validation: mismatched or nonexistent node raises WriterPassError, no Turn
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from anthropic.types import Message, TextBlock, Usage

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
from afterworlds.models.enums import CastRole, IntentType, StoryMode
from afterworlds.models.intent_classification import IntentClassificationResult
from afterworlds.models.story import Arc, Chapter, Story
from afterworlds.models.story_bible import CastEntry, StoryBibleContext
from afterworlds.persistence.crud.node import create_node, get_turn
from afterworlds.persistence.crud.story import create_arc, create_chapter, create_story
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.persistence.orm.base import Base
from afterworlds.pipeline.writer.caller import AnthropicMessagesPayload
from afterworlds.pipeline.writer.config import WriterConfig
from afterworlds.pipeline.writer.models import WriterPassError, WriterResult
from afterworlds.pipeline.writer.service import WriterService

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def engine():  # type: ignore[no-untyped-def]
    """In-memory SQLite engine with all tables created from ORM metadata."""
    eng = create_engine("sqlite://")
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)
    eng.dispose()


@pytest.fixture()
def session(engine):  # type: ignore[no-untyped-def]
    """SQLAlchemy session bound to the in-memory engine."""
    factory = create_session_factory(engine)
    sess = factory()
    try:
        yield sess
    finally:
        sess.close()


@pytest.fixture()
def seeded_ids(session):  # type: ignore[no-untyped-def]
    """Seed Story → Arc → Chapter → Node; return (story_id, node_id)."""
    from afterworlds.models.node import Node

    now = datetime(2026, 1, 1, tzinfo=UTC)
    story = Story(
        title="Test Story",
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
    return story.story_id, node.node_id


def _make_icr(
    intent: IntentType = IntentType.IN_CHARACTER_ACTION,
    raw_input: str = "I push the door.",
) -> IntentClassificationResult:
    return IntentClassificationResult(
        intent_type=intent,
        confidence=0.90,
        raw_input=raw_input,
        ambiguous=False,
    )


def _make_assembled(
    raw_input: str = "I push the door.",
    story_id: UUID | None = None,
) -> AssembledContext:
    sid = story_id if story_id is not None else uuid4()
    context = StoryBibleContext(
        story_id=sid,
        setting=None,
        cast=(
            CastEntry(
                story_id=sid,
                name="Aldric",
                role=CastRole.PROTAGONIST,
                created_at=datetime(2026, 1, 1, tzinfo=UTC),
            ),
        ),
        locked_facts=(),
        forbidden_facts=(),
        relationship_ledger=(),
        active_plot_threads=(),
        events=(),
    )
    sp = StablePrefix(
        system_prompt="You are the story architect.",
        story_bible_context=context,
        rolling_summary_text=None,
        rules_package_slice=None,
        retrieval_memory=RetrievalMemoryPayload(),
    )
    vs = VolatileSuffix(
        recent_turns=[],
        current_input=raw_input,
        classified_intent=_make_icr(raw_input=raw_input),
    )
    return AssembledContext(
        stable_prefix=sp,
        volatile_suffix=vs,
        pass_forward_ledger=PassForwardLedger(),
    )


def _make_config() -> WriterConfig:
    return WriterConfig(
        model="claude-sonnet-test",
        api_key_env="ANTHROPIC_API_KEY",
        extended_ttl=True,
    )


def _fake_message(
    text: str = "The door swings open.",
    input_tokens: int = 100,
    output_tokens: int = 50,
    cache_read_input_tokens: int | None = None,
    cache_creation_input_tokens: int | None = None,
) -> Message:
    return Message(
        id="msg_fake",
        type="message",
        role="assistant",
        content=[TextBlock(type="text", text=text)],
        model="claude-sonnet-4-5-20251001",
        stop_reason="end_turn",
        stop_sequence=None,
        usage=Usage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_read_input_tokens=cache_read_input_tokens,
            cache_creation_input_tokens=cache_creation_input_tokens,
        ),
    )


def _make_fake_caller(  # type: ignore[no-untyped-def]
    response: Message | None = None, raise_exc: Exception | None = None
):
    """Return a fake WriterModelCaller callable."""
    captured: list[AnthropicMessagesPayload] = []

    def caller(payload: AnthropicMessagesPayload) -> Message:
        captured.append(payload)
        if raise_exc is not None:
            raise raise_exc
        return response or _fake_message()

    caller.captured = captured  # type: ignore[attr-defined]
    return caller


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


class TestHappyPath:
    def test_write_returns_writer_result(self, session, seeded_ids) -> None:  # type: ignore[no-untyped-def]
        """write() returns a WriterResult with non-empty assistant_output."""
        story_id, node_id = seeded_ids
        fake = _make_fake_caller(_fake_message("The door swings open with a groan."))
        service = WriterService(session, _make_config(), fake)

        result = service.write(_make_assembled(story_id=story_id), story_id, node_id)

        assert isinstance(result, WriterResult)
        assert result.assistant_output == "The door swings open with a groan."
        assert result.turn_id is not None

    def test_turn_persisted_linked_to_node(self, session, seeded_ids) -> None:  # type: ignore[no-untyped-def]
        """A Turn row is persisted and linked to the supplied node_id."""
        story_id, node_id = seeded_ids
        fake = _make_fake_caller(_fake_message("You enter the chamber."))
        service = WriterService(session, _make_config(), fake)
        assembled = _make_assembled("Enter the chamber.", story_id=story_id)

        result = service.write(assembled, story_id, node_id)

        fetched = get_turn(session, result.turn_id)
        assert fetched is not None
        assert fetched.node_id == node_id
        assert fetched.assistant_output == "You enter the chamber."
        assert fetched.user_input == "Enter the chamber."

    def test_turn_user_input_matches_assembled_input(  # type: ignore[no-untyped-def]
        self, session, seeded_ids
    ) -> None:
        """Persisted Turn.user_input matches the current_input from AssembledContext."""
        story_id, node_id = seeded_ids
        raw = "What do I see?"
        fake = _make_fake_caller()
        service = WriterService(session, _make_config(), fake)

        result = service.write(
            _make_assembled(raw, story_id=story_id), story_id, node_id
        )

        fetched = get_turn(session, result.turn_id)
        assert fetched is not None
        assert fetched.user_input == raw

    def test_turn_icr_round_trips(self, session, seeded_ids) -> None:  # type: ignore[no-untyped-def]
        """ICR round-trips as typed IntentClassificationResult, not as a string."""
        story_id, node_id = seeded_ids
        assembled = _make_assembled("I attack.", story_id=story_id)
        icr = IntentClassificationResult(
            intent_type=IntentType.IN_CHARACTER_ACTION,
            confidence=0.88,
            raw_input="I attack.",
            ambiguous=False,
        )

        vs = VolatileSuffix(
            recent_turns=[],
            current_input="I attack.",
            classified_intent=icr,
        )
        assembled_with_icr = AssembledContext(
            stable_prefix=assembled.stable_prefix,
            volatile_suffix=vs,
            pass_forward_ledger=PassForwardLedger(),
        )

        fake = _make_fake_caller()
        service = WriterService(session, _make_config(), fake)
        result = service.write(assembled_with_icr, story_id, node_id)

        fetched = get_turn(session, result.turn_id)
        assert fetched is not None
        assert fetched.intent_classification_result is not None
        assert isinstance(
            fetched.intent_classification_result, IntentClassificationResult
        )
        assert (
            fetched.intent_classification_result.intent_type
            == IntentType.IN_CHARACTER_ACTION
        )
        assert abs(fetched.intent_classification_result.confidence - 0.88) < 1e-6
        assert fetched.intent_classification_result.raw_input == "I attack."

    def test_return_turn_id_matches_persisted_row(  # type: ignore[no-untyped-def]
        self, session, seeded_ids
    ) -> None:
        """The turn_id in WriterResult matches the persisted Turn row."""
        story_id, node_id = seeded_ids
        fake = _make_fake_caller()
        service = WriterService(session, _make_config(), fake)

        result = service.write(_make_assembled(story_id=story_id), story_id, node_id)

        fetched = get_turn(session, result.turn_id)
        assert fetched is not None
        assert fetched.turn_id == result.turn_id


# ---------------------------------------------------------------------------
# Text concatenation and trimming
# ---------------------------------------------------------------------------


class TestParsing:
    def test_multiple_text_blocks_concatenated_in_order(  # type: ignore[no-untyped-def]
        self, session, seeded_ids
    ) -> None:
        """Multiple text blocks are concatenated in order, not reordered."""
        story_id, node_id = seeded_ids
        multi_block_msg = Message(
            id="msg_multi",
            type="message",
            role="assistant",
            content=[
                TextBlock(type="text", text="Part one."),
                TextBlock(type="text", text=" Part two."),
                TextBlock(type="text", text=" Part three."),
            ],
            model="claude-sonnet-4-5-20251001",
            stop_reason="end_turn",
            stop_sequence=None,
            usage=Usage(input_tokens=10, output_tokens=5),
        )
        fake = _make_fake_caller(multi_block_msg)
        service = WriterService(session, _make_config(), fake)

        result = service.write(_make_assembled(story_id=story_id), story_id, node_id)

        assert result.assistant_output == "Part one. Part two. Part three."

    def test_whitespace_trimmed(self, session, seeded_ids) -> None:  # type: ignore[no-untyped-def]
        """Leading and trailing whitespace is trimmed from the concatenated output."""
        story_id, node_id = seeded_ids
        msg = _fake_message(text="  \n  The room is dark.  \n  ")
        fake = _make_fake_caller(msg)
        service = WriterService(session, _make_config(), fake)

        result = service.write(_make_assembled(story_id=story_id), story_id, node_id)

        assert result.assistant_output == "The room is dark."

    def test_empty_after_trim_raises_writer_pass_error(  # type: ignore[no-untyped-def]
        self, session, seeded_ids
    ) -> None:
        """Whitespace-only response raises WriterPassError; no Turn persisted."""
        story_id, node_id = seeded_ids
        msg = _fake_message(text="   \n   ")
        fake = _make_fake_caller(msg)
        service = WriterService(session, _make_config(), fake)

        with pytest.raises(WriterPassError):
            service.write(_make_assembled(story_id=story_id), story_id, node_id)

        from afterworlds.persistence.orm.node import TurnORM

        rows = session.query(TurnORM).filter(TurnORM.node_id == str(node_id)).all()
        assert rows == []

    def test_malformed_response_raises_writer_pass_error(  # type: ignore[no-untyped-def]
        self, session, seeded_ids
    ) -> None:
        """Non-Message response raises WriterPassError with cause; no Turn persisted."""
        story_id, node_id = seeded_ids

        def bad_caller(payload: AnthropicMessagesPayload) -> object:  # type: ignore[return]
            return {"not": "a message"}

        service = WriterService(session, _make_config(), bad_caller)  # type: ignore[arg-type]

        with pytest.raises(WriterPassError):
            service.write(_make_assembled(story_id=story_id), story_id, node_id)

    def test_provider_exception_raises_writer_pass_error(  # type: ignore[no-untyped-def]
        self,
        session,
        seeded_ids,
    ) -> None:
        """Provider exception raises WriterPassError wrapping original."""
        story_id, node_id = seeded_ids
        original_exc = ConnectionError("network failure")
        fake = _make_fake_caller(raise_exc=original_exc)
        service = WriterService(session, _make_config(), fake)

        with pytest.raises(WriterPassError) as exc_info:
            service.write(_make_assembled(story_id=story_id), story_id, node_id)

        assert exc_info.value.__cause__ is original_exc

        from afterworlds.persistence.orm.node import TurnORM

        rows = session.query(TurnORM).filter(TurnORM.node_id == str(node_id)).all()
        assert rows == []


# ---------------------------------------------------------------------------
# Lineage validation
# ---------------------------------------------------------------------------


class TestLineageValidation:
    def test_mismatched_story_raises_writer_pass_error(  # type: ignore[no-untyped-def]
        self, session, seeded_ids
    ) -> None:
        """write() raises WriterPassError when node_id does not belong to story_id."""
        _correct_story_id, node_id = seeded_ids
        wrong_story_id = uuid4()

        fake = _make_fake_caller()
        service = WriterService(session, _make_config(), fake)

        with pytest.raises(WriterPassError, match="does not belong to story"):
            service.write(
                _make_assembled(story_id=wrong_story_id), wrong_story_id, node_id
            )

    def test_mismatched_story_no_turn_persisted(  # type: ignore[no-untyped-def]
        self, session, seeded_ids
    ) -> None:
        """No Turn is persisted when the lineage check fails."""
        _correct_story_id, node_id = seeded_ids
        wrong_story_id = uuid4()

        fake = _make_fake_caller()
        service = WriterService(session, _make_config(), fake)

        with pytest.raises(WriterPassError):
            service.write(
                _make_assembled(story_id=wrong_story_id), wrong_story_id, node_id
            )

        from afterworlds.persistence.orm.node import TurnORM

        rows = session.query(TurnORM).filter(TurnORM.node_id == str(node_id)).all()
        assert rows == []

    def test_nonexistent_node_raises_writer_pass_error(  # type: ignore[no-untyped-def]
        self, session, seeded_ids
    ) -> None:
        """write() raises WriterPassError when node_id was never seeded."""
        story_id, _seeded_node_id = seeded_ids
        phantom_node_id = uuid4()

        fake = _make_fake_caller()
        service = WriterService(session, _make_config(), fake)

        with pytest.raises(WriterPassError, match="does not belong to story"):
            service.write(_make_assembled(story_id=story_id), story_id, phantom_node_id)

    def test_mismatched_context_story_raises_writer_pass_error(  # type: ignore[no-untyped-def]
        self, session, seeded_ids
    ) -> None:
        """WriterPassError raised when built_context story_id differs from story_id."""
        story_id, node_id = seeded_ids
        other_story_id = uuid4()

        fake = _make_fake_caller()
        service = WriterService(session, _make_config(), fake)

        with pytest.raises(
            WriterPassError, match="built_context was assembled for story"
        ):
            service.write(_make_assembled(story_id=other_story_id), story_id, node_id)

    def test_mismatched_context_story_no_turn_persisted(  # type: ignore[no-untyped-def]
        self, session, seeded_ids
    ) -> None:
        """No Turn is persisted when built_context story_id does not match story_id."""
        story_id, node_id = seeded_ids
        other_story_id = uuid4()

        fake = _make_fake_caller()
        service = WriterService(session, _make_config(), fake)

        with pytest.raises(WriterPassError):
            service.write(_make_assembled(story_id=other_story_id), story_id, node_id)

        from afterworlds.persistence.orm.node import TurnORM

        rows = session.query(TurnORM).filter(TurnORM.node_id == str(node_id)).all()
        assert rows == []

    def test_mismatched_context_story_no_provider_call(  # type: ignore[no-untyped-def]
        self, session, seeded_ids
    ) -> None:
        """The provider is never called when built_context story_id does not match."""
        story_id, node_id = seeded_ids
        other_story_id = uuid4()

        fake = _make_fake_caller()
        service = WriterService(session, _make_config(), fake)

        with pytest.raises(WriterPassError):
            service.write(_make_assembled(story_id=other_story_id), story_id, node_id)

        assert len(fake.captured) == 0  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# Model caller injection
# ---------------------------------------------------------------------------


class TestModelCallerInjection:
    def test_fake_caller_is_invoked(self, session, seeded_ids) -> None:  # type: ignore[no-untyped-def]
        """The injected fake caller is invoked with the rendered payload."""
        story_id, node_id = seeded_ids
        fake = _make_fake_caller()
        service = WriterService(session, _make_config(), fake)

        service.write(_make_assembled(story_id=story_id), story_id, node_id)

        assert len(fake.captured) == 1  # type: ignore[attr-defined]
        payload = fake.captured[0]  # type: ignore[attr-defined]
        assert "model" in payload
        assert "messages" in payload
        assert "system" in payload

    def test_no_real_network_call(self, session, seeded_ids) -> None:  # type: ignore[no-untyped-def]
        """Service does not attempt a real network call when a fake is injected."""
        story_id, node_id = seeded_ids
        import os

        env_backup = os.environ.pop("ANTHROPIC_API_KEY", None)
        try:
            fake = _make_fake_caller()
            service = WriterService(session, _make_config(), fake)
            service.write(_make_assembled(story_id=story_id), story_id, node_id)
        finally:
            if env_backup is not None:
                os.environ["ANTHROPIC_API_KEY"] = env_backup


# ---------------------------------------------------------------------------
# Cache metrics propagation
# ---------------------------------------------------------------------------


class TestCacheMetrics:
    def test_cache_metrics_present_when_reported(  # type: ignore[no-untyped-def]
        self, session, seeded_ids
    ) -> None:
        """WriterResult surfaces all four token counts when reported."""
        story_id, node_id = seeded_ids
        msg = _fake_message(
            text="The scene unfolds.",
            input_tokens=200,
            output_tokens=80,
            cache_read_input_tokens=150,
            cache_creation_input_tokens=50,
        )
        fake = _make_fake_caller(msg)
        service = WriterService(session, _make_config(), fake)

        result = service.write(_make_assembled(story_id=story_id), story_id, node_id)

        assert result.input_token_count == 200
        assert result.output_token_count == 80
        assert result.cache_read_token_count == 150
        assert result.cache_creation_token_count == 50

    def test_cache_metrics_none_when_not_reported(  # type: ignore[no-untyped-def]
        self, session, seeded_ids
    ) -> None:
        """Cache token fields are None (not 0) when the provider omits them."""
        story_id, node_id = seeded_ids
        msg = _fake_message(
            text="The scene unfolds.",
            input_tokens=100,
            output_tokens=40,
            cache_read_input_tokens=None,
            cache_creation_input_tokens=None,
        )
        fake = _make_fake_caller(msg)
        service = WriterService(session, _make_config(), fake)

        result = service.write(_make_assembled(story_id=story_id), story_id, node_id)

        assert result.cache_read_token_count is None
        assert result.cache_creation_token_count is None

    def test_zero_token_counts_preserved(  # type: ignore[no-untyped-def]
        self, session, seeded_ids
    ) -> None:
        """Reported zero token counts are preserved as 0, not collapsed to None."""
        story_id, node_id = seeded_ids
        msg = _fake_message(
            text="The scene unfolds.",
            input_tokens=0,
            output_tokens=0,
        )
        fake = _make_fake_caller(msg)
        service = WriterService(session, _make_config(), fake)

        result = service.write(_make_assembled(story_id=story_id), story_id, node_id)

        assert result.input_token_count == 0
        assert result.output_token_count == 0

    def test_model_identifier_format(  # type: ignore[no-untyped-def]
        self, session, seeded_ids
    ) -> None:
        """model_identifier is formatted as 'anthropic:<model_string>'."""
        story_id, node_id = seeded_ids
        msg = _fake_message()
        fake = _make_fake_caller(msg)
        service = WriterService(session, _make_config(), fake)

        result = service.write(_make_assembled(story_id=story_id), story_id, node_id)

        assert result.model_identifier.startswith("anthropic:")
        assert "claude" in result.model_identifier
