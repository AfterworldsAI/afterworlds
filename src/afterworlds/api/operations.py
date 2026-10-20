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
    DataRequestDTO,
    DataRequestKind,
    DataRequestPhaseDTO,
    DataRequestReceiptDTO,
    DataRequestScope,
    DataRequestState,
    DataRequestTransitionDTO,
    DeletionPreviewResponse,
    EntitlementHistoryItemDTO,
    ExportArtifactDTO,
    RetainedCategoryDTO,
    SupportEventDTO,
)
from afterworlds.api.errors import ApiErrorCode, ApiErrorResponse
from afterworlds.entitlement.inspection import EventView
from afterworlds.operations.errors import OperationError, OperationErrorKind
from afterworlds.operations.requests import RequestView
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


def _actor_role(view: RequestView, actor_ref: str) -> str:
    if actor_ref == "lifecycle_executor":
        return "system"
    return "requester" if actor_ref == view.requester_ref else "administrator"


def request_dto(view: RequestView, *, administrator: bool) -> DataRequestDTO:
    """Status for the requester (no internal actor references) or for the
    Owner administrator (with them and the subject)."""
    return DataRequestDTO(
        request_id=UUID(view.request_id),
        kind=DataRequestKind(view.kind),
        environment="remote" if view.environment == "remote" else "local",
        scope=DataRequestScope(view.scope),
        story_ids=[UUID(s) for s in view.story_refs],
        state=DataRequestState(view.state),
        revision=view.revision,
        requested_at=view.requested_at,
        verified_at=view.verified_at,
        confirmed_at=view.confirmed_at,
        approved_at=view.approved_at,
        closed_at=view.closed_at,
        export_deadline_at=view.export_deadline_at,
        live_deadline_at=view.live_deadline_at,
        backup_deadline_at=view.backup_deadline_at,
        overdue=list(view.overdue),
        missed_deadlines=list(view.missed_deadlines),
        progress_code=view.progress_code,
        policy_version=view.policy_version,
        transitions=[
            DataRequestTransitionDTO(
                revision=t.revision,
                state=DataRequestState(t.state),
                attempt_id=UUID(t.attempt_id) if t.attempt_id else None,
                actor_role=_actor_role(view, t.actor_ref),
                actor_ref=t.actor_ref if administrator else None,
                authorization_code=t.authorization_code,
                reason_code=t.reason_code,
                reason_text=t.reason_text,
                recorded_at=t.recorded_at,
            )
            for t in view.transitions
        ],
        phases=[
            DataRequestPhaseDTO(
                phase_code=p.phase_code,
                outcome_code=p.outcome_code,
                attempt_id=UUID(p.attempt_id),
                counts=p.counts,
                detail_code=p.detail_code,
                observed_at=p.observed_at,
                deadline_at=p.deadline_at,
            )
            for p in view.phases
        ],
        receipts=[
            DataRequestReceiptDTO(
                receipt_id=UUID(r["receipt_id"]),
                receipt_kind=r["receipt_kind"],
                attempt_id=UUID(r["attempt_id"]),
                created_at=datetime.fromisoformat(r["created_at"]),
                body=r["body"],
            )
            for r in view.receipts
        ],
        artifact=(
            ExportArtifactDTO(
                status=view.artifact.status,
                available_at=view.artifact.available_at,
                expires_at=view.artifact.expires_at,
                removed_at=view.artifact.removed_at,
                size_bytes=view.artifact.size_bytes,
            )
            if view.artifact
            else None
        ),
        subject_ref=UUID(view.subject_ref) if administrator else None,
    )


def preview_dto(preview: dict[str, Any]) -> DeletionPreviewResponse:
    return DeletionPreviewResponse(
        scope=DataRequestScope(preview["scope"]),
        story_ids=[UUID(s) for s in preview["story_ids"]],
        counts=preview["counts"],
        removed_classes=preview["removed_classes"],
        retained_categories=[
            RetainedCategoryDTO(**c) for c in preview["retained_categories"]
        ],
        scope_revision=preview["scope_revision"],
        live_deletion_limit_days=preview["live_deletion_limit_days"],
        final_deletion_limit_days=preview["final_deletion_limit_days"],
        commercial_dependency=preview["commercial_dependency"],
        notices=preview["notices"],
    )


OPERATIONS_PATH_PREFIXES = ("/api/data-requests", "/api/admin")


def _known_parts() -> frozenset[str]:
    from afterworlds.api import dto

    models = (
        dto.CreateDataRequest,
        dto.ConfirmDeletionRequest,
        dto.DataRequestStepRequest,
        dto.RejectDataRequest,
        dto.ReceiptLookupRequest,
        dto.CreditAdjustmentRequest,
        dto.CreditAdjustmentPreviewRequest,
        dto.AnomalyNoteRequest,
        dto.RevokeSessionsRequest,
        dto.SignInRequest,
    )
    params = {
        "body",
        "path",
        "query",
        "request_id",
        "account_id",
        "operation_id",
        "anomaly_id",
        "after_sequence",
        "limit",
    }
    return frozenset(params.union(*(m.model_fields for m in models)))


def operations_validation_location(loc: tuple[int | str, ...]) -> str:
    """Dotted location naming only known fields: an unknown property name is
    client-chosen (it could carry a secret) and is never echoed."""
    known = _known_parts()
    return ".".join(
        str(part) if isinstance(part, int) or part in known else "<unrecognized>"
        for part in loc
    )
