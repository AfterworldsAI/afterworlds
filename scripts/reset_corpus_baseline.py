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

Preflight: the ``--db-url`` reconstruction source is opened and validated, and the
published rules-corpus packages **and their proof-bound persisted corpora** are fully
loaded and verified **before** anything is deleted, using the same engine/session and
retrieval configuration the rebuild then uses. Verification is Issue 5c's own
canonical proof — the expected vector logical state is built from SQL, the
persisted-corpus digest is recomputed from the persisted rows, and it must equal the
digest recorded at publication — so tampered content, provenance, or locator values
are rejected even when perfectly well-formed. If the database is unavailable,
incompatible (e.g. unmigrated), holds no published corpus release, or holds one whose
persisted corpus cannot be reconstructed or no longer matches its proof, the command
exits non-zero with Chroma untouched — it never erases projections it could not
faithfully rebuild.

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

from afterworlds.ingestion.corpus.persistence import (  # noqa: E402
    verify_chunk_runtime_membership,
    verify_persisted_digest,
    verify_persisted_page_coverage,
    verify_single_source,
)
from afterworlds.ingestion.corpus.vector_publication import (  # noqa: E402
    expected_vector_state_from_sql,
)
from afterworlds.persistence.database import (  # noqa: E402
    create_engine,
    create_session_factory,
)
from afterworlds.persistence.orm.corpus import CorpusReleaseORM  # noqa: E402
from afterworlds.persistence.orm.rules_package import RuleChunkORM  # noqa: E402
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


def validate_corpus_payload(
    session: Session, pkg: str, config: RetrievalMemoryConfig
) -> list[str]:
    """Verify the published release's **proof-bound** persisted corpus.

    A published ``rp_corpus_releases`` row is an *identity*, not a payload, and a
    structurally well-formed payload is not the same as the proven one: content,
    provenance, or a locator can be swapped for another perfectly valid value and
    every structural check still passes. Reindexing that after the reset writes a
    silently wrong projection, with the proven one already deleted.

    So the check is Issue 5c's own canonical proof, not a parallel one. The
    expected vector logical state is built from SQL through the same retrieval
    configuration the rebuild will use
    (:func:`expected_vector_state_from_sql`) — the Chroma store is about to be
    cleared, so what must be proven is the state the rebuild will *write*. The
    persisted-corpus digest is then recomputed from the persisted rows by the
    canonical implementation and compared against the release's stored digest
    (:func:`verify_persisted_digest`). One proof therefore governs content,
    provenance, locator values, membership, policy, ledger, reconciliation,
    source state, and expected vector state; a reconstruction failure (missing,
    malformed, or inconsistent persisted state) is itself a violation.

    Returns the list of violations (empty iff this package is rebuildable and
    still matches what publication proved).

    Issue-5c-specific by construction — it runs only over packages selected from
    ``rp_corpus_releases``. Generic Rules Packages have no corpus release row,
    are never selected here, and keep their broader contract (a generic package
    may legitimately hold zero chunks); ``reindex_from_sql`` is unchanged.
    """
    violations: list[str] = []
    # Materialize exactly what reindex_from_sql will read, so a missing payload is
    # named plainly rather than surfacing only as a digest mismatch.
    rows = list(
        session.execute(
            select(RuleChunkORM)
            .where(RuleChunkORM.rules_package_id == pkg)
            .where(RuleChunkORM.is_enabled.is_(True))
        ).scalars()
    )
    if not rows:
        violations.append(
            f"{pkg}: no enabled rp_chunks rows — a published Issue-5c corpus "
            "would rebuild to an empty collection"
        )
    violations.extend(verify_chunk_runtime_membership(session, pkg))
    violations.extend(verify_single_source(session, pkg))
    violations.extend(verify_persisted_page_coverage(session, pkg))

    # The canonical proof. Any reconstruction failure is a violation in itself —
    # an unprovable corpus must not be rebuilt over a store we are about to wipe.
    try:
        expected_vectors = expected_vector_state_from_sql(
            session, pkg, config
        ).to_payload()
        if not verify_persisted_digest(session, pkg, expected_vectors):
            violations.append(
                f"{pkg}: recomputed persisted-corpus digest does not match the "
                "digest recorded at publication — the persisted corpus is not "
                "the one that was proven"
            )
    except Exception as exc:  # noqa: BLE001 — any failure to reconstruct is fatal
        violations.append(
            f"{pkg}: persisted corpus cannot be reconstructed for proof: "
            f"{type(exc).__name__}: {exc}"
        )
    return violations


def preflight(
    db_url: str, config: RetrievalMemoryConfig
) -> tuple[Engine, sessionmaker[Session], list[UUID]]:
    """Prove the rebuild source is usable BEFORE the reset, and materialize it.

    Chroma is a rebuildable projection of SQLite — but only while SQLite is
    actually reachable and holds a *complete, valid* payload to rebuild from.
    This connects through the same engine/session configuration the rebuild will
    use (a mistyped/unreachable/unmigrated URL therefore fails here, not after
    the deletion), materializes the published package identities, and then fully
    loads and validates each one's chunk payload
    (:func:`validate_corpus_payload`), so the rebuild never depends on a lazy
    cursor — or on unverified rows — read across the reset.

    Raises :class:`PreflightError` if the database is unavailable, incompatible
    (e.g. unmigrated — no ``rp_corpus_releases``), holds no published corpus
    release, or holds one whose payload is missing/unreadable/malformed/orphaned
    or fails Issue 5c's completeness and integrity requirements. On failure the
    engine is disposed here; on success the caller owns it (returned alongside
    the factory) and disposes it when done.
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
            if not packages:
                raise PreflightError(
                    f"{db_url!r} holds no published corpus release — there would "
                    "be nothing to rebuild the rules corpus from"
                )
            violations: list[str] = []
            for pkg_uuid in packages:
                violations.extend(
                    validate_corpus_payload(session, str(pkg_uuid), config)
                )
    except PreflightError:
        engine.dispose()  # type: ignore[union-attr]
        raise
    except (SQLAlchemyError, ValueError) as exc:
        if engine is not None:
            engine.dispose()
        raise PreflightError(
            f"cannot read the published corpus payload from {db_url!r}: {exc}"
        ) from exc
    if violations:
        engine.dispose()
        raise PreflightError(
            "published corpus payload is not rebuildable:\n  - "
            + "\n  - ".join(violations)
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
        engine, factory, packages = preflight(args.db_url, config)
    except PreflightError as exc:
        print(f"Preflight FAILED — Chroma was NOT modified: {exc}")
        return 1
    print(
        f"Preflight OK: {len(packages)} published rules-corpus package(s) "
        "validated and materialized; ready to rebuild."
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
