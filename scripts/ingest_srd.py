#!/usr/bin/env python
"""CLI — build and publish the authoritative SRD 5.2.1 corpus release.

CRD Issue 5c (#132) / ADR-005c Completion Contract A. This script runs the
deterministic corpus pipeline directly from the authoritative PDF
(``docs/sources/DnD5_5e_SRD_CC_v5_2_1.pdf``), then persists, reconstructs,
proves, and gates the release strictly from the target database's actual
state (Component K steps c-g) before publishing.

It does **not** read the quarantined legacy artifact. The former ``--data-path``
default (the legacy structured JSON under ``data/srd/``) was removed under Owner
Decision 1 (strict legacy quarantine); that artifact is inert evidence at
``docs/legacy/quarantine/`` and is unreachable from every executable path.

The target database is brought to the repository's current Alembic head before
the final gate runs — including migration 0018's legacy-package purge — via the
same ``upgrade_to_head`` the application uses at startup
(``afterworlds.api.db_bootstrap``). This is not assumed to be sufficient on its
own: the gate also runs a live zero-reachability check against the same session
(Component L) and fails closed if an active legacy row remains regardless of
migration state.

Usage
-----
    python scripts/ingest_srd.py \\
        --pdf-path docs/sources/DnD5_5e_SRD_CC_v5_2_1.pdf \\
        --db-url sqlite:///afterworlds.db
"""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path

# Ensure project src is on path when run from repo root
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from afterworlds.api.db_bootstrap import upgrade_to_head  # noqa: E402
from afterworlds.ingestion.corpus.persistence import finalize_release  # noqa: E402
from afterworlds.ingestion.corpus.pipeline import build_candidate  # noqa: E402
from afterworlds.persistence.database import (  # noqa: E402
    create_engine,
    create_session_factory,
)
from afterworlds.pipeline.retrieval.client import build_chroma_client  # noqa: E402
from afterworlds.pipeline.retrieval.config import (  # noqa: E402
    RetrievalMemoryConfig,
)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_DEFAULT_PDF = "docs/sources/DnD5_5e_SRD_CC_v5_2_1.pdf"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build and publish the authoritative SRD 5.2.1 corpus release."
    )
    parser.add_argument("--pdf-path", default=_DEFAULT_PDF)
    parser.add_argument("--db-url", default="sqlite:///afterworlds.db")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    pdf_path = Path(args.pdf_path)
    if not pdf_path.exists():
        print(f"ERROR: authoritative PDF not found: {pdf_path}", file=sys.stderr)
        return 1

    print(f"Building corpus candidate from {pdf_path} ...")
    candidate = build_candidate(pdf_path)
    print(f"  package : {candidate.package_uuid}")
    print(f"  version : {candidate.release_version}")
    print(f"  chunks  : {len(candidate.members.chunks)}")

    print(f"Applying migrations to head against: {args.db_url}")
    upgrade_to_head(args.db_url)

    engine = create_engine(args.db_url)
    session_factory = create_session_factory(engine)

    # Real embedded Chroma client + config (Issue 18 seam). The default local
    # ONNX MiniLM embedding function is resolved inside the reindex path; no fake
    # is ever selected in production (embedding.resolve_default_embedding_function).
    retrieval_config = RetrievalMemoryConfig.from_env()
    chroma_client = build_chroma_client(retrieval_config)

    now = datetime.now(UTC).isoformat()
    with session_factory() as session:
        result = finalize_release(
            session,
            candidate,
            repo_root=_REPO_ROOT,
            now=now,
            chroma_client=chroma_client,
            retrieval_config=retrieval_config,
        )

    if result.reused:
        print(f"Release {candidate.package_uuid} already published — no-op.")
        return 0

    if not result.published:
        print("PUBLICATION GATE FAILED — nothing was persisted:", file=sys.stderr)
        failures = result.gate.failures if result.gate is not None else ()
        for failure in failures:
            print(f"  - {failure}", file=sys.stderr)
        return 1

    print("Publication gate passed.")
    print("=== Corpus release persisted and published ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
