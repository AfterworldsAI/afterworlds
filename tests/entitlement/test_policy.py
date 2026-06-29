"""TurnCostPolicy tests — AC 51–59."""

from __future__ import annotations

from decimal import Decimal

import pytest

from afterworlds.entitlement.enums import ModelTier, PipelinePassId
from afterworlds.entitlement.errors import EntitlementSettlementError
from afterworlds.entitlement.models import PassUsageSnapshot, TurnCostPolicyConfig
from afterworlds.entitlement.policy import TurnCostPolicy
from tests.entitlement.conftest import make_pass_snapshot, make_policy

# ---------------------------------------------------------------------------
# AC 51: two instances with different weights compute different deductions
# ---------------------------------------------------------------------------


def test_different_configs_produce_different_deductions() -> None:
    """AC 51: two TurnCostPolicy instances with different weights differ."""
    snapshots = [make_pass_snapshot(input_tokens=1000, output_tokens=1000)]

    policy_a = TurnCostPolicy(
        config=TurnCostPolicyConfig(tokens_per_credit=Decimal("100"))
    )
    policy_b = TurnCostPolicy(
        config=TurnCostPolicyConfig(tokens_per_credit=Decimal("1000"))
    )

    assert policy_a.compute_deduction(snapshots) != policy_b.compute_deduction(
        snapshots
    )


def test_default_config_not_shared_between_instances() -> None:
    """AC 51: None sentinel pattern — default config not a shared mutable instance."""
    p1 = TurnCostPolicy()
    p2 = TurnCostPolicy()
    assert p1._config is not p2._config


# ---------------------------------------------------------------------------
# AC 52: different token counts produce different deductions
# ---------------------------------------------------------------------------


def test_different_token_counts_different_deductions() -> None:
    """AC 52: snapshots with different token counts differ."""
    policy = make_policy()
    snap_small = make_pass_snapshot(input_tokens=100, output_tokens=50)
    snap_large = make_pass_snapshot(input_tokens=10000, output_tokens=5000)

    d_small = policy.compute_deduction([snap_small])
    d_large = policy.compute_deduction([snap_large])
    assert d_large > d_small


# ---------------------------------------------------------------------------
# AC 53: empty snapshot list raises
# ---------------------------------------------------------------------------


def test_empty_snapshot_list_raises() -> None:
    """AC 53: empty snapshot list raises EntitlementSettlementError."""
    with pytest.raises(EntitlementSettlementError, match="empty"):
        make_policy().compute_deduction([])


# ---------------------------------------------------------------------------
# AC 56: normalization=None uses Decimal("1.0")
# ---------------------------------------------------------------------------


def test_normalization_none_uses_factor_1() -> None:
    """AC 56: normalization=None → factor 1.0 → same as explicit factor 1."""

    class IdentityNorm:
        def get_factor(self, provider: str, model_tier: ModelTier) -> Decimal:
            return Decimal("1.0")

    snapshots = [
        PassUsageSnapshot(
            pass_id=PipelinePassId.WRITER,
            model_tier=ModelTier.SONNET,
            provider="mock-provider",
            input_tokens=1000,
            output_tokens=500,
        )
    ]

    policy = make_policy()
    d_no_norm = policy.compute_deduction(snapshots)
    d_with_norm = policy.compute_deduction(snapshots, normalization=IdentityNorm())
    assert d_no_norm == d_with_norm


# ---------------------------------------------------------------------------
# AC 57: normalization supplied but provider=None raises
# ---------------------------------------------------------------------------


def test_normalization_supplied_but_provider_none_raises() -> None:
    """AC 57: normalization supplied but snapshot.provider=None raises."""

    class MockNorm:
        def get_factor(self, provider: str, model_tier: ModelTier) -> Decimal:
            return Decimal("2.0")

    snapshots = [
        PassUsageSnapshot(
            pass_id=PipelinePassId.WRITER,
            model_tier=ModelTier.SONNET,
            provider=None,  # Missing provider
            input_tokens=1000,
            output_tokens=500,
        )
    ]

    with pytest.raises(EntitlementSettlementError, match="provider is None"):
        make_policy().compute_deduction(snapshots, normalization=MockNorm())


