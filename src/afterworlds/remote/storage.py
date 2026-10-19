"""Remote storage boundary -- prerequisite #205 §4/§5 (ADR-021 D5-D7, D10).

* deletion-suppression instructions (the authoritative input CRD Issue 22
  supplies) and their backup deadlines;
* the backup inventory, whose 21-day lifetime runs from original capture and
  survives copies and restores;
* the restore gate: a restored content store is not served until both stores
  were replaced (write-ahead ``copying`` state) and every active suppression
  is enforced and verified;
* the fresh-store rule, the vector-store binding and the single-writer locks
  on both physical stores.

Coverage is proof-based: a backup is clear of a suppression only if the
capture proved the suppressed content absent from both stores; capture
refuses while that proof is impossible. Every maintenance step records its
state before touching files, so an interrupted capture/restore/disposal
leaves inventoried, retryable state rather than untracked data.

All state lives in the control store, outside the content snapshot.
"""

from __future__ import annotations

import json
import os
import shutil
import sqlite3
from collections.abc import Callable, Iterable, Iterator
from contextlib import closing, contextmanager
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


_UNFINISHED_RESTORE = ("copying", "pending_enforcement")
#: The deployment-binding marker and serve lock inside the vector directory,
#: and the snapshot subdirectory holding the copied vector store.
VECTOR_MARKER = "afterworlds-deployment.json"
VECTOR_LOCK = ".afterworlds-serve.lock"
SNAPSHOT_VECTOR_DIR = "chroma"


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

    Low-level writer. CRD Issue 22 must call
    :func:`afterworlds.remote.access.record_suppression_fenced`, the only
    supported entry point: calling this directly bypasses the account fence.

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
    clean_suppression_ids: Iterable[str] = (),
) -> str:
    """Inventory a backup. ``clean_suppression_ids`` names the active
    suppressions whose content the capture proved absent from both stores."""
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
                clean_suppression_ids=json.dumps(sorted(set(clean_suppression_ids))),
            )
        )
    return backup_id


def set_backup_status(
    control: sessionmaker[Session], backup_id: str, verification_status: str
) -> None:
    with control.begin() as s:
        row = s.get(BackupInventoryORM, backup_id)
        if row is None:
            raise KeyError(backup_id)
        row.verification_status = verification_status


def copy_backup(
    control: sessionmaker[Session], backup_id: str, *, storage_locator: str
) -> str:
    """Inventory a copy. It keeps the original capture time, expiry and proof."""
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
                clean_suppression_ids=source.clean_suppression_ids,
            )
        )
    return copy_id


#: Proof that a backup's copy is gone: removed by the disposal, or verified
#: absent under a readable parent. Nothing else satisfies a disposal.
DISPOSAL_EVIDENCE = frozenset({"removed", "verified_absent"})


def dispose_backup(
    control: sessionmaker[Session], backup_id: str, *, now: datetime, evidence: str
) -> None:
    """Record a proven disposal. ``verification_status`` keeps describing the
    capture (for instance ``unverified`` for an interrupted one); the disposal
    evidence is what discharges the backup's obligations."""
    if evidence not in DISPOSAL_EVIDENCE:
        raise ValueError(f"not disposal evidence: {evidence!r}")
    with control.begin() as s:
        row = s.get(BackupInventoryORM, backup_id)
        if row is None:
            raise KeyError(backup_id)
        if row.disposed_at is None:
            row.disposed_at = iso(now)
            row.disposal_evidence = evidence


