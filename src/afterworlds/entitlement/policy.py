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
    PipelinePassId.PLANNER: ModelTier.HAIKU,
    PipelinePassId.WRITER: ModelTier.SONNET,
    PipelinePassId.EXTRACTOR: ModelTier.SONNET,
    PipelinePassId.CONTRADICTION: ModelTier.HAIKU,
    PipelinePassId.INPUT_SAFETY: ModelTier.HAIKU,
    PipelinePassId.OUTPUT_SAFETY: ModelTier.HAIKU,
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

        Non-None pass results only.  Intent classification produces no snapshot.
        Safety pass snapshots are included when present (consumed hosted compute).

        Uses ``PASS_TIER_DEFAULTS`` for model_tier since v1 pass results do not
        report model_tier directly.

        Raises ``EntitlementSettlementError`` if ``input_token_count`` or
        ``output_token_count`` is None on any pass result.
        """
        # Inline imports to avoid circular imports from pipeline modules.
        from afterworlds.pipeline.extractor.models import (
            ExtractorResult,
        )  # noqa: PLC0415
        from afterworlds.pipeline.planner.models import PlannerResult  # noqa: PLC0415
        from afterworlds.pipeline.safety.models import SafetyResult  # noqa: PLC0415

        snapshots: list[PassUsageSnapshot] = []

        def _require_tokens(
            pass_id: PipelinePassId,
            input_t: int | None,
            output_t: int | None,
            cache_read: int | None,
            cache_create: int | None,
            model_id: str | None,
        ) -> PassUsageSnapshot:
            if input_t is None:
                raise EntitlementSettlementError(
                    f"input_token_count is None for pass {pass_id}; cannot settle"
                )
            if output_t is None:
                raise EntitlementSettlementError(
                    f"output_token_count is None for pass {pass_id}; cannot settle"
                )
            return PassUsageSnapshot(
                pass_id=pass_id,
                model_tier=PASS_TIER_DEFAULTS[pass_id],
                model_identifier=model_id,
                input_tokens=input_t,
                output_tokens=output_t,
                cache_read_tokens=cache_read or 0,
                cache_creation_tokens=cache_create or 0,
            )

        def _safety_snapshot(
            pass_id: PipelinePassId, sr: SafetyResult
        ) -> PassUsageSnapshot:
            usage = sr.usage
            in_t = usage.input_tokens if usage else None
            out_t = usage.output_tokens if usage else None
            cr = usage.cache_read_input_tokens if usage else None
            cc = usage.cache_creation_input_tokens if usage else None
            return _require_tokens(pass_id, in_t, out_t, cr, cc, None)

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
                )
            )

        if result.writer_result is not None:
            wr = result.writer_result
            snapshots.append(
                _require_tokens(
                    PipelinePassId.WRITER,
                    wr.input_token_count,
                    wr.output_token_count,
                    wr.cache_read_token_count,
                    wr.cache_creation_token_count,
                    wr.model_identifier,
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
                    None,
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
