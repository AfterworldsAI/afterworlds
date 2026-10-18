"""Operator commands for the remote store/backup/restore boundary (ADR-021 D10).

Every command takes the content-store lock, so none runs while the app serves::

    python -m afterworlds.remote.storage_cli capture --to DIR
    python -m afterworlds.remote.storage_cli restore --backup-id ID
    python -m afterworlds.remote.storage_cli verify-restore --restore-id ID
    python -m afterworlds.remote.storage_cli due

``capture`` snapshots the content SQLite store (online backup API) and the
Chroma directory and inventories them with their capture time. ``restore``
copies an inventoried, unexpired snapshot back and records a pending restore:
the app refuses to start until ``verify-restore`` confirms every active
deletion suppression holds (CRD Issue 22 supplies the enforcement). ``due``
lists backups past their 21-day lifetime. Configuration comes from the same
environment variables as the app.
"""

from __future__ import annotations

import argparse
import shutil
import sqlite3
import sys
from contextlib import closing
from pathlib import Path
from uuid import UUID

from afterworlds.api.config import load_settings
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.pipeline.retrieval.client import build_chroma_client
from afterworlds.pipeline.retrieval.config import RetrievalMemoryConfig
from afterworlds.pipeline.retrieval.write_service import RetrievalMemoryWriteService
from afterworlds.remote.control_orm import BackupInventoryORM
from afterworlds.remote.control_store import open_control_store, utc_now
from afterworlds.remote.storage import (
    acquire_store_lock,
    begin_restore,
    content_store_id,
    due_backups,
    register_backup,
    sqlite_path,
    verify_restore,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Remote storage operations")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("capture").add_argument("--to", required=True, type=Path)
    sub.add_parser("restore").add_argument("--backup-id", required=True)
    sub.add_parser("verify-restore").add_argument("--restore-id", required=True)
    sub.add_parser("due")
    args = parser.parse_args(argv)

    settings = load_settings()
    if settings.deployment != "remote" or settings.control_database_url is None:
        parser.error("requires AFTERWORLDS_DEPLOYMENT=remote and a control store")
    lock = acquire_store_lock(settings.database_url)
    try:
        control = open_control_store(settings.control_database_url)
        content = create_session_factory(create_engine(settings.database_url))
        db_path = sqlite_path(settings.database_url)
        chroma_dir = Path(RetrievalMemoryConfig.from_env().persist_directory)
        now = utc_now()
        if args.command == "capture":
            target: Path = args.to
            target.mkdir(parents=True, exist_ok=False)
            with (
                closing(sqlite3.connect(db_path)) as src,
                closing(sqlite3.connect(target / db_path.name)) as dst,
            ):
                src.backup(dst)
            if chroma_dir.is_dir():
                shutil.copytree(chroma_dir, target / "chroma")
            backup_id = register_backup(
                control,
                store_id=content_store_id(content),
                storage_locator=str(target),
                original_capture_at=now,
            )
            print(backup_id)
        elif args.command == "restore":
            with control() as s:
                row = s.get(BackupInventoryORM, args.backup_id)
            if row is None:
                print("backup is not inventoried", file=sys.stderr)
                return 1
            restore_id = begin_restore(control, args.backup_id, now=now)
            source = Path(row.storage_locator)
            shutil.copyfile(source / db_path.name, db_path)
            for suffix in ("-wal", "-shm"):
                db_path.with_name(db_path.name + suffix).unlink(missing_ok=True)
            if (source / "chroma").is_dir():
                shutil.rmtree(chroma_dir, ignore_errors=True)
                shutil.copytree(source / "chroma", chroma_dir)
            print(restore_id)
        elif args.command == "verify-restore":
            config = RetrievalMemoryConfig.from_env()
            writes = RetrievalMemoryWriteService(build_chroma_client(config), config)
            remaining = verify_restore(
                control,
                args.restore_id,
                content,
                lambda story: writes.count_for_story(UUID(story)),
                now=now,
            )
            if remaining:
                print("suppressed stories still present: " + ", ".join(remaining))
                return 2
            print("verified")
        else:
            for backup_id in due_backups(control, now=now):
                print(backup_id)
    finally:
        lock.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