def _disposed(row: BackupInventoryORM) -> bool:
    return row.disposed_at is not None and row.disposal_evidence in DISPOSAL_EVIDENCE


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

    A backup is clear of the suppression only if its capture proved that
    content absent (``clean_suppression_ids``); capture time alone proves
    nothing. Every other backup is affected until disposed. An inaccessible
    or unverified entry never counts as disposed: unverified coverage is a
    failure, not presumed compliance.
    """
    with control() as s:
        sup = s.get(DeletionSuppressionORM, suppression_id)
        if sup is None:
            raise KeyError(suppression_id)
        deadline = parse_iso(sup.backup_horizon_at)
        affected = [
            row
            for row in s.scalars(sa.select(BackupInventoryORM))
            if suppression_id not in json.loads(row.clean_suppression_ids)
        ]
    # A proven disposal discharges the obligation, whatever the capture's own
    # status was; an undisposed copy that is not verified is unverified.
    pending = tuple(r.backup_id for r in affected if not _disposed(r))
    unverified = tuple(
        r.backup_id
        for r in affected
        if not _disposed(r) and r.verification_status != "verified"
    )
    complete = not pending and not unverified
    return BackupDisposition(
        deadline=deadline,
        pending_backup_ids=pending,
        unverified_backup_ids=unverified,
        complete=complete,
        overdue=not complete and now >= deadline,
    )


def capture_preconditions(
    control: sessionmaker[Session],
    content: sessionmaker[Session],
    story_chunk_count: Callable[[str], int],
) -> list[str]:
    """Refuse a capture that would copy content already under deletion, and
    return the suppressions the capture is proven clean of (all active ones).
    A pending restore or any suppressed content still present refuses it."""
    if pending_restores(control):
        raise StoreRefused("a restore is pending; capture would copy unverified data")
    remaining = suppressed_content_present(control, content, story_chunk_count)
    if remaining:
        raise StoreRefused(
            "suppressed content is still present ("
            + ", ".join(remaining)
            + "); a backup now would copy it"
        )
    return [sup.suppression_id for sup in active_suppressions(control)]


# -- restore gate -----------------------------------------------------------


def begin_restore(
    control: sessionmaker[Session],
    backup_id: str,
    *,
    live_database: Path,
    now: datetime,
) -> str:
    """Record, before any file is touched, that *backup_id* is being restored
    over *live_database* (state ``copying``); the app will not serve until
    :func:`mark_restore_copied` and :func:`verify_restore` both pass.

    Refused, before anything is recorded or copied, when the backup is
    expired, disposed or unverified (restore never renews its life), when its
    snapshot lacks either store, or when the restore cannot prove
    entitlement-ledger continuity (:func:`check_ledger_continuity`). Any
    earlier unfinished restore is superseded, so a failed attempt can be
    retried.
    """
    with control() as s:
        row = s.get(BackupInventoryORM, backup_id)
        if row is None:
            raise StoreRefused("backup is not inventoried")
        if row.disposed_at is not None or parse_iso(row.expires_at) <= now:
            raise StoreRefused("backup is past its 21-day lifetime or disposed")
        if row.verification_status != "verified":
            raise StoreRefused("backup coverage is unverified")
        locator = Path(row.storage_locator)
        store_id = row.store_id
    with control() as s:
        bound = s.get(DeploymentMarkerORM, 1)
    if bound is None or store_id != bound.content_store_id:
        raise StoreRefused("the backup belongs to a different deployment")
    if read_vector_marker(locator / SNAPSHOT_VECTOR_DIR) != store_id:
        raise StoreRefused("the backup's vector snapshot is missing or not bound")
    if _content_marker(locator / live_database.name) != store_id:
        raise StoreRefused("the backup's content snapshot is missing or not bound")
    check_ledger_continuity(live_database, locator / live_database.name)
    restore_id = str(uuid4())
    with control.begin() as s:
        for old in s.scalars(
            sa.select(RestoreRecordORM).where(
                RestoreRecordORM.status.in_(_UNFINISHED_RESTORE)
            )
        ):
            old.status = "superseded"
        s.add(
            RestoreRecordORM(
                restore_id=restore_id,
                backup_id=backup_id,
                restored_at=iso(now),
                status="copying",
            )
        )
    return restore_id


def mark_restore_copied(control: sessionmaker[Session], restore_id: str) -> None:
    """Both stores were replaced from the snapshot; suppression proof is next."""
    with control.begin() as s:
        row = s.get(RestoreRecordORM, restore_id)
        if row is None or row.status != "copying":
            raise StoreRefused("no restore copy is in progress under that ID")
        row.status = "pending_enforcement"


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
                    RestoreRecordORM.status.in_(_UNFINISHED_RESTORE)
                )
            )
        )


def suppressed_content_present(
    control: sessionmaker[Session],
    content: sessionmaker[Session],
    story_chunk_count: Callable[[str], int],
) -> list[str]:
    """Story IDs under active suppression that still have content.

    Targets are the listed Story IDs plus, for an account-scope instruction,
    every Story the account has ever owned in the store's ownership map
    (retired mappings included: the inventory must not depend on parent
    links). A target remains while any content table with a ``story_id``
    column still has a row for it -- not just ``stories``, since FK cascade
    alone does not prove deletion (ADR-0004 amendment) -- or while it has
    story-memory chunks. ``turns`` carry no ``story_id``: Turns orphaned by
    ``SET NULL`` are attributable only through the pre-detachment inventory
    (``remote.inventory``), which CRD Issue 22's enforcer disposes of first.
    A failing chunk count read propagates: an unavailable read is not zero.
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
    return sorted(
        story for story in targets if story in present or story_chunk_count(story) != 0
    )


