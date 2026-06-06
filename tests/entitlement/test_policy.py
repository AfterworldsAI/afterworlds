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


# Forward declarations to satisfy mypy in the last test
from uuid import UUID  # noqa: E402

from sqlalchemy.orm import Session  # noqa: E402

from afterworlds.entitlement.service import EntitlementService  # noqa: E402
