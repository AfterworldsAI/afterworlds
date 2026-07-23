"""Fixtures for the Issue 5c corpus-integrity suite.

The real corpus build (extraction + ledger + reconcile + digest) is expensive,
so it is built once per session and shared. Adversarial gate/findings tests use
small synthetic ledgers built by :func:`synthetic_release` and run fast.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from afterworlds.ingestion.corpus.hashing import content_id
from afterworlds.ingestion.corpus.models import (
    Container,
    ContainerType,
    Leaf,
    LeafType,
    SourceLedger,
)
from afterworlds.ingestion.corpus.pipeline import ReleaseArtifacts, build_release
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.persistence.orm.base import Base

REPO_ROOT = Path(__file__).resolve().parents[3]
PDF_PATH = REPO_ROOT / "docs" / "sources" / "DnD5_5e_SRD_CC_v5_2_1.pdf"


@pytest.fixture(scope="session")
def release() -> ReleaseArtifacts:
    """The real corpus release, built once for the whole test session."""
    return build_release(PDF_PATH)


@pytest.fixture()
def engine():  # type: ignore[no-untyped-def]
    eng = create_engine("sqlite://")

    from sqlalchemy import event

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
