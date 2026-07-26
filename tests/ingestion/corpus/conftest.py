"""Fixtures for the Issue 5c corpus-integrity suite.

The real corpus build (extraction + ledger + reconcile + digest) is expensive,
so the candidate is built once per session and shared; ``release`` additionally
finalizes it (persist -> reconstruct -> prove -> gate -> publish) once against a
private, already-committed store, so it exercises the *real* Component K c-g
lifecycle rather than an in-memory approximation. Adversarial gate/findings
tests use small synthetic ledgers built by :func:`synthetic_release` and run
fast.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from sqlalchemy import event

from afterworlds.ingestion.corpus.bundle import (
    build_bundle,
    derive_package_uuid,
    derive_release_version,
    reconciliation_hash,
    transform_config_hash,
    transform_config_payload,
)
from afterworlds.ingestion.corpus.concordance import VERSION_CANARIES
from afterworlds.ingestion.corpus.hashing import content_id
from afterworlds.ingestion.corpus.ledger import build_ledger, ledger_hash
from afterworlds.ingestion.corpus.models import (
    Container,
    ContainerType,
    Leaf,
    LeafType,
    SourceLedger,
)
from afterworlds.ingestion.corpus.pdf_source import (
    PDF_SHA256,
    ExtractedPage,
    extraction_config,
)
from afterworlds.ingestion.corpus.persistence import finalize_release
from afterworlds.ingestion.corpus.pipeline import (
    CandidateRelease,
    ReleaseArtifacts,
    build_candidate,
)
from afterworlds.ingestion.corpus.policy import FROZEN_POLICY, policy_hash
from afterworlds.ingestion.corpus.reconcile import reconcile
from afterworlds.ingestion.corpus.transform import build_corpus
from afterworlds.models.retrieval import rules_corpus_vector_identity
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.persistence.orm.base import Base
from afterworlds.pipeline.retrieval.client import build_isolated_test_chroma_client
from afterworlds.pipeline.retrieval.config import RetrievalMemoryConfig
from afterworlds.pipeline.retrieval.embedding import DeterministicFakeEmbeddingFunction

REPO_ROOT = Path(__file__).resolve().parents[3]
PDF_PATH = REPO_ROOT / "docs" / "sources" / "DnD5_5e_SRD_CC_v5_2_1.pdf"

NOW = "2026-07-23T00:00:00Z"


# The six version-canary pages (Component J) — the minimum real SRD pages a
# candidate must contain to pass the production publication gate's canary +
# concordance checks. A candidate restricted to just these pages (~250 chunks vs
# 13,658) still exercises the *complete, unmocked* finalize/gate/persist/reindex
# path — see ``compact_candidate``.
_CANARY_PAGES = frozenset(c.printed_page for c in VERSION_CANARIES)


def _candidate_from_pages(
    pages: list[ExtractedPage], embedding_model_id: str
) -> CandidateRelease:
    """Assemble a real CandidateRelease from a subset of already-extracted PDF
    pages via the production pipeline (build_ledger → build_corpus → reconcile →
    build_bundle). No mocks: the result binds the real ``PDF_SHA256`` and
    extraction config, so a canary-page subset passes the genuine gate."""
    ledger = build_ledger(pages)
    ex = extraction_config()
    vid = rules_corpus_vector_identity(embedding_model_id)
    tconfig = transform_config_payload(ex, FROZEN_POLICY, vid)
    thash = transform_config_hash(ex, FROZEN_POLICY, vid)
    pkg = derive_package_uuid(PDF_SHA256, thash)
    members = build_corpus(ledger, pkg)
    recon = reconcile(ledger, members, FROZEN_POLICY)
    bundle = build_bundle(ledger, members, recon)
    return CandidateRelease(
        pages=pages,
        ledger=ledger,
        members=members,
        reconciliation=recon,
        policy=FROZEN_POLICY,
        bundle=bundle,
        package_uuid=pkg,
        release_version=derive_release_version(PDF_SHA256, thash),
        authoritative_source_hash=PDF_SHA256,
        transform_config_hash=thash,
        transform_config=tconfig,
        ledger_hash=ledger_hash(ledger),
        policy_hash=policy_hash(FROZEN_POLICY),
        reconciliation_hash=reconciliation_hash(recon),
    )


@pytest.fixture(scope="session")
def full_candidate() -> CandidateRelease:
    """The real full-SRD pre-persistence candidate, built once for the session.

    This is the primary build (no fixture dependencies), so a test module may
    safely shadow ``candidate`` with the compact one without recursion.
    """
    return build_candidate(PDF_PATH, retrieval_config=RetrievalMemoryConfig())


@pytest.fixture(scope="session")
def candidate(full_candidate: CandidateRelease) -> CandidateRelease:
    """The full-SRD candidate (default). Other corpus test modules consume the
    complete corpus through this name."""
    return full_candidate


@pytest.fixture(scope="session")
def compact_candidate(full_candidate: CandidateRelease) -> CandidateRelease:
    """A real, gate-passing candidate restricted to the six version-canary pages
    (~250 chunks vs 13,658). Reuses ``full_candidate``'s already-extracted pages
    (no extra PDF work) and runs the full production pipeline, so tests using it
    exercise the genuine finalize/gate/persist/reindex path at a fraction of the
    cost. Depends on ``full_candidate`` (never shadowed), not ``candidate``."""
    subset = [p for p in full_candidate.pages if p.printed_page in _CANARY_PAGES]
    return _candidate_from_pages(subset, RetrievalMemoryConfig().embedding_model_id)


@pytest.fixture()
def retrieval_config() -> RetrievalMemoryConfig:
    """Default retrieval config (deterministic; local ONNX model id)."""
    return RetrievalMemoryConfig()


@pytest.fixture()
def fake_embedding() -> DeterministicFakeEmbeddingFunction:
    """Explicit offline embedding function — never selected implicitly."""
    return DeterministicFakeEmbeddingFunction()


@pytest.fixture()
def chroma_client(tmp_path):  # type: ignore[no-untyped-def]
    """A fully isolated on-disk Chroma client rooted at a per-test tmp dir."""
    return build_isolated_test_chroma_client(str(tmp_path / "chroma"))


def finalize_in_fresh_db(candidate: CandidateRelease):  # type: ignore[no-untyped-def]
    """Finalize *candidate* against a brand-new, already-committed in-memory DB
    plus a private, isolated on-disk Chroma store and the deterministic offline
    embedding function.

    Returns the ``FinalizeResult``; the caller is responsible for asserting
    ``published``/``reused`` as appropriate to the test.
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
        result = finalize_release(
            sess,
            candidate,
            repo_root=REPO_ROOT,
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
def full_release(full_candidate: CandidateRelease) -> ReleaseArtifacts:
    """The real full-SRD corpus release, finalized once for the whole session.

    Goes through the actual publish lifecycle (finalize_release) rather than
    being assembled in memory, so every test that reads from this fixture is
    implicitly exercising Component K's full acyclic c-g order. Depends on
    ``full_candidate`` (never shadowed) to keep the shadow-safe dependency chain.
    """
    result = finalize_in_fresh_db(full_candidate)
    assert result.published and result.artifacts is not None, result.gate
    return result.artifacts


@pytest.fixture(scope="session")
def release(full_release: ReleaseArtifacts) -> ReleaseArtifacts:
    """The full-SRD release (default). Other corpus test modules consume the
    complete corpus through this name."""
    return full_release


@pytest.fixture(scope="session")
def compact_release(compact_candidate: CandidateRelease) -> ReleaseArtifacts:
    """The compact (canary-page) candidate finalized once — a genuine publish
    through the real gate, not an in-memory assembly, so persist/reconstruct/
    digest tests exercise the true lifecycle on a small corpus."""
    result = finalize_in_fresh_db(compact_candidate)
    assert result.published and result.artifacts is not None, result.gate
    return result.artifacts


@pytest.fixture()
def engine():  # type: ignore[no-untyped-def]
    eng = create_engine("sqlite://")

    @event.listens_for(eng, "connect")
    def _fk(dbapi, _rec):  # type: ignore[no-untyped-def]
        dbapi.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)
    eng.dispose()


