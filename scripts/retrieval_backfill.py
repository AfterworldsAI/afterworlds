#!/usr/bin/env python
"""CLI script — backfill or reindex Retrieval Memory for one story.

CRD Issue 18 / ADR-018 D7: recovery for a Chroma write failure is a re-run;
this script is the idempotent manual backfill/reindex path.

Usage
-----
    python scripts/retrieval_backfill.py --story-id <uuid> --mode backfill \\
        --chroma-path .chroma_data --db-url sqlite:///afterworlds.db

    python scripts/retrieval_backfill.py --story-id <uuid> --mode reindex \\
        --chroma-path .chroma_data --db-url sqlite:///afterworlds.db

Remote deployment (prerequisite #205 §5): with ``AFTERWORLDS_DEPLOYMENT=remote``
the job must carry its trusted account scope (``--account-id``) and is
refused unless that account still owns the Story, is active and the Story is
not under deletion suppression -- checked when the job runs, so a stale job
can neither cross accounts nor recreate deleted content.
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any
from uuid import UUID

# Ensure project src is on path when run from repo root
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

# Import all ORM models so Base.metadata is complete
from chromadb.api.shared_system_client import SharedSystemClient  # noqa: E402

import afterworlds.persistence.orm.character_sheet  # noqa: E402, F401
import afterworlds.persistence.orm.node  # noqa: E402, F401
import afterworlds.persistence.orm.retrieval  # noqa: E402, F401
import afterworlds.persistence.orm.rules_package  # noqa: E402, F401
import afterworlds.persistence.orm.session_state  # noqa: E402, F401
import afterworlds.persistence.orm.state  # noqa: E402, F401
import afterworlds.persistence.orm.story  # noqa: E402, F401
import afterworlds.persistence.orm.story_bible  # noqa: E402, F401
from afterworlds.persistence.crud.story import get_story  # noqa: E402
from afterworlds.persistence.database import (  # noqa: E402
    create_engine,
    create_session_factory,
)
from afterworlds.pipeline.retrieval.backfill import (  # noqa: E402
    backfill_story,
    reindex_story,
)
from afterworlds.pipeline.retrieval.client import build_chroma_client  # noqa: E402
from afterworlds.pipeline.retrieval.config import RetrievalMemoryConfig  # noqa: E402
from afterworlds.pipeline.retrieval.write_service import (  # noqa: E402
    RetrievalMemoryWriteService,
)
from afterworlds.remote.access import (  # noqa: E402
    AccessPolicy,
    DelayedWorkScope,
    StoryAccessDenied,
    story_owner,
    work_scope,
)
from afterworlds.remote.control_store import open_control_store  # noqa: E402
from afterworlds.remote.identity import IdentityService  # noqa: E402
from afterworlds.remote.retrieval_guard import GuardedRetrievalWrites  # noqa: E402
from afterworlds.remote.storage import (  # noqa: E402
    StoreRefused,
    maintenance_locks,
    pending_restores,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Backfill or reindex Retrieval Memory for one story."
    )
    parser.add_argument("--story-id", required=True, help="Story UUID")
    parser.add_argument(
        "--mode",
        choices=["backfill", "reindex", "delete"],
        default="backfill",
        help="backfill: ingest missing eligible turns. "
        "reindex: wipe and rebuild from SQLite ground truth. "
        "delete: remove all chunks for the story (no rebuild).",
    )
    parser.add_argument(
        "--chroma-path",
        default=None,
        help="Override persist_directory. Defaults to the same "
        "environment-derived config the application uses "
        "(AFTERWORLDS_RETRIEVAL_PERSIST_DIRECTORY), so this only needs to "
        "be passed to deliberately point at a different Chroma directory.",
    )
    parser.add_argument("--db-url", default="sqlite:///afterworlds.db")
    parser.add_argument(
        "--account-id",
        default=None,
        help="Remote deployment only: the owning hosted account (required).",
    )
    return parser.parse_args(argv)


class _NoNotices:
    def send(self, *, contact_address: str, kind: str, code: str) -> None:
        raise AssertionError("backfill sends no notices")


def remote_scope_check(
    session_factory: Any, story_id: UUID, account_id: str | None, mode: str
) -> None:
    """Recheck the job's trusted scope (remote only); exit 3 when refused."""
    if os.environ.get("AFTERWORLDS_DEPLOYMENT") != "remote":
        return
    control_url = os.environ.get("AFTERWORLDS_CONTROL_DATABASE_URL")
    if account_id is None or control_url is None:
        print(
            "remote backfill requires --account-id and "
            "AFTERWORLDS_CONTROL_DATABASE_URL",
            file=sys.stderr,
        )
        raise SystemExit(3)
    control = open_control_store(control_url)
    policy = AccessPolicy(IdentityService(control, _NoNotices()), control)
    scope = DelayedWorkScope(
        account_id=UUID(account_id), story_id=story_id, operation=f"retrieval_{mode}"
    )
    session = session_factory()
    try:
        if mode == "delete":
            # Deletion enforces a suppression: it needs the owner, not an
            # unsuppressed Story (remote/retrieval_guard.py).
            if story_owner(session, story_id) != account_id:
                raise StoryAccessDenied(scope.operation)
        else:
            policy.check_delayed_work(session, scope)
    except StoryAccessDenied:
        print("story not accessible for this account", file=sys.stderr)
        raise SystemExit(3) from None
    finally:
        session.close()


