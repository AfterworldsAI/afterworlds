"""Deterministic corpus evidence report — CRD Issue 5c, Component H.

A pipeline-generated (never hand-typed) report produced only after persistence
(K step e). It summarizes and verifies the frozen ledger, the frozen policy, the
reconciliation member, and the actual persisted state.

It contains the authoritative-source/transform/bundle-root/frozen-ledger hashes
and the persisted-corpus digest — but **not** its own hash — and is **not** a
bundle member (it contains the bundle root and cannot be covered by it). Its hash
is computed over the completed report (K step f) and recorded externally.

The payload's shape lives in exactly one place, :mod:`report_schema`. This
module builds that typed object and hashes its canonical dump; it holds no
second description of the document.
"""

from __future__ import annotations

import logging
import platform
from collections import Counter
from dataclasses import dataclass
from typing import Any

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
from afterworlds.ingestion.corpus.report_schema import (
    CANONICAL_CANARY_NAMES,
    EVIDENCE_REPORT_SCHEMA_VERSION,
    PYTHON_TARGET,
    Accounting,
    CorpusEvidenceReport,
    Findings,
    PolicyReference,
    ReproductionTarget,
    parse_recorded_report,
)

__all__ = [
    "CANONICAL_CANARY_NAMES",
    "EVIDENCE_REPORT_SCHEMA_VERSION",
    "PYTHON_TARGET",
    "CorpusEvidenceReport",
    "EvidenceReport",
    "build_report",
    "parse_recorded_report",
    "recorded_success_violations",
    "report_hash",
]

_log = logging.getLogger(__name__)


