"""Ingestion-wide fixtures: the one real CRD Issue 5c release.

Building the production corpus from the committed PDF and finalizing it through
the genuine persist → reconstruct → digest → gate → publish lifecycle costs
about two minutes. Both suites that need it — CRD Issue 5c's own tests and CRD
Issue 5d's production-corpus control — must share one build, so these fixtures
live here rather than in either subdirectory. Defined in a parent ``conftest``,
they are a single session-scoped fixture definition; duplicated per directory
they would be two, and the cost would double.

Everything else stays where it is used. This module holds only what more than
one subdirectory needs.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from sqlalchemy import event

from afterworlds.ingestion.corpus.persistence import _finalize_core, finalize_release
from afterworlds.ingestion.corpus.pipeline import (
    CandidateRelease,
    ReleaseArtifacts,
    build_candidate,
)
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.persistence.orm.base import Base
from afterworlds.pipeline.retrieval.client import build_isolated_test_chroma_client
from afterworlds.pipeline.retrieval.config import RetrievalMemoryConfig
from afterworlds.pipeline.retrieval.embedding import DeterministicFakeEmbeddingFunction

REPO_ROOT = Path(__file__).resolve().parents[2]
PDF_PATH = REPO_ROOT / "docs" / "sources" / "DnD5_5e_SRD_CC_v5_2_1.pdf"

NOW = "2026-07-23T00:00:00Z"


def finalize_in_fresh_db(candidate: CandidateRelease, *, core: bool = False):  # type: ignore[no-untyped-def]
    """Finalize *candidate* against a brand-new, already-committed in-memory DB
    plus a private, isolated on-disk Chroma store and the deterministic offline
    embedding function.

    ``core=False`` (default) uses the production ``finalize_release`` (with its
    completeness guard) — for the full-SRD candidate. ``core=True`` uses the
    private ``_finalize_core`` seam, which skips the completeness guard so a
    compact (partial) candidate can still exercise the persist/gate lifecycle.
    Returns the ``FinalizeResult``; the caller asserts ``published``/``reused``.
    """
    eng = create_engine("sqlite://")

    @event.listens_for(eng, "connect")
    def _fk(dbapi, _rec):  # type: ignore[no-untyped-def]
        dbapi.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(eng)
    factory = create_session_factory(eng)
    sess = factory()
    chroma_dir = tempfile.mkdtemp(prefix="corpus-chroma-")
    client = build_isolated_test_chroma_client(chroma_dir)
    finalize = _finalize_core if core else finalize_release
    try:
        result = finalize(
            sess,
            candidate,
            now=NOW,
            chroma_client=client,
            retrieval_config=RetrievalMemoryConfig(),
            embedding_function=DeterministicFakeEmbeddingFunction(),
        )
    finally:
        sess.close()
        eng.dispose()
    return result


@pytest.fixture(scope="session")
def full_candidate() -> CandidateRelease:
    """The real full-SRD pre-persistence candidate, built once for the session.

    This is the primary build (no fixture dependencies), so a test module may
    safely shadow ``candidate`` with the compact one without recursion.
    """
    return build_candidate(PDF_PATH, retrieval_config=RetrievalMemoryConfig())


@pytest.fixture(scope="session")
def full_release(full_candidate: CandidateRelease) -> ReleaseArtifacts:
    """The real full-SRD corpus release, finalized once for the whole session.

    Goes through the actual publish lifecycle (``finalize_release``) rather than
    being assembled in memory, so every test that reads from this fixture is
    implicitly exercising Component K's full acyclic c–g order. Depends on
    ``full_candidate`` (never shadowed) to keep the shadow-safe dependency
    chain.
    """
    result = finalize_in_fresh_db(full_candidate)
    assert result.published and result.artifacts is not None, result.gate
    return result.artifacts
