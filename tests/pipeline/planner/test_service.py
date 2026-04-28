"""Unit tests for PlannerService — CRD Issue 12a.

Test classes
------------
TestHappyPath                 — well-formed response returns PlannerResult
TestSchemaValidation          — PlannerOutput field_validator rules
TestProviderException         — provider exception → PlannerPassError
TestMissingToolBlock          — no tool-use block → PlannerPassError
TestRendererStructure         — payload shape: model, tool_choice, system, block order
TestSystemPromptPlacement     — system_prompt in system param + first user block
TestCacheBreakpoint           — cache_control on last stable-prefix block
TestExtendedTTL               — ttl honours extended_ttl config flag
TestCallerInjection           — custom caller is invoked; default not constructed
TestCacheMetricsPropagation   — all four token counts propagated to PlannerResult
TestBuiltContextImmutability  — caller's AssembledContext is not mutated
TestEmptyPassForwardLedger    — empty ledger produces no extra user block
TestNotesField                — None and present notes handled correctly
TestModelIdentifier           — model_identifier includes provider prefix
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import pytest
from anthropic.types import Message, TextBlock, ToolUseBlock, Usage
from pydantic import ValidationError

from afterworlds.models.context import (
    AssembledContext,
    PassForwardEntry,
    PassForwardLedger,
    RetrievalMemoryPayload,
    StablePrefix,
    VolatileSuffix,
)
from afterworlds.models.enums import (
    CastRole,
    IntentType,
)
from afterworlds.models.intent_classification import IntentClassificationResult
from afterworlds.models.story_bible import (
    CastEntry,
    StoryBibleContext,
)
from afterworlds.pipeline.planner.caller import (
    PRODUCE_PLAN_TOOL_NAME,
    PlannerPayload,
)
from afterworlds.pipeline.planner.config import PlannerConfig
from afterworlds.pipeline.planner.models import (
    PlannerOutput,
    PlannerPassError,
    PlannerResult,
)
from afterworlds.pipeline.planner.service import PlannerService, _collect_stable_texts
from afterworlds.pipeline.writer.config import WriterConfig
from afterworlds.pipeline.writer.renderer import PromptRenderer

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_config(extended_ttl: bool = True) -> PlannerConfig:
    return PlannerConfig(
        model="claude-haiku-test",
        api_key_env="ANTHROPIC_API_KEY",
        extended_ttl=extended_ttl,
    )


def _make_assembled(
    story_id: UUID | None = None,
    rolling_summary: str | None = None,
    ledger_entries: list[tuple[str, str]] | None = None,
    current_input: str = "I examine the corridor.",
) -> AssembledContext:
    if story_id is None:
        story_id = uuid4()
    ctx = StoryBibleContext(
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
    sp = StablePrefix(
        system_prompt="You are the story architect.",
        story_bible_context=ctx,
        rolling_summary_text=rolling_summary,
        rules_package_slice=None,
        retrieval_memory=RetrievalMemoryPayload(),
    )
    icr = IntentClassificationResult(
        intent_type=IntentType.IN_CHARACTER_ACTION,
        confidence=0.90,
        raw_input=current_input,
        ambiguous=False,
    )
    vs = VolatileSuffix(
        recent_turns=[],
        current_input=current_input,
        classified_intent=icr,
    )
    entries = []
    if ledger_entries:
        for name, content in ledger_entries:
            entries.append(PassForwardEntry(pass_name=name, content=content))
    return AssembledContext(
        stable_prefix=sp,
        volatile_suffix=vs,
        pass_forward_ledger=PassForwardLedger(entries=entries),
    )


def _fake_tool_response(
    tool_input: dict[str, Any] | None = None,
    input_tokens: int = 100,
    output_tokens: int = 50,
    cache_read_input_tokens: int | None = None,
    cache_creation_input_tokens: int | None = None,
) -> Message:
    if tool_input is None:
        tool_input = {
            "scene_goal": "Escape the hotel.",
            "next_beat": "Aldric steps into the corridor.",
            "facts_needed": [],
        }
    return Message(
        id="msg_fake_planner",
        type="message",
        role="assistant",
        content=[
            ToolUseBlock(
                type="tool_use",
                id="toolu_fake_01",
                name=PRODUCE_PLAN_TOOL_NAME,
                input=tool_input,
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


def _make_fake_caller(
    response: Message | None = None,
    raise_exc: Exception | None = None,
):  # type: ignore[no-untyped-def]
    captured: list[PlannerPayload] = []

    def caller(payload: PlannerPayload) -> Message:
        captured.append(payload)
        if raise_exc is not None:
            raise raise_exc
        return response or _fake_tool_response()

    caller.captured = captured  # type: ignore[attr-defined]
    return caller


# ---------------------------------------------------------------------------
# TestHappyPath
# ---------------------------------------------------------------------------


class TestHappyPath:
    def test_returns_planner_result(self) -> None:
        caller = _make_fake_caller()
        svc = PlannerService(config=_make_config(), caller=caller)
        result = svc.plan(_make_assembled())
        assert isinstance(result, PlannerResult)

    def test_fields_propagated(self) -> None:
        tool_input = {
            "scene_goal": "Escape the hotel.",
            "next_beat": "Aldric slips through the service exit.",
            "facts_needed": ["Aldric has the Obsidian Key."],
            "notes": "Keep tension high.",
        }
        caller = _make_fake_caller(_fake_tool_response(tool_input))
        svc = PlannerService(config=_make_config(), caller=caller)
        result = svc.plan(_make_assembled())

        assert result.plan.scene_goal == "Escape the hotel."
        assert result.plan.next_beat == "Aldric slips through the service exit."
        assert result.plan.facts_needed == ["Aldric has the Obsidian Key."]
        assert result.plan.notes == "Keep tension high."

    def test_notes_none_when_absent(self) -> None:
        tool_input = {
            "scene_goal": "Escape.",
            "next_beat": "Aldric moves.",
            "facts_needed": [],
        }
        caller = _make_fake_caller(_fake_tool_response(tool_input))
        svc = PlannerService(config=_make_config(), caller=caller)
        result = svc.plan(_make_assembled())
        assert result.plan.notes is None

    def test_model_identifier_present(self) -> None:
        caller = _make_fake_caller()
        svc = PlannerService(config=_make_config(), caller=caller)
        result = svc.plan(_make_assembled())
        assert result.model_identifier == "anthropic:claude-haiku-test"


# ---------------------------------------------------------------------------
# TestSchemaValidation
# ---------------------------------------------------------------------------


class TestSchemaValidation:
    def test_empty_scene_goal_rejected(self) -> None:
        with pytest.raises(ValidationError):
            PlannerOutput(
                scene_goal="",
                next_beat="Some beat.",
                facts_needed=[],
            )

    def test_whitespace_scene_goal_rejected(self) -> None:
        with pytest.raises(ValidationError):
            PlannerOutput(
                scene_goal="   ",
                next_beat="Some beat.",
                facts_needed=[],
            )

    def test_empty_next_beat_rejected(self) -> None:
        with pytest.raises(ValidationError):
            PlannerOutput(
                scene_goal="Some goal.",
                next_beat="",
                facts_needed=[],
            )

    def test_whitespace_next_beat_rejected(self) -> None:
        with pytest.raises(ValidationError):
            PlannerOutput(
                scene_goal="Some goal.",
                next_beat="\t",
                facts_needed=[],
            )

    def test_empty_string_notes_rejected(self) -> None:
        with pytest.raises(ValidationError):
            PlannerOutput(
                scene_goal="Some goal.",
                next_beat="Some beat.",
                facts_needed=[],
                notes="",
            )

    def test_whitespace_only_notes_rejected(self) -> None:
        with pytest.raises(ValidationError):
            PlannerOutput(
                scene_goal="Some goal.",
                next_beat="Some beat.",
                facts_needed=[],
                notes="   ",
            )

    def test_none_notes_accepted(self) -> None:
        output = PlannerOutput(
            scene_goal="Some goal.",
            next_beat="Some beat.",
            facts_needed=[],
            notes=None,
        )
        assert output.notes is None

    def test_valid_notes_accepted(self) -> None:
        output = PlannerOutput(
            scene_goal="Some goal.",
            next_beat="Some beat.",
            facts_needed=[],
            notes="Keep tension high.",
        )
        assert output.notes == "Keep tension high."

    def test_extra_field_rejected(self) -> None:
        with pytest.raises(ValidationError):
            PlannerOutput(  # type: ignore[call-arg]
                scene_goal="Some goal.",
                next_beat="Some beat.",
                facts_needed=[],
                unknown_field="surprise",
            )

    def test_empty_facts_needed_accepted(self) -> None:
        output = PlannerOutput(
            scene_goal="Some goal.",
            next_beat="Some beat.",
            facts_needed=[],
        )
        assert output.facts_needed == []

    def test_whitespace_only_fact_entry_rejected(self) -> None:
        with pytest.raises(ValidationError):
            PlannerOutput(
                scene_goal="Some goal.",
                next_beat="Some beat.",
                facts_needed=["   "],
            )

    def test_empty_string_fact_entry_rejected(self) -> None:
        with pytest.raises(ValidationError):
            PlannerOutput(
                scene_goal="Some goal.",
                next_beat="Some beat.",
                facts_needed=[""],
            )

    def test_mixed_valid_and_blank_fact_rejected(self) -> None:
        with pytest.raises(ValidationError):
            PlannerOutput(
                scene_goal="Some goal.",
                next_beat="Some beat.",
                facts_needed=["Valid fact.", ""],
            )

    def test_valid_facts_accepted(self) -> None:
        output = PlannerOutput(
            scene_goal="Some goal.",
            next_beat="Some beat.",
            facts_needed=["Aldric has the key.", "Room 14 is on the east wing."],
        )
        assert len(output.facts_needed) == 2


# ---------------------------------------------------------------------------
# TestProviderException
# ---------------------------------------------------------------------------


class TestProviderException:
    def test_provider_exception_raises_planner_pass_error(self) -> None:
        caller = _make_fake_caller(raise_exc=RuntimeError("Network error"))
        svc = PlannerService(config=_make_config(), caller=caller)
        with pytest.raises(PlannerPassError, match="Planner provider call failed"):
            svc.plan(_make_assembled())


# ---------------------------------------------------------------------------
# TestMissingToolBlock
# ---------------------------------------------------------------------------


class TestMissingToolBlock:
    def test_no_tool_block_raises_planner_pass_error(self) -> None:
        no_tool_response = Message(
            id="msg_fake_no_tool",
            type="message",
            role="assistant",
            content=[TextBlock(type="text", text="I cannot plan this.")],
            model="claude-haiku-4-5-20251001",
            stop_reason="end_turn",
            stop_sequence=None,
            usage=Usage(
                input_tokens=50,
                output_tokens=10,
                cache_read_input_tokens=None,
                cache_creation_input_tokens=None,
            ),
        )
        caller = _make_fake_caller(response=no_tool_response)
        svc = PlannerService(config=_make_config(), caller=caller)
        with pytest.raises(PlannerPassError):
            svc.plan(_make_assembled())


# ---------------------------------------------------------------------------
# TestFactsNeededValidationViaService
# ---------------------------------------------------------------------------


class TestFactsNeededValidationViaService:
    def test_whitespace_fact_raises_planner_pass_error(self) -> None:
        """Blank facts_needed items from the model surface as PlannerPassError."""
        bad_input = {
            "scene_goal": "Escape.",
            "next_beat": "Aldric runs.",
            "facts_needed": ["   "],
        }
        caller = _make_fake_caller(_fake_tool_response(bad_input))
        svc = PlannerService(config=_make_config(), caller=caller)
        svc._system_prompt = "PLANNER PROMPT"
        with pytest.raises(PlannerPassError, match="schema validation"):
            svc.plan(_make_assembled())

    def test_empty_string_fact_raises_planner_pass_error(self) -> None:
        bad_input = {
            "scene_goal": "Escape.",
            "next_beat": "Aldric runs.",
            "facts_needed": [""],
        }
        caller = _make_fake_caller(_fake_tool_response(bad_input))
        svc = PlannerService(config=_make_config(), caller=caller)
        svc._system_prompt = "PLANNER PROMPT"
        with pytest.raises(PlannerPassError, match="schema validation"):
            svc.plan(_make_assembled())


# ---------------------------------------------------------------------------
# TestRendererStructure
# ---------------------------------------------------------------------------


class TestRendererStructure:
    def test_model_in_payload(self) -> None:
        caller = _make_fake_caller()
        svc = PlannerService(config=_make_config(), caller=caller)
        svc.plan(_make_assembled())
        payload = caller.captured[0]
        assert payload["model"] == "claude-haiku-test"

    def test_tool_choice_forced(self) -> None:
        caller = _make_fake_caller()
        svc = PlannerService(config=_make_config(), caller=caller)
        svc.plan(_make_assembled())
        payload = caller.captured[0]
        assert payload["tool_choice"] == {
            "type": "tool",
            "name": PRODUCE_PLAN_TOOL_NAME,
        }

    def test_single_user_message(self) -> None:
        caller = _make_fake_caller()
        svc = PlannerService(config=_make_config(), caller=caller)
        svc.plan(_make_assembled())
        payload = caller.captured[0]
        messages = payload["messages"]
        assert isinstance(messages, list)
        assert len(messages) == 1
        assert messages[0]["role"] == "user"

    def test_volatile_suffix_block_last(self) -> None:
        caller = _make_fake_caller()
        svc = PlannerService(config=_make_config(), caller=caller)
        svc.plan(_make_assembled(current_input="I push the door."))
        payload = caller.captured[0]
        user_content = payload["messages"][0]["content"]
        last_block = user_content[-1]
        assert isinstance(last_block, dict)
        assert "I push the door." in last_block.get("text", "")

    def test_tool_spec_present(self) -> None:
        caller = _make_fake_caller()
        svc = PlannerService(config=_make_config(), caller=caller)
        svc.plan(_make_assembled())
        payload = caller.captured[0]
        tools = payload["tools"]
        assert isinstance(tools, list)
        assert len(tools) == 1
        assert tools[0]["name"] == PRODUCE_PLAN_TOOL_NAME


# ---------------------------------------------------------------------------
# TestSystemPromptPlacement
# ---------------------------------------------------------------------------


class TestSystemPromptPlacement:
    def test_pass_prompt_in_system_param(self) -> None:
        """Planner pass prompt appears in the 'system' parameter."""
        caller = _make_fake_caller()
        # Use a config that loads from a real file — patch load_planner_prompt instead.
        # We inject a config and override the internal system prompt attribute.
        svc = PlannerService(config=_make_config(), caller=caller)
        svc._system_prompt = "PLANNER SYSTEM PROMPT"
        svc.plan(_make_assembled())
        payload = caller.captured[0]
        system = payload["system"]
        assert isinstance(system, list)
        assert any("PLANNER SYSTEM PROMPT" in b.get("text", "") for b in system)

    def test_story_bible_is_first_user_block(self) -> None:
        """Story Bible context is the first user-message stable-prefix block."""
        caller = _make_fake_caller()
        svc = PlannerService(config=_make_config(), caller=caller)
        svc._system_prompt = "PLANNER SYSTEM PROMPT"
        svc.plan(_make_assembled())
        payload = caller.captured[0]
        user_content = payload["messages"][0]["content"]
        first_block = user_content[0]
        assert isinstance(first_block, dict)
        assert "Story Bible" in first_block.get("text", "")

    def test_mode_contract_not_in_user_blocks(self) -> None:
        """sp.system_prompt must not appear in any user-message content block."""
        caller = _make_fake_caller()
        svc = PlannerService(config=_make_config(), caller=caller)
        svc._system_prompt = "PLANNER SYSTEM PROMPT"
        svc.plan(_make_assembled())
        payload = caller.captured[0]
        user_content = payload["messages"][0]["content"]
        for block in user_content:
            assert isinstance(block, dict)
            assert "You are the story architect." not in block.get("text", "")

    def test_pass_prompt_not_in_user_blocks(self) -> None:
        """Pass prompt must not appear in user-message content blocks."""
        caller = _make_fake_caller()
        svc = PlannerService(config=_make_config(), caller=caller)
        svc._system_prompt = "UNIQUE_PLANNER_PROMPT_MARKER"
        svc.plan(_make_assembled())
        payload = caller.captured[0]
        user_content = payload["messages"][0]["content"]
        for block in user_content:
            assert isinstance(block, dict)
            assert "UNIQUE_PLANNER_PROMPT_MARKER" not in block.get("text", "")


# ---------------------------------------------------------------------------
# TestCacheBreakpoint
# ---------------------------------------------------------------------------


class TestCacheBreakpoint:
    def test_exactly_one_cache_control_marker(self) -> None:
        caller = _make_fake_caller()
        svc = PlannerService(config=_make_config(), caller=caller)
        svc._system_prompt = "PLANNER PROMPT"
        svc.plan(_make_assembled(rolling_summary="Summary here."))
        payload = caller.captured[0]
        user_content = payload["messages"][0]["content"]
        cached = [
            b for b in user_content if isinstance(b, dict) and "cache_control" in b
        ]
        assert len(cached) == 1

    def test_cache_control_on_last_stable_prefix_block(self) -> None:
        caller = _make_fake_caller()
        svc = PlannerService(config=_make_config(), caller=caller)
        svc._system_prompt = "PLANNER PROMPT"
        svc.plan(_make_assembled(rolling_summary="Session summary here."))
        payload = caller.captured[0]
        user_content = payload["messages"][0]["content"]
        cached = [
            b for b in user_content if isinstance(b, dict) and "cache_control" in b
        ]
        assert len(cached) == 1
        # Last stable block is rolling summary when present
        assert "Session summary here." in cached[0].get("text", "")

    def test_volatile_blocks_have_no_cache_control(self) -> None:
        caller = _make_fake_caller()
        svc = PlannerService(config=_make_config(), caller=caller)
        svc._system_prompt = "PLANNER PROMPT"
        svc.plan(_make_assembled(current_input="What is happening?"))
        payload = caller.captured[0]
        user_content = payload["messages"][0]["content"]
        input_blocks = [
            b
            for b in user_content
            if isinstance(b, dict) and "What is happening?" in b.get("text", "")
        ]
        for b in input_blocks:
            assert "cache_control" not in b


# ---------------------------------------------------------------------------
# TestExtendedTTL
# ---------------------------------------------------------------------------


class TestExtendedTTL:
    def test_extended_ttl_sets_1h(self) -> None:
        caller = _make_fake_caller()
        svc = PlannerService(config=_make_config(extended_ttl=True), caller=caller)
        svc._system_prompt = "PLANNER PROMPT"
        svc.plan(_make_assembled())
        payload = caller.captured[0]
        user_content = payload["messages"][0]["content"]
        cached = [
            b for b in user_content if isinstance(b, dict) and "cache_control" in b
        ]
        assert cached
        assert cached[0]["cache_control"]["ttl"] == "1h"

    def test_default_ttl_sets_5m(self) -> None:
        caller = _make_fake_caller()
        svc = PlannerService(config=_make_config(extended_ttl=False), caller=caller)
        svc._system_prompt = "PLANNER PROMPT"
        svc.plan(_make_assembled())
        payload = caller.captured[0]
        user_content = payload["messages"][0]["content"]
        cached = [
            b for b in user_content if isinstance(b, dict) and "cache_control" in b
        ]
        assert cached
        assert cached[0]["cache_control"]["ttl"] == "5m"


# ---------------------------------------------------------------------------
# TestCallerInjection
# ---------------------------------------------------------------------------


class TestCallerInjection:
    def test_custom_caller_invoked(self) -> None:
        caller = _make_fake_caller()
        svc = PlannerService(config=_make_config(), caller=caller)
        svc._system_prompt = "PLANNER PROMPT"
        svc.plan(_make_assembled())
        assert len(caller.captured) == 1

    def test_default_caller_not_constructed_when_injected(self) -> None:
        """When a custom caller is injected, AnthropicPlannerCaller is not built."""
        caller = _make_fake_caller()
        # PlannerService.__init__ should not attempt to read the API key env
        # when a caller is explicitly provided.
        import os

        original = os.environ.pop("ANTHROPIC_API_KEY", None)
        try:
            svc = PlannerService(config=_make_config(), caller=caller)
            svc._system_prompt = "PLANNER PROMPT"
            svc.plan(_make_assembled())  # must not raise KeyError / ValueError
        finally:
            if original is not None:
                os.environ["ANTHROPIC_API_KEY"] = original


# ---------------------------------------------------------------------------
# TestCacheMetricsPropagation
# ---------------------------------------------------------------------------


class TestCacheMetricsPropagation:
    def test_all_four_token_counts_propagated(self) -> None:
        response = _fake_tool_response(
            input_tokens=200,
            output_tokens=75,
            cache_read_input_tokens=150,
            cache_creation_input_tokens=50,
        )
        caller = _make_fake_caller(response=response)
        svc = PlannerService(config=_make_config(), caller=caller)
        svc._system_prompt = "PLANNER PROMPT"
        result = svc.plan(_make_assembled())

        assert result.input_token_count == 200
        assert result.output_token_count == 75
        assert result.cache_read_token_count == 150
        assert result.cache_creation_token_count == 50

    def test_none_cache_counts_propagated(self) -> None:
        response = _fake_tool_response(
            input_tokens=100,
            output_tokens=50,
            cache_read_input_tokens=None,
            cache_creation_input_tokens=None,
        )
        caller = _make_fake_caller(response=response)
        svc = PlannerService(config=_make_config(), caller=caller)
        svc._system_prompt = "PLANNER PROMPT"
        result = svc.plan(_make_assembled())

        assert result.cache_read_token_count is None
        assert result.cache_creation_token_count is None


# ---------------------------------------------------------------------------
# TestBuiltContextImmutability
# ---------------------------------------------------------------------------


class TestBuiltContextImmutability:
    def test_context_not_mutated_by_plan(self) -> None:
        ctx = _make_assembled()
        original_len = len(ctx.pass_forward_ledger.entries)
        original_prompt = ctx.stable_prefix.system_prompt

        caller = _make_fake_caller()
        svc = PlannerService(config=_make_config(), caller=caller)
        svc._system_prompt = "PLANNER PROMPT"
        svc.plan(ctx)

        assert len(ctx.pass_forward_ledger.entries) == original_len
        assert ctx.stable_prefix.system_prompt == original_prompt


# ---------------------------------------------------------------------------
# TestEmptyPassForwardLedger
# ---------------------------------------------------------------------------


class TestEmptyPassForwardLedger:
    def test_empty_ledger_produces_no_extra_user_block(self) -> None:
        """Empty PassForwardLedger at Planner invocation produces no extra block."""
        caller = _make_fake_caller()
        svc = PlannerService(config=_make_config(), caller=caller)
        svc._system_prompt = "PLANNER PROMPT"
        ctx = _make_assembled()  # ledger is empty by default
        svc.plan(ctx)

        payload = caller.captured[0]
        user_content = payload["messages"][0]["content"]
        # No block should contain PassForwardLedger markup
        for block in user_content:
            assert isinstance(block, dict)
            assert "[WRITER OUTPUT]" not in block.get("text", "")
            assert "[PLANNER OUTPUT]" not in block.get("text", "")

    def test_non_empty_ledger_appears_after_stable_prefix(self) -> None:
        """Pre-populated ledger entry appears after the cache-control block."""
        caller = _make_fake_caller()
        svc = PlannerService(config=_make_config(), caller=caller)
        svc._system_prompt = "PLANNER PROMPT"
        ctx = _make_assembled(ledger_entries=[("writer", "The door is open.")])
        svc.plan(ctx)

        payload = caller.captured[0]
        user_content = payload["messages"][0]["content"]

        cached_idx = next(
            i
            for i, b in enumerate(user_content)
            if isinstance(b, dict) and "cache_control" in b
        )
        ledger_blocks = [
            (i, b)
            for i, b in enumerate(user_content)
            if isinstance(b, dict) and "The door is open." in b.get("text", "")
        ]
        assert ledger_blocks, "Ledger content not found in user blocks"
        ledger_idx = ledger_blocks[0][0]
        assert ledger_idx > cached_idx


# ---------------------------------------------------------------------------
# TestNotesField
# ---------------------------------------------------------------------------


class TestNotesField:
    def test_notes_none_propagates_as_none(self) -> None:
        tool_input = {
            "scene_goal": "Escape.",
            "next_beat": "Aldric runs.",
            "facts_needed": [],
        }
        caller = _make_fake_caller(_fake_tool_response(tool_input))
        svc = PlannerService(config=_make_config(), caller=caller)
        svc._system_prompt = "PLANNER PROMPT"
        result = svc.plan(_make_assembled())
        assert result.plan.notes is None

    def test_notes_value_propagates(self) -> None:
        tool_input = {
            "scene_goal": "Escape.",
            "next_beat": "Aldric runs.",
            "facts_needed": [],
            "notes": "Keep it brief.",
        }
        caller = _make_fake_caller(_fake_tool_response(tool_input))
        svc = PlannerService(config=_make_config(), caller=caller)
        svc._system_prompt = "PLANNER PROMPT"
        result = svc.plan(_make_assembled())
        assert result.plan.notes == "Keep it brief."


# ---------------------------------------------------------------------------
# TestModelIdentifier
# ---------------------------------------------------------------------------


class TestModelIdentifier:
    def test_model_identifier_includes_provider_prefix(self) -> None:
        caller = _make_fake_caller()
        svc = PlannerService(
            config=PlannerConfig(model="claude-haiku-custom", api_key_env="X"),
            caller=caller,
        )
        svc._system_prompt = "PLANNER PROMPT"
        result = svc.plan(_make_assembled())
        assert result.model_identifier.startswith("anthropic:")
        assert "claude-haiku-custom" in result.model_identifier


# ---------------------------------------------------------------------------
# TestCollectStableTexts
# ---------------------------------------------------------------------------


class TestCollectStableTexts:
    def test_story_bible_is_first(self) -> None:
        ctx = _make_assembled()
        texts = _collect_stable_texts(ctx)
        assert "Story Bible" in texts[0]

    def test_system_prompt_not_in_stable_texts(self) -> None:
        ctx = _make_assembled()
        texts = _collect_stable_texts(ctx)
        assert not any(ctx.stable_prefix.system_prompt in t for t in texts)

    def test_rolling_summary_included_when_present(self) -> None:
        ctx = _make_assembled(rolling_summary="Session summary here.")
        texts = _collect_stable_texts(ctx)
        assert any("Session summary here." in t for t in texts)

    def test_rolling_summary_omitted_when_none(self) -> None:
        ctx = _make_assembled(rolling_summary=None)
        texts = _collect_stable_texts(ctx)
        assert not any("Session summary" in t for t in texts)


# ---------------------------------------------------------------------------
# TestCacheLayoutMatchesWriter
# ---------------------------------------------------------------------------


class TestCacheLayoutMatchesWriter:
    """Regression: Planner stable-prefix user blocks match Writer renderer order."""

    def _make_writer_config(self) -> WriterConfig:
        return WriterConfig(
            model="claude-sonnet-test",
            api_key_env="ANTHROPIC_API_KEY",
            extended_ttl=True,
        )

    def test_stable_texts_identical_to_writer(self) -> None:
        ctx = _make_assembled(rolling_summary="Summary for cache test.")
        planner_texts = _collect_stable_texts(ctx)
        writer_texts = PromptRenderer(
            self._make_writer_config()
        )._collect_stable_prefix_texts(ctx)
        assert planner_texts == writer_texts

    def test_stable_texts_identical_without_rolling_summary(self) -> None:
        ctx = _make_assembled(rolling_summary=None)
        planner_texts = _collect_stable_texts(ctx)
        writer_texts = PromptRenderer(
            self._make_writer_config()
        )._collect_stable_prefix_texts(ctx)
        assert planner_texts == writer_texts

    def test_stable_texts_story_bible_first_for_both(self) -> None:
        ctx = _make_assembled()
        planner_texts = _collect_stable_texts(ctx)
        writer_texts = PromptRenderer(
            self._make_writer_config()
        )._collect_stable_prefix_texts(ctx)
        assert "Story Bible" in planner_texts[0]
        assert "Story Bible" in writer_texts[0]
        assert planner_texts[0] == writer_texts[0]
