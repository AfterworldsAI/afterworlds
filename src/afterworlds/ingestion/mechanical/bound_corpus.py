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

from collections.abc import Mapping
from dataclasses import dataclass
from functools import cached_property

from sqlalchemy import select
from sqlalchemy.orm import Session

from afterworlds.ingestion.corpus.models import Disposition
from afterworlds.persistence.orm.corpus import CorpusProjectionORM, LedgerLeafORM
from afterworlds.persistence.orm.rules_package import RuleChunkORM

__all__ = ["BoundCorpusSnapshot", "ChunkCoverage", "load_bound_corpus"]


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


def load_bound_corpus(
    session: Session, package_uuid: str, release_version: str
) -> BoundCorpusSnapshot:
    """Resolve the snapshot from persisted 5c state."""
    leaf_lengths = {
        row.leaf_id: len(row.content)
        for row in session.execute(
            select(LedgerLeafORM).where(
                LedgerLeafORM.package_uuid == package_uuid,
                LedgerLeafORM.disposition == Disposition.REPRESENTED.value,
            )
        )
        .scalars()
        .all()
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
