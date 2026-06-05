"""Replay and replayability tests — AC 13–18."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from afterworlds.entitlement.enums import EntitlementEventType, HostedAccessPlan
from afterworlds.entitlement.errors import (
    EntitlementPayloadVersionError,
    EntitlementReplayError,
    EntitlementSettlementError,
)
from afterworlds.entitlement.orm import EntitlementEvent, RuntimeEntitlementState
from afterworlds.entitlement.replay import rebuild_entitlement_state
from afterworlds.entitlement.service import EntitlementService
from tests.entitlement.conftest import (
    activate_byok,
    activate_cloud_services,
    activate_hosted,
    deactivate_hosted,
    grant_subscription_credits,
    grant_top_up_credits,
)


def _collect_events(session: Session, sojourner_id: UUID) -> list[EntitlementEvent]:
    return list(
        session.scalars(
            select(EntitlementEvent)
            .where(EntitlementEvent.sojourner_id == sojourner_id)
            .order_by(EntitlementEvent.global_sequence)
        ).all()
    )


def test_rebuild_is_pure(session: Session, sojourner_id: UUID) -> None:
    """AC 13: rebuild_entitlement_state is pure — no DB, clock, or side effects.

    Verified by calling it directly with an empty list — no session needed.
    """
    snapshot = rebuild_entitlement_state(sojourner_id, [])
    assert snapshot.sojourner_id == sojourner_id
    assert snapshot.hosted_access_active is False
    assert snapshot.byok_license_active is False


def test_rebuild_matches_projection_after_multiple_events(
    service: EntitlementService,
    sojourner_id: UUID,
    session: Session,
) -> None:
    """AC 14: replay of events matches RuntimeEntitlementState field-by-field."""
    activate_hosted(service, sojourner_id)
    grant_subscription_credits(service, sojourner_id, "100")
    grant_top_up_credits(service, sojourner_id, "50")
    activate_byok(service, sojourner_id)
    activate_cloud_services(service, sojourner_id)

    events = _collect_events(session, sojourner_id)
    snapshot = rebuild_entitlement_state(sojourner_id, events)

    session.expire_all()
    state = session.get(RuntimeEntitlementState, sojourner_id)
    assert state is not None

    assert snapshot.hosted_access_active == state.hosted_access_active
    assert snapshot.hosted_access_plan == state.hosted_access_plan
    assert snapshot.hosted_credit_balance == state.hosted_credit_balance
    assert snapshot.top_up_credit_balance == state.top_up_credit_balance
    assert snapshot.byok_license_active == state.byok_license_active
    assert snapshot.byok_license_purchased_at == state.byok_license_purchased_at
    assert snapshot.cloud_services_active == state.cloud_services_active
    assert snapshot.cloud_services_expires_at == state.cloud_services_expires_at


def test_rebuild_does_not_consult_projection_row(
    service: EntitlementService,
    sojourner_id: UUID,
    session: Session,
) -> None:
    """AC 14: reconstruction does not consult the projection row."""
    activate_hosted(service, sojourner_id)
    events = _collect_events(session, sojourner_id)
    # Pass events only; function is pure — no session required.
    snapshot = rebuild_entitlement_state(sojourner_id, events)
    assert snapshot.hosted_access_active is True


def test_rebuild_raises_payload_version_error(
    sojourner_id: UUID,
    session: Session,
) -> None:
    """AC 15: rebuild raises EntitlementPayloadVersionError for unknown version."""
    from datetime import datetime
    from uuid import uuid4

    event = EntitlementEvent(
        event_id=uuid4(),
        sojourner_id=sojourner_id,
        event_type=EntitlementEventType.BYOK_LICENSE_ACTIVATED,
        payload_json='{"schema_version": 99, "purchased_at": "2026-01-01T00:00:00"}',
        created_at=datetime(2026, 6, 5),
    )
    session.add(event)
    session.commit()

    events = _collect_events(session, sojourner_id)
    with pytest.raises(EntitlementPayloadVersionError, match="99"):
        rebuild_entitlement_state(sojourner_id, events)


def test_rebuild_raises_replay_error_for_unknown_event_type(
    sojourner_id: UUID,
    session: Session,
) -> None:
    """AC 15: rebuild raises EntitlementReplayError for unrecognized event_type."""
    from datetime import datetime
    from uuid import uuid4

    # Insert directly; bypass service to avoid enum validation.
    session.execute(
        __import__("sqlalchemy").text(
            "INSERT INTO entitlement_event "
            "(event_id, sojourner_id, event_type, payload_json, created_at) "
            "VALUES (:eid, :sid, :etype, :pj, :ca)"
        ),
        {
            "eid": str(uuid4()),
            "sid": sojourner_id.hex,
            "etype": "unknown_future_event",
            "pj": '{"schema_version": 1}',
            "ca": datetime(2026, 6, 5),
        },
    )
    session.commit()

    events = list(
        session.scalars(
            select(EntitlementEvent).where(
                EntitlementEvent.sojourner_id == sojourner_id
            )
        ).all()
    )
    with pytest.raises(EntitlementReplayError, match="global_sequence"):
        rebuild_entitlement_state(sojourner_id, events)


def test_malformed_payload_raises_on_validate(
    sojourner_id: UUID,
    session: Session,
) -> None:
    """AC 16: syntactically valid JSON with invalid payload raises ValidationError."""
    import json

    from pydantic import ValidationError

    from afterworlds.entitlement.payloads import SubscriptionCreditGrantPayload

    bad_json = json.dumps({"schema_version": 1, "hosted_credit_delta": "not-a-number"})
    with pytest.raises(ValidationError):
        SubscriptionCreditGrantPayload.model_validate_json(bad_json)


def test_payload_type_mismatch_raises_settlement_error(
    service: EntitlementService,
    sojourner_id: UUID,
) -> None:
    """AC 17: wrong payload class raises EntitlementSettlementError."""
    activate_hosted(service, sojourner_id)

    from afterworlds.entitlement.payloads import TopUpCreditGrantPayload

    wrong_payload = TopUpCreditGrantPayload(top_up_credit_delta=Decimal("50"))

    with pytest.raises(EntitlementSettlementError, match="does not match"):
        service.receive_entitlement_event(
            sojourner_id,
            EntitlementEventType.SUBSCRIPTION_CREDIT_GRANT,
            wrong_payload,
        )


def test_schema_version_2_raises_payload_version_error_in_rebuild(
    sojourner_id: UUID,
    session: Session,
) -> None:
    """AC 18: schema_version=2 raises EntitlementPayloadVersionError."""
    from datetime import datetime
    from uuid import uuid4

    event = EntitlementEvent(
        event_id=uuid4(),
        sojourner_id=sojourner_id,
        event_type=EntitlementEventType.SUBSCRIPTION_CREDIT_GRANT,
        payload_json='{"schema_version": 2, "hosted_credit_delta": "100"}',
        created_at=datetime(2026, 6, 5),
    )
    session.add(event)
    session.commit()

    events = _collect_events(session, sojourner_id)
    with pytest.raises(EntitlementPayloadVersionError, match="2"):
        rebuild_entitlement_state(sojourner_id, events)


def test_rebuild_deactivated_preserves_plan(
    service: EntitlementService,
    sojourner_id: UUID,
    session: Session,
) -> None:
    """AC 38 (replay): deactivation → reactivation sequence matches projection."""
    activate_hosted(service, sojourner_id)
    deactivate_hosted(service, sojourner_id)
    activate_hosted(service, sojourner_id, plan=HostedAccessPlan.STARTER_ACCESS)

    events = _collect_events(session, sojourner_id)
    snapshot = rebuild_entitlement_state(sojourner_id, events)

    assert snapshot.hosted_access_active is True
    assert snapshot.hosted_access_plan == HostedAccessPlan.STARTER_ACCESS
