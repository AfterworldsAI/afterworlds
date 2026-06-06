"""Access path status and precondition tests — AC 23–39."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

import pytest
from sqlalchemy.orm import Session

from afterworlds.entitlement.enums import (
    EntitlementEventType,
    HostedUnavailableReason,
)
from afterworlds.entitlement.errors import EntitlementSettlementError
from afterworlds.entitlement.service import EntitlementService
from tests.entitlement.conftest import (
    _FIXED_FUTURE,
    _FIXED_NOW,
    _FIXED_PAST,
    activate_byok,
    activate_cloud_services,
    activate_hosted,
    deactivate_hosted,
    grant_subscription_credits,
    grant_top_up_credits,
    lapse_cloud_services,
)

# ---------------------------------------------------------------------------
# AC 23: preconditions — credit mutation events require hosted_access_plan set
# ---------------------------------------------------------------------------


def test_subscription_grant_fails_without_hosted_plan(
    service: EntitlementService,
    sojourner_id: UUID,
) -> None:
    """AC 23: SUBSCRIPTION_CREDIT_GRANT raises if hosted_access_plan is None."""
    with pytest.raises(EntitlementSettlementError, match="hosted_access_plan"):
        grant_subscription_credits(service, sojourner_id)


def test_top_up_grant_fails_without_hosted_plan(
    service: EntitlementService,
    sojourner_id: UUID,
) -> None:
    """AC 23: TOP_UP_CREDIT_GRANT raises if hosted_access_plan is None."""
    with pytest.raises(EntitlementSettlementError, match="hosted_access_plan"):
        grant_top_up_credits(service, sojourner_id)


def test_credit_deduction_fails_without_hosted_plan(
    service: EntitlementService,
    sojourner_id: UUID,
) -> None:
    """AC 23: CREDIT_DEDUCTION raises if hosted_access_plan is None."""
    from afterworlds.entitlement.payloads import CreditDeductionPayload

    with pytest.raises(EntitlementSettlementError, match="hosted_access_plan"):
        service.receive_entitlement_event(
            sojourner_id,
            EntitlementEventType.CREDIT_DEDUCTION,
            CreditDeductionPayload(
                hosted_credit_delta=Decimal("-5"),
                top_up_credit_delta=Decimal("0"),
            ),
        )


# ---------------------------------------------------------------------------
# AC 24: absent Sojourner — fully-false no-access status, no row created
# ---------------------------------------------------------------------------


def test_absent_sojourner_returns_no_access_status(
    service: EntitlementService,
    sojourner_id: UUID,
    session: Session,
) -> None:
    """AC 24: get_access_path_status returns fully-false for absent Sojourner."""
    from afterworlds.entitlement.orm import RuntimeEntitlementState

    status = service.get_access_path_status(sojourner_id)
    assert status.hosted_turn_available is False
    assert status.byok_turn_available is False
    assert status.cloud_services_active is False
    assert status.cloud_services_lapsed is False  # never activated
    assert status.hosted_credit_balance is None
    assert status.top_up_credit_balance is None
    assert status.total_hosted_credit_balance is None
    # No row created
    assert session.get(RuntimeEntitlementState, sojourner_id) is None


# ---------------------------------------------------------------------------
# AC 25–26: Cloud Services expiration
# ---------------------------------------------------------------------------


def test_cloud_services_active_with_none_expires_at_is_inactive(
    service: EntitlementService,
    sojourner_id: UUID,
    session: Session,
) -> None:
    """AC 25: cloud_services_active=True + expires_at=None → active=False in status."""
    activate_hosted(service, sojourner_id)
    activate_byok(service, sojourner_id)

    # Manually set cloud_services_active=True with expires_at=None.
    from afterworlds.entitlement.orm import RuntimeEntitlementState

    state = session.get(RuntimeEntitlementState, sojourner_id)
    assert state is not None
    state.cloud_services_active = True
    state.cloud_services_expires_at = None
    session.commit()

    status = service.get_access_path_status(sojourner_id)
    assert status.cloud_services_active is False
    assert status.cloud_services_lapsed is True  # active=True + None expires_at


def test_cloud_services_active_with_expired_expires_at_is_inactive(
    service: EntitlementService,
    sojourner_id: UUID,
    session: Session,
) -> None:
    """AC 26: cloud_services_active=True + expired expires_at → active=False."""
    activate_cloud_services(service, sojourner_id, expires_at=_FIXED_PAST)

    status = service.get_access_path_status(sojourner_id)
    assert status.cloud_services_active is False
    assert status.cloud_services_lapsed is True  # active=True + expired expires_at


def test_cloud_services_lapsed_after_explicit_lapse_event(
    service: EntitlementService,
    sojourner_id: UUID,
) -> None:
    """P2 regression: CLOUD_SERVICES_LAPSED event → lapsed=True, active=False.

    CLOUD_SERVICES_LAPSED clears cloud_services_active but preserves expires_at.
    _build_access_path_status must report lapsed=True even though active=False,
    so the active-vs-lapsed distinction is not lost after an explicit lapse event.
    """
    activate_cloud_services(service, sojourner_id, expires_at=_FIXED_FUTURE)
    lapse_cloud_services(service, sojourner_id)

    status = service.get_access_path_status(sojourner_id)
    assert status.cloud_services_active is False
    assert status.cloud_services_lapsed is True


# ---------------------------------------------------------------------------
# AC 27: balance None vs Decimal("0")
# ---------------------------------------------------------------------------


def test_balances_none_when_no_hosted_plan(
    service: EntitlementService,
    sojourner_id: UUID,
) -> None:
    """AC 27: balances are None when no hosted plan ever activated."""
    activate_byok(service, sojourner_id)
    status = service.get_access_path_status(sojourner_id)
    assert status.hosted_credit_balance is None
    assert status.top_up_credit_balance is None
    assert status.total_hosted_credit_balance is None


def test_balances_zero_when_plan_depleted(
    service: EntitlementService,
    sojourner_id: UUID,
) -> None:
    """AC 27: balances are Decimal('0') when plan exists but depleted."""
    activate_hosted(service, sojourner_id)
    # No credits granted — balance starts at 0.
    status = service.get_access_path_status(sojourner_id)
    assert status.hosted_credit_balance == Decimal("0")
    assert status.top_up_credit_balance == Decimal("0")
    assert status.total_hosted_credit_balance == Decimal("0")


# ---------------------------------------------------------------------------
# AC 28: byok_turn_available independent of cloud_services
# ---------------------------------------------------------------------------


def test_byok_available_independent_of_cloud_services(
    service: EntitlementService,
    sojourner_id: UUID,
) -> None:
    """AC 28: byok_turn_available = byok_license_active, independent of CS."""
    activate_byok(service, sojourner_id)
    # No cloud services activated.
    status = service.get_access_path_status(sojourner_id)
    assert status.byok_turn_available is True
    assert status.cloud_services_active is False


# ---------------------------------------------------------------------------
# AC 29: inactive hosted access retains credit balances
# ---------------------------------------------------------------------------


def test_inactive_hosted_retains_balances(
    service: EntitlementService,
    sojourner_id: UUID,
) -> None:
    """AC 29: inactive hosted access retains credit balances; turns blocked."""
    activate_hosted(service, sojourner_id)
    grant_subscription_credits(service, sojourner_id, "100")
    deactivate_hosted(service, sojourner_id)

    status = service.get_access_path_status(sojourner_id)
    assert status.hosted_turn_available is False
    assert (
        status.hosted_unavailable_reason
        == HostedUnavailableReason.SUBSCRIPTION_INACTIVE
    )
    assert status.hosted_credit_balance == Decimal("100")


# ---------------------------------------------------------------------------
# AC 30–39: access path tests
# ---------------------------------------------------------------------------


def test_active_subscription_positive_credits_hosted_available(
    service: EntitlementService,
    sojourner_id: UUID,
) -> None:
    """AC 30: active subscription + positive credits → hosted_turn_available=True."""
    activate_hosted(service, sojourner_id)
    grant_subscription_credits(service, sojourner_id, "50")

    status = service.get_access_path_status(sojourner_id)
    assert status.hosted_turn_available is True
    assert status.hosted_unavailable_reason is None


def test_exhausted_credits_hosted_unavailable(
    service: EntitlementService,
    sojourner_id: UUID,
) -> None:
    """AC 31: exhausted credits → hosted_turn_available=False, CREDITS_EXHAUSTED."""
    activate_hosted(service, sojourner_id)
    # No credits granted.
    status = service.get_access_path_status(sojourner_id)
    assert status.hosted_turn_available is False
    assert status.hosted_unavailable_reason == HostedUnavailableReason.CREDITS_EXHAUSTED


def test_inactive_subscription_hosted_unavailable(
    service: EntitlementService,
    sojourner_id: UUID,
) -> None:
    """AC 32: inactive subscription → hosted_turn_available=False."""
    activate_hosted(service, sojourner_id)
    grant_subscription_credits(service, sojourner_id, "100")
    deactivate_hosted(service, sojourner_id)

    status = service.get_access_path_status(sojourner_id)
    assert status.hosted_turn_available is False
    assert (
        status.hosted_unavailable_reason
        == HostedUnavailableReason.SUBSCRIPTION_INACTIVE
    )


def test_active_byok_active_cloud_both_true(
    service: EntitlementService,
    sojourner_id: UUID,
) -> None:
    """AC 33: active BYOK + active Cloud Services → both available."""
    activate_byok(service, sojourner_id)
    activate_cloud_services(service, sojourner_id)

    status = service.get_access_path_status(sojourner_id)
    assert status.byok_turn_available is True
    assert status.cloud_services_active is True
    assert status.cloud_services_lapsed is False  # active with future expiry


def test_active_byok_lapsed_cloud_services(
    service: EntitlementService,
    sojourner_id: UUID,
) -> None:
    """AC 34: active BYOK + lapsed Cloud Services → byok=True, cloud=False."""
    activate_byok(service, sojourner_id)
    activate_cloud_services(service, sojourner_id, expires_at=_FIXED_PAST)

    status = service.get_access_path_status(sojourner_id)
    assert status.byok_turn_available is True
    assert status.cloud_services_active is False
    assert status.cloud_services_lapsed is True  # active=True + expired expires_at


def test_active_hosted_and_byok_both_true(
    service: EntitlementService,
    sojourner_id: UUID,
) -> None:
    """AC 35: active hosted + active BYOK → both True."""
    activate_hosted(service, sojourner_id)
    grant_subscription_credits(service, sojourner_id, "100")
    activate_byok(service, sojourner_id)

    status = service.get_access_path_status(sojourner_id)
    assert status.hosted_turn_available is True
    assert status.byok_turn_available is True


def test_inactive_hosted_active_byok(
    service: EntitlementService,
    sojourner_id: UUID,
) -> None:
    """AC 36: inactive hosted + active BYOK → hosted=False, byok=True."""
    activate_hosted(service, sojourner_id)
    grant_subscription_credits(service, sojourner_id, "100")
    deactivate_hosted(service, sojourner_id)
    activate_byok(service, sojourner_id)

    status = service.get_access_path_status(sojourner_id)
    assert status.hosted_turn_available is False
    assert status.byok_turn_available is True


def test_exhausted_hosted_active_byok(
    service: EntitlementService,
    sojourner_id: UUID,
) -> None:
    """AC 37: exhausted hosted + active BYOK → hosted=False, byok=True."""
    activate_hosted(service, sojourner_id)
    activate_byok(service, sojourner_id)
    # No credits granted.

    status = service.get_access_path_status(sojourner_id)
    assert status.hosted_turn_available is False
    assert status.hosted_unavailable_reason == HostedUnavailableReason.CREDITS_EXHAUSTED
    assert status.byok_turn_available is True


def test_reactivation_hosted_available_after_deactivate_reactivate(
    service: EntitlementService,
    sojourner_id: UUID,
    session: Session,
) -> None:
    """AC 38: hosted deactivated → reactivated → hosted_turn_available=True."""
    from sqlalchemy import select

    from afterworlds.entitlement.orm import EntitlementEvent
    from afterworlds.entitlement.replay import rebuild_entitlement_state

    activate_hosted(service, sojourner_id)
    grant_subscription_credits(service, sojourner_id, "100")
    deactivate_hosted(service, sojourner_id)
    activate_hosted(service, sojourner_id)

    status = service.get_access_path_status(sojourner_id)
    assert status.hosted_turn_available is True

    # Verify replay matches.
    events = list(
        session.scalars(
            select(EntitlementEvent).where(
                EntitlementEvent.sojourner_id == sojourner_id
            )
        ).all()
    )
    snapshot = rebuild_entitlement_state(sojourner_id, events)
    assert snapshot.hosted_access_active is True


def test_reactivation_cloud_services(
    service: EntitlementService,
    sojourner_id: UUID,
) -> None:
    """AC 39: Cloud Services lapsed → reactivated with new expires_at → active=True."""
    activate_cloud_services(service, sojourner_id, expires_at=_FIXED_FUTURE)
    lapse_cloud_services(service, sojourner_id)

    status_lapsed = service.get_access_path_status(sojourner_id)
    assert status_lapsed.cloud_services_active is False
    assert status_lapsed.cloud_services_lapsed is True

    activate_cloud_services(service, sojourner_id, expires_at=_FIXED_FUTURE)

    status_active = service.get_access_path_status(sojourner_id)
    assert status_active.cloud_services_active is True
    assert status_active.cloud_services_lapsed is False


# ---------------------------------------------------------------------------
# Datetime normalization regression — P2 fix
# ---------------------------------------------------------------------------


def test_service_aware_clock_naive_stored_expiry_active(
    session: Session,
    sojourner_id: UUID,
) -> None:
    """Aware injected clock vs naive stored expiry: no TypeError; reports active."""

    def aware_clock() -> datetime:
        return _FIXED_NOW.replace(tzinfo=UTC)

    svc = EntitlementService(session=session, clock=aware_clock)
    activate_cloud_services(svc, sojourner_id, expires_at=_FIXED_FUTURE)

    status = svc.get_access_path_status(sojourner_id)
    assert status.cloud_services_active is True
    assert status.cloud_services_lapsed is False


def test_service_aware_clock_naive_stored_expiry_expired(
    session: Session,
    sojourner_id: UUID,
) -> None:
    """Aware injected clock vs naive expired stored expiry: reports inactive."""

    def aware_clock() -> datetime:
        return _FIXED_NOW.replace(tzinfo=UTC)

    svc = EntitlementService(session=session, clock=aware_clock)
    activate_cloud_services(svc, sojourner_id, expires_at=_FIXED_PAST)

    status = svc.get_access_path_status(sojourner_id)
    assert status.cloud_services_active is False
    assert status.cloud_services_lapsed is True
