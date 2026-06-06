"""Pure replay function for entitlement state — CRD Issue 13.

``rebuild_entitlement_state`` is a pure function: no DB reads, no clock, no side
effects.  It orders events by ``global_sequence`` ascending and applies the event
application rules from the spec table to produce an ``EntitlementStateSnapshot``.

This function is the audit and correctness anchor for the event-sourced design:
replay of the ordered event log must reconstruct current state identically to the
live ``RuntimeEntitlementState`` projection, without consulting that projection row.

``effective_at`` fields in payloads are business timestamps; they do not affect
replay order.  Replay order is ``global_sequence`` ascending.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from decimal import Decimal
from uuid import UUID

from afterworlds.entitlement.enums import EntitlementEventType
from afterworlds.entitlement.errors import (
    EntitlementPayloadVersionError,
    EntitlementReplayError,
)
from afterworlds.entitlement.models import EntitlementStateSnapshot
from afterworlds.entitlement.orm import EntitlementEvent
from afterworlds.entitlement.payloads import (
    ENTITLEMENT_PAYLOAD_CLASS_MAP,
    ByokLicenseActivatedPayload,
    CloudServicesActivatedPayload,
    CloudServicesLapsedPayload,
    CreditDeductionPayload,
    HostedAccessActivatedPayload,
    HostedAccessDeactivatedPayload,
    ManualCreditAdjustmentPayload,
    SubscriptionCreditGrantPayload,
    TopUpCreditGrantPayload,
)


def rebuild_entitlement_state(
    sojourner_id: UUID,
    events: Iterable[EntitlementEvent],
) -> EntitlementStateSnapshot:
    """Reconstruct entitlement state from an ordered event log.

    Pure function.  No DB reads.  No clock.  No side effects.

    Orders events by ``global_sequence`` ascending.  Deserializes each payload
    via ``ENTITLEMENT_PAYLOAD_CLASS_MAP`` and ``model_validate_json``.  Applies
    event application rules from the spec table.

    ``None`` deltas in ``ManualCreditAdjustmentPayload`` are treated as
    ``Decimal("0")``.

    Raises ``EntitlementPayloadVersionError(event_id, event_type, seen_version)``
    for unsupported ``schema_version``.
    Raises ``EntitlementReplayError(global_sequence)`` for unrecognized
    ``event_type``.
    """
    snapshot = EntitlementStateSnapshot(sojourner_id=sojourner_id)

    sorted_events = sorted(
        (e for e in events if e.sojourner_id == sojourner_id),
        key=lambda e: e.global_sequence,
    )

    for event in sorted_events:
        _apply_event_to_snapshot(snapshot, event)

    return snapshot


def _apply_event_to_snapshot(
    snapshot: EntitlementStateSnapshot,
    event: EntitlementEvent,
) -> None:
    # Convert raw str to enum; raises EntitlementReplayError for unknown types.
    try:
        event_type = EntitlementEventType(event.event_type)
    except ValueError:
        raise EntitlementReplayError(
            f"Unrecognized event_type at global_sequence={event.global_sequence}: "
            f"{event.event_type!r}"
        ) from None

    payload_class = ENTITLEMENT_PAYLOAD_CLASS_MAP.get(event_type)
    if payload_class is None:
        raise EntitlementReplayError(
            f"Unhandled event_type at global_sequence={event.global_sequence}: "
            f"{event_type!r}"
        )

    # Pre-check schema_version before calling model_validate_json so we can
    # distinguish unsupported version from malformed data.
    raw = json.loads(event.payload_json)
    seen_version = raw.get("schema_version")
    if seen_version != 1:
        raise EntitlementPayloadVersionError(
            f"Unsupported schema_version {seen_version!r} for event_id="
            f"{event.event_id} event_type={event.event_type!r}"
        )

    payload = payload_class.model_validate_json(event.payload_json)

    if event_type == EntitlementEventType.HOSTED_ACCESS_ACTIVATED:
        assert isinstance(payload, HostedAccessActivatedPayload)
        snapshot.hosted_access_active = True
        snapshot.hosted_access_plan = payload.plan

    elif event_type == EntitlementEventType.HOSTED_ACCESS_DEACTIVATED:
        assert isinstance(payload, HostedAccessDeactivatedPayload)
        snapshot.hosted_access_active = False
        # hosted_access_plan is intentionally preserved — distinguishes
        # SUBSCRIPTION_INACTIVE from NO_SUBSCRIPTION.

    elif event_type == EntitlementEventType.SUBSCRIPTION_CREDIT_GRANT:
        assert isinstance(payload, SubscriptionCreditGrantPayload)
        snapshot.hosted_credit_balance += payload.hosted_credit_delta

    elif event_type == EntitlementEventType.TOP_UP_CREDIT_GRANT:
        assert isinstance(payload, TopUpCreditGrantPayload)
        snapshot.top_up_credit_balance += payload.top_up_credit_delta

    elif event_type == EntitlementEventType.CREDIT_DEDUCTION:
        assert isinstance(payload, CreditDeductionPayload)
        snapshot.hosted_credit_balance += payload.hosted_credit_delta
        snapshot.top_up_credit_balance += payload.top_up_credit_delta

    elif event_type == EntitlementEventType.BYOK_LICENSE_ACTIVATED:
        assert isinstance(payload, ByokLicenseActivatedPayload)
        snapshot.byok_license_active = True
        snapshot.byok_license_purchased_at = payload.purchased_at

    elif event_type == EntitlementEventType.CLOUD_SERVICES_ACTIVATED:
        assert isinstance(payload, CloudServicesActivatedPayload)
        snapshot.cloud_services_active = True
        snapshot.cloud_services_expires_at = payload.expires_at

    elif event_type == EntitlementEventType.CLOUD_SERVICES_LAPSED:
        assert isinstance(payload, CloudServicesLapsedPayload)
        snapshot.cloud_services_active = False

    elif event_type == EntitlementEventType.MANUAL_CREDIT_ADJUSTMENT:
        assert isinstance(payload, ManualCreditAdjustmentPayload)
        hd = payload.hosted_credit_delta or Decimal("0")
        td = payload.top_up_credit_delta or Decimal("0")
        snapshot.hosted_credit_balance += hd
        snapshot.top_up_credit_balance += td

    else:
        raise EntitlementReplayError(
            f"Unhandled event_type at global_sequence={event.global_sequence}: "
            f"{event_type!r}"
        )
