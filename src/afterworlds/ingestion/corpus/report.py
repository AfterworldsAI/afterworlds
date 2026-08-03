"""Deterministic corpus evidence report — CRD Issue 5c, Component H.

A pipeline-generated (never hand-typed) report produced only after persistence
(K step e). It summarizes and verifies the frozen ledger, the frozen policy, the
reconciliation member, and the actual persisted state.

It contains the authoritative-source/transform/bundle-root/frozen-ledger hashes
and the persisted-corpus digest — but **not** its own hash — and is **not** a
bundle member (it contains the bundle root and cannot be covered by it). Its hash
is computed over the completed report (K step f) and recorded externally.

The document itself is defined once, in :mod:`report_schema`. This module
assembles its inputs and hands them to the one parser; it holds no second
description of the payload's shape.
"""

from __future__ import annotations

import logging
import platform
from collections import Counter
from collections.abc import Mapping

from afterworlds.ingestion.corpus.concordance import CanaryResult, ConcordanceResult
from afterworlds.ingestion.corpus.hashing import canonical_bytes, hash_obj
from afterworlds.ingestion.corpus.models import (
    CorpusBundleMembers,
    Disposition,
    ReconciliationMember,
    ReconciliationPolicy,
    SourceLedger,
)
from afterworlds.ingestion.corpus.policy import policy_hash
from afterworlds.ingestion.corpus.report_schema import (
    EVIDENCE_REPORT_SCHEMA_VERSION,
    PYTHON_TARGET,
    CorpusEvidenceReport,
    canonical_report,
    parse_recorded_report,
)

_log = logging.getLogger(__name__)

#: Compatibility vocabulary, not a second type. ``EvidenceReport`` *is*
#: :class:`CorpusEvidenceReport` — the same class object, so there is nothing to
#: construct, nothing to unwrap, no ``payload`` to substitute and no ``persisted``
#: flag to trust. The name is retained for one concrete reason: ``pipeline.py``
#: imports it, and ``pipeline.py`` is one of the eleven modules whose source
#: bytes are bound into the transform identity. Retyping an annotation there
#: would remint the package UUID and release version over a post-persistence
#: plumbing edit that changes no candidate corpus, no bundle member, and no
#: report schema — an avoidable whole-file-hash side effect, not a transform
#: change. The alias keeps the audited source byte-identical while leaving
#: exactly one report representation in the system.
EvidenceReport = CorpusEvidenceReport

__all__ = [
    "EVIDENCE_REPORT_SCHEMA_VERSION",
    "PYTHON_TARGET",
    "REPORT_PROOF_COLUMNS",
    "EvidenceReport",
    "build_report",
    "recorded_identities",
    "recorded_success_violations",
    "report_hash",
    "report_state_violations",
    "state_derived_fields",
]


