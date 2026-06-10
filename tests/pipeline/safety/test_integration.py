"""Default-CI integration tests for SafetyService — CRD Issue 12b / 14a.

Uses a high-fidelity fake ProviderAdapter with four scripted scenarios:
  - Scenario 1: INPUT × ALLOW (benign player input)
  - Scenario 2: INPUT × BLOCK (hard-prohibited player input)
  - Scenario 3: OUTPUT × ALLOW (clean writer prose)
  - Scenario 4: OUTPUT × BLOCK (writer prose that crossed a threshold)
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from afterworlds.entitlement.enums import ModelTier, PipelinePassId
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
from afterworlds.pipeline.provider._models import (
    ProviderCallRequest,
    ProviderCallResult,
    ProviderToolCallPart,
)
from afterworlds.pipeline.safety.caller import REPORT_SAFETY_TOOL_NAME
from afterworlds.pipeline.safety.config import SafetyConfig
from afterworlds.pipeline.safety.models import (
    SafetyTarget,
    SafetyVerdict,
)
from afterworlds.pipeline.safety.service import SafetyService


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


class _ScriptedAdapter:
    """Fake ProviderAdapter that plays back scripted safety tool inputs."""

    def __init__(
        self,
        tool_inputs: list[dict],
        pass_id: PipelinePassId = PipelinePassId.INPUT_SAFETY,
    ) -> None:
        self._responses = [
            ProviderCallResult(
                pass_id=pass_id,
                provider_name="anthropic",
                model_identifier="anthropic:claude-haiku-test",
                model_tier=ModelTier.HAIKU,
                content_parts=[
                    ProviderToolCallPart(
                        tool_name=REPORT_SAFETY_TOOL_NAME,
                        tool_input=ti,
                    )
                ],
                input_token_count=100,
                output_token_count=40,
                cache_read_token_count=75,
                cache_creation_token_count=None,
                cache_warmed=True,
                latency_ms=5,
            )
            for ti in tool_inputs
        ]
        self._idx = 0
        self.provider_name = "anthropic"

    def call(self, request: ProviderCallRequest) -> ProviderCallResult:
        result = self._responses[self._idx]
        self._idx += 1
        return result


def _make_svc_and_adapter(
    tool_inputs: list[dict],
    pass_id: PipelinePassId = PipelinePassId.INPUT_SAFETY,
) -> tuple[SafetyService, _ScriptedAdapter]:
    config = SafetyConfig(
        model="claude-haiku-test",
        api_key_env="ANTHROPIC_API_KEY",
        extended_ttl=True,
    )
    svc = SafetyService(config=config)
    svc._system_prompt = "SAFETY PROMPT"
    adapter = _ScriptedAdapter(tool_inputs, pass_id=pass_id)
    return svc, adapter


class TestScenario1InputAllow:
    SCRIPTED = {"concerns": []}

    def test_verdict_allow(self) -> None:
        svc, adapter = _make_svc_and_adapter([self.SCRIPTED])
        result = svc.check(  # type: ignore[arg-type]
            _make_context("I open the door."),
            "I open the door.",
            SafetyTarget.INPUT,
            provider=adapter,
        )
        assert result.verdict == SafetyVerdict.ALLOW

    def test_target_input(self) -> None:
        svc, adapter = _make_svc_and_adapter([self.SCRIPTED])
        result = svc.check(  # type: ignore[arg-type]
            _make_context("I open the door."),
            "I open the door.",
            SafetyTarget.INPUT,
            provider=adapter,
        )
        assert result.target == SafetyTarget.INPUT

    def test_no_concerns(self) -> None:
        svc, adapter = _make_svc_and_adapter([self.SCRIPTED])
        result = svc.check(  # type: ignore[arg-type]
            _make_context("I open the door."),
            "I open the door.",
            SafetyTarget.INPUT,
            provider=adapter,
        )
        assert result.report.concerns == []

    def test_built_context_unchanged(self) -> None:
        svc, adapter = _make_svc_and_adapter([self.SCRIPTED])
        ctx = _make_context("I open the door.")
        original_ledger_len = len(ctx.pass_forward_ledger.entries)
        svc.check(ctx, "I open the door.", SafetyTarget.INPUT, provider=adapter)  # type: ignore[arg-type]
        assert len(ctx.pass_forward_ledger.entries) == original_ledger_len


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
        svc, adapter = _make_svc_and_adapter([self.SCRIPTED])
        result = svc.check(  # type: ignore[arg-type]
            _make_context("bad input"),
            "bad input",
            SafetyTarget.INPUT,
            provider=adapter,
        )
        assert result.verdict == SafetyVerdict.BLOCK

    def test_one_concern(self) -> None:
        svc, adapter = _make_svc_and_adapter([self.SCRIPTED])
        result = svc.check(  # type: ignore[arg-type]
            _make_context("bad input"),
            "bad input",
            SafetyTarget.INPUT,
            provider=adapter,
        )
        assert len(result.report.concerns) == 1

    def test_concern_category(self) -> None:
        from afterworlds.pipeline.safety.models import SafetyCategory

        svc, adapter = _make_svc_and_adapter([self.SCRIPTED])
        result = svc.check(  # type: ignore[arg-type]
            _make_context("bad input"),
            "bad input",
            SafetyTarget.INPUT,
            provider=adapter,
        )
        assert result.report.concerns[0].category == SafetyCategory.SEXUAL_MINOR


class TestScenario3OutputAllow:
    SCRIPTED = {"concerns": []}

    def test_verdict_allow(self) -> None:
        svc, adapter = _make_svc_and_adapter(
            [self.SCRIPTED], PipelinePassId.OUTPUT_SAFETY
        )
        result = svc.check(
            _make_context(),
            "Aldric Crane stepped into the corridor.",
            SafetyTarget.OUTPUT,
            provider=adapter,  # type: ignore[arg-type]
        )
        assert result.verdict == SafetyVerdict.ALLOW

    def test_target_output(self) -> None:
        svc, adapter = _make_svc_and_adapter(
            [self.SCRIPTED], PipelinePassId.OUTPUT_SAFETY
        )
        result = svc.check(
            _make_context(),
            "Aldric Crane stepped into the corridor.",
            SafetyTarget.OUTPUT,
            provider=adapter,  # type: ignore[arg-type]
        )
        assert result.target == SafetyTarget.OUTPUT

    def test_built_context_unchanged(self) -> None:
        svc, adapter = _make_svc_and_adapter(
            [self.SCRIPTED], PipelinePassId.OUTPUT_SAFETY
        )
        ctx = _make_context()
        original_ledger_len = len(ctx.pass_forward_ledger.entries)
        svc.check(  # type: ignore[arg-type]
            ctx,
            "Aldric Crane stepped into the corridor.",
            SafetyTarget.OUTPUT,
            provider=adapter,
        )
        assert len(ctx.pass_forward_ledger.entries) == original_ledger_len


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
        svc, adapter = _make_svc_and_adapter(
            [self.SCRIPTED], PipelinePassId.OUTPUT_SAFETY
        )
        result = svc.check(
            _make_context(),
            "Writer produced dangerous content.",
            SafetyTarget.OUTPUT,
            provider=adapter,  # type: ignore[arg-type]
        )
        assert result.verdict == SafetyVerdict.BLOCK

    def test_usage_surfaced(self) -> None:
        svc, adapter = _make_svc_and_adapter(
            [self.SCRIPTED], PipelinePassId.OUTPUT_SAFETY
        )
        result = svc.check(
            _make_context(),
            "Writer produced dangerous content.",
            SafetyTarget.OUTPUT,
            provider=adapter,  # type: ignore[arg-type]
        )
        assert result.input_token_count == 100
        assert result.output_token_count == 40
        assert result.cache_read_token_count == 75
        assert result.cache_creation_token_count is None
