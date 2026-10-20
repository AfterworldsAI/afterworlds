"""Typed CRD Issue 22 operation failures (translated once in the API layer)."""

from __future__ import annotations

from enum import StrEnum


class OperationErrorKind(StrEnum):
    INVALID_INPUT = "invalid_input"
    NOT_FOUND = "not_found"
    #: The same operation/request identity reused with a different target or
    #: payload, or an invalid state transition.
    CONFLICT = "conflict"
    #: The displayed state/revision is no longer current.
    STALE = "stale"
    #: An owning-service precondition refused the effect (no effect).
    PRECONDITION_FAILED = "precondition_failed"
    #: The effect may or may not have committed: read status before retrying.
    OUTCOME_UNKNOWN = "outcome_unknown"
    #: A required store or dependency could not be read.
    UNAVAILABLE = "unavailable"
    #: Supported scope but not this request (safe reason).
    UNSUPPORTED = "unsupported"
    #: Another account operation holds the fence.
    IN_PROGRESS = "in_progress"


class OperationError(Exception):
    def __init__(self, kind: OperationErrorKind, message: str) -> None:
        super().__init__(message)
        self.kind = kind
