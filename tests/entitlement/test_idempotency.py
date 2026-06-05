"""Idempotency tests — AC 48–50."""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import patch
from uuid import UUID

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from afterworlds.entitlement.enums import EntitlementEventType
from afterworlds.entitlement.errors import (
    EntitlementIdempotencyConflictError,
)
from afterworlds.entitlement.payloads import SubscriptionCreditGrantPayload
from afterworlds.entitlement.service import EntitlementService
from tests.entitlement.conftest import activate_hosted

# ---------------------------------------------------------------------------
# AC 48: same idempotency_key + matching fields → return existing; no re-apply
# ---------------------------------------------------------------------------


def test_idempotent_grant_returns_existing_event(
    service: EntitlementService,
    sojourner_id: UUID,
    session: Session,
) -> None:
    """AC 48: same idempotency_key + matching payload → existing event returned."""
    activate_hosted(service, sojourner_id)

    payload = SubscriptionCreditGrantPayload(hosted_credit_delta=Decimal("50"))

    event1 = service.receive_entitlement_event(
        sojourner_id,
        EntitlementEventType.SUBSCRIPTION_CREDIT_GRANT,
        payload,
        idempotency_key="grant-001",
    )
    event2 = service.receive_entitlement_event(
        sojourner_id,
        EntitlementEventType.SUBSCRIPTION_CREDIT_GRANT,
        payload,
        idempotency_key="grant-001",
    )

    assert event1.event_id == event2.event_id

    # State must NOT be double-applied.
    from afterworlds.entitlement.orm import RuntimeEntitlementState

    session.expire_all()
    state = session.get(RuntimeEntitlementState, sojourner_id)
    assert state is not None
    assert state.hosted_credit_balance == Decimal("50")


# ---------------------------------------------------------------------------
# AC 49: same idempotency_key + field mismatch → EntitlementIdempotencyConflictError
# ---------------------------------------------------------------------------


def test_idempotency_conflict_different_payload(
    service: EntitlementService,
    sojourner_id: UUID,
) -> None:
    """AC 49: same key + different amount → EntitlementIdempotencyConflictError."""
    activate_hosted(service, sojourner_id)

    service.receive_entitlement_event(
        sojourner_id,
        EntitlementEventType.SUBSCRIPTION_CREDIT_GRANT,
        SubscriptionCreditGrantPayload(hosted_credit_delta=Decimal("50")),
        idempotency_key="grant-conflict",
    )
    with pytest.raises(EntitlementIdempotencyConflictError):
        service.receive_entitlement_event(
            sojourner_id,
            EntitlementEventType.SUBSCRIPTION_CREDIT_GRANT,
            SubscriptionCreditGrantPayload(hosted_credit_delta=Decimal("999")),
            idempotency_key="grant-conflict",
        )


def test_idempotency_conflict_different_event_type(
    service: EntitlementService,
    sojourner_id: UUID,
) -> None:
    """AC 49: same key + different event_type → EntitlementIdempotencyConflictError."""
    from afterworlds.entitlement.payloads import TopUpCreditGrantPayload

    activate_hosted(service, sojourner_id)

    service.receive_entitlement_event(
        sojourner_id,
        EntitlementEventType.SUBSCRIPTION_CREDIT_GRANT,
        SubscriptionCreditGrantPayload(hosted_credit_delta=Decimal("50")),
        idempotency_key="key-type-conflict",
    )
    with pytest.raises(EntitlementIdempotencyConflictError):
        service.receive_entitlement_event(
            sojourner_id,
            EntitlementEventType.TOP_UP_CREDIT_GRANT,
            TopUpCreditGrantPayload(top_up_credit_delta=Decimal("50")),
            idempotency_key="key-type-conflict",
        )


# ---------------------------------------------------------------------------
# AC 50: race-safe test — simulate IntegrityError; service refetches without
#        double-mutation.
# ---------------------------------------------------------------------------


def test_race_safe_integrity_error_returns_existing(
    service: EntitlementService,
    sojourner_id: UUID,
    session: Session,
) -> None:
    """AC 50: simulate IntegrityError; service refetches existing and returns it."""
    activate_hosted(service, sojourner_id)

    # First successful insert.
    payload = SubscriptionCreditGrantPayload(hosted_credit_delta=Decimal("75"))
    event1 = service.receive_entitlement_event(
        sojourner_id,
        EntitlementEventType.SUBSCRIPTION_CREDIT_GRANT,
        payload,
        idempotency_key="race-key-001",
    )

    # Simulate a concurrent insert by patching session.commit to raise
    # IntegrityError on the first call after the competing insert is in place.
    from afterworlds.entitlement.orm import RuntimeEntitlementState

    original_commit = session.commit

    call_count = [0]

    def patched_commit() -> None:
        call_count[0] += 1
        if call_count[0] == 1:
            raise IntegrityError("unique constraint", {}, Exception())
        return original_commit()

    with patch.object(session, "commit", side_effect=patched_commit):
        # The service catches the IntegrityError, rolls back, refetches by
        # idempotency_key, and returns the existing event.
        event2 = service.receive_entitlement_event(
            sojourner_id,
            EntitlementEventType.SUBSCRIPTION_CREDIT_GRANT,
            payload,
            idempotency_key="race-key-001",
        )

    assert event2.event_id == event1.event_id

    # Balance must still be 75, not 150 (no double-apply).
    session.expire_all()
    state = session.get(RuntimeEntitlementState, sojourner_id)
    assert state is not None
    assert state.hosted_credit_balance == Decimal("75")
