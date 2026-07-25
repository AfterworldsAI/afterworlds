"""Deterministic corpus evidence report — CRD Issue 5c, Component H.

A pipeline-generated (never hand-typed) report produced only after persistence
(K step e). It summarizes and verifies the frozen ledger, the frozen policy, the
reconciliation member, and the actual persisted state.

It contains the authoritative-source/transform/bundle-root/frozen-ledger hashes
and the persisted-corpus digest — but **not** its own hash — and is **not** a
bundle member (it contains the bundle root and cannot be covered by it). Its hash
is computed over the completed report (K step f) and recorded externally.
"""

from __future__ import annotations

import platform
import sys
from collections import Counter
from dataclasses import dataclass

from afterworlds.ingestion.corpus.concordance import CanaryResult, ConcordanceResult
from afterworlds.ingestion.corpus.hashing import hash_obj
from afterworlds.ingestion.corpus.models import (
    CorpusBundleMembers,
    Disposition,
    ReconciliationMember,
    ReconciliationPolicy,
    SourceLedger,
)
from afterworlds.ingestion.corpus.policy import policy_hash


@dataclass(frozen=True)
class EvidenceReport:
    """The completed evidence report payload and the flag that it postdates persist."""

    payload: dict[str, object]
    persisted: bool


def build_report(
    *,
    ledger: SourceLedger,
    members: CorpusBundleMembers,
    recon: ReconciliationMember,
    policy: ReconciliationPolicy,
    authoritative_source_hash: str,
    transform_config_hash: str,
    transform_config: dict[str, object],
    bundle_root_hash: str,
    ledger_hash_value: str,
    persisted_corpus_digest: str,
    concordance: ConcordanceResult,
    canaries: tuple[CanaryResult, ...],
    legacy_reachability_violations: int,
    persisted: bool,
) -> EvidenceReport:
    """Build the evidence report after persistence (K step e)."""
    leaf_totals = Counter(leaf.leaf_type.value for leaf in ledger.leaves)
    disp_by_leaf = {d.leaf_id: d for d in recon.dispositions}
    represented_totals: Counter[str] = Counter()
    excluded_by_reason: Counter[str] = Counter()
    for leaf in ledger.leaves:
        d = disp_by_leaf[leaf.leaf_id]
        if d.disposition is Disposition.REPRESENTED:
            represented_totals[leaf.leaf_type.value] += 1
        elif d.disposition is Disposition.EXCLUDED and d.exclusion_reason_code:
            excluded_by_reason[d.exclusion_reason_code] += 1

    prepublication_ok = (
        recon.unresolved_leaves == 0
        and not recon.findings.gaps
        and not recon.findings.overlaps
        and not recon.findings.orphans
        and not recon.findings.duplications
        and concordance.passed
        and all(c.passed for c in canaries)
        and legacy_reachability_violations == 0
        and persisted
    )

    payload: dict[str, object] = {
        "report_version": "5c-evidence-1",
        # Proof hashes (NOT this report's own hash).
        "authoritative_source_hash": authoritative_source_hash,
        "transform_config_hash": transform_config_hash,
        "bundle_root_hash": bundle_root_hash,
        "frozen_source_ledger_hash": ledger_hash_value,
        "persisted_corpus_digest": persisted_corpus_digest,
        # Complete Component B transform identity: extractor config + the
        # first-party source manifest/hash + deterministic invocation + IR flag
        # (not just ledger.extraction_config — PR #134 P1).
        "transform_identity": {
            "extractor": transform_config.get("extraction_config"),
            **(
                transform_config.get("transform_identity", {})  # type: ignore[dict-item]
                if isinstance(transform_config.get("transform_identity"), dict)
                else {}
            ),
        },
        # Identity-bearing rules-corpus vector configuration (embedding model +
        # logical schema/ID/metadata contract) bound into the release identity
        # (PR #134 P1); recorded so a model/schema change is on the record.
        "rules_corpus_vector_identity": transform_config.get(
            "rules_corpus_vector_identity"
        ),
        # The environment needed to reproduce the transform (Component B). Recorded
        # here (not in the corpus content hashes) so an identical corpus keeps the
        # same package identity across platforms while the environment stays on
        # record; reproducibility is claimed within this recorded environment.
        "reproduction_environment": {
            "python": f"{sys.version_info.major}.{sys.version_info.minor}",
            "platform_system": platform.system(),
            "platform_machine": platform.machine(),
        },
        "reconciliation_policy_reference": {
            "policy_version": policy.policy_version,
            "policy_hash": policy_hash(policy),
            "applied_policy_hash": recon.policy_hash,
        },
        # Ledger + reconciliation summary.
        "source_ledger_leaf_totals": dict(sorted(leaf_totals.items())),
        "represented_totals": dict(sorted(represented_totals.items())),
        "excluded_totals_by_reason": dict(sorted(excluded_by_reason.items())),
        "unresolved_leaves": recon.unresolved_leaves,
        "declared_projection_count": len(recon.projections),
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
        "invalid_locators": len(concordance.locator_failures),
        "concordance_failures": len(concordance.content_failures),
        "version_canaries": {c.name: c.passed for c in canaries},
        "legacy_reachability_violations": legacy_reachability_violations,
        "prepublication_validation_status": "pass" if prepublication_ok else "fail",
    }
    return EvidenceReport(payload=payload, persisted=persisted)


def report_hash(report: EvidenceReport) -> str:
    """Hash the completed evidence report (K step f)."""
    return hash_obj(report.payload)
