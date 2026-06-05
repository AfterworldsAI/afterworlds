"""Entitlement event payload classes — CRD Issue 13.

All payloads carry ``schema_version: Literal[1] = 1`` so that Pydantic rejects
any stored JSON whose version does not match.  Payloads must not contain raw
API keys, payment secrets, or provider credentials.

``effective_at`` fields in payloads are business timestamps (metadata recording
when an event took effect commercially).  They do not affect replay order.
Replay order is determined by ``EntitlementEvent.global_sequence``.

Serialization: ``payload.model_dump_json()`` — always includes ``schema_version``.

Deserialization: ``ENTITLEMENT_PAYLOAD_CLASS_MAP[event_type].model_validate_json()``
— full Pydantic validation runs on every deserialize, including the
``schema_version`` literal check.  Pre-check the version via ``json.loads``
before calling ``model_validate_json``; if ``schema_version`` is absent or not 1,
raise ``EntitlementPayloadVersionError`` directly.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from afterworlds.entitlement.enums import (
    CloudServicesDeactivationReason,
    EntitlementEventType,
    HostedAccessDeactivationReason,
    HostedAccessPlan,
)


class HostedAccessActivatedPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal[1] = 1
    plan: HostedAccessPlan
    effective_at: datetime
    external_source: str | None = None
    external_reference_id: str | None = None


class HostedAccessDeactivatedPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal[1] = 1
    effective_at: datetime
    reason: HostedAccessDeactivationReason
    detail: str | None = None


class SubscriptionCreditGrantPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal[1] = 1
    hosted_credit_delta: Decimal
    period_start: datetime | None = None
    external_source: str | None = None
    external_reference_id: str | None = None

    @field_validator("hosted_credit_delta")
    @classmethod
    def must_be_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("hosted_credit_delta must be > 0 for a credit grant")
        return v


class TopUpCreditGrantPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal[1] = 1
    top_up_credit_delta: Decimal
    external_source: str | None = None
    external_reference_id: str | None = None

    @field_validator("top_up_credit_delta")
    @classmethod
    def must_be_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("top_up_credit_delta must be > 0 for a credit grant")
        return v


class CreditDeductionPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal[1] = 1
    hosted_credit_delta: Decimal
    top_up_credit_delta: Decimal

    @field_validator("hosted_credit_delta", "top_up_credit_delta")
    @classmethod
    def must_be_non_positive(cls, v: Decimal) -> Decimal:
        if v > 0:
            raise ValueError("credit deltas must be <= 0 for a deduction")
        return v

    @model_validator(mode="after")
    def at_least_one_nonzero(self) -> CreditDeductionPayload:
        if self.hosted_credit_delta == 0 and self.top_up_credit_delta == 0:
            raise ValueError("at least one delta must be < 0 for a credit deduction")
        return self


class ByokLicenseActivatedPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal[1] = 1
    purchased_at: datetime
    external_source: str | None = None
    external_reference_id: str | None = None


class CloudServicesActivatedPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal[1] = 1
    expires_at: datetime
    external_source: str | None = None
    external_reference_id: str | None = None


class CloudServicesLapsedPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal[1] = 1
    effective_at: datetime
    reason: CloudServicesDeactivationReason
    detail: str | None = None


class ManualCreditAdjustmentPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal[1] = 1
    hosted_credit_delta: Decimal | None = None
    top_up_credit_delta: Decimal | None = None
    reason: str
    adjusted_by: str

    @model_validator(mode="after")
    def at_least_one_non_zero_delta(self) -> ManualCreditAdjustmentPayload:
        hd = self.hosted_credit_delta or Decimal("0")
        td = self.top_up_credit_delta or Decimal("0")
        if hd == 0 and td == 0:
            raise ValueError(
                "at least one delta must be non-zero for a manual adjustment"
            )
        if not self.reason.strip():
            raise ValueError("reason must not be empty or whitespace")
        if not self.adjusted_by.strip():
            raise ValueError("adjusted_by must not be empty or whitespace")
        return self


ENTITLEMENT_PAYLOAD_CLASS_MAP: dict[EntitlementEventType, type[BaseModel]] = {
    EntitlementEventType.HOSTED_ACCESS_ACTIVATED: HostedAccessActivatedPayload,
    EntitlementEventType.HOSTED_ACCESS_DEACTIVATED: HostedAccessDeactivatedPayload,
    EntitlementEventType.SUBSCRIPTION_CREDIT_GRANT: SubscriptionCreditGrantPayload,
    EntitlementEventType.TOP_UP_CREDIT_GRANT: TopUpCreditGrantPayload,
    EntitlementEventType.CREDIT_DEDUCTION: CreditDeductionPayload,
    EntitlementEventType.BYOK_LICENSE_ACTIVATED: ByokLicenseActivatedPayload,
    EntitlementEventType.CLOUD_SERVICES_ACTIVATED: CloudServicesActivatedPayload,
    EntitlementEventType.CLOUD_SERVICES_LAPSED: CloudServicesLapsedPayload,
    EntitlementEventType.MANUAL_CREDIT_ADJUSTMENT: ManualCreditAdjustmentPayload,
}

EntitlementEventPayload = (
    HostedAccessActivatedPayload
    | HostedAccessDeactivatedPayload
    | SubscriptionCreditGrantPayload
    | TopUpCreditGrantPayload
    | CreditDeductionPayload
    | ByokLicenseActivatedPayload
    | CloudServicesActivatedPayload
    | CloudServicesLapsedPayload
    | ManualCreditAdjustmentPayload
)
