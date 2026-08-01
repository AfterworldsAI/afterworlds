"""Bound-corpus resolution — CRD Issue 5d, against real persisted 5c rows.

The snapshot is the single source of release-scoped truth the validators read,
so what it includes and excludes decides whether a prose binding resolves to
real authority. These tests use actual `rp_ledger_leaves`, `rp_chunks`, and
`rp_corpus_projections` rows rather than a hand-built snapshot.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from sqlalchemy.orm import Session

from afterworlds.ingestion.mechanical.bound_corpus import load_bound_corpus
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.persistence.orm.base import Base
from afterworlds.persistence.orm.corpus import (
    CorpusProjectionORM,
    CorpusReleaseORM,
    LedgerLeafORM,
)
from afterworlds.persistence.orm.rules_package import (
    RuleChunkORM,
    RuleSourceORM,
    RulesPackageORM,
)

BOUND = "pkg-bound"
OTHER = "pkg-other"
NOW = "2026-07-31T00:00:00Z"


def _package(session: Session, package_uuid: str) -> None:
    session.add(
        RulesPackageORM(
            rules_package_id=package_uuid,
            name=f"SRD ({package_uuid})",
            system="dnd5e",
            version="5.2.1",
            is_enabled=True,
            publication_status="published",
            created_at=NOW,
            updated_at=NOW,
        )
    )
    session.flush()
    session.add(
        CorpusReleaseORM(
            package_uuid=package_uuid,
            release_version="rel-1",
            authoritative_source_hash="a" * 64,
            transform_config_hash="b" * 64,
            bundle_root_hash="c" * 64,
            ledger_hash="1" * 64,
            policy_hash="2" * 64,
            reconciliation_hash="3" * 64,
            transform_config={},
            publication_status="published",
            created_at=NOW,
        )
    )
    session.add(
        RuleSourceORM(
            source_id=f"src-{package_uuid}",
            rules_package_id=package_uuid,
            name="SRD",
            category="core",
            precedence_rank=1,
            is_enabled=True,
            created_at=NOW,
        )
    )
    session.flush()


def _leaf(
    session: Session, package_uuid: str, leaf_id: str, content: str, disposition: str
) -> None:
    session.add(
        LedgerLeafORM(
            package_uuid=package_uuid,
            leaf_id=leaf_id,
            printed_page=1,
            page_index=0,
            leaf_type="paragraph",
            content=content,
            char_start=0,
            char_end=len(content),
            occurrence_index=0,
            container_path=[],
            disposition=disposition,
        )
    )


def _chunk(session: Session, package_uuid: str, chunk_id: str) -> None:
    session.add(
        RuleChunkORM(
            chunk_id=chunk_id,
            rules_package_id=package_uuid,
            source_id=f"src-{package_uuid}",
            subsystem="general",
            content="governing prose",
            source_document="SRD",
            source_locator_type="page",
            source_locator_value="1",
            created_at=NOW,
        )
    )


def _projected(
    session: Session, package_uuid: str, chunk_id: str, leaf_id: str
) -> None:
    session.add(
        CorpusProjectionORM(
            package_uuid=package_uuid,
            projection_id=f"proj-{chunk_id}",
            leaf_id=leaf_id,
            chunk_id=chunk_id,
            role="primary",
            cover_start=0,
            cover_end=10,
        )
    )


@pytest.fixture()
def session(tmp_path) -> Iterator[Session]:  # type: ignore[no-untyped-def]
    engine = create_engine(f"sqlite:///{tmp_path / 'corpus.db'}")
    Base.metadata.create_all(engine)
    with create_session_factory(engine)() as s:
        _package(s, BOUND)
        _package(s, OTHER)

        _leaf(s, BOUND, "leaf-represented", "twelve chars", "represented")
        _leaf(s, BOUND, "leaf-excluded", "excluded text", "excluded")
        _leaf(s, OTHER, "leaf-elsewhere", "other package", "represented")

        _chunk(s, BOUND, "chunk-projected")
        _chunk(s, BOUND, "chunk-unprojected")
        _chunk(s, OTHER, "chunk-other-package")
        _projected(s, BOUND, "chunk-projected", "leaf-represented")
        # Projected in the other package only.
        _projected(s, OTHER, "chunk-other-package", "leaf-elsewhere")
        # Declared projected here but with no chunk row behind it.
        _projected(s, BOUND, "chunk-phantom", "leaf-represented")
        s.flush()
        yield s


def test_leaf_lengths_cover_only_the_represented_population(session: Session) -> None:
    snapshot = load_bound_corpus(session, BOUND, "rel-1")
    # 5c exclusions stay excluded: an excluded leaf is neither required to be
    # classified nor allowed to be.
    assert snapshot.leaf_lengths == {"leaf-represented": len("twelve chars")}


def test_snapshot_is_scoped_to_the_bound_package(session: Session) -> None:
    snapshot = load_bound_corpus(session, BOUND, "rel-1")
    assert "leaf-elsewhere" not in snapshot.leaf_lengths
    assert "chunk-other-package" not in snapshot.authoritative_chunk_ids


def test_authoritative_chunks_require_both_halves(session: Session) -> None:
    snapshot = load_bound_corpus(session, BOUND, "rel-1")
    # Projected *and* persisted under this package.
    assert snapshot.authoritative_chunk_ids == frozenset({"chunk-projected"})
    # Exists in rp_chunks but was never projected into this release.
    assert "chunk-unprojected" not in snapshot.authoritative_chunk_ids
    # Projected but has no chunk row behind it.
    assert "chunk-phantom" not in snapshot.authoritative_chunk_ids


def test_unknown_package_resolves_to_an_empty_snapshot(session: Session) -> None:
    snapshot = load_bound_corpus(session, "pkg-missing", "rel-1")
    assert snapshot.leaf_lengths == {}
    assert snapshot.authoritative_chunk_ids == frozenset()


def test_coverage_edges_round_trip_from_real_projection_rows(session: Session) -> None:
    snapshot = load_bound_corpus(session, BOUND, "rel-1")
    edges = {
        (c.chunk_id, c.leaf_id, c.cover_start, c.cover_end, c.role)
        for c in snapshot.chunk_coverage
    }
    assert edges == {("chunk-projected", "leaf-represented", 0, 10, "primary")}
    # projection_id survives too, so the relation is not a lossy copy.
    assert all(c.projection_id for c in snapshot.chunk_coverage)


def test_phantom_and_unprojected_chunks_carry_no_coverage(session: Session) -> None:
    snapshot = load_bound_corpus(session, BOUND, "rel-1")
    assert not snapshot.covers_span("chunk-phantom", "leaf-represented", 0, 5)
    assert not snapshot.covers_span("chunk-unprojected", "leaf-represented", 0, 5)
    assert "chunk-phantom" not in snapshot.authoritative_chunk_ids
    assert "chunk-unprojected" not in snapshot.authoritative_chunk_ids


def test_coverage_answers_containment_for_the_bound_release(session: Session) -> None:
    snapshot = load_bound_corpus(session, BOUND, "rel-1")
    assert snapshot.covers_span("chunk-projected", "leaf-represented", 0, 10)
    assert snapshot.covers_span("chunk-projected", "leaf-represented", 2, 8)
    assert not snapshot.covers_span("chunk-projected", "leaf-represented", 0, 11)
    assert not snapshot.covers_span("chunk-projected", "leaf-elsewhere", 0, 5)


def test_another_packages_projection_edges_are_never_read(session: Session) -> None:
    # The validator must not claim to resolve one release while reading
    # another package's edges.
    snapshot = load_bound_corpus(session, BOUND, "rel-1")
    assert all(c.chunk_id != "chunk-other-package" for c in snapshot.chunk_coverage)
    other = load_bound_corpus(session, OTHER, "rel-1")
    assert other.authoritative_chunk_ids == frozenset({"chunk-other-package"})
    assert other.covers_span("chunk-other-package", "leaf-elsewhere", 0, 10)
    assert not other.covers_span("chunk-projected", "leaf-represented", 0, 10)
