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

import logging
import platform
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

_log = logging.getLogger(__name__)

# The declared Python target (pyproject ``requires-python``; Python 3.12 only per
# CLAUDE.md). Recorded as a *declared, host-independent* reproduction target — the
# actual runtime interpreter/host is a diagnostic and never enters this
# identity-bearing payload (PR #134 R16).
PYTHON_TARGET = "3.12"

# Canonical evidence-report schema version. Bumped across canonical-shape changes:
# "2" for the R16 host-independent ``reproduction_target`` change; "3" for the R18
# pre-release clean-baseline change that removed the legacy-reachability status
# (Issue 5c Rev7 / Issue 18 Rev6 supersede the strict cross-store quarantine
# contract). This version is bound into ``transform_config_payload`` (hence the
# transform hash / package UUID / release version), so an evidence-report *schema*
# change mints a NEW immutable release instead of being reused under a
# predecessor's identity (R17 mechanism). It is deliberately an *explicit* schema
# identity rather than a byte-level hash of report.py: only an intentional
# canonical-shape change should remint, never a comment/docstring/logging edit.
EVIDENCE_REPORT_SCHEMA_VERSION = "5c-evidence-3"


@dataclass(frozen=True)
class EvidenceReport:
    """The completed evidence report payload and the flag that it postdates persist."""

    payload: dict[str, object]
    persisted: bool


# ---------------------------------------------------------------------------
# What a successful publication looks like in the report's own numbers
# ---------------------------------------------------------------------------
#
# One definition, consumed at two boundaries with different trust levels:
#
# * :func:`build_report` derives ``prepublication_validation_status`` from it, so
#   a report cannot be *written* claiming success alongside contradictory
#   summaries; and
# * :func:`recorded_success_violations` applies it to a payload read back out of
#   the database, whose provenance is unknown — JSON round-tripped, possibly
#   hand-edited, types unproven.
#
# ``gate.run_gate`` deliberately keeps its own one-line status check: it holds
# the freshly built :class:`EvidenceReport` object, with a live ``persisted``
# flag and typed sub-objects, so it asks a different question of a value it just
# produced. What must not diverge is the *semantics* below, and it does not.

#: Top-level payload counters that must be zero for a successful verdict.
_ZERO_COUNTERS = ("unresolved_leaves", "invalid_locators", "concordance_failures")
#: Reconciliation findings that must all be zero for a successful verdict.
_ZERO_FINDINGS = ("gaps", "overlaps", "orphans", "duplications")
#: Accounting keys, and the equation they must satisfy.
_ACCOUNTING_KEYS = (
    "inventoried_leaves",
    "represented_leaves",
    "excluded_leaves",
    "unresolved_leaves",
)
#: Every key ``build_report`` produces. A payload missing one is not this shape.
REQUIRED_REPORT_KEYS = frozenset(
    {
        "report_version",
        "authoritative_source_hash",
        "transform_config_hash",
        "bundle_root_hash",
        "frozen_source_ledger_hash",
        "persisted_corpus_digest",
        "transform_identity",
        "rules_corpus_vector_identity",
        "reproduction_target",
        "reconciliation_policy_reference",
        "source_ledger_leaf_totals",
        "represented_totals",
        "excluded_totals_by_reason",
        "unresolved_leaves",
        "declared_projection_count",
        "accounting",
        "findings",
        "invalid_locators",
        "concordance_failures",
        "version_canaries",
        "prepublication_validation_status",
    }
)


def _count(payload: dict[str, object], key: str) -> int | None:
    """A payload counter as an ``int``, or ``None`` if it is not one.

    ``bool`` is excluded explicitly: it is an ``int`` subclass, so ``True``
    would otherwise read as the count ``1`` and let a hand-edited report satisfy
    an equation with a boolean.
    """
    value = payload.get(key)
    return value if type(value) is int else None


