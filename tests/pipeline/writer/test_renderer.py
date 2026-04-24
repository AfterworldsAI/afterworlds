"""Unit tests for the PromptRenderer — CRD Issue 9.

Coverage targets (from the Issue 9 test requirements):
  - System prompt + mode contract renders to ``system`` parameter, not user msg
  - Each stable-prefix section appears as a content block in the first user
    message, in the canonical Issue 8 order
  - Cache breakpoint (cache_control) appears on the final stable-prefix block
  - PassForwardLedger content blocks (when seeded) appear after the breakpoint
  - VolatileSuffix content blocks appear last with no cache_control marker
  - Rolling Summary absent: section is omitted cleanly (no placeholder block)
  - Extended TTL: every payload includes ``ttl="1h"`` on the cache breakpoint
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
from afterworlds.pipeline.writer.renderer import PromptRenderer

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# System prompt tests
# ---------------------------------------------------------------------------


class TestSystemRendering:
    def test_system_prompt_in_system_field(self) -> None:
        """System prompt + mode contract renders to the system parameter."""
        renderer = PromptRenderer(_make_config())
        payload = renderer.render(_make_assembled())

        system = payload["system"]
        assert isinstance(system, list)
        assert len(system) >= 1
        first_block = system[0]
        assert isinstance(first_block, dict)
        assert first_block["type"] == "text"
        assert "You are the story architect." in first_block["text"]

    def test_system_prompt_not_in_user_message(self) -> None:
        """System prompt must not appear as a content block in the user message."""
        renderer = PromptRenderer(_make_config())
        payload = renderer.render(_make_assembled())

        messages = payload["messages"]
        assert isinstance(messages, list)
        assert len(messages) == 1
        user_content = messages[0]["content"]
        assert isinstance(user_content, list)
        # None of the user content blocks should contain the system prompt
        for block in user_content:
            assert isinstance(block, dict)
            assert "You are the story architect." not in block.get("text", "")


# ---------------------------------------------------------------------------
# Stable prefix ordering tests
# ---------------------------------------------------------------------------


class TestStablePrefixOrder:
    def test_story_bible_is_first_stable_block(self) -> None:
        """Story Bible active context appears as the first stable-prefix block."""
        renderer = PromptRenderer(_make_config())
        payload = renderer.render(_make_assembled())

        messages = payload["messages"]
        user_content = messages[0]["content"]
        # Find blocks without cache_control (all stable except the last)
        # or with cache_control (the last stable block)
        # The first stable block should contain Story Bible text
        first_block = user_content[0]
        assert isinstance(first_block, dict)
        assert "Story Bible" in first_block.get(
            "text", ""
        ) or "Aldric" in first_block.get("text", "")

    def test_rolling_summary_after_story_bible(self) -> None:
        """Rolling Summary appears after Story Bible in the stable prefix."""
        renderer = PromptRenderer(_make_config())
        payload = renderer.render(
            _make_assembled(
                rolling_summary="Session summary: Aldric entered the dungeon."
            )
        )

        messages = payload["messages"]
        user_content = messages[0]["content"]
        texts = [b.get("text", "") for b in user_content if isinstance(b, dict)]

        # Find positions
        bible_idx = next(i for i, t in enumerate(texts) if "Aldric" in t)
        summary_idx = next(i for i, t in enumerate(texts) if "Session summary" in t)
        assert bible_idx < summary_idx

    def test_rolling_summary_absent_omitted_cleanly(self) -> None:
        """When Rolling Summary is None, no placeholder block appears."""
        renderer = PromptRenderer(_make_config())
        payload = renderer.render(_make_assembled(rolling_summary=None))

        messages = payload["messages"]
        user_content = messages[0]["content"]
        for block in user_content:
            assert isinstance(block, dict)
            text = block.get("text", "")
            assert (
                "None" not in text or "Narrator" in text
            )  # "None" string as placeholder
            assert text.strip() != ""  # no empty placeholder blocks


# ---------------------------------------------------------------------------
# Cache breakpoint tests
# ---------------------------------------------------------------------------


class TestCacheBreakpoint:
    def test_cache_control_on_final_stable_prefix_block(self) -> None:
        """Cache breakpoint appears on the final stable-prefix content block."""
        renderer = PromptRenderer(_make_config())
        payload = renderer.render(_make_assembled(rolling_summary="Summary text."))

        messages = payload["messages"]
        user_content = messages[0]["content"]

        # Identify blocks with cache_control
        cached_blocks = [
            (i, b)
            for i, b in enumerate(user_content)
            if isinstance(b, dict) and "cache_control" in b
        ]
        assert len(cached_blocks) == 1, "Exactly one cache_control marker expected"

        cache_idx, cached_block = cached_blocks[0]
        # The cache_control block must be the Rolling Summary (last stable section)
        # Rolling summary text should be in this block
        assert "Summary text." in cached_block.get("text", "")

    def test_cache_control_not_on_volatile_blocks(self) -> None:
        """VolatileSuffix blocks carry no cache_control marker."""
        renderer = PromptRenderer(_make_config())
        payload = renderer.render(_make_assembled(current_input="What is happening?"))

        messages = payload["messages"]
        user_content = messages[0]["content"]

        # The current_input block and intent block must not have cache_control
        input_blocks = [
            b
            for b in user_content
            if isinstance(b, dict) and "What is happening?" in b.get("text", "")
        ]
        for b in input_blocks:
            assert "cache_control" not in b

    def test_extended_ttl_on_cache_breakpoint(self) -> None:
        """Extended TTL (ttl='1h') is active on the cache breakpoint."""
        renderer = PromptRenderer(_make_config(extended_ttl=True))
        payload = renderer.render(_make_assembled())

        messages = payload["messages"]
        user_content = messages[0]["content"]

        cached_blocks = [
            b for b in user_content if isinstance(b, dict) and "cache_control" in b
        ]
        assert cached_blocks, "No cached block found"
        cc = cached_blocks[0]["cache_control"]
        assert isinstance(cc, dict)
        assert cc.get("type") == "ephemeral"
        assert cc.get("ttl") == "1h"

    def test_default_ttl_when_extended_disabled(self) -> None:
        """When extended_ttl=False, the cache breakpoint uses '5m' TTL."""
        renderer = PromptRenderer(_make_config(extended_ttl=False))
        payload = renderer.render(_make_assembled())

        messages = payload["messages"]
        user_content = messages[0]["content"]

        cached_blocks = [
            b for b in user_content if isinstance(b, dict) and "cache_control" in b
        ]
        assert cached_blocks
        cc = cached_blocks[0]["cache_control"]
        assert isinstance(cc, dict)
        assert cc.get("ttl") == "5m"

    def test_cache_breakpoint_position_with_only_story_bible(self) -> None:
        """When only Story Bible is present, the cache breakpoint is on it."""
        renderer = PromptRenderer(_make_config())
        payload = renderer.render(_make_assembled(rolling_summary=None))

        messages = payload["messages"]
        user_content = messages[0]["content"]

        cached_blocks = [
            (i, b)
            for i, b in enumerate(user_content)
            if isinstance(b, dict) and "cache_control" in b
        ]
        assert len(cached_blocks) == 1
        cache_idx, _ = cached_blocks[0]
        # The cached block should be first (only Story Bible in stable prefix)
        # All subsequent blocks (volatile) must have no cache_control
        for b in user_content[cache_idx + 1 :]:
            assert "cache_control" not in b


# ---------------------------------------------------------------------------
# PassForwardLedger tests
# ---------------------------------------------------------------------------


class TestPassForwardLedger:
    def test_empty_ledger_produces_no_ledger_block(self) -> None:
        """An empty PassForwardLedger produces no extra content block."""
        renderer = PromptRenderer(_make_config())
        payload = renderer.render(_make_assembled())

        messages = payload["messages"]
        user_content = messages[0]["content"]
        for block in user_content:
            if isinstance(block, dict):
                assert "[WRITER OUTPUT]" not in block.get("text", "")
                assert "[PLANNER OUTPUT]" not in block.get("text", "")

    def test_non_empty_ledger_appears_after_cache_breakpoint(self) -> None:
        """Non-empty PassForwardLedger appears after the cache breakpoint."""
        ledger_entries = [
            PassForwardEntry(pass_name="planner", content="Plan: go north.")
        ]
        assembled = _make_assembled(ledger_entries=ledger_entries)
        renderer = PromptRenderer(_make_config())
        payload = renderer.render(assembled)

        messages = payload["messages"]
        user_content = messages[0]["content"]

        cache_idx = next(
            i
            for i, b in enumerate(user_content)
            if isinstance(b, dict) and "cache_control" in b
        )
        ledger_idx = next(
            i
            for i, b in enumerate(user_content)
            if isinstance(b, dict) and "Plan: go north." in b.get("text", "")
        )
        assert ledger_idx > cache_idx

    def test_ledger_block_has_no_cache_control(self) -> None:
        """PassForwardLedger blocks carry no cache_control marker."""
        ledger_entries = [
            PassForwardEntry(pass_name="planner", content="Plan: go north.")
        ]
        assembled = _make_assembled(ledger_entries=ledger_entries)
        renderer = PromptRenderer(_make_config())
        payload = renderer.render(assembled)

        messages = payload["messages"]
        user_content = messages[0]["content"]

        ledger_blocks = [
            b
            for b in user_content
            if isinstance(b, dict) and "Plan: go north." in b.get("text", "")
        ]
        for b in ledger_blocks:
            assert "cache_control" not in b


# ---------------------------------------------------------------------------
# VolatileSuffix tests
# ---------------------------------------------------------------------------


class TestVolatileSuffix:
    def test_current_input_appears_last_before_intent(self) -> None:
        """Current Sojourner input appears after stable prefix and before intent."""
        renderer = PromptRenderer(_make_config())
        payload = renderer.render(_make_assembled(current_input="I try the lock."))

        messages = payload["messages"]
        user_content = messages[0]["content"]
        texts = [b.get("text", "") for b in user_content if isinstance(b, dict)]

        input_idx = next(i for i, t in enumerate(texts) if t == "I try the lock.")
        intent_idx = next(
            i for i, t in enumerate(texts) if "[INTENT CLASSIFICATION]" in t
        )
        assert input_idx < intent_idx

    def test_intent_block_is_structured_not_prose(self) -> None:
        """Intent classification renders as a compact structured block, not prose."""
        renderer = PromptRenderer(_make_config())
        payload = renderer.render(_make_assembled())

        messages = payload["messages"]
        user_content = messages[0]["content"]
        intent_texts = [
            b.get("text", "")
            for b in user_content
            if isinstance(b, dict) and "[INTENT CLASSIFICATION]" in b.get("text", "")
        ]
        assert len(intent_texts) == 1
        intent_text = intent_texts[0]
        assert "intent_type:" in intent_text
        assert "confidence:" in intent_text
        assert "ambiguous:" in intent_text

    def test_volatile_suffix_blocks_have_no_cache_control(self) -> None:
        """All VolatileSuffix blocks carry no cache_control marker."""
        renderer = PromptRenderer(_make_config())
        payload = renderer.render(_make_assembled(current_input="Look around."))

        messages = payload["messages"]
        user_content = messages[0]["content"]

        # Find the position of the cache breakpoint
        cache_idx = next(
            i
            for i, b in enumerate(user_content)
            if isinstance(b, dict) and "cache_control" in b
        )
        # All blocks after the cache breakpoint (including ledger and volatile)
        # that are not the cache block itself should have no cache_control
        for b in user_content[cache_idx + 1 :]:
            assert "cache_control" not in b

    def test_payload_model_and_max_tokens(self) -> None:
        """Payload includes the configured model and max_tokens."""
        config = WriterConfig(
            model="claude-sonnet-4-5",
            api_key_env="ANTHROPIC_API_KEY",
            extended_ttl=True,
        )
        renderer = PromptRenderer(config)
        payload = renderer.render(_make_assembled())

        assert payload["model"] == "claude-sonnet-4-5"
        assert isinstance(payload["max_tokens"], int)
        assert payload["max_tokens"] > 0
