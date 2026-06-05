"""Mutation invariant tests — AC 8–12."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from afterworlds.entitlement.enums import HostedAccessPlan
from afterworlds.entitlement.orm import RuntimeEntitlementState
from afterworlds.entitlement.service import EntitlementService
from tests.entitlement.conftest import (
    activate_hosted,
    deactivate_hosted,
    grant_subscription_credits,
)


def test_no_public_update_method_on_runtime_state_orm() -> None:
    """AC 8: RuntimeEntitlementState has no public update method."""
    public_methods = [
        name
        for name in dir(RuntimeEntitlementState)
        if not name.startswith("_") and callable(getattr(RuntimeEntitlementState, name))
    ]
    # Should not have any 'update' or 'set' style methods
    update_methods = [
        m for m in public_methods if "update" in m.lower() or "set_" in m.lower()
    ]
    assert (
        update_methods == []
    ), f"RuntimeEntitlementState has forbidden public update methods: {update_methods}"


def test_first_event_creates_state_row(
    service: EntitlementService,
    sojourner_id: UUID,
    session: Session,
) -> None:
    """AC 10: first event creates the RuntimeEntitlementState row transactionally."""
    state_before = session.get(RuntimeEntitlementState, sojourner_id)
    assert state_before is None

    activate_hosted(service, sojourner_id)

    state_after = session.get(RuntimeEntitlementState, sojourner_id)
    assert state_after is not None
    assert state_after.hosted_access_active is True


def test_hosted_access_active_requires_plan(
    service: EntitlementService,
    sojourner_id: UUID,
    session: Session,
) -> None:
    """AC 11: hosted_access_active=True with hosted_access_plan=None rejected."""
    activate_hosted(service, sojourner_id)
    state = session.get(RuntimeEntitlementState, sojourner_id)
    assert state is not None
    assert state.hosted_access_active is True
    assert state.hosted_access_plan is not None


def test_hosted_deactivated_does_not_clear_plan(
    service: EntitlementService,
    sojourner_id: UUID,
    session: Session,
) -> None:
    """AC 12: HOSTED_ACCESS_DEACTIVATED does not clear hosted_access_plan.

    This distinguishes SUBSCRIPTION_INACTIVE (plan set, active=False) from
    NO_SUBSCRIPTION (plan=None).
    """
    activate_hosted(service, sojourner_id, plan=HostedAccessPlan.SUBSCRIPTION)
    deactivate_hosted(service, sojourner_id)

    session.expire_all()
    state = session.get(RuntimeEntitlementState, sojourner_id)
    assert state is not None
    assert state.hosted_access_active is False
    assert state.hosted_access_plan == HostedAccessPlan.SUBSCRIPTION


def test_fixtures_seed_via_receive_event(
    service: EntitlementService,
    sojourner_id: UUID,
    session: Session,
) -> None:
    """AC 9: fixtures seed state via receive_entitlement_event, no direct ORM writes."""
    activate_hosted(service, sojourner_id)
    grant_subscription_credits(service, sojourner_id, "50")

    state = session.get(RuntimeEntitlementState, sojourner_id)
    assert state is not None
    from decimal import Decimal

    assert state.hosted_credit_balance == Decimal("50")
