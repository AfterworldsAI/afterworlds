"""Support lookup, history and controlled remediation -- CRD Issue 22 §1-§3.

Reads compose the owning services' read paths (identity, entitlement); they
never activate, repair, call a provider or a payment service. The one
remediation that changes money is a manual credit adjustment, which goes only
through ``EntitlementService.receive_entitlement_event`` with
``MANUAL_CREDIT_ADJUSTMENT``, a trusted ``adjusted_by`` and a namespaced
idempotency key derived from the operation ID (CRD Issue 13 stays the
accounting authority; the support stream is provenance, not a ledger).

Order of effects for an adjustment, so effect and provenance never disagree:

1. the staff Actor is revalidated against the identity store;
2. a ``requested`` support event commits (audit failure: no effect);
3. stale state is refused against the displayed ``last_entitlement_event_id``;
4. the entitlement event commits inside the entitlement owner;
5. a ``committed`` outcome event records its ``event_id``.

If step 5 (or the response) is lost, the effect is still discoverable: a
status read or an identical retry finds the entitlement event by its
idempotency key and appends the missing outcome. Nothing is retried blindly.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from afterworlds.entitlement.enums import EntitlementEventType
from afterworlds.entitlement.errors import (
    EntitlementConcurrencyError,
    EntitlementIdempotencyConflictError,
    EntitlementSettlementError,
)
from afterworlds.entitlement.inspection import (
    Projection,
    find_by_idempotency_key,
    read_projection,
)
from afterworlds.entitlement.payloads import ManualCreditAdjustmentPayload
from afterworlds.entitlement.service import EntitlementService
from afterworlds.operations.errors import OperationError, OperationErrorKind
from afterworlds.operations.orm import SupportActionEventORM
from afterworlds.operations.policy import POLICY_VERSION
from afterworlds.remote.control_store import iso, parse_iso, utc_now
from afterworlds.remote.identity import Actor, ActorKind, IdentityService

REASON_MAX_LENGTH = 280
_CONTROL = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")
#: Provider keys and bearer-style tokens (Anthropic, OpenRouter, OpenAI and
#: generic ``sk-``/``Bearer``-prefixed secrets).
_CREDENTIAL = re.compile(r"(sk-[A-Za-z0-9_\-]{8,}|Bearer\s+\S{8,})", re.IGNORECASE)
_DELTA = re.compile(r"^[+-]?\d{1,8}(\.\d{1,4})?$")
#: Namespace of support adjustments in the global entitlement idempotency keys.
IDEMPOTENCY_PREFIX = "crd22-support-adjustment:"
ADJUST_CREDITS = "manual_credit_adjustment"

OUTCOME_REQUESTED = "requested"
OUTCOME_COMMITTED = "committed"
_TERMINAL = frozenset(
    {
        OUTCOME_COMMITTED,
        "rejected_precondition",
        "rejected_stale",
        "conflict",
        "failed",
    }
)


def bounded_text(value: str, what: str = "reason") -> str:
    """Untrusted operator/requester text: trimmed, 1-280 characters, no
    control characters. Stored and shown as plain text, never markup."""
    text = value.strip()
    if not text or len(text) > REASON_MAX_LENGTH or _CONTROL.search(text):
        raise OperationError(
            OperationErrorKind.INVALID_INPUT,
            f"A {what} of 1-{REASON_MAX_LENGTH} printable characters is required.",
        )
    if _CREDENTIAL.search(text):
        # Never stored: a reason is a bounded explanation, not a place for a
        # key or token (the text is not echoed back either).
        raise OperationError(
            OperationErrorKind.INVALID_INPUT,
            f"The {what} looks like it contains a credential; remove it.",
        )
    return text


def parse_delta(value: str | None) -> Decimal | None:
    """Exact signed credit delta: at most 4 decimal places (existing
    precision), refused rather than rounded so the preview equals the effect."""
    if value is None or value.strip() == "":
        return None
    if not _DELTA.match(value.strip()):
        raise OperationError(
            OperationErrorKind.INVALID_INPUT,
            "Credit deltas are signed decimals with at most 4 decimal places.",
        )
    return Decimal(value.strip())


def _fmt(value: Decimal | None) -> str | None:
    return None if value is None else f"{value:.4f}"


@dataclass(frozen=True)
class AdjustmentRequest:
    operation_id: UUID
    account_id: UUID
    hosted_credit_delta: Decimal | None
    top_up_credit_delta: Decimal | None
    reason: str
    expected_last_event_id: UUID | None


@dataclass(frozen=True)
class AdjustmentPreview:
    account_id: UUID
    projection: Projection | None
    hosted_credit_delta: Decimal
    top_up_credit_delta: Decimal
    resulting_hosted: Decimal | None
    resulting_top_up: Decimal | None
    #: Why the entitlement owner would refuse it (no effect), if known now.
    refusal_code: str | None


@dataclass(frozen=True)
class SupportEvent:
    event_id: str
    event_order: int
    operation_id: str
    subject_ref: str
    actor_ref: str
    action_code: str
    target_type: str
    target_ref: str
    reason_code: str
    reason_text: str | None
    hosted_credit_delta: str | None
    top_up_credit_delta: str | None
    requested_at: datetime
    recorded_at: datetime
    outcome_code: str
    source_entitlement_event_id: str | None
    supersedes_event_id: str | None


@dataclass(frozen=True)
class OperationStatus:
    operation_id: UUID
    #: requested (uncertain/incomplete) | committed | rejected_* | conflict |
    #: failed
    outcome_code: str
    source_entitlement_event_id: str | None
    events: tuple[SupportEvent, ...]


def _canonical(
    event: SupportEvent,
) -> tuple[str, str | None, str | None, str | None, str]:
    """The logical action an operation ID was claimed for."""
    return (
        event.target_ref,
        event.hosted_credit_delta,
        event.top_up_credit_delta,
        event.reason_text,
        event.actor_ref,
    )


def _matches(found: Any, requested: SupportEvent) -> bool:
    """Whether the owner's event under this operation's key is exactly the
    claimed action (subject, type and typed payload)."""
    if (
        str(found.sojourner_id) != requested.target_ref
        or found.event_type != EntitlementEventType.MANUAL_CREDIT_ADJUSTMENT.value
    ):
        return False
    try:
        payload = ManualCreditAdjustmentPayload.model_validate_json(found.payload_json)
    except ValueError:
        return False
    return (
        _fmt(payload.hosted_credit_delta) == requested.hosted_credit_delta
        and _fmt(payload.top_up_credit_delta) == requested.top_up_credit_delta
        and payload.reason == requested.reason_text
        and payload.adjusted_by == requested.actor_ref
    )


def _event(row: SupportActionEventORM) -> SupportEvent:
    return SupportEvent(
        event_id=row.event_id,
        event_order=row.event_order,
        operation_id=row.operation_id,
        subject_ref=row.subject_ref,
        actor_ref=row.actor_ref,
        action_code=row.action_code,
        target_type=row.target_type,
        target_ref=row.target_ref,
        reason_code=row.reason_code,
        reason_text=row.reason_text,
        hosted_credit_delta=row.hosted_credit_delta,
        top_up_credit_delta=row.top_up_credit_delta,
        requested_at=parse_iso(row.requested_at),
        recorded_at=parse_iso(row.recorded_at),
        outcome_code=row.outcome_code,
        source_entitlement_event_id=row.source_entitlement_event_id,
        supersedes_event_id=row.supersedes_event_id,
    )


class SupportService:
    """Owner-administrator support actions over the owning services."""

    def __init__(
        self,
        ops: sessionmaker[Session],
        content: sessionmaker[Session],
        identity: IdentityService,
        *,
        now: Callable[[], datetime] = utc_now,
    ) -> None:
        self._ops = ops
        self._content = content
        self._identity = identity
        self._now = now

    # -- reads -------------------------------------------------------------

    def preview_adjustment(
        self,
        account_id: UUID,
        hosted: Decimal | None,
        top_up: Decimal | None,
    ) -> AdjustmentPreview:
        hd, td = hosted or Decimal("0"), top_up or Decimal("0")
        if hd == 0 and td == 0:
            raise OperationError(
                OperationErrorKind.INVALID_INPUT, "At least one delta must be non-zero."
            )
        with self._content() as s:
            projection = read_projection(s, account_id)
        refusal = None
        if projection is None or projection.hosted_access_plan is None:
            refusal = "hosted_access_never_activated"
        return AdjustmentPreview(
            account_id=account_id,
            projection=projection,
            hosted_credit_delta=hd,
            top_up_credit_delta=td,
            resulting_hosted=(
                projection.hosted_credit_balance + hd if projection else None
            ),
            resulting_top_up=(
                projection.top_up_credit_balance + td if projection else None
            ),
            refusal_code=refusal,
        )

    def history(self, account_id: UUID) -> tuple[SupportEvent, ...]:
        """The account's support stream in ``event_order`` (its own order)."""
        with self._ops() as s:
            rows = s.scalars(
                sa.select(SupportActionEventORM)
                .where(SupportActionEventORM.subject_ref == str(account_id))
                .order_by(SupportActionEventORM.event_order)
            )
            return tuple(_event(r) for r in rows)

    def status(self, operation_id: UUID) -> OperationStatus:
        """Authoritative outcome of an operation, reconciling a committed
        effect whose outcome record was lost."""
        events = self._events(operation_id)
        if not events:
            raise OperationError(OperationErrorKind.NOT_FOUND, "Unknown operation.")
        terminal = next((e for e in events if e.outcome_code in _TERMINAL), None)
        if terminal is None:
            self._reconcile(events[0])
            events = self._events(operation_id)
            terminal = next((e for e in events if e.outcome_code in _TERMINAL), None)
        # The first terminal outcome is the outcome; nothing later changes it.
        committed = (
            terminal
            if terminal and terminal.outcome_code == OUTCOME_COMMITTED
            else None
        )
        return OperationStatus(
            operation_id=operation_id,
            outcome_code=terminal.outcome_code if terminal else OUTCOME_REQUESTED,
            source_entitlement_event_id=(
                committed.source_entitlement_event_id if committed else None
            ),
            events=events,
        )

    # -- remediation -------------------------------------------------------

    def adjust_credits(
        self, actor: Actor, request: AdjustmentRequest
    ) -> OperationStatus:
        if actor.kind is not ActorKind.STAFF or actor.principal_ref is None:
            raise OperationError(
                OperationErrorKind.INVALID_INPUT, "Staff authority is required."
            )
        reason = bounded_text(request.reason)
        hd, td = request.hosted_credit_delta, request.top_up_credit_delta
        if (hd or 0) == 0 and (td or 0) == 0:
            raise OperationError(
                OperationErrorKind.INVALID_INPUT, "At least one delta must be non-zero."
            )
        if not self._identity.actor_is_current(actor):
            raise OperationError(
                OperationErrorKind.PRECONDITION_FAILED, "staff_session_not_current"
            )
        if self._identity.get_account(request.account_id) is None:
            raise OperationError(OperationErrorKind.NOT_FOUND, "Account not found.")
        canonical = (
            str(request.account_id),
            _fmt(hd),
            _fmt(td),
            reason,
            actor.principal_ref,
        )
        existing = self._events(request.operation_id)
        if not existing:
            # The claim is atomic: one ``requested`` row per operation (unique
            # index). A concurrent reuse loses here and is compared below.
            claimed = self._append(
                operation_id=request.operation_id,
                account_id=request.account_id,
                actor_ref=actor.principal_ref,
                hosted=hd,
                top_up=td,
                reason=reason,
                outcome=OUTCOME_REQUESTED,
            )
            existing = (claimed,) if claimed else self._events(request.operation_id)
        first = existing[0]
        if _canonical(first) != canonical:
            raise OperationError(
                OperationErrorKind.CONFLICT,
                "This operation ID was already used for a different action.",
            )
        if any(e.outcome_code in _TERMINAL for e in existing):
            return self.status(request.operation_id)
        requested = first
        key = IDEMPOTENCY_PREFIX + str(request.operation_id)
        with self._content() as s:
            found = find_by_idempotency_key(s, key)
            projection = read_projection(s, request.account_id)
        if found is not None:
            # Response or outcome record was lost after the effect committed:
            # accepted only if the owner's event is exactly this action.
            outcome = OUTCOME_COMMITTED if _matches(found, requested) else "conflict"
            return self._finish(requested, outcome, str(found.event_id))
        current = projection.last_entitlement_event_id if projection else None
        if current != request.expected_last_event_id:
            return self._finish(requested, "rejected_stale", None)
        payload = ManualCreditAdjustmentPayload(
            hosted_credit_delta=hd,
            top_up_credit_delta=td,
            reason=reason,
            adjusted_by=actor.principal_ref,
        )
        try:
            with self._content() as s:
                event = EntitlementService(s).receive_entitlement_event(
                    request.account_id,
                    EntitlementEventType.MANUAL_CREDIT_ADJUSTMENT,
                    payload,
                    idempotency_key=key,
                )
                event_id = str(event.event_id)
        except EntitlementSettlementError:
            return self._finish(requested, "rejected_precondition", None)
        except EntitlementIdempotencyConflictError:
            return self._finish(requested, "conflict", None)
        except EntitlementConcurrencyError:
            # Rolled back inside the owner: no effect; a new operation may run.
            return self._finish(requested, "failed", None)
        except SQLAlchemyError:
            raise OperationError(
                OperationErrorKind.OUTCOME_UNKNOWN,
                "The adjustment's outcome is unknown; read its status before "
                "submitting anything else.",
            ) from None
        try:
            return self._finish(requested, OUTCOME_COMMITTED, event_id)
        except SQLAlchemyError:
            raise OperationError(
                OperationErrorKind.OUTCOME_UNKNOWN,
                "The adjustment committed but its record could not be confirmed; "
                "read its status.",
            ) from None

    # -- internals ---------------------------------------------------------

    def _events(self, operation_id: UUID) -> tuple[SupportEvent, ...]:
        with self._ops() as s:
            rows = s.scalars(
                sa.select(SupportActionEventORM)
                .where(SupportActionEventORM.operation_id == str(operation_id))
                .order_by(SupportActionEventORM.event_order)
            )
            return tuple(_event(r) for r in rows)

    def _reconcile(self, requested: SupportEvent) -> None:
        key = IDEMPOTENCY_PREFIX + requested.operation_id
        with self._content() as s:
            found = find_by_idempotency_key(s, key)
        if found is not None:
            outcome = OUTCOME_COMMITTED if _matches(found, requested) else "conflict"
            self._finish(requested, outcome, str(found.event_id))

    def _finish(
        self, requested: SupportEvent, outcome: str, source: str | None
    ) -> OperationStatus:
        operation_id = UUID(requested.operation_id)
        with self._ops() as s:
            s.connection().exec_driver_sql("BEGIN IMMEDIATE")
            done = s.scalar(
                sa.select(SupportActionEventORM.outcome_code).where(
                    SupportActionEventORM.operation_id == requested.operation_id,
                    SupportActionEventORM.outcome_code != OUTCOME_REQUESTED,
                )
            )
            if done is None:
                s.add(
                    self._row(
                        operation_id=operation_id,
                        account_id=UUID(requested.subject_ref),
                        actor_ref=requested.actor_ref,
                        hosted=(
                            Decimal(requested.hosted_credit_delta)
                            if requested.hosted_credit_delta
                            else None
                        ),
                        top_up=(
                            Decimal(requested.top_up_credit_delta)
                            if requested.top_up_credit_delta
                            else None
                        ),
                        reason=requested.reason_text or "",
                        outcome=outcome,
                        requested_at=requested.requested_at,
                        source=source,
                        supersedes=requested.event_id,
                    )
                )
            s.commit()
        return self.status(operation_id)

    def _append(
        self,
        *,
        operation_id: UUID,
        account_id: UUID,
        actor_ref: str,
        hosted: Decimal | None,
        top_up: Decimal | None,
        reason: str,
        outcome: str,
    ) -> SupportEvent | None:
        row = self._row(
            operation_id=operation_id,
            account_id=account_id,
            actor_ref=actor_ref,
            hosted=hosted,
            top_up=top_up,
            reason=reason,
            outcome=outcome,
            requested_at=self._now(),
            source=None,
            supersedes=None,
        )
        try:
            with self._ops.begin() as s:
                s.add(row)
                s.flush()
                return _event(row)
        except IntegrityError:
            return None  # another request claimed this operation first
        except SQLAlchemyError:
            raise OperationError(
                OperationErrorKind.UNAVAILABLE,
                "The support record could not be written; nothing was changed.",
            ) from None

    def _row(
        self,
        *,
        operation_id: UUID,
        account_id: UUID,
        actor_ref: str,
        hosted: Decimal | None,
        top_up: Decimal | None,
        reason: str,
        outcome: str,
        requested_at: datetime,
        source: str | None,
        supersedes: str | None,
    ) -> SupportActionEventORM:
        return SupportActionEventORM(
            event_id=str(uuid4()),
            schema_version=1,
            operation_id=str(operation_id),
            subject_ref=str(account_id),
            actor_ref=actor_ref,
            action_code=ADJUST_CREDITS,
            target_type="hosted_account",
            target_ref=str(account_id),
            reason_code="administrator",
            reason_text=reason,
            hosted_credit_delta=_fmt(hosted),
            top_up_credit_delta=_fmt(top_up),
            requested_at=iso(requested_at),
            recorded_at=iso(self._now()),
            outcome_code=outcome,
            source_entitlement_event_id=source,
            idempotency_ref=IDEMPOTENCY_PREFIX + str(operation_id),
            policy_version=POLICY_VERSION,
            supersedes_event_id=supersedes,
        )