# ---------------------------------------------------------------------------
# AC 59: extract_snapshots falls back to PASS_TIER_DEFAULTS
# ---------------------------------------------------------------------------


def test_extract_snapshots_uses_pass_tier_defaults() -> None:
    """AC 59: extract_snapshots uses PASS_TIER_DEFAULTS for model_tier."""
    from uuid import uuid4

    from afterworlds.entitlement.policy import PASS_TIER_DEFAULTS
    from tests.entitlement.test_settlement import _make_delivered_result

    result = _make_delivered_result(uuid4(), input_tokens=500, output_tokens=200)
    snapshots = TurnCostPolicy.extract_snapshots(result)  # type: ignore[arg-type]

    for snap in snapshots:
        assert snap.model_tier == PASS_TIER_DEFAULTS[snap.pass_id]


# ---------------------------------------------------------------------------
# Manual credit adjustment None deltas treated as Decimal("0") during application
# AC 22 arithmetic test
# ---------------------------------------------------------------------------


def test_manual_adjustment_none_delta_arithmetic(
    service: EntitlementService,
    sojourner_id: UUID,
    session: Session,
) -> None:
    """AC 22: None deltas in ManualCreditAdjustmentPayload treated as zero on apply."""
    from decimal import Decimal

    from afterworlds.entitlement.enums import EntitlementEventType
    from afterworlds.entitlement.orm import RuntimeEntitlementState
    from afterworlds.entitlement.payloads import ManualCreditAdjustmentPayload
    from tests.entitlement.conftest import activate_hosted, grant_subscription_credits

    activate_hosted(service, sojourner_id)
    grant_subscription_credits(service, sojourner_id, "100")

    service.receive_entitlement_event(
        sojourner_id,
        EntitlementEventType.MANUAL_CREDIT_ADJUSTMENT,
        ManualCreditAdjustmentPayload(
            hosted_credit_delta=None,  # None → 0
            top_up_credit_delta=Decimal("10"),
            reason="bonus top-up",
            adjusted_by="admin",
        ),
    )

    session.expire_all()
    state = session.get(RuntimeEntitlementState, sojourner_id)
    assert state is not None
    # hosted unchanged (delta was None → 0)
    assert state.hosted_credit_balance == Decimal("100")
    # top-up gained 10
    assert state.top_up_credit_balance == Decimal("10")


# ---------------------------------------------------------------------------
# P2 regression: negative token counts rejected at billing input boundary
# ---------------------------------------------------------------------------


def test_pass_snapshot_rejects_negative_input_tokens() -> None:
    """P2: PassUsageSnapshot rejects negative input_tokens."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        PassUsageSnapshot(
            pass_id=PipelinePassId.WRITER,
            model_tier=ModelTier.SONNET,
            input_tokens=-1,
            output_tokens=500,
        )


def test_pass_snapshot_rejects_negative_output_tokens() -> None:
    """P2: PassUsageSnapshot rejects negative output_tokens."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        PassUsageSnapshot(
            pass_id=PipelinePassId.WRITER,
            model_tier=ModelTier.SONNET,
            input_tokens=1000,
            output_tokens=-1,
        )


def test_pass_snapshot_rejects_negative_cache_read_tokens() -> None:
    """P2: PassUsageSnapshot rejects negative cache_read_tokens."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        PassUsageSnapshot(
            pass_id=PipelinePassId.WRITER,
            model_tier=ModelTier.SONNET,
            input_tokens=1000,
            output_tokens=500,
            cache_read_tokens=-1,
        )


def test_pass_snapshot_rejects_negative_cache_creation_tokens() -> None:
    """P2: PassUsageSnapshot rejects negative cache_creation_tokens."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        PassUsageSnapshot(
            pass_id=PipelinePassId.WRITER,
            model_tier=ModelTier.SONNET,
            input_tokens=1000,
            output_tokens=500,
            cache_creation_tokens=-1,
        )