@dataclass(frozen=True)
class EvidenceReport:
    """The completed evidence report and the flag that it postdates persist.

    ``payload`` is the typed canonical object, not a dictionary. Anything that
    hashes, persists, or transmits the report goes through :meth:`dump`, so
    there is one serialization and no second rendering that could drift.
    """

    payload: CorpusEvidenceReport
    persisted: bool

    def dump(self) -> dict[str, Any]:
        """The canonical JSON-compatible payload — hashed and persisted."""
        return self.payload.dump()


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
    persisted: bool,
) -> EvidenceReport:
    """Build the evidence report after persistence (K step e).

    Constructs the canonical typed object directly — the model is the shape,
    not a lint pass over a dictionary. The recorded transform and vector
    identities are validated on the way in rather than copied through, so a
    config missing either one fails here instead of producing a report
    describing a release nobody can verify.
    """
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

    # Complete Component B transform identity: extractor config + the first-party
    # source manifest/hash + deterministic invocation + IR flag (not just
    # ledger.extraction_config — PR #134 P1). The recorded invocation's steps are
    # a tuple in memory and a list once JSON round-tripped; both canonicalize to
    # the same bytes, so normalizing here does not move the hash.
    recorded_identity = transform_config.get("transform_identity")
    transform_identity: dict[str, object] = {
        "extractor": transform_config.get("extraction_config"),
        **(recorded_identity if isinstance(recorded_identity, dict) else {}),
    }

    fields: dict[str, Any] = {
        # Canonical schema version, also bound into the transform identity so a
        # schema change remints the release rather than being reused (R17).
        "report_version": EVIDENCE_REPORT_SCHEMA_VERSION,
        # Proof hashes (NOT this report's own hash).
        "authoritative_source_hash": authoritative_source_hash,
        "transform_config_hash": transform_config_hash,
        "bundle_root_hash": bundle_root_hash,
        "frozen_source_ledger_hash": ledger_hash_value,
        "persisted_corpus_digest": persisted_corpus_digest,
        "transform_identity": transform_identity,
        # Identity-bearing rules-corpus vector configuration (embedding model +
        # logical schema/ID/metadata contract) bound into the release identity
        # (PR #134 P1); recorded so a model/schema change is on the record.
        "rules_corpus_vector_identity": transform_config.get(
            "rules_corpus_vector_identity"
        ),
        # The *declared* environment needed to reproduce the transform (Component
        # B): the Python target here, plus the exact pinned extractor/parser/tool
        # versions and deterministic invocation already carried by
        # ``transform_identity`` above. This is host-independent by construction —
        # no runtime host name, OS, architecture, absolute path, timestamp, or PID
        # enters this identity-bearing payload, so the same committed inputs yield a
        # byte-identical evidence report (hence release identity) on every supported
        # host (PR #134 R16). Actual host diagnostics are logged, never hashed.
        "reproduction_target": ReproductionTarget(python_target=PYTHON_TARGET),
        "reconciliation_policy_reference": PolicyReference(
            policy_version=policy.policy_version,
            policy_hash=policy_hash(policy),
            applied_policy_hash=recon.policy_hash,
        ),
        # Ledger + reconciliation summary.
        "source_ledger_leaf_totals": dict(sorted(leaf_totals.items())),
        "represented_totals": dict(sorted(represented_totals.items())),
        "excluded_totals_by_reason": dict(sorted(excluded_by_reason.items())),
        "unresolved_leaves": recon.unresolved_leaves,
        "declared_projection_count": len(recon.projections),
        "accounting": Accounting(
            inventoried_leaves=recon.inventoried_leaves,
            represented_leaves=recon.represented_leaves,
            excluded_leaves=recon.excluded_leaves,
            unresolved_leaves=recon.unresolved_leaves,
        ),
        "findings": Findings(
            gaps=len(recon.findings.gaps),
            overlaps=len(recon.findings.overlaps),
            orphans=len(recon.findings.orphans),
            duplications=len(recon.findings.duplications),
        ),
        "invalid_locators": len(concordance.locator_failures),
        "concordance_failures": len(concordance.content_failures),
        "version_canaries": {c.name: c.passed for c in canaries},
    }

    # The verdict is read off the assembled document through the same method a
    # stored report is measured by, so a report claiming "pass" over
    # contradictory summaries cannot be produced here — and an incomplete canary
    # run is refused by the model before the question is even asked.
    provisional = CorpusEvidenceReport.model_validate(
        {**fields, "prepublication_validation_status": "fail"}
    )
    status = "pass" if persisted and not provisional.verdict_violations() else "fail"

    # Actual host as an operational diagnostic ONLY — deliberately outside the
    # returned payload, so it never reaches the report hash, the persisted-corpus
    # digest, the package identity, or any publication-gate comparison. Never
    # labels the real host as the fixed target (PR #134 R16).
    _log.info(
        "corpus evidence report built (diagnostic, not hashed): host system=%s "
        "machine=%s python=%s",
        platform.system(),
        platform.machine(),
        platform.python_version(),
    )
    return EvidenceReport(
        payload=CorpusEvidenceReport.model_validate(
            {**fields, "prepublication_validation_status": status}
        ),
        persisted=persisted,
    )


def recorded_success_violations(payload: object) -> tuple[str, ...]:
    """Is a *recorded* report a well-formed, successful 5c verdict?

    Parse first, then judge. Shape, closed populations, and value domains
    belong to the typed model; this adds only the verdict question, on a
    document that has already proven it is this schema.

    Deliberately bounded to what the report contains. It reconstructs no
    history and does not reopen the vector store (Owner Decision 2026-08-01);
    agreement with the release row and with reconstructed 5c state is proven
    contextually by :func:`persistence.verify_published_release`.
    """
    parsed, violations = parse_recorded_report(payload)
    if parsed is None:
        return violations
    return parsed.success_violations()


def report_hash(report: EvidenceReport) -> str:
    """Hash the completed evidence report (K step f).

    Over the canonical dump of the typed payload — the same bytes SQL persists,
    so a stored report always rehashes to the value recorded beside it.
    """
    return hash_obj(report.dump())
