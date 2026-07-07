"""Typed API error envelope — Binding Decision 10.

One error shape for every failure. Read-path and bootstrapping failures fail
closed with actionable typed errors; blanket ``except Exception`` is confined
to the single top-level translator installed on the app in ``app.py``.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel


class ApiErrorCode(StrEnum):
    NOT_FOUND = "not_found"
    VALIDATION_FAILED = "validation_failed"
    ENTITLEMENT_BLOCKED = "entitlement_blocked"
    BYOK_CREDENTIALS_REQUIRED = "byok_credentials_required"
    TURN_IN_FLIGHT = "turn_in_flight"
    SETUP_REQUIRED = "setup_required"
    SETUP_STATE_CONFLICT = "setup_state_conflict"
    INTERNAL_ERROR = "internal_error"


class ApiError(BaseModel):
    """The single API error envelope shape."""

    model_config = {"extra": "forbid"}

    error_code: ApiErrorCode
    message: str
    detail: dict[str, str] | None = None
    schema_version: Literal[1] = 1


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
