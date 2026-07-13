"""PendingRollRequestService — CRD Issue 15 Phase 6.

Manages the pending-roll-request lifecycle for the RPG adjudication loop:

  - load_pending_for_story: read the active pending roll from the DB before
    the outer transaction opens (opens its own short-lived read session).
  - mark_consumed: update status='consumed' inside the caller's transaction
    after the provisional Turn row exists.
  - check_no_pending_for_story: raise PendingRollDuplicateError if a pending
    roll already exists before a new one is announced (inside the transaction
    so the check and write are atomic).

``PendingRollDuplicateError`` is a typed runtime exception.  The orchestrator
catches it in ``_narrative_persist`` and maps it to PIPELINE_ERROR.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import TYPE_CHECKING, Literal, cast
from uuid import UUID

from sqlalchemy.orm import Session

from afterworlds.models.enums import RollVisibility
from afterworlds.models.rpg import PendingRollRequest

if TYPE_CHECKING:
    from afterworlds.persistence.orm.rpg import PendingRollRequestORM


class PendingRollDuplicateError(Exception):
    """Raised when a pending roll is announced while one already exists.

    Superseded as the primary story-level gate by ``ActionSequenceStateConflictError``
    (CRD Issue 15b) — the authoritative "one unresolved thing per story" invariant now
    lives on ``action_resolution_sequences``. This still fires as a lower-level
    defense-in-depth check inside ``check_no_pending_for_story``.
    """

    code = "ACTION_SEQUENCE_STATE_CONFLICT"


class PendingRollAlreadyConsumedError(Exception):
    """Raised when mark_consumed targets a row that is no longer pending."""

    code = "PENDING_ROLL_ALREADY_CONSUMED"


class PendingRollRequestService:
    """Pending-roll-request lifecycle manager for the RPG adjudication loop.

    Args:
        session_factory: factory returning a fresh SQLAlchemy Session.
            ``load_pending_for_story`` opens and closes its own session.
            ``mark_consumed`` and ``check_no_pending_for_story`` receive the
            outer transaction session from the orchestrator.
    """

    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory

    def load_pending_for_story(self, story_id: UUID) -> PendingRollRequest | None:
        """Return the active pending roll for a story, or None.

        Opens and closes its own read session so this does not participate
        in the outer transaction.  Must be called before the outer transaction
        opens (pre-transaction intercept in the orchestrator).
        """
        from afterworlds.persistence.orm.rpg import PendingRollRequestORM

        session = self._session_factory()
        try:
            orm: PendingRollRequestORM | None = (
                session.query(PendingRollRequestORM)
                .filter_by(story_id=str(story_id), status="pending")
                .one_or_none()
            )
            return _orm_to_model(orm) if orm is not None else None
        finally:
            session.close()

    def mark_consumed(
        self,
        session: Session,
        request_id: UUID,
        consumed_turn_id: UUID,
    ) -> None:
        """Mark a pending roll as consumed inside the caller's transaction.

        Must be called after the provisional Turn row exists so the
        ``consumed_turn_id`` foreign key is valid.
        """
        from afterworlds.persistence.orm.rpg import PendingRollRequestORM

        rowcount = (
            session.query(PendingRollRequestORM)
            .filter_by(request_id=str(request_id), status="pending")
            .update({"status": "consumed", "consumed_turn_id": str(consumed_turn_id)})
        )
        if rowcount == 0:
            raise PendingRollAlreadyConsumedError(
                f"PendingRollRequest {request_id!r} is not in 'pending' status; "
                "cannot consume"
            )

    def check_no_pending_for_story(self, session: Session, story_id: UUID) -> None:
        """Raise PendingRollDuplicateError if an active pending roll exists.

        Must be called inside the outer transaction immediately before writing
        a new PendingRollRequestORM so the check and write are atomic.
        """
        from afterworlds.persistence.orm.rpg import PendingRollRequestORM

        existing: PendingRollRequestORM | None = (
            session.query(PendingRollRequestORM)
            .filter_by(story_id=str(story_id), status="pending")
            .first()
        )
        if existing is not None:
            raise PendingRollDuplicateError(
                f"Story {story_id} already has an active pending roll "
                f"request {existing.request_id!r}; cannot announce another"
            )


def _orm_to_model(orm: PendingRollRequestORM) -> PendingRollRequest:
    """Convert a ``PendingRollRequestORM`` row to a ``PendingRollRequest`` model.

    Revised for CRD Issue 15b: display/derivation fields are retired in favor
    of the structured ``instruction_snapshot_json``; see ADR-015b's Column
    Disposition table.
    """
    return PendingRollRequest(
        request_id=UUID(orm.request_id),
        story_id=UUID(orm.story_id),
        session_id=UUID(orm.session_id),
        character_id=UUID(orm.character_id),
        visibility=RollVisibility(orm.visibility),
        source_proposal_ref=orm.source_proposal_ref,
        originating_turn_id=UUID(orm.originating_turn_id),
        consumed_turn_id=(
            UUID(orm.consumed_turn_id) if orm.consumed_turn_id is not None else None
        ),
        status=cast(Literal["pending", "consumed", "cancelled", "expired"], orm.status),
        created_at=datetime.fromisoformat(orm.created_at),
        schema_version=cast(Literal[1], orm.schema_version),
        adapter_context_hash=orm.adapter_context_hash,
        sequence_id=(UUID(orm.sequence_id) if orm.sequence_id is not None else None),
        step_id=(UUID(orm.step_id) if orm.step_id is not None else None),
        instruction_id=(
            UUID(orm.instruction_id) if orm.instruction_id is not None else None
        ),
        instruction_revision=orm.instruction_revision,
        instruction_schema_version=orm.instruction_schema_version,
        instruction_snapshot_json=orm.instruction_snapshot_json,
    )


__all__ = [
    "PendingRollAlreadyConsumedError",
    "PendingRollDuplicateError",
    "PendingRollRequestService",
]
