"""The bound 5c corpus a candidate is validated against — CRD Issue 5d.

Validation needs three things from the exact published CRD Issue 5c release:
how long each represented leaf's canonical text is, which chunks are
authoritative governing prose for that release, and — the part that makes exact
prose provenance checkable — *which subspans of which leaves each chunk
actually covers*.

All three are resolved here, once, into a frozen snapshot. The validators stay
pure functions over it, so there is one release-scoped resolution seam and no
validator can accidentally read a different release than the candidate claims.

Coverage is the single truth about chunks. Authoritative membership is derived
from it rather than supplied alongside it, so a snapshot cannot claim a chunk
is authoritative while carrying no projection coverage for it — the state that
made a cross-chunk provenance claim look valid.

A chunk counts as authoritative only when both halves of the 5c contract hold:
it exists in ``rp_chunks`` under the bound package, and it has at least one
``rp_corpus_projections`` edge under that package. A projected phantom with no
chunk row and a persisted chunk that was never projected are both excluded, and
because membership is derived, exclusion also removes its coverage.

**Coordinate system.** ``cover_start``/``cover_end`` are half-open offsets into
the source *leaf's* content — CRD Issue 5c states this on ``ProjectionEdge``
and proves it by slicing ``leaf.content[cover_start:cover_end]`` in its own
publication gate. CRD Issue 5d semantic spans index that same leaf content.
The two coordinate systems are therefore identical, which is what makes the
containment test below meaningful rather than a coincidence of integers.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from functools import cached_property

from sqlalchemy import select
from sqlalchemy.orm import Session

from afterworlds.ingestion.corpus.models import Disposition
from afterworlds.ingestion.corpus.operational import OperationalCorpusSnapshot
from afterworlds.ingestion.mechanical.models import ReleaseBinding
from afterworlds.persistence.orm.corpus import (
    CorpusProjectionORM,
    CorpusReleaseORM,
    LedgerContainerORM,
    LedgerLeafORM,
)
from afterworlds.persistence.orm.rules_package import RuleChunkORM
from afterworlds.quarantine import refuse_quarantined

__all__ = [
    "BoundCorpusSnapshot",
    "ChunkCoverage",
    "bound_corpus_from_operational",
    "leaves_under",
    "load_bound_corpus",
    "published_release_binding",
]


@dataclass(frozen=True)
class ChunkCoverage:
    """One 5c projection edge: a chunk covering a subspan of one leaf.

    ``role`` and ``projection_id`` are retained rather than dropped — losing
    them would make this a lossy copy of the 5c relation, and role is what
    distinguishes ordinary authoritative coverage from the attribution repeat
    5c permits to overlap.
    """

    chunk_id: str
    leaf_id: str
    cover_start: int
    cover_end: int
    role: str
    projection_id: str


def _merge(intervals: list[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    """Merge half-open intervals, joining adjacent and overlapping ones.

    Adjacency counts as continuous: ``[0,10)`` followed by ``[10,20)`` is one
    covered run, because the leaf text between them has no hole. Merging here
    rather than at query time means a span crossing two consecutive edges of
    the same chunk is covered, while a span crossing a genuine gap is not.
    """
    merged: list[tuple[int, int]] = []
    for start, end in sorted(intervals):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return tuple(merged)


@dataclass(frozen=True)
class BoundCorpusSnapshot:
    """Authoritative facts about one published 5c release, resolved once.

    ``leaf_lengths`` covers exactly the ``REPRESENTED`` population — the
    accounting population #137 contract 1 defines — so a leaf 5c excluded is
    neither required to be classified nor allowed to be.
    """

    package_uuid: str
    release_version: str
    leaf_lengths: Mapping[str, int]
    chunk_coverage: tuple[ChunkCoverage, ...]

    @cached_property
    def authoritative_chunk_ids(self) -> frozenset[str]:
        """Chunks that actually project into this release, derived from coverage."""
        return frozenset(c.chunk_id for c in self.chunk_coverage)

    @cached_property
    def _covered_runs(self) -> dict[tuple[str, str], tuple[tuple[int, int], ...]]:
        by_pair: dict[tuple[str, str], list[tuple[int, int]]] = {}
        for edge in self.chunk_coverage:
            by_pair.setdefault((edge.chunk_id, edge.leaf_id), []).append(
                (edge.cover_start, edge.cover_end)
            )
        return {pair: _merge(spans) for pair, spans in by_pair.items()}

    def covers_span(
        self, chunk_id: str, leaf_id: str, char_start: int, char_end: int
    ) -> bool:
        """Does *chunk_id* cover this leaf subspan completely?

        The whole span must lie inside one covered run of that chunk on that
        leaf. Partial overlap fails, a different leaf fails, a span crossing a
        gap fails, and a chunk this release never projected fails — in every
        case the chunk does not actually contain the cited text, so it cannot
        be its governing prose.
        """
        if char_end <= char_start:
            return False
        for start, end in self._covered_runs.get((chunk_id, leaf_id), ()):
            if start <= char_start and char_end <= end:
                return True
        return False

    def chunk_relative_range(
        self, chunk_id: str, leaf_id: str, char_start: int, char_end: int
    ) -> tuple[int, int] | None:
        """Translate a leaf subspan into offsets in *chunk_id*'s own text.

        A prose binding names a chunk, but the accepted span is expressed in
        leaf coordinates. Exact prose resolution has to slice the chunk, so the
        two coordinate systems have to be related — and they only can be when
        this release's projection makes the relation unambiguous.

        Returns ``None`` — fail closed, never a guess — unless the chunk covers
        this leaf as **one** run *and* covers no other leaf. Both conditions
        matter: a chunk assembled from several leaves has an unknown prefix
        length before this leaf's text, and a chunk covering one leaf in two
        runs has an unknown gap inside it. In either case the offset cannot be
        derived, and inventing one would silently return the wrong sentence as
        governing authority.

        The production SRD 5.2.1 release satisfies both conditions everywhere —
        chunk and leaf are in strict bijection and every projection edge covers
        its whole leaf — but this does not assume that. It checks, per binding.
        """
        if not self.covers_span(chunk_id, leaf_id, char_start, char_end):
            return None
        covered_leaves = {
            edge.leaf_id for edge in self.chunk_coverage if edge.chunk_id == chunk_id
        }
        if len(covered_leaves) != 1:
            return None
        runs = self._covered_runs.get((chunk_id, leaf_id), ())
        if len(runs) != 1:
            return None
        run_start = runs[0][0]
        return char_start - run_start, char_end - run_start

    def unique_chunk_range(
        self, leaf_id: str, char_start: int, char_end: int
    ) -> tuple[str, int, int] | None:
        """The one chunk a leaf subspan can be bound to, in that chunk's offsets.

        The binding step every authoring batch repeats: of the chunks covering
        *leaf_id*, exactly one may translate the span through
        :meth:`chunk_relative_range`. ``None`` -- fail closed -- when none does,
        or when several do, because choosing between them would be a guess
        about which chunk governs.
        """
        hits = {
            edge.chunk_id: rng
            for edge in self.chunk_coverage
            if edge.leaf_id == leaf_id
            and (
                rng := self.chunk_relative_range(
                    edge.chunk_id, leaf_id, char_start, char_end
                )
            )
            is not None
        }
        if len(hits) != 1:
            return None
        ((chunk_id, (start, end)),) = hits.items()
        return chunk_id, start, end


def bound_corpus_from_operational(
    snapshot: OperationalCorpusSnapshot,
) -> BoundCorpusSnapshot:
    """Adapt the verified 5c-owned trust seam to 5d's validation view."""
    persisted = {chunk.chunk_id for chunk in snapshot.chunks}
    return BoundCorpusSnapshot(
        package_uuid=snapshot.package_uuid,
        release_version=snapshot.release_version,
        leaf_lengths={leaf.leaf_id: len(leaf.content) for leaf in snapshot.leaves},
        chunk_coverage=tuple(
            ChunkCoverage(
                chunk_id=edge.chunk_id,
                leaf_id=edge.leaf_id,
                cover_start=edge.cover_start,
                cover_end=edge.cover_end,
                role=edge.role,
                projection_id=edge.projection_id,
            )
            for edge in snapshot.projections
            if edge.chunk_id in persisted
        ),
    )


