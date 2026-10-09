"""Rebuild the superseded release the pinned replay scripts read, into OUT.

usage: superseded_release.py OUT NOW

The replay scripts under ``.claude/review-notes/`` read release
``5.2.1-corpus.3fe24ff6-4e3`` from a private scratch store that is never
delivered. That release is the qualified source built with the pre-correction
``CORPUS_FILES`` order, which its delivered identity records. This rebuilds it
through the production lifecycle, then refuses any identity that differs from
the recorded one. Run as a child process: the order override must not leak into
the test session, which asserts the current order.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

from sqlalchemy import event

import afterworlds.ingestion.corpus.source_ledger as source_ledger
import afterworlds.ingestion.corpus.source_units as source_units
from afterworlds.ingestion.corpus.persistence import finalize_source_release
from afterworlds.ingestion.corpus.pipeline import build_source_candidate
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.persistence.orm.base import Base
from afterworlds.pipeline.retrieval.client import build_isolated_test_chroma_client
from afterworlds.pipeline.retrieval.config import RetrievalMemoryConfig
from afterworlds.pipeline.retrieval.embedding import DeterministicFakeEmbeddingFunction

REPO_ROOT = Path(__file__).resolve().parents[2]
IDENTITY = (
    REPO_ROOT
    / ".claude"
    / "review-notes"
    / "issue-5c-release-order-candidate"
    / "releases"
    / "old"
    / "identity.json"
)


def main(out: Path, now: str) -> None:
    recorded = json.loads(IDENTITY.read_text(encoding="utf-8"))
    order = tuple(recorded["corpus_files"])
    # source_ledger binds the name at import, so both modules are rebound.
    source_units.CORPUS_FILES = vars(source_ledger)["CORPUS_FILES"] = order
    candidate = build_source_candidate(
        REPO_ROOT, retrieval_config=RetrievalMemoryConfig()
    )
    engine = create_engine(f"sqlite:///{out}")

    @event.listens_for(engine, "connect")
    def _fk(dbapi, _rec):  # type: ignore[no-untyped-def]
        dbapi.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    client = build_isolated_test_chroma_client(
        tempfile.mkdtemp(prefix="superseded-release-chroma-")
    )
    try:
        with create_session_factory(engine)() as session:
            result = finalize_source_release(
                session,
                candidate,
                now=now,
                chroma_client=client,
                retrieval_config=RetrievalMemoryConfig(),
                embedding_function=DeterministicFakeEmbeddingFunction(),
            )
    finally:
        engine.dispose()
    assert result.published and result.artifacts is not None, result.gate
    built = {
        "corpus_files": list(order),
        "package_uuid": candidate.package_uuid,
        "release_version": candidate.release_version,
        "transform_config_hash": candidate.transform_config_hash,
        "ledger_hash": candidate.ledger_hash,
        "bundle_root_hash": candidate.bundle.bundle_root_hash,
        "authoritative_source_hash": candidate.authoritative_source_hash,
        "persisted_corpus_digest": result.artifacts.report.payload.get(
            "persisted_corpus_digest"
        ),
        "units": len(candidate.ledger.leaves),
        "containers": len(candidate.ledger.containers),
        "chunks": len(candidate.members.chunks),
        "citation_report": (
            candidate.citation_report.payload() if candidate.citation_report else None
        ),
    }
    assert built == recorded, {k: v for k, v in built.items() if recorded.get(k) != v}


if __name__ == "__main__":
    main(Path(sys.argv[1]), sys.argv[2])
