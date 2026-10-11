"""Typed outcomes of the CRD Issue 2b state services.

Every refusal is a typed value or a typed exception carrying one. Nothing here
degrades to a default, an ability-only roll or an ``undetermined`` outcome.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from afterworlds.services.rules_authority.outcomes import AuthorityOutcome


class FailureCode(StrEnum):
    """Why recorded state is not valid or not ready under a binding."""

    #: An identity names no record (or component) of the bound authority.
    INVALID_IDENTITY = "invalid_identity"
    #: The identity resolves, but to a record of the wrong kind.
    WRONG_KIND = "wrong_kind"
    #: A family the bound authority makes applicable is not recorded.
    MISSING_STATE = "missing_state"
    #: A value exceeds a bound the structured authority states.
    BOUND_EXCEEDED = "bound_exceeded"
    #: A recorded choice was made under a source schema the target changed.
    SCHEMA_CHANGED = "schema_changed"
    #: Recorded state contradicts itself across families.
    INCONSISTENT = "inconsistent"


@dataclass(frozen=True)
class StateFailure:
    code: FailureCode
    path: str
    detail: str

    def __str__(self) -> str:
        return f"{self.code.value} at {self.path}: {self.detail}"


class StateServiceError(Exception):
    """Base of the 2b state service's typed refusals."""


class SubjectNotFoundError(StateServiceError):
    pass


class InvalidStateError(StateServiceError):
    """Recorded or proposed state fails validation against its binding."""

    def __init__(self, failures: tuple[StateFailure, ...]) -> None:
        self.failures = failures
        super().__init__("; ".join(str(f) for f in failures))


class StaleRevisionError(StateServiceError):
    """Work computed against a superseded revision or binding cannot commit."""


class BindingRefusedError(StateServiceError):
    """The subject's recorded binding is not usable current authority."""

    def __init__(self, outcome: AuthorityOutcome, detail: str) -> None:
        self.outcome = outcome
        super().__init__(f"{outcome.value}: {detail}")


class UnsupportedIdentityError(StateServiceError):
    """An identity the item and state contracts cannot represent."""


class AffectedEventsPendingError(StateServiceError):
    """An operation must wait for affected pending or in-flight events."""