def load_bound_corpus(
    session: Session, package_uuid: str, release_version: str
) -> BoundCorpusSnapshot:
    """Resolve the snapshot from persisted 5c state."""
    refuse_quarantined(
        "bound 5c corpus load",
        package_uuid=package_uuid,
        release_version=release_version,
    )
    leaf_lengths = {
        row.leaf_id: len(row.content)
        for row in _represented_leaves(session, package_uuid)
    }

    persisted = {
        row.chunk_id
        for row in session.execute(
            select(RuleChunkORM).where(RuleChunkORM.rules_package_id == package_uuid)
        )
        .scalars()
        .all()
    }

    # Every filter is applied on the way in, so the snapshot cannot carry
    # coverage for a chunk it does not consider authoritative.
    coverage = tuple(
        ChunkCoverage(
            chunk_id=row.chunk_id,
            leaf_id=row.leaf_id,
            cover_start=row.cover_start,
            cover_end=row.cover_end,
            role=row.role,
            projection_id=row.projection_id,
        )
        for row in session.execute(
            select(CorpusProjectionORM)
            .where(CorpusProjectionORM.package_uuid == package_uuid)
            .order_by(
                CorpusProjectionORM.chunk_id,
                CorpusProjectionORM.leaf_id,
                CorpusProjectionORM.cover_start,
                CorpusProjectionORM.cover_end,
            )
        )
        .scalars()
        .all()
        if row.chunk_id in persisted
    )

    return BoundCorpusSnapshot(
        package_uuid=package_uuid,
        release_version=release_version,
        leaf_lengths=leaf_lengths,
        chunk_coverage=coverage,
    )


