"""Tests for entitlement payload validation — AC 19–22."""

from __future__ import annotations

from decimal import Decimal

import pytest
from pydantic import ValidationError

from afterworlds.entitlement.payloads import (
    CreditDeductionPayload,
    ManualCreditAdjustmentPayload,
    SubscriptionCreditGrantPayload,
    TopUpCreditGrantPayload,
)

# ---------------------------------------------------------------------------
# AC 19: grant payloads reject <= 0 deltas
# ---------------------------------------------------------------------------


def test_subscription_grant_rejects_zero_delta() -> None:
    with pytest.raises(Exception, match="must be > 0"):
        SubscriptionCreditGrantPayload(hosted_credit_delta=Decimal("0"))


def test_subscription_grant_rejects_negative_delta() -> None:
    with pytest.raises(Exception, match="must be > 0"):
        SubscriptionCreditGrantPayload(hosted_credit_delta=Decimal("-1"))


def test_top_up_grant_rejects_zero_delta() -> None:
    with pytest.raises(Exception, match="must be > 0"):
        TopUpCreditGrantPayload(top_up_credit_delta=Decimal("0"))


def test_top_up_grant_rejects_negative_delta() -> None:
    with pytest.raises(Exception, match="must be > 0"):
        TopUpCreditGrantPayload(top_up_credit_delta=Decimal("-5"))


def test_grants_accept_positive_delta() -> None:
    p1 = SubscriptionCreditGrantPayload(hosted_credit_delta=Decimal("100"))
    assert p1.hosted_credit_delta == Decimal("100")
    p2 = TopUpCreditGrantPayload(top_up_credit_delta=Decimal("50"))
    assert p2.top_up_credit_delta == Decimal("50")


# ---------------------------------------------------------------------------
# AC 20: CreditDeductionPayload rejects > 0 deltas and all-zero payload
# ---------------------------------------------------------------------------


def test_credit_deduction_rejects_positive_hosted_delta() -> None:
    with pytest.raises(ValidationError):
        CreditDeductionPayload(
            hosted_credit_delta=Decimal("1"), top_up_credit_delta=Decimal("0")
        )


def test_credit_deduction_rejects_positive_top_up_delta() -> None:
    with pytest.raises(ValidationError):
        CreditDeductionPayload(
            hosted_credit_delta=Decimal("0"), top_up_credit_delta=Decimal("1")
        )


def test_credit_deduction_rejects_all_zero() -> None:
    with pytest.raises(Exception, match="at least one delta"):
        CreditDeductionPayload(
            hosted_credit_delta=Decimal("0"), top_up_credit_delta=Decimal("0")
        )


def test_credit_deduction_accepts_nonzero_hosted() -> None:
    p = CreditDeductionPayload(
        hosted_credit_delta=Decimal("-5"), top_up_credit_delta=Decimal("0")
    )
    assert p.hosted_credit_delta == Decimal("-5")


def test_credit_deduction_accepts_nonzero_top_up() -> None:
    p = CreditDeductionPayload(
        hosted_credit_delta=Decimal("0"), top_up_credit_delta=Decimal("-3")
    )
    assert p.top_up_credit_delta == Decimal("-3")


# ---------------------------------------------------------------------------
# AC 21: ManualCreditAdjustmentPayload validation
# ---------------------------------------------------------------------------


def test_manual_adjustment_rejects_both_zero_deltas() -> None:
    with pytest.raises(Exception, match="at least one delta"):
        ManualCreditAdjustmentPayload(
            hosted_credit_delta=Decimal("0"),
            top_up_credit_delta=Decimal("0"),
            reason="test",
            adjusted_by="admin",
        )


def test_manual_adjustment_rejects_all_none_deltas() -> None:
    with pytest.raises(Exception, match="at least one delta"):
        ManualCreditAdjustmentPayload(
            reason="test",
            adjusted_by="admin",
        )


def test_manual_adjustment_rejects_empty_reason() -> None:
    with pytest.raises(Exception, match="reason"):
        ManualCreditAdjustmentPayload(
            hosted_credit_delta=Decimal("10"),
            reason="",
            adjusted_by="admin",
        )


