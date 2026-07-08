"""Shared OrchestrationResult builders for API turn-submission tests.

Not a fixture module in the pytest sense (no autouse), just factory
functions -- OrchestrationResult enforces per-disposition field invariants
at construction time, so tests need valid, disposition-appropriate results.
"""

from __future__ import annotations

from uuid import UUID, uuid4

from afterworlds.models.enums import IntentType
from afterworlds.models.extractor import ExtractorProposalSet, ExtractorRoutingSummary
from afterworlds.models.intent_classification import IntentClassificationResult
from afterworlds.pipeline.contradiction.models import (
    ContradictionResult,
    ContradictionVerdict,
)
from afterworlds.pipeline.extractor.models import ExtractorResult
from afterworlds.pipeline.orchestrator.models import (
    OrchestrationResult,
    PipelineDisposition,
)
from afterworlds.pipeline.planner.models import PlannerOutput, PlannerResult
from afterworlds.pipeline.writer.models import WriterResult


def _intent_result(
    intent_type: IntentType = IntentType.IN_CHARACTER_ACTION,
) -> IntentClassificationResult:
    return IntentClassificationResult(
        intent_type=intent_type, confidence=0.9, raw_input="test input", ambiguous=False
    )


def make_pipeline_error_result(summary: str = "boom") -> OrchestrationResult:
    return OrchestrationResult(
        disposition=PipelineDisposition.PIPELINE_ERROR,
        delivered_output=None,
        turn_id=None,
        intent_classification=_intent_result(),
        pipeline_error_summary=summary,
        total_latency_ms=1,
        pass_latency_breakdown={},
    )


def make_refused_by_provider_result() -> OrchestrationResult:
    from afterworlds.pipeline._refusal import PassIdentifier, ProviderRefusal

    return OrchestrationResult(
        disposition=PipelineDisposition.REFUSED_BY_PROVIDER,
        delivered_output=None,
        turn_id=None,
        intent_classification=_intent_result(),
        provider_refusal=ProviderRefusal(
            provider="anthropic",
            pass_identifier=PassIdentifier.WRITER,
            coarse_reason="synthetic refusal",
        ),
        total_latency_ms=1,
        pass_latency_breakdown={},
    )


def make_delivered_result(
    turn_id: UUID | None = None, *, with_usage_metrics: bool = True
) -> OrchestrationResult:
    """A valid DELIVERED result.

    ``with_usage_metrics=False`` omits token counts on every pass result,
    which is what ``TurnCostPolicy.extract_snapshots`` requires to raise
    ``EntitlementSettlementError`` -- used to exercise the settlement-failure
    warning path (Binding Decision 5 / DoR-D) deliberately.
    """
    turn_id = turn_id or uuid4()
    input_tokens = 100 if with_usage_metrics else None
    output_tokens = 50 if with_usage_metrics else None
    return OrchestrationResult(
        disposition=PipelineDisposition.DELIVERED,
        delivered_output="The story continues.",
        turn_id=turn_id,
        intent_classification=_intent_result(),
        planner_result=PlannerResult(
            plan=PlannerOutput(scene_goal="goal", next_beat="beat", facts_needed=[]),
            model_identifier="anthropic:claude-sonnet",
            latency_ms=1,
            input_token_count=input_tokens,
            output_token_count=output_tokens,
            cache_read_token_count=None,
            cache_creation_token_count=None,
        ),
        writer_result=WriterResult(
            turn_id=turn_id,
            assistant_output="The story continues.",
            model_identifier="anthropic:claude-sonnet",
            latency_ms=1,
            input_token_count=input_tokens,
            output_token_count=output_tokens,
            cache_read_token_count=None,
            cache_creation_token_count=None,
        ),
        extractor_result=ExtractorResult(
            proposal_set=ExtractorProposalSet(proposals=[]),
            routed=ExtractorRoutingSummary(
                locked_fact_staged_ids=[],
                soft_fact_staged_ids=[],
                transient_state_staged_ids=[],
                unresolved_thread_staged_ids=[],
                event_ids=[],
            ),
            input_token_count=input_tokens,
            output_token_count=output_tokens,
            cache_read_token_count=None,
            cache_creation_token_count=None,
        ),
        contradiction_result=ContradictionResult(
            verdict=ContradictionVerdict.CLEAR,
            violations=[],
            model_identifier="anthropic:claude-haiku",
            latency_ms=1,
            input_token_count=input_tokens,
            output_token_count=output_tokens,
            cache_read_token_count=None,
            cache_creation_token_count=None,
        ),
        total_latency_ms=1,
        pass_latency_breakdown={},
    )
