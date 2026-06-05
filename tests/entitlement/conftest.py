"""Shared fixtures for entitlement tests."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

import afterworlds.entitlement.orm  # noqa: F401 — registers ORM models with Base
from afterworlds.entitlement.enums import (
    EntitlementEventType,
    HostedAccessDeactivationReason,
    HostedAccessPlan,
    ModelTier,
    PipelinePassId,
)
from afterworlds.entitlement.models import PassUsageSnapshot, TurnCostPolicyConfig
from afterworlds.entitlement.payloads import (
    ByokLicenseActivatedPayload,
    CloudServicesActivatedPayload,
    CloudServicesLapsedPayload,
    HostedAccessActivatedPayload,
    HostedAccessDeactivatedPayload,
    SubscriptionCreditGrantPayload,
    TopUpCreditGrantPayload,
)
from afterworlds.entitlement.policy import TurnCostPolicy
from afterworlds.entitlement.service import EntitlementService
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.persistence.orm.base import Base

_FIXED_NOW = datetime(2026, 6, 5, 12, 0, 0)
_FIXED_FUTURE = datetime(2027, 1, 1, 0, 0, 0)
_FIXED_PAST = datetime(2025, 1, 1, 0, 0, 0)


@pytest.fixture()
def engine():  # type: ignore[no-untyped-def]
    """In-memory SQLite engine with all tables and append-only triggers."""
    eng = create_engine("sqlite://")
    Base.metadata.create_all(eng)
    with eng.begin() as conn:
        conn.execute(
            text(
                "CREATE TRIGGER prevent_entitlement_event_update "
                "BEFORE UPDATE ON entitlement_event BEGIN "
                "SELECT RAISE(ABORT, 'entitlement_event is append-only:"
                " UPDATE is forbidden'); END"
            )
        )
        conn.execute(
            text(
                "CREATE TRIGGER prevent_entitlement_event_delete "
                "BEFORE DELETE ON entitlement_event BEGIN "
                "SELECT RAISE(ABORT, 'entitlement_event is append-only:"
                " DELETE is forbidden'); END"
            )
        )
    yield eng
    Base.metadata.drop_all(eng)
    eng.dispose()


@pytest.fixture()
def session(engine):  # type: ignore[no-untyped-def]
    """SQLAlchemy session bound to the in-memory engine."""
    factory = create_session_factory(engine)
    sess = factory()
    try:
        yield sess
    finally:
        sess.close()


@pytest.fixture()
def fixed_clock() -> Callable[[], datetime]:
    return lambda: _FIXED_NOW


@pytest.fixture()
def service(
    session: Session, fixed_clock: Callable[[], datetime]
) -> EntitlementService:
    return EntitlementService(session=session, clock=fixed_clock)


@pytest.fixture()
def sojourner_id() -> UUID:
    return uuid4()


def activate_hosted(
    service: EntitlementService,
    sojourner_id: UUID,
    plan: HostedAccessPlan = HostedAccessPlan.SUBSCRIPTION,
) -> None:
    service.receive_entitlement_event(
        sojourner_id,
        EntitlementEventType.HOSTED_ACCESS_ACTIVATED,
        HostedAccessActivatedPayload(plan=plan, effective_at=_FIXED_NOW),
    )


def grant_subscription_credits(
    service: EntitlementService,
    sojourner_id: UUID,
    amount: str = "100",
) -> None:
    from decimal import Decimal

    service.receive_entitlement_event(
        sojourner_id,
        EntitlementEventType.SUBSCRIPTION_CREDIT_GRANT,
        SubscriptionCreditGrantPayload(hosted_credit_delta=Decimal(amount)),
    )


def grant_top_up_credits(
    service: EntitlementService,
    sojourner_id: UUID,
    amount: str = "50",
) -> None:
    from decimal import Decimal

    service.receive_entitlement_event(
        sojourner_id,
        EntitlementEventType.TOP_UP_CREDIT_GRANT,
        TopUpCreditGrantPayload(top_up_credit_delta=Decimal(amount)),
    )


def activate_byok(
    service: EntitlementService,
    sojourner_id: UUID,
) -> None:
    service.receive_entitlement_event(
        sojourner_id,
        EntitlementEventType.BYOK_LICENSE_ACTIVATED,
        ByokLicenseActivatedPayload(purchased_at=_FIXED_NOW),
    )


def activate_cloud_services(
    service: EntitlementService,
    sojourner_id: UUID,
    expires_at: datetime = _FIXED_FUTURE,
) -> None:
    service.receive_entitlement_event(
        sojourner_id,
        EntitlementEventType.CLOUD_SERVICES_ACTIVATED,
        CloudServicesActivatedPayload(expires_at=expires_at),
    )


def lapse_cloud_services(
    service: EntitlementService,
    sojourner_id: UUID,
) -> None:
    from afterworlds.entitlement.enums import CloudServicesDeactivationReason

    service.receive_entitlement_event(
        sojourner_id,
        EntitlementEventType.CLOUD_SERVICES_LAPSED,
        CloudServicesLapsedPayload(
            effective_at=_FIXED_NOW,
            reason=CloudServicesDeactivationReason.NON_RENEWAL,
        ),
    )


def deactivate_hosted(
    service: EntitlementService,
    sojourner_id: UUID,
) -> None:
    service.receive_entitlement_event(
        sojourner_id,
        EntitlementEventType.HOSTED_ACCESS_DEACTIVATED,
        HostedAccessDeactivatedPayload(
            effective_at=_FIXED_NOW,
            reason=HostedAccessDeactivationReason.SUBSCRIPTION_CANCELLED,
        ),
    )


def make_pass_snapshot(
    pass_id: PipelinePassId = PipelinePassId.WRITER,
    model_tier: ModelTier = ModelTier.SONNET,
    input_tokens: int = 1000,
    output_tokens: int = 500,
) -> PassUsageSnapshot:
    return PassUsageSnapshot(
        pass_id=pass_id,
        model_tier=model_tier,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )


def make_policy(tokens_per_credit: str = "1000") -> TurnCostPolicy:
    from decimal import Decimal

    return TurnCostPolicy(
        config=TurnCostPolicyConfig(tokens_per_credit=Decimal(tokens_per_credit))
    )
