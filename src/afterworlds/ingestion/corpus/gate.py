"""Publication gate — CRD Issue 5c, Component I (K step g).

Runs over the external release/publication record after the evidence report is
generated and hashed. It recomputes every proof identity from the supplied
artifacts and fails when any listed condition is absent or violated. Publication
proves corpus publication only — never adapter support (ADR-005c Decisions 1, 6).

The gate is a pure function of the artifacts (plus the independently supplied
publication evidence: SQL/vector persistence and chunk/source runtime membership),
so each failure condition can be exercised in isolation and the whole gate passes
only when every condition holds. (The pre-release clean baseline — Issue 5c Rev7 /
Issue 18 Rev6 — retired the strict legacy-reachability check that was here.)
"""

from __future__ import annotations

from dataclasses import dataclass

from afterworlds.ingestion.corpus.bundle import (
    build_bundle,
    persisted_corpus_digest,
    reconciliation_hash,
)
from afterworlds.ingestion.corpus.concordance import check_concordance
from afterworlds.ingestion.corpus.hashing import hash_obj
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
    policy_payload,
)
from afterworlds.ingestion.corpus.report import report_hash, report_state_violations


@dataclass(frozen=True)
class PublicationEvidence:
    """Real-operation evidence the release-capable gate requires (Component I).

    Every field must be supplied explicitly by the caller from an actual
    operation — there are **no defaults**, so no production caller can obtain a
    successful SQL/vector/membership verdict by omitting an argument or
    hard-coding ``True`` (PR #134 remediation, defect family 1). ``finalize_release``
    builds this from the real reindex/read-back/reconstruction results; gate
    unit tests construct it explicitly per scenario.
    """

    sql_persist_ok: bool
    vector_write_ok: bool
    chunk_membership_violations: int
    source_membership_violations: int
    vector_verification_failures: tuple[str, ...]


