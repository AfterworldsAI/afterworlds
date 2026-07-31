"""The bound 5c corpus a candidate is validated against — CRD Issue 5d.

Validation needs two things from the exact published CRD Issue 5c release: how
long each represented leaf's canonical text is (so a span partition can be
checked), and which chunks are authoritative governing prose for that release
(so a prose binding resolves to real authority rather than to any non-empty
string).

Both are resolved here, once, into a frozen snapshot. The validators stay pure
functions over that snapshot instead of each growing a private query, so there
is one source-resolution path and a validator cannot accidentally read a
different release than the one the candidate claims.

A chunk counts as authoritative only when it satisfies *both* halves of the 5c
contract: it exists in ``rp_chunks`` under the bound package, and it is in that
release's declared ``rp_corpus_projections`` population. A chunk that exists but
was never projected is not governing authority for this release, and neither is
one belonging to some other package.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from afterworlds.ingestion.corpus.models import Disposition
from afterworlds.persistence.orm.corpus import CorpusProjectionORM, LedgerLeafORM
from afterworlds.persistence.orm.rules_package import RuleChunkORM

__all__ = ["BoundCorpusSnapshot", "load_bound_corpus"]


@dataclass(frozen=True)
class BoundCorpusSnapshot:
    """Authoritative facts about one published 5c release, resolved once.

    ``leaf_lengths`` covers exactly the ``REPRESENTED`` population — the
    accounting population #137 contract 1 defines — so a leaf 5c excluded is
    neither required to be classified nor allowed to be.
    """

    package_uuid: str
    release_version: str
    leaf_lengths: dict[str, int]
    authoritative_chunk_ids: frozenset[str]


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

    projected = {
        row.chunk_id
        for row in session.execute(
            select(CorpusProjectionORM).where(
                CorpusProjectionORM.package_uuid == package_uuid
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

    return BoundCorpusSnapshot(
        package_uuid=package_uuid,
        release_version=release_version,
        leaf_lengths=leaf_lengths,
        authoritative_chunk_ids=frozenset(projected & persisted),
    )
