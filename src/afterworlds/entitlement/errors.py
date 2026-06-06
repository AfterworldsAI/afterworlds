"""Entitlement error types — CRD Issue 13."""

from __future__ import annotations

from afterworlds.errors import AfterworldsError


class EntitlementSettlementError(AfterworldsError):
    """Settlement failure: missing metrics; wrong access_path; computed deduction <= 0;
    DELIVERED/OOC result without turn_id; payload/event-type mismatch; provider=None
    when normalization supplied; credit mutation before hosted access ever activated.
    """


class EntitlementIdempotencyConflictError(AfterworldsError):
    """Same idempotency_key submitted with a different sojourner_id,
    event_type, turn_id, or payload field values.
    """


class EntitlementSettlementConflictError(AfterworldsError):
    """Same turn_id already has a CREDIT_DEDUCTION event with different
    deduction amounts.
    """


class EntitlementPayloadVersionError(AfterworldsError):
    """Payload schema_version is not supported.

    Include event_id, event_type, seen_version in the error message.
    """


class EntitlementReplayError(AfterworldsError):
    """rebuild_entitlement_state encountered an unrecognized event_type.

    Include global_sequence of the offending event in the error message.
    """


class EntitlementConcurrencyError(AfterworldsError):
    """Optimistic concurrency check failed after all retry attempts.

    The ``last_entitlement_event_id`` version guard detected a concurrent write
    on every attempt (conditional UPDATE rowcount==0 each time, or repeated
    first-row INSERT races).  The projection was never silently overwritten;
    the caller must retry at a higher level or surface the error.
    """


class CloudServicesLapsedError(AfterworldsError):
    """CloudServicesGate blocked a cloud operation for a lapsed, expired, or
    expires_at=None Sojourner.
    """
