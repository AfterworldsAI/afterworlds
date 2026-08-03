"""Fixtures for the Issue 5c corpus-integrity suite.

The real corpus build (extraction + ledger + reconcile + digest) is expensive,
so the candidate is built once per session and shared; ``release`` additionally
finalizes it (persist -> reconstruct -> prove -> gate -> publish) once against a
private, already-committed store, so it exercises the *real* Component K c-g
lifecycle rather than an in-memory approximation. Adversarial gate/findings
tests use small synthetic ledgers built by :func:`synthetic_release` and run
fast.

``full_candidate``, ``full_release``, and ``finalize_in_fresh_db`` live in the
parent ``tests/ingestion/conftest.py``: the CRD Issue 5d production-corpus
control needs the same real release, and one session-scoped definition means
one build rather than two. They are re-exported here so this suite's modules
keep importing them from ``.conftest``.
"""

from __future__ import annotations

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
from afterworlds.ingestion.corpus.pipeline import CandidateRelease, ReleaseArtifacts
from afterworlds.ingestion.corpus.policy import FROZEN_POLICY, policy_hash
from afterworlds.ingestion.corpus.reconcile import reconcile
from afterworlds.ingestion.corpus.transform import build_corpus
from afterworlds.models.retrieval import rules_corpus_vector_identity
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.persistence.orm.base import Base
from afterworlds.pipeline.retrieval.client import build_isolated_test_chroma_client
from afterworlds.pipeline.retrieval.config import RetrievalMemoryConfig
from afterworlds.pipeline.retrieval.embedding import DeterministicFakeEmbeddingFunction
from tests.ingestion.conftest import (  # noqa: F401  (re-exported for this suite)
    NOW,
    PDF_PATH,
    finalize_in_fresh_db,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


# The six version-canary pages (Component J). A candidate restricted to just
# these pages (~250 chunks vs 13,658) is a *partial* corpus: it exercises the
# complete, unmocked persist/reconstruct/digest/gate/reindex machinery via the
# private ``_finalize_core`` seam at a fraction of the cost, but it is NOT
# authoritative-source-complete, so the public ``finalize_release`` correctly
# rejects it (PR #134 completeness proof) — see ``compact_candidate`` and the
# six-page negative control in test_persistence_quarantine.
_CANARY_PAGES = frozenset(c.printed_page for c in VERSION_CANARIES)


def _candidate_from_pages(
    pages: list[ExtractedPage], embedding_model_id: str
) -> CandidateRelease:
    """Assemble a real CandidateRelease from a subset of already-extracted PDF
    pages via the production pipeline (build_ledger → build_corpus → reconcile →
    build_bundle). No mocks: the result binds the real ``PDF_SHA256`` and
    extraction config and exercises the genuine build machinery — but a canary-
    page subset is a *partial* corpus that the public completeness proof rejects;
    it is finalized only via the private ``_finalize_core`` seam."""
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
def candidate(full_candidate: CandidateRelease) -> CandidateRelease:
    """The full-SRD candidate (default). Other corpus test modules consume the
    complete corpus through this name."""
    return full_candidate


@pytest.fixture(scope="session")
def compact_candidate(full_candidate: CandidateRelease) -> CandidateRelease:
    """A real candidate restricted to the six version-canary pages (~250 chunks
    vs 13,658). Reuses ``full_candidate``'s already-extracted pages (no extra PDF
    work) and runs the full production build pipeline, so tests using it exercise
    the genuine persist/digest/gate/reindex machinery via ``_finalize_core`` at a
    fraction of the cost. It is a *partial* corpus (six of 364 pages), so the
    public ``finalize_release`` completeness proof rejects it. Depends on
    ``full_candidate`` (never shadowed), not ``candidate``."""
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


@pytest.fixture(scope="session")
def release(full_release: ReleaseArtifacts) -> ReleaseArtifacts:
    """The full-SRD release (default). Other corpus test modules consume the
    complete corpus through this name."""
    return full_release


@pytest.fixture(scope="session")
def compact_release(compact_candidate: CandidateRelease) -> ReleaseArtifacts:
    """The compact (canary-page) candidate finalized once through the private
    ``_finalize_core`` seam — a genuine persist→reconstruct→digest→gate→publish,
    not an in-memory assembly, so persist/reconstruct/digest/tamper tests
    exercise the true lifecycle on a small corpus. The public completeness proof
    is intentionally bypassed here (this is a partial corpus); production
    publication of a partial corpus is proven to fail by the negative control."""
    result = finalize_in_fresh_db(compact_candidate, core=True)
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
