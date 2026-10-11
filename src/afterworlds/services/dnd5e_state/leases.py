"""Durable in-flight turn leases — the in-progress adjudication marker.

A pending roll is already durable (``pending_roll_requests``). An adjudicating
turn in flight was not: its work lived only in memory until its outer
transaction committed. A lease makes it durable so a shared rule change
cannot activate underneath it:

1. :func:`acquire` commits a lease row in its **own** transaction before the
   turn reads any subject binding;
2. the turn's outer transaction deletes it (:func:`release`) atomically with
   the turn's own commit, and the rollback cleanup deletes it too.

SQLite admits one writer at a time, so either the lease commits first and
activation sees it and holds, or activation commits first and the turn then
reads a binding that is no longer current and refuses before doing any work.

:func:`clear_orphans` runs once at application start. The application runs a
single worker (the per-story lock is in-process), so a lease present at start
belongs to a turn that never committed: no event exists behind it. Clearing it
recovers a lease, never a pending roll; pending rolls are never cancelled or
expired.
"""

from __future__ import annotations

from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlalchemy.orm import Session, sessionmaker

from afterworlds.persistence.orm.dnd5e_state import RpgTurnLeaseORM

__all__ = ["acquire", "clear_orphans", "release", "release_committed"]


def acquire(factory: sessionmaker[Session], story_id: UUID, *, now: str) -> str:
    """Commit a lease for *story_id* in its own transaction; return its id."""
    lease_id = str(uuid4())
    with factory() as session, session.begin():
        session.add(
            RpgTurnLeaseORM(lease_id=lease_id, story_id=str(story_id), started_at=now)
        )
    return lease_id


def release(session: Session, lease_id: str) -> None:
    """Delete a lease inside the caller's transaction."""
    session.execute(
        sa.delete(RpgTurnLeaseORM).where(RpgTurnLeaseORM.lease_id == lease_id)
    )


def release_committed(factory: sessionmaker[Session], lease_id: str) -> None:
    """Delete a lease in its own transaction (rollback cleanup)."""
    with factory() as session, session.begin():
        release(session, lease_id)


def clear_orphans(factory: sessionmaker[Session]) -> int:
    """At application start, delete leases no running turn can own."""
    with factory() as session, session.begin():
        result = session.execute(sa.delete(RpgTurnLeaseORM))
        return int(result.rowcount)  # type: ignore[attr-defined]
