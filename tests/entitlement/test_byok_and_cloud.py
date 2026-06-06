"""BYOK activation and Cloud Services gate tests — AC 60–62."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import pytest
from sqlalchemy.orm import Session

from afterworlds.entitlement.enums import CloudServiceOperation
from afterworlds.entitlement.errors import CloudServicesLapsedError
from afterworlds.entitlement.gate import CloudServicesGate
from afterworlds.entitlement.orm import RuntimeEntitlementState
from afterworlds.entitlement.service import EntitlementService
from tests.entitlement.conftest import (
    _FIXED_FUTURE,
    _FIXED_NOW,
    _FIXED_PAST,
    activate_byok,
    activate_cloud_services,
    activate_hosted,
    grant_subscription_credits,
)

# ---------------------------------------------------------------------------
# AC 60: BYOK_LICENSE_ACTIVATED sets byok_license_purchased_at
# ---------------------------------------------------------------------------


def test_byok_license_activated_sets_purchased_at(
    service: EntitlementService,
    sojourner_id: UUID,
    session: Session,
) -> None:
    """AC 60: BYOK_LICENSE_ACTIVATED sets byok_license_purchased_at."""
    activate_byok(service, sojourner_id)

    session.expire_all()
    state = session.get(RuntimeEntitlementState, sojourner_id)
    assert state is not None
    assert state.byok_license_active is True
    assert state.byok_license_purchased_at == _FIXED_NOW


def test_byok_replay_reflects_purchased_at(
    service: EntitlementService,
    sojourner_id: UUID,
    session: Session,
) -> None:
    """AC 60: replay of BYOK_LICENSE_ACTIVATED reflects purchased_at correctly."""
    from sqlalchemy import select

    from afterworlds.entitlement.orm import EntitlementEvent
    from afterworlds.entitlement.replay import rebuild_entitlement_state

    activate_byok(service, sojourner_id)

    events = list(
        session.scalars(
            select(EntitlementEvent).where(
                EntitlementEvent.sojourner_id == sojourner_id
            )
        ).all()
    )
    snapshot = rebuild_entitlement_state(sojourner_id, events)
    assert snapshot.byok_license_active is True
    assert snapshot.byok_license_purchased_at == _FIXED_NOW


# ---------------------------------------------------------------------------
# AC 61: CloudServicesGate raises/passes correctly
# ---------------------------------------------------------------------------


def test_cloud_services_gate_raises_for_lapsed(
    session: Session,
    sojourner_id: UUID,
) -> None:
    """AC 61: require_cloud_services raises CloudServicesLapsedError when lapsed."""
    gate = CloudServicesGate(session=session, clock=lambda: _FIXED_NOW)

    with pytest.raises(CloudServicesLapsedError):
        gate.require_cloud_services(sojourner_id, CloudServiceOperation.SYNC)


def test_cloud_services_gate_raises_for_expired(
    service: EntitlementService,
    session: Session,
    sojourner_id: UUID,
) -> None:
    """AC 61: require_cloud_services raises for expired expires_at."""
    activate_cloud_services(service, sojourner_id, expires_at=_FIXED_PAST)

    gate = CloudServicesGate(session=session, clock=lambda: _FIXED_NOW)
    with pytest.raises(CloudServicesLapsedError):
        gate.require_cloud_services(sojourner_id, CloudServiceOperation.BACKUP)


def test_cloud_services_gate_does_not_raise_for_active(
    service: EntitlementService,
    session: Session,
    sojourner_id: UUID,
) -> None:
    """AC 61: require_cloud_services does not raise when active + non-expired."""
    activate_cloud_services(service, sojourner_id, expires_at=_FIXED_FUTURE)

    gate = CloudServicesGate(session=session, clock=lambda: _FIXED_NOW)
    gate.require_cloud_services(
        sojourner_id, CloudServiceOperation.HOSTED_STORAGE_WRITE
    )


def test_cloud_services_gate_raises_for_none_expires_at(
    service: EntitlementService,
    session: Session,
    sojourner_id: UUID,
) -> None:
    """AC 61: require_cloud_services raises for expires_at=None."""
    activate_byok(service, sojourner_id)

    # Force cloud_services_active=True with expires_at=None.
    state = session.get(RuntimeEntitlementState, sojourner_id)
    assert state is not None
    state.cloud_services_active = True
    state.cloud_services_expires_at = None
    session.commit()

    gate = CloudServicesGate(session=session, clock=lambda: _FIXED_NOW)
    with pytest.raises(CloudServicesLapsedError):
        gate.require_cloud_services(sojourner_id, CloudServiceOperation.REMOTE_ACCESS)


# ---------------------------------------------------------------------------
# AC 62: CloudServicesGate independence — must not inspect hosted state
# ---------------------------------------------------------------------------


def test_cloud_services_gate_independent_of_hosted_subscription(
    service: EntitlementService,
    session: Session,
    sojourner_id: UUID,
) -> None:
    """AC 62: Sojourner with active hosted subscription but no CLOUD_SERVICES_ACTIVATED
    event has cloud_services_active=False; gate raises CloudServicesLapsedError.
    The gate must not inspect hosted_access_active or hosted_access_plan.
    """
    activate_hosted(service, sojourner_id)
    grant_subscription_credits(service, sojourner_id, "100")
    # No CLOUD_SERVICES_ACTIVATED event issued.

    status = service.get_access_path_status(sojourner_id)
    assert status.cloud_services_active is False

    gate = CloudServicesGate(session=session, clock=lambda: _FIXED_NOW)
    with pytest.raises(CloudServicesLapsedError):
        gate.require_cloud_services(sojourner_id, CloudServiceOperation.SYNC)


# ---------------------------------------------------------------------------
# Datetime normalization regression — P2 fix
# ---------------------------------------------------------------------------


def test_gate_aware_clock_naive_stored_expiry_active(
    service: EntitlementService,
    session: Session,
    sojourner_id: UUID,
) -> None:
    """Aware injected clock vs naive stored expiry: no TypeError; gate passes."""
    activate_cloud_services(service, sojourner_id, expires_at=_FIXED_FUTURE)

    aware_now = _FIXED_NOW.replace(tzinfo=UTC)
    gate = CloudServicesGate(session=session, clock=lambda: aware_now)
    gate.require_cloud_services(sojourner_id, CloudServiceOperation.SYNC)


def test_gate_aware_clock_naive_stored_expiry_expired_raises(
    service: EntitlementService,
    session: Session,
    sojourner_id: UUID,
) -> None:
    """Aware injected clock vs naive expired stored expiry: gate raises."""
    activate_cloud_services(service, sojourner_id, expires_at=_FIXED_PAST)

    aware_now = _FIXED_NOW.replace(tzinfo=UTC)
    gate = CloudServicesGate(session=session, clock=lambda: aware_now)
    with pytest.raises(CloudServicesLapsedError):
        gate.require_cloud_services(sojourner_id, CloudServiceOperation.SYNC)


def test_gate_effective_aware_expiry_aware_clock_active() -> None:
    """_cloud_services_effective: aware expiry + aware clock → True (no TypeError)."""
    from types import SimpleNamespace

    state = SimpleNamespace(
        cloud_services_active=True,
        cloud_services_expires_at=datetime(2027, 1, 1, tzinfo=UTC),
    )
    aware_now = datetime(2026, 6, 5, 12, 0, 0, tzinfo=UTC)
    assert CloudServicesGate._cloud_services_effective(state, aware_now) is True  # type: ignore[arg-type]


def test_gate_effective_aware_expiry_expired() -> None:
    """_cloud_services_effective: aware expired expiry + aware clock → False."""
    from types import SimpleNamespace

    state = SimpleNamespace(
        cloud_services_active=True,
        cloud_services_expires_at=datetime(2025, 1, 1, tzinfo=UTC),
    )
    aware_now = datetime(2026, 6, 5, 12, 0, 0, tzinfo=UTC)
    assert CloudServicesGate._cloud_services_effective(state, aware_now) is False  # type: ignore[arg-type]
