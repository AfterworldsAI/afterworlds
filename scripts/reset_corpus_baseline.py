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
configured client. Idempotent: safe to re-run (a reset of an empty store is a
no-op, and reindex is deterministic).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from uuid import UUID

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sqlalchemy import select  # noqa: E402

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


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db-url", required=True, help="SQLAlchemy DB URL (authoritative)")
    args = ap.parse_args()

    config = RetrievalMemoryConfig.from_env()
    # Resolve + validate the exact configured target before any destructive action;
    # refuses an unsafe target (root/home/cwd/ancestor/empty) rather than proceeding.
    target = resolve_reset_target(config.persist_directory)
    print(f"Chroma target validated: {target}")

    # Step 3: full reset of the configured store (delete every collection).
    client = build_chroma_client(config)
    deleted = reset_chroma_store(client)
    print(f"Reset complete: deleted {len(deleted)} collection(s).")

    # Step 4: rebuild the rules-corpus projection only from the published,
    # SQLite-authoritative Issue-5c corpus package(s) via the Issue 18 reindex path.
    engine = create_engine(args.db_url)
    factory = create_session_factory(engine)
    service = RulesCorpusService(client, config)
    rebuilt = 0
    with factory() as session:
        published = list(
            session.execute(
                select(CorpusReleaseORM.package_uuid).where(
                    CorpusReleaseORM.publication_status == "published"
                )
            ).scalars()
        )
        for pkg in published:
            written = service.reindex_from_sql(session, UUID(pkg))
            print(f"Rebuilt rules corpus for {pkg}: {written} chunks.")
            rebuilt += 1
    if rebuilt == 0:
        print("No published corpus release found — store reset only (idempotent).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
