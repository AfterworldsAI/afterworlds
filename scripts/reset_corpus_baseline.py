#!/usr/bin/env python
"""One-time pre-release Chroma baseline reset + rules-corpus rebuild.

CRD Issue 5c (#132), Round 18. Owner decision (Issue 5c Rev7 / Issue 18 Rev6):
Afterworlds is pre-release, so as a **one-time explicit remediation** the
configured development ChromaDB store is reset in full, then the corrected
rules-corpus projection is rebuilt from the published Issue-5c SQLite-authoritative
package via Issue 18's existing reindex path. There is no selective per-collection
legacy cleanup, no legacy-UUID handoff, and no prefix-based deletion.

This is **not** startup behavior — never wire it into ordinary application startup;
resetting on startup could later erase valid user data.

Usage
-----
    python scripts/reset_corpus_baseline.py --db-url sqlite:///afterworlds.db

The Chroma target is the configured ``RetrievalMemoryConfig.persist_directory``
(``AFTERWORLDS_RETRIEVAL_PERSIST_DIRECTORY``); it is resolved and validated before any
destructive action and the reset only ever deletes collections through the
configured client. Idempotent: safe to re-run against the same database (deleting
an already-empty *store* is a no-op and reindex is deterministic). Note this is
about the Chroma store, not the database — an empty *database* aborts, see below.

Preflight: the ``--db-url`` reconstruction source is opened, validated, and its
published rules-corpus package identities fully materialized **before** anything is
deleted, using the same engine/session configuration the rebuild then uses. If the
database is unavailable, incompatible (e.g. unmigrated), or holds no published
corpus release, the command exits non-zero with Chroma untouched — it never erases
projections it could not rebuild.

DESTRUCTIVE — what this deletes and what it does NOT rebuild
------------------------------------------------------------
The reset is a **full-store** reset: it deletes **every** collection in the
configured store, **including the shared ``story_memory`` collection**. This
command then rebuilds **published Issue-5c rules-corpus projections only**. It
does **not** restore story memory, and it deliberately does not enumerate or
reindex stories — restoration is an existing per-story Issue 18 operation, not
part of the Issue-5c baseline (GitHub #132 Owner Decision 1: "any desired
story-memory backfill uses Issue 18's existing reindex path and is not
redesigned here").

Story memory is a rebuildable projection of SQLite-authoritative turns, so
nothing is lost that SQLite cannot regenerate — but it is regenerated only when
an operator asks for it. To restore it, run the existing Issue 18 CLI once per
surviving story::

    python scripts/retrieval_backfill.py --story-id <uuid> --mode reindex \\
        --db-url sqlite:///afterworlds.db
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from uuid import UUID

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sqlalchemy import Engine, select  # noqa: E402
from sqlalchemy.exc import SQLAlchemyError  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402

from afterworlds.persistence.database import (  # noqa: E402
    create_engine,
    create_session_factory,
)
from afterworlds.persistence.orm.corpus import CorpusReleaseORM  # noqa: E402
from afterworlds.pipeline.retrieval.baseline_reset import (  # noqa: E402
    reset_chroma_store,
    resolve_reset_target,
)
from afterworlds.pipeline.retrieval.client import build_chroma_client  # noqa: E402
from afterworlds.pipeline.retrieval.config import RetrievalMemoryConfig  # noqa: E402
from afterworlds.pipeline.retrieval.rules_corpus_service import (  # noqa: E402
    RulesCorpusService,
)

WARNING = """\
DESTRUCTIVE: this is a FULL-STORE reset — every collection in the configured
Chroma store is deleted, INCLUDING the shared 'story_memory' collection.
This command rebuilds published Issue-5c rules-corpus projections ONLY.
It does NOT restore story memory and does not enumerate or reindex stories.
Story memory is a rebuildable projection of SQLite-authoritative turns; to
restore it, run the existing Issue 18 CLI once per surviving story:
    python scripts/retrieval_backfill.py --story-id <uuid> --mode reindex \\
        --db-url <same db url>
