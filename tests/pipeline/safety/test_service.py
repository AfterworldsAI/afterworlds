"""Unit tests for SafetyService — CRD Issue 12b.

Covers:
  - Schema validation (evidence_summary >300 chars, unknown category, missing
    fields, extra fields) all propagate as SafetyPassError through the service
  - Verdict derivation invariant: empty → ALLOW, non-empty → BLOCK
  - Parse failures: no tool block, text-only response, provider exception
  - Category round-trips for all six categories
  - OTHER non-use: safety.md contains an "OTHER — When Not To Use" section
  - Target-specific label rendering (INPUT vs OUTPUT)
  - Prompt rendering: two system blocks, mode contract in system (not user),
    Story Bible as first user block, cache breakpoint on last stable-prefix
    block with ttl="1h"
  - Extended TTL and default TTL
  - BuiltContext immutability (ledger, stable_prefix)
  - PassForwardLedger non-mutation even when ledger has content
  - Model caller injection
  - Cache metrics: TokenUsage fields surfaced; absent → None
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest
from anthropic.types import Message, ToolUseBlock, Usage

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
from afterworlds.pipeline.safety.caller import REPORT_SAFETY_TOOL_NAME
from afterworlds.pipeline.safety.config import SafetyConfig
from afterworlds.pipeline.safety.models import (
    SafetyCategory,
    SafetyPassError,
    SafetyTarget,
    SafetyVerdict,
)
from afterworlds.pipeline.safety.service import SafetyService

# ---------------------------------------------------------------------------
# Test fixtures
# ---------------------------------------------------------------------------


def _make_assembled(
    current_input: str = "I look around.",
    system_prompt: str = "You are a story planner.",
    ledger_entries: list[PassForwardEntry] | None = None,
) -> AssembledContext:
    story_id = uuid4()
    ctx = StoryBibleContext(
        story_id=story_id,
        setting=None,
        cast=(
            CastEntry(
                story_id=story_id,
                name="Mira Sol",
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
        system_prompt=system_prompt,
        story_bible_context=ctx,
        rolling_summary_text=None,
        rules_package_slice=None,
        retrieval_memory=RetrievalMemoryPayload(),
    )
    icr = IntentClassificationResult(
        intent_type=IntentType.IN_CHARACTER_ACTION,
        confidence=0.9,
        raw_input=current_input,
        ambiguous=False,
    )
    vs = VolatileSuffix(
        recent_turns=[],
        current_input=current_input,
        classified_intent=icr,
    )
    ledger = PassForwardLedger(entries=ledger_entries or [])
    return AssembledContext(
        stable_prefix=sp, volatile_suffix=vs, pass_forward_ledger=ledger
    )


def _fake_tool_response(
    tool_input: dict,  # type: ignore[type-arg]
    cache_read: int | None = 80,
    cache_creation: int | None = None,
) -> Message:
    return Message(
        id="msg_fake_safety",
        type="message",
        role="assistant",
        content=[
            ToolUseBlock(
                type="tool_use",
                id="toolu_fake_safety",
                name=REPORT_SAFETY_TOOL_NAME,
                input=tool_input,
            )
        ],
        model="claude-haiku-test",
        stop_reason="tool_use",
        stop_sequence=None,
        usage=Usage(
            input_tokens=100,
            output_tokens=50,
            cache_read_input_tokens=cache_read,
            cache_creation_input_tokens=cache_creation,
        ),
    )


def _text_only_response() -> Message:
    from anthropic.types import TextBlock

    return Message(
        id="msg_fake_text",
        type="message",
        role="assistant",
        content=[TextBlock(type="text", text="I cannot help with that.")],
        model="claude-haiku-test",
        stop_reason="end_turn",
        stop_sequence=None,
        usage=Usage(
            input_tokens=100,
            output_tokens=20,
            cache_read_input_tokens=None,
            cache_creation_input_tokens=None,
        ),
    )


def _make_svc(caller: object) -> SafetyService:  # type: ignore[type-arg]
    config = SafetyConfig(
        model="claude-haiku-test",
        api_key_env="ANTHROPIC_API_KEY",
        extended_ttl=True,
    )
    svc = SafetyService(config=config, caller=caller)  # type: ignore[arg-type]
    svc._system_prompt = "SAFETY PROMPT"
    return svc


def _make_svc_default_ttl(caller: object) -> SafetyService:  # type: ignore[type-arg]
    config = SafetyConfig(
        model="claude-haiku-test",
        api_key_env="ANTHROPIC_API_KEY",
        extended_ttl=False,
    )
    svc = SafetyService(config=config, caller=caller)  # type: ignore[arg-type]
    svc._system_prompt = "SAFETY PROMPT"
    return svc


# ---------------------------------------------------------------------------
# Verdict derivation
# ---------------------------------------------------------------------------


class TestVerdictDerivation:
    def test_empty_concerns_yields_allow(self) -> None:
        caller = lambda _: _fake_tool_response({"concerns": []})  # noqa: E731
        result = _make_svc(caller).check(
            _make_assembled(), "Hello world", SafetyTarget.INPUT
        )
        assert result.verdict == SafetyVerdict.ALLOW

    def test_non_empty_concerns_yields_block(self) -> None:
        concern = {
            "category": "SEXUAL_MINOR",
            "description": "Explicit content involving a minor.",
            "evidence_summary": "Character described as 14 in explicit scene.",
        }
        caller = lambda _: _fake_tool_response({"concerns": [concern]})  # noqa: E731
        result = _make_svc(caller).check(
            _make_assembled(), "some text", SafetyTarget.INPUT
        )
        assert result.verdict == SafetyVerdict.BLOCK

    def test_verdict_is_computed_not_model_supplied(self) -> None:
        caller = lambda _: _fake_tool_response({"concerns": []})  # noqa: E731
        result = _make_svc(caller).check(
            _make_assembled(), "safe text", SafetyTarget.INPUT
        )
        assert not hasattr(result.report, "verdict")
        assert result.verdict == SafetyVerdict.ALLOW


# ---------------------------------------------------------------------------
# Schema validation → SafetyPassError
# ---------------------------------------------------------------------------


class TestSchemaValidation:
    def _check(self, tool_input: dict) -> None:  # type: ignore[type-arg]
        caller = lambda _: _fake_tool_response(tool_input)  # noqa: E731
        with pytest.raises(SafetyPassError):
            _make_svc(caller).check(_make_assembled(), "text", SafetyTarget.INPUT)

    def test_missing_category_raises(self) -> None:
        self._check(
            {
                "concerns": [
                    {
                        "description": "desc",
                        "evidence_summary": "summary",
                    }
                ]
            }
        )

    def test_missing_description_raises(self) -> None:
        self._check(
            {
                "concerns": [
                    {
                        "category": "OTHER",
                        "evidence_summary": "summary",
                    }
                ]
            }
        )

    def test_missing_evidence_summary_raises(self) -> None:
        self._check(
            {
                "concerns": [
                    {
                        "category": "OTHER",
                        "description": "desc",
                    }
                ]
            }
        )

    def test_evidence_summary_over_300_chars_raises(self) -> None:
        self._check(
            {
                "concerns": [
                    {
                        "category": "OTHER",
                        "description": "desc",
                        "evidence_summary": "x" * 301,
                    }
                ]
            }
        )

    def test_unknown_category_raises(self) -> None:
        self._check(
            {
                "concerns": [
                    {
                        "category": "MADE_UP_CATEGORY",
                        "description": "desc",
                        "evidence_summary": "summary",
                    }
                ]
            }
        )

    def test_extra_fields_on_concern_raises(self) -> None:
        self._check(
            {
                "concerns": [
                    {
                        "category": "OTHER",
                        "description": "desc",
                        "evidence_summary": "summary",
                        "severity": "high",  # extra field
                    }
                ]
            }
        )

    def test_extra_fields_on_report_raises(self) -> None:
        self._check(
            {
                "concerns": [],
                "verdict": "allow",  # extra field
            }
        )


# ---------------------------------------------------------------------------
# Category round-trips
# ---------------------------------------------------------------------------


class TestCategoryRoundTrips:
    @pytest.mark.parametrize(
        "category",
        [
            "SEXUAL_MINOR",
            "REAL_PERSON_TARGETED_HARM",
            "HATE_TARGETED",
            "SELF_HARM_INSTRUCTIONAL",
            "DANGEROUS_OPERATIONAL",
            "OTHER",
        ],
    )
    def test_category_deserializes(self, category: str) -> None:
        concern = {
            "category": category,
            "description": f"Concern in {category}",
            "evidence_summary": "Evidence here.",
        }
        caller = lambda _: _fake_tool_response({"concerns": [concern]})  # noqa: E731
        result = _make_svc(caller).check(_make_assembled(), "text", SafetyTarget.INPUT)
        assert result.report.concerns[0].category == SafetyCategory(category)


# ---------------------------------------------------------------------------
# Parse failures
# ---------------------------------------------------------------------------


class TestParseFailures:
    def test_no_tool_block_raises_safety_pass_error(self) -> None:
        caller = lambda _: _text_only_response()  # noqa: E731
        with pytest.raises(SafetyPassError):
            _make_svc(caller).check(_make_assembled(), "text", SafetyTarget.INPUT)

    def test_provider_exception_raises_safety_pass_error(self) -> None:
        def failing_caller(_: object) -> Message:
            raise RuntimeError("Network error")

        with pytest.raises(SafetyPassError):
            _make_svc(failing_caller).check(
                _make_assembled(), "text", SafetyTarget.INPUT
            )

    def test_provider_exception_never_returns_allow(self) -> None:
        def failing_caller(_: object) -> Message:
            raise RuntimeError("Connection refused")

        with pytest.raises(SafetyPassError) as exc_info:
            _make_svc(failing_caller).check(
                _make_assembled(), "text", SafetyTarget.INPUT
            )
        assert exc_info.value is not None


# ---------------------------------------------------------------------------
# Target label rendering
# ---------------------------------------------------------------------------


class TestTargetLabelRendering:
    def _capture_payload(self) -> tuple[dict, SafetyService]:  # type: ignore[type-arg]
        captured: list[dict] = []  # type: ignore[type-arg]

        def capturing_caller(payload: dict) -> Message:  # type: ignore[type-arg]
            captured.append(payload)
            return _fake_tool_response({"concerns": []})

        svc = _make_svc(capturing_caller)
        return captured, svc  # type: ignore[return-value]

    def test_input_label_in_user_block(self) -> None:
        captured, svc = self._capture_payload()
        ctx = _make_assembled()
        svc.check(ctx, "Player typed this.", SafetyTarget.INPUT)
        user_content = captured[0]["messages"][0]["content"]
        last_block = user_content[-1]
        assert "[SOJOURNER INPUT FOR SAFETY EVALUATION]" in last_block["text"]
        assert "Player typed this." in last_block["text"]

    def test_output_label_in_user_block(self) -> None:
        captured, svc = self._capture_payload()
        ctx = _make_assembled()
        svc.check(ctx, "Writer wrote this.", SafetyTarget.OUTPUT)
        user_content = captured[0]["messages"][0]["content"]
        last_block = user_content[-1]
        assert "[WRITER OUTPUT FOR SAFETY EVALUATION]" in last_block["text"]
        assert "Writer wrote this." in last_block["text"]

    def test_evaluated_text_not_in_stable_prefix_blocks(self) -> None:
        """Evaluated text must only appear in the volatile suffix, not in
        stable-prefix blocks that would pollute the cache."""
        captured, svc = self._capture_payload()
        ctx = _make_assembled()
        evaluated_text = "UNIQUE_EVAL_TEXT_12345"
        svc.check(ctx, evaluated_text, SafetyTarget.INPUT)
        user_content = captured[0]["messages"][0]["content"]
        # last block is the volatile/label block — all preceding blocks are stable
        for block in user_content[:-1]:
            assert evaluated_text not in block["text"]


# ---------------------------------------------------------------------------
# Prompt rendering
# ---------------------------------------------------------------------------


class TestPromptRendering:
    def _capture_payload(self) -> tuple[list[dict], SafetyService]:  # type: ignore[type-arg]
        captured: list[dict] = []  # type: ignore[type-arg]

        def capturing_caller(payload: dict) -> Message:  # type: ignore[type-arg]
            captured.append(payload)
            return _fake_tool_response({"concerns": []})

        svc = _make_svc(capturing_caller)
        return captured, svc  # type: ignore[return-value]

    def test_two_system_blocks(self) -> None:
        captured, svc = self._capture_payload()
        svc.check(_make_assembled(), "text", SafetyTarget.INPUT)
        assert len(captured[0]["system"]) == 2

    def test_first_system_block_is_safety_prompt(self) -> None:
        captured, svc = self._capture_payload()
        svc.check(_make_assembled(), "text", SafetyTarget.INPUT)
        assert captured[0]["system"][0]["text"] == "SAFETY PROMPT"

    def test_second_system_block_is_mode_contract(self) -> None:
        captured, svc = self._capture_payload()
        mode_prompt = "You are the RPG narrator."
        ctx = _make_assembled(system_prompt=mode_prompt)
        svc.check(ctx, "text", SafetyTarget.INPUT)
        assert captured[0]["system"][1]["text"] == mode_prompt

    def test_mode_contract_not_in_user_blocks(self) -> None:
        captured, svc = self._capture_payload()
        mode_prompt = "UNIQUE_MODE_CONTRACT_XYZ"
        ctx = _make_assembled(system_prompt=mode_prompt)
        svc.check(ctx, "text", SafetyTarget.INPUT)
        user_content = captured[0]["messages"][0]["content"]
        for block in user_content:
            assert mode_prompt not in block["text"]

    def test_story_bible_is_first_user_block(self) -> None:
        captured, svc = self._capture_payload()
        svc.check(_make_assembled(), "text", SafetyTarget.INPUT)
        user_content = captured[0]["messages"][0]["content"]
        first_block = user_content[0]
        assert "Mira Sol" in first_block["text"]

    def test_cache_breakpoint_on_last_stable_prefix_block(self) -> None:
        captured, svc = self._capture_payload()
        ctx = _make_assembled()
        svc.check(ctx, "text", SafetyTarget.INPUT)
        user_content = captured[0]["messages"][0]["content"]
        # The volatile block (last) has no cache_control; the last stable block does
        # We have one stable block (Story Bible only, no rolling summary etc.)
        stable_blocks = user_content[:-1] if len(user_content) > 1 else []
        if stable_blocks:
            last_stable = stable_blocks[-1]
            assert "cache_control" in last_stable
        volatile_block = user_content[-1]
        assert (
            "cache_control" not in volatile_block
            or volatile_block.get("cache_control") is None
        )

    def test_extended_ttl_on_cache_block(self) -> None:
        captured, svc = self._capture_payload()
        svc.check(_make_assembled(), "text", SafetyTarget.INPUT)
        user_content = captured[0]["messages"][0]["content"]
        for block in user_content:
            if block.get("cache_control"):
                assert block["cache_control"]["ttl"] == "1h"
                break

    def test_default_ttl_when_extended_disabled(self) -> None:
        captured: list[dict] = []  # type: ignore[type-arg]

        def capturing_caller(payload: dict) -> Message:  # type: ignore[type-arg]
            captured.append(payload)
            return _fake_tool_response({"concerns": []})

        svc = _make_svc_default_ttl(capturing_caller)
        svc.check(_make_assembled(), "text", SafetyTarget.INPUT)
        user_content = captured[0]["messages"][0]["content"]
        for block in user_content:
            if block.get("cache_control"):
                assert block["cache_control"]["ttl"] == "5m"
                break


# ---------------------------------------------------------------------------
# PassForwardLedger non-mutation
# ---------------------------------------------------------------------------


class TestPassForwardLedgerNonMutation:
    def test_empty_ledger_unchanged(self) -> None:
        caller = lambda _: _fake_tool_response({"concerns": []})  # noqa: E731
        ctx = _make_assembled()
        original_len = len(ctx.pass_forward_ledger.entries)
        _make_svc(caller).check(ctx, "text", SafetyTarget.INPUT)
        assert len(ctx.pass_forward_ledger.entries) == original_len

    def test_ledger_with_writer_content_unchanged(self) -> None:
        """Even when the ledger has Writer content, it must not be mutated."""
        entry = PassForwardEntry(pass_name="writer", content="Writer prose here.")
        caller = lambda _: _fake_tool_response({"concerns": []})  # noqa: E731
        ctx = _make_assembled(ledger_entries=[entry])
        original_len = len(ctx.pass_forward_ledger.entries)
        _make_svc(caller).check(ctx, "text", SafetyTarget.OUTPUT)
        assert len(ctx.pass_forward_ledger.entries) == original_len

    def test_writer_ledger_not_in_safety_user_blocks(self) -> None:
        """Writer prose in the ledger must not appear in Safety user blocks."""
        captured: list[dict] = []  # type: ignore[type-arg]

        def capturing_caller(payload: dict) -> Message:  # type: ignore[type-arg]
            captured.append(payload)
            return _fake_tool_response({"concerns": []})

        writer_prose = "WRITER_PROSE_CONTENT_UNIQUE_99"
        entry = PassForwardEntry(pass_name="writer", content=writer_prose)
        ctx = _make_assembled(ledger_entries=[entry])
        _make_svc(capturing_caller).check(ctx, "eval text", SafetyTarget.OUTPUT)
        user_content = captured[0]["messages"][0]["content"]
        for block in user_content:
            assert writer_prose not in block["text"]


# ---------------------------------------------------------------------------
# BuiltContext immutability
# ---------------------------------------------------------------------------


class TestBuiltContextImmutability:
    def test_stable_prefix_unchanged(self) -> None:
        caller = lambda _: _fake_tool_response({"concerns": []})  # noqa: E731
        ctx = _make_assembled(system_prompt="Original mode contract.")
        _make_svc(caller).check(ctx, "text", SafetyTarget.INPUT)
        assert ctx.stable_prefix.system_prompt == "Original mode contract."

    def test_volatile_suffix_unchanged(self) -> None:
        caller = lambda _: _fake_tool_response({"concerns": []})  # noqa: E731
        ctx = _make_assembled(current_input="original input")
        _make_svc(caller).check(ctx, "text", SafetyTarget.INPUT)
        assert ctx.volatile_suffix.current_input == "original input"


# ---------------------------------------------------------------------------
# Token usage / cache metrics
# ---------------------------------------------------------------------------


class TestTokenUsage:
    def test_usage_fields_populated(self) -> None:
        caller = lambda _: _fake_tool_response(  # noqa: E731
            {"concerns": []}, cache_read=80, cache_creation=None
        )
        result = _make_svc(caller).check(_make_assembled(), "text", SafetyTarget.INPUT)
        assert result.usage is not None
        assert result.usage.input_tokens == 100
        assert result.usage.output_tokens == 50
        assert result.usage.cache_read_input_tokens == 80
        assert result.usage.cache_creation_input_tokens is None

    def test_absent_cache_creation_is_none_not_zero(self) -> None:
        caller = lambda _: _fake_tool_response(  # noqa: E731
            {"concerns": []}, cache_read=None, cache_creation=None
        )
        result = _make_svc(caller).check(_make_assembled(), "text", SafetyTarget.INPUT)
        assert result.usage is not None
        assert result.usage.cache_read_input_tokens is None
        assert result.usage.cache_creation_input_tokens is None


# ---------------------------------------------------------------------------
# Safety prompt — OTHER non-use section
# ---------------------------------------------------------------------------


class TestSafetyPromptOtherNonUse:
    def test_other_non_use_section_present(self) -> None:
        prompt_path = Path(__file__).parents[3] / "docs" / "prompts" / "safety.md"
        content = prompt_path.read_text(encoding="utf-8")
        assert "## OTHER — When Not To Use" in content
