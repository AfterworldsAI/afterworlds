"""Ingestion-wide fixtures: the real CRD Issue 5c releases.

Building the production corpus from the committed PDF and finalizing it through
the genuine persist → reconstruct → digest → gate → publish lifecycle costs
about two minutes. Both suites that need it — CRD Issue 5c's own tests and CRD
Issue 5d's production-corpus control — must share one build, so these fixtures
live here rather than in either subdirectory. Defined in a parent ``conftest``,
they are a single session-scoped fixture definition; duplicated per directory
they would be two, and the cost would double.

The replacement release built from the qualified Markdown source is here for
the same reason. CRD Issue 5c's suite builds it to assert the reset, and CRD
Issue 5d's shared-tool readiness proof needs a *live session over the very same
published state* -- which ``finalize_in_fresh_db`` cannot hand back, because it
closes its session and disposes its engine. So ``source_release_db`` publishes
through the real lifecycle into a file, once, and every consumer opens its own
session on it.

Everything else stays where it is used. This module holds only what more than
one subdirectory needs.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from sqlalchemy import event

from afterworlds.ingestion.corpus.persistence import (
    _finalize_core,
    finalize_release,
    finalize_source_release,
)
from afterworlds.ingestion.corpus.pipeline import (
    CandidateRelease,
    ReleaseArtifacts,
    build_candidate,
    build_source_candidate,
)
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.persistence.orm.base import Base
from afterworlds.pipeline.retrieval.client import build_isolated_test_chroma_client
from afterworlds.pipeline.retrieval.config import RetrievalMemoryConfig
from afterworlds.pipeline.retrieval.embedding import DeterministicFakeEmbeddingFunction

REPO_ROOT = Path(__file__).resolve().parents[2]
PDF_PATH = REPO_ROOT / "docs" / "sources" / "DnD5_5e_SRD_CC_v5_2_1.pdf"

NOW = "2026-07-23T00:00:00Z"

#: Every test that finalizes a corpus release through this helper is finalizing a
#: *quarantined* product. Recorded Owner Decision 2026-09-21 retires the SRD 5.2.1
#: corpus release `4458fa10-4a66-5e0e-9ecc-ea37530ad2b4` /
#: `5.2.1-corpus.36b786d8-fa2`, but what is actually retired is the PDF-geometric
#: *transform* that built it: `afterworlds.quarantine` refuses the transform
#: recipe hash recorded in every candidate this pipeline produces, so reaching a
#: different package UUID (by reconfiguring the embedding model label, say) does
#: not reach an admitted product. Finalization is therefore refused whatever
#: identity the candidate carries, alongside the publication, retrieval,
#: corpus-load and runtime-selection seams this lifecycle runs through.
#:
#: Skipped rather than rewritten or deleted: these tests still accurately describe
#: the implementation in the tree, and the Owner Decision retires the superseded
#: work in a later increment (its Step 5), not in the quarantine increment. The
#: quarantine's own regression coverage is `tests/test_quarantine_5c_5d.py`; the
#: retired-versus-still-live disposition of every skip, and the operational
#: coverage the replacement corpus owes, are recorded in
#: `docs/architecture/issue-5c-5d-clean-restart.md`.
QUARANTINED_RECONSTRUCTION = (
    "quarantined 5c/5d product: finalizing a release built by the retired "
    "PDF-geometric transform is refused by the Recorded Owner Decision 2026-09-21 "
    "clean restart (docs/decisions/owner-decision-2026-09-21-5c-5d-clean-restart.md) "
    "whatever package identity the candidate carries; this suite is retired with "
    "the superseded work, not repaired"
)


def finalize_in_fresh_db(  # type: ignore[no-untyped-def]
    candidate: CandidateRelease, *, core: bool = False, source: bool = False
):
    """Finalize *candidate* against a brand-new, already-committed in-memory DB
    plus a private, isolated on-disk Chroma store and the deterministic offline
    embedding function.

    ``core=False`` (default) uses the production ``finalize_release`` (with its
    completeness guard) — for the full-SRD candidate. ``core=True`` uses the
    private ``_finalize_core`` seam, which skips the completeness guard so a
    compact (partial) candidate can still exercise the persist/gate lifecycle.
    ``source=True`` uses ``finalize_source_release``, the production entry for
    the Markdown-built corpus, whose guards are the ones that mean something on
    that path.
    Returns the ``FinalizeResult``; the caller asserts ``published``/``reused``.

    The helper itself is shared lifecycle machinery, not a quarantined product:
    what the Recorded Owner Decision retires is the PDF-geometric *transform*,
    so the refusal lives on the candidate that carries that recipe
    (``full_candidate``) and the source-built corpus finalizes through here for
    real.
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
    if core:
        finalize = _finalize_core
    else:
        finalize = finalize_source_release if source else finalize_release
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

    Every consumer of this fixture -- directly, or through ``compact_candidate``
    and the releases derived from them -- is asserting about the quarantined
    PDF-geometric product, so the refusal is raised here, once, at the single
    point where that recipe enters a test.
    """
    pytest.skip(QUARANTINED_RECONSTRUCTION)
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


@pytest.fixture(scope="session")
def source_candidate() -> CandidateRelease:
    """The real Markdown-source-built candidate, built once for the session.

    The replacement for ``full_candidate``: same production build machinery, but
    from the qualified snapshot rather than the retired PDF geometry, so it is
    not the quarantined product and finalizes for real. It costs about half a
    minute (the official PDF still has to be extracted for the citations), which
    is why every module that needs it shares this one build.
    """
    return build_source_candidate(REPO_ROOT, retrieval_config=RetrievalMemoryConfig())


@pytest.fixture(scope="session")
def source_release_db(tmp_path_factory, source_candidate: CandidateRelease) -> Path:  # type: ignore[no-untyped-def]
    """The replacement corpus published through the real lifecycle into a file.

    A *file* rather than ``sqlite://`` so the persisted state outlives the
    session that wrote it: CRD Issue 5d reads 5c's published tables back through
    ``load_bound_corpus``, and proving that against the real release means
    opening a fresh session on state the 5c lifecycle actually committed, not on
    an in-memory database that vanishes with its engine.

    Isolated on both stores -- a private temporary SQLite file and a private
    Chroma directory -- so nothing here can touch a shared one.
    """
    db_path = tmp_path_factory.mktemp("published-source") / "afterworlds.db"
    engine = create_engine(f"sqlite:///{db_path}")

    @event.listens_for(engine, "connect")
    def _fk(dbapi, _rec):  # type: ignore[no-untyped-def]
        dbapi.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    factory = create_session_factory(engine)
    client = build_isolated_test_chroma_client(
        tempfile.mkdtemp(prefix="source-release-chroma-")
    )
    try:
        with factory() as session:
            result = finalize_source_release(
                session,
                source_candidate,
                now=NOW,
                chroma_client=client,
                retrieval_config=RetrievalMemoryConfig(),
                embedding_function=DeterministicFakeEmbeddingFunction(),
            )
    finally:
        engine.dispose()
    assert result.published and result.artifacts is not None, result.gate
    return db_path
