"""Publication gate — CRD Issue 5c, Component I (K step g).

Runs over the external release/publication record after the evidence report is
generated and hashed. It recomputes every proof identity from the supplied
artifacts and fails when any listed condition is absent or violated. Publication
proves corpus publication only — never adapter support (ADR-005c Decisions 1, 6).

The gate is a pure function of the artifacts (plus the independently supplied
legacy-reachability violation count), so each failure condition can be exercised
in isolation and the whole gate passes only when every condition holds.
"""

from __future__ import annotations

from afterworlds.ingestion.corpus.bundle import (
    build_bundle,
    persisted_corpus_digest,
    reconciliation_hash,
    transform_config_hash,
)
from afterworlds.ingestion.corpus.concordance import check_concordance
from afterworlds.ingestion.corpus.ledger import ledger_hash
from afterworlds.ingestion.corpus.models import (
    Disposition,
    GateResult,
    LeafType,
)
from afterworlds.ingestion.corpus.pdf_source import PDF_SHA256
from afterworlds.ingestion.corpus.pipeline import ReleaseArtifacts
from afterworlds.ingestion.corpus.policy import (
    ATTRIBUTION_ROLE,
    exclusion_reason_for,
    normalize,
    policy_hash,
)
from afterworlds.ingestion.corpus.report import report_hash


