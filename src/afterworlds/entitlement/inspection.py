"""Read-only inspection of the entitlement ledger -- CRD Issue 13 owner reads
for CRD Issue 22 support.

Nothing here writes, repairs or rebuilds the projection: a replay mismatch or
an unreadable event is reported, never fixed (Required Behavior 2). Order is
``global_sequence`` ascending; ``created_at`` is display metadata only.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

import sqlalchemy as sa
from pydantic import BaseModel, ValidationError
from sqlalchemy.orm import Session

from afterworlds.entitlement.enums import EntitlementEventType, HostedAccessPlan
from afterworlds.entitlement.errors import (
    EntitlementPayloadVersionError,
    EntitlementReplayError,
)
from afterworlds.entitlement.orm import EntitlementEvent, RuntimeEntitlementState
from afterworlds.entitlement.payloads import ENTITLEMENT_PAYLOAD_CLASS_MAP
from afterworlds.entitlement.replay import rebuild_entitlement_state
from afterworlds.entitlement.time_utils import to_utc_naive


@dataclass(frozen=True)
class Projection:
    """The current projection row, copied out (read-only)."""

    hosted_access_active: bool
    hosted_access_plan: HostedAccessPlan | None
    hosted_credit_balance: Decimal
    top_up_credit_balance: Decimal
    byok_license_active: bool
    byok_license_purchased_at: datetime | None
    cloud_services_active: bool
    cloud_services_expires_at: datetime | None
    last_entitlement_event_id: UUID | None


def read_projection(session: Session, sojourner_id: UUID) -> Projection | None:
    row = session.get(RuntimeEntitlementState, sojourner_id)
    if row is None:
        return None
    return Projection(
        hosted_access_active=row.hosted_access_active,
        hosted_access_plan=row.hosted_access_plan,
        hosted_credit_balance=row.hosted_credit_balance,
        top_up_credit_balance=row.top_up_credit_balance,
        byok_license_active=row.byok_license_active,
        byok_license_purchased_at=row.byok_license_purchased_at,
        cloud_services_active=row.cloud_services_active,
        cloud_services_expires_at=row.cloud_services_expires_at,
        last_entitlement_event_id=row.last_entitlement_event_id,
    )


@dataclass(frozen=True)
class EventView:
    global_sequence: int
    event_id: UUID
    event_type: str
    created_at: datetime
    turn_id: UUID | None
    idempotency_key: str | None
    #: The parsed typed payload, or None with ``parse_error`` set.
    payload: BaseModel | None
    parse_error: str | None


def _parse(event: EntitlementEvent) -> tuple[BaseModel | None, str | None]:
    try:
        event_type = EntitlementEventType(event.event_type)
    except ValueError:
        return None, "unknown_event_type"
    try:
        raw = json.loads(event.payload_json)
    except ValueError:
        return None, "malformed_payload"
    if not isinstance(raw, dict) or raw.get("schema_version") != 1:
        return None, "unsupported_schema_version"
    try:
        return (
            ENTITLEMENT_PAYLOAD_CLASS_MAP[event_type].model_validate_json(
                event.payload_json
            ),
            None,
        )
    except ValidationError:
        return None, "malformed_payload"


@dataclass(frozen=True)
class EventPage:
    events: tuple[EventView, ...]
    total_events: int
    next_after_sequence: int | None


def list_events(
    session: Session, sojourner_id: UUID, *, after_sequence: int, limit: int
) -> EventPage:
    """One page in replay order strictly after *after_sequence*; the cursor is
    the last sequence returned, so pages never skip or repeat an event."""
    rows = list(
        session.scalars(
            sa.select(EntitlementEvent)
            .where(
                EntitlementEvent.sojourner_id == sojourner_id,
                EntitlementEvent.global_sequence > after_sequence,
            )
            .order_by(EntitlementEvent.global_sequence)
            .limit(limit + 1)
        )
    )
    total = session.scalar(
        sa.select(sa.func.count()).where(EntitlementEvent.sojourner_id == sojourner_id)
    )
    page = rows[:limit]
    views = []
    for row in page:
        payload, error = _parse(row)
        views.append(
            EventView(
                global_sequence=row.global_sequence,
                event_id=row.event_id,
                event_type=row.event_type,
                created_at=row.created_at,
                turn_id=row.turn_id,
                idempotency_key=row.idempotency_key,
                payload=payload,
                parse_error=error,
            )
        )
    return EventPage(
        events=tuple(views),
        total_events=int(total or 0),
        next_after_sequence=page[-1].global_sequence if len(rows) > limit else None,
    )


class ReplayStatus(StrEnum):
    CONSISTENT = "consistent"
    MISMATCH = "mismatch"
    UNREADABLE = "unreadable"
    ABSENT = "absent"


@dataclass(frozen=True)
class ReplayCheck:
    status: ReplayStatus
    detail_code: str | None
    through_sequence: int | None
    mismatched_fields: tuple[str, ...] = ()


_COMPARED = (
    "hosted_access_active",
    "hosted_access_plan",
    "hosted_credit_balance",
    "top_up_credit_balance",
    "byok_license_active",
    "byok_license_purchased_at",
    "cloud_services_active",
    "cloud_services_expires_at",
)


def _norm(value: object) -> object:
    return to_utc_naive(value) if isinstance(value, datetime) else value


def replay_check(session: Session, sojourner_id: UUID) -> ReplayCheck:
    """Replay the subject's ordered events and compare with the projection.
    Reports; never rebuilds or overwrites anything."""
    events = list(
        session.scalars(
            sa.select(EntitlementEvent)
            .where(EntitlementEvent.sojourner_id == sojourner_id)
            .order_by(EntitlementEvent.global_sequence)
        )
    )
    projection = read_projection(session, sojourner_id)
    through = events[-1].global_sequence if events else None
    if not events and projection is None:
        return ReplayCheck(ReplayStatus.ABSENT, None, None)
    try:
        snapshot = rebuild_entitlement_state(sojourner_id, events)
    except EntitlementPayloadVersionError:
        return ReplayCheck(
            ReplayStatus.UNREADABLE, "unsupported_schema_version", through
        )
    except (EntitlementReplayError, ValidationError, ValueError):
        return ReplayCheck(ReplayStatus.UNREADABLE, "unparseable_event", through)
    if projection is None:
        return ReplayCheck(ReplayStatus.MISMATCH, "projection_missing", through)
    mismatched = tuple(
        name
        for name in _COMPARED
        if _norm(getattr(snapshot, name)) != _norm(getattr(projection, name))
    )
    if events and projection.last_entitlement_event_id != events[-1].event_id:
        mismatched += ("last_entitlement_event_id",)
    if mismatched:
        return ReplayCheck(
            ReplayStatus.MISMATCH, "projection_differs", through, mismatched
        )
    return ReplayCheck(ReplayStatus.CONSISTENT, None, through)


def find_by_idempotency_key(session: Session, key: str) -> EntitlementEvent | None:
    return session.scalars(
        sa.select(EntitlementEvent).where(EntitlementEvent.idempotency_key == key)
    ).first()


def subjects_with_events(session: Session) -> list[UUID]:
    return list(session.scalars(sa.select(EntitlementEvent.sojourner_id).distinct()))