def verdict_violations(payload: dict[str, object]) -> tuple[str, ...]:
    """Why these report numbers do not state a successful publication.

    Pure over the payload, so it says the same thing about a report being built
    and a report being read back. Empty exactly when every verdict-bearing
    summary is present, correctly typed, and success-valued.
    """
    violations: list[str] = []
    for key in _ZERO_COUNTERS:
        count = _count(payload, key)
        if count is None:
            violations.append(f"{key} is missing or not an integer")
        elif count != 0:
            violations.append(f"{key} is {count}, not 0")

    findings = payload.get("findings")
    if not isinstance(findings, dict):
        violations.append("findings is missing or not an object")
    else:
        for key in _ZERO_FINDINGS:
            found = findings.get(key)
            if type(found) is not int:
                violations.append(f"findings.{key} is missing or not an integer")
            elif found != 0:
                violations.append(f"findings.{key} is {found}, not 0")

    canaries = payload.get("version_canaries")
    if not isinstance(canaries, dict):
        violations.append("version_canaries is missing or not an object")
    else:
        for name, passed in sorted(canaries.items()):
            if type(passed) is not bool:
                violations.append(f"version_canaries.{name} is not a boolean")
            elif not passed:
                violations.append(f"version canary {name} did not pass")

    accounting = payload.get("accounting")
    if not isinstance(accounting, dict):
        violations.append("accounting is missing or not an object")
    else:
        counts: dict[str, int] = {}
        for key in _ACCOUNTING_KEYS:
            value = accounting.get(key)
            if type(value) is not int:
                violations.append(f"accounting.{key} is missing or not an integer")
            else:
                counts[key] = value
        if len(counts) == len(_ACCOUNTING_KEYS):
            if counts["unresolved_leaves"] != 0:
                violations.append(
                    f"accounting.unresolved_leaves is "
                    f"{counts['unresolved_leaves']}, not 0"
                )
            if counts["inventoried_leaves"] != (
                counts["represented_leaves"]
                + counts["excluded_leaves"]
                + counts["unresolved_leaves"]
            ):
                violations.append("accounting equation does not balance")
            top_level = _count(payload, "unresolved_leaves")
            if top_level is not None and top_level != counts["unresolved_leaves"]:
                violations.append(
                    "accounting.unresolved_leaves disagrees with the top-level "
                    "unresolved_leaves"
                )
    return tuple(violations)


def recorded_success_violations(payload: object) -> tuple[str, ...]:
    """Is a *recorded* evidence report a well-formed, successful 5c verdict?

    What a downstream consumer needs before treating a stored report as proof
    that a release published successfully. Identity — that the payload hashes to
    its recorded hash and states the release's proof identities — is necessary
    but not sufficient: a report edited to ``"fail"`` and rehashed keeps every
    identity intact while recording that publication did *not* succeed.

    Deliberately bounded to what the report actually contains. It reconstructs
    no history, and it does not reopen the vector store (Owner Decision
    2026-08-01); the recorded digest is verified as an exact recorded value by
    the caller.
    """
    if not isinstance(payload, dict):
        return (f"evidence report is {type(payload).__name__}, not an object",)
    violations: list[str] = []
    if payload.get("report_version") != EVIDENCE_REPORT_SCHEMA_VERSION:
        violations.append(
            f"report_version {payload.get('report_version')!r} is not the supported "
            f"{EVIDENCE_REPORT_SCHEMA_VERSION!r}"
        )
    if missing := sorted(REQUIRED_REPORT_KEYS - set(payload)):
        violations.append(f"evidence report is missing {missing}")
    status = payload.get("prepublication_validation_status")
    if status != "pass":
        violations.append(
            f"prepublication_validation_status is {status!r}, not 'pass' — the "
            "recorded evidence states this release did not publish successfully"
        )
    # Evaluated even when the status already says "pass": the defect being closed
    # is a payload that *claims* success while its own summaries record failures.
    violations.extend(verdict_violations(payload))
    return tuple(violations)


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

    payload: dict[str, object] = {
        # Canonical schema version, also bound into the transform identity so a
        # schema change remints the release rather than being reused (R17).
        "report_version": EVIDENCE_REPORT_SCHEMA_VERSION,
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
        # The *declared* environment needed to reproduce the transform (Component
        # B): the Python target here, plus the exact pinned extractor/parser/tool
        # versions and deterministic invocation already carried by
        # ``transform_identity`` above. This is host-independent by construction —
        # no runtime host name, OS, architecture, absolute path, timestamp, or PID
        # enters this identity-bearing payload, so the same committed inputs yield a
        # byte-identical evidence report (hence release identity) on every supported
        # host (PR #134 R16). Actual host diagnostics are logged, never hashed.
        "reproduction_target": {"python_target": PYTHON_TARGET},
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
    }
    # The verdict is derived from the payload that has just been assembled, not
    # from a second predicate over the source objects. One definition (below) of
    # what a successful publication looks like in the numbers, so a recorded
    # report claiming "pass" alongside contradictory summaries is impossible to
    # produce here and detectable everywhere it is read back.
    payload["prepublication_validation_status"] = (
        "pass" if persisted and not verdict_violations(payload) else "fail"
    )
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
    return EvidenceReport(payload=payload, persisted=persisted)


def report_hash(report: EvidenceReport) -> str:
    """Hash the completed evidence report (K step f)."""
    return hash_obj(report.payload)
