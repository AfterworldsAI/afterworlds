"""Acyclic reproducible production build — CRD Issue 5c, Component K (a0–g).

Drives the fixed acyclic order that produces every proof identity, so no
artifact is ever covered by a hash it contains and the evidence report is never
generated before the (logical) persisted state exists:

    a0  freeze the reconciliation policy (committed input, covered by B)
    a1  derive and hash the frozen source ledger
    a2  generate the canonical corpus members from the frozen ledger
    a3  apply only the frozen policy → reconciliation member
    b   compute the bundle-root hash
    (c  persist — see persistence layer)
    d   compute the persisted-corpus digest from the canonical logical state
    e   generate the evidence report (post-persistence)
    f   hash the completed evidence report
    g   record the five top-level hashes in the release record

A clean checkout regenerates a0–g byte-for-byte from committed inputs.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from afterworlds.ingestion.corpus.bundle import (
    build_bundle,
    derive_package_uuid,
    derive_release_version,
    persisted_corpus_digest,
    reconciliation_hash,
    transform_config_hash,
    transform_config_payload,
)
from afterworlds.ingestion.corpus.concordance import (
    CanaryResult,
    ConcordanceResult,
    check_canaries,
    check_concordance,
)
from afterworlds.ingestion.corpus.ledger import build_ledger, ledger_hash
from afterworlds.ingestion.corpus.models import (
    CanonicalBundle,
    CorpusBundleMembers,
    ReconciliationMember,
    ReconciliationPolicy,
    ReleaseIdentity,
    ReleaseRecord,
    SourceLedger,
)
from afterworlds.ingestion.corpus.pdf_source import (
    PDF_SHA256,
    ExtractedPage,
    extract_pages,
    extraction_config,
)
from afterworlds.ingestion.corpus.policy import FROZEN_POLICY, policy_hash
from afterworlds.ingestion.corpus.reconcile import reconcile
from afterworlds.ingestion.corpus.report import (
    EvidenceReport,
    build_report,
    report_hash,
)
from afterworlds.ingestion.corpus.transform import build_corpus


@dataclass(frozen=True)
class ReleaseArtifacts:
    """Everything a build produces, in one immutable bundle."""

    pages: list[ExtractedPage]
    ledger: SourceLedger
    members: CorpusBundleMembers
    reconciliation: ReconciliationMember
    policy: ReconciliationPolicy
    bundle: CanonicalBundle
    report: EvidenceReport
    release: ReleaseRecord
    concordance: ConcordanceResult
    canaries: tuple[CanaryResult, ...]


def build_release(
    pdf_path: Path,
    *,
    legacy_reachability_violations: int = 0,
    persisted: bool = True,
    policy: ReconciliationPolicy = FROZEN_POLICY,
) -> ReleaseArtifacts:
    """Execute steps a0–g and return the release artifacts (Component K)."""
    # a0 — freeze policy (committed input).
    p_hash = policy_hash(policy)
    ex_cfg = extraction_config()
    tconfig = transform_config_payload(ex_cfg, policy)
    thash = transform_config_hash(ex_cfg, policy)

    # a1 — derive + hash the frozen source ledger.
    pages = extract_pages(pdf_path)
    ledger = build_ledger(pages)
    l_hash = ledger_hash(ledger)

    package_uuid = derive_package_uuid(PDF_SHA256, thash)
    release_version = derive_release_version(thash)

    # a2 — generate canonical corpus members from the frozen ledger.
    members = build_corpus(ledger)

    # a3 — reconciliation by applying only the frozen policy.
    recon = reconcile(ledger, members, policy)
    r_hash = reconciliation_hash(recon)

    # b — bundle-root hash.
    bundle = build_bundle(ledger, members, recon)

    concordance = check_concordance(members.chunks, pages)
    canaries = check_canaries(pages)

    # d — persisted-corpus digest from the canonical logical persisted state.
    digest = (
        persisted_corpus_digest(
            package_uuid, release_version, ledger, members, recon, policy
        )
        if persisted
        else ""
    )

    # e — evidence report (post-persistence).
    report = build_report(
        ledger=ledger,
        members=members,
        recon=recon,
        policy=policy,
        authoritative_source_hash=PDF_SHA256,
        transform_config_hash=thash,
        bundle_root_hash=bundle.bundle_root_hash,
        ledger_hash_value=l_hash,
        persisted_corpus_digest=digest,
        concordance=concordance,
        canaries=canaries,
        legacy_reachability_violations=legacy_reachability_violations,
        persisted=persisted,
    )
    # f — hash the completed report.
    report_h = report_hash(report)

    # g — external release/publication record with the five top-level hashes.
    release = ReleaseRecord(
        package_uuid=package_uuid,
        release_version=release_version,
        identity=ReleaseIdentity(
            authoritative_source_hash=PDF_SHA256,
            transform_config_hash=thash,
            bundle_root_hash=bundle.bundle_root_hash,
            evidence_report_hash=report_h,
            persisted_corpus_digest=digest,
        ),
        transform_config=tconfig,
        ledger_hash=l_hash,
        policy_hash=p_hash,
        reconciliation_hash=r_hash,
        corpus_report_reference=report_h,
    )
    return ReleaseArtifacts(
        pages=pages,
        ledger=ledger,
        members=members,
        reconciliation=recon,
        policy=policy,
        bundle=bundle,
        report=report,
        release=release,
        concordance=concordance,
        canaries=canaries,
    )
