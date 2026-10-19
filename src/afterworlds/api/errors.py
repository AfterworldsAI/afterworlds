"""Typed API error envelope — Binding Decision 10.

One error shape for every failure. Read-path and bootstrapping failures fail
closed with actionable typed errors; blanket ``except Exception`` is confined
to the single top-level translator installed on the app in ``app.py``.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel


class ApiErrorCode(StrEnum):
    NOT_FOUND = "not_found"
    VALIDATION_FAILED = "validation_failed"
    ENTITLEMENT_BLOCKED = "entitlement_blocked"
    BYOK_CREDENTIALS_REQUIRED = "byok_credentials_required"
    TURN_IN_FLIGHT = "turn_in_flight"
    SETUP_REQUIRED = "setup_required"
    SETUP_STATE_CONFLICT = "setup_state_conflict"
    # ADR-017b: a mode represented internally but not offered by this release.
    MODE_UNAVAILABLE = "mode_unavailable"
    INTERNAL_ERROR = "internal_error"
    # CRD Issue 15b action-resolution refusals (#127 Errors), translated
    # one-to-one from the backend's typed codes by ``api/rpg_actions.py``.
    PENDING_ROLL_NOT_FOUND = "pending_roll_not_found"
    PENDING_ROLL_NOT_PLAYER_VISIBLE = "pending_roll_not_player_visible"
    PENDING_ROLL_ALREADY_CONSUMED = "pending_roll_already_consumed"
    PENDING_ROLL_REVISION_MISMATCH = "pending_roll_revision_mismatch"
    PENDING_ROLL_TERM_MISMATCH = "pending_roll_term_mismatch"
    PENDING_ROLL_INVALID_VALUE = "pending_roll_invalid_value"
    PENDING_ROLL_INVALID_AGGREGATE = "pending_roll_invalid_aggregate"
    ACTION_SEQUENCE_NOT_FOUND = "action_sequence_not_found"
    # 15b-32: success-equivalent for the client, which refetches the
    # transcript and pending interaction instead of presenting an error.
    ACTION_SEQUENCE_ALREADY_COMPLETED = "action_sequence_already_completed"
    ACTION_SEQUENCE_STATE_CONFLICT = "action_sequence_state_conflict"
    ACTION_ADJUSTMENT_NOT_ALLOWED = "action_adjustment_not_allowed"
    ACTION_ADJUSTMENT_INELIGIBLE = "action_adjustment_ineligible"
    MECHANICAL_DECISION_INVALID = "mechanical_decision_invalid"
    MECHANICAL_DECISION_REVISION_MISMATCH = "mechanical_decision_revision_mismatch"
    SEQUENCE_NOT_READY_FOR_NARRATION = "sequence_not_ready_for_narration"
    # CRD Issue 20 BYOK settings failures (``api/account.py``).
    CREDENTIAL_STORE_READ_ONLY = "credential_store_read_only"
    CREDENTIAL_STORE_UNAVAILABLE = "credential_store_unavailable"
    CREDENTIAL_SETTINGS_UNAVAILABLE = "credential_settings_unavailable"
    CREDENTIAL_NOT_CONFIGURED = "credential_not_configured"
    CREDENTIAL_VALIDATION_SUPERSEDED = "credential_validation_superseded"
    CREDENTIAL_VALIDATION_UNAVAILABLE = "credential_validation_unavailable"
    # Prerequisite #205 remote identity boundary (``api/remote_access.py``).
    AUTHENTICATION_REQUIRED = "authentication_required"
    AUTHENTICATION_FAILED = "authentication_failed"
    STAFF_AUTHORITY_REQUIRED = "staff_authority_required"
    REQUEST_ORIGIN_REJECTED = "request_origin_rejected"
    BYOK_LOCAL_ONLY = "byok_local_only"
    DEPLOYMENT_ROUTE_UNAVAILABLE = "deployment_route_unavailable"
    IDENTITY_UNAVAILABLE = "identity_unavailable"
    ACCOUNT_OPERATION_IN_PROGRESS = "account_operation_in_progress"


class ApiError(BaseModel):
    """The single API error envelope shape."""

    model_config = {"extra": "forbid"}

    error_code: ApiErrorCode
    message: str
    detail: dict[str, str] | None = None
    schema_version: Literal[1] = 1


#: ``responses=`` for routes whose typed errors are part of their generated
#: contract (CRD Issue 15b): exception-handler shapes are otherwise absent
#: from OpenAPI, so ``ApiError``/``ApiErrorCode`` reach the TypeScript types.
API_ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    status: {"model": ApiError} for status in (401, 403, 404, 409, 422)
}


class ApiErrorResponse(Exception):
    """Raised by handlers/services to produce a typed ``ApiError`` HTTP response.

    Carries its own HTTP status so handlers never choose status codes ad hoc.
    """

    def __init__(
        self,
        status_code: int,
        error_code: ApiErrorCode,
        message: str,
        detail: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.error = ApiError(error_code=error_code, message=message, detail=detail)
