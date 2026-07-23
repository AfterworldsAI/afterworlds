#!/usr/bin/env python
"""CLI — build and persist the authoritative SRD 5.2.1 corpus release.

CRD Issue 5c (#132) / ADR-005c Completion Contract A. This script runs the
deterministic corpus pipeline directly from the authoritative PDF
(``docs/sources/DnD5_5e_SRD_CC_v5_2_1.pdf``) and persists a new immutable
release only if it passes the publication gate.

It does **not** read the quarantined legacy artifact. The former ``--data-path``
default (the legacy structured JSON under ``data/srd/``) was removed under Owner
Decision 1 (strict legacy quarantine); that artifact is inert evidence at
``docs/legacy/quarantine/`` and is unreachable from every executable path.

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

# Import all corpus + rules-package ORM models so Base.metadata is complete.
import afterworlds.persistence.orm.corpus  # noqa: E402, F401
import afterworlds.persistence.orm.rules_package  # noqa: E402, F401
from afterworlds.ingestion.corpus.gate import run_gate  # noqa: E402
from afterworlds.ingestion.corpus.persistence import persist_release  # noqa: E402
from afterworlds.ingestion.corpus.pipeline import build_release  # noqa: E402
from afterworlds.ingestion.corpus.quarantine import (  # noqa: E402
    check_legacy_reachability,
)
from afterworlds.persistence.database import (  # noqa: E402
    create_engine,
    create_session_factory,
)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_DEFAULT_PDF = "docs/sources/DnD5_5e_SRD_CC_v5_2_1.pdf"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build and persist the authoritative SRD 5.2.1 corpus release."
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

    print(f"Building corpus release from {pdf_path} ...")
    violations = check_legacy_reachability(None, _REPO_ROOT)
    artifacts = build_release(pdf_path, legacy_reachability_violations=len(violations))
    print(f"  package : {artifacts.release.package_uuid}")
    print(f"  version : {artifacts.release.release_version}")
    print(f"  chunks  : {len(artifacts.members.chunks)}")

    gate = run_gate(artifacts, legacy_reachability_violations=len(violations))
    if not gate.passed:
        print("PUBLICATION GATE FAILED:", file=sys.stderr)
        for failure in gate.failures:
            print(f"  - {failure}", file=sys.stderr)
        return 1
    print("Publication gate passed.")

    print(f"Connecting to database: {args.db_url}")
    engine = create_engine(args.db_url)
    from afterworlds.persistence.orm.base import Base

    Base.metadata.create_all(engine)
    session_factory = create_session_factory(engine)
    now = datetime.now(UTC).isoformat()
    with session_factory() as session:
        persist_release(session, artifacts, now=now)
        session.commit()
    print("=== Corpus release persisted ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
