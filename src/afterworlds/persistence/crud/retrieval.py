"""CRUD helpers for the Retrieval Memory RPG turn-marker sidecar.

CRD Issue 18 / ADR-018 D6. See ``persistence/orm/retrieval.py`` for schema
and ``pipeline/retrieval/eligibility.py`` for the eligibility predicate that
consumes these helpers.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from afterworlds.models.enums import RpgTurnRetrievalCategory
from afterworlds.persistence.orm.retrieval import (
    RetrievalMarkerEraBoundaryORM,
    RpgTurnRetrievalMarkerORM,
)
from afterworlds.persistence.orm.rpg import PendingRollRequestORM


def create_rpg_turn_retrieval_marker(
    session: Session,
    turn_id: UUID,
    story_id: UUID,
    category: RpgTurnRetrievalCategory,
    created_at: str,
) -> None:
    """Insert a marker row. Must run inside the caller's outer transaction.

    Raises on flush failure (e.g. duplicate ``turn_id``) — callers on the
    mandatory narrative-persist path must catch and map to typed
    PIPELINE_ERROR; this function does not swallow.
    """
    session.add(
        RpgTurnRetrievalMarkerORM(
            turn_id=str(turn_id),
            story_id=str(story_id),
            category=category.value,
            created_at=created_at,
        )
    )
    session.flush()


def get_rpg_turn_retrieval_marker(
    session: Session, turn_id: UUID
) -> RpgTurnRetrievalCategory | None:
    """Return the marker category for *turn_id*, or None if no row exists."""
    row = session.get(RpgTurnRetrievalMarkerORM, str(turn_id))
    if row is None:
        return None
    return RpgTurnRetrievalCategory(row.category)


def get_era_boundary_timestamp(session: Session) -> str | None:
    """Return the persisted marker-era boundary timestamp, or None.

    None means either "no boundary row exists yet" (pre-migration DB, should
    not occur once migration 0015 has run) or "no turns existed at
    migration-apply time" (every turn is post-boundary).
    """
    row = session.execute(
        select(RetrievalMarkerEraBoundaryORM).where(
            RetrievalMarkerEraBoundaryORM.id == 1
        )
    ).scalar_one_or_none()
    return row.boundary_timestamp if row is not None else None


def is_post_boundary(turn_timestamp: str, boundary_timestamp: str | None) -> bool:
    """Return True when *turn_timestamp* is strictly after the era boundary.

    ISO-8601 UTC timestamps (as produced by ``datetime.isoformat()`` on a
    UTC-aware datetime) sort correctly as plain strings — see
    ``services/context_builder.py``'s timestamp-sort rationale. A None
    boundary means no turns existed at migration time, so every turn is
    post-boundary.
    """
    if boundary_timestamp is None:
        return True
    return turn_timestamp > boundary_timestamp


def has_pending_roll_request_originating_from_turn(
    session: Session, turn_id: UUID
) -> bool:
    """Return True if a ``PendingRollRequest`` row's ``originating_turn_id``
    equals *turn_id* (any status).

    Codex review (PR #119): a legacy pre-marker RPG turn that announced a
    roll must still be excluded from retrieval eligibility even though it
    predates the marker sidecar entirely and carries no marker row — the
    era-boundary table (ADR-018 D6) makes ``PendingRollRequest`` the sole
    signal for that shape. This reads only the persisted row; it never
    inspects prose or ``RpgSessionState.play_status``.
    """
    return (
        session.query(PendingRollRequestORM)
        .filter_by(originating_turn_id=str(turn_id))
        .first()
        is not None
    )
