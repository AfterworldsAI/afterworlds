"""Fixtures for the Issue 5c corpus-integrity suite.

The real source release is built and published once per session in the parent
``tests/ingestion/conftest.py`` and exposed here as ``release``, so the generic
gate and lifecycle tests exercise the genuine Component K c-g lifecycle on the
current corpus. Adversarial gate/findings tests use small synthetic ledgers and
run fast.

``source_candidate`` and ``finalize_in_fresh_db`` live in the parent conftest
because CRD Issue 5d's shared-tool readiness proof needs the same release; they
are re-exported here so this suite's modules keep importing them from
``.conftest``. The retired PDF-geometric candidates (``candidate`` built from the
PDF, and the six-canary-page ``compact_candidate``) were removed with that corpus.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import event

from afterworlds.ingestion.corpus.hashing import content_id
from afterworlds.ingestion.corpus.models import (
    Container,
    ContainerType,
    Leaf,
    LeafType,
    SourceLedger,
)
from afterworlds.ingestion.corpus.pipeline import ReleaseArtifacts
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.persistence.orm.base import Base
from afterworlds.pipeline.retrieval.client import build_isolated_test_chroma_client
from afterworlds.pipeline.retrieval.config import RetrievalMemoryConfig
from afterworlds.pipeline.retrieval.embedding import DeterministicFakeEmbeddingFunction
from tests.ingestion.conftest import (
    NOW,
    PDF_PATH,
    finalize_in_fresh_db,
    source_candidate,
    source_release,
)

# Re-exported for this suite's modules (see the module docstring).
__all__ = [
    "NOW",
    "PDF_PATH",
    "finalize_in_fresh_db",
    "source_candidate",
    "source_release",
]

REPO_ROOT = Path(__file__).resolve().parents[3]


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
def release(source_release: ReleaseArtifacts) -> ReleaseArtifacts:
    """The published source release under the name the generic gate and
    lifecycle tests use."""
    return source_release


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