def test_pass_snapshot_accepts_zero_token_counts() -> None:
    """P2: Zero token counts are valid (not rejected)."""
    snap = PassUsageSnapshot(
        pass_id=PipelinePassId.WRITER,
        model_tier=ModelTier.SONNET,
        input_tokens=0,
        output_tokens=0,
        cache_read_tokens=0,
        cache_creation_tokens=0,
    )
    assert snap.input_tokens == 0
    assert snap.cache_read_tokens == 0


def test_extract_snapshots_rejects_negative_input_tokens() -> None:
    """P2: extract_snapshots raises for negative input_token_count."""
    from uuid import uuid4

    from pydantic import ValidationError

    from tests.entitlement.test_settlement import _make_delivered_result

    result = _make_delivered_result(uuid4(), input_tokens=-1, output_tokens=500)
    with pytest.raises(ValidationError):
        TurnCostPolicy.extract_snapshots(result)  # type: ignore[arg-type]


def test_extract_snapshots_rejects_negative_output_tokens() -> None:
    """P2: extract_snapshots raises for negative output_token_count."""
    from uuid import uuid4

    from pydantic import ValidationError

    from tests.entitlement.test_settlement import _make_delivered_result

    result = _make_delivered_result(uuid4(), input_tokens=1000, output_tokens=-1)
    with pytest.raises(ValidationError):
        TurnCostPolicy.extract_snapshots(result)  # type: ignore[arg-type]


def test_compute_deduction_unchanged_for_valid_positive_snapshots() -> None:
    """P2: compute_deduction behavior is unchanged for valid positive snapshots."""
    policy = make_policy("1000")
    snap = make_pass_snapshot(input_tokens=1000, output_tokens=500)
    deduction = policy.compute_deduction([snap])
    assert deduction == Decimal("1.5")


# ---------------------------------------------------------------------------
# P1-2: extract_snapshots propagates provider and model_tier from pass results
# ---------------------------------------------------------------------------


def test_extract_snapshots_propagates_provider_and_model_tier() -> None:
    """P1-2: extract_snapshots copies provider/model_tier from pass results."""
    from uuid import uuid4

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
        OrchestrationResult,
        PipelineDisposition,
    )
    from afterworlds.pipeline.planner.models import PlannerOutput, PlannerResult
    from afterworlds.pipeline.writer.models import WriterResult

    turn_id = uuid4()
    planner = PlannerResult(
        plan=PlannerOutput(scene_goal="g", next_beat="b", facts_needed=[]),
        model_identifier="claude-haiku",
        latency_ms=0,
        input_token_count=100,
        output_token_count=50,
        cache_read_token_count=None,
        cache_creation_token_count=None,
        provider="anthropic",
        model_tier="haiku",
    )
    writer = WriterResult(
        turn_id=turn_id,
        assistant_output="prose",
        model_identifier="claude-sonnet",
        latency_ms=0,
        input_token_count=200,
        output_token_count=80,
        cache_read_token_count=None,
        cache_creation_token_count=None,
        provider="anthropic",
        model_tier="sonnet",
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
        input_token_count=150,
        output_token_count=60,
        cache_read_token_count=None,
        cache_creation_token_count=None,
        provider="anthropic",
        model_identifier="claude-sonnet",
        model_tier="sonnet",
    )
    contradiction = ContradictionResult(
        verdict=ContradictionVerdict.CLEAR,
        violations=[],
        model_identifier="claude-haiku",
        latency_ms=0,
        input_token_count=80,
        output_token_count=20,
        cache_read_token_count=None,
        cache_creation_token_count=None,
        provider="anthropic",
        model_tier="haiku",
    )
    result = OrchestrationResult(
        disposition=PipelineDisposition.DELIVERED,
        delivered_output="prose",
        turn_id=turn_id,
        intent_classification=IntentClassificationResult(
            intent_type=IntentType.IN_CHARACTER_ACTION,
            confidence=1.0,
            raw_input="",
            ambiguous=False,
        ),
        planner_result=planner,
        writer_result=writer,
        extractor_result=extractor,
        contradiction_result=contradiction,
        total_latency_ms=0,
        pass_latency_breakdown={},
    )

    snapshots = TurnCostPolicy.extract_snapshots(result)  # type: ignore[arg-type]
    assert all(s.provider == "anthropic" for s in snapshots)
    writer_snap = next(s for s in snapshots if s.pass_id == PipelinePassId.WRITER)
    assert writer_snap.model_tier == ModelTier.SONNET
    planner_snap = next(s for s in snapshots if s.pass_id == PipelinePassId.PLANNER)
    assert planner_snap.model_tier == ModelTier.HAIKU