@pytest.fixture()
def session(engine):  # type: ignore[no-untyped-def]
    factory = create_session_factory(engine)
    sess = factory()
    try:
        yield sess
    finally:
        sess.close()


def make_leaf(
    page: int,
    leaf_type: LeafType,
    content: str,
    char_start: int,
    occurrence: int,
    container_path: tuple[str, ...] = (),
) -> Leaf:
    """Build a single synthetic leaf with a content-derived id."""
    end = char_start + len(content)
    return Leaf(
        leaf_id=content_id("leaf", page, char_start, end, leaf_type.value, content),
        printed_page=page,
        page_index=page - 1,
        leaf_type=leaf_type,
        content=content,
        char_start=char_start,
        char_end=end,
        occurrence_index=occurrence,
        container_path=container_path,
    )


def synthetic_ledger(leaves: list[Leaf], containers: list[Container]) -> SourceLedger:
    return SourceLedger(
        source_document="D&D SRD 5.2.1",
        source_version="5.2.1",
        source_sha256="0" * 64,
        extraction_config={"tool": "synthetic"},
        containers=tuple(containers),
        leaves=tuple(leaves),
    )


def simple_container(
    label: str, ctype: ContainerType = ContainerType.SECTION
) -> Container:
    return Container(
        container_id=content_id("container", ctype.value, label, 1, None),
        container_type=ctype,
        label=label,
        printed_page=1,
        parent_id=None,
    )
