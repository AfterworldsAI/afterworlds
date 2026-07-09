"""Settlement and pool split tests — AC 40–47, 58."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from sqlalchemy.orm import Session

from afterworlds.entitlement.enums import (
    EntitlementEventType,
    ModelTier,
    PipelinePassId,
    RuntimeAccessPath,
)
from afterworlds.entitlement.errors import (
    EntitlementSettlementConflictError,
    EntitlementSettlementError,
)
from afterworlds.entitlement.models import PassUsageSnapshot, TurnCostPolicyConfig
from afterworlds.entitlement.policy import TurnCostPolicy
from afterworlds.entitlement.service import EntitlementService
from tests.entitlement.conftest import (
    activate_hosted,
    grant_subscription_credits,
    make_policy,
)


def _make_delivered_result(
    turn_id: UUID,
    input_tokens: int = 1000,
    output_tokens: int = 500,
    include_classifier_usage: bool = False,
) -> object:
    """Create a minimal OrchestrationResult with DELIVERED disposition."""
    from afterworlds.models.enums import IntentType
    from afterworlds.models.extractor import (
        ExtractorProposalSet,
        ExtractorRoutingSummary,
    )
    from afterworlds.models.intent_classification import IntentClassificationResult
    from afterworlds.pipeline.contradiction.models import (
        ContradictionResult,
        ContradictionVerdict,
    )
    from afterworlds.pipeline.extractor.models import ExtractorResult
    from afterworlds.pipeline.orchestrator.models import (
        IntentClassifierUsage,
        OrchestrationResult,
        PipelineDisposition,
    )
    from afterworlds.pipeline.planner.models import PlannerOutput, PlannerResult
    from afterworlds.pipeline.writer.models import WriterResult

    intent = IntentClassificationResult(
        intent_type=IntentType.IN_CHARACTER_ACTION,
        confidence=1.0,
        raw_input="",
        ambiguous=False,
    )
    planner = PlannerResult(
        plan=PlannerOutput(scene_goal="g", next_beat="b", facts_needed=[]),
        model_identifier="test",
        latency_ms=0,
        input_token_count=input_tokens,
        output_token_count=output_tokens,
        cache_read_token_count=None,
        cache_creation_token_count=None,
    )
    writer = WriterResult(
        turn_id=turn_id,
        assistant_output="prose",
        model_identifier="test",
        latency_ms=0,
        input_token_count=input_tokens,
        output_token_count=output_tokens,
        cache_read_token_count=None,
        cache_creation_token_count=None,
    )
    extractor = ExtractorResult(
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
    )
    contradiction = ContradictionResult(
        verdict=ContradictionVerdict.CLEAR,
        violations=[],
        model_identifier="test",
        latency_ms=0,
        input_token_count=input_tokens,
        output_token_count=output_tokens,
        cache_read_token_count=None,
        cache_creation_token_count=None,
    )
    classifier_usage = (
        IntentClassifierUsage(
            pass_id=PipelinePassId.INTENT_CLASSIFIER,
            provider="test-provider",
            model_identifier="test",
            model_tier=ModelTier.HAIKU,
            input_token_count=input_tokens,
            output_token_count=output_tokens,
            cache_read_token_count=None,
            cache_creation_token_count=None,
            latency_ms=1,
        )
        if include_classifier_usage
        else None
    )
    return OrchestrationResult(
        disposition=PipelineDisposition.DELIVERED,
        delivered_output="prose",
        turn_id=turn_id,
        intent_classification=intent,
        planner_result=planner,
        writer_result=writer,
        extractor_result=extractor,
        contradiction_result=contradiction,
        intent_classifier_usage=classifier_usage,
        total_latency_ms=0,
        pass_latency_breakdown={},
    )


def _make_blocked_result() -> object:
    """BLOCKED_INPUT_SAFETY result — turn_id=None."""
    from afterworlds.models.enums import IntentType
    from afterworlds.models.intent_classification import IntentClassificationResult
    from afterworlds.pipeline.orchestrator.models import (
        OrchestrationResult,
        PipelineDisposition,
    )
    from afterworlds.pipeline.safety.models import (
        SafetyCategory,
        SafetyConcern,
        SafetyReport,
        SafetyResult,
        SafetyTarget,
    )

    intent = IntentClassificationResult(
        intent_type=IntentType.IN_CHARACTER_ACTION,
        confidence=1.0,
        raw_input="",
        ambiguous=False,
    )
    safety_result = SafetyResult(
        report=SafetyReport(
            concerns=[
                SafetyConcern(
                    category=SafetyCategory.OTHER,
                    description="test",
                    evidence_summary="blocked",
                )
            ]
        ),
        target=SafetyTarget.INPUT,
    )
    return OrchestrationResult(
        disposition=PipelineDisposition.BLOCKED_INPUT_SAFETY,
        delivered_output=None,
        turn_id=None,
        intent_classification=intent,
        input_safety_result=safety_result,
        total_latency_ms=0,
        pass_latency_breakdown={},
    )


# ---------------------------------------------------------------------------
# AC 40: settle raises if access_path != HOSTED
# ---------------------------------------------------------------------------


def test_settle_raises_for_byok_access_path(
    service: EntitlementService,
    sojourner_id: UUID,
) -> None:
    """AC 40: settle_hosted_turn_cost raises EntitlementSettlementError for BYOK."""
    activate_hosted(service, sojourner_id)
    grant_subscription_credits(service, sojourner_id, "100")
    result = _make_delivered_result(uuid4())

    with pytest.raises(EntitlementSettlementError, match="HOSTED"):
        service.settle_hosted_turn_cost(
            sojourner_id,
            result,
            policy=make_policy(),
            access_path=RuntimeAccessPath.BYOK,
        )


# ---------------------------------------------------------------------------
# AC 41: settle returns None for non-DELIVERED/OOC_HANDLED dispositions
# ---------------------------------------------------------------------------


def test_settle_returns_none_for_blocked_disposition(
    service: EntitlementService,
    sojourner_id: UUID,
) -> None:
    """AC 41: settle returns None for BLOCKED_INPUT_SAFETY."""
    activate_hosted(service, sojourner_id)
    result = _make_blocked_result()

    outcome = service.settle_hosted_turn_cost(
        sojourner_id,
        result,
        policy=make_policy(),
        access_path=RuntimeAccessPath.HOSTED,
    )
    assert outcome is None


# ---------------------------------------------------------------------------
# AC 43: pool depletion order
# ---------------------------------------------------------------------------


def test_pool_split_hosted_only() -> None:
    """AC 43: deduction from hosted only (hosted has enough)."""
    hosted_d, top_up_d = TurnCostPolicy.compute_pool_split(
        Decimal("5"), Decimal("10"), Decimal("5")
    )
    assert hosted_d == Decimal("-5")
    assert top_up_d == Decimal("0")


def test_pool_split_spanning() -> None:
    """AC 43: spanning hosted + top-up (hosted insufficient alone)."""
    hosted_d, top_up_d = TurnCostPolicy.compute_pool_split(
        Decimal("12"), Decimal("10"), Decimal("5")
    )
    assert hosted_d == Decimal("-10")
    assert top_up_d == Decimal("-2")


def test_pool_split_top_up_only() -> None:
    """AC 43: top-up only (hosted already depleted)."""
    hosted_d, top_up_d = TurnCostPolicy.compute_pool_split(
        Decimal("5"), Decimal("0"), Decimal("10")
    )
    assert hosted_d == Decimal("0")
    assert top_up_d == Decimal("-5")


def test_pool_split_both_insufficient_balance_goes_negative() -> None:
    """AC 43: balance goes negative when both insufficient."""
    hosted_d, top_up_d = TurnCostPolicy.compute_pool_split(
        Decimal("20"), Decimal("5"), Decimal("3")
    )
    # top-up depleted, remaining goes on hosted
    assert top_up_d == Decimal("-3")
    assert hosted_d == Decimal("-17")
    assert hosted_d + top_up_d == Decimal("-20")


# ---------------------------------------------------------------------------
# AC 44: idempotent settlement — same turn_id, same amounts
# ---------------------------------------------------------------------------


def test_settle_idempotent_same_amounts(
    service: EntitlementService,
    sojourner_id: UUID,
) -> None:
    """AC 44: same turn_id + same amounts → returns existing event."""
    activate_hosted(service, sojourner_id)
    grant_subscription_credits(service, sojourner_id, "100")

    turn_id = uuid4()
    result = _make_delivered_result(turn_id)
    policy = make_policy()

    event1 = service.settle_hosted_turn_cost(
        sojourner_id, result, policy=policy, access_path=RuntimeAccessPath.HOSTED
    )
    event2 = service.settle_hosted_turn_cost(
        sojourner_id, result, policy=policy, access_path=RuntimeAccessPath.HOSTED
    )
    assert event1 is not None
    assert event2 is not None
    assert event1.event_id == event2.event_id


# ---------------------------------------------------------------------------
# AC 45: settlement conflict — same turn_id, different amounts
# ---------------------------------------------------------------------------


def test_settle_conflict_different_amounts(
    service: EntitlementService,
    sojourner_id: UUID,
    session: Session,
) -> None:
    """AC 45: same turn_id + different amounts → EntitlementSettlementConflictError."""
    activate_hosted(service, sojourner_id)
    grant_subscription_credits(service, sojourner_id, "100")

    turn_id = uuid4()
    result_1000 = _make_delivered_result(turn_id, input_tokens=1000, output_tokens=500)
    result_5000 = _make_delivered_result(turn_id, input_tokens=5000, output_tokens=3000)

    policy = make_policy()
    service.settle_hosted_turn_cost(
        sojourner_id, result_1000, policy=policy, access_path=RuntimeAccessPath.HOSTED
    )

    with pytest.raises(EntitlementSettlementConflictError):
        service.settle_hosted_turn_cost(
            sojourner_id,
            result_5000,
            policy=policy,
            access_path=RuntimeAccessPath.HOSTED,
        )


# ---------------------------------------------------------------------------
# AC 46: settlement proceeds even if hosted access changes
# ---------------------------------------------------------------------------


def test_settle_proceeds_after_hosted_deactivated(
    service: EntitlementService,
    sojourner_id: UUID,
) -> None:
    """AC 46: settlement proceeds when hosted access deactivated after preflight."""
    from tests.entitlement.conftest import deactivate_hosted

    activate_hosted(service, sojourner_id)
    grant_subscription_credits(service, sojourner_id, "100")

    # Deactivate after preflight; settlement should still succeed.
    deactivate_hosted(service, sojourner_id)

    turn_id = uuid4()
    result = _make_delivered_result(turn_id)
    event = service.settle_hosted_turn_cost(
        sojourner_id, result, policy=make_policy(), access_path=RuntimeAccessPath.HOSTED
    )
    assert event is not None


# ---------------------------------------------------------------------------
# AC 47: positive and negative MANUAL_CREDIT_ADJUSTMENT
# ---------------------------------------------------------------------------


def test_manual_adjustment_positive_and_negative(
    service: EntitlementService,
    sojourner_id: UUID,
    session: Session,
) -> None:
    """AC 47: positive and negative MANUAL_CREDIT_ADJUSTMENT events both apply."""
    from afterworlds.entitlement.orm import RuntimeEntitlementState
    from afterworlds.entitlement.payloads import ManualCreditAdjustmentPayload

    activate_hosted(service, sojourner_id)
    grant_subscription_credits(service, sojourner_id, "100")

    service.receive_entitlement_event(
        sojourner_id,
        EntitlementEventType.MANUAL_CREDIT_ADJUSTMENT,
        ManualCreditAdjustmentPayload(
            hosted_credit_delta=Decimal("20"),
            reason="bonus",
            adjusted_by="admin",
        ),
    )

    session.expire_all()
    state = session.get(RuntimeEntitlementState, sojourner_id)
    assert state is not None
    assert state.hosted_credit_balance == Decimal("120")

    service.receive_entitlement_event(
        sojourner_id,
        EntitlementEventType.MANUAL_CREDIT_ADJUSTMENT,
        ManualCreditAdjustmentPayload(
            hosted_credit_delta=Decimal("-30"),
            reason="correction",
            adjusted_by="admin",
        ),
    )

    session.expire_all()
    state = session.get(RuntimeEntitlementState, sojourner_id)
    assert state is not None
    assert state.hosted_credit_balance == Decimal("90")


# ---------------------------------------------------------------------------
# P1 regression: CREDIT_DEDUCTION with turn_id=None must be rejected before
# any DB mutation — a NULL turn_id bypasses the partial-unique index that
# enforces one settlement per turn, opening a silent duplicate-settle path.
# ---------------------------------------------------------------------------


def test_credit_deduction_requires_turn_id(
    service: EntitlementService,
    sojourner_id: UUID,
) -> None:
    """P1: receive_entitlement_event(CREDIT_DEDUCTION, turn_id=None) raises."""
    from afterworlds.entitlement.payloads import CreditDeductionPayload

    activate_hosted(service, sojourner_id)
    grant_subscription_credits(service, sojourner_id, "100")

    payload = CreditDeductionPayload(
        hosted_credit_delta=Decimal("-5"),
        top_up_credit_delta=Decimal("0"),
    )
    with pytest.raises(EntitlementSettlementError, match="turn_id"):
        service.receive_entitlement_event(
            sojourner_id,
            EntitlementEventType.CREDIT_DEDUCTION,
            payload,
            turn_id=None,
        )


# ---------------------------------------------------------------------------
# AC 58: ROUND_HALF_UP to four decimal places
# ---------------------------------------------------------------------------


def test_credit_computation_round_half_up() -> None:
    """AC 58: all credit computations use ROUND_HALF_UP to 4 decimal places."""
    policy = TurnCostPolicy(config=TurnCostPolicyConfig(tokens_per_credit=Decimal("3")))
    snapshots = [
        PassUsageSnapshot(
            pass_id=PipelinePassId.WRITER,
            model_tier=ModelTier.SONNET,
            input_tokens=1,
            output_tokens=1,
        )
    ]
    # 2 tokens / 3 tokens_per_credit = 0.66666...
    # ROUND_HALF_UP to 4 places = 0.6667
    deduction = policy.compute_deduction(snapshots)
    assert deduction == Decimal("0.6667")