def test_compute_deduction_with_real_normalization_succeeds() -> None:
    """P1: compute_deduction with AnthropicNormalizationFactorProvider succeeds."""
    from afterworlds.pipeline.provider.normalization import (
        AnthropicNormalizationFactorProvider,
    )

    snapshots = [
        PassUsageSnapshot(
            pass_id=PipelinePassId.WRITER,
            model_tier=ModelTier.SONNET,
            provider="anthropic",
            input_tokens=1000,
            output_tokens=500,
        )
    ]
    deduction = make_policy("1000").compute_deduction(
        snapshots, normalization=AnthropicNormalizationFactorProvider()
    )
    assert deduction > 0


# ---------------------------------------------------------------------------
# Round 7: extract_snapshots — RPG adjudication billing (code-only vs provider-backed)
# ---------------------------------------------------------------------------


def _make_adj_result(
    provider: str | None = None,
    model_identifier: str | None = None,
    model_tier: str | None = None,
    input_token_count: int | None = None,
    output_token_count: int | None = None,
    cache_read_token_count: int | None = None,
    cache_creation_token_count: int | None = None,
) -> object:
    """Minimal OrchestrationResult (PIPELINE_ERROR) with rpg_adjudication_result set."""
    from afterworlds.models.enums import IntentType
    from afterworlds.models.intent_classification import IntentClassificationResult
    from afterworlds.pipeline.orchestrator.models import (
        OrchestrationResult,
        PipelineDisposition,
    )
    from afterworlds.pipeline.rpg.models import AdjudicationPassResult

    adj = AdjudicationPassResult(
        proposals=(),
        writer_views=(),
        provider=provider,
        model_identifier=model_identifier,
        model_tier=model_tier,
        input_token_count=input_token_count,
        output_token_count=output_token_count,
        cache_read_token_count=cache_read_token_count,
        cache_creation_token_count=cache_creation_token_count,
    )
    return OrchestrationResult(
        disposition=PipelineDisposition.PIPELINE_ERROR,
        delivered_output=None,
        turn_id=None,
        intent_classification=IntentClassificationResult(
            intent_type=IntentType.IN_CHARACTER_ACTION,
            confidence=1.0,
            raw_input="",
            ambiguous=False,
        ),
        pipeline_error_summary="adjudication billing test",
        total_latency_ms=0,
        pass_latency_breakdown={},
        rpg_adjudication_result=adj,
    )


def test_extract_snapshots_rpg_adjudication_provider_backed_included() -> None:
    """Provider-backed adjudication result produces RPG_ADJUDICATION snapshot."""
    result = _make_adj_result(
        provider="anthropic",
        model_identifier="claude-haiku",
        model_tier="haiku",
        input_token_count=200,
        output_token_count=80,
    )
    snapshots = TurnCostPolicy.extract_snapshots(result)  # type: ignore[arg-type]
    pass_ids = [s.pass_id for s in snapshots]
    assert PipelinePassId.RPG_ADJUDICATION in pass_ids


