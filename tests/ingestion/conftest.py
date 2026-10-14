"""Ingestion-wide fixtures: the real CRD Issue 5c source release.

Building the corpus from the qualified Markdown source (and extracting the
official PDF its citations point at) costs about half a minute, and publishing
it through the genuine persist -> reconstruct -> digest -> gate -> publish
lifecycle costs more. Both CRD Issue 5c's own tests and CRD Issue 5d's
shared-tool readiness proof need it, so the build and the publications live
here as session-scoped fixtures rather than in either subdirectory.

``source_release_db`` publishes into a file because CRD Issue 5d needs a *live
session over the very same published state*, which ``finalize_in_fresh_db``
cannot hand back: it closes its session and disposes its engine.

The original PDF-geometric candidate (``full_candidate`` and the releases built
from it) was retired with that corpus under the Recorded Owner Decision of
21 September 2026, Step 5.

Everything else stays where it is used. This module holds only what more than
one subdirectory needs.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
from sqlalchemy import event

# Story and Node: every story-scoped model's FK targets. Registered here so
# Base.metadata.create_all does not depend on which other test modules were
# collected first (an RPG import registers story-scoped tables alone).
import afterworlds.persistence.orm.node  # noqa: F401
import afterworlds.persistence.orm.story  # noqa: F401
from afterworlds.ingestion.corpus.persistence import (
    FinalizeResult,
    finalize_source_release,
)
from afterworlds.ingestion.corpus.pipeline import (
    CandidateRelease,
    ReleaseArtifacts,
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


def finalize_in_fresh_db(candidate: CandidateRelease) -> FinalizeResult:
    """Finalize *candidate* through ``finalize_source_release`` against a
    brand-new in-memory DB plus a private, isolated on-disk Chroma store and the
    deterministic offline embedding function.

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
    try:
        result = finalize_source_release(
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
def source_candidate() -> CandidateRelease:
    """The real Markdown-source-built candidate, built once for the session.

    It costs about half a minute (the official PDF still has to be extracted for
    the citations), which is why every module that needs it shares this one
    build.
    """
    return build_source_candidate(REPO_ROOT, retrieval_config=RetrievalMemoryConfig())


@pytest.fixture(scope="session")
def source_release(source_candidate: CandidateRelease) -> ReleaseArtifacts:
    """The source release finalized once through the real lifecycle.

    The completed post-persistence artifacts, for the generic gate and
    lifecycle assertions that read a published release rather than a store.
    """
    result = finalize_in_fresh_db(source_candidate)
    assert result.published and result.artifacts is not None, result.gate
    return result.artifacts


@pytest.fixture(scope="session")
def source_release_db(
    tmp_path_factory: pytest.TempPathFactory, source_candidate: CandidateRelease
) -> Path:
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


#: Where the pinned replay scripts under ``.claude/review-notes/`` read the
#: superseded release ``5.2.1-corpus.3fe24ff6-4e3`` (their ``SCRATCH_DB``). It is
#: a private ``.claude/_*`` scratch store that is never delivered, so a clean
#: checkout has no file there; the tests read a rebuilt copy instead.
SUPERSEDED_STORE = REPO_ROOT / ".claude" / "_rc" / "msc" / "rel" / "afterworlds.db"
_PRIVATE = (REPO_ROOT / ".claude").as_posix() + "/_"


def _refuse_private_stores(event: str, args: tuple[object, ...]) -> None:
    """Fail any test-time open of a private ``.claude/_*`` path, loudly.

    A present private store would otherwise mask a missing rebinding: the suite
    would pass where the store happens to exist and fail on a clean checkout.
    """
    if (
        event in ("open", "sqlite3.connect")
        and isinstance(args[0], (str, bytes, os.PathLike))
        and _PRIVATE in os.fsdecode(args[0]).replace("\\", "/")
    ):
        raise PermissionError(f"test read a private store: {args[0]!r}")


sys.addaudithook(_refuse_private_stores)


@pytest.fixture(scope="session")
def superseded_release_db(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """The superseded release, rebuilt once from delivered inputs.

    Built in a child process by ``superseded_release.py``, which refuses any
    identity other than the delivered recorded one, so the replay scripts read
    the release they were recorded against. Isolated like ``source_release_db``.
    """
    db_path = tmp_path_factory.mktemp("superseded-release") / "afterworlds.db"
    subprocess.run(
        [sys.executable, str(Path(__file__).with_name("superseded_release.py"))]
        + [str(db_path), NOW],
        cwd=REPO_ROOT,
        check=True,
    )
    return db_path


def _rebind_superseded_store(request: pytest.FixtureRequest) -> None:
    stale = [
        module
        for module in list(sys.modules.values())
        if getattr(module, "__dict__", {}).get("SCRATCH_DB") == SUPERSEDED_STORE
    ]
    if stale:
        store = request.getfixturevalue("superseded_release_db")
        for module in stale:
            vars(module)["SCRATCH_DB"] = store


@pytest.fixture(scope="session", autouse=True)
def _superseded_store_for_session(request: pytest.FixtureRequest) -> None:
    """Point every loaded replay script at the rebuilt release.

    Session scope runs before any module-scoped fixture, after collection has
    loaded the scripts the test modules name at import.
    """
    _rebind_superseded_store(request)


@pytest.fixture(autouse=True)
def _superseded_store_for_test(request: pytest.FixtureRequest) -> None:
    """Rebind scripts first loaded since, through a fixture or an earlier test."""
    _rebind_superseded_store(request)
