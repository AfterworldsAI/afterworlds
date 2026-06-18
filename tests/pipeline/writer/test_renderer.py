"""Unit tests for the Writer pass rendering — CRD Issue 9 / 14a.

These tests exercise WriterService._render() which produces a ProviderCallRequest.
Coverage targets (from the Issue 9 test requirements):
  - System prompt renders to system_blocks, not rendered_blocks
  - Each stable-prefix section appears as a content block in rendered_blocks
    in the canonical Issue 8 order
  - Cache breakpoint (has_cache_breakpoint=True) appears on the final
    stable-prefix block
  - PassForwardLedger content blocks (when seeded) appear after the breakpoint
  - VolatileSuffix content blocks appear last with no has_cache_breakpoint marker
  - Rolling Summary absent: section is omitted cleanly (no placeholder block)
  - Extended TTL: the cache breakpoint block has ttl="1h"
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from afterworlds.models.context import (
    AssembledContext,
    PassForwardEntry,
    PassForwardLedger,
    RetrievalMemoryPayload,
    StablePrefix,
    VolatileSuffix,
)
from afterworlds.models.enums import CastRole, IntentType
from afterworlds.models.intent_classification import IntentClassificationResult
from afterworlds.models.story_bible import CastEntry, StoryBibleContext
from afterworlds.pipeline.writer.config import WriterConfig
from afterworlds.pipeline.writer.service import WriterService


def _make_minimal_bible() -> StoryBibleContext:
    story_id = uuid4()
    return StoryBibleContext(
        story_id=story_id,
        setting=None,
        cast=(
            CastEntry(
                story_id=story_id,
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


def _make_icr(
    intent: IntentType = IntentType.IN_CHARACTER_ACTION,
    raw_input: str = "I push the door.",
) -> IntentClassificationResult:
    return IntentClassificationResult(
        intent_type=intent,
        confidence=0.95,
        raw_input=raw_input,
        ambiguous=False,
    )


def _make_stable_prefix(
    rolling_summary: str | None = None,
) -> StablePrefix:
    return StablePrefix(
        system_prompt="You are the story architect.",
        story_bible_context=_make_minimal_bible(),
        rolling_summary_text=rolling_summary,
        rules_package_slice=None,
        retrieval_memory=RetrievalMemoryPayload(),
    )


def _make_volatile_suffix(
    current_input: str = "I push the door.",
) -> VolatileSuffix:
    return VolatileSuffix(
        recent_turns=[],
        current_input=current_input,
        classified_intent=_make_icr(raw_input=current_input),
    )


def _make_assembled(
    rolling_summary: str | None = None,
    ledger_entries: list[PassForwardEntry] | None = None,
    current_input: str = "I push the door.",
) -> AssembledContext:
    ledger = PassForwardLedger()
    if ledger_entries:
        for e in ledger_entries:
            ledger.add(e.pass_name, e.content)
    return AssembledContext(
        stable_prefix=_make_stable_prefix(rolling_summary=rolling_summary),
        volatile_suffix=_make_volatile_suffix(current_input=current_input),
        pass_forward_ledger=ledger,
    )


def _make_config(extended_ttl: bool = True) -> WriterConfig:
    return WriterConfig(
        model="claude-sonnet-test",
        api_key_env="ANTHROPIC_API_KEY",
        extended_ttl=extended_ttl,
    )


def _make_service(extended_ttl: bool = True) -> WriterService:
    return WriterService(session=None, config=_make_config(extended_ttl))  # type: ignore[arg-type]


class TestSystemRendering:
    def test_system_prompt_in_system_blocks(self) -> None:
        """System prompt renders to system_blocks, not rendered_blocks."""
        svc = _make_service()
        request = svc._render(_make_assembled())
        assert len(request.system_blocks) >= 1
        assert "You are the story architect." in request.system_blocks[0].text

    def test_system_prompt_not_in_rendered_blocks(self) -> None:
        """System prompt must not appear in any rendered_block."""
        svc = _make_service()
        request = svc._render(_make_assembled())
        for block in request.rendered_blocks:
            assert "You are the story architect." not in block.text


class TestStablePrefixOrder:
    def test_story_bible_is_first_stable_block(self) -> None:
        """Story Bible active context appears as the first rendered_block."""
        svc = _make_service()
        request = svc._render(_make_assembled())
        first_block = request.rendered_blocks[0]
        assert "Story Bible" in first_block.text or "Aldric" in first_block.text

    def test_rolling_summary_after_story_bible(self) -> None:
        """Rolling Summary appears after Story Bible in rendered_blocks."""
        svc = _make_service()
        request = svc._render(
            _make_assembled(
                rolling_summary="Session summary: Aldric entered the dungeon."
            )
        )
        texts = [b.text for b in request.rendered_blocks]
        bible_idx = next(i for i, t in enumerate(texts) if "Aldric" in t)
        summary_idx = next(i for i, t in enumerate(texts) if "Session summary" in t)
        assert bible_idx < summary_idx

    def test_rolling_summary_absent_omitted_cleanly(self) -> None:
        """When Rolling Summary is None, no placeholder block appears."""
        svc = _make_service()
        request = svc._render(_make_assembled(rolling_summary=None))
        for block in request.rendered_blocks:
            text = block.text
            assert "None" not in text or "Narrator" in text
            assert text.strip() != ""


class TestCacheBreakpoint:
    def test_cache_control_on_final_stable_prefix_block(self) -> None:
        """Cache breakpoint on the final stable-prefix rendered_block."""
        svc = _make_service()
        request = svc._render(_make_assembled(rolling_summary="Summary text."))

        cached = [b for b in request.rendered_blocks if b.has_cache_breakpoint]
        assert len(cached) == 1
        assert "Summary text." in cached[0].text

    def test_cache_control_not_on_volatile_blocks(self) -> None:
        """VolatileSuffix blocks carry no cache breakpoint."""
        svc = _make_service()
        request = svc._render(_make_assembled(current_input="What is happening?"))

        input_blocks = [
            b for b in request.rendered_blocks if "What is happening?" in b.text
        ]
        for b in input_blocks:
            assert not b.has_cache_breakpoint

    def test_extended_ttl_on_cache_breakpoint(self) -> None:
        """Extended TTL (ttl='1h') is active on the cache breakpoint."""
        svc = _make_service(extended_ttl=True)
        request = svc._render(_make_assembled())

        cached = [b for b in request.rendered_blocks if b.has_cache_breakpoint]
        assert cached
        assert cached[0].ttl == "1h"

    def test_default_ttl_when_extended_disabled(self) -> None:
        """When extended_ttl=False, the cache breakpoint uses '5m' TTL."""
        svc = _make_service(extended_ttl=False)
        request = svc._render(_make_assembled())

        cached = [b for b in request.rendered_blocks if b.has_cache_breakpoint]
        assert cached
        assert cached[0].ttl == "5m"

    def test_cache_breakpoint_position_with_only_story_bible(self) -> None:
        """When only Story Bible is present, the cache breakpoint is on it."""
        svc = _make_service()
        request = svc._render(_make_assembled(rolling_summary=None))

        blocks = request.rendered_blocks
        cache_idx = next(
            (i for i, b in enumerate(blocks) if b.has_cache_breakpoint), None
        )
        assert cache_idx is not None
        for b in blocks[cache_idx + 1 :]:
            assert not b.has_cache_breakpoint


class TestPassForwardLedger:
    def test_empty_ledger_produces_no_ledger_block(self) -> None:
        """An empty PassForwardLedger produces no extra content block."""
        svc = _make_service()
        request = svc._render(_make_assembled())
        for block in request.rendered_blocks:
            assert "[WRITER OUTPUT]" not in block.text
            assert "[PLANNER OUTPUT]" not in block.text

    def test_non_empty_ledger_appears_after_cache_breakpoint(self) -> None:
        """Non-empty PassForwardLedger appears after the cache breakpoint."""
        ledger_entries = [
            PassForwardEntry(pass_name="planner", content="Plan: go north.")
        ]
        assembled = _make_assembled(ledger_entries=ledger_entries)
        svc = _make_service()
        request = svc._render(assembled)

        blocks = request.rendered_blocks
        cache_idx = next(i for i, b in enumerate(blocks) if b.has_cache_breakpoint)
        ledger_idx = next(
            i for i, b in enumerate(blocks) if "Plan: go north." in b.text
        )
        assert ledger_idx > cache_idx

    def test_ledger_block_has_no_cache_control(self) -> None:
        """PassForwardLedger blocks carry no cache breakpoint."""
        ledger_entries = [
            PassForwardEntry(pass_name="planner", content="Plan: go north.")
        ]
        assembled = _make_assembled(ledger_entries=ledger_entries)
        svc = _make_service()
        request = svc._render(assembled)

        ledger_blocks = [
            b for b in request.rendered_blocks if "Plan: go north." in b.text
        ]
        for b in ledger_blocks:
            assert not b.has_cache_breakpoint


class TestVolatileSuffix:
    def test_current_input_appears_in_rendered_blocks(self) -> None:
        """Current Sojourner input appears in rendered_blocks."""
        svc = _make_service()
        request = svc._render(_make_assembled(current_input="I try the lock."))
        texts = [b.text for b in request.rendered_blocks]
        assert any("I try the lock." in t for t in texts)

    def test_intent_block_is_structured_not_prose(self) -> None:
        """Intent classification renders as a compact structured block."""
        svc = _make_service()
        request = svc._render(_make_assembled())
        intent_texts = [
            b.text
            for b in request.rendered_blocks
            if "[INTENT CLASSIFICATION]" in b.text
        ]
        assert len(intent_texts) == 1
        intent_text = intent_texts[0]
        assert "intent_type:" in intent_text
        assert "confidence:" in intent_text
        assert "ambiguous:" in intent_text

    def test_volatile_suffix_blocks_have_no_cache_control(self) -> None:
        """All VolatileSuffix blocks carry no cache breakpoint."""
        svc = _make_service()
        request = svc._render(_make_assembled(current_input="Look around."))
        blocks = request.rendered_blocks
        cache_idx = next(i for i, b in enumerate(blocks) if b.has_cache_breakpoint)
        for b in blocks[cache_idx + 1 :]:
            assert not b.has_cache_breakpoint

    def test_pass_id_is_writer(self) -> None:
        """pass_id is set to WRITER."""
        from afterworlds.entitlement.enums import PipelinePassId

        svc = _make_service()
        request = svc._render(_make_assembled())
        assert request.pass_id == PipelinePassId.WRITER