def test_extract_snapshots_rpg_adjudication_code_only_excluded() -> None:
    """Code-only consume path (all None) produces no RPG_ADJUDICATION snapshot."""
    result = _make_adj_result()  # all fields default to None → code-only
    snapshots = TurnCostPolicy.extract_snapshots(result)  # type: ignore[arg-type]
    pass_ids = [s.pass_id for s in snapshots]
    assert PipelinePassId.RPG_ADJUDICATION not in pass_ids


def test_extract_snapshots_rpg_adjudication_missing_input_token_raises() -> None:
    """Provider-backed adjudication with missing input_token_count raises."""
    result = _make_adj_result(
        provider="anthropic",
        model_identifier="claude-haiku",
        model_tier="haiku",
        input_token_count=None,  # missing
        output_token_count=80,
    )
    with pytest.raises(EntitlementSettlementError):
        TurnCostPolicy.extract_snapshots(result)  # type: ignore[arg-type]


def test_extract_snapshots_rpg_adjudication_missing_output_token_raises() -> None:
    """Provider-backed adjudication with missing output_token_count raises."""
    result = _make_adj_result(
        provider="anthropic",
        model_identifier="claude-haiku",
        model_tier="haiku",
        input_token_count=200,
        output_token_count=None,  # missing
    )
    with pytest.raises(EntitlementSettlementError):
        TurnCostPolicy.extract_snapshots(result)  # type: ignore[arg-type]


def test_extract_snapshots_rpg_adjudication_partial_token_not_silently_skipped() -> (
    None
):
    """Partial token data (input set, no provider/model) is not silently skipped."""
    result = _make_adj_result(
        input_token_count=200,  # only input set; provider/model/output all None
    )
    with pytest.raises(EntitlementSettlementError):
        TurnCostPolicy.extract_snapshots(result)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Round 2 (CRD Issue 16): BRANCHING_WRITER and BRANCHING_OOC_CONFIG_EXTRACTOR
# in PASS_TIER_DEFAULTS and extract_snapshots
# ---------------------------------------------------------------------------


def test_pass_tier_defaults_includes_branching_writer() -> None:
    """BRANCHING_WRITER must be in PASS_TIER_DEFAULTS at SONNET tier."""
    from afterworlds.entitlement.enums import ModelTier
    from afterworlds.entitlement.policy import PASS_TIER_DEFAULTS

    assert PipelinePassId.BRANCHING_WRITER in PASS_TIER_DEFAULTS
    assert PASS_TIER_DEFAULTS[PipelinePassId.BRANCHING_WRITER] is ModelTier.SONNET


def test_pass_tier_defaults_includes_branching_ooc_extractor() -> None:
    """BRANCHING_OOC_CONFIG_EXTRACTOR must be in PASS_TIER_DEFAULTS at HAIKU tier."""
    from afterworlds.entitlement.enums import ModelTier
    from afterworlds.entitlement.policy import PASS_TIER_DEFAULTS

    assert PipelinePassId.BRANCHING_OOC_CONFIG_EXTRACTOR in PASS_TIER_DEFAULTS
    assert (
        PASS_TIER_DEFAULTS[PipelinePassId.BRANCHING_OOC_CONFIG_EXTRACTOR]
        is ModelTier.HAIKU
    )


def _make_branching_writer_result(
    input_token_count: int | None = 100,
    output_token_count: int | None = 50,
) -> object:
    """Minimal OrchestrationResult (PIPELINE_ERROR) with branching_pass_result set."""
    from afterworlds.models.enums import (
        BranchingCadence,
        IntentType,
        InteractionStyle,
    )
    from afterworlds.models.intent_classification import IntentClassificationResult
    from afterworlds.pipeline.branching.models import BranchingPassResult
    from afterworlds.pipeline.orchestrator.models import (
        OrchestrationResult,
        PipelineDisposition,
    )

    bpr = BranchingPassResult(
        narrative_text="test",
        interaction_style=InteractionStyle.HYBRID,
        branching_cadence=BranchingCadence.BALANCED,
        length_preference=None,
        freeform_available=True,
        branch_count_range=None,
        branch_options=[],
        branch_presentation_state="held",
        provider="anthropic",
        model_identifier="claude-sonnet-4-5",
        model_tier="sonnet",
        latency_ms=100,
        input_token_count=input_token_count,
        output_token_count=output_token_count,
    )
    return OrchestrationResult(
        disposition=PipelineDisposition.PIPELINE_ERROR,
        delivered_output=None,
        turn_id=None,
        intent_classification=IntentClassificationResult(
            intent_type=IntentType.IN_CHARACTER_ACTION,
            confidence=1.0,
            raw_input="",
            ambiguous=False,
        ),
        pipeline_error_summary="branching writer billing test",
        total_latency_ms=0,
        pass_latency_breakdown={},
        branching_pass_result=bpr,
    )


