"""Turn cost policy — CRD Issue 13.

``TurnCostPolicy`` computes the credit deduction for a delivered turn.
``NormalizationFactorProvider`` is a protocol seam for Issue 14's
provider/platform-specific calibration inputs.

Issue 13 owns the policy shape and defaults.  Issue 14 supplies the
``NormalizationFactorProvider`` implementation with provider/platform-specific
normalization factors and cache calibration inputs; it does not change these
defaults.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from typing import TYPE_CHECKING, Protocol

from afterworlds.entitlement.enums import ModelTier, PipelinePassId
from afterworlds.entitlement.errors import EntitlementSettlementError
from afterworlds.entitlement.models import PassUsageSnapshot, TurnCostPolicyConfig

if TYPE_CHECKING:
    from afterworlds.pipeline.orchestrator.models import OrchestrationResult


PASS_TIER_DEFAULTS: dict[PipelinePassId, ModelTier] = {
    # Round 8 remediation (PR #126 P1): fallback only -- OrchestrationResult
    # .intent_classifier_usage already carries its own model_tier from the
    # provider-routed call, so this entry is consulted only if that usage
    # snapshot were ever missing a tier (kept in sync with the
    # provider-adapter pass profile per that module's "MUST agree" invariant).
    PipelinePassId.INTENT_CLASSIFIER: ModelTier.HAIKU,
    PipelinePassId.PLANNER: ModelTier.HAIKU,
    PipelinePassId.RPG_ADJUDICATION: ModelTier.HAIKU,
    PipelinePassId.WRITER: ModelTier.SONNET,
    PipelinePassId.EXTRACTOR: ModelTier.SONNET,
    PipelinePassId.CONTRADICTION: ModelTier.HAIKU,
    PipelinePassId.INPUT_SAFETY: ModelTier.HAIKU,
    PipelinePassId.OUTPUT_SAFETY: ModelTier.HAIKU,
    PipelinePassId.BRANCHING_WRITER: ModelTier.SONNET,
    PipelinePassId.BRANCHING_OOC_CONFIG_EXTRACTOR: ModelTier.HAIKU,
    PipelinePassId.WRITING_OOC_CONFIG_EXTRACTOR: ModelTier.HAIKU,
}

_CREDIT_QUANTIZE = Decimal("0.0001")


class NormalizationFactorProvider(Protocol):
    """Issue 14 supplies provider/platform-specific normalization and cache
    calibration inputs.
    """

    def get_factor(self, provider: str, model_tier: ModelTier) -> Decimal: ...


class TurnCostPolicy:
    """Computes the hosted credit deduction for a delivered turn.

    Accepts an optional ``TurnCostPolicyConfig`` via constructor injection.
    The ``None`` sentinel pattern is required; do not use a default mutable
    parameter value.
    """

    def __init__(self, config: TurnCostPolicyConfig | None = None) -> None:
        self._config = config if config is not None else TurnCostPolicyConfig()

    def compute_deduction(
        self,
        snapshots: list[PassUsageSnapshot],
        normalization: NormalizationFactorProvider | None = None,
    ) -> Decimal:
        """Compute total credit deduction for the given pass usage snapshots.

        Formula per snapshot::

            effective_tokens = (
                input_tokens * input_token_weight
                + output_tokens * output_token_weight
                + cache_creation_tokens * cache_creation_weight
                + cache_read_tokens * cache_read_weight
            ) * tier_weight * normalization_factor

        Total deduction = quantize(
            sum(effective_tokens) / tokens_per_credit,
            Decimal("0.0001"), ROUND_HALF_UP
        )

        Raises ``EntitlementSettlementError`` for:
        - Empty snapshot list.
        - Snapshot with normalization supplied but provider=None.
        - Computed deduction <= 0 for non-empty list.
        """
        if not snapshots:
            raise EntitlementSettlementError(
                "snapshot list is empty; cannot compute deduction"
            )

        cfg = self._config
        total_effective = Decimal("0")

        for snap in snapshots:
            if normalization is not None and snap.provider is None:
                raise EntitlementSettlementError(
                    "normalization supplied but snapshot.provider is None"
                    f" for pass {snap.pass_id}"
                )

            norm_factor = (
                normalization.get_factor(snap.provider, snap.model_tier)  # type: ignore[arg-type]
                if normalization is not None
                else Decimal("1.0")
            )

            tier_weight = (
                cfg.haiku_tier_weight
                if snap.model_tier == ModelTier.HAIKU
                else cfg.sonnet_tier_weight
            )

            effective = (
                (
                    Decimal(snap.input_tokens) * cfg.input_token_weight
                    + Decimal(snap.output_tokens) * cfg.output_token_weight
                    + Decimal(snap.cache_creation_tokens) * cfg.cache_creation_weight
                    + Decimal(snap.cache_read_tokens) * cfg.cache_read_weight
                )
                * tier_weight
                * norm_factor
            )

            total_effective += effective

        deduction = (total_effective / cfg.tokens_per_credit).quantize(
            _CREDIT_QUANTIZE, rounding=ROUND_HALF_UP
        )

        if deduction <= 0:
            raise EntitlementSettlementError(
                f"computed deduction is {deduction!r} (<= 0)"
                " for non-empty snapshot list"
            )

        return deduction

    @classmethod
    def extract_snapshots(cls, result: OrchestrationResult) -> list[PassUsageSnapshot]:
        """Extract ``PassUsageSnapshot`` objects from a delivered OrchestrationResult.

        Non-None pass results only.  Intent classification is included via
        ``result.intent_classifier_usage`` when present (Round 8 remediation,
        PR #126 P1).  Safety pass snapshots are included when present
        (consumed hosted compute).

        Uses pass result ``model_tier`` when set; falls back to
        ``PASS_TIER_DEFAULTS`` for backward compatibility.

        Raises ``EntitlementSettlementError`` if ``input_token_count`` or
        ``output_token_count`` is None on any pass result.
        """
        # Inline imports to avoid circular imports from pipeline modules.
        from afterworlds.pipeline.extractor.models import (
            ExtractorResult,
        )  # noqa: PLC0415
        from afterworlds.pipeline.planner.models import PlannerResult  # noqa: PLC0415
        from afterworlds.pipeline.rpg.models import (
            AdjudicationPassResult,
        )  # noqa: PLC0415
        from afterworlds.pipeline.safety.models import SafetyResult  # noqa: PLC0415

        snapshots: list[PassUsageSnapshot] = []

        def _require_tokens(
            pass_id: PipelinePassId,
            input_t: int | None,
            output_t: int | None,
            cache_read: int | None,
            cache_create: int | None,
            model_id: str | None,
            provider: str | None = None,
            model_tier_str: str | None = None,
        ) -> PassUsageSnapshot:
            if input_t is None:
                raise EntitlementSettlementError(
                    f"input_token_count is None for pass {pass_id}; cannot settle"
                )
            if output_t is None:
                raise EntitlementSettlementError(
                    f"output_token_count is None for pass {pass_id}; cannot settle"
                )
            tier: ModelTier
            if model_tier_str is not None:
                try:
                    tier = ModelTier(model_tier_str)
                except ValueError:
                    tier = PASS_TIER_DEFAULTS[pass_id]
            else:
                tier = PASS_TIER_DEFAULTS[pass_id]
            return PassUsageSnapshot(
                pass_id=pass_id,
                model_tier=tier,
                provider=provider,
                model_identifier=model_id,
                input_tokens=input_t,
                output_tokens=output_t,
                cache_read_tokens=cache_read or 0,
                cache_creation_tokens=cache_create or 0,
            )

        def _safety_snapshot(
            pass_id: PipelinePassId, sr: SafetyResult
        ) -> PassUsageSnapshot:
            return _require_tokens(
                pass_id,
                sr.input_token_count,
                sr.output_token_count,
                sr.cache_read_token_count,
                sr.cache_creation_token_count,
                sr.model_identifier,
                provider=sr.provider,
                model_tier_str=sr.model_tier,
            )

        if result.intent_classifier_usage is not None:
            icu = result.intent_classifier_usage
            snapshots.append(
                _require_tokens(
                    PipelinePassId.INTENT_CLASSIFIER,
                    icu.input_token_count,
                    icu.output_token_count,
                    icu.cache_read_token_count,
                    icu.cache_creation_token_count,
                    icu.model_identifier,
                    provider=icu.provider,
                    model_tier_str=icu.model_tier.value,
                )
            )

        if result.input_safety_result is not None:
            snapshots.append(
                _safety_snapshot(
                    PipelinePassId.INPUT_SAFETY, result.input_safety_result
                )
            )

        if result.planner_result is not None:
            assert isinstance(result.planner_result, PlannerResult)
            pr = result.planner_result
            snapshots.append(
                _require_tokens(
                    PipelinePassId.PLANNER,
                    pr.input_token_count,
                    pr.output_token_count,
                    pr.cache_read_token_count,
                    pr.cache_creation_token_count,
                    pr.model_identifier,
                    provider=pr.provider,
                    model_tier_str=pr.model_tier,
                )
            )

        if result.rpg_adjudication_result is not None:
            assert isinstance(result.rpg_adjudication_result, AdjudicationPassResult)
            ar = result.rpg_adjudication_result
            is_code_only = (
                ar.provider is None
                and ar.model_identifier is None
                and ar.model_tier is None
                and ar.input_token_count is None
                and ar.output_token_count is None
                and ar.cache_read_token_count is None
                and ar.cache_creation_token_count is None
            )
            if not is_code_only:
                snapshots.append(
                    _require_tokens(
                        PipelinePassId.RPG_ADJUDICATION,
                        ar.input_token_count,
                        ar.output_token_count,
                        ar.cache_read_token_count,
                        ar.cache_creation_token_count,
                        ar.model_identifier,
                        provider=ar.provider,
                        model_tier_str=ar.model_tier,
                    )
                )

        if result.writer_result is not None and result.branching_pass_result is None:
            wr = result.writer_result
            snapshots.append(
                _require_tokens(
                    PipelinePassId.WRITER,
                    wr.input_token_count,
                    wr.output_token_count,
                    wr.cache_read_token_count,
                    wr.cache_creation_token_count,
                    wr.model_identifier,
                    provider=wr.provider,
                    model_tier_str=wr.model_tier,
                )
            )

        if result.output_safety_result is not None:
            snapshots.append(
                _safety_snapshot(
                    PipelinePassId.OUTPUT_SAFETY, result.output_safety_result
                )
            )

        if result.extractor_result is not None:
            assert isinstance(result.extractor_result, ExtractorResult)
            er = result.extractor_result
            snapshots.append(
                _require_tokens(
                    PipelinePassId.EXTRACTOR,
                    er.input_token_count,
                    er.output_token_count,
                    er.cache_read_token_count,
                    er.cache_creation_token_count,
                    er.model_identifier,
                    provider=er.provider,
                    model_tier_str=er.model_tier,
                )
            )

        if result.contradiction_result is not None:
            cr_result = result.contradiction_result
            snapshots.append(
                _require_tokens(
                    PipelinePassId.CONTRADICTION,
                    cr_result.input_token_count,
                    cr_result.output_token_count,
                    cr_result.cache_read_token_count,
                    cr_result.cache_creation_token_count,
                    cr_result.model_identifier,
                    provider=cr_result.provider,
                    model_tier_str=cr_result.model_tier,
                )
            )

        if result.branching_pass_result is not None:
            from afterworlds.pipeline.branching.models import (  # noqa: PLC0415
                BranchingPassResult,
            )

            assert isinstance(result.branching_pass_result, BranchingPassResult)
            bpr = result.branching_pass_result
            snapshots.append(
                _require_tokens(
                    PipelinePassId.BRANCHING_WRITER,
                    bpr.input_token_count,
                    bpr.output_token_count,
                    bpr.cache_read_token_count,
                    bpr.cache_creation_token_count,
                    bpr.model_identifier,
                    provider=bpr.provider,
                    model_tier_str=bpr.model_tier,
                )
            )

        if result.branching_ooc_config_result is not None:
            from afterworlds.pipeline.branching.models import (  # noqa: PLC0415
                BranchingOocConfigExtractorResult,
            )

            assert isinstance(
                result.branching_ooc_config_result, BranchingOocConfigExtractorResult
            )
            bocr = result.branching_ooc_config_result
            snapshots.append(
                _require_tokens(
                    PipelinePassId.BRANCHING_OOC_CONFIG_EXTRACTOR,
                    bocr.input_token_count,
                    bocr.output_token_count,
                    bocr.cache_read_token_count,
                    bocr.cache_creation_token_count,
                    bocr.model_identifier,
                    provider=bocr.provider,
                    model_tier_str=bocr.model_tier,
                )
            )

        if result.writing_ooc_config_result is not None:
            from afterworlds.pipeline.writing.models import (  # noqa: PLC0415
                WritingOocConfigExtractorResult,
            )

            assert isinstance(
                result.writing_ooc_config_result, WritingOocConfigExtractorResult
            )
            wocr = result.writing_ooc_config_result
            snapshots.append(
                _require_tokens(
                    PipelinePassId.WRITING_OOC_CONFIG_EXTRACTOR,
                    wocr.input_token_count,
                    wocr.output_token_count,
                    wocr.cache_read_token_count,
                    wocr.cache_creation_token_count,
                    wocr.model_identifier,
                    provider=wocr.provider,
                    model_tier_str=wocr.model_tier,
                )
            )

        return snapshots

    @classmethod
    def compute_pool_split(
        cls,
        total_deduction: Decimal,
        hosted_balance: Decimal,
        top_up_balance: Decimal,
    ) -> tuple[Decimal, Decimal]:
        """Return (hosted_delta, top_up_delta), both <= 0.

        Depletes hosted first (positive balance portion only), then top-up.
        Any remaining deficit stays on hosted (balance may go negative per
        Owner Decision #3).
        """
        from_hosted = min(total_deduction, max(hosted_balance, Decimal("0")))
        remaining = total_deduction - from_hosted
        from_top_up = min(remaining, max(top_up_balance, Decimal("0")))
        still_remaining = remaining - from_top_up
        return -(from_hosted + still_remaining), -from_top_up
