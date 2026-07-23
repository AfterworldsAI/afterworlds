"""Persist a corpus release and recompute its digest from the DB — Issue 5c.

Component K step c (persist) and the tamper-detection half of Component A/I: the
persisted-corpus digest is recomputed from the actual persisted rows, so editing
any persisted leaf, disposition, exclusion reason, projection link, policy
reference, or reconciliation finding changes the recomputed digest and fails the
publication gate.

The authoritative RuleChunks persist into the existing ``rp_chunks`` table
(Issue 5a model, unextended); the ledger, policy, reconciliation, projection
linkage, and release record persist into the Issue 5c ``rp_*`` tables. Rows are
inserted in canonical order (ledger/occurrence order) so a reconstruction reads
back in the exact order the in-memory payload used.
"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from afterworlds.ingestion.corpus.bundle import (
    persisted_corpus_digest,
    persisted_corpus_payload,
)
from afterworlds.ingestion.corpus.models import (
    Container,
    ContainerType,
    CorpusBundleMembers,
    CorpusChunk,
    Disposition,
    Leaf,
    LeafDisposition,
    LeafType,
    ProjectionEdge,
    ReconciliationFindings,
    ReconciliationMember,
    ReconciliationPolicy,
    SourceLedger,
)
from afterworlds.ingestion.corpus.pipeline import ReleaseArtifacts
from afterworlds.ingestion.corpus.policy import FROZEN_POLICY, policy_payload
from afterworlds.persistence.orm.corpus import (
    CorpusProjectionORM,
    CorpusReleaseORM,
    LedgerContainerORM,
    LedgerLeafORM,
    ReconciliationORM,
    ReconciliationPolicyORM,
    SourceLedgerORM,
)
from afterworlds.persistence.orm.rules_package import (
    RuleChunkORM,
    RuleSourceORM,
    RulesPackageORM,
)


def persist_release(session: Session, artifacts: ReleaseArtifacts, *, now: str) -> None:
    """Persist the full release into SQL (Component K step c)."""
    rel = artifacts.release
    pkg = rel.package_uuid
    ledger = artifacts.ledger
    recon = artifacts.reconciliation

    # Package + source rows (host the authoritative RuleChunks).
    session.add(
        RulesPackageORM(
            rules_package_id=pkg,
            name="SRD 5.2.1 Corpus",
            system="d20",
            version=rel.release_version,
            is_enabled=True,
            publication_status="draft",
            published_at=None,
            created_at=now,
            updated_at=now,
        )
    )
    session.flush()  # package must exist before FK-referencing rows insert
    source_id = pkg  # deterministic 1:1 source for this single-source corpus
    session.add(
        RuleSourceORM(
            source_id=source_id,
            rules_package_id=pkg,
            name="SRD 5.2.1",
            category="core_rulebook",
            precedence_rank=1,
            is_enabled=True,
            created_at=now,
        )
    )
    session.flush()

    # Release record.
    ident = rel.identity
    session.add(
        CorpusReleaseORM(
            package_uuid=pkg,
            release_version=rel.release_version,
            authoritative_source_hash=ident.authoritative_source_hash,
            transform_config_hash=ident.transform_config_hash,
            bundle_root_hash=ident.bundle_root_hash,
            evidence_report_hash=ident.evidence_report_hash,
            persisted_corpus_digest=ident.persisted_corpus_digest,
            ledger_hash=rel.ledger_hash,
            policy_hash=rel.policy_hash,
            reconciliation_hash=rel.reconciliation_hash,
            corpus_report_reference=rel.corpus_report_reference,
            transform_config=rel.transform_config,
            report_payload=artifacts.report.payload,
            publication_status="draft",
            created_at=now,
        )
    )
    # The release row is the FK parent of every Issue 5c table; flush it (and the
    # source, parent of the chunks) before inserting children. No ORM
    # relationships are declared, so the unit of work cannot order these itself.
    session.flush()
    session.add(
        SourceLedgerORM(
            package_uuid=pkg,
            ledger_hash=rel.ledger_hash,
            source_document=ledger.source_document,
            source_version=ledger.source_version,
            source_sha256=ledger.source_sha256,
            extraction_config=ledger.extraction_config,
        )
    )
    session.add(
        ReconciliationPolicyORM(
            package_uuid=pkg,
            policy_version=artifacts.policy.policy_version,
            policy_hash=recon.policy_hash,
            payload=policy_payload(artifacts.policy),
        )
    )
    session.add(
        ReconciliationORM(
            package_uuid=pkg,
            policy_hash=recon.policy_hash,
            inventoried_leaves=recon.inventoried_leaves,
            represented_leaves=recon.represented_leaves,
            excluded_leaves=recon.excluded_leaves,
            unresolved_leaves=recon.unresolved_leaves,
            findings={
                "gaps": list(recon.findings.gaps),
                "overlaps": list(recon.findings.overlaps),
                "orphans": list(recon.findings.orphans),
                "duplications": list(recon.findings.duplications),
                "unresolved": list(recon.findings.unresolved),
            },
        )
    )

    # Containers (insertion order == ledger.containers order).
    session.add_all(
        LedgerContainerORM(
            package_uuid=pkg,
            container_id=c.container_id,
            container_type=c.container_type.value,
            label=c.label,
            printed_page=c.printed_page,
            parent_id=c.parent_id,
        )
        for c in ledger.containers
    )

    # Leaves + dispositions (insertion order == ledger.leaves order).
    disp_by_leaf = {d.leaf_id: d for d in recon.dispositions}
    session.add_all(
        LedgerLeafORM(
            package_uuid=pkg,
            leaf_id=leaf.leaf_id,
            printed_page=leaf.printed_page,
            page_index=leaf.page_index,
            leaf_type=leaf.leaf_type.value,
            content=leaf.content,
            char_start=leaf.char_start,
            char_end=leaf.char_end,
            occurrence_index=leaf.occurrence_index,
            container_path=list(leaf.container_path),
            disposition=disp_by_leaf[leaf.leaf_id].disposition.value,
            exclusion_reason_code=disp_by_leaf[leaf.leaf_id].exclusion_reason_code,
        )
        for leaf in ledger.leaves
    )

    # Authoritative RuleChunks into rp_chunks (unextended Issue 5a model).
    session.add_all(
        RuleChunkORM(
            chunk_id=chunk.chunk_id,
            rules_package_id=pkg,
            source_id=source_id,
            subsystem=chunk.subsystem,
            content=chunk.content,
            source_document=ledger.source_document,
            source_locator_type="page",
            source_locator_value=f"p. {chunk.printed_page}",
            source_section_label=chunk.section_label,
            is_enabled=True,
            created_at=now,
        )
        for chunk in members_chunks(artifacts)
    )

    # Declared-projection linkage (insertion order == recon.projections order).
    session.add_all(
        CorpusProjectionORM(
            package_uuid=pkg,
            projection_id=e.projection_id,
            leaf_id=e.leaf_id,
            chunk_id=e.chunk_id,
            role=e.role,
            cover_start=e.cover_start,
            cover_end=e.cover_end,
        )
        for e in recon.projections
    )
    session.flush()


def members_chunks(artifacts: ReleaseArtifacts) -> tuple[CorpusChunk, ...]:
    return artifacts.members.chunks


# ---------------------------------------------------------------------------
# Reconstruction from the DB (tamper detection)
# ---------------------------------------------------------------------------


def _load_ledger(session: Session, pkg: str) -> SourceLedger:
    meta = session.execute(
        select(SourceLedgerORM).where(SourceLedgerORM.package_uuid == pkg)
    ).scalar_one()
    containers = tuple(
        Container(
            container_id=row.container_id,
            container_type=ContainerType(row.container_type),
            label=row.label,
            printed_page=row.printed_page,
            parent_id=row.parent_id,
        )
        for row in session.execute(
            select(LedgerContainerORM)
            .where(LedgerContainerORM.package_uuid == pkg)
            .order_by(LedgerContainerORM.row_id)
        ).scalars()
    )
    leaf_rows = list(
        session.execute(
            select(LedgerLeafORM)
            .where(LedgerLeafORM.package_uuid == pkg)
            .order_by(LedgerLeafORM.row_id)
        ).scalars()
    )
    leaves = tuple(
        Leaf(
            leaf_id=row.leaf_id,
            printed_page=row.printed_page,
            page_index=row.page_index,
            leaf_type=LeafType(row.leaf_type),
            content=row.content,
            char_start=row.char_start,
            char_end=row.char_end,
            occurrence_index=row.occurrence_index,
            container_path=tuple(row.container_path),
        )
        for row in leaf_rows
    )
    return SourceLedger(
        source_document=meta.source_document,
        source_version=meta.source_version,
        source_sha256=meta.source_sha256,
        extraction_config=meta.extraction_config,
        containers=containers,
        leaves=leaves,
    )


def _load_reconciliation(
    session: Session, pkg: str, policy: ReconciliationPolicy
) -> ReconciliationMember:
    recon_row = session.execute(
        select(ReconciliationORM).where(ReconciliationORM.package_uuid == pkg)
    ).scalar_one()
    leaf_rows = list(
        session.execute(
            select(LedgerLeafORM)
            .where(LedgerLeafORM.package_uuid == pkg)
            .order_by(LedgerLeafORM.row_id)
        ).scalars()
    )
    dispositions = tuple(
        LeafDisposition(
            leaf_id=row.leaf_id,
            disposition=Disposition(row.disposition),
            exclusion_reason_code=row.exclusion_reason_code,
        )
        for row in leaf_rows
    )
    projections = tuple(
        ProjectionEdge(
            projection_id=row.projection_id,
            leaf_id=row.leaf_id,
            chunk_id=row.chunk_id,
            role=row.role,
            cover_start=row.cover_start,
            cover_end=row.cover_end,
        )
        for row in session.execute(
            select(CorpusProjectionORM)
            .where(CorpusProjectionORM.package_uuid == pkg)
            .order_by(CorpusProjectionORM.row_id)
        ).scalars()
    )
    findings = ReconciliationFindings(
        gaps=tuple(recon_row.findings["gaps"]),
        overlaps=tuple(recon_row.findings["overlaps"]),
        orphans=tuple(recon_row.findings["orphans"]),
        duplications=tuple(recon_row.findings["duplications"]),
        unresolved=tuple(recon_row.findings["unresolved"]),
    )
    return ReconciliationMember(
        policy_version=policy.policy_version,
        policy_hash=recon_row.policy_hash,
        dispositions=dispositions,
        projections=projections,
        findings=findings,
        inventoried_leaves=recon_row.inventoried_leaves,
        represented_leaves=recon_row.represented_leaves,
        excluded_leaves=recon_row.excluded_leaves,
        unresolved_leaves=recon_row.unresolved_leaves,
    )


def _load_members(
    session: Session, pkg: str, ledger: SourceLedger
) -> CorpusBundleMembers:
    leaves_by_id = {leaf.leaf_id: leaf for leaf in ledger.leaves}
    occ = {leaf.leaf_id: leaf.occurrence_index for leaf in ledger.leaves}
    # chunk_id -> ordered leaf ids (projection insertion order)
    chunk_leaves: dict[str, list[str]] = {}
    for row in session.execute(
        select(CorpusProjectionORM)
        .where(CorpusProjectionORM.package_uuid == pkg)
        .order_by(CorpusProjectionORM.row_id)
    ).scalars():
        chunk_leaves.setdefault(row.chunk_id, []).append(row.leaf_id)
    chunk_rows = {
        chunk_row.chunk_id: chunk_row
        for chunk_row in session.execute(
            select(RuleChunkORM).where(RuleChunkORM.rules_package_id == pkg)
        ).scalars()
    }
    chunks: list[CorpusChunk] = []
    for chunk_id, leaf_ids in chunk_leaves.items():
        chunk_row = chunk_rows[chunk_id]
        primary = leaves_by_id[leaf_ids[0]]
        chunks.append(
            CorpusChunk(
                chunk_id=chunk_id,
                subsystem=chunk_row.subsystem,
                content=chunk_row.content,
                printed_page=primary.printed_page,
                section_label=chunk_row.source_section_label,
                container_path=primary.container_path,
                source_leaf_ids=tuple(leaf_ids),
            )
        )
    # Restore canonical (build_corpus) order: by primary leaf occurrence index.
    chunks.sort(key=lambda c: occ[c.source_leaf_ids[0]])
    return CorpusBundleMembers(chunks=tuple(chunks), derivative_notes=())


def recompute_persisted_digest(
    session: Session, pkg: str, *, policy: ReconciliationPolicy = FROZEN_POLICY
) -> str:
    """Recompute the persisted-corpus digest from the actual DB rows."""
    release = session.execute(
        select(CorpusReleaseORM).where(CorpusReleaseORM.package_uuid == pkg)
    ).scalar_one()
    ledger = _load_ledger(session, pkg)
    recon = _load_reconciliation(session, pkg, policy)
    members = _load_members(session, pkg, ledger)
    return persisted_corpus_digest(
        release.package_uuid, release.release_version, ledger, members, recon, policy
    )


def verify_persisted_digest(
    session: Session, pkg: str, *, policy: ReconciliationPolicy = FROZEN_POLICY
) -> bool:
    """True iff the recomputed digest matches the stored release digest."""
    release = session.execute(
        select(CorpusReleaseORM).where(CorpusReleaseORM.package_uuid == pkg)
    ).scalar_one()
    return recompute_persisted_digest(session, pkg, policy=policy) == (
        release.persisted_corpus_digest
    )


def reconstruct_payload(
    session: Session, pkg: str, *, policy: ReconciliationPolicy = FROZEN_POLICY
) -> dict[str, object]:
    """Reconstruct the canonical persisted-corpus payload from the DB (debug)."""
    release = session.execute(
        select(CorpusReleaseORM).where(CorpusReleaseORM.package_uuid == pkg)
    ).scalar_one()
    ledger = _load_ledger(session, pkg)
    recon = _load_reconciliation(session, pkg, policy)
    members = _load_members(session, pkg, ledger)
    return persisted_corpus_payload(
        release.package_uuid, release.release_version, ledger, members, recon, policy
    )


def delete_release(session: Session, pkg: str) -> None:
    """Remove a release and all its rows (cascade via FK + explicit chunks)."""
    session.execute(delete(RuleChunkORM).where(RuleChunkORM.rules_package_id == pkg))
    session.execute(
        delete(RulesPackageORM).where(RulesPackageORM.rules_package_id == pkg)
    )
    session.flush()
