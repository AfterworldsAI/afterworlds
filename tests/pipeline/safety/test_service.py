"""Unit tests for SafetyService — CRD Issue 12b / 14a.

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
  - Provider adapter injection
  - Cache metrics: flat *_token_count fields surfaced; absent → None
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest

from afterworlds.entitlement.enums import ModelTier, PipelinePassId
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
from afterworlds.pipeline._stable_prefix_renderer import TTL_DEFAULT, TTL_EXTENDED
from afterworlds.pipeline.provider._models import (
    ProviderCallRequest,
    ProviderCallResult,
    ProviderTextPart,
    ProviderToolCallPart,
)
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


def _fake_tool_result(
    tool_input: dict[str, Any],
    cache_read: int | None = 80,
    cache_creation: int | None = None,
    pass_id: PipelinePassId = PipelinePassId.INPUT_SAFETY,
) -> ProviderCallResult:
    return ProviderCallResult(
        pass_id=pass_id,
        provider_name="anthropic",
        model_identifier="anthropic:claude-haiku-test",
        model_tier=ModelTier.HAIKU,
        content_parts=[
            ProviderToolCallPart(
                tool_name=REPORT_SAFETY_TOOL_NAME,
                tool_input=tool_input,
            )
        ],
        input_token_count=100,
        output_token_count=50,
        cache_read_token_count=cache_read,
        cache_creation_token_count=cache_creation,
        cache_warmed=bool(cache_read),
        latency_ms=1,
    )


def _text_only_result() -> ProviderCallResult:
    return ProviderCallResult(
        pass_id=PipelinePassId.INPUT_SAFETY,
        provider_name="anthropic",
        model_identifier="anthropic:claude-haiku-test",
        model_tier=ModelTier.HAIKU,
        content_parts=[ProviderTextPart(text="I cannot help with that.")],
        input_token_count=100,
        output_token_count=20,
        cache_read_token_count=None,
        cache_creation_token_count=None,
        cache_warmed=False,
        latency_ms=1,
    )


class _FakeProviderAdapter:
    """Capturing fake ProviderAdapter for SafetyService tests."""

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
        return self._result or _fake_tool_result({"concerns": []})


def _make_svc(extended_ttl: bool = True) -> SafetyService:
    config = SafetyConfig(
        model="claude-haiku-test",
        api_key_env="ANTHROPIC_API_KEY",
        extended_ttl=extended_ttl,
    )
    svc = SafetyService(config=config)
    svc._system_prompt = "SAFETY PROMPT"
    return svc


# ---------------------------------------------------------------------------
# Verdict derivation
# ---------------------------------------------------------------------------


class TestVerdictDerivation:
    def test_empty_concerns_yields_allow(self) -> None:
        adapter = _FakeProviderAdapter(_fake_tool_result({"concerns": []}))
        result = _make_svc().check(
            _make_assembled(), "Hello world", SafetyTarget.INPUT, provider=adapter  # type: ignore[arg-type]
        )
        assert result.verdict == SafetyVerdict.ALLOW

    def test_non_empty_concerns_yields_block(self) -> None:
        concern = {
            "category": "SEXUAL_MINOR",
            "description": "Explicit content involving a minor.",
            "evidence_summary": "Character described as 14 in explicit scene.",
        }
        adapter = _FakeProviderAdapter(_fake_tool_result({"concerns": [concern]}))
        result = _make_svc().check(
            _make_assembled(), "some text", SafetyTarget.INPUT, provider=adapter  # type: ignore[arg-type]
        )
        assert result.verdict == SafetyVerdict.BLOCK

    def test_verdict_is_computed_not_model_supplied(self) -> None:
        adapter = _FakeProviderAdapter(_fake_tool_result({"concerns": []}))
        result = _make_svc().check(
            _make_assembled(), "safe text", SafetyTarget.INPUT, provider=adapter  # type: ignore[arg-type]
        )
        assert not hasattr(result.report, "verdict")
        assert result.verdict == SafetyVerdict.ALLOW


# ---------------------------------------------------------------------------
# Schema validation → SafetyPassError
# ---------------------------------------------------------------------------


class TestSchemaValidation:
    def _check(self, tool_input: dict[str, Any]) -> None:
        adapter = _FakeProviderAdapter(_fake_tool_result(tool_input))
        with pytest.raises(SafetyPassError):
            _make_svc().check(
                _make_assembled(), "text", SafetyTarget.INPUT, provider=adapter  # type: ignore[arg-type]
            )

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
                        "severity": "high",
                    }
                ]
            }
        )

    def test_extra_fields_on_report_raises(self) -> None:
        self._check(
            {
                "concerns": [],
                "verdict": "allow",
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
        adapter = _FakeProviderAdapter(_fake_tool_result({"concerns": [concern]}))
        result = _make_svc().check(
            _make_assembled(), "text", SafetyTarget.INPUT, provider=adapter  # type: ignore[arg-type]
        )
        assert result.report.concerns[0].category == SafetyCategory(category)


# ---------------------------------------------------------------------------
# Parse failures
# ---------------------------------------------------------------------------


class TestParseFailures:
    def test_no_tool_block_raises_safety_pass_error(self) -> None:
        adapter = _FakeProviderAdapter(_text_only_result())
        with pytest.raises(SafetyPassError):
            _make_svc().check(
                _make_assembled(), "text", SafetyTarget.INPUT, provider=adapter  # type: ignore[arg-type]
            )

    def test_provider_exception_raises_safety_pass_error(self) -> None:
        adapter = _FakeProviderAdapter(raise_exc=RuntimeError("Network error"))
        with pytest.raises(SafetyPassError):
            _make_svc().check(
                _make_assembled(), "text", SafetyTarget.INPUT, provider=adapter  # type: ignore[arg-type]
            )

    def test_provider_exception_never_returns_allow(self) -> None:
        adapter = _FakeProviderAdapter(raise_exc=RuntimeError("Connection refused"))
        with pytest.raises(SafetyPassError) as exc_info:
            _make_svc().check(
                _make_assembled(), "text", SafetyTarget.INPUT, provider=adapter  # type: ignore[arg-type]
            )
        assert exc_info.value is not None


# ---------------------------------------------------------------------------
# Target label rendering
# ---------------------------------------------------------------------------


class TestTargetLabelRendering:
    def test_input_label_in_rendered_blocks(self) -> None:
        adapter = _FakeProviderAdapter(_fake_tool_result({"concerns": []}))
        svc = _make_svc()
        svc.check(  # type: ignore[arg-type]
            _make_assembled(),
            "Player typed this.",
            SafetyTarget.INPUT,
            provider=adapter,
        )
        request = adapter.captured_requests[0]
        last_block = request.rendered_blocks[-1]
        assert "[SOJOURNER INPUT FOR SAFETY EVALUATION]" in last_block.text
        assert "Player typed this." in last_block.text

    def test_output_label_in_rendered_blocks(self) -> None:
        adapter = _FakeProviderAdapter(_fake_tool_result({"concerns": []}))
        svc = _make_svc()
        svc.check(  # type: ignore[arg-type]
            _make_assembled(),
            "Writer wrote this.",
            SafetyTarget.OUTPUT,
            provider=adapter,
        )
        request = adapter.captured_requests[0]
        last_block = request.rendered_blocks[-1]
        assert "[WRITER OUTPUT FOR SAFETY EVALUATION]" in last_block.text
        assert "Writer wrote this." in last_block.text

    def test_evaluated_text_not_in_stable_prefix_blocks(self) -> None:
        """Evaluated text must only appear in the volatile suffix, not in
        stable-prefix blocks that would pollute the cache."""
        adapter = _FakeProviderAdapter(_fake_tool_result({"concerns": []}))
        svc = _make_svc()
        evaluated_text = "UNIQUE_EVAL_TEXT_12345"
        svc.check(
            _make_assembled(), evaluated_text, SafetyTarget.INPUT, provider=adapter  # type: ignore[arg-type]
        )
        request = adapter.captured_requests[0]
        # last block is the volatile/label block — all preceding blocks are stable
        for block in request.rendered_blocks[:-1]:
            assert evaluated_text not in block.text


# ---------------------------------------------------------------------------
# Prompt rendering
# ---------------------------------------------------------------------------


class TestPromptRendering:
    def test_two_system_blocks(self) -> None:
        adapter = _FakeProviderAdapter(_fake_tool_result({"concerns": []}))
        svc = _make_svc()
        svc.check(_make_assembled(), "text", SafetyTarget.INPUT, provider=adapter)  # type: ignore[arg-type]
        request = adapter.captured_requests[0]
        assert len(request.system_blocks) == 2

    def test_first_system_block_is_safety_prompt(self) -> None:
        adapter = _FakeProviderAdapter(_fake_tool_result({"concerns": []}))
        svc = _make_svc()
        svc.check(_make_assembled(), "text", SafetyTarget.INPUT, provider=adapter)  # type: ignore[arg-type]
        request = adapter.captured_requests[0]
        assert request.system_blocks[0].text == "SAFETY PROMPT"

    def test_second_system_block_is_mode_contract(self) -> None:
        adapter = _FakeProviderAdapter(_fake_tool_result({"concerns": []}))
        svc = _make_svc()
        mode_prompt = "You are the RPG narrator."
        ctx = _make_assembled(system_prompt=mode_prompt)
        svc.check(ctx, "text", SafetyTarget.INPUT, provider=adapter)  # type: ignore[arg-type]
        request = adapter.captured_requests[0]
        assert request.system_blocks[1].text == mode_prompt

    def test_mode_contract_not_in_rendered_blocks(self) -> None:
        adapter = _FakeProviderAdapter(_fake_tool_result({"concerns": []}))
        svc = _make_svc()
        mode_prompt = "UNIQUE_MODE_CONTRACT_XYZ"
        ctx = _make_assembled(system_prompt=mode_prompt)
        svc.check(ctx, "text", SafetyTarget.INPUT, provider=adapter)  # type: ignore[arg-type]
        request = adapter.captured_requests[0]
        for block in request.rendered_blocks:
            assert mode_prompt not in block.text

    def test_story_bible_is_first_rendered_block(self) -> None:
        adapter = _FakeProviderAdapter(_fake_tool_result({"concerns": []}))
        svc = _make_svc()
        svc.check(_make_assembled(), "text", SafetyTarget.INPUT, provider=adapter)  # type: ignore[arg-type]
        request = adapter.captured_requests[0]
        first_block = request.rendered_blocks[0]
        assert "Mira Sol" in first_block.text

    def test_cache_breakpoint_on_last_stable_prefix_block(self) -> None:
        adapter = _FakeProviderAdapter(_fake_tool_result({"concerns": []}))
        svc = _make_svc()
        ctx = _make_assembled()
        svc.check(ctx, "text", SafetyTarget.INPUT, provider=adapter)  # type: ignore[arg-type]
        request = adapter.captured_requests[0]
        # The volatile block (last) has no cache breakpoint; the last stable block does
        stable_blocks = (
            request.rendered_blocks[:-1] if len(request.rendered_blocks) > 1 else []
        )
        if stable_blocks:
            last_stable = stable_blocks[-1]
            assert last_stable.has_cache_breakpoint
        volatile_block = request.rendered_blocks[-1]
        assert not volatile_block.has_cache_breakpoint

    def test_extended_ttl_on_cache_block(self) -> None:
        adapter = _FakeProviderAdapter(_fake_tool_result({"concerns": []}))
        svc = _make_svc(extended_ttl=True)
        svc.check(_make_assembled(), "text", SafetyTarget.INPUT, provider=adapter)  # type: ignore[arg-type]
        request = adapter.captured_requests[0]
        cached = [b for b in request.rendered_blocks if b.has_cache_breakpoint]
        assert cached
        assert cached[0].ttl == TTL_EXTENDED

    def test_default_ttl_when_extended_disabled(self) -> None:
        adapter = _FakeProviderAdapter(_fake_tool_result({"concerns": []}))
        svc = _make_svc(extended_ttl=False)
        svc.check(_make_assembled(), "text", SafetyTarget.INPUT, provider=adapter)  # type: ignore[arg-type]
        request = adapter.captured_requests[0]
        cached = [b for b in request.rendered_blocks if b.has_cache_breakpoint]
        assert cached
        assert cached[0].ttl == TTL_DEFAULT

    def test_forced_tool_name_set(self) -> None:
        adapter = _FakeProviderAdapter(_fake_tool_result({"concerns": []}))
        svc = _make_svc()
        svc.check(_make_assembled(), "text", SafetyTarget.INPUT, provider=adapter)  # type: ignore[arg-type]
        request = adapter.captured_requests[0]
        assert request.forced_tool_name == REPORT_SAFETY_TOOL_NAME

    def test_input_pass_id(self) -> None:
        adapter = _FakeProviderAdapter(_fake_tool_result({"concerns": []}))
        svc = _make_svc()
        svc.check(_make_assembled(), "text", SafetyTarget.INPUT, provider=adapter)  # type: ignore[arg-type]
        request = adapter.captured_requests[0]
        assert request.pass_id == PipelinePassId.INPUT_SAFETY

    def test_output_pass_id(self) -> None:
        fake = _fake_tool_result({"concerns": []}, pass_id=PipelinePassId.OUTPUT_SAFETY)
        adapter = _FakeProviderAdapter(fake)
        svc = _make_svc()
        svc.check(_make_assembled(), "text", SafetyTarget.OUTPUT, provider=adapter)  # type: ignore[arg-type]
        request = adapter.captured_requests[0]
        assert request.pass_id == PipelinePassId.OUTPUT_SAFETY


# ---------------------------------------------------------------------------
# PassForwardLedger non-mutation
# ---------------------------------------------------------------------------


class TestPassForwardLedgerNonMutation:
    def test_empty_ledger_unchanged(self) -> None:
        adapter = _FakeProviderAdapter(_fake_tool_result({"concerns": []}))
        ctx = _make_assembled()
        original_len = len(ctx.pass_forward_ledger.entries)
        _make_svc().check(ctx, "text", SafetyTarget.INPUT, provider=adapter)  # type: ignore[arg-type]
        assert len(ctx.pass_forward_ledger.entries) == original_len

    def test_ledger_with_writer_content_unchanged(self) -> None:
        """Even when the ledger has Writer content, it must not be mutated."""
        entry = PassForwardEntry(pass_name="writer", content="Writer prose here.")
        adapter = _FakeProviderAdapter(_fake_tool_result({"concerns": []}))
        ctx = _make_assembled(ledger_entries=[entry])
        original_len = len(ctx.pass_forward_ledger.entries)
        _make_svc().check(ctx, "text", SafetyTarget.OUTPUT, provider=adapter)  # type: ignore[arg-type]
        assert len(ctx.pass_forward_ledger.entries) == original_len

    def test_writer_ledger_not_in_safety_rendered_blocks(self) -> None:
        """Writer prose in the ledger must not appear in Safety rendered_blocks."""
        adapter = _FakeProviderAdapter(_fake_tool_result({"concerns": []}))
        writer_prose = "WRITER_PROSE_CONTENT_UNIQUE_99"
        entry = PassForwardEntry(pass_name="writer", content=writer_prose)
        ctx = _make_assembled(ledger_entries=[entry])
        _make_svc().check(ctx, "eval text", SafetyTarget.OUTPUT, provider=adapter)  # type: ignore[arg-type]
        request = adapter.captured_requests[0]
        for block in request.rendered_blocks:
            assert writer_prose not in block.text


# ---------------------------------------------------------------------------
# BuiltContext immutability
# ---------------------------------------------------------------------------


class TestBuiltContextImmutability:
    def test_stable_prefix_unchanged(self) -> None:
        adapter = _FakeProviderAdapter(_fake_tool_result({"concerns": []}))
        ctx = _make_assembled(system_prompt="Original mode contract.")
        _make_svc().check(ctx, "text", SafetyTarget.INPUT, provider=adapter)  # type: ignore[arg-type]
        assert ctx.stable_prefix.system_prompt == "Original mode contract."

    def test_volatile_suffix_unchanged(self) -> None:
        adapter = _FakeProviderAdapter(_fake_tool_result({"concerns": []}))
        ctx = _make_assembled(current_input="original input")
        _make_svc().check(ctx, "text", SafetyTarget.INPUT, provider=adapter)  # type: ignore[arg-type]
        assert ctx.volatile_suffix.current_input == "original input"


# ---------------------------------------------------------------------------
# Token usage / cache metrics
# ---------------------------------------------------------------------------


class TestTokenUsage:
    def test_token_count_fields_populated(self) -> None:
        adapter = _FakeProviderAdapter(
            _fake_tool_result({"concerns": []}, cache_read=80, cache_creation=None)
        )
        result = _make_svc().check(
            _make_assembled(), "text", SafetyTarget.INPUT, provider=adapter  # type: ignore[arg-type]
        )
        assert result.input_token_count == 100
        assert result.output_token_count == 50
        assert result.cache_read_token_count == 80
        assert result.cache_creation_token_count is None

    def test_absent_cache_creation_is_none_not_zero(self) -> None:
        adapter = _FakeProviderAdapter(
            _fake_tool_result({"concerns": []}, cache_read=None, cache_creation=None)
        )
        result = _make_svc().check(
            _make_assembled(), "text", SafetyTarget.INPUT, provider=adapter  # type: ignore[arg-type]
        )
        assert result.cache_read_token_count is None
        assert result.cache_creation_token_count is None

    def test_provider_and_model_identifier_propagated(self) -> None:
        adapter = _FakeProviderAdapter(_fake_tool_result({"concerns": []}))
        result = _make_svc().check(
            _make_assembled(), "text", SafetyTarget.INPUT, provider=adapter  # type: ignore[arg-type]
        )
        assert result.provider == "anthropic"
        assert result.model_identifier == "anthropic:claude-haiku-test"


# ---------------------------------------------------------------------------
# Safety prompt — OTHER non-use section
# ---------------------------------------------------------------------------


class TestSafetyPromptOtherNonUse:
    def test_other_non_use_section_present(self) -> None:
        prompt_path = Path(__file__).parents[3] / "docs" / "prompts" / "safety.md"
        content = prompt_path.read_text(encoding="utf-8")
        assert "## OTHER — When Not To Use" in content
