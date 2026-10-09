"""Bound-corpus resolution — CRD Issue 5d, against real persisted 5c rows.

The snapshot is the single source of release-scoped truth the validators read,
so what it includes and excludes decides whether a prose binding resolves to
real authority. These tests use actual `rp_ledger_leaves`, `rp_chunks`, and
`rp_corpus_projections` rows rather than a hand-built snapshot.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from sqlalchemy import delete
from sqlalchemy.exc import MultipleResultsFound
from sqlalchemy.orm import Session

from afterworlds.ingestion.mechanical.bound_corpus import (
    BoundCorpusSnapshot,
    ChunkCoverage,
    leaves_under,
    load_bound_corpus,
    published_release_binding,
)
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.persistence.orm.base import Base
from afterworlds.persistence.orm.corpus import (
    CorpusProjectionORM,
    CorpusReleaseORM,
    LedgerContainerORM,
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
    session: Session,
    package_uuid: str,
    leaf_id: str,
    content: str,
    disposition: str,
    container_path: list[str] | None = None,
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
            container_path=container_path or [],
            disposition=disposition,
        )
    )


def _container(
    session: Session,
    package_uuid: str,
    container_id: str,
    label: str,
    parent_id: str | None,
) -> None:
    session.add(
        LedgerContainerORM(
            package_uuid=package_uuid,
            container_id=container_id,
            container_type="section",
            label=label,
            printed_page=1,
            parent_id=parent_id,
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


# ---------------------------------------------------------------------------
# Section selection
# ---------------------------------------------------------------------------


@pytest.fixture()
def selection_session(session: Session) -> Session:
    """The bound package plus a container tree to select sections out of.

    Layered on the shared fixture rather than folded into it: the snapshot
    tests above assert an exact represented population, and adding leaves for a
    different concern would make those assertions about this fixture's contents
    instead of about the filter they exist to prove.

    ``Conditions`` appears twice at different depths, so a suffix match has
    something to be ambiguous about; ``c-cycle`` parents itself, so the label
    walk has a malformed row to terminate on.
    """
    _container(session, BOUND, "c-root", "Rules", None)
    _container(session, BOUND, "c-inner", "Conditions", "c-root")
    _container(session, BOUND, "c-odd", "Oddly Nested", "c-root")
    _container(session, BOUND, "c-deep", "Conditions", "c-odd")
    _container(session, BOUND, "c-cycle", "Cyclic", "c-cycle")
    _leaf(session, BOUND, "leaf-in-section", "in section", "represented", ["c-inner"])
    _leaf(session, BOUND, "leaf-deeper", "deeper", "represented", ["c-odd", "c-deep"])
    _leaf(session, BOUND, "leaf-cyclic", "cyclic", "represented", ["c-cycle"])
    _leaf(session, BOUND, "leaf-unrepresented", "dropped", "excluded", ["c-inner"])
    session.flush()
    return session


def test_selection_matches_a_container_path_suffix(selection_session: Session) -> None:
    """A bare label selects every container path ending in it.

    Both the shallow and the deep ``Conditions`` match, which is the point: the
    source decides the depth, so a caller that wants only one qualifies it.
    """
    assert leaves_under(selection_session, BOUND, "rel-1", ("Conditions",)) == (
        "leaf-deeper",
        "leaf-in-section",
    )
    assert leaves_under(
        selection_session, BOUND, "rel-1", ("Oddly Nested", "Conditions")
    ) == ("leaf-deeper",)
    assert leaves_under(selection_session, BOUND, "rel-1", ("Rules", "Conditions")) == (
        "leaf-in-section",
    )


def test_selection_offers_only_what_the_release_represents(
    selection_session: Session,
) -> None:
    """An excluded leaf under the same container is never selected.

    Selection and the snapshot read the same predicate, so a selector cannot
    hand the authoring path a leaf the binding seam would refuse.
    """
    selected = leaves_under(selection_session, BOUND, "rel-1", ("Conditions",))
    assert "leaf-unrepresented" not in selected
    assert set(selected) <= set(
        load_bound_corpus(selection_session, BOUND, "rel-1").leaf_lengths
    )


def test_selection_needs_a_label(selection_session: Session) -> None:
    """An empty selection is a caller mistake, not "everything"."""
    with pytest.raises(ValueError, match="at least one container label"):
        leaves_under(selection_session, BOUND, "rel-1", ())


def test_an_unknown_label_selects_nothing(selection_session: Session) -> None:
    """No approximation, no nearest match -- a label the source does not print
    selects nothing at all."""
    assert leaves_under(selection_session, BOUND, "rel-1", ("Not A Heading",)) == ()


def test_a_cyclic_parent_link_terminates(selection_session: Session) -> None:
    """Malformed stored parent links select, they do not hang.

    A ledger should never contain one; if it does, the authoring path should
    fail visibly at the next check rather than never returning.
    """
    assert leaves_under(selection_session, BOUND, "rel-1", ("Cyclic",)) == (
        "leaf-cyclic",
    )


def test_selection_is_scoped_to_the_bound_package(selection_session: Session) -> None:
    """Another package's containers and leaves are never reached."""
    assert leaves_under(selection_session, OTHER, "rel-1", ("Conditions",)) == ()


def test_a_subspan_binds_to_its_one_covering_chunk(session: Session) -> None:
    snapshot = load_bound_corpus(session, BOUND, "rel-1")
    assert snapshot.unique_chunk_range("leaf-represented", 2, 8) == (
        "chunk-projected",
        2,
        8,
    )
    # Past the covered run, and on a leaf no chunk covers: nothing to bind.
    assert snapshot.unique_chunk_range("leaf-represented", 0, 11) is None
    assert snapshot.unique_chunk_range("leaf-excluded", 0, 5) is None


def test_two_covering_chunks_bind_to_neither() -> None:
    snapshot = BoundCorpusSnapshot(
        package_uuid=BOUND,
        release_version="rel-1",
        leaf_lengths={"leaf": 10},
        chunk_coverage=tuple(
            ChunkCoverage(cid, "leaf", 0, 10, "primary", f"proj-{cid}")
            for cid in ("chunk-a", "chunk-b")
        ),
    )
    assert snapshot.chunk_relative_range("chunk-a", "leaf", 1, 4) == (1, 4)
    # Either chunk alone translates the span; choosing one would be a guess.
    assert snapshot.unique_chunk_range("leaf", 1, 4) is None


def test_the_published_binding_is_read_back_from_the_one_release(
    session: Session,
) -> None:
    # Two packages' releases: which one is "published" is not decidable.
    with pytest.raises(MultipleResultsFound):
        published_release_binding(session)
    session.execute(
        delete(CorpusReleaseORM).where(CorpusReleaseORM.package_uuid == OTHER)
    )
    with pytest.raises(ValueError, match="records no persisted corpus digest"):
        published_release_binding(session)
    release = session.get(CorpusReleaseORM, BOUND)
    assert release is not None
    release.persisted_corpus_digest = "d" * 64
    binding = published_release_binding(session)
    assert (binding.package_uuid, binding.release_version) == (BOUND, "rel-1")
    assert binding.persisted_corpus_digest == "d" * 64
    assert binding.bundle_root_hash == "c" * 64