def build_effective_config(chroma_path: str | None) -> RetrievalMemoryConfig:
    """Build the config this script uses for every mode (backfill/reindex/delete).

    Starts from ``RetrievalMemoryConfig.from_env()`` -- the same
    environment-derived config the running application uses -- rather than
    dataclass defaults (Codex review, PR #119): a recovery script that
    silently rebuilt with default ``embedding_model_id``/
    ``chunk_char_ceiling``/etc. instead of the env-configured values could
    recreate the exact mismatch it was meant to fix.
    ``chroma_path`` overrides only ``persist_directory``, and only when
    explicitly provided (``None`` leaves the env-derived value untouched).
    """
    config = RetrievalMemoryConfig.from_env()
    if chroma_path is not None:
        config = replace(config, persist_directory=chroma_path)
    return config


def _run_mode(
    mode: str,
    session_factory: Any,
    write_service: Any,
    story_id: UUID,
    delete: Any,
) -> None:
    session = session_factory()
    try:
        story = get_story(session, story_id)
        if story is None:
            print(f"story {story_id} not found", file=sys.stderr)
            raise SystemExit(1)
        story_mode = story.mode
        if mode == "delete":
            remaining = delete()
            print(f"deleted story chunks; remaining={remaining}")
            if remaining != 0:
                raise SystemExit(2)
            return
        if mode == "reindex":
            report = reindex_story(session, write_service, story_id, story_mode)
        else:
            report = backfill_story(session, write_service, story_id, story_mode)
    finally:
        session.close()

    print(
        f"scanned={report.turns_scanned} ingested={report.turns_ingested} "
        f"skipped={report.turns_skipped_ineligible} "
        f"data_integrity_errors={list(report.data_integrity_errors)}"
    )
    if report.data_integrity_errors:
        raise SystemExit(2)


def _remote_main(args: argparse.Namespace, story_id: UUID, config: Any) -> None:
    """The remote job: inside both store locks (so never beside a serving app
    or a storage operation), refused while a restore is pending, and every
    write rechecks the job's trusted scope through the Retrieval guard, so a
    closure or suppression mid-job stops the remaining writes. Exit 3 on any
    refusal."""
    control_url = os.environ.get("AFTERWORLDS_CONTROL_DATABASE_URL")
    if args.account_id is None or control_url is None:
        print(
            "remote backfill requires --account-id and "
            "AFTERWORLDS_CONTROL_DATABASE_URL",
            file=sys.stderr,
        )
        raise SystemExit(3)
    control = open_control_store(control_url)
    try:
        with maintenance_locks(args.db_url, Path(config.persist_directory), control):
            if pending_restores(control):
                print("a restore is pending; no job may run", file=sys.stderr)
                raise SystemExit(3)
            engine = create_engine(args.db_url)
            session_factory = create_session_factory(engine)
            try:
                remote_scope_check(
                    session_factory, story_id, args.account_id, args.mode
                )
                policy = AccessPolicy(IdentityService(control, _NoNotices()), control)
                writes = GuardedRetrievalWrites(
                    RetrievalMemoryWriteService(build_chroma_client(config), config),
                    policy,
                    session_factory,
                )
                scope = DelayedWorkScope(
                    UUID(args.account_id), story_id, f"retrieval_{args.mode}"
                )
                with work_scope(scope):
                    _run_mode(
                        args.mode,
                        session_factory,
                        writes,
                        story_id,
                        lambda: writes.delete_story_for(scope),
                    )
            except StoryAccessDenied:
                print("story not accessible for this account", file=sys.stderr)
                raise SystemExit(3) from None
            finally:
                engine.dispose()
                SharedSystemClient.clear_system_cache()
    except StoreRefused as exc:
        print(f"refused: {exc}", file=sys.stderr)
        raise SystemExit(3) from None


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    story_id = UUID(args.story_id)
    config = build_effective_config(args.chroma_path)
    if os.environ.get("AFTERWORLDS_DEPLOYMENT") == "remote":
        _remote_main(args, story_id, config)
        return

    engine = create_engine(args.db_url)
    session_factory = create_session_factory(engine)
    write_service = RetrievalMemoryWriteService(build_chroma_client(config), config)
    _run_mode(
        args.mode,
        session_factory,
        write_service,
        story_id,
        lambda: write_service.delete_story(story_id),
    )


if __name__ == "__main__":
    main()
