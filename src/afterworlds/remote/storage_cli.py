"""Operator commands for the remote store/backup/restore boundary (ADR-021 D10).

Every command holds both physical stores' locks (content SQLite and the bound
vector store), so none runs beside a serving app::

    python -m afterworlds.remote.storage_cli capture --to DIR
    python -m afterworlds.remote.storage_cli restore --backup-id ID
    python -m afterworlds.remote.storage_cli verify-restore --restore-id ID
    python -m afterworlds.remote.storage_cli due
    python -m afterworlds.remote.storage_cli dispose --backup-id ID

``capture`` inventories first, then snapshots both stores; it refuses while a
restore is pending or suppressed content is still present. ``restore``
records a ``copying`` restore, replaces both stores and marks them copied;
the app refuses to start until ``verify-restore`` confirms every active
deletion suppression holds (CRD Issue 22 supplies the enforcement). A failed
step leaves inventoried, retryable state. ``due`` lists backups past their
21-day lifetime; ``dispose`` removes one's files, then records the disposal.
Configuration comes from the same environment variables as the app.
"""

from __future__ import annotations

import argparse
import gc
import sys
from collections.abc import Callable
from pathlib import Path

from chromadb.api.shared_system_client import SharedSystemClient

from afterworlds.api.config import load_settings
from afterworlds.operations.compaction import compaction_unfinished
from afterworlds.operations.enforcement import physical_disposal_pending
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.pipeline.retrieval.client import build_chroma_client
from afterworlds.pipeline.retrieval.collections import (
    get_existing_story_memory_collection_for_delete,
)
from afterworlds.pipeline.retrieval.config import RetrievalMemoryConfig
from afterworlds.remote.control_store import (
    ControlStoreUnavailable,
    connect_control_store,
    utc_now,
)
from afterworlds.remote.storage import (
    StoreRefused,
    capture_snapshot,
    dispose_snapshot,
    due_backups,
    maintenance_locks,
    refuse_notice_store_exposure,
    refuse_store_aliasing,
    restore_snapshot,
    sqlite_path,
    verify_restore,
)


def _chunk_counter(config: RetrievalMemoryConfig) -> Callable[[str], int]:
    """Story-memory chunk counts without creating the collection; a missing
    collection is zero, an unreadable one raises (never presumed zero)."""
    client = build_chroma_client(config)

    def count(story_id: str) -> int:
        collection = get_existing_story_memory_collection_for_delete(client)
        if collection is None:
            return 0
        return len(collection.get(where={"story_id": story_id}).get("ids") or [])

    return count


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Remote storage operations")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("capture").add_argument("--to", required=True, type=Path)
    sub.add_parser("restore").add_argument("--backup-id", required=True)
    sub.add_parser("verify-restore").add_argument("--restore-id", required=True)
    sub.add_parser("due")
    sub.add_parser("dispose").add_argument("--backup-id", required=True)
    args = parser.parse_args(argv)

    settings = load_settings()
    if settings.deployment != "remote" or settings.control_database_url is None:
        parser.error("requires AFTERWORLDS_DEPLOYMENT=remote and a control store")
    try:
        refuse_store_aliasing(settings.database_url, settings.control_database_url)
        # due/dispose only remove backups: a misconfiguration must never
        # prevent removing one (even an unsafely placed one).
        if settings.notice_outbox_dir is not None and args.command not in (
            "due",
            "dispose",
        ):
            # capture copies, and restore rewrites, the live vector store
            refuse_notice_store_exposure(
                settings.notice_outbox_dir,
                Path(RetrievalMemoryConfig.from_env().persist_directory),
                settings.frontend_dist_dir,
            )
    except StoreRefused as exc:
        print(f"{args.command} refused: {exc}", file=sys.stderr)
        return 1
    try:
        # Never migrates: a maintenance command opens the existing control
        # store and is refused beside a serving app before any schema change.
        control = connect_control_store(settings.control_database_url)
    except ControlStoreUnavailable as exc:
        print(f"{args.command} refused: {exc}", file=sys.stderr)
        return 1
    now = utc_now()
    if args.command in ("due", "dispose"):
        # Backup-only: control authority and backup storage, never the live
        # content or vector paths (they may be down; the deadlines still run).
        try:
            with maintenance_locks(
                settings.database_url,
                Path(),
                control,
                touches_live_stores=False,
            ):
                try:
                    if args.command == "dispose":
                        dispose_snapshot(control, args.backup_id, now=now)
                        print("disposed")
                    else:
                        for backup_id in due_backups(control, now=now):
                            print(backup_id)
                except (StoreRefused, KeyError) as exc:
                    print(f"{args.command} refused: {exc}", file=sys.stderr)
                    return 1
        finally:
            control.kw["bind"].dispose()
        return 0
    config = RetrievalMemoryConfig.from_env()
    vector_dir = Path(config.persist_directory)
    if compaction_unfinished(vector_dir):
        print(
            f"{args.command} refused: a store compaction did not finish; run "
            "`python -m afterworlds.operations.maintenance compact` again",
            file=sys.stderr,
        )
        return 1
    confidential = [settings.notice_outbox_dir] if settings.notice_outbox_dir else []
    db_path = sqlite_path(settings.database_url)
    with maintenance_locks(
        settings.database_url,
        vector_dir,
        control,
    ):
        engine = create_engine(settings.database_url)
        content = create_session_factory(engine)
        try:
            if args.command == "capture":
                # CRD Issue 22: a capture before physical compaction would copy
                # deleted content in free pages or vector segments.
                pending = physical_disposal_pending(control)
                if pending:
                    raise StoreRefused(
                        "deleted content awaits physical compaction ("
                        + ", ".join(pending)
                        + "); run `python -m afterworlds.operations.maintenance "
                        "compact` first"
                    )
                print(
                    capture_snapshot(
                        control,
                        content,
                        database_path=db_path,
                        vector_dir=vector_dir,
                        target=args.to,
                        story_chunk_count=_chunk_counter(config),
                        now=now,
                        confidential=confidential,
                        public_root=settings.frontend_dist_dir,
                    )
                )
            elif args.command == "restore":
                engine.dispose()  # the live file is about to be replaced
                print(
                    restore_snapshot(
                        control,
                        args.backup_id,
                        database_path=db_path,
                        vector_dir=vector_dir,
                        now=now,
                        confidential=confidential,
                        public_root=settings.frontend_dist_dir,
                    )
                )
            elif args.command == "verify-restore":
                remaining = verify_restore(
                    control,
                    args.restore_id,
                    content,
                    _chunk_counter(config),
                    now=now,
                )
                if remaining:
                    print("suppressed stories still present: " + ", ".join(remaining))
                    return 2
                print("verified")
        except (StoreRefused, KeyError) as exc:
            print(f"{args.command} refused: {exc}", file=sys.stderr)
            return 1
        finally:
            engine.dispose()
            # Release embedded Chroma's file handles before the locks go.
            SharedSystemClient.clear_system_cache()
            gc.collect()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
