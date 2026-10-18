"""Remote storage boundary -- prerequisite #205 §4/§5 (ADR-021 D5-D7, D10).

* deletion-suppression instructions (the authoritative input CRD Issue 22
  supplies) and their backup deadlines;
* the backup inventory, whose 21-day lifetime runs from original capture and
  survives copies and restores;
* the restore gate: a restored content store is not served until every active
  suppression is enforced and verified;
* the fresh-store rule and the single-writer store lock.

All state lives in the control store, outside the content snapshot.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Callable, Iterable
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import IO
from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

from afterworlds.persistence.orm.ownership import (
    AccountResourceORM,
    RemoteStoreMarkerORM,
)
from afterworlds.remote.control_orm import (
    BackupInventoryORM,
    DeletionSuppressionORM,
    DeploymentMarkerORM,
    RestoreRecordORM,
)
from afterworlds.remote.control_store import POLICY_VERSION, iso, parse_iso
from afterworlds.services.dnd5e_state.leases import _try_lock

#: D4: every backup's rolling lifetime from its original capture.
BACKUP_LIFETIME = timedelta(days=21)
#: D4: overall limit for affected-backup disposal after a confirmed deletion.
DELETION_BACKUP_DEADLINE = timedelta(days=30)
ANNUAL_REVIEW = timedelta(days=365)


class StoreRefused(RuntimeError):
    """The remote deployment refuses to serve this store combination."""


# -- deletion suppression ---------------------------------------------------


@dataclass(frozen=True)
class Suppression:
    suppression_id: str
    subject_ref: str
    story_refs: frozenset[str]
    scope: str
    effective_boundary_at: datetime
    backup_horizon_at: datetime


def record_suppression(
    control: sessionmaker[Session],
    *,
    subject_ref: str,
    story_refs: Iterable[str],
    request_id: str,
    scope: str,
    effective_boundary_at: datetime,
    now: datetime,
) -> str:
    """Accept an authoritative deletion-suppression instruction.

    The backup horizon is the overall 30-day limit from the confirmed request
    boundary -- not 30 days after live deletion.
    """
    if scope not in ("story", "account"):
        raise ValueError(f"unsupported suppression scope {scope!r}")
    suppression_id = str(uuid4())
    with control.begin() as s:
        s.add(
            DeletionSuppressionORM(
                suppression_id=suppression_id,
                schema_version=1,
                subject_ref=subject_ref,
                story_refs=json.dumps(sorted(set(story_refs))),
                request_id=request_id,
                scope=scope,
                effective_boundary_at=iso(effective_boundary_at),
                policy_version=POLICY_VERSION,
                created_at=iso(now),
                backup_horizon_at=iso(effective_boundary_at + DELETION_BACKUP_DEADLINE),
                status="active",
                annual_review_at=iso(now + ANNUAL_REVIEW),
            )
        )
    return suppression_id


def active_suppressions(control: sessionmaker[Session]) -> list[Suppression]:
    # shortcut: loads every active suppression per call; index story_refs in a
    # side table once suppression counts grow beyond a small operational set.
    with control() as s:
        rows = s.scalars(
            sa.select(DeletionSuppressionORM).where(
                DeletionSuppressionORM.status == "active"
            )
        ).all()
        return [
            Suppression(
                suppression_id=row.suppression_id,
                subject_ref=row.subject_ref,
                story_refs=frozenset(json.loads(row.story_refs)),
                scope=row.scope,
                effective_boundary_at=parse_iso(row.effective_boundary_at),
                backup_horizon_at=parse_iso(row.backup_horizon_at),
            )
            for row in rows
        ]


def is_suppressed(
    control: sessionmaker[Session], *, story_id: str, account_id: str | None
) -> bool:
    """A Story is suppressed if named by an active instruction, or if its
    owning account is under an active account-scope instruction."""
    return any(
        story_id in sup.story_refs
        or (sup.scope == "account" and sup.subject_ref == account_id)
        for sup in active_suppressions(control)
    )


# -- backup inventory -------------------------------------------------------


def register_backup(
    control: sessionmaker[Session],
    *,
    store_id: str,
    storage_locator: str,
    original_capture_at: datetime,
    class_code: str = "content_snapshot",
    verification_status: str = "verified",
) -> str:
    backup_id = str(uuid4())
    with control.begin() as s:
        s.add(
            BackupInventoryORM(
                backup_id=backup_id,
                store_id=store_id,
                storage_locator=storage_locator,
                class_code=class_code,
                original_capture_at=iso(original_capture_at),
                policy_version=POLICY_VERSION,
                expires_at=iso(original_capture_at + BACKUP_LIFETIME),
                verification_status=verification_status,
            )
        )
    return backup_id


def copy_backup(
    control: sessionmaker[Session], backup_id: str, *, storage_locator: str
) -> str:
    """Inventory a copy. It keeps the original capture time and expiry."""
    with control.begin() as s:
        source = s.get(BackupInventoryORM, backup_id)
        if source is None:
            raise KeyError(backup_id)
        copy_id = str(uuid4())
        s.add(
            BackupInventoryORM(
                backup_id=copy_id,
                store_id=source.store_id,
                storage_locator=storage_locator,
                class_code=source.class_code,
                original_capture_at=source.original_capture_at,
                copied_from_backup_id=source.backup_id,
                policy_version=source.policy_version,
                expires_at=source.expires_at,
                verification_status=source.verification_status,
            )
        )
    return copy_id


def dispose_backup(
    control: sessionmaker[Session], backup_id: str, *, now: datetime
) -> None:
    with control.begin() as s:
        row = s.get(BackupInventoryORM, backup_id)
        if row is None:
            raise KeyError(backup_id)
        row.disposed_at = row.disposed_at or iso(now)


def due_backups(control: sessionmaker[Session], *, now: datetime) -> list[str]:
    """Undisposed backups at or past their 21-day expiry: dispose them now."""
    with control() as s:
        return [
            row.backup_id
            for row in s.scalars(
                sa.select(BackupInventoryORM).where(
                    BackupInventoryORM.disposed_at.is_(None)
                )
            )
            if parse_iso(row.expires_at) <= now
        ]


@dataclass(frozen=True)
class BackupDisposition:
    """Backup obligations of one suppression (CRD Issue 22 final completion)."""

    deadline: datetime
    pending_backup_ids: tuple[str, ...]
    unverified_backup_ids: tuple[str, ...]
    complete: bool
    overdue: bool


def backup_disposition(
    control: sessionmaker[Session], suppression_id: str, *, now: datetime
) -> BackupDisposition:
    """Which inventoried backups may still hold the suppressed content.

    Any backup captured at or before the deletion boundary is affected until
    disposed. An inaccessible or unverified entry never counts as disposed:
    unverified coverage is a failure, not presumed compliance.
    """
    with control() as s:
        sup = s.get(DeletionSuppressionORM, suppression_id)
        if sup is None:
            raise KeyError(suppression_id)
        boundary = parse_iso(sup.effective_boundary_at)
        deadline = parse_iso(sup.backup_horizon_at)
        affected = [
            row
            for row in s.scalars(sa.select(BackupInventoryORM))
            if parse_iso(row.original_capture_at) <= boundary
        ]
    pending = tuple(r.backup_id for r in affected if r.disposed_at is None)
    unverified = tuple(
        r.backup_id for r in affected if r.verification_status != "verified"
    )
    complete = not pending and not unverified
    return BackupDisposition(
        deadline=deadline,
        pending_backup_ids=pending,
        unverified_backup_ids=unverified,
        complete=complete,
        overdue=not complete and now >= deadline,
    )


# -- restore gate -----------------------------------------------------------


def begin_restore(
    control: sessionmaker[Session],
    backup_id: str,
    *,
    live_database: Path,
    now: datetime,
) -> str:
    """Record that *backup_id* is being restored over *live_database*; the app
    will not serve the content store until :func:`verify_restore` passes.

    Refused, before anything is copied, when the backup is expired, disposed or
    unverified (restore never renews its life), or when the restore cannot
    prove entitlement-ledger continuity (:func:`check_ledger_continuity`).
    """
    with control() as s:
        row = s.get(BackupInventoryORM, backup_id)
        if row is None:
            raise StoreRefused("backup is not inventoried")
        if row.disposed_at is not None or parse_iso(row.expires_at) <= now:
            raise StoreRefused("backup is past its 21-day lifetime or disposed")
        if row.verification_status != "verified":
            raise StoreRefused("backup coverage is unverified")
        snapshot = Path(row.storage_locator) / live_database.name
    check_ledger_continuity(live_database, snapshot)
    restore_id = str(uuid4())
    with control.begin() as s:
        s.add(
            RestoreRecordORM(
                restore_id=restore_id,
                backup_id=backup_id,
                restored_at=iso(now),
                status="pending_enforcement",
            )
        )
    return restore_id


def _ledger(path: Path, *, read_only: bool) -> list[tuple[int, str]]:
    target = f"file:{path.as_posix()}?mode=ro" if read_only else str(path)
    with closing(sqlite3.connect(target, uri=read_only)) as conn:
        return [
            (int(seq), str(event_id))
            for seq, event_id in conn.execute(
                "SELECT global_sequence, event_id FROM entitlement_event"
                " ORDER BY global_sequence"
            )
        ]


def check_ledger_continuity(live_database: Path, snapshot: Path) -> None:
    """Refuse a restore that would rewind the entitlement ledger.

    ``entitlement_event`` is append-only accounting authority (ADR-013) kept in
    the content store, so a snapshot may be restored only if the live ledger is
    a prefix of the snapshot's, in the same ``global_sequence`` order with the
    same event IDs. A live store that is missing or unreadable cannot prove
    that, so it is refused too. Nothing is carried forward or rebuilt: deciding
    how an unprovable restore is accepted is not this hook's to make.
    """
    if not snapshot.is_file():
        raise StoreRefused("the backup's content snapshot is missing")
    try:
        restored = _ledger(snapshot, read_only=True)
    except sqlite3.Error:
        raise StoreRefused("the backup's entitlement ledger is unreadable") from None
    if not live_database.is_file():
        raise StoreRefused(
            "the live content store is missing, so entitlement-ledger "
            "continuity cannot be proven"
        )
    try:
        # Not read-only: the stopped live store may still hold WAL frames,
        # which a read-only connection without its -shm file cannot read.
        live = _ledger(live_database, read_only=False)
    except sqlite3.Error:
        raise StoreRefused(
            "the live entitlement ledger is unreadable, so continuity cannot "
            "be proven"
        ) from None
    if restored[: len(live)] != live[: len(restored)]:
        raise StoreRefused("the backup's entitlement ledger diverges from the live one")
    if len(live) > len(restored):
        raise StoreRefused(
            f"restoring would discard {len(live) - len(restored)} entitlement "
            "event(s) recorded after the backup was captured"
        )


def pending_restores(control: sessionmaker[Session]) -> list[str]:
    with control() as s:
        return list(
            s.scalars(
                sa.select(RestoreRecordORM.restore_id).where(
                    RestoreRecordORM.status == "pending_enforcement"
                )
            )
        )


def verify_restore(
    control: sessionmaker[Session],
    restore_id: str,
    content: sessionmaker[Session],
    story_chunk_count: Callable[[str], int],
    *,
    now: datetime,
) -> list[str]:
    """Verify every active suppression holds in the restored stores.

    Targets are the listed Story IDs plus, for an account-scope instruction,
    every Story the account has ever owned in the restored store's ownership
    map (retired mappings included: the inventory must not depend on parent
    links). A target remains while any content table with a ``story_id``
    column still has a row for it -- not just ``stories``, since FK cascade
    alone does not prove deletion (ADR-0004 amendment) -- or while it has
    story-memory chunks. ``turns`` carry no ``story_id``: Turns orphaned by
    ``SET NULL`` are attributable only through CRD Issue 22's pre-detachment
    inventory, which its enforcer must dispose of before this check.

    Returns the Story IDs still present; empty means verified, and the
    restore is marked so. A failing chunk count read propagates: an
    unavailable read is not proof of zero.
    """
    suppressions = active_suppressions(control)
    targets = {story for sup in suppressions for story in sup.story_refs}
    accounts = {sup.subject_ref for sup in suppressions if sup.scope == "account"}
    present: set[str] = set()
    with content() as s:
        if accounts:
            targets |= set(
                s.scalars(
                    sa.select(AccountResourceORM.resource_id).where(
                        AccountResourceORM.account_id.in_(accounts),
                        AccountResourceORM.resource_type == "story",
                    )
                )
            )
        inspector = sa.inspect(s.get_bind())
        for table in inspector.get_table_names():
            columns = {c["name"] for c in inspector.get_columns(table)}
            if "story_id" not in columns or not targets:
                continue
            present |= set(
                s.scalars(
                    sa.select(sa.column("story_id"))
                    .select_from(sa.table(table))
                    .where(sa.column("story_id").in_(targets))
                    .distinct()
                )
            )
    remaining = sorted(
        story for story in targets if story in present or story_chunk_count(story) != 0
    )
    if not remaining:
        with control.begin() as s:
            row = s.get(RestoreRecordORM, restore_id)
            if row is None:
                raise KeyError(restore_id)
            row.status = "verified"
            row.verified_at = iso(now)
            for sup in s.scalars(
                sa.select(DeletionSuppressionORM).where(
                    DeletionSuppressionORM.status == "active"
                )
            ):
                sup.last_verified_at = iso(now)
    return remaining


# -- fresh remote store and the single-writer lock ---------------------------


def sqlite_path(database_url: str) -> Path:
    url = make_url(database_url)
    if url.get_backend_name() != "sqlite" or url.database in (None, "", ":memory:"):
        raise StoreRefused("the remote deployment requires a file-backed SQLite store")
    return Path(str(url.database)).resolve()


def acquire_store_lock(database_url: str) -> IO[bytes]:
    """Hold an exclusive OS lock for the life of the serving process (D6).

    A second app process, or a restore while the app runs, fails here.
    """
    path = sqlite_path(database_url)
    lock_path = path.with_name(path.name + ".serve.lock")
    handle = lock_path.open("a+b")
    if not _try_lock(handle):
        handle.close()
        raise StoreRefused(
            "another process is serving or maintaining this content store"
        )
    return handle


_FOREIGN_DATA_TABLES = ("sojourner_identity", "stories", "entitlement_event")


def check_content_store_before_migration(
    database_url: str, control: sessionmaker[Session]
) -> bool:
    """Refuse a pre-existing store not initialized for this deployment (D7).

    Runs before any migration so a refused store is never modified. Returns
    True when the content store must be initialized (brand new).
    """
    path = sqlite_path(database_url)
    with control() as s:
        bound = s.get(DeploymentMarkerORM, 1)
    tables: set[str] = set()
    if path.exists():
        with closing(sqlite3.connect(path)) as conn:
            tables = {
                name
                for (name,) in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
            marker = (
                conn.execute(
                    "SELECT content_store_id FROM remote_store_marker WHERE id = 1"
                ).fetchone()
                if "remote_store_marker" in tables
                else None
            )
    else:
        marker = None
    if not tables:
        if bound is not None:
            raise StoreRefused(
                "the control store is bound to a content store that is missing"
            )
        return True
    if marker is None:
        raise StoreRefused(
            "the content store was not initialized for this remote deployment; "
            "remote stores never import local or test data"
        )
    if bound is None or bound.content_store_id != marker[0]:
        raise StoreRefused("the content store belongs to a different deployment")
    return False


def initialize_remote_content_store(
    content: sessionmaker[Session], control: sessionmaker[Session], *, now: datetime
) -> str:
    """Mark a freshly migrated, empty content store as this deployment's."""
    with content.begin() as s:
        for table in _FOREIGN_DATA_TABLES:
            if s.execute(sa.text(f"SELECT 1 FROM {table} LIMIT 1")).first():
                raise StoreRefused(f"a fresh remote store must be empty ({table})")
        store_id = str(uuid4())
        s.add(
            RemoteStoreMarkerORM(
                id=1, content_store_id=store_id, initialized_at=iso(now)
            )
        )
    with control.begin() as s:
        s.add(
            DeploymentMarkerORM(
                id=1, content_store_id=store_id, initialized_at=iso(now)
            )
        )
    return store_id


def content_store_id(content: sessionmaker[Session]) -> str:
    with content() as s:
        marker = s.get(RemoteStoreMarkerORM, 1)
        if marker is None:
            raise StoreRefused("content store has no remote marker")
        return marker.content_store_id
