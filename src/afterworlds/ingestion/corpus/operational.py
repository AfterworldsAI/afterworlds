"""Narrow operational corpus contract consumed by CRD Issue 5d.

This module is the downstream trust seam established by CRD Issue 5c's
2026-08-03 operational-reliability amendment.  It verifies the exact SQLite
state that 5d consumes without replaying 5c's publication history and without
opening ChromaDB.

The operational digest covers represented source leaves, authoritative chunks,
their source membership, and the projection edges connecting them.  Ledgers,
reconciliation policy, bundle genealogy, and the diagnostic evidence report
remain 5c-internal publication machinery and are deliberately outside this
downstream contract.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from afterworlds.ingestion.corpus.hashing import hash_obj
from afterworlds.persistence.orm.corpus import (
    CorpusProjectionORM,
    CorpusReleaseORM,
    LedgerLeafORM,
    SourceLedgerORM,
)
from afterworlds.persistence.orm.rules_package import (
    RuleChunkORM,
    RuleSourceORM,
    RulesPackageORM,
)

CORPUS_CONTRACT_VERSION = "5c-operational-1"


class OperationalCorpusVerificationError(RuntimeError):
    """Raised when a release cannot be trusted through the operational seam."""

    def __init__(self, violations: tuple[str, ...]) -> None:
        super().__init__("; ".join(violations))
        self.violations = violations


@dataclass(frozen=True)
class OperationalSource:
    source_id: str
    rules_package_id: str
    name: str
    category: str
    precedence_rank: int
    is_enabled: bool


@dataclass(frozen=True)
class OperationalLeaf:
    leaf_id: str
    printed_page: int
    page_index: int
    leaf_type: str
    content: str
    char_start: int
    char_end: int
    occurrence_index: int
    container_path: tuple[str, ...]
    table_id: str | None
    table_row: int | None
    table_col: int | None
    table_segment: int | None


@dataclass(frozen=True)
class OperationalChunk:
    chunk_id: str
    source_id: str
    subsystem: str
    content: str
    source_document: str
    source_locator_type: str
    source_locator_value: str
    source_section_label: str | None
    is_enabled: bool


@dataclass(frozen=True)
class OperationalProjection:
    projection_id: str
    leaf_id: str
    chunk_id: str
    role: str
    cover_start: int
    cover_end: int


@dataclass(frozen=True)
class OperationalCorpusSnapshot:
    """The complete versioned SQLite corpus surface approved for 5d."""

    package_uuid: str
    release_version: str
    authoritative_source_hash: str
    corpus_contract_version: str
    persisted_corpus_digest: str
    source_document: str
    source_version: str
    sources: tuple[OperationalSource, ...]
    leaves: tuple[OperationalLeaf, ...]
    chunks: tuple[OperationalChunk, ...]
    projections: tuple[OperationalProjection, ...]


def operational_corpus_payload(
    snapshot: OperationalCorpusSnapshot,
) -> dict[str, object]:
    """Canonical payload of only the authoritative state 5d consumes."""
    return {
        "package_uuid": snapshot.package_uuid,
        "release_version": snapshot.release_version,
        "authoritative_source_hash": snapshot.authoritative_source_hash,
        "corpus_contract_version": snapshot.corpus_contract_version,
        "persisted_corpus_digest": snapshot.persisted_corpus_digest,
        "source_document": snapshot.source_document,
        "source_version": snapshot.source_version,
        "sources": [
            {
                "source_id": source.source_id,
                "rules_package_id": source.rules_package_id,
                "name": source.name,
                "category": source.category,
                "precedence_rank": source.precedence_rank,
                "is_enabled": source.is_enabled,
            }
            for source in snapshot.sources
        ],
        "represented_leaves": [
            {
                "leaf_id": leaf.leaf_id,
                "printed_page": leaf.printed_page,
                "page_index": leaf.page_index,
                "leaf_type": leaf.leaf_type,
                "content": leaf.content,
                "char_start": leaf.char_start,
                "char_end": leaf.char_end,
                "occurrence_index": leaf.occurrence_index,
                "container_path": list(leaf.container_path),
                "table_id": leaf.table_id,
                "table_row": leaf.table_row,
                "table_col": leaf.table_col,
                "table_segment": leaf.table_segment,
            }
            for leaf in snapshot.leaves
        ],
        "chunks": [
            {
                "chunk_id": chunk.chunk_id,
                "source_id": chunk.source_id,
                "subsystem": chunk.subsystem,
                "content": chunk.content,
                "source_document": chunk.source_document,
                "source_locator_type": chunk.source_locator_type,
                "source_locator_value": chunk.source_locator_value,
                "source_section_label": chunk.source_section_label,
                "is_enabled": chunk.is_enabled,
            }
            for chunk in snapshot.chunks
        ],
        "projections": [
            {
                "projection_id": edge.projection_id,
                "leaf_id": edge.leaf_id,
                "chunk_id": edge.chunk_id,
                "role": edge.role,
                "cover_start": edge.cover_start,
                "cover_end": edge.cover_end,
            }
            for edge in snapshot.projections
        ],
    }


def operational_corpus_digest(snapshot: OperationalCorpusSnapshot) -> str:
    return hash_obj(operational_corpus_payload(snapshot))


def build_operational_corpus_snapshot(
    session: Session,
    package_uuid: str,
    *,
    corpus_contract_version: str,
    persisted_corpus_digest: str,
) -> OperationalCorpusSnapshot:
    """Read the downstream corpus surface directly from SQLite."""
    release = session.get(CorpusReleaseORM, package_uuid)
    ledger = session.get(SourceLedgerORM, package_uuid)
    if release is None or ledger is None:
        missing = "release" if release is None else "source ledger"
        raise OperationalCorpusVerificationError(
            (f"package {package_uuid} has no {missing} row",)
        )

    sources = tuple(
        OperationalSource(
            source_id=row.source_id,
            rules_package_id=row.rules_package_id,
            name=row.name,
            category=row.category,
            precedence_rank=row.precedence_rank,
            is_enabled=row.is_enabled,
        )
        for row in session.execute(
            select(RuleSourceORM)
            .where(RuleSourceORM.rules_package_id == package_uuid)
            .order_by(RuleSourceORM.precedence_rank, RuleSourceORM.source_id)
        ).scalars()
    )
    leaves = tuple(
        OperationalLeaf(
            leaf_id=row.leaf_id,
            printed_page=row.printed_page,
            page_index=row.page_index,
            leaf_type=row.leaf_type,
            content=row.content,
            char_start=row.char_start,
            char_end=row.char_end,
            occurrence_index=row.occurrence_index,
            container_path=tuple(row.container_path),
            table_id=row.table_id,
            table_row=row.table_row,
            table_col=row.table_col,
            table_segment=row.table_segment,
        )
        for row in session.execute(
            select(LedgerLeafORM)
            .where(
                LedgerLeafORM.package_uuid == package_uuid,
                LedgerLeafORM.disposition == "represented",
            )
            .order_by(LedgerLeafORM.leaf_id)
        ).scalars()
    )
    chunks = tuple(
        OperationalChunk(
            chunk_id=row.chunk_id,
            source_id=row.source_id,
            subsystem=row.subsystem,
            content=row.content,
            source_document=row.source_document,
            source_locator_type=row.source_locator_type,
            source_locator_value=row.source_locator_value,
            source_section_label=row.source_section_label,
            is_enabled=row.is_enabled,
        )
        for row in session.execute(
            select(RuleChunkORM)
            .where(RuleChunkORM.rules_package_id == package_uuid)
            .order_by(RuleChunkORM.chunk_id)
        ).scalars()
    )
    projections = tuple(
        OperationalProjection(
            projection_id=row.projection_id,
            leaf_id=row.leaf_id,
            chunk_id=row.chunk_id,
            role=row.role,
            cover_start=row.cover_start,
            cover_end=row.cover_end,
        )
        for row in session.execute(
            select(CorpusProjectionORM)
            .where(CorpusProjectionORM.package_uuid == package_uuid)
            .order_by(
                CorpusProjectionORM.chunk_id,
                CorpusProjectionORM.leaf_id,
                CorpusProjectionORM.cover_start,
                CorpusProjectionORM.cover_end,
                CorpusProjectionORM.projection_id,
            )
        ).scalars()
    )
    return OperationalCorpusSnapshot(
        package_uuid=package_uuid,
        release_version=release.release_version,
        authoritative_source_hash=release.authoritative_source_hash,
        corpus_contract_version=corpus_contract_version,
        persisted_corpus_digest=persisted_corpus_digest,
        source_document=ledger.source_document,
        source_version=ledger.source_version,
        sources=sources,
        leaves=leaves,
        chunks=chunks,
        projections=projections,
    )


def operational_structure_violations(
    snapshot: OperationalCorpusSnapshot,
) -> tuple[str, ...]:
    """Validate reachability and closure of the narrow downstream surface."""
    violations: list[str] = []
    pkg = snapshot.package_uuid
    sources = {source.source_id: source for source in snapshot.sources}
    if set(sources) != {pkg}:
        violations.append(
            f"expected exactly one authoritative source {pkg}, found {sorted(sources)}"
        )
    authoritative = sources.get(pkg)
    if authoritative is not None:
        if authoritative.rules_package_id != pkg:
            violations.append("authoritative source belongs to another package")
        if not authoritative.is_enabled:
            violations.append("authoritative source is disabled")

    leaf_by_id = {leaf.leaf_id: leaf for leaf in snapshot.leaves}
    chunk_by_id = {chunk.chunk_id: chunk for chunk in snapshot.chunks}
    projected_leaves: set[str] = set()
    projected_chunks: set[str] = set()
    projection_ids: set[str] = set()
    for edge in snapshot.projections:
        if edge.projection_id in projection_ids:
            violations.append(f"duplicate projection id {edge.projection_id}")
        projection_ids.add(edge.projection_id)
        leaf = leaf_by_id.get(edge.leaf_id)
        chunk = chunk_by_id.get(edge.chunk_id)
        if leaf is None:
            violations.append(
                f"projection {edge.projection_id} references absent represented leaf "
                f"{edge.leaf_id}"
            )
        else:
            projected_leaves.add(edge.leaf_id)
            if not (0 <= edge.cover_start < edge.cover_end <= len(leaf.content)):
                violations.append(
                    f"projection {edge.projection_id} has invalid leaf coverage"
                )
        if chunk is None:
            violations.append(
                "projection "
                f"{edge.projection_id} references absent chunk {edge.chunk_id}"
            )
        else:
            projected_chunks.add(edge.chunk_id)

    for leaf_id in sorted(set(leaf_by_id) - projected_leaves):
        violations.append(f"represented leaf {leaf_id} has no authoritative projection")
    for chunk_id in sorted(set(chunk_by_id) - projected_chunks):
        violations.append(f"chunk {chunk_id} has no authoritative projection")
    for chunk in snapshot.chunks:
        if chunk.source_id != pkg:
            violations.append(
                f"chunk {chunk.chunk_id} belongs to source {chunk.source_id}, not {pkg}"
            )
        if not chunk.is_enabled:
            violations.append(f"authoritative chunk {chunk.chunk_id} is disabled")
    if not snapshot.leaves:
        violations.append("operational corpus contains no represented leaves")
    if not snapshot.chunks:
        violations.append("operational corpus contains no authoritative chunks")
    return tuple(violations)


def load_verified_operational_corpus(
    session: Session,
    package_uuid: str,
    *,
    release_version: str,
    authoritative_source_hash: str,
    transform_config_hash: str,
    bundle_root_hash: str,
    persisted_corpus_digest: str,
    supported_contract_versions: frozenset[str],
) -> OperationalCorpusSnapshot:
    """Verify and return one approved release without historical re-proof."""
    violations: list[str] = []
    release = session.get(CorpusReleaseORM, package_uuid)
    package = session.get(RulesPackageORM, package_uuid)
    ledger = session.get(SourceLedgerORM, package_uuid)
    if release is None:
        raise OperationalCorpusVerificationError(
            (f"no published corpus release for package {package_uuid}",)
        )
    if package is None:
        violations.append(f"no Rules Package row for {package_uuid}")
    else:
        if package.version != release.release_version:
            violations.append("package version and corpus release version disagree")
        if package.publication_status != "published" or not package.is_enabled:
            violations.append("Rules Package is not published and enabled")
    if release.publication_status != "published":
        violations.append("corpus release is not published")

    for name, expected in (
        ("release_version", release_version),
        ("authoritative_source_hash", authoritative_source_hash),
        ("transform_config_hash", transform_config_hash),
        ("bundle_root_hash", bundle_root_hash),
        ("persisted_corpus_digest", persisted_corpus_digest),
    ):
        if getattr(release, name) != expected:
            violations.append(f"declared {name} does not match the published release")

    if ledger is None:
        violations.append("published release has no authoritative source ledger")
    elif ledger.source_sha256 != release.authoritative_source_hash:
        violations.append("source ledger hash disagrees with the published source")

    contract_version = release.corpus_contract_version
    recorded_digest = release.operational_corpus_digest
    if contract_version not in supported_contract_versions:
        violations.append(f"unsupported corpus contract version {contract_version!r}")
    if not recorded_digest:
        violations.append("published release has no operational corpus digest")
    if violations:
        raise OperationalCorpusVerificationError(tuple(violations))

    assert contract_version is not None
    assert release.persisted_corpus_digest is not None
    snapshot = build_operational_corpus_snapshot(
        session,
        package_uuid,
        corpus_contract_version=contract_version,
        persisted_corpus_digest=release.persisted_corpus_digest,
    )
    violations.extend(operational_structure_violations(snapshot))
    if operational_corpus_digest(snapshot) != recorded_digest:
        violations.append(
            "authoritative SQLite corpus does not match its operational digest"
        )
    if violations:
        raise OperationalCorpusVerificationError(tuple(violations))
    return snapshot