def run_gate(
    artifacts: ReleaseArtifacts,
    *,
    legacy_reachability_violations: int = 0,
    sql_persist_ok: bool = True,
    vector_write_ok: bool = True,
) -> GateResult:
    """Run the publication gate over the release record (Component I)."""
    a = artifacts
    f: list[str] = []
    policy = a.policy
    ledger = a.ledger
    recon = a.reconciliation
    rel = a.release
    ident = rel.identity

    leaves_by_id = {leaf.leaf_id: leaf for leaf in ledger.leaves}
    container_labels = {c.container_id: c.label for c in ledger.containers}

    # 1. Authoritative-source match.
    if ident.authoritative_source_hash != PDF_SHA256:
        f.append("authoritative_source_hash mismatch")

    # 2. Transform identity present + hash matches the committed config.
    if not rel.transform_config:
        f.append("transform identity missing")
    recomputed_thash = transform_config_hash(ledger.extraction_config, policy)
    if ident.transform_config_hash != recomputed_thash:
        f.append("transform_config_hash mismatch (config or policy substituted)")

    # 3. Policy committed/frozen before output: the applied policy hash must be
    #    the frozen policy hash, and it must be covered by the transform config.
    if recon.policy_hash != policy_hash(policy):
        f.append("reconciliation applied a policy other than the frozen policy")

    # 4. Complete frozen ledger + hash matches (no substituted ledger).
    if not ledger.leaves:
        f.append("frozen ledger is empty")
    if rel.ledger_hash != ledger_hash(ledger):
        f.append("frozen_source_ledger_hash mismatch (ledger substituted)")

    # 5. Reconciliation did not mutate the ledger: dispositions cover exactly the
    #    ledger's leaves (none added/deleted/resegmented/relabeled/relocated).
    disp_ids = [d.leaf_id for d in recon.dispositions]
    if len(disp_ids) != len(set(disp_ids)):
        f.append("duplicate leaf disposition (ledger mutated)")
    if set(disp_ids) != set(leaves_by_id):
        f.append("reconciliation mutated the frozen ledger (leaf set differs)")

    # 6/7. Only policy-defined reasons/roles; excluded reasons policy-approved and
    #      type-eligible.
    reason_codes = {r.code for r in policy.exclusion_reasons}
    role_names = {r.name for r in policy.projection_roles}
    for d in recon.dispositions:
        if d.disposition is Disposition.EXCLUDED:
            reason = policy.reason(d.exclusion_reason_code or "")
            leaf = leaves_by_id.get(d.leaf_id)
            if reason is None or d.exclusion_reason_code not in reason_codes:
                f.append(f"excluded leaf {d.leaf_id} uses unapproved reason")
            elif leaf is not None and leaf.leaf_type not in reason.eligible_leaf_types:
                f.append(f"excluded leaf {d.leaf_id} reason not type-eligible")
            # An exclusion the frozen policy would not itself assign is invalid.
            elif (
                leaf is not None
                and exclusion_reason_for(leaf, container_labels) is None
            ):
                f.append(f"excluded leaf {d.leaf_id} not excludable under policy")
    for edge in recon.projections:
        if edge.role not in role_names:
            f.append(f"projection {edge.projection_id} uses unknown role {edge.role}")

    # 8. Zero unresolved atomic leaves.
    if recon.unresolved_leaves != 0 or recon.findings.unresolved:
        f.append("nonzero unresolved leaves")
    if any(d.disposition is Disposition.UNRESOLVED for d in recon.dispositions):
        f.append("unresolved disposition present")

    # 9/10. No gaps, no unauthorized overlaps.
    if recon.findings.gaps:
        f.append("represented leaf with uncovered subspan (gap)")
    if recon.findings.overlaps:
        f.append("overlapping coverage without a policy-authorized role")

    # 11. Overlap role must be the attribution-repeat (overlap-authorized) role.
    overlap_ok_roles = {r.name for r in policy.projection_roles if r.allows_overlap}
    if overlap_ok_roles != {ATTRIBUTION_ROLE}:
        f.append("overlap-authorized role set changed from the frozen policy")

    # 12. Each chunk's declared coverage matches its normalized content.
    chunk_by_id = {c.chunk_id: c for c in a.members.chunks}
    cover: dict[str, list[str]] = {}
    for edge in recon.projections:
        leaf = leaves_by_id.get(edge.leaf_id)
        if leaf is not None:
            cover.setdefault(edge.chunk_id, []).append(
                leaf.content[edge.cover_start : edge.cover_end]
            )
    for chunk_id, parts in cover.items():
        chunk = chunk_by_id.get(chunk_id)
        if chunk is None:
            continue
        if normalize(" ".join(parts)) != normalize(chunk.content):
            f.append(f"chunk {chunk_id} declared coverage != normalized content")

    # 13/14. No duplicate projections, no orphans.
    if recon.findings.duplications:
        f.append("duplicate/equivalent projection")
    if recon.findings.orphans:
        f.append("orphan output record (no leaf link)")

    # 15. Concordance passes (re-run independently).
    if not check_concordance(a.members.chunks, a.pages).passed:
        f.append("concordance failed")
    if not all(c.passed for c in a.canaries):
        f.append("version canary failed")

    # 16. No substituted reconciliation / policy / report / bundle.
    if rel.reconciliation_hash != reconciliation_hash(recon):
        f.append("reconciliation_hash mismatch (reconciliation substituted)")
    if rel.policy_hash != policy_hash(policy):
        f.append("policy_hash mismatch (policy substituted)")
    if (
        ident.bundle_root_hash
        != build_bundle(ledger, a.members, recon).bundle_root_hash
    ):
        f.append("bundle_root_hash mismatch")
    if ident.evidence_report_hash != report_hash(a.report):
        f.append("evidence_report_hash mismatch (report substituted)")
    if rel.corpus_report_reference != ident.evidence_report_hash:
        f.append("corpus report reference != evidence report hash")

    # 17. Persisted-corpus digest matches (tamper detection).
    recomputed_digest = persisted_corpus_digest(
        rel.package_uuid, rel.release_version, ledger, a.members, recon, policy
    )
    if ident.persisted_corpus_digest != recomputed_digest:
        f.append("persisted_corpus_digest mismatch (tampered persisted state)")

    # 18. Evidence report postdates persistence and carries the digest.
    if not a.report.persisted:
        f.append("evidence report predates persistence")
    if not a.report.payload.get("persisted_corpus_digest"):
        f.append("evidence report lacks persisted-corpus digest")
    if a.report.payload.get("prepublication_validation_status") != "pass":
        f.append("evidence report prepublication status is not pass")

    # 19. Accounting equation holds.
    if recon.inventoried_leaves != (
        recon.represented_leaves + recon.excluded_leaves + recon.unresolved_leaves
    ):
        f.append("accounting equation does not balance")

    # 20. SQL/vector persistence succeeded.
    if not sql_persist_ok:
        f.append("SQL persistence incomplete")
    if not vector_write_ok:
        f.append("vector write incomplete")

    # 21. Five release-hash fields present.
    if not all(
        (
            ident.authoritative_source_hash,
            ident.transform_config_hash,
            ident.bundle_root_hash,
            ident.evidence_report_hash,
            ident.persisted_corpus_digest,
        )
    ):
        f.append("a top-level release hash is missing")

    # 22. Zero legacy-reachability violations (Owner Decision 1 / Component L).
    if legacy_reachability_violations != 0:
        f.append("legacy-reachability violation present")

    return GateResult(passed=not f, failures=tuple(f))


# Attribution leaves are the only overlap-eligible leaf type in the frozen
# policy; expose the check for tests that assert the policy's overlap surface.
def overlap_eligible_leaf_types() -> tuple[LeafType, ...]:
    return (LeafType.ATTRIBUTION,)