def verify_restore(
    control: sessionmaker[Session],
    restore_id: str,
    content: sessionmaker[Session],
    story_chunk_count: Callable[[str], int],
    *,
    now: datetime,
) -> list[str]:
    """Verify a restore whose store replacement completed.

    Refused unless the restore reached ``pending_enforcement`` (both stores
    were replaced): an absence of suppression targets is never evidence of a
    successful restore. Returns the suppressed Story IDs still present; empty
    means verified, and the restore is marked so.
    """
    with control() as s:
        row = s.get(RestoreRecordORM, restore_id)
        if row is None:
            raise KeyError(restore_id)
        if row.status != "pending_enforcement":
            raise StoreRefused(
                f"restore is {row.status}; both stores must be replaced first"
            )
    remaining = suppressed_content_present(control, content, story_chunk_count)
    if not remaining:
        with control.begin() as s:
            record = s.get(RestoreRecordORM, restore_id)
            assert record is not None
            record.status = "verified"
            record.verified_at = iso(now)
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


# -- the vector store: binding and lock --------------------------------------


def read_vector_marker(vector_dir: Path) -> str | None:
    marker = vector_dir / VECTOR_MARKER
    if not marker.is_file():
        return None
    try:
        return str(json.loads(marker.read_text(encoding="utf-8"))["content_store_id"])
    except (OSError, ValueError, KeyError):
        return None


def _vector_dir_is_empty(vector_dir: Path) -> bool:
    if not vector_dir.exists():
        return True
    return all(p.name in (VECTOR_LOCK,) for p in vector_dir.iterdir())


def check_vector_store(vector_dir: Path, control: sessionmaker[Session]) -> None:
    """Refuse a vector directory that is not this deployment's (ADR-021 D7).

    Allowed: absent/empty (a fresh deployment, bound at initialization) or
    carrying this deployment's marker. A directory holding unmarked or
    another deployment's data -- local, test or another remote store -- is
    refused untouched; it is never adopted. A bound deployment whose vector
    directory has gone missing is refused too."""
    with control() as s:
        bound = s.get(DeploymentMarkerORM, 1)
    marker = read_vector_marker(vector_dir)
    if bound is None:
        if marker is not None or not _vector_dir_is_empty(vector_dir):
            raise StoreRefused(
                "the vector store holds data that does not belong to this new "
                "deployment; remote stores never import local or test data"
            )
        return
    if marker != bound.content_store_id:
        raise StoreRefused(
            "the vector store is missing or belongs to a different deployment"
        )


