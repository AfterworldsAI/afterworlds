#!/usr/bin/env python
"""Retired CLI tombstone — the original PDF-geometric SRD corpus ingestion.

The Recorded Owner Decision of 21 September 2026 retired the PDF-geometric
corpus this command built and published. Its build and finalization code has
been removed. The command stays as a refusal so an old runbook or automation
fails loudly instead of reaching a database or vector store: the refusal is the
first statement, ahead of argument parsing, migrations and client construction.

The replacement corpus is built from the qualified Markdown source by
``afterworlds.ingestion.corpus.pipeline.build_source_candidate`` and published by
``afterworlds.ingestion.corpus.persistence.finalize_source_release``.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project src is on path when run from repo root
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from afterworlds.quarantine import QuarantinedAuthorityError  # noqa: E402


def main() -> int:
    raise QuarantinedAuthorityError(
        "obsolete corpus ingestion command (scripts/ingest_srd.py)",
        ("command=scripts/ingest_srd.py",),
    )


if __name__ == "__main__":
    sys.exit(main())
