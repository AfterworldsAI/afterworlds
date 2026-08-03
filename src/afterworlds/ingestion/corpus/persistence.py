"""Persist a corpus release and finalize it from actual DB state — Issue 5c.

Component K steps c–g. The root defect this module fixes (PR #134 remediation):
a release's proof identities must be produced *from the database*, in the
acyclic order Component K mandates, not claimed in memory before persistence
occurs:

    c  persist the candidate as a non-runtime-visible draft
    d  reconstruct the authoritative logical state from the actual persisted
       rows and compute the persisted-corpus digest from that reconstruction
    e  generate the evidence report from the reconstructed state (+ a live
       legacy zero-reachability check against the same session)
    f  hash the completed evidence report
    g  record the five top-level hashes and run the final publication gate
       against the DB-grounded artifacts; publish only if it passes

:func:`finalize_release` is the sole entry point that performs c–g and
transitions a release to ``published``. :func:`persist_release` is the lower
-level step-c-only primitive (used by ``finalize_release`` internally, and
directly by tests that already hold a fully-identified ``ReleaseArtifacts`` and
want to exercise persistence/reconstruction/tamper-detection in isolation).

The authoritative RuleChunks persist into the existing ``rp_chunks`` table
(Issue 5a model, unextended); the ledger, policy, reconciliation, projection
linkage, and release record persist into the Issue 5c ``rp_*`` tables. Rows are
inserted in canonical order (ledger/occurrence order) so a reconstruction reads
back in the exact order the in-memory payload used.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from sqlalchemy import delete, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from afterworlds.ingestion.corpus.bundle import (
    build_bundle,
    persisted_corpus_digest,
    persisted_corpus_payload,
    reconciliation_hash,
)
from afterworlds.ingestion.corpus.concordance import check_canaries, check_concordance
from afterworlds.ingestion.corpus.gate import PublicationEvidence, run_gate
from afterworlds.ingestion.corpus.hashing import hash_obj
from afterworlds.ingestion.corpus.ledger import ledger_hash
from afterworlds.ingestion.corpus.models import (
    CanonicalBundle,
    Container,
    ContainerType,
    CorpusBundleMembers,
    CorpusChunk,
    Disposition,
    GateResult,
    Leaf,
    LeafDisposition,
    LeafType,
    PersistedSource,
    ProjectionEdge,
    ReconciliationFindings,
    ReconciliationMember,
    ReconciliationPolicy,
    ReleaseIdentity,
    ReleaseRecord,
    SourceLedger,
)
from afterworlds.ingestion.corpus.pdf_source import ExtractedPage
from afterworlds.ingestion.corpus.pipeline import CandidateRelease, ReleaseArtifacts
from afterworlds.ingestion.corpus.policy import (
    PolicyReconstructionError,
    policy_from_payload,
    policy_hash,
    policy_payload,
)
from afterworlds.ingestion.corpus.report import (
    EVIDENCE_REPORT_SCHEMA_VERSION,
    EvidenceReport,
    build_report,
    parse_recorded_report,
    report_hash,
)
from afterworlds.ingestion.corpus.report_schema import CorpusEvidenceReport
from afterworlds.ingestion.corpus.source_completeness import (
    EXPECTED_PAGE_COUNT,
    verify_source_completeness,
)
from afterworlds.ingestion.corpus.table_inventory import (
    check_against_committed_inventory,
)
from afterworlds.ingestion.corpus.vector_publication import (
    cleanup_vector_collection,
    reindex_and_verify,
    verify_only,
)
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
from afterworlds.pipeline.retrieval.config import RetrievalMemoryConfig
from afterworlds.pipeline.retrieval.embedding import RetrievalEmbeddingFunction

if TYPE_CHECKING:
    from chromadb.api import ClientAPI


class PersistedReportError(ValueError):
    """A stored evidence report that is not the canonical schema.

    Raised rather than reported during reconstruction: a payload that will not
    parse is not a weaker report, it is not this document, and continuing would
    build artifacts around a shape nobody published.
    """


# ---------------------------------------------------------------------------
# Shared row-building primitives
# ---------------------------------------------------------------------------


def _persist_package_and_source(
    session: Session, pkg: str, release_version: str, *, now: str
) -> str:
    """Insert the package + its single source row; returns the source id."""
    session.add(
        RulesPackageORM(
            rules_package_id=pkg,
            name="SRD 5.2.1 Corpus",
            system="d20",
            version=release_version,
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
    return source_id


def _persist_release_record(
    session: Session,
    pkg: str,
    *,
    release_version: str,
    authoritative_source_hash: str,
    transform_config_hash: str,
    bundle_root_hash: str,
    evidence_report_hash: str | None,
    persisted_corpus_digest: str | None,
    ledger_hash: str,
    policy_hash: str,
    reconciliation_hash: str,
    corpus_report_reference: str | None,
    transform_config: dict[str, Any],
    report_payload: dict[str, Any] | None,
    now: str,
) -> None:
    """Insert the external release/publication record (draft).

    ``evidence_report_hash``/``persisted_corpus_digest``/``corpus_report_reference``/
    ``report_payload`` are ``None`` when this is the pre-finalize draft insert
    (Component K step c) — those are post-persistence proof identities (steps
    d/e/f) that ``finalize_release`` fills in afterward via
    :func:`_set_post_persistence_identity`, once they exist to compute.
    """
    session.add(
        CorpusReleaseORM(
            package_uuid=pkg,
            release_version=release_version,
            authoritative_source_hash=authoritative_source_hash,
            transform_config_hash=transform_config_hash,
            bundle_root_hash=bundle_root_hash,
            evidence_report_hash=evidence_report_hash,
            persisted_corpus_digest=persisted_corpus_digest,
            ledger_hash=ledger_hash,
            policy_hash=policy_hash,
            reconciliation_hash=reconciliation_hash,
            corpus_report_reference=corpus_report_reference,
            transform_config=transform_config,
            report_payload=report_payload,
            publication_status="draft",
            created_at=now,
        )
    )
    # The release row is the FK parent of every Issue 5c table; flush it before
    # inserting children. No ORM relationships are declared, so the unit of
    # work cannot order these itself.
    session.flush()


def _persist_bundle_rows(
    session: Session,
    pkg: str,
    source_id: str,
    *,
    ledger: SourceLedger,
    recon: ReconciliationMember,
    policy: ReconciliationPolicy,
    members: CorpusBundleMembers,
    now: str,
) -> None:
    """Insert the ledger/policy/reconciliation/leaves/chunks/projections rows."""
    session.add(
        SourceLedgerORM(
            package_uuid=pkg,
            ledger_hash=ledger_hash(ledger),
            source_document=ledger.source_document,
            source_version=ledger.source_version,
            source_sha256=ledger.source_sha256,
            extraction_config=ledger.extraction_config,
        )
    )
    session.add(
        ReconciliationPolicyORM(
            package_uuid=pkg,
            policy_version=policy.policy_version,
            policy_hash=recon.policy_hash,
            payload=policy_payload(policy),
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
            table_id=leaf.table_id,
            table_row=leaf.table_row,
            table_col=leaf.table_col,
            table_segment=leaf.table_segment,
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
        for chunk in members.chunks
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


def persist_release(session: Session, artifacts: ReleaseArtifacts, *, now: str) -> None:
    """Persist an already-finalized release's full state (Component K step c).

    Used when the release's identity — including the post-persistence proof
    hashes — is already known, e.g. re-persisting a previously finalized
    ``ReleaseArtifacts`` into a different store to exercise persistence,
    reconstruction, and tamper detection in isolation. Production publication
    goes through :func:`finalize_release` instead, which computes those hashes
    from the actual persisted state rather than trusting them from the caller.
    """
    rel = artifacts.release
    pkg = rel.package_uuid
    ident = rel.identity
    source_id = _persist_package_and_source(session, pkg, rel.release_version, now=now)
    _persist_release_record(
        session,
        pkg,
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
        report_payload=artifacts.report.dump(),
        now=now,
    )
    _persist_bundle_rows(
        session,
        pkg,
        source_id,
        ledger=artifacts.ledger,
        recon=artifacts.reconciliation,
        policy=artifacts.policy,
        members=artifacts.members,
        now=now,
    )


# ---------------------------------------------------------------------------
# Reconstruction from the DB (tamper detection + post-persistence proof)
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
            table_id=row.table_id,
            table_row=row.table_row,
            table_col=row.table_col,
            table_segment=row.table_segment,
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


def _load_policy(session: Session, pkg: str) -> ReconciliationPolicy:
    """Reconstruct the applied reconciliation policy from the persisted rows.

    The DB-grounded policy every reconstruction/digest/report/reuse path must
    use — never ``FROZEN_POLICY`` or a caller policy (PR #134 P1). Reads the
    ``rp_reconciliation_policies`` row, reconstructs the policy from its payload,
    and validates a closed chain of cross-references so that a missing, malformed,
    deleted, or inconsistent persisted policy fails closed:

    * the policy row exists and its payload is a well-formed policy;
    * the payload-derived version/hash match the row's recorded version/hash;
    * the row's ``policy_hash`` matches ``rp_reconciliations.policy_hash``;
    * the row's ``policy_hash`` matches ``rp_corpus_releases.policy_hash``;
    * the reconstructed policy payload matches the policy embedded in the stored
      transform configuration.

    Raises:
        PolicyReconstructionError: on any missing/malformed/inconsistent state.
    """
    release = session.execute(
        select(CorpusReleaseORM).where(CorpusReleaseORM.package_uuid == pkg)
    ).scalar_one_or_none()
    if release is None:
        raise PolicyReconstructionError(f"no corpus release row for {pkg}")
    policy_row = session.execute(
        select(ReconciliationPolicyORM).where(
            ReconciliationPolicyORM.package_uuid == pkg
        )
    ).scalar_one_or_none()
    if policy_row is None:
        raise PolicyReconstructionError(
            f"missing rp_reconciliation_policies row for {pkg}"
        )

    policy = policy_from_payload(policy_row.payload)  # fails closed if malformed
    recomputed_hash = policy_hash(policy)

    if policy.policy_version != policy_row.policy_version:
        raise PolicyReconstructionError(
            "policy_version mismatch (payload vs rp_reconciliation_policies row)"
        )
    if recomputed_hash != policy_row.policy_hash:
        raise PolicyReconstructionError(
            "policy_hash mismatch (payload vs rp_reconciliation_policies row)"
        )

    recon_row = session.execute(
        select(ReconciliationORM).where(ReconciliationORM.package_uuid == pkg)
    ).scalar_one_or_none()
    if recon_row is None or recon_row.policy_hash != policy_row.policy_hash:
        raise PolicyReconstructionError(
            "policy_hash mismatch (policy row vs rp_reconciliations)"
        )
    if release.policy_hash != policy_row.policy_hash:
        raise PolicyReconstructionError(
            "policy_hash mismatch (policy row vs rp_corpus_releases)"
        )

    tconfig = release.transform_config
    if not isinstance(tconfig, dict) or tconfig.get(
        "reconciliation_policy"
    ) != policy_payload(policy):
        raise PolicyReconstructionError(
            "reconstructed policy != policy embedded in stored transform config"
        )
    return policy


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
    """Reconstruct the authoritative corpus members from persisted rows.

    Scoped strictly to the declared-projection set: a chunk with no declared
    projection is not authoritative corpus content (it is an orphan — a
    provenance failure, Component I) and does not enter this reconstruction or
    the persisted-corpus digest. Whether the DB *also* holds such an orphan row
    (or a disabled projected chunk/source) is a separate runtime-visibility
    question that this function does not answer — see
    :func:`verify_chunk_runtime_membership`, whose violations must independently
    gate publication.
    """
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
        chunk_row = chunk_rows.get(chunk_id)
        if chunk_row is None:
            continue  # a declared projection with no backing row: an I-level
            # failure surfaced by verify_chunk_runtime_membership, not silently
            # synthesized here.
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
                # Runtime-visible provenance read back from the actual persisted
                # rp_chunks row (Component G, PR #134 defect family 2). Bound
                # into the persisted-corpus digest so tampering any cited
                # locator field breaks verify_persisted_digest and the gate,
                # rather than being silently synthesized from the ledger.
                source_document=chunk_row.source_document,
                source_locator_type=chunk_row.source_locator_type,
                source_locator_value=chunk_row.source_locator_value,
                # Persisted source membership read back from the actual rp_chunks
                # row (Component G, PR #134 defect family 3). Bound into the
                # digest so reassigning a chunk to a different source_id after
                # persistence breaks verify_persisted_digest and the gate.
                source_id=chunk_row.source_id,
            )
        )
    # Restore canonical (build_corpus) order: by primary leaf occurrence index.
    chunks.sort(key=lambda c: occ[c.source_leaf_ids[0]])
    return CorpusBundleMembers(chunks=tuple(chunks), derivative_notes=())


def _load_sources(session: Session, pkg: str) -> tuple[PersistedSource, ...]:
    """Reconstruct the complete logical RuleSource set from persisted rows.

    Canonically ordered by ``(precedence_rank, source_id)`` so the bound set is
    deterministic. Excludes ``created_at`` (operational, not part of the logical
    source identity/authority the proof binds — PR #134 defect family 3).
    """
    rows = session.execute(
        select(RuleSourceORM).where(RuleSourceORM.rules_package_id == pkg)
    ).scalars()
    sources = [
        PersistedSource(
            source_id=row.source_id,
            rules_package_id=row.rules_package_id,
            name=row.name,
            category=row.category,
            precedence_rank=row.precedence_rank,
            is_enabled=row.is_enabled,
        )
        for row in rows
    ]
    sources.sort(key=lambda s: (s.precedence_rank, s.source_id))
    return tuple(sources)


# Expected single-source metadata for the SRD corpus, mirroring the values
# _persist_package_and_source writes. The Issue-5c invariant is that the release
# has exactly this one authoritative source and every chunk is assigned to it.
_SOURCE_NAME = "SRD 5.2.1"
_SOURCE_CATEGORY = "core_rulebook"
_SOURCE_PRECEDENCE = 1


def verify_persisted_page_coverage(session: Session, pkg: str) -> tuple[str, ...]:
    """Cheap DB-grounded completeness check on the reuse path.

    ``finalize_release`` guards fresh publication on ``candidate.pages``, but the
    reuse path reconstructs an *already-persisted* release; a release persisted
    incompletely (not through a full candidate) would otherwise pass reuse on a
    full candidate. This asserts the persisted ledger leaves cover every printed
    page ``1..EXPECTED_PAGE_COUNT`` — an omitted authoritative page fails reuse
    closed. Returns the list of violations (empty iff fully covered).
    """
    persisted_pages = set(
        session.execute(
            select(LedgerLeafORM.printed_page).where(LedgerLeafORM.package_uuid == pkg)
        ).scalars()
    )
    missing = sorted(set(range(1, EXPECTED_PAGE_COUNT + 1)) - persisted_pages)
    if missing:
        return (
            f"persisted ledger omits authoritative printed pages {missing[:8]}"
            + (" …" if len(missing) > 8 else ""),
        )
    return ()


def _report_schema_ok(report: CorpusEvidenceReport, transform_config: object) -> bool:
    """Reuse-compatibility check for the evidence-report schema (R17).

    The *contextual* half of the schema question, and the only half left here:
    the canonical model already proves the report declares the supported
    version, so this compares that version with the one recorded in the stored
    transform configuration. Binding the schema version into the transform
    identity already gives a differently-schema'd release a different
    ``package_uuid``; this is the fail-closed backstop on the reuse path.

    Takes the **parsed** report, never the raw payload: a raw-dictionary report
    verifier beside the canonical model is the duplication this conversion
    removed.
    """
    if not isinstance(transform_config, dict):
        return False
    return (
        report.report_version == EVIDENCE_REPORT_SCHEMA_VERSION
        and transform_config.get("evidence_report_schema_version")
        == EVIDENCE_REPORT_SCHEMA_VERSION
    )


def verify_single_source(session: Session, pkg: str) -> tuple[str, ...]:
    """Fail-closed Issue-5c single-source invariant over the persisted rows.

    The corpus release must have **exactly one** authoritative RuleSource, with a
    deterministic ``source_id == package_uuid``, the expected metadata, enabled,
    and **every** persisted chunk assigned to it (PR #134 defect family 3).
    Reconstructed from persisted state — never trusting candidate assertions.
    Returns the list of violations; publication must fail closed when non-empty.
    """
    sources = list(
        session.execute(
            select(RuleSourceORM).where(RuleSourceORM.rules_package_id == pkg)
        ).scalars()
    )
    violations: list[str] = []
    # The authoritative source is deterministically the one whose id == the
    # package uuid; any other source row is an unexpected extra (checked
    # explicitly rather than via a bare count so the reassigned-chunk case —
    # whose target source must exist to satisfy the composite FK — reports the
    # specific chunk violation too).
    authoritative = next((s for s in sources if s.source_id == pkg), None)
    for extra in sorted(s.source_id for s in sources if s.source_id != pkg):
        violations.append(f"unexpected extra source {extra} (only one is allowed)")
    if authoritative is None:
        violations.append(f"no authoritative source with source_id == {pkg}")
    else:
        if authoritative.name != _SOURCE_NAME:
            violations.append(
                f"authoritative source name {authoritative.name!r} unexpected"
            )
        if authoritative.category != _SOURCE_CATEGORY:
            violations.append(
                f"authoritative source category {authoritative.category!r} unexpected"
            )
        if authoritative.precedence_rank != _SOURCE_PRECEDENCE:
            violations.append(
                f"authoritative source precedence_rank "
                f"{authoritative.precedence_rank} unexpected"
            )
        if not authoritative.is_enabled:
            violations.append("authoritative source is disabled")
    mismatched = sorted(
        (row.chunk_id, row.source_id)
        for row in session.execute(
            select(RuleChunkORM).where(RuleChunkORM.rules_package_id == pkg)
        ).scalars()
        if row.source_id != pkg
    )
    for cid, wrong_source in mismatched:
        violations.append(
            f"chunk {cid} assigned to source {wrong_source} other than the "
            "single authoritative source"
        )
    return tuple(violations)


def verify_chunk_runtime_membership(session: Session, pkg: str) -> tuple[str, ...]:
    """Fail-closed check: DB-persisted ``rp_chunks`` vs. the declared projection.

    The persisted-corpus digest and evidence report are computed only over the
    *declared-projection* chunk set (:func:`_load_members`); ``RulesPackageService``
    and vector reindexing instead read *every enabled* ``rp_chunks`` row for the
    package whose source is enabled. Those two views must coincide exactly for
    the published package to expose precisely the canonical, proven chunks —
    otherwise:

    * an extra enabled ``rp_chunks`` row with no declared projection would be
      served by runtime reads while remaining invisible to the digest/report
      (the orphan-chunk gap); or
    * a declared-projected chunk (or its source) disabled after persistence
      would still count in the digest/report while runtime reads omit it.

    Returns the list of such violations; publication must fail closed when
    non-empty (Component I).
    """
    projected_ids = {
        chunk_id
        for chunk_id in session.execute(
            select(CorpusProjectionORM.chunk_id).where(
                CorpusProjectionORM.package_uuid == pkg
            )
        ).scalars()
    }
    chunk_rows = {
        row.chunk_id: row
        for row in session.execute(
            select(RuleChunkORM).where(RuleChunkORM.rules_package_id == pkg)
        ).scalars()
    }
    persisted_ids = set(chunk_rows)

    violations: list[str] = []
    for cid in sorted(persisted_ids - projected_ids):
        violations.append(
            f"orphan rp_chunks row {cid} has no declared projection but would "
            "be served by runtime reads"
        )
    for cid in sorted(projected_ids - persisted_ids):
        violations.append(f"declared projection references missing rp_chunks row {cid}")

    source_rows = {
        row.source_id: row
        for row in session.execute(
            select(RuleSourceORM).where(RuleSourceORM.rules_package_id == pkg)
        ).scalars()
    }
    for cid in sorted(projected_ids & persisted_ids):
        row = chunk_rows[cid]
        if not row.is_enabled:
            violations.append(
                f"declared-projected chunk {cid} is disabled; runtime reads "
                "would omit it"
            )
            continue
        source = source_rows.get(row.source_id)
        if source is None or not source.is_enabled:
            violations.append(
                f"declared-projected chunk {cid} source {row.source_id} is "
                "disabled; runtime reads would omit it"
            )
    return tuple(violations)


def recompute_persisted_digest(
    session: Session,
    pkg: str,
    vector_state: dict[str, object],
) -> str:
    """Recompute the persisted-corpus digest from the actual DB rows plus the
    actual read-back vector logical state (``vector_state``).

    The applied policy is reconstructed and validated from the persisted rows
    (:func:`_load_policy`), never a caller/default policy — so tampering the
    persisted policy version/hash/payload/cross-reference fails closed here (PR
    #134 P1). The caller supplies ``vector_state`` from
    :func:`read_actual_vector_state` (never a SQL-synthesized fiction), so a
    missing/stale/tampered Chroma collection recomputes to a different digest.
    """
    release = session.execute(
        select(CorpusReleaseORM).where(CorpusReleaseORM.package_uuid == pkg)
    ).scalar_one()
    policy = _load_policy(session, pkg)
    ledger = _load_ledger(session, pkg)
    recon = _load_reconciliation(session, pkg, policy)
    members = _load_members(session, pkg, ledger)
    sources = _load_sources(session, pkg)
    return persisted_corpus_digest(
        release.package_uuid,
        release.release_version,
        ledger,
        members,
        recon,
        policy,
        sources,
        vector_state,
    )


def verify_persisted_digest(
    session: Session,
    pkg: str,
    vector_state: dict[str, object],
) -> bool:
    """True iff the recomputed digest matches the stored release digest.

    ``vector_state`` is the actual read-back vector logical state; pass the
    output of :func:`read_actual_vector_state` so a divergent Chroma collection
    (as well as any tampered SQL row) makes this return ``False``. An
    inconsistent persisted *policy* fails closed by raising
    :class:`PolicyReconstructionError` (a stronger signal than a digest
    mismatch) rather than returning ``False``.
    """
    release = session.execute(
        select(CorpusReleaseORM).where(CorpusReleaseORM.package_uuid == pkg)
    ).scalar_one()
    return recompute_persisted_digest(session, pkg, vector_state) == (
        release.persisted_corpus_digest
    )


#: What a downstream consumer must be able to prove about a release before it
#: may treat that release as authority. Each entry is
#: ``(evidence-report key, rp_corpus_releases column)``: the recorded report and
#: the recorded release row must state the same proof identity, or one of them
#: has been edited since publication.
_REPORT_PROOF_COLUMNS = (
    ("authoritative_source_hash", "authoritative_source_hash"),
    ("transform_config_hash", "transform_config_hash"),
    ("bundle_root_hash", "bundle_root_hash"),
    ("frozen_source_ledger_hash", "ledger_hash"),
    ("persisted_corpus_digest", "persisted_corpus_digest"),
)


def _recorded_release_violations(
    release: CorpusReleaseORM,
    package: RulesPackageORM | None,
    report: CorpusEvidenceReport,
) -> tuple[str, ...]:
    """Every invariant the *recorded* 5c publication record must satisfy.

    One closure rather than a growing list of remembered checks. Each review
    round added the next field somebody noticed was missing — the transform
    configuration's own hash, then the corpus report reference — and both were
    invariants ``gate.run_gate`` already required at publication. The downstream
    seam was re-deriving the release proof from memory instead of stating it.

    Scope is deliberate: this proves what the *rows* must say about each other,
    needing no corpus reconstruction. Declared-binding equality, the contextual
    report-versus-config comparison, and everything requiring reconstructed
    ledger/policy/reconciliation state stay with the verifier's later stages;
    Chroma stays out entirely (Owner Decision 2026-08-01).
    """
    violations: list[str] = []

    if package is None:
        violations.append(f"no rp_packages row for {release.package_uuid}")
    elif package.publication_status != "published" or not package.is_enabled:
        violations.append(
            f"rp_packages row for {release.package_uuid} is not published and "
            f"enabled (publication_status={package.publication_status!r}, "
            f"is_enabled={package.is_enabled})"
        )
    elif package.published_at is None:
        violations.append(
            f"rp_packages row for {release.package_uuid} is published but "
            "records no published_at"
        )

    if release.publication_status != "published":
        violations.append(
            f"release {release.package_uuid} is in publication_status "
            f"{release.publication_status!r}, not 'published'"
        )

    # The transform configuration is the authority every contextual identity
    # comparison rests on, so it has to prove it is the configuration whose hash
    # minted this package before any of them may read it.
    if not isinstance(release.transform_config, dict):
        violations.append("recorded transform configuration is not an object")
    elif hash_obj(release.transform_config) != release.transform_config_hash:
        violations.append(
            "recorded transform configuration does not hash to the release's "
            "recorded transform_config_hash"
        )

    # The report is hashed through the canonical serializer — the same call
    # publication makes — never over the row's raw JSON.
    derived = report_hash(EvidenceReport(payload=report, persisted=True))
    if derived != release.evidence_report_hash:
        violations.append(
            "recorded evidence-report payload does not hash to the recorded "
            "evidence_report_hash"
        )
    # ``run_gate`` condition 16 requires these to be the same value. A cleared or
    # redirected reference is a release that no longer satisfies its own
    # publication invariant.
    if release.corpus_report_reference != release.evidence_report_hash:
        violations.append(
            f"corpus_report_reference {release.corpus_report_reference!r} != "
            f"evidence_report_hash {release.evidence_report_hash!r}"
        )

    for report_key, column in _REPORT_PROOF_COLUMNS:
        if getattr(report, report_key) != getattr(release, column):
            violations.append(
                f"recorded evidence report states {report_key}="
                f"{getattr(report, report_key)!r}, release row records "
                f"{column}={getattr(release, column)!r}"
            )

    for column in (
        "release_version",
        "authoritative_source_hash",
        "transform_config_hash",
        "bundle_root_hash",
        "persisted_corpus_digest",
        "ledger_hash",
        "policy_hash",
        "reconciliation_hash",
        "evidence_report_hash",
        "corpus_report_reference",
    ):
        if not getattr(release, column):
            violations.append(f"release {release.package_uuid} records no {column}")

    return tuple(violations)


def _recorded_identity_violations(
    report: CorpusEvidenceReport, transform_config: dict[str, Any]
) -> tuple[str, ...]:
    """Does the report's recorded identity match the recorded transform config?

    The canonical value proves these maps are complete and correctly shaped; it
    cannot know whether they describe *this* release. That comparison needs the
    stored transform configuration — which the caller has already proven hashes
    to its recorded identity, so it is authority here rather than another
    unverified row.

    Every fragment comes from **one** canonical dump. Serializing the nested
    values independently would be a second rendering of the report, and the two
    could diverge the moment the canonical dump normalizes anything.
    """
    recorded = report.dump()
    identity = dict(recorded["transform_identity"])
    extractor = identity.pop("extractor")

    violations: list[str] = []
    if extractor != transform_config.get("extraction_config"):
        violations.append(
            "recorded evidence report's extractor identity != the release's "
            "recorded transform extraction_config"
        )
    stored_identity = transform_config.get("transform_identity")
    if not isinstance(stored_identity, dict) or identity != _jsonish(stored_identity):
        violations.append(
            "recorded evidence report's transform identity != the release's "
            "recorded transform_identity"
        )
    if recorded["rules_corpus_vector_identity"] != _jsonish(
        transform_config.get("rules_corpus_vector_identity")
    ):
        violations.append(
            "recorded evidence report's rules-corpus vector identity != the "
            "release's recorded rules_corpus_vector_identity"
        )
    return tuple(violations)


def _jsonish(value: object) -> object:
    """Normalize in-memory tuples to the JSON shape the report round-trips as.

    ``transform_identity()`` returns tuples that JSON renders as arrays, and the
    two hash identically (:func:`hashing.canonical_bytes`). Comparing the parsed
    report against the in-memory config therefore needs the same normalization
    the wire format already applies — not a change to either side.
    """
    if isinstance(value, dict):
        return {k: _jsonish(v) for k, v in value.items()}
    if isinstance(value, tuple | list):
        return [_jsonish(v) for v in value]
    return value


def _recomputed_report_violations(
    report: CorpusEvidenceReport,
    ledger: SourceLedger,
    recon: ReconciliationMember,
    policy: ReconciliationPolicy,
) -> tuple[str, ...]:
    """Does the report's arithmetic match the state actually persisted?

    Every summary here is recomputable from reconstructed rows, so a recorded
    total that was edited and rehashed is caught by *derivation* rather than by
    a schema rule. What is deliberately not recomputed: the concordance and
    canary results, which would require reopening the authoritative PDF, and
    the vector half of the persisted-corpus digest, which would require Chroma
    (Owner Decision 2026-08-01). Those are verified through their closed
    successful recorded form instead.
    """
    disp_by_leaf = {d.leaf_id: d for d in recon.dispositions}
    leaf_totals: Counter[str] = Counter()
    represented: Counter[str] = Counter()
    excluded: Counter[str] = Counter()
    for leaf in ledger.leaves:
        leaf_totals[leaf.leaf_type.value] += 1
        disposition = disp_by_leaf.get(leaf.leaf_id)
        if disposition is None:
            continue
        if disposition.disposition is Disposition.REPRESENTED:
            represented[leaf.leaf_type.value] += 1
        elif (
            disposition.disposition is Disposition.EXCLUDED
            and disposition.exclusion_reason_code
        ):
            excluded[disposition.exclusion_reason_code] += 1

    expected: dict[str, object] = {
        "source_ledger_leaf_totals": dict(sorted(leaf_totals.items())),
        "represented_totals": dict(sorted(represented.items())),
        "excluded_totals_by_reason": dict(sorted(excluded.items())),
        "declared_projection_count": len(recon.projections),
        "unresolved_leaves": recon.unresolved_leaves,
        "accounting": {
            "inventoried_leaves": recon.inventoried_leaves,
            "represented_leaves": recon.represented_leaves,
            "excluded_leaves": recon.excluded_leaves,
            "unresolved_leaves": recon.unresolved_leaves,
        },
        "findings": {
            "gaps": len(recon.findings.gaps),
            "overlaps": len(recon.findings.overlaps),
            "orphans": len(recon.findings.orphans),
            "duplications": len(recon.findings.duplications),
        },
        "reconciliation_policy_reference": {
            "policy_version": policy.policy_version,
            "policy_hash": policy_hash(policy),
            "applied_policy_hash": recon.policy_hash,
        },
    }
    recorded = report.dump()
    return tuple(
        f"recorded evidence report states {field}={recorded[field]!r}, "
        f"reconstructed 5c state derives {value!r}"
        for field, value in expected.items()
        if recorded[field] != value
    )


def verify_published_release(
    session: Session,
    pkg: str,
    *,
    release_version: str,
    authoritative_source_hash: str,
    transform_config_hash: str,
    bundle_root_hash: str,
    corpus_digest: str,
) -> tuple[str, ...]:
    """Prove that *pkg* is an exactly-published, reconstructable 5c release.

    The seam a downstream subsystem calls before treating this release as
    authority — CRD Issue 5d binds its mechanical projections to a release by
    six values, and comparing those values only against each other proves that
    two claims agree, not that the release they name exists and is published.
    Owned here because every reconstruction and proof primitive it needs is
    already here; 5d calls it rather than re-deriving a second opinion about
    what a published 5c release is.

    The five declared values (plus *pkg* itself) must equal the authoritative
    ``rp_corpus_releases`` row, that row must be published under a
    published/enabled ``rp_packages`` row, its recorded evidence report must
    still hash to its recorded hash, state the same proof identities as the row,
    **and record a successful publication verdict**
    (:func:`report.recorded_success_violations`), and the ledger, reconciliation,
    and bundle-root identities must be exactly what the persisted rows
    reconstruct to.

    **What this cannot re-prove.** ``persisted_corpus_digest`` binds the actual
    read-back *vector* logical state as well as SQL (Component A), so it is not
    recomputable from a session alone. It is verified here as an exact recorded
    value, cross-checked against the recorded evidence report, and its
    cross-store half remains proven by :func:`finalize_release`, which is the
    only path that may set it. Re-proving that half needs a Chroma client and
    belongs to a caller that has one.

    Returns the violations, empty iff the release is publishable authority.
    """
    violations: list[str] = []
    release = session.execute(
        select(CorpusReleaseORM).where(CorpusReleaseORM.package_uuid == pkg)
    ).scalar_one_or_none()
    if release is None:
        # Nothing further is meaningful: there is no authoritative release to
        # compare a declaration with.
        return (f"no rp_corpus_releases row for package {pkg}",)
    package_row = session.execute(
        select(RulesPackageORM).where(RulesPackageORM.rules_package_id == pkg)
    ).scalar_one_or_none()

    for field, declared in (
        ("release_version", release_version),
        ("authoritative_source_hash", authoritative_source_hash),
        ("transform_config_hash", transform_config_hash),
        ("bundle_root_hash", bundle_root_hash),
        ("persisted_corpus_digest", corpus_digest),
    ):
        recorded = getattr(release, field)
        if recorded != declared:
            violations.append(
                f"declared {field} {declared!r} is not the authoritative "
                f"release's {recorded!r}"
            )

    payload = release.report_payload
    if release.evidence_report_hash is None or payload is None:
        violations.append(
            f"release {pkg} carries no recorded evidence report "
            "(hash and/or payload absent)"
        )
        # Everything below reads that payload, so continuing would bury the real
        # finding under violations derived from it.
        return tuple(violations)
    # Intrinsic shape, closed populations, canonical constants, and value
    # domains: the canonical model's, not this function's. The raw payload is
    # input to parsing and nothing else — a report is never verified from the
    # dictionary it arrived in.
    report, parse_violations = parse_recorded_report(payload)
    if report is None:
        violations.extend(
            f"recorded evidence report is not the canonical schema: {v}"
            for v in parse_violations
        )
        return tuple(violations)

    if not _report_schema_ok(report, release.transform_config):
        violations.append(
            "recorded evidence-report schema version "
            f"(report={report.report_version!r}) is contradictory vs the "
            f"supported {EVIDENCE_REPORT_SCHEMA_VERSION!r} recorded in the "
            "release's transform configuration"
        )
        return tuple(violations)

    # The external publication record, as one closed invariant rather than the
    # checks this function happened to remember.
    closure = _recorded_release_violations(release, package_row, report)
    violations.extend(closure)
    if closure:
        # Every comparison below reads the transform configuration or the row
        # identities the closure just refused; continuing would derive noise
        # from state already known to be untrustworthy.
        return tuple(violations)

    # Identity is necessary but not sufficient. A report edited to "fail" — or to
    # "pass" over summaries that record failures — and rehashed keeps every proof
    # identity intact while recording that publication did not succeed.
    violations.extend(
        f"recorded evidence report is not a successful 5c verdict: {v}"
        for v in report.success_violations()
    )
    assert isinstance(release.transform_config, dict)  # proven by the closure
    violations.extend(_recorded_identity_violations(report, release.transform_config))

    try:
        policy = _load_policy(session, pkg)
        ledger = _load_ledger(session, pkg)
        recon = _load_reconciliation(session, pkg, policy)
        members = _load_members(session, pkg, ledger)
    except (PolicyReconstructionError, SQLAlchemyError, KeyError, ValueError) as exc:
        # Deliberately broad: this runs over rows that may have been partially
        # migrated or edited directly, and every way that can fail — a missing
        # row, an unreadable enum, a findings key that is gone — means the same
        # thing, that the release does not reconstruct.
        violations.append(
            f"release {pkg} does not reconstruct from persisted rows: {exc}"
        )
        return tuple(violations)

    # ``_load_policy`` already fails closed on a policy_hash that disagrees with
    # the policy row, the reconciliation row, or the release row, so the policy
    # identity is proven by having got here at all.
    for label, recomputed, recorded in (
        ("ledger_hash", ledger_hash(ledger), release.ledger_hash),
        (
            "reconciliation_hash",
            reconciliation_hash(recon),
            release.reconciliation_hash,
        ),
        (
            "bundle_root_hash",
            build_bundle(ledger, members, recon).bundle_root_hash,
            release.bundle_root_hash,
        ),
    ):
        if recomputed != recorded:
            violations.append(
                f"recorded {label} {recorded!r} is not what the reconstructed "
                f"5c state derives ({recomputed!r})"
            )

    violations.extend(_recomputed_report_violations(report, ledger, recon, policy))
    violations.extend(verify_single_source(session, pkg))
    violations.extend(verify_chunk_runtime_membership(session, pkg))
    return tuple(violations)


def reconstruct_payload(
    session: Session,
    pkg: str,
    vector_state: dict[str, object],
) -> dict[str, object]:
    """Reconstruct the canonical persisted-corpus payload from the DB (debug)."""
    release = session.execute(
        select(CorpusReleaseORM).where(CorpusReleaseORM.package_uuid == pkg)
    ).scalar_one()
    policy = _load_policy(session, pkg)
    ledger = _load_ledger(session, pkg)
    recon = _load_reconciliation(session, pkg, policy)
    members = _load_members(session, pkg, ledger)
    sources = _load_sources(session, pkg)
    return persisted_corpus_payload(
        release.package_uuid,
        release.release_version,
        ledger,
        members,
        recon,
        policy,
        sources,
        vector_state,
    )


def delete_release(session: Session, pkg: str) -> None:
    """Remove a release and all its rows (cascade via FK + explicit chunks)."""
    session.execute(delete(RuleChunkORM).where(RuleChunkORM.rules_package_id == pkg))
    session.execute(
        delete(RulesPackageORM).where(RulesPackageORM.rules_package_id == pkg)
    )
    session.flush()


# ---------------------------------------------------------------------------
# finalize_release — Component K steps c–g, the corrected publication lifecycle
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FinalizeResult:
    """Outcome of :func:`finalize_release`.

    ``reused`` is True only for the idempotent no-op path: an identical release
    (same content-derived ``package_uuid``) was already published in this
    database, so nothing was re-persisted or mutated. ``artifacts`` is populated
    whenever ``published`` is True (fresh publish or verified reuse); ``gate``
    is populated whenever a fresh publish attempt was made (whether it passed
    or failed) and is ``None`` on the reuse path, where the gate does not
    re-run.
    """

    published: bool
    reused: bool
    artifacts: ReleaseArtifacts | None
    gate: GateResult | None


def _reconstruct_artifacts(
    session: Session,
    pkg: str,
    *,
    pages: list[ExtractedPage],
    bundle: CanonicalBundle,
    vector_state: dict[str, object],
) -> tuple[ReleaseArtifacts, tuple[str, ...], tuple[str, ...]]:
    """Load a fully-persisted release's DB-grounded artifacts + its chunk-runtime
    membership and single-source violations (used by both the fresh-publish and
    the idempotent-reuse path).

    The applied policy is reconstructed and validated from the persisted rows
    (:func:`_load_policy`), never a caller policy — so a tampered persisted policy
    fails closed here (PR #134 P1). ``vector_state`` is the actual read-back
    vector logical state; it is carried on the artifacts so the gate recomputes
    the persisted-corpus digest over the real cross-store state (Component A /
    K step c).
    """
    release_row = session.execute(
        select(CorpusReleaseORM).where(CorpusReleaseORM.package_uuid == pkg)
    ).scalar_one()
    policy = _load_policy(session, pkg)
    ledger = _load_ledger(session, pkg)
    recon = _load_reconciliation(session, pkg, policy)
    members = _load_members(session, pkg, ledger)
    sources = _load_sources(session, pkg)
    membership_violations = verify_chunk_runtime_membership(session, pkg)
    source_violations = verify_single_source(session, pkg)
    concordance = check_concordance(members.chunks, pages)
    canaries = check_canaries(pages)

    assert release_row.evidence_report_hash is not None
    assert release_row.persisted_corpus_digest is not None
    assert release_row.corpus_report_reference is not None
    assert release_row.report_payload is not None

    identity = ReleaseIdentity(
        authoritative_source_hash=release_row.authoritative_source_hash,
        transform_config_hash=release_row.transform_config_hash,
        bundle_root_hash=release_row.bundle_root_hash,
        evidence_report_hash=release_row.evidence_report_hash,
        persisted_corpus_digest=release_row.persisted_corpus_digest,
    )
    release_record = ReleaseRecord(
        package_uuid=pkg,
        release_version=release_row.release_version,
        identity=identity,
        transform_config=release_row.transform_config,
        ledger_hash=release_row.ledger_hash,
        policy_hash=release_row.policy_hash,
        reconciliation_hash=release_row.reconciliation_hash,
        corpus_report_reference=release_row.corpus_report_reference,
    )
    # The stored payload is parsed back through the canonical model, never
    # wrapped as-is: reconstruction is a read of unknown-provenance JSON, and a
    # payload that is not this schema must fail here rather than flow onward as
    # a report-shaped dict.
    parsed, parse_violations = parse_recorded_report(release_row.report_payload)
    if parsed is None:
        raise PersistedReportError(
            f"stored evidence report for {pkg} is not the canonical "
            f"{EVIDENCE_REPORT_SCHEMA_VERSION} schema: {list(parse_violations)}"
        )
    report = EvidenceReport(payload=parsed, persisted=True)
    artifacts = ReleaseArtifacts(
        pages=pages,
        ledger=ledger,
        members=members,
        reconciliation=recon,
        policy=policy,
        bundle=bundle,
        report=report,
        release=release_record,
        concordance=concordance,
        canaries=canaries,
        sources=sources,
        vector_state=vector_state,
    )
    return artifacts, membership_violations, source_violations


def finalize_release(
    session: Session,
    candidate: CandidateRelease,
    *,
    now: str,
    chroma_client: ClientAPI,
    retrieval_config: RetrievalMemoryConfig,
    embedding_function: RetrievalEmbeddingFunction | None = None,
) -> FinalizeResult:
    """Production publication entry: prove authoritative-source completeness,
    then finalize.

    The sole production path. Before any SQL flush or Chroma write, it rejects a
    candidate that does not exhaustively match the authoritative 364-page PDF —
    an omitted, duplicated, reordered, or substituted page (PR #134 completeness
    defect). Because the guard runs before persistence, a rejected candidate
    leaves no package, release, or vector state (nothing to roll back). The
    persist→reconstruct→digest→report→gate→publish machinery lives in the private
    :func:`_finalize_core`; only that already-validated core is reachable to
    lower-layer tests, and it is never a production validation bypass (no test
    flag, caller boolean, or public shortcut).
    """
    completeness_failures = verify_source_completeness(candidate.pages)
    # Independent table oracle: the live reconstruction must match the committed
    # expected-table inventory (R15 F4) — a suppressed, flattened, fragmented,
    # merged, or invented logical table blocks publication before any store
    # mutation. Full-corpus only; the private core seam (compact lower-layer
    # tests) legitimately bypasses this partial-corpus-invalid check.
    inventory = check_against_committed_inventory(candidate.pages)
    guard_failures = list(completeness_failures)
    if not inventory.passed:
        guard_failures.append(
            "table reconstruction diverges from the committed expected-table "
            f"inventory (suppressed={len(inventory.suppressed)}, "
            f"invented={len(inventory.invented)}, "
            f"mismatched={len(inventory.mismatched)})"
        )
    if guard_failures:
        return FinalizeResult(
            published=False,
            reused=False,
            artifacts=None,
            gate=GateResult(passed=False, failures=tuple(guard_failures)),
        )
    return _finalize_core(
        session,
        candidate,
        now=now,
        chroma_client=chroma_client,
        retrieval_config=retrieval_config,
        embedding_function=embedding_function,
    )


def _finalize_core(
    session: Session,
    candidate: CandidateRelease,
    *,
    now: str,
    chroma_client: ClientAPI,
    retrieval_config: RetrievalMemoryConfig,
    embedding_function: RetrievalEmbeddingFunction | None = None,
) -> FinalizeResult:
    """Persist, reconstruct, prove, gate, and (only if the gate passes) publish.

    Private core assuming the candidate's authoritative-source completeness has
    already been proven by :func:`finalize_release` (production) — or that the
    caller is a lower-layer test deliberately exercising the persist/reconstruct/
    digest/gate lifecycle on a compact, partial corpus through this internal seam.
    It is NOT a production entry point and performs no completeness check itself.

    Executes Component K steps c–g in the mandated order, across **both** stores:

    1. Idempotency check: an already-*published* release for this content
       -derived ``package_uuid`` is a safe no-op — but only after re-proving the
       existing cross-store state (full gate + package-row state + actual vector
       read-back); a changed source/config produces a different ``package_uuid``
       and is always a new release.
    2. (c) Persist the candidate as a non-runtime-visible ``draft`` into SQL
       (flushed, not committed) **and** reindex it into the real Chroma
       rules-corpus collection via the Issue 18 seam, then read the collection
       back and verify it against SQL ground truth.
    3. Reconstruct the authoritative logical state from the rows just persisted
       (never from the in-memory candidate) and verify DB-vs-declared chunk
       membership.
    4. (d) Compute the persisted-corpus digest from that reconstruction **plus
       the actual verified vector logical state**.
    5. Live legacy zero-reachability check against *this* session.
    6. (e) Generate the post-persistence evidence report; (f) hash it.
    7. (g) Run the final gate over the DB-grounded artifacts, with real
       (non-default) :class:`PublicationEvidence` for SQL persistence, vector
       write/verification, legacy reachability, and chunk-runtime membership.
    8. If the gate passes: transition both records to ``published``, set
       ``published_at``, and commit. If it fails: roll the SQL transaction back
       **and** drop the vector collection this attempt created — no partial
       content survives a failed gate in either store.

    The fresh path from step 2's first SQL mutation through the commit in step 8
    is a single exception boundary; the only SQL touched before it is the
    read-only idempotency ``select``. Vector cleanup is armed only across the
    window where a collection can exist, so a pre-vector failure rolls back SQL
    without creating, inspecting, or deleting anything in Chroma.
    """
    pkg = candidate.package_uuid

    existing = session.execute(
        select(CorpusReleaseORM).where(CorpusReleaseORM.package_uuid == pkg)
    ).scalar_one_or_none()
    if existing is not None:
        if existing.publication_status != "published":
            # persist_release/finalize_release only ever commit a row whose
            # publication_status is "published" (success) or roll back entirely
            # (failure) — a non-published row surviving to a new attempt means
            # an earlier run committed partway through, outside this contract.
            # Fail closed rather than silently mutating or republishing it.
            return FinalizeResult(
                published=False,
                reused=False,
                artifacts=None,
                gate=GateResult(
                    passed=False,
                    failures=(
                        f"release {pkg} already has a non-published row in "
                        f"publication_status={existing.publication_status!r}; "
                        "refusing to mutate — investigate before retrying",
                    ),
                ),
            )
        # Reuse path: verify the existing vectors against SQL ground truth
        # WITHOUT rewriting them, so a missing/stale/tampered collection cannot
        # be silently rebuilt into a false "successful reuse".
        vector_result = verify_only(
            session, pkg, chroma_client, retrieval_config, embedding_function
        )
        try:
            artifacts, membership_violations, source_violations = (
                _reconstruct_artifacts(
                    session,
                    pkg,
                    pages=candidate.pages,
                    bundle=candidate.bundle,
                    vector_state=vector_result.state.to_payload(),
                )
            )
        except PersistedReportError as exc:
            # A stored report that is not the canonical schema fails reuse
            # closed, as an ordinary failed result: publication must never
            # propagate a parse error to its caller.
            return FinalizeResult(
                published=False,
                reused=False,
                artifacts=None,
                gate=GateResult(
                    passed=False,
                    failures=(
                        "persisted evidence-report schema version is not the "
                        f"supported {EVIDENCE_REPORT_SCHEMA_VERSION!r}: {exc}",
                    ),
                ),
            )
        except PolicyReconstructionError as exc:
            # A missing/malformed/inconsistent persisted policy fails reuse closed
            # (reported as an ordinary failed result, consistent with the other
            # reuse-rejection cases) — never republished on a caller/default
            # policy (PR #134 P1).
            return FinalizeResult(
                published=False,
                reused=False,
                artifacts=None,
                gate=GateResult(
                    passed=False,
                    failures=(f"persisted reconciliation policy invalid: {exc}",),
                ),
            )
        sql_persist_ok = (
            len(artifacts.ledger.leaves) == len(candidate.ledger.leaves)
            and len(artifacts.members.chunks) == len(candidate.members.chunks)
            and not membership_violations
        )
        evidence = PublicationEvidence(
            sql_persist_ok=sql_persist_ok,
            vector_write_ok=vector_result.ok,
            chunk_membership_violations=len(membership_violations),
            source_membership_violations=len(source_violations),
            vector_verification_failures=vector_result.failures,
        )
        # Re-run the *full* gate against the reconstructed existing release —
        # not just the digest — so a reuse can't be accepted on a release whose
        # other proof identities (bundle root, evidence-report hash,
        # reconciliation hash), live legacy state, or actual vector state no
        # longer satisfy publication.
        gate = run_gate(artifacts, evidence)
        package_row = session.execute(
            select(RulesPackageORM).where(RulesPackageORM.rules_package_id == pkg)
        ).scalar_one_or_none()
        package_state_ok = (
            package_row is not None
            and package_row.is_enabled
            and package_row.publication_status == "published"
        )
        page_coverage_violations = verify_persisted_page_coverage(session, pkg)
        schema_ok = _report_schema_ok(
            artifacts.report.payload, artifacts.release.transform_config
        )
        if (
            not gate.passed
            or not package_state_ok
            or page_coverage_violations
            or not schema_ok
        ):
            failures = list(gate.failures)
            if not package_state_ok:
                failures.append(
                    f"rp_packages row for {pkg} is missing or not in a "
                    "published+enabled state consistent with its published "
                    "rp_corpus_releases row"
                )
            failures.extend(page_coverage_violations)
            if not schema_ok:
                failures.append(
                    "persisted evidence-report schema version "
                    f"(report={artifacts.report.payload.report_version!r}) is "
                    "missing/obsolete/contradictory vs the supported "
                    f"{EVIDENCE_REPORT_SCHEMA_VERSION!r} — refusing to reuse"
                )
            return FinalizeResult(
                published=False,
                reused=False,
                artifacts=None,
                gate=GateResult(passed=False, failures=tuple(failures)),
            )
        return FinalizeResult(
            published=True, reused=True, artifacts=artifacts, gate=gate
        )

    # --- c–g: one exception + cross-store compensation boundary ----------
    # The boundary begins BEFORE the first fresh-release SQL mutation, so a
    # failure during draft persistence (package/source/release/bundle rows) is
    # rolled back too — not only the vector attempt (PR #134 R19). Vector cleanup
    # starts DISARMED: a pre-vector SQL failure must never create, inspect, or
    # delete a Chroma collection. It is ARMED immediately before reindex_and_verify
    # (which may write the collection and then raise during read-back) and DISARMED
    # only after a successful publication commit. The Chroma write is not part of
    # the SQL transaction, so from arming until commit every unsuccessful exit rolls
    # back SQL and drops this attempt's collection (AGENTS.md rollback priority).
    cleanup_armed = False
    try:
        # --- c: persist the candidate as a non-runtime-visible SQL draft ---------
        source_id = _persist_package_and_source(
            session, pkg, candidate.release_version, now=now
        )
        _persist_release_record(
            session,
            pkg,
            release_version=candidate.release_version,
            authoritative_source_hash=candidate.authoritative_source_hash,
            transform_config_hash=candidate.transform_config_hash,
            bundle_root_hash=candidate.bundle.bundle_root_hash,
            evidence_report_hash=None,
            persisted_corpus_digest=None,
            ledger_hash=candidate.ledger_hash,
            policy_hash=candidate.policy_hash,
            reconciliation_hash=candidate.reconciliation_hash,
            corpus_report_reference=None,
            transform_config=candidate.transform_config,
            report_payload=None,
            now=now,
        )
        _persist_bundle_rows(
            session,
            pkg,
            source_id,
            ledger=candidate.ledger,
            recon=candidate.reconciliation,
            policy=candidate.policy,
            members=candidate.members,
            now=now,
        )

        # Arm vector cleanup now: reindex_and_verify can write the collection and
        # then raise during read-back. A pre-vector SQL failure above never reaches
        # here, so it can never create/inspect/delete a collection.
        cleanup_armed = True
        vector_result = reindex_and_verify(
            session, pkg, chroma_client, retrieval_config, embedding_function
        )

        # --- reconstruct strictly from what was just persisted ----------------
        # The applied policy is reconstructed + validated from the persisted rows
        # (never candidate.policy), so the digest/report/gate all bind the DB
        # -grounded policy (PR #134 P1).
        policy = _load_policy(session, pkg)
        membership_violations = verify_chunk_runtime_membership(session, pkg)
        source_violations = verify_single_source(session, pkg)
        ledger = _load_ledger(session, pkg)
        recon = _load_reconciliation(session, pkg, policy)
        members = _load_members(session, pkg, ledger)
        sources = _load_sources(session, pkg)

        # --- d: persisted-corpus digest from the actual persisted state (SQL +
        #        actual verified vector logical state) ------------------------
        vector_state = vector_result.state.to_payload()
        digest = persisted_corpus_digest(
            pkg,
            candidate.release_version,
            ledger,
            members,
            recon,
            policy,
            sources,
            vector_state,
        )

        # --- e: post-persistence evidence report; f: hash it ------------------
        concordance = check_concordance(members.chunks, candidate.pages)
        canaries = check_canaries(candidate.pages)
        report = build_report(
            ledger=ledger,
            members=members,
            recon=recon,
            policy=policy,
            authoritative_source_hash=candidate.authoritative_source_hash,
            transform_config_hash=candidate.transform_config_hash,
            transform_config=candidate.transform_config,
            bundle_root_hash=candidate.bundle.bundle_root_hash,
            ledger_hash_value=ledger_hash(ledger),
            persisted_corpus_digest=digest,
            concordance=concordance,
            canaries=canaries,
            persisted=True,  # legitimate: computed from the reconstruction above
        )
        report_h = report_hash(report)

        identity = ReleaseIdentity(
            authoritative_source_hash=candidate.authoritative_source_hash,
            transform_config_hash=candidate.transform_config_hash,
            bundle_root_hash=candidate.bundle.bundle_root_hash,
            evidence_report_hash=report_h,
            persisted_corpus_digest=digest,
        )
        release_record = ReleaseRecord(
            package_uuid=pkg,
            release_version=candidate.release_version,
            identity=identity,
            transform_config=candidate.transform_config,
            ledger_hash=candidate.ledger_hash,
            policy_hash=candidate.policy_hash,
            reconciliation_hash=candidate.reconciliation_hash,
            corpus_report_reference=report_h,
        )
        artifacts = ReleaseArtifacts(
            pages=candidate.pages,
            ledger=ledger,
            members=members,
            reconciliation=recon,
            policy=policy,
            bundle=candidate.bundle,
            report=report,
            release=release_record,
            concordance=concordance,
            canaries=canaries,
            sources=sources,
            vector_state=vector_state,
        )

        # Real evidence, not a rubber-stamped default: persistence is judged "ok"
        # only if reconstruction actually reproduced what was just written.
        sql_persist_ok = (
            len(ledger.leaves) == len(candidate.ledger.leaves)
            and len(members.chunks) == len(candidate.members.chunks)
            and not membership_violations
        )
        evidence = PublicationEvidence(
            sql_persist_ok=sql_persist_ok,
            vector_write_ok=vector_result.ok,
            chunk_membership_violations=len(membership_violations),
            source_membership_violations=len(source_violations),
            vector_verification_failures=vector_result.failures,
        )

        # --- g: fill in the post-persistence identity, then run the final gate -
        release_row = session.execute(
            select(CorpusReleaseORM).where(CorpusReleaseORM.package_uuid == pkg)
        ).scalar_one()
        release_row.evidence_report_hash = report_h
        release_row.persisted_corpus_digest = digest
        release_row.corpus_report_reference = report_h
        release_row.report_payload = report.dump()
        session.flush()

        gate = run_gate(artifacts, evidence)

        if gate.passed:
            package_row = session.execute(
                select(RulesPackageORM).where(RulesPackageORM.rules_package_id == pkg)
            ).scalar_one()
            package_row.publication_status = "published"
            package_row.published_at = now
            package_row.updated_at = now
            release_row.publication_status = "published"
            session.commit()
            # Publication is durable in both stores — only now is it safe to
            # disarm compensation.
            cleanup_armed = False
            return FinalizeResult(
                published=True, reused=False, artifacts=artifacts, gate=gate
            )

        # Expected failed gate: roll back SQL and drop this attempt's collection,
        # then return the ordinary failed result. Disarm first so that if this
        # cleanup itself fails, the except below re-raises it instead of retrying
        # — we never return a clean failed result while a collection leaked.
        session.rollback()
        cleanup_armed = False
        cleanup_vector_collection(chroma_client, pkg)
        return FinalizeResult(published=False, reused=False, artifacts=None, gate=gate)
    except Exception:
        # Any unsuccessful exit before a successful commit: an ordinary exception,
        # a commit exception, or a failed-gate cleanup failure. Roll back SQL and,
        # if still armed, drop this attempt's collection. The original exception
        # propagates; a cleanup failure is never swallowed (it chains onto it).
        session.rollback()
        if cleanup_armed:
            cleanup_vector_collection(chroma_client, pkg)
        raise