def bind_vector_store(vector_dir: Path, store_id: str) -> None:
    vector_dir.mkdir(parents=True, exist_ok=True)
    (vector_dir / VECTOR_MARKER).write_text(
        json.dumps({"content_store_id": store_id}), encoding="utf-8"
    )


def acquire_vector_lock(vector_dir: Path) -> IO[bytes]:
    """Exclusive lock on the physical vector store, held with the content
    lock, so two deployments can never write one embedded Chroma."""
    vector_dir.mkdir(parents=True, exist_ok=True)
    handle = (vector_dir / VECTOR_LOCK).open("a+b")
    if not _try_lock(handle):
        handle.close()
        raise StoreRefused(
            "another process is serving or maintaining this vector store"
        )
    return handle


# -- maintenance operations (storage_cli and tests use these) ----------------


@contextmanager
def maintenance_locks(
    database_url: str,
    vector_dir: Path,
    control: sessionmaker[Session],
    *,
    touches_live_stores: bool = True,
) -> Iterator[None]:
    """Hold both physical stores' locks: no maintenance or job runs beside a
    serving app. Work that touches the live stores also requires the content,
    control and vector stores to be one deployment's. Backup expiry and
    disposal touch only backup copies and the control store, so they need
    just the control binding and stay possible while a live store is damaged
    (the 21-day obligation must remain enforceable during an outage)."""
    content_lock = acquire_store_lock(database_url)
    try:
        vector_lock = acquire_vector_lock(vector_dir)
        try:
            if touches_live_stores:
                check_store_pairing(database_url, vector_dir, control)
            else:
                with control() as s:
                    if s.get(DeploymentMarkerORM, 1) is None:
                        raise StoreRefused(
                            "the control store is not bound to a deployment"
                        )
            yield
        finally:
            vector_lock.close()
    finally:
        content_lock.close()


def _content_marker(path: Path, *, live: bool = False) -> str | None:
    """The ``remote_store_marker`` of a SQLite file; None if absent or unmarked.

    A snapshot is opened read-only. A *live* store is opened normally, like
    :func:`_ledger`: after an unclean stop it may hold WAL frames a read-only
    connection cannot read; an unreadable live store raises rather than being
    reported as foreign."""
    if not path.is_file():
        return None
    target = str(path) if live else f"file:{path.as_posix()}?mode=ro"
    try:
        with closing(sqlite3.connect(target, uri=not live)) as conn:
            row = conn.execute(
                "SELECT content_store_id FROM remote_store_marker WHERE id = 1"
            ).fetchone()
    except sqlite3.Error:
        if live:
            raise StoreRefused("the live content store is unreadable") from None
        return None
    return str(row[0]) if row else None


def check_store_pairing(
    database_url: str, vector_dir: Path, control: sessionmaker[Session]
) -> None:
    """Maintenance may touch data only when the configured content store, the
    control store and the vector store all belong to one deployment. Locking a
    file proves exclusivity, not ownership."""
    with control() as s:
        bound = s.get(DeploymentMarkerORM, 1)
    if bound is None:
        raise StoreRefused("the control store is not bound to a deployment")
    if _content_marker(sqlite_path(database_url), live=True) != (
        bound.content_store_id
    ):
        raise StoreRefused("the content store belongs to a different deployment")
    check_vector_store(vector_dir, control)