def published_release_binding(session: Session) -> ReleaseBinding:
    """The six coordinates of the one release *session*'s store published.

    Read back from ``rp_corpus_releases`` rather than carried in from a build,
    because what 5d binds to is what 5c persisted. Refuses a store holding no
    release or several, and a release whose corpus digest was never recorded.
    """
    row = session.execute(select(CorpusReleaseORM)).scalars().one()
    if row.persisted_corpus_digest is None:
        raise ValueError(
            f"release {row.package_uuid} / {row.release_version} records no "
            "persisted corpus digest"
        )
    return ReleaseBinding(
        package_uuid=row.package_uuid,
        release_version=row.release_version,
        authoritative_source_hash=row.authoritative_source_hash,
        transform_config_hash=row.transform_config_hash,
        bundle_root_hash=row.bundle_root_hash,
        persisted_corpus_digest=row.persisted_corpus_digest,
    )


def _represented_leaves(
    session: Session, package_uuid: str
) -> tuple[LedgerLeafORM, ...]:
    """The ``REPRESENTED`` ledger leaves of one package, in stored order.

    The one read of the accounting population, so the snapshot and
    :func:`leaves_under` cannot come to differ about what 5c represents -- a
    second copy of this predicate is exactly how a selector starts offering a
    leaf the binding seam does not admit.
    """
    return tuple(
        session.execute(
            select(LedgerLeafORM).where(
                LedgerLeafORM.package_uuid == package_uuid,
                LedgerLeafORM.disposition == Disposition.REPRESENTED.value,
            )
        )
        .scalars()
        .all()
    )


def leaves_under(
    session: Session,
    package_uuid: str,
    release_version: str,
    labels: Sequence[str],
) -> tuple[str, ...]:
    """Represented leaf ids under every container path ending in *labels*.

    Selection, not binding. A reviewer names a section the way the source
    prints it -- ``("Blinded [Condition]",)``, or with ancestors to
    disambiguate -- and this resolves that to the leaf ids the rest of 5d
    speaks in. It is deliberately *not* a field of
    :class:`BoundCorpusSnapshot`: the snapshot is a coordinate system, and
    giving it container paths would make every validator a consumer of 5c's
    heading structure rather than of its offsets.

    *labels* matches as a **suffix** of a container's own label path, so a bare
    leaf label works and an ambiguous one can be qualified by prepending its
    ancestors. Matching a suffix rather than a full path is what keeps a
    selection honest about 5c's structure instead of assuming a uniform depth:
    the source's own heading levels are preserved faithfully, irregularities
    included, and a caller that guesses the depth would silently select
    nothing.

    Returns sorted leaf ids, empty when nothing matches. Reading 5c structure
    is not authoring a rule: nothing here interprets, edits, or reconstructs
    the source, and the leaf ids it returns are only an argument to the
    proposal a human still has to review.
    """
    refuse_quarantined(
        "bound 5c section selection",
        package_uuid=package_uuid,
        release_version=release_version,
    )
    if not labels:
        raise ValueError("a section selection needs at least one container label")

    containers = (
        session.execute(
            select(LedgerContainerORM).where(
                LedgerContainerORM.package_uuid == package_uuid
            )
        )
        .scalars()
        .all()
    )
    label_of = {c.container_id: c.label for c in containers}
    parent_of = {c.container_id: c.parent_id for c in containers}

    def label_path(container_id: str) -> tuple[str, ...]:
        path: list[str] = []
        seen: set[str] = set()
        current: str | None = container_id
        # ``seen`` guards a cycle in stored parent links rather than trusting
        # the rows to be acyclic; a malformed ledger should select nothing, not
        # hang the authoring path.
        while current is not None and current in label_of and current not in seen:
            seen.add(current)
            path.append(label_of[current])
            current = parent_of.get(current)
        return tuple(reversed(path))

    wanted = tuple(labels)
    matched = frozenset(
        cid for cid in label_of if label_path(cid)[-len(wanted) :] == wanted
    )
    if not matched:
        return ()
    return tuple(
        sorted(
            row.leaf_id
            for row in _represented_leaves(session, package_uuid)
            if matched.intersection(row.container_path)
        )
    )
