"""CRD Issue 22 operator maintenance commands (app stopped)::

    python -m afterworlds.operations.maintenance compact
    python -m afterworlds.operations.maintenance expire
    python -m afterworlds.operations.maintenance finalize
    python -m afterworlds.operations.maintenance enforce-restore
    python -m afterworlds.operations.maintenance release-suppression --suppression-id ID
    python -m afterworlds.operations.maintenance reviews

``compact`` physically disposes of logically deleted content (both live
stores) and records it on every pending deletion; ``expire`` runs the D4
retention sweep; ``finalize`` re-evaluates deletions waiting on compaction
or backup disposal; ``enforce-restore`` re-applies every active deletion to
a restored store (then run ``storage_cli verify-restore``);
``release-suppression`` releases a suppression only when its end conditions
are verified; ``reviews`` lists annual reviews due. A remote deployment
holds the three store locks (#205 ``maintenance_locks``), so none runs
beside a serving app; a local one must be run with the app stopped.
Configuration comes from the same environment variables as the app.
"""

from __future__ import annotations

import argparse
import gc
import json
import subprocess
import sys
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path

from chromadb.api import ClientAPI
from chromadb.api.shared_system_client import SharedSystemClient
from chromadb.errors import ChromaError
from sqlalchemy.orm import Session, sessionmaker

from afterworlds.api.config import load_settings
from afterworlds.operations.compaction import (
    compact_stores,
    compaction_unfinished,
)
from afterworlds.operations.deletion import DeletionContext, evaluate
from afterworlds.operations.enforcement import enforce_restore, record_compaction
from afterworlds.operations.requests import RequestState, RequestStore
from afterworlds.operations.retention import release_suppression, reviews_due, sweep
from afterworlds.operations.vectors import story_chunk_deleter
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.pipeline.retrieval.client import build_chroma_client
from afterworlds.pipeline.retrieval.config import RetrievalMemoryConfig
from afterworlds.remote.control_store import (
    ControlStoreUnavailable,
    connect_control_store,
    utc_now,
)
from afterworlds.remote.storage import StoreRefused, maintenance_locks, sqlite_path


@contextmanager
def _stores() -> (
    Iterator[
        tuple[sessionmaker[Session], sessionmaker[Session] | None, Path, Path, str]
    ]
):
    settings = load_settings()
    vector_dir = Path(RetrievalMemoryConfig.from_env().persist_directory)
    remote = settings.deployment == "remote"
    content = create_session_factory(create_engine(settings.database_url))
    control = None
    try:
        if remote:
            assert settings.control_database_url is not None
            control = connect_control_store(settings.control_database_url)
            with maintenance_locks(settings.database_url, vector_dir, control):
                yield content, control, sqlite_path(
                    settings.database_url
                ), vector_dir, "remote"
        else:
            yield content, None, sqlite_path(settings.database_url), vector_dir, "local"
    finally:
        content.kw["bind"].dispose()
        if control is not None:
            control.kw["bind"].dispose()
        SharedSystemClient.clear_system_cache()
        gc.collect()


def _client() -> Callable[[], ClientAPI]:
    config = RetrievalMemoryConfig.from_env()
    return lambda: build_chroma_client(config)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="CRD Issue 22 maintenance")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("compact", "expire", "finalize", "enforce-restore", "reviews"):
        sub.add_parser(name)
    sub.add_parser("release-suppression").add_argument(
        "--suppression-id", required=True
    )
    args = parser.parse_args(argv)
    now = utc_now()
    vector = Path(RetrievalMemoryConfig.from_env().persist_directory)
    if args.command != "compact" and compaction_unfinished(vector):
        print(
            f"{args.command} refused: a store compaction did not finish; run "
            "`compact` again first",
            file=sys.stderr,
        )
        return 1
    try:
        with _stores() as (content, control, db_path, vector_dir, env):
            ops = control if control is not None else content
            if args.command == "compact":
                content.kw["bind"].dispose()
                evidence = compact_stores(db_path, vector_dir, _client())
                done = record_compaction(ops, evidence, now=utc_now)
                print(json.dumps({"compacted": evidence, "requests": done}))
            elif args.command == "expire":
                print(
                    json.dumps(
                        sweep(
                            ops=ops, content=content, control=control, now=now
                        ).as_dict()
                    )
                )
            elif args.command == "finalize":
                store = RequestStore(ops, now=utc_now)
                ctx = DeletionContext(
                    store=store,
                    ops=ops,
                    content=content,
                    environment=env,
                    delete_story_chunks=story_chunk_deleter(_client()),
                    now=utc_now,
                    control=control,
                )
                states = {}
                for rid in store.request_ids():
                    _, state, attempt = store.state_of(rid)
                    if (
                        state is RequestState.IN_PROGRESS
                        and attempt
                        and store.header(rid).kind == "deletion"
                    ):
                        states[rid] = evaluate(ctx, rid, attempt).value
                print(json.dumps(states))
            elif args.command == "enforce-restore":
                if control is None:
                    parser.error("enforce-restore requires a remote deployment")
                print(
                    json.dumps(
                        enforce_restore(
                            control,
                            content,
                            database_path=db_path,
                            vector_dir=vector_dir,
                            client_factory=_client(),
                            now=now,
                        )
                    )
                )
            elif args.command == "release-suppression":
                if control is None:
                    parser.error("release-suppression requires a remote deployment")
                released = release_suppression(control, args.suppression_id, now=now)
                print("released" if released else "end conditions not met; kept")
                return 0 if released else 2
            else:
                print(json.dumps(reviews_due(ops, control, now=now)))
    except (StoreRefused, ControlStoreUnavailable, KeyError) as exc:
        print(f"{args.command} refused: {exc}", file=sys.stderr)
        return 1
    except (ChromaError, subprocess.CalledProcessError, OSError) as exc:
        # Nothing is reported done; an interrupted compaction resumes on retry.
        print(
            f"{args.command} failed ({type(exc).__name__}); retry the command",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
