"""Typed payloads and exceptions for the RPG Adjudication pass — CRD Issue 15."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

from afterworlds.models.rpg import (
    ResolvedAdjudicationRecord,
    WriterAdjudicationView,
)


class AdjudicationPassResult(BaseModel):
    """Complete result returned by ``RpgAdjudicationPassService.adjudicate()``.

    ``proposals`` and ``writer_views`` are parallel sequences: each proposal
    at index i has a corresponding writer view at index i.  The Orchestrator
    appends ``writer_views`` to the ``PassForwardLedger`` for the Writer pass.

    ``sequence`` is set when the turn's resolution paused for the Sojourner
    (CRD Issue 15b): a ``SequenceStart`` the announce transaction persists.
    ``proposals`` is then empty and ``writer_views`` holds the single
    announcement of what the Sojourner is asked for.

    Token counts follow the ``PlannerResult`` convention: the pass service
    populates them from the provider call result.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    proposals: tuple[ResolvedAdjudicationRecord, ...]
    writer_views: tuple[WriterAdjudicationView, ...]
    #: CRD Issue 15b: the action-resolution sequence this turn starts
    #: (``SequenceStart``), or ``None``.
    sequence: Any = None
    #: CRD Issue 15b, Group 17: a turn that needed no player input but
    #: resolved a contest (``CompletedSequence``): the delivered Turn
    #: persists its ledger completed and audits from its events.
    completed_sequence: Any = None
    #: CRD Issue 15c: the subjects besides the acting character that this
    #: turn's operations read (``TurnCharacter``/``TurnCreature``), each with
    #: the revision and binding it was read at. The orchestrator rechecks
    #: every one at commit and applies their effects atomically with the Turn.
    subjects: tuple[Any, ...] = ()
    #: CRD Issue 15c: the actor-turn coordination the turn read, when it has
    #: an edge (``StoredCoordination``). The orchestrator replays the records'
    #: edges onto it and commits by compare-and-swap with the Turn.
    coordination: Any = None
    #: CRD Issue 15c: ``(story_id, snapshot)`` of every character and creature
    #: with its revision, taken before the turn's discovery scans (aura
    #: holders, turn-bounded effects), whose absences it consumed. The
    #: orchestrator requires the story unchanged at commit.
    discovery: Any = None

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


class PreflightGapError(AdjudicationPassError):
    """A refusal raised after a die of the turn was rolled (CRD Issue 15c).

    The preflight checks every operation before any die, so this marks a
    defect in it. It is never an ordinary refusal: the turn fails closed with
    the defect named, and nothing is committed.
    """


class PlayerInputRequired(Exception):  # noqa: N818 - a pause, not a failure
    """An action-resolution sequence pauses here (CRD Issue 15b): the next
    die is the Sojourner's to roll, or a result triggered their decision.
    Raised by the sequence's dice source and caught only by the sequence
    engine; every other handler lets it through. It carries the stored
    authority of the pending interaction."""

    def __init__(self, roll: Any = None, decision: Any = None) -> None:
        #: The pending die's ``RollInstructionSnapshot``.
        self.roll = roll
        #: ``(MechanicalDecisionSnapshot, operation index, decision index)``.
        self.decision = decision
        super().__init__("player input required")


class ActionResolutionError(Exception):
    """A typed action-resolution failure (#127 Errors). ``code`` is stable;
    the message never carries hidden mechanics. Nothing was committed."""

    code = "ACTION_SEQUENCE_STATE_CONFLICT"


class PendingRollNotFoundError(ActionResolutionError):
    """PENDING_ROLL_NOT_FOUND"""

    code = "PENDING_ROLL_NOT_FOUND"


class PendingRollNotPlayerVisibleError(ActionResolutionError):
    """PENDING_ROLL_NOT_PLAYER_VISIBLE"""

    code = "PENDING_ROLL_NOT_PLAYER_VISIBLE"


class PendingRollAlreadyConsumedError(ActionResolutionError):
    """PENDING_ROLL_ALREADY_CONSUMED"""

    code = "PENDING_ROLL_ALREADY_CONSUMED"


class PendingRollRevisionMismatchError(ActionResolutionError):
    """PENDING_ROLL_REVISION_MISMATCH"""

    code = "PENDING_ROLL_REVISION_MISMATCH"


class PendingRollTermMismatchError(ActionResolutionError):
    """PENDING_ROLL_TERM_MISMATCH"""

    code = "PENDING_ROLL_TERM_MISMATCH"


class PendingRollInvalidValueError(ActionResolutionError):
    """PENDING_ROLL_INVALID_VALUE"""

    code = "PENDING_ROLL_INVALID_VALUE"


class PendingRollInvalidAggregateError(ActionResolutionError):
    """PENDING_ROLL_INVALID_AGGREGATE"""

    code = "PENDING_ROLL_INVALID_AGGREGATE"


class ActionSequenceNotFoundError(ActionResolutionError):
    """ACTION_SEQUENCE_NOT_FOUND"""

    code = "ACTION_SEQUENCE_NOT_FOUND"


class ActionSequenceAlreadyCompletedError(ActionResolutionError):
    """ACTION_SEQUENCE_ALREADY_COMPLETED"""

    code = "ACTION_SEQUENCE_ALREADY_COMPLETED"


class ActionSequenceStateConflictError(ActionResolutionError):
    """ACTION_SEQUENCE_STATE_CONFLICT"""

    code = "ACTION_SEQUENCE_STATE_CONFLICT"


class ActionAdjustmentNotAllowedError(ActionResolutionError):
    """ACTION_ADJUSTMENT_NOT_ALLOWED"""

    code = "ACTION_ADJUSTMENT_NOT_ALLOWED"


class ActionAdjustmentIneligibleError(ActionResolutionError):
    """ACTION_ADJUSTMENT_INELIGIBLE"""

    code = "ACTION_ADJUSTMENT_INELIGIBLE"


class MechanicalDecisionInvalidError(ActionResolutionError):
    """MECHANICAL_DECISION_INVALID"""

    code = "MECHANICAL_DECISION_INVALID"


class MechanicalDecisionRevisionMismatchError(ActionResolutionError):
    """MECHANICAL_DECISION_REVISION_MISMATCH"""

    code = "MECHANICAL_DECISION_REVISION_MISMATCH"


class SequenceNotReadyForNarrationError(ActionResolutionError):
    """SEQUENCE_NOT_READY_FOR_NARRATION"""

    code = "SEQUENCE_NOT_READY_FOR_NARRATION"


class ActionSequenceIntegrityError(ActionResolutionError):
    """The stored authority and what code computes from current state
    disagree: never silently replaced."""

    code = "ACTION_SEQUENCE_STATE_CONFLICT"


__all__ = [
    "ActionAdjustmentIneligibleError",
    "ActionAdjustmentNotAllowedError",
    "ActionResolutionError",
    "ActionSequenceAlreadyCompletedError",
    "ActionSequenceIntegrityError",
    "ActionSequenceNotFoundError",
    "ActionSequenceStateConflictError",
    "AdjudicationPassError",
    "AdjudicationPassResult",
    "MechanicalDecisionInvalidError",
    "MechanicalDecisionRevisionMismatchError",
    "PendingRollAlreadyConsumedError",
    "PendingRollInvalidAggregateError",
    "PendingRollInvalidValueError",
    "PendingRollNotFoundError",
    "PendingRollNotPlayerVisibleError",
    "PendingRollRevisionMismatchError",
    "PendingRollTermMismatchError",
    "PlayerInputRequired",
    "PreflightGapError",
    "SequenceNotReadyForNarrationError",
]