"""


class PreflightError(RuntimeError):
    """The configured SQLite reconstruction source cannot support the rebuild.

    Raised before anything is deleted, so the caller can exit with Chroma
    untouched rather than erasing projections it then cannot rebuild.
    """


def preflight(db_url: str) -> tuple[Engine, sessionmaker[Session], list[UUID]]:
    """Prove the rebuild source is usable BEFORE the reset, and materialize it.

    Chroma is a rebuildable projection of SQLite — but only while SQLite is
    actually reachable and holds the published releases to rebuild from. This
    connects through the same engine/session configuration the rebuild will use
    (a mistyped/unreachable/unmigrated URL therefore fails here, not after the
    deletion) and returns the **fully materialized** package identities, so the
    rebuild never depends on a lazy cursor opened across the reset.

    Raises :class:`PreflightError` if the database is unavailable, incompatible
    (e.g. unmigrated — no ``rp_corpus_releases``), or holds no published corpus
    release to rebuild. On failure the engine is disposed here; on success the
    caller owns it (returned alongside the factory) and disposes it when done.
    """
    engine = None
    try:
        engine = create_engine(db_url)
        factory = create_session_factory(engine)
        with factory() as session:
            packages = [
                UUID(pkg)
                for pkg in session.execute(
                    select(CorpusReleaseORM.package_uuid).where(
                        CorpusReleaseORM.publication_status == "published"
                    )
                ).scalars()
            ]
    except (SQLAlchemyError, ValueError) as exc:
        if engine is not None:
            engine.dispose()
        raise PreflightError(
            f"cannot read published corpus releases from {db_url!r}: {exc}"
        ) from exc
    if not packages:
        engine.dispose()
        raise PreflightError(
            f"{db_url!r} holds no published corpus release — there would be "
            "nothing to rebuild the rules corpus from"
        )
    return engine, factory, packages


def main() -> int:
    # Raw formatter: the destructive-behaviour section above must reach --help
    # laid out as written, not reflowed into one paragraph.
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--db-url", required=True, help="SQLAlchemy DB URL (authoritative)")
    args = ap.parse_args()

    config = RetrievalMemoryConfig.from_env()
    # Resolve + validate the exact configured target before any destructive action;
    # refuses an unsafe target (root/home/cwd/ancestor/empty) rather than proceeding.
    target = resolve_reset_target(config.persist_directory)
    print(f"Chroma target validated: {target}")

    # Step 2: prove the rebuild source before deleting the thing it rebuilds.
    # An unreachable/unmigrated/empty database discovered *after* the reset would
    # leave the rules-corpus projections erased with nothing to restore them from.
    try:
        engine, factory, packages = preflight(args.db_url)
    except PreflightError as exc:
        print(f"Preflight FAILED — Chroma was NOT modified: {exc}")
        return 1
    print(
        f"Preflight OK: {len(packages)} published rules-corpus package(s) to rebuild."
    )

    # Step 3: full reset of the configured store (delete every collection).
    # The operator is told what this destroys BEFORE anything is destroyed — a
    # warning printed after the deletion would be a report, not a warning.
    client = build_chroma_client(config)
    print(WARNING)
    deleted = reset_chroma_store(client)
    print(f"Reset complete: deleted {len(deleted)} collection(s).")

    # Step 4: rebuild exactly the package identities proven above — the same
    # SQLite-authoritative releases, via the Issue 18 reindex path. No re-query:
    # the rebuild set is the preflighted set.
    service = RulesCorpusService(client, config)
    try:
        with factory() as session:
            for pkg in packages:
                written = service.reindex_from_sql(session, pkg)
                print(f"Rebuilt rules corpus for {pkg}: {written} chunks.")
    finally:
        # The preflight engine is owned here; release it (it holds a SQLite/WAL
        # connection) rather than relying on process exit.
        engine.dispose()
    print(
        "Story memory was NOT restored (rules corpus only). Reindex any story you "
        "still want with: scripts/retrieval_backfill.py --story-id <uuid> "
        "--mode reindex"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
