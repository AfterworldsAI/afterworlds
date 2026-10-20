"""CRD Issue 22 API seam: typed operation failures and view builders.

Keeps the support and data-request handlers thin (Binding Decision 2):
services decide, this module translates their typed results and failures
into the versioned DTOs and the one error envelope.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, NoReturn
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError

from afterworlds.api.dto import (
    EntitlementHistoryItemDTO,
    SupportEventDTO,
)
from afterworlds.api.errors import ApiErrorCode, ApiErrorResponse
from afterworlds.entitlement.inspection import EventView
from afterworlds.operations.errors import OperationError, OperationErrorKind
from afterworlds.operations.support import IDEMPOTENCY_PREFIX, SupportEvent

_ERRORS: dict[OperationErrorKind, tuple[int, ApiErrorCode]] = {
    OperationErrorKind.INVALID_INPUT: (422, ApiErrorCode.VALIDATION_FAILED),
    OperationErrorKind.NOT_FOUND: (404, ApiErrorCode.NOT_FOUND),
    OperationErrorKind.CONFLICT: (409, ApiErrorCode.OPERATION_CONFLICT),
    OperationErrorKind.STALE: (409, ApiErrorCode.OPERATION_STALE),
    OperationErrorKind.PRECONDITION_FAILED: (
        409,
        ApiErrorCode.OPERATION_PRECONDITION_FAILED,
    ),
    OperationErrorKind.OUTCOME_UNKNOWN: (503, ApiErrorCode.OPERATION_OUTCOME_UNKNOWN),
    OperationErrorKind.UNAVAILABLE: (503, ApiErrorCode.OPERATION_UNAVAILABLE),
    OperationErrorKind.UNSUPPORTED: (422, ApiErrorCode.OPERATION_UNSUPPORTED),
    OperationErrorKind.IN_PROGRESS: (409, ApiErrorCode.ACCOUNT_OPERATION_IN_PROGRESS),
}


def raise_operation_error(exc: OperationError) -> NoReturn:
    status_code, code = _ERRORS[exc.kind]
    raise ApiErrorResponse(status_code, code, str(exc)) from None


def run_operation[T](operation: Callable[[], T]) -> T:
    """Run a CRD Issue 22 service call with typed, sanitized failures: a store
    fault never reaches the client as driver text."""
    failure: OperationError | None = None
    try:
        return operation()
    except OperationError as exc:
        failure = exc
    except SQLAlchemyError:
        failure = OperationError(
            OperationErrorKind.UNAVAILABLE,
            "An operations store could not be read; nothing is reported as done.",
        )
    assert failure is not None
    raise_operation_error(failure)


def _utc(value: datetime | None) -> datetime | None:
    if value is None or value.tzinfo is not None:
        return value
    return value.replace(tzinfo=UTC)


def _credit(value: object) -> str | None:
    return f"{value:.4f}" if isinstance(value, Decimal) else None


def history_item(view: EventView) -> EntitlementHistoryItemDTO:
    payload: BaseModel | None = view.payload

    def get(name: str) -> Any:
        return getattr(payload, name, None)

    key = view.idempotency_key or ""
    operation = (
        UUID(key.removeprefix(IDEMPOTENCY_PREFIX))
        if key.startswith(IDEMPOTENCY_PREFIX)
        else None
    )
    reason = get("reason")
    manual = view.event_type == "manual_credit_adjustment"
    return EntitlementHistoryItemDTO(
        global_sequence=view.global_sequence,
        event_id=view.event_id,
        event_type=view.event_type,
        created_at=_utc(view.created_at) or view.created_at,
        turn_id=view.turn_id,
        support_operation_id=operation,
        plan=str(get("plan")) if get("plan") is not None else None,
        hosted_credit_delta=_credit(get("hosted_credit_delta")),
        top_up_credit_delta=_credit(get("top_up_credit_delta")),
        effective_at=_utc(get("effective_at")),
        expires_at=_utc(get("expires_at")),
        purchased_at=_utc(get("purchased_at")),
        reason_code=None if manual or reason is None else str(reason),
        manual_reason=str(reason) if manual and reason is not None else None,
        adjusted_by=get("adjusted_by"),
        external_source=get("external_source"),
        external_reference_id=get("external_reference_id"),
        has_detail=bool(get("detail")),
        parse_error=view.parse_error,
    )


def support_event(event: SupportEvent) -> SupportEventDTO:
    return SupportEventDTO(
        event_id=UUID(event.event_id),
        event_order=event.event_order,
        operation_id=UUID(event.operation_id),
        actor_ref=event.actor_ref,
        action_code=event.action_code,
        target_type=event.target_type,
        target_ref=event.target_ref,
        reason_code=event.reason_code,
        reason_text=event.reason_text,
        hosted_credit_delta=event.hosted_credit_delta,
        top_up_credit_delta=event.top_up_credit_delta,
        requested_at=event.requested_at,
        recorded_at=event.recorded_at,
        outcome_code=event.outcome_code,
        source_entitlement_event_id=(
            UUID(event.source_entitlement_event_id)
            if event.source_entitlement_event_id
            else None
        ),
        supersedes_event_id=(
            UUID(event.supersedes_event_id) if event.supersedes_event_id else None
        ),
    )