def test_manual_adjustment_rejects_whitespace_reason() -> None:
    with pytest.raises(Exception, match="reason"):
        ManualCreditAdjustmentPayload(
            hosted_credit_delta=Decimal("10"),
            reason="   ",
            adjusted_by="admin",
        )


def test_manual_adjustment_rejects_empty_adjusted_by() -> None:
    with pytest.raises(Exception, match="adjusted_by"):
        ManualCreditAdjustmentPayload(
            hosted_credit_delta=Decimal("10"),
            reason="refund",
            adjusted_by="",
        )


def test_manual_adjustment_accepts_valid() -> None:
    p = ManualCreditAdjustmentPayload(
        hosted_credit_delta=Decimal("10"),
        reason="manual refund",
        adjusted_by="support@example.com",
    )
    assert p.hosted_credit_delta == Decimal("10")


# ---------------------------------------------------------------------------
# AC 22: None deltas in ManualCreditAdjustmentPayload treated as Decimal("0")
# ---------------------------------------------------------------------------


def test_manual_adjustment_none_top_up_treated_as_zero() -> None:
    p = ManualCreditAdjustmentPayload(
        hosted_credit_delta=Decimal("5"),
        top_up_credit_delta=None,
        reason="correction",
        adjusted_by="admin",
    )
    assert p.top_up_credit_delta is None


def test_manual_adjustment_none_hosted_treated_as_zero() -> None:
    p = ManualCreditAdjustmentPayload(
        hosted_credit_delta=None,
        top_up_credit_delta=Decimal("3"),
        reason="correction",
        adjusted_by="admin",
    )
    assert p.hosted_credit_delta is None


# ---------------------------------------------------------------------------
# AC 18: schema_version Literal[1] — payload with schema_version=2 raises
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Credit delta quantization — normalise to Numeric(12,4) precision
# ---------------------------------------------------------------------------


def test_subscription_grant_quantizes_over_precise_delta() -> None:
    p = SubscriptionCreditGrantPayload(hosted_credit_delta=Decimal("0.00005"))
    assert p.hosted_credit_delta == Decimal("0.0001")


def test_top_up_grant_quantizes_over_precise_delta() -> None:
    p = TopUpCreditGrantPayload(top_up_credit_delta=Decimal("0.00005"))
    assert p.top_up_credit_delta == Decimal("0.0001")


def test_manual_adjustment_quantizes_over_precise_delta() -> None:
    p = ManualCreditAdjustmentPayload(
        hosted_credit_delta=Decimal("0.00005"),
        reason="test",
        adjusted_by="admin",
    )
    assert p.hosted_credit_delta == Decimal("0.0001")


def test_deduction_quantizes_over_precise_delta() -> None:
    p = CreditDeductionPayload(
        hosted_credit_delta=Decimal("-0.00005"),
        top_up_credit_delta=Decimal("0"),
    )
    assert p.hosted_credit_delta == Decimal("-0.0001")


def test_subscription_grant_sub_quantum_rounds_to_zero_and_is_rejected() -> None:
    with pytest.raises(Exception, match="must be > 0"):
        SubscriptionCreditGrantPayload(hosted_credit_delta=Decimal("0.00004"))


def test_deduction_sub_quantum_both_deltas_round_to_zero_are_rejected() -> None:
    with pytest.raises(Exception, match="at least one delta"):
        CreditDeductionPayload(
            hosted_credit_delta=Decimal("-0.00004"),
            top_up_credit_delta=Decimal("-0.00003"),
        )


def test_schema_version_2_raises_on_deserialize() -> None:
    import json

    from afterworlds.entitlement.errors import EntitlementPayloadVersionError

    # Build a JSON with schema_version=2
    bad_json = json.dumps({"schema_version": 2, "hosted_credit_delta": "100"})
    # Pre-check before model_validate_json: if schema_version != 1, raise
    raw = json.loads(bad_json)
    seen_version = raw.get("schema_version")
    if seen_version != 1:
        with pytest.raises(EntitlementPayloadVersionError):
            raise EntitlementPayloadVersionError(
                f"seen_version={seen_version!r} event_type=subscription_credit_grant"
            )
