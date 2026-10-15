"""Typed seam between the thin RPG action routes and the action-resolution
service (CRD Issue 15b Phase 3, 15b-29).

Route modules may not import the RPG pipeline (``test_handler_thinness``), so
this module owns the only three things the routes need from it:

- delegation to ``ActionResolutionService`` (dice, validation, transitions,
  events, audits and effects all stay there);
- story scoping: the service looks a pending roll or decision up by its own
  id, so a submission is delegated only when that id is the story's current
  pending interaction. Another story's id never advances its sequence under
  this story's lock;
- translation of the backend's typed ``ActionResolutionError`` codes into the
  single error envelope. Messages are fixed per code: a backend message may
  quote adjudication detail or a value range, which never reaches a client
  (15b-17).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import NoReturn
from uuid import UUID

from afterworlds.api.errors import ApiErrorCode, ApiErrorResponse
from afterworlds.models.rpg import (
    ActionResolutionAdvanceResult,
    MechanicalDecisionSubmission,
    PhysicalAggregateRollSubmission,
    RawPlayerRollSubmission,
)
from afterworlds.pipeline.rpg.models import ActionResolutionError
from afterworlds.pipeline.rpg.sequence import ActionResolutionService

_REFETCH = "Refetch the pending interaction."

#: Backend code -> (HTTP status, error code, client message).
ACTION_ERRORS: dict[str, tuple[int, ApiErrorCode, str]] = {
    "PENDING_ROLL_NOT_FOUND": (
        404,
        ApiErrorCode.PENDING_ROLL_NOT_FOUND,
        f"This story has no such pending roll. {_REFETCH}",
    ),
    "PENDING_ROLL_NOT_PLAYER_VISIBLE": (
        403,
        ApiErrorCode.PENDING_ROLL_NOT_PLAYER_VISIBLE,
        "This roll is not the Sojourner's to make.",
    ),
    "PENDING_ROLL_ALREADY_CONSUMED": (
        409,
        ApiErrorCode.PENDING_ROLL_ALREADY_CONSUMED,
        f"This roll was already submitted. {_REFETCH}",
    ),
    "PENDING_ROLL_REVISION_MISMATCH": (
        409,
        ApiErrorCode.PENDING_ROLL_REVISION_MISMATCH,
        f"The roll instruction has changed. {_REFETCH}",
    ),
    "PENDING_ROLL_TERM_MISMATCH": (
        422,
        ApiErrorCode.PENDING_ROLL_TERM_MISMATCH,
        "The submitted dice do not match the roll instruction's terms.",
    ),
    "PENDING_ROLL_INVALID_VALUE": (
        422,
        ApiErrorCode.PENDING_ROLL_INVALID_VALUE,
        "A submitted die value is not a possible face of its die.",
    ),
    "PENDING_ROLL_INVALID_AGGREGATE": (
        422,
        ApiErrorCode.PENDING_ROLL_INVALID_AGGREGATE,
        "The reported total is not possible for this roll.",
    ),
    "ACTION_SEQUENCE_NOT_FOUND": (
        404,
        ApiErrorCode.ACTION_SEQUENCE_NOT_FOUND,
        "This story has no such action sequence.",
    ),
    "ACTION_SEQUENCE_ALREADY_COMPLETED": (
        409,
        ApiErrorCode.ACTION_SEQUENCE_ALREADY_COMPLETED,
        "This action was already narrated. Refetch the transcript and the "
        "pending interaction.",
    ),
    "ACTION_SEQUENCE_STATE_CONFLICT": (
        409,
        ApiErrorCode.ACTION_SEQUENCE_STATE_CONFLICT,
        f"The action can no longer advance as submitted. {_REFETCH}",
    ),
    "ACTION_ADJUSTMENT_NOT_ALLOWED": (
        422,
        ApiErrorCode.ACTION_ADJUSTMENT_NOT_ALLOWED,
        "That option is not offered for this roll.",
    ),
    "ACTION_ADJUSTMENT_INELIGIBLE": (
        409,
        ApiErrorCode.ACTION_ADJUSTMENT_INELIGIBLE,
        f"That option no longer applies to this roll. {_REFETCH}",
    ),
    "MECHANICAL_DECISION_INVALID": (
        422,
        ApiErrorCode.MECHANICAL_DECISION_INVALID,
        f"That is not an option of this story's pending decision. {_REFETCH}",
    ),
    "MECHANICAL_DECISION_REVISION_MISMATCH": (
        409,
        ApiErrorCode.MECHANICAL_DECISION_REVISION_MISMATCH,
        f"The decision has changed. {_REFETCH}",
    ),
    "SEQUENCE_NOT_READY_FOR_NARRATION": (
        409,
        ApiErrorCode.SEQUENCE_NOT_READY_FOR_NARRATION,
        f"The action still awaits the Sojourner. {_REFETCH}",
    ),
}


def raise_for_action_sequence_error(code: str) -> NoReturn:
    """Raise the envelope for a backend action-resolution code, as carried
    by ``OrchestrationResult.action_sequence_error`` or the service's errors.
    """
    status, error_code, message = ACTION_ERRORS[code]
    raise ApiErrorResponse(status, error_code, message)


class RpgActions:
    """The routes' view of the action-resolution service: player views in,
    player views out, typed envelope errors on refusal."""

    def __init__(self, sequences: ActionResolutionService) -> None:
        self._sequences = sequences

    def current(self, story_id: UUID) -> ActionResolutionAdvanceResult | None:
        return self._call(self._sequences.current, story_id)

    def submit_roll(
        self,
        story_id: UUID,
        submission: RawPlayerRollSubmission | PhysicalAggregateRollSubmission,
    ) -> ActionResolutionAdvanceResult:
        self._require_pending_roll(story_id, submission.pending_roll_request_id)
        return self._call(self._sequences.consume_roll, submission)

    def adjust(
        self,
        story_id: UUID,
        pending_roll_request_id: UUID,
        expected_instruction_revision: int,
        option_id: str,
    ) -> ActionResolutionAdvanceResult:
        self._require_pending_roll(story_id, pending_roll_request_id)
        return self._call(
            self._sequences.apply_adjustment,
            pending_roll_request_id,
            expected_instruction_revision,
            option_id,
        )

    def decide(
        self, story_id: UUID, submission: MechanicalDecisionSubmission
    ) -> ActionResolutionAdvanceResult:
        current = self.current(story_id)
        if (
            current is None
            or current.pending_decision is None
            or current.pending_decision.decision_request_id
            != submission.decision_request_id
        ):
            raise_for_action_sequence_error("MECHANICAL_DECISION_INVALID")
        return self._call(self._sequences.submit_decision, submission)

    def refuse_settled_resume(
        self, story_id: UUID, sequence_id: UUID, node_id: UUID
    ) -> None:
        """For a resume with no runnable access path (15b-32): a sequence that
        is not the story's unresolved one is classified by the owning
        service's own delivery check, which refuses it typed (already
        completed, or not found) before reading anything else. The story's
        unresolved sequence, ready or not, is left untouched for the access
        block: one unresolved sequence per story makes the two cases
        exhaustive."""
        current = self.current(story_id)
        if current is not None and current.sequence_id == sequence_id:
            return
        self._call(self._sequences.prepare_delivery, story_id, sequence_id, node_id)

    def _require_pending_roll(self, story_id: UUID, request_id: UUID) -> None:
        current = self.current(story_id)
        if (
            current is None
            or current.pending_roll is None
            or current.pending_roll.pending_roll_request_id != request_id
        ):
            raise_for_action_sequence_error("PENDING_ROLL_NOT_FOUND")

    @staticmethod
    def _call[T](fn: Callable[..., T], *args: object) -> T:
        try:
            return fn(*args)
        except ActionResolutionError as exc:
            raise_for_action_sequence_error(exc.code)


__all__ = ["ACTION_ERRORS", "RpgActions", "raise_for_action_sequence_error"]
