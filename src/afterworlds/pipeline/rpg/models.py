"""Typed payloads and exceptions for the RPG Adjudication pass — CRD Issue 15.
Revised by CRD Issue 15b.
"""

from __future__ import annotations

from pydantic import BaseModel

from afterworlds.models.rpg import (
    ResolvedAdjudicationRecord,
    RollProposal,
    WriterAdjudicationView,
)


class AdjudicationPassResult(BaseModel):
    """Complete result returned by ``RpgAdjudicationPassService.adjudicate()``.

    ``proposals`` and ``writer_views`` are parallel sequences: each proposal
    at index i has a corresponding writer view at index i.  The Orchestrator
    appends ``writer_views`` to the ``PassForwardLedger`` for the Writer pass.

    ``player_proposal`` is populated for turns that need a PLAYER roll; it is
    None for AI/hidden roll turns and for turns where no roll is required.
    CRD Issue 15b: this service no longer builds a ``PendingRollRequest``
    itself (that required sequence-scoped identity it doesn't own) — the
    orchestrator hands the raw proposal to
    ``ActionResolutionService.start_sequence`` inside its own transaction.

    Token counts follow the ``PlannerResult`` convention: the pass service
    populates them from the provider call result; they may be None if the
    adjudication pass did not call the provider.
    """

    proposals: tuple[ResolvedAdjudicationRecord, ...]
    writer_views: tuple[WriterAdjudicationView, ...]
    player_proposal: RollProposal | None = None

    provider: str | None = None
    model_identifier: str | None = None
    model_tier: str | None = None
    latency_ms: int = 0
    input_token_count: int | None = None
    output_token_count: int | None = None
    cache_read_token_count: int | None = None
    cache_creation_token_count: int | None = None


class AdjudicationPassError(Exception):
    """Fail-closed exception for the RPG Adjudication pass.

    Covers: no tool_use block, tool name mismatch, malformed proposal output,
    provider exception, and schema validation failure.  No DB state is committed
    when this is raised.
    """


# ---------------------------------------------------------------------------
# CRD Issue 15b — typed ActionResolutionService errors
# ---------------------------------------------------------------------------


class ActionResolutionError(Exception):
    """Base class for typed ActionResolutionService errors.

    ``code`` is the typed error name from ADR-015b's Errors section — API
    handlers (Phase 3) translate it without re-deriving the mapping.
    """

    code: str = "ACTION_RESOLUTION_ERROR"


class PendingRollNotFoundError(ActionResolutionError):
    code = "PENDING_ROLL_NOT_FOUND"


class PendingRollNotPlayerVisibleError(ActionResolutionError):
    code = "PENDING_ROLL_NOT_PLAYER_VISIBLE"


class PendingRollRevisionMismatchError(ActionResolutionError):
    code = "PENDING_ROLL_REVISION_MISMATCH"


class PendingRollTermMismatchError(ActionResolutionError):
    code = "PENDING_ROLL_TERM_MISMATCH"


class PendingRollInvalidValueError(ActionResolutionError):
    code = "PENDING_ROLL_INVALID_VALUE"


class PendingRollInvalidAggregateError(ActionResolutionError):
    code = "PENDING_ROLL_INVALID_AGGREGATE"


class ActionSequenceNotFoundError(ActionResolutionError):
    code = "ACTION_SEQUENCE_NOT_FOUND"


class ActionSequenceAlreadyCompletedError(ActionResolutionError):
    code = "ACTION_SEQUENCE_ALREADY_COMPLETED"


class ActionSequenceStateConflictError(ActionResolutionError):
    code = "ACTION_SEQUENCE_STATE_CONFLICT"


class ActionAdjustmentNotAllowedError(ActionResolutionError):
    code = "ACTION_ADJUSTMENT_NOT_ALLOWED"


class ActionAdjustmentIneligibleError(ActionResolutionError):
    code = "ACTION_ADJUSTMENT_INELIGIBLE"


class MechanicalDecisionInvalidError(ActionResolutionError):
    code = "MECHANICAL_DECISION_INVALID"


class SequenceNotReadyForNarrationError(ActionResolutionError):
    code = "SEQUENCE_NOT_READY_FOR_NARRATION"


__all__ = [
    "ActionAdjustmentIneligibleError",
    "ActionAdjustmentNotAllowedError",
    "ActionResolutionError",
    "ActionSequenceAlreadyCompletedError",
    "ActionSequenceNotFoundError",
    "ActionSequenceStateConflictError",
    "AdjudicationPassError",
    "AdjudicationPassResult",
    "MechanicalDecisionInvalidError",
    "PendingRollInvalidAggregateError",
    "PendingRollInvalidValueError",
    "PendingRollNotFoundError",
    "PendingRollNotPlayerVisibleError",
    "PendingRollRevisionMismatchError",
    "PendingRollTermMismatchError",
    "SequenceNotReadyForNarrationError",
]