def state_derived_fields(
    *,
    ledger: SourceLedger,
    recon: ReconciliationMember,
    policy: ReconciliationPolicy,
    transform_config: dict[str, object],
) -> dict[str, object]:
    """The report claims that are a pure function of reconstructed 5c state.

    One definition, used twice and never reimplemented: :func:`build_report`
    emits these fields, and :func:`report_state_violations` recomputes them from
    the persisted rows and compares. Writing the comparison as "what would this
    report say if it were built from this state" means a field added to the
    document is checked contextually the moment it is derived here — the defect
    that let coherently rewritten totals pass was a *second*, shorter list of
    what to compare.
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

    identity = transform_config.get("transform_identity")
    return {
        # Complete Component B transform identity: extractor config + the
        # first-party source manifest/hash + deterministic invocation + IR flag
        # (not just ledger.extraction_config — PR #134 P1).
        "transform_identity": {
            "extractor": transform_config.get("extraction_config"),
            **(identity if isinstance(identity, dict) else {}),
        },
        # Identity-bearing rules-corpus vector configuration (embedding model +
        # logical schema/ID/metadata contract) bound into the release identity
        # (PR #134 P1); recorded so a model/schema change is on the record.
        "rules_corpus_vector_identity": transform_config.get(
            "rules_corpus_vector_identity"
        ),
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
    }


#: ``(report key, release column)`` for the proof identities a published release
#: records in both places. The report's own hash is deliberately absent: a
#: document cannot contain its own digest.
#:
#: One list, read two ways. :func:`recorded_identities` uses it to lift the
#: values off a ``rp_corpus_releases`` row; the publication gate, which holds
#: in-memory models that spread the same five values across a
#: :class:`ReleaseIdentity` and a :class:`ReleaseRecord`, states them directly.
#: The *comparison* and the key set stay here either way.
REPORT_PROOF_COLUMNS = (
    ("authoritative_source_hash", "authoritative_source_hash"),
    ("transform_config_hash", "transform_config_hash"),
    ("bundle_root_hash", "bundle_root_hash"),
    ("frozen_source_ledger_hash", "ledger_hash"),
    ("persisted_corpus_digest", "persisted_corpus_digest"),
)


def recorded_identities(release: object) -> dict[str, object]:
    """The five proof identities as a persisted release row records them."""
    return {key: getattr(release, column) for key, column in REPORT_PROOF_COLUMNS}


def report_state_violations(
    report: CorpusEvidenceReport,
    *,
    identities: Mapping[str, object],
    transform_config: dict[str, object],
    ledger: SourceLedger,
    reconciliation: ReconciliationMember,
    policy: ReconciliationPolicy,
) -> tuple[str, ...]:
    """Does this report describe *this* persisted corpus?

    The single definition of report-versus-state agreement, shared by the
    published-authority seam and the publication gate. Parsing proves a report
    is well-formed and self-consistent; hashing proves it has not been edited
    since it was recorded. Neither asks whether its summaries are true of the
    rows beside it — so a report whose ``declared_projection_count``, totals, and
    accounting are rewritten to different but internally successful values,
    rehashed, and re-referenced was accepted as published authority.

    Every SQL-reconstructable claim is recomputed through
    :func:`state_derived_fields` and compared, alongside the five proof
    identities against their release columns. Comparison is over canonical
    bytes, because the same logical value arrives as tuples in memory and lists
    out of a JSON column.

    Deliberately silent about the three claims SQL cannot recompute —
    concordance, canary execution, and the live vector half of the
    persisted-corpus digest. Those keep their recorded-successful-form treatment
    under the 2026-08-01 Owner Decision, and are re-run for real by the paths
    that hold pages and vector state.

    ``identities`` maps report key to the value the release records for it —
    :func:`recorded_identities` builds it from a persisted row.
    """
    violations: list[str] = []
    recorded = report.dump()
    expected = state_derived_fields(
        ledger=ledger,
        recon=reconciliation,
        policy=policy,
        transform_config=transform_config,
    )
    for key, want in sorted(expected.items()):
        if canonical_bytes(recorded[key]) != canonical_bytes(want):
            violations.append(
                f"recorded evidence report states {key}={recorded[key]!r}, the "
                f"reconstructed 5c state derives {want!r}"
            )
    for key, declared in sorted(identities.items()):
        if recorded[key] != declared:
            violations.append(
                f"recorded evidence report states {key}={recorded[key]!r}, the "
                f"release records {declared!r}"
            )
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
) -> CorpusEvidenceReport:
    """Build the evidence report after persistence (K step e).

    Returns the canonical document itself. There is no completed-report wrapper:
    one existed, holding the payload beside a caller-supplied ``persisted``
    flag, and it was the hash-bearing authority every consumer actually read —
    so ``object.__setattr__(report, "payload", forged)`` replaced the whole
    document after construction while the tuple tree inside stayed immutable.

    That the report postdates persistence is now structural rather than
    declared. ``persisted_corpus_digest`` is a required argument, and gate
    condition 17 *recomputes* it over the reconstructed SQL rows and the actual
    read-back vector state — so a value invented before persistence fails there
    rather than being taken on trust (a caller can pass any string here; what it
    cannot do is pass one that survives the gate). :class:`ReleaseArtifacts` —
    the only thing ``run_gate`` accepts — is constructed in exactly two places,
    both in :mod:`persistence`, and both hold reconstructed state.
    """
    fields: dict[str, object] = {
        # Canonical schema version, also bound into the transform identity so a
        # schema change remints the release rather than being reused (R17).
        "report_version": EVIDENCE_REPORT_SCHEMA_VERSION,
        # Proof hashes (NOT this report's own hash).
        "authoritative_source_hash": authoritative_source_hash,
        "transform_config_hash": transform_config_hash,
        "bundle_root_hash": bundle_root_hash,
        "frozen_source_ledger_hash": ledger_hash_value,
        "persisted_corpus_digest": persisted_corpus_digest,
        # The *declared* environment needed to reproduce the transform (Component
        # B): the Python target here, plus the exact pinned extractor/parser/tool
        # versions and deterministic invocation already carried by
        # ``transform_identity`` below. This is host-independent by construction —
        # no runtime host name, OS, architecture, absolute path, timestamp, or PID
        # enters this identity-bearing payload, so the same committed inputs yield a
        # byte-identical evidence report (hence release identity) on every supported
        # host (PR #134 R16). Actual host diagnostics are logged, never hashed.
        "reproduction_target": {"python_target": PYTHON_TARGET},
        **state_derived_fields(
            ledger=ledger, recon=recon, policy=policy, transform_config=transform_config
        ),
        # The three claims SQL alone cannot recompute: concordance is measured
        # against the authoritative PDF and canaries are executed against its
        # pages, so both are recorded evidence rather than reconstructable state
        # (Owner Decision 2026-08-01).
        "invalid_locators": len(concordance.locator_failures),
        "concordance_failures": len(concordance.content_failures),
        "version_canaries": {c.name: c.passed for c in canaries},
    }

    # The verdict is read off the assembled document through the same method a
    # stored report is measured by, so a report claiming "pass" over
    # contradictory summaries cannot be produced here — and an incomplete canary
    # run, an unsupported schema version, or a non-canonical reproduction target
    # is refused by the parser before the question is even asked.
    provisional = canonical_report(
        {**fields, "prepublication_validation_status": "fail"}
    )
    status = "fail" if provisional.verdict_violations() else "pass"

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
    return canonical_report({**fields, "prepublication_validation_status": status})


def recorded_success_violations(payload: object) -> tuple[str, ...]:
    """Is a *recorded* report a well-formed, successful 5c verdict?

    Parse first, then judge. Shape, closed populations, and value domains belong
    to the typed document; this adds only the verdict question, on something that
    has already proven it is this schema.

    Deliberately bounded to what the report contains. It reconstructs no history
    and does not reopen the vector store (Owner Decision 2026-08-01); agreement
    with the release row and with reconstructed 5c state is proven contextually
    by :func:`persistence.verify_published_release`.
    """
    parsed, violations = parse_recorded_report(payload)
    if parsed is None:
        return violations
    return parsed.success_violations()


def report_hash(report: CorpusEvidenceReport) -> str:
    """Hash the completed evidence report (K step f).

    Over the canonical dump of the document itself — the same bytes SQL
    persists, so a stored report always rehashes to the value recorded beside
    it. Takes the canonical value rather than a container holding one: there is
    no other report type to pass, which is why nothing here checks for one.
    """
    return hash_obj(report.dump())
