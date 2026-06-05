"""SQLAlchemy ORM models for entitlement state and event log — CRD Issue 13.

Mutation invariant: ``RuntimeEntitlementState`` has no public repository method
for arbitrary updates.  The only write path in application code is
``EntitlementService.receive_entitlement_event``, which applies event application
rules and updates the row in the same transaction as the event append.  This is a
service/repository design constraint — tests verify no public repository update
method exists for this table.

``EntitlementEvent`` is append-only.  SQLite triggers (created by Alembic migration
0009) prevent UPDATE and DELETE at the DB layer.  Corrections are new events.

``global_sequence`` is ``INTEGER PRIMARY KEY`` — the SQLite rowid alias.  SQLite
auto-increments it on every insert without the AUTOINCREMENT keyword.  This is the
only SQLite-valid approach for a monotonic non-UUID sequence on a table whose
logical primary key is a UUID.  All external references and FKs use ``event_id``;
all replay ordering uses ``global_sequence``.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlalchemy import Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from afterworlds.entitlement.enums import HostedAccessPlan
from afterworlds.persistence.orm.base import Base


class RuntimeEntitlementState(Base):
    """Current-state projection.  One row per Sojourner.

    The first event for a Sojourner creates this row transactionally inside
    ``EntitlementService.receive_entitlement_event``.  Reads before any event
    return a synthetic no-access status without creating a row.

    Invariant: ``hosted_access_active=True`` requires ``hosted_access_plan`` is
    not None.  ``HOSTED_ACCESS_DEACTIVATED`` sets ``hosted_access_active=False``
    but does NOT clear ``hosted_access_plan``.  ``hosted_access_plan=None`` means
    hosted access has never been activated (NO_SUBSCRIPTION).

    Balances may go negative (Owner Decision #3).  No rollover/cap fields —
    rollover/cap policy is an open Known Unknown.
    """

    __tablename__ = "runtime_entitlement_state"

    sojourner_id: Mapped[UUID] = mapped_column(
        sa.Uuid(as_uuid=True, native_uuid=False),
        primary_key=True,
    )

    hosted_access_active: Mapped[bool] = mapped_column(sa.Boolean, default=False)
    hosted_access_plan: Mapped[HostedAccessPlan | None] = mapped_column(
        sa.Enum(HostedAccessPlan, native_enum=False, length=64),
        nullable=True,
        default=None,
    )

    hosted_credit_balance: Mapped[Decimal] = mapped_column(
        Numeric(12, 4, asdecimal=True),
        default=Decimal("0"),
        server_default="0",
    )
    top_up_credit_balance: Mapped[Decimal] = mapped_column(
        Numeric(12, 4, asdecimal=True),
        default=Decimal("0"),
        server_default="0",
    )

    byok_license_active: Mapped[bool] = mapped_column(sa.Boolean, default=False)
    byok_license_purchased_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime, nullable=True, default=None
    )
    cloud_services_active: Mapped[bool] = mapped_column(sa.Boolean, default=False)
    cloud_services_expires_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime, nullable=True, default=None
    )

    created_at: Mapped[datetime] = mapped_column(sa.DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(sa.DateTime, nullable=False)
    last_entitlement_event_id: Mapped[UUID | None] = mapped_column(
        sa.Uuid(as_uuid=True, native_uuid=False),
        sa.ForeignKey("entitlement_event.event_id"),
        nullable=True,
        default=None,
    )


class EntitlementEvent(Base):
    """Append-only entitlement event log.

    ``global_sequence`` is ``INTEGER PRIMARY KEY`` (SQLite rowid alias;
    auto-increments without AUTOINCREMENT keyword).

    All external references and FKs use ``event_id`` (UUID with UNIQUE constraint).
    Replay ordering uses ``global_sequence`` ascending.

    ``created_at`` is set by the injectable clock; it is for display only.
    ``effective_at`` fields in payloads are business timestamps; they do not
    affect replay order.
    """

    __tablename__ = "entitlement_event"
    __table_args__ = (
        sa.Index("ix_entitlement_event_event_id", "event_id", unique=True),
    )

    global_sequence: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[UUID] = mapped_column(
        sa.Uuid(as_uuid=True, native_uuid=False),
        default=uuid4,
    )
    sojourner_id: Mapped[UUID] = mapped_column(
        sa.Uuid(as_uuid=True, native_uuid=False),
        nullable=False,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    turn_id: Mapped[UUID | None] = mapped_column(
        sa.Uuid(as_uuid=True, native_uuid=False),
        nullable=True,
        default=None,
        index=True,
    )
    idempotency_key: Mapped[str | None] = mapped_column(
        sa.String(255),
        nullable=True,
        default=None,
    )
    payload_json: Mapped[str] = mapped_column(sa.Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime, nullable=False, index=True
    )
