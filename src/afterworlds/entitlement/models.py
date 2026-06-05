"""Pure Pydantic models for entitlement service results — CRD Issue 13.

These are not ORM models.  They carry the typed service-layer DTOs:
``AccessPathStatus`` (returned by ``get_access_path_status``),
``EntitlementStateSnapshot`` (used by the pure replay function),
``PassUsageSnapshot`` (per-pass token usage for cost computation), and
``TurnCostPolicyConfig`` (configurable weights for ``TurnCostPolicy``).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from afterworlds.entitlement.enums import (
    HostedAccessPlan,
    HostedUnavailableReason,
    ModelTier,
    PipelinePassId,
)


class AccessPathStatus(BaseModel):
    """Typed result from ``EntitlementService.get_access_path_status``.

    ``None`` on balance fields means "no account/plan".  ``Decimal("0")`` means
    "plan exists, balance depleted".  Inactive hosted access may retain credit
    balances; turns are blocked but balances are not destroyed.
    """

    model_config = ConfigDict(extra="forbid")

    sojourner_id: UUID
    hosted_turn_available: bool
    byok_turn_available: bool
    cloud_services_active: bool

    hosted_credit_balance: Decimal | None
    top_up_credit_balance: Decimal | None
    total_hosted_credit_balance: Decimal | None

    hosted_unavailable_reason: HostedUnavailableReason | None = None
    cloud_services_lapsed: bool = False


class EntitlementStateSnapshot(BaseModel):
    """Pure Pydantic snapshot used by ``rebuild_entitlement_state``.

    Not an ORM model.  Fields default to no-access state so replay of an
    empty event list returns a valid snapshot.
    """

    model_config = ConfigDict(extra="forbid")

    sojourner_id: UUID
    hosted_access_active: bool = False
    hosted_access_plan: HostedAccessPlan | None = None
    hosted_credit_balance: Decimal = Decimal("0")
    top_up_credit_balance: Decimal = Decimal("0")
    byok_license_active: bool = False
    byok_license_purchased_at: datetime | None = None
    cloud_services_active: bool = False
    cloud_services_expires_at: datetime | None = None


class PassUsageSnapshot(BaseModel):
    """Per-pass token usage for turn cost computation.

    ``input_tokens`` and ``output_tokens`` are required; absence raises
    ``EntitlementSettlementError``.  ``cache_read_tokens`` and
    ``cache_creation_tokens`` default to 0; absence is not an error.

    ``provider`` is required when a ``NormalizationFactorProvider`` is
    supplied to ``TurnCostPolicy.compute_deduction``.  For v1 (normalization
    always None), provider may be None.

    ``model_identifier`` is for audit only and is not used in cost computation.
    """

    model_config = ConfigDict(extra="forbid")

    pass_id: PipelinePassId
    model_tier: ModelTier
    provider: str | None = None
    model_identifier: str | None = None
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int = 0
    cache_creation_tokens: int = 0


@dataclass
class TurnCostPolicyConfig:
    """Configurable weights for ``TurnCostPolicy``.

    All weights are provider-neutral Decimal constants.  Issue 13 owns these
    defaults.  Issue 14 supplies ``NormalizationFactorProvider`` for
    provider/platform-specific calibration inputs; it does not change these
    defaults.

    ``tokens_per_credit`` is a placeholder; the final value is an owner
    decision before pricing lock.
    """

    haiku_tier_weight: Decimal = field(default_factory=lambda: Decimal("1.0"))
    sonnet_tier_weight: Decimal = field(default_factory=lambda: Decimal("1.0"))
    input_token_weight: Decimal = field(default_factory=lambda: Decimal("1.0"))
    output_token_weight: Decimal = field(default_factory=lambda: Decimal("1.0"))
    cache_creation_weight: Decimal = field(default_factory=lambda: Decimal("1.0"))
    cache_read_weight: Decimal = field(default_factory=lambda: Decimal("1.0"))
    tokens_per_credit: Decimal = field(default_factory=lambda: Decimal("1000"))