def run_gate(
    artifacts: ReleaseArtifacts,
    evidence: PublicationEvidence,
) -> GateResult:
    """Run the publication gate over the release record (Component I)."""
    a = artifacts
    chunk_membership_violations = evidence.chunk_membership_violations
    sql_persist_ok = evidence.sql_persist_ok
    vector_write_ok = evidence.vector_write_ok
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

    # 2. Transform identity present, complete, and internally consistent.
    #    Validated against the *complete recorded* transform configuration
    #    (extractor config + frozen policy + first-party source manifest), not by
    #    reconstructing the old partial identity from ledger.extraction_config +
    #    policy alone — an omitted source manifest (the pre-fix payload) or a
    #    recorded config whose stored hash no longer matches it is rejected here
    #    (PR #134 P1). The "code change → new identity" protection itself lives at
    #    build_candidate (manifest → transform hash → package_uuid → reuse miss);
    #    the gate proves the recorded hash was honestly derived from a complete
    #    recorded config and that config matches the reconstructed artifacts.
    tconfig = rel.transform_config
    ti = tconfig.get("transform_identity") if isinstance(tconfig, dict) else None
    if not tconfig or not isinstance(ti, dict) or not ti.get("transform_source_hash"):
        f.append("transform identity incomplete (no first-party source manifest)")
    elif ident.transform_config_hash != hash_obj(tconfig):
        f.append("transform_config_hash mismatch (recorded transform config tampered)")
    if isinstance(tconfig, dict):
        if tconfig.get("extraction_config") != ledger.extraction_config:
            f.append("recorded transform config extractor != reconstructed ledger")
        if tconfig.get("reconciliation_policy") != policy_payload(policy):
            f.append("recorded transform config policy != frozen policy")
        # Identity-bearing vector configuration is present and ties the recorded
        # embedding model to the ACTUAL persisted vector logical state — so a
        # model-only reindex cannot pass under an identity minted for a different
        # model (PR #134 P1). Contribution to package_uuid/version lives in the
        # transform hash; here the gate confirms recorded identity ↔ real store.
        vid = tconfig.get("rules_corpus_vector_identity")
        if not isinstance(vid, dict) or not vid.get("embedding_model_id"):
            f.append("rules-corpus vector identity missing from transform config")
        elif vid.get("embedding_model_id") != a.vector_state.get("embedding_model_id"):
            f.append(
                "recorded vector embedding_model_id != actual persisted vector state"
            )

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

    # 17. Persisted-corpus digest matches (tamper detection) — recomputed over
    #     the reconstructed SQL state **and the actual read-back vector logical
    #     state** carried on the artifacts, so a missing/stale/tampered Chroma
    #     collection (or a tampered SQL provenance field) fails here.
    recomputed_digest = persisted_corpus_digest(
        rel.package_uuid,
        rel.release_version,
        ledger,
        a.members,
        recon,
        policy,
        a.sources,
        a.vector_state,
    )
    if ident.persisted_corpus_digest != recomputed_digest:
        f.append("persisted_corpus_digest mismatch (tampered persisted state)")

    # 18. Evidence report postdates persistence and carries the digest.
    #     The former `if not a.report.persisted` check is gone: that flag lived
    #     on a wrapper outside the hashed payload and was set by the caller, so
    #     it asserted the ordering rather than proving it. The ordering is now
    #     structural — `persisted_corpus_digest` is a required argument to
    #     `build_report`, and condition 17 above recomputes it over the
    #     reconstructed SQL rows and the actual read-back vector state — so a
    #     digest invented before persistence fails there rather than being
    #     trusted here. `ReleaseArtifacts` is constructed in exactly two places,
    #     both in `persistence`, both from reconstructed state.
    if not a.report.persisted_corpus_digest:
        f.append("evidence report lacks persisted-corpus digest")
    if a.report.prepublication_validation_status != "pass":
        f.append("evidence report prepublication status is not pass")

    # 18b. The report describes THIS corpus, not merely a coherent one. Shared
    #      with the published-authority seam so there is one definition of
    #      report-versus-state agreement; the gate needs its own call because a
    #      fresh publication has no proven release to load yet.
    f.extend(
        report_state_violations(
            a.report,
            identities={
                "authoritative_source_hash": ident.authoritative_source_hash,
                "transform_config_hash": ident.transform_config_hash,
                "bundle_root_hash": ident.bundle_root_hash,
                "frozen_source_ledger_hash": rel.ledger_hash,
                "persisted_corpus_digest": ident.persisted_corpus_digest,
            },
            transform_config=tconfig if isinstance(tconfig, dict) else {},
            ledger=ledger,
            reconciliation=recon,
            policy=policy,
        )
    )

    # 19. Accounting equation holds.
    if recon.inventoried_leaves != (
        recon.represented_leaves + recon.excluded_leaves + recon.unresolved_leaves
    ):
        f.append("accounting equation does not balance")

    # 20. SQL/vector persistence succeeded — from real operation evidence, never
    #     a caller-hardcoded True (PR #134 defect family 1). A vector write
    #     failure or any read-back discrepancy (empty/missing/extra/stale
    #     document, metadata or embedding-model mismatch) blocks publication.
    if not sql_persist_ok:
        f.append("SQL persistence incomplete")
    if not vector_write_ok:
        f.append("vector write incomplete")
    for vf in evidence.vector_verification_failures:
        f.append(f"vector verification: {vf}")

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

    # 22. Persisted rp_chunks exactly matches the declared projection set, and
    #     every declared-projected chunk and its source are runtime-enabled —
    #     otherwise the digest/report can pass while runtime reads omit or add
    #     content (checked against the live DB by
    #     persistence.verify_chunk_runtime_membership; not recomputable from
    #     in-memory artifacts alone).
    if chunk_membership_violations != 0:
        f.append("persisted rp_chunks runtime-membership violation present")

    # 23. Single authoritative source, deterministic source_id == package_uuid,
    #     expected metadata + enabled, and every persisted chunk assigned to it
    #     (checked against the live DB by persistence.verify_single_source; not
    #     recomputable from in-memory artifacts alone). An extra/missing/altered/
    #     disabled/reassigned source fails closed (PR #134 defect family 3). The
    #     full ordered source set is *also* bound into the persisted-corpus digest
    #     (condition 17), so a silent metadata edit is caught even without this
    #     structural count.
    if evidence.source_membership_violations != 0:
        f.append("persisted source-membership invariant violation present")

    return GateResult(passed=not f, failures=tuple(f))


# Attribution leaves are the only overlap-eligible leaf type in the frozen
# policy; expose the check for tests that assert the policy's overlap surface.
def overlap_eligible_leaf_types() -> tuple[LeafType, ...]:
    return (LeafType.ATTRIBUTION,)
