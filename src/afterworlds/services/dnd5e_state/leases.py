"""Durable in-flight turn leases — the in-progress adjudication marker.

An unresolved action-resolution sequence is already durable (CRD Issue 15b:
``action_resolution_sequences``). An adjudicating
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

Recovery needs proof, not an assumption
---------------------------------------
A lease left by a process that stopped mid-turn marks no event, and would
hold every affected rule change forever. Nothing about a single configured
worker proves that another process is not using the same database, so
:func:`clear_orphans` deletes a lease only when its **owner is proven dead**:

* each process that takes a lease is an *owner* with its own id, recorded on
  every lease it takes, and holds an exclusive OS lock on a sidecar file
  ``<database>.turn-owners/<owner>.owner`` for as long as it lives. The OS
  releases that lock when the process ends, however it ends;
* recovery deletes an owner's leases only if it can take that owner's lock
  itself, and it **holds that lock until the deletion has committed**: the
  proof stays valid for the whole transaction. A lock it cannot take belongs
  to a live process; the leases stay. An owner still starting (file created,
  not yet locked) that meets a held proof cannot lock its file, so its
  :func:`acquire` refuses before writing any lease; it never becomes live
  underneath a deletion. After the commit, recovery removes only the files
  of owners whose leases it deleted: those owners had locked their file, so
  they were real and are proven dead. A file whose owner had no lease is
  kept, because it may belong to an owner still starting that could yet lock
  it and lease; removing it would leave that owner's later leases without a
  proof. Removal is best-effort and idempotent (a file still open elsewhere,
  or already removed by a concurrent recovery, is left alone).
  Leases of the recovering process itself stay (another app in this process
  may be mid-turn). Leases whose owner file is missing, or whose database is
  not a file, cannot be proven abandoned and stay.

Recovery never touches a pending roll; pending rolls are never cancelled or
expired.
"""

from __future__ import annotations

import contextlib
import sys
from pathlib import Path
from threading import Lock
from typing import IO
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlalchemy.orm import Session, sessionmaker

from afterworlds.persistence.orm.dnd5e_state import RpgTurnLeaseORM

__all__ = ["acquire", "clear_orphans", "release", "release_committed"]

_SUFFIX = ".owner"
_GUARD = Lock()
#: This process's owner id per owner directory (``None``: no file database).
_OWNERS: dict[Path | None, str] = {}
#: Open, locked owner files; held for the life of the process.
_HANDLES: list[IO[bytes]] = []


def _owner_dir(session: Session) -> Path | None:
    url = session.get_bind().engine.url
    if url.get_backend_name() != "sqlite" or url.database in (None, "", ":memory:"):
        return None
    database = Path(str(url.database)).resolve()
    return database.with_name(database.name + ".turn-owners")


def _try_lock(handle: IO[bytes]) -> bool:
    """Take an exclusive, non-blocking OS lock on *handle*'s first byte."""
    try:
        if sys.platform == "win32":
            import msvcrt

            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return False
    return True


def _owner(session: Session) -> str:
    """This process's owner id for the session's database, created once."""
    directory = _owner_dir(session)
    with _GUARD:
        owner = _OWNERS.get(directory)
        if owner is None:
            owner = str(uuid4())
            if directory is not None:
                directory.mkdir(exist_ok=True)
                handle = (directory / f"{owner}{_SUFFIX}").open("xb")
                if not _try_lock(handle):
                    handle.close()
                    raise RuntimeError(f"cannot lock turn-lease owner file {owner}")
                _HANDLES.append(handle)
            _OWNERS[directory] = owner
    return owner


def acquire(factory: sessionmaker[Session], story_id: UUID, *, now: str) -> str:
    """Commit a lease for *story_id* in its own transaction; return its id."""
    lease_id = str(uuid4())
    with factory() as session, session.begin():
        session.add(
            RpgTurnLeaseORM(
                lease_id=lease_id,
                story_id=str(story_id),
                owner_id=_owner(session),
                started_at=now,
            )
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
    """Delete the leases of owners proven dead; keep every other lease.

    Returns the number of leases recovered.
    """
    recovered = 0
    proofs: list[tuple[Path, IO[bytes], int]] = []
    try:
        with factory() as session, session.begin():
            directory = _owner_dir(session)
            if directory is None or not directory.is_dir():
                return 0
            with _GUARD:
                mine = _OWNERS.get(directory)
            for path in sorted(directory.glob(f"*{_SUFFIX}")):
                owner = path.name.removesuffix(_SUFFIX)
                if owner == mine:
                    continue
                try:
                    handle = path.open("rb")
                except FileNotFoundError:
                    continue  # a concurrent recovery removed it
                if not _try_lock(handle):
                    handle.close()  # a live process holds it
                    continue
                # Unlocked: the lock is held until the deletion commits.
                result = session.execute(
                    sa.delete(RpgTurnLeaseORM).where(RpgTurnLeaseORM.owner_id == owner)
                )
                deleted = int(result.rowcount)  # type: ignore[attr-defined]
                proofs.append((path, handle, deleted))
                recovered += deleted
    finally:
        for _, proof, _ in proofs:
            proof.close()
    for path, _, deleted in proofs:
        # ponytail: unleased owner files are kept (one small file per such
        # process); prune by age if they ever accumulate.
        if deleted:
            with contextlib.suppress(OSError):
                path.unlink(missing_ok=True)
    return recovered