def capture_snapshot(
    control: sessionmaker[Session],
    content: sessionmaker[Session],
    *,
    database_path: Path,
    vector_dir: Path,
    target: Path,
    story_chunk_count: Callable[[str], int],
    now: datetime,
) -> str:
    """Snapshot both stores into *target* and inventory it.

    The inventory row (``unverified``, original capture time, the proven-clean
    suppressions) is written before any file, and becomes ``verified`` only
    after both copies complete; an interrupted capture stays inventoried and
    counts as unverified coverage."""
    clean = capture_preconditions(control, content, story_chunk_count)
    store_id = content_store_id(content)
    # Claim a new, empty directory before inventorying it: an existing path
    # is refused untouched, so a later disposal can never remove data this
    # capture did not create. A failure between here and registration leaves
    # only an empty directory.
    try:
        target.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        raise StoreRefused(f"capture target {target} already exists") from None
    backup_id = register_backup(
        control,
        store_id=store_id,
        storage_locator=str(target),
        original_capture_at=now,
        verification_status="unverified",
        clean_suppression_ids=clean,
    )
    with (
        closing(sqlite3.connect(database_path)) as src,
        closing(sqlite3.connect(target / database_path.name)) as dst,
    ):
        src.backup(dst)
    shutil.copytree(
        vector_dir,
        target / SNAPSHOT_VECTOR_DIR,
        ignore=shutil.ignore_patterns(VECTOR_LOCK),
    )
    if read_vector_marker(target / SNAPSHOT_VECTOR_DIR) != store_id:
        raise StoreRefused("the copied vector store is not bound to this deployment")
    set_backup_status(control, backup_id, "verified")
    return backup_id


def restore_snapshot(
    control: sessionmaker[Session],
    backup_id: str,
    *,
    database_path: Path,
    vector_dir: Path,
    now: datetime,
) -> str:
    """Replace both stores from *backup_id*. Recorded as ``copying`` first and
    marked copied only after both replacements finish; a failure leaves the
    restore unfinished (the app refuses to serve) and a retry supersedes it."""
    restore_id = begin_restore(control, backup_id, live_database=database_path, now=now)
    with control() as s:
        row = s.get(BackupInventoryORM, backup_id)
        assert row is not None
        source = Path(row.storage_locator)
    # The live path holds either the old store or the complete snapshot,
    # never a partial file: checkpoint and empty the live WAL, stage the copy
    # beside it, then swap atomically. Both carry this deployment's identity,
    # so an interruption anywhere leaves a store the documented retry accepts.
    if database_path.is_file():
        with closing(sqlite3.connect(database_path)) as conn:
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    staged = database_path.with_name(database_path.name + ".restoring")
    shutil.copyfile(source / database_path.name, staged)
    os.replace(staged, database_path)
    for suffix in ("-wal", "-shm"):
        database_path.with_name(database_path.name + suffix).unlink(missing_ok=True)
    # Keep the held lock file; replace everything else in the vector store.
    # The held lock file and the deployment marker are never removed: the
    # snapshot's marker is the same binding (checked by begin_restore), so an
    # interrupted cleanup leaves a store this deployment can still maintain.
    for child in vector_dir.iterdir():
        if child.name in (VECTOR_LOCK, VECTOR_MARKER):
            continue
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()
    shutil.copytree(source / SNAPSHOT_VECTOR_DIR, vector_dir, dirs_exist_ok=True)
    mark_restore_copied(control, restore_id)
    return restore_id


def dispose_snapshot(
    control: sessionmaker[Session], backup_id: str, *, now: datetime
) -> None:
    """Remove a backup's files, then record the disposal. Retry-safe: a path
    already gone is recorded as disposed only when its parent is readable
    (verified absence); any access failure marks it ``inaccessible``."""
    with control() as s:
        row = s.get(BackupInventoryORM, backup_id)
        if row is None:
            raise KeyError(backup_id)
        locator = Path(row.storage_locator)
    try:
        if locator.exists():
            shutil.rmtree(locator)
            evidence = "removed"
        elif locator.parent.is_dir():
            evidence = "verified_absent"
        else:
            raise OSError(f"cannot verify that {locator} is absent")
        if locator.exists():
            raise OSError(f"{locator} is still present")
    except OSError:
        set_backup_status(control, backup_id, "inaccessible")
        raise StoreRefused("the backup could not be verified as removed") from None
    dispose_backup(control, backup_id, now=now, evidence=evidence)