def _make_ooc_extractor_result(
    input_token_count: int | None = 50,
    output_token_count: int | None = 20,
) -> object:
    """Minimal OrchestrationResult (PIPELINE_ERROR) with ooc_config_result set."""
    from afterworlds.models.enums import IntentType
    from afterworlds.models.intent_classification import IntentClassificationResult
    from afterworlds.pipeline.branching.models import (
        BranchingConfigUpdate,
        BranchingOocConfigExtractorResult,
    )
    from afterworlds.pipeline.orchestrator.models import (
        OrchestrationResult,
        PipelineDisposition,
    )

    bocr = BranchingOocConfigExtractorResult(
        config_update=BranchingConfigUpdate(),
        provider="anthropic",
        model_identifier="claude-haiku-4-5-20251001",
        model_tier="haiku",
        latency_ms=30,
        input_token_count=input_token_count,
        output_token_count=output_token_count,
    )
    return OrchestrationResult(
        disposition=PipelineDisposition.PIPELINE_ERROR,
        delivered_output=None,
        turn_id=None,
        intent_classification=IntentClassificationResult(
            intent_type=IntentType.IN_CHARACTER_ACTION,
            confidence=1.0,
            raw_input="",
            ambiguous=False,
        ),
        pipeline_error_summary="ooc extractor billing test",
        total_latency_ms=0,
        pass_latency_breakdown={},
        branching_ooc_config_result=bocr,
    )


def test_extract_snapshots_includes_branching_writer() -> None:
    """BRANCHING_WRITER snapshot is produced when branching_pass_result is set."""
    result = _make_branching_writer_result()
    snapshots = TurnCostPolicy.extract_snapshots(result)  # type: ignore[arg-type]
    pass_ids = [s.pass_id for s in snapshots]
    assert PipelinePassId.BRANCHING_WRITER in pass_ids


def test_extract_snapshots_branching_writer_nil_input_tokens_raises() -> None:
    """Missing input_token_count on branching_pass_result raises settlement error."""
    result = _make_branching_writer_result(input_token_count=None)
    with pytest.raises(EntitlementSettlementError):
        TurnCostPolicy.extract_snapshots(result)  # type: ignore[arg-type]


def test_extract_snapshots_includes_branching_ooc_extractor() -> None:
    """BRANCHING_OOC_CONFIG_EXTRACTOR snapshot produced when ooc result is set."""
    result = _make_ooc_extractor_result()
    snapshots = TurnCostPolicy.extract_snapshots(result)  # type: ignore[arg-type]
    pass_ids = [s.pass_id for s in snapshots]
    assert PipelinePassId.BRANCHING_OOC_CONFIG_EXTRACTOR in pass_ids


def test_extract_snapshots_skips_branching_ooc_extractor_when_none() -> None:
    """No OOC extractor snapshot when branching_ooc_config_result is None."""
    result = _make_branching_writer_result()
    snapshots = TurnCostPolicy.extract_snapshots(result)  # type: ignore[arg-type]
    pass_ids = [s.pass_id for s in snapshots]
    assert PipelinePassId.BRANCHING_OOC_CONFIG_EXTRACTOR not in pass_ids


