"""Default-CI integration tests for SafetyService — CRD Issue 12b.

Uses a high-fidelity fake caller with four scripted scenarios:
  - Scenario 1: INPUT × ALLOW (benign player input)
  - Scenario 2: INPUT × BLOCK (hard-prohibited player input)
  - Scenario 3: OUTPUT × ALLOW (clean writer prose)
  - Scenario 4: OUTPUT × BLOCK (writer prose that crossed a threshold)

These tests run in default CI (no special env flags required).
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from anthropic.types import Message, ToolUseBlock, Usage

from afterworlds.models.context import (
    AssembledContext,
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
    SafetyTarget,
    SafetyVerdict,
)
from afterworlds.pipeline.safety.service import SafetyService

# ---------------------------------------------------------------------------
# Shared context factory
# ---------------------------------------------------------------------------


def _make_context(current_input: str = "I look around.") -> AssembledContext:
    story_id = uuid4()
    ctx = StoryBibleContext(
        story_id=story_id,
        setting=None,
        cast=(
            CastEntry(
                story_id=story_id,
                name="Aldric Crane",
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
        system_prompt="You are the Sojourn safety evaluator.",
        story_bible_context=ctx,
        rolling_summary_text=None,
        rules_package_slice=None,
        retrieval_memory=RetrievalMemoryPayload(),
    )
    icr = IntentClassificationResult(
        intent_type=IntentType.IN_CHARACTER_ACTION,
        confidence=0.95,
        raw_input=current_input,
        ambiguous=False,
    )
    vs = VolatileSuffix(
        recent_turns=[],
        current_input=current_input,
        classified_intent=icr,
    )
    return AssembledContext(
        stable_prefix=sp,
        volatile_suffix=vs,
        pass_forward_ledger=PassForwardLedger(),
    )


# ---------------------------------------------------------------------------
# High-fidelity fake
# ---------------------------------------------------------------------------


def _scripted_caller(tool_inputs: list[dict]) -> object:  # type: ignore[type-arg]
    """Return a caller that plays back scripted tool inputs in order."""
    responses = [
        Message(
            id=f"msg_fake_{i}",
            type="message",
            role="assistant",
            content=[
                ToolUseBlock(
                    type="tool_use",
                    id=f"toolu_fake_{i}",
                    name=REPORT_SAFETY_TOOL_NAME,
                    input=ti,
                )
            ],
            model="claude-haiku-4-5-20251001",
            stop_reason="tool_use",
            stop_sequence=None,
            usage=Usage(
                input_tokens=100,
                output_tokens=40,
                cache_read_input_tokens=75,
                cache_creation_input_tokens=None,
            ),
        )
        for i, ti in enumerate(tool_inputs)
    ]
    idx = [0]

    def caller(payload: object) -> Message:  # type: ignore[type-arg]
        response = responses[idx[0]]
        idx[0] += 1
        return response

    return caller


def _make_svc(tool_inputs: list[dict]) -> SafetyService:  # type: ignore[type-arg]
    config = SafetyConfig(
        model="claude-haiku-test",
        api_key_env="ANTHROPIC_API_KEY",
        extended_ttl=True,
    )
    svc = SafetyService(
        config=config,
        caller=_scripted_caller(tool_inputs),  # type: ignore[arg-type]
    )
    svc._system_prompt = "SAFETY PROMPT"
    return svc


# ---------------------------------------------------------------------------
# Scenario 1 — INPUT × ALLOW
# ---------------------------------------------------------------------------


class TestScenario1InputAllow:
    SCRIPTED = {"concerns": []}

    def test_verdict_allow(self) -> None:
        result = _make_svc([self.SCRIPTED]).check(
            _make_context("I open the door."), "I open the door.", SafetyTarget.INPUT
        )
        assert result.verdict == SafetyVerdict.ALLOW

    def test_target_input(self) -> None:
        result = _make_svc([self.SCRIPTED]).check(
            _make_context("I open the door."), "I open the door.", SafetyTarget.INPUT
        )
        assert result.target == SafetyTarget.INPUT

    def test_no_concerns(self) -> None:
        result = _make_svc([self.SCRIPTED]).check(
            _make_context("I open the door."), "I open the door.", SafetyTarget.INPUT
        )
        assert result.report.concerns == []

    def test_built_context_unchanged(self) -> None:
        ctx = _make_context("I open the door.")
        original_ledger_len = len(ctx.pass_forward_ledger.entries)
        _make_svc([self.SCRIPTED]).check(ctx, "I open the door.", SafetyTarget.INPUT)
        assert len(ctx.pass_forward_ledger.entries) == original_ledger_len


# ---------------------------------------------------------------------------
# Scenario 2 — INPUT × BLOCK
# ---------------------------------------------------------------------------


class TestScenario2InputBlock:
    SCRIPTED = {
        "concerns": [
            {
                "category": "SEXUAL_MINOR",
                "description": "Request explicitly involving a minor sexually.",
                "evidence_summary": "Character stated to be 13 in explicit context.",
            }
        ]
    }

    def test_verdict_block(self) -> None:
        result = _make_svc([self.SCRIPTED]).check(
            _make_context("bad input"), "bad input", SafetyTarget.INPUT
        )
        assert result.verdict == SafetyVerdict.BLOCK

    def test_one_concern(self) -> None:
        result = _make_svc([self.SCRIPTED]).check(
            _make_context("bad input"), "bad input", SafetyTarget.INPUT
        )
        assert len(result.report.concerns) == 1

    def test_concern_category(self) -> None:
        from afterworlds.pipeline.safety.models import SafetyCategory

        result = _make_svc([self.SCRIPTED]).check(
            _make_context("bad input"), "bad input", SafetyTarget.INPUT
        )
        assert result.report.concerns[0].category == SafetyCategory.SEXUAL_MINOR


# ---------------------------------------------------------------------------
# Scenario 3 — OUTPUT × ALLOW
# ---------------------------------------------------------------------------


class TestScenario3OutputAllow:
    SCRIPTED = {"concerns": []}

    def test_verdict_allow(self) -> None:
        result = _make_svc([self.SCRIPTED]).check(
            _make_context(),
            "Aldric Crane stepped into the corridor.",
            SafetyTarget.OUTPUT,
        )
        assert result.verdict == SafetyVerdict.ALLOW

    def test_target_output(self) -> None:
        result = _make_svc([self.SCRIPTED]).check(
            _make_context(),
            "Aldric Crane stepped into the corridor.",
            SafetyTarget.OUTPUT,
        )
        assert result.target == SafetyTarget.OUTPUT

    def test_built_context_unchanged(self) -> None:
        ctx = _make_context()
        original_ledger_len = len(ctx.pass_forward_ledger.entries)
        _make_svc([self.SCRIPTED]).check(
            ctx, "Aldric Crane stepped into the corridor.", SafetyTarget.OUTPUT
        )
        assert len(ctx.pass_forward_ledger.entries) == original_ledger_len


# ---------------------------------------------------------------------------
# Scenario 4 — OUTPUT × BLOCK
# ---------------------------------------------------------------------------


class TestScenario4OutputBlock:
    SCRIPTED = {
        "concerns": [
            {
                "category": "DANGEROUS_OPERATIONAL",
                "description": "Working synthesis instructions in narrative text.",
                "evidence_summary": (
                    "Step-by-step chemical synthesis route with reagents."
                ),
            }
        ]
    }

    def test_verdict_block(self) -> None:
        result = _make_svc([self.SCRIPTED]).check(
            _make_context(),
            "Writer produced dangerous content.",
            SafetyTarget.OUTPUT,
        )
        assert result.verdict == SafetyVerdict.BLOCK

    def test_usage_surfaced(self) -> None:
        result = _make_svc([self.SCRIPTED]).check(
            _make_context(),
            "Writer produced dangerous content.",
            SafetyTarget.OUTPUT,
        )
        assert result.usage is not None
        assert result.usage.input_tokens == 100
        assert result.usage.output_tokens == 40
        assert result.usage.cache_read_input_tokens == 75
        assert result.usage.cache_creation_input_tokens is None