# ---------------------------------------------------------------------------
# Round 3: WRITER snapshot skipped when branching_pass_result present
# ---------------------------------------------------------------------------


def _make_branching_writer_both() -> object:
    """PIPELINE_ERROR result with BOTH writer_result and branching_pass_result.

    Simulates the synthetic WriterResult stamped for downstream prose-consuming
    passes alongside the real BranchingPassResult.  Used to verify no double-charge.
    """
    from uuid import uuid4

    from afterworlds.models.enums import BranchingCadence, IntentType, InteractionStyle
    from afterworlds.models.intent_classification import IntentClassificationResult
    from afterworlds.pipeline.branching.models import BranchingPassResult
    from afterworlds.pipeline.orchestrator.models import (
        OrchestrationResult,
        PipelineDisposition,
    )
    from afterworlds.pipeline.writer.models import WriterResult

    bpr = BranchingPassResult(
        narrative_text="test",
        interaction_style=InteractionStyle.HYBRID,
        branching_cadence=BranchingCadence.BALANCED,
        length_preference=None,
        freeform_available=True,
        branch_count_range=None,
        branch_options=[],
        branch_presentation_state="held",
        provider="anthropic",
        model_identifier="claude-sonnet-4-5",
        model_tier="sonnet",
        latency_ms=100,
        input_token_count=100,
        output_token_count=50,
    )
    wr = WriterResult(
        turn_id=uuid4(),
        assistant_output="prose",
        model_identifier="claude-sonnet-4-5",
        latency_ms=10,
        input_token_count=200,
        output_token_count=80,
        cache_read_token_count=None,
        cache_creation_token_count=None,
        provider="anthropic",
        model_tier="sonnet",
    )
    return OrchestrationResult(
        disposition=PipelineDisposition.PIPELINE_ERROR,
        delivered_output=None,
        turn_id=None,
        intent_classification=IntentClassificationResult(
            intent_type=IntentType.IN_CHARACTER_ACTION,
            confidence=1.0,
            raw_input="",
            ambiguous=False,
        ),
        pipeline_error_summary="double-charge regression test",
        total_latency_ms=0,
        pass_latency_breakdown={},
        writer_result=wr,
        branching_pass_result=bpr,
    )


def test_extract_snapshots_prose_writer_emits_writer_snapshot() -> None:
    """Prose Writer turn (no branching_pass_result) still emits WRITER snapshot."""
    from uuid import uuid4

    from tests.entitlement.test_settlement import _make_delivered_result

    result = _make_delivered_result(uuid4())
    snapshots = TurnCostPolicy.extract_snapshots(result)  # type: ignore[arg-type]
    pass_ids = [s.pass_id for s in snapshots]
    assert PipelinePassId.WRITER in pass_ids


def test_extract_snapshots_branching_writer_turn_no_writer_snapshot() -> None:
    """Branching turn: BRANCHING_WRITER present, WRITER absent (no double-charge)."""
    result = _make_branching_writer_both()
    snapshots = TurnCostPolicy.extract_snapshots(result)  # type: ignore[arg-type]
    pass_ids = [s.pass_id for s in snapshots]
    assert PipelinePassId.BRANCHING_WRITER in pass_ids
    assert PipelinePassId.WRITER not in pass_ids


def test_extract_snapshots_branching_writer_no_duplicate_snapshots() -> None:
    """No duplicate WRITER/BRANCHING_WRITER when both result fields are present."""
    result = _make_branching_writer_both()
    snapshots = TurnCostPolicy.extract_snapshots(result)  # type: ignore[arg-type]
    pass_ids = [s.pass_id for s in snapshots]
    assert pass_ids.count(PipelinePassId.WRITER) == 0
    assert pass_ids.count(PipelinePassId.BRANCHING_WRITER) == 1


# Forward declarations to satisfy mypy in the last test
from uuid import UUID  # noqa: E402

from sqlalchemy.orm import Session  # noqa: E402

from afterworlds.entitlement.service import EntitlementService  # noqa: E402
