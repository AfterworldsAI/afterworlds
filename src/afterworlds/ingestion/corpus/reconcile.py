"""Deterministic reconciliation — CRD Issue 5c, Component D (K step a3).

Generated from the frozen ledger and the canonical corpus output by applying
**only** the frozen reconciliation policy. The reconciler may not invent
exclusion categories, reason codes, projection roles, or overlap permissions —
it applies the committed policy and records the exact policy identity/version/
hash it used and the result.

It owns each leaf's single final disposition, its policy-approved exclusion
reason where excluded, the declared-projection edges (leaf → chunk under a
policy role, with covered subspans), and the gap/overlap/orphan/duplication/
unresolved findings. The accounting equation ranges over atomic leaves only:

    inventoried atomic leaves
        = represented leaves + excluded (policy-approved) leaves + unresolved

The findings computation is a pure function (:func:`compute_findings`) so the
gate's adversarial cases — partial coverage → gap, unauthorized overlap,
orphan output, relabeled duplicate — can be exercised directly.
"""

from __future__ import annotations

from afterworlds.ingestion.corpus.hashing import content_id
from afterworlds.ingestion.corpus.models import (
    CorpusBundleMembers,
    CorpusChunk,
    Disposition,
    Leaf,
    LeafDisposition,
    ProjectionEdge,
    ReconciliationFindings,
    ReconciliationMember,
    ReconciliationPolicy,
    SourceLedger,
)
from afterworlds.ingestion.corpus.policy import (
    AUTHORITATIVE_ROLE,
    exclusion_reason_for,
    normalize,
    policy_hash,
)


def _full_coverage_edges(
    chunks: tuple[CorpusChunk, ...], leaves_by_id: dict[str, Leaf]
) -> tuple[ProjectionEdge, ...]:
    """Build declared-projection edges from the corpus output (real path).

    Each chunk fully covers each of its source leaves (transform contract). The
    covered subspan is the leaf's whole content; the projection id is content-
    derived so a duplicate edge is a duplicate identity.
    """
    edges: list[ProjectionEdge] = []
    for chunk in chunks:
        for leaf_id in chunk.source_leaf_ids:
            leaf = leaves_by_id.get(leaf_id)
            cover_end = len(leaf.content) if leaf is not None else 0
            edges.append(
                ProjectionEdge(
                    projection_id=content_id(
                        "projection", leaf_id, chunk.chunk_id, AUTHORITATIVE_ROLE
                    ),
                    leaf_id=leaf_id,
                    chunk_id=chunk.chunk_id,
                    role=AUTHORITATIVE_ROLE,
                    cover_start=0,
                    cover_end=cover_end,
                )
            )
    return tuple(edges)


def compute_findings(
    leaves_by_id: dict[str, Leaf],
    edges: tuple[ProjectionEdge, ...],
    chunks: tuple[CorpusChunk, ...],
    policy: ReconciliationPolicy,
    represented: set[str],
) -> ReconciliationFindings:
    """Pure identity-level findings computation (Component D).

    * gap — a represented leaf whose edge subspans do not cover its whole span.
    * overlap — a leaf whose edges overlap on a subspan under a role that does
      not authorize overlap.
    * orphan — a chunk with no leaf link.
    * duplication — a duplicate projection identity, or two policy-equivalent
      chunks covering the same leaf subspan without a distinct overlap role.
    """
    gaps: list[str] = []
    overlaps: list[str] = []
    orphans: list[str] = []
    duplications: list[str] = []

    role_allows_overlap = {r.name: r.allows_overlap for r in policy.projection_roles}

    # Orphans: a chunk that links to no (existing) leaf.
    for chunk in chunks:
        linked = [lid for lid in chunk.source_leaf_ids if lid in leaves_by_id]
        if not linked:
            orphans.append(chunk.chunk_id)

    # Duplicate projection identities.
    seen_proj: set[str] = set()
    for edge in edges:
        if edge.projection_id in seen_proj:
            duplications.append(edge.projection_id)
        seen_proj.add(edge.projection_id)

    # Per-leaf coverage, overlap, and equivalent-duplicate checks.
    edges_by_leaf: dict[str, list[ProjectionEdge]] = {}
    for edge in edges:
        edges_by_leaf.setdefault(edge.leaf_id, []).append(edge)
    chunk_by_id = {c.chunk_id: c for c in chunks}

    for leaf_id in represented:
        leaf = leaves_by_id[leaf_id]
        span = len(leaf.content)
        leaf_edges = sorted(
            edges_by_leaf.get(leaf_id, []), key=lambda e: (e.cover_start, e.cover_end)
        )
        # Coverage union + overlap detection.
        covered_to = 0
        has_gap = False
        prev_end = 0
        for edge in leaf_edges:
            if edge.cover_start > covered_to:
                has_gap = True
            # Overlapping subspan — only legal under an overlap-authorized role.
            if edge.cover_start < prev_end and not role_allows_overlap.get(
                edge.role, False
            ):
                overlaps.append(leaf_id)
            covered_to = max(covered_to, edge.cover_end)
            prev_end = max(prev_end, edge.cover_end)
        if covered_to < span:
            has_gap = True
        if has_gap:
            gaps.append(leaf_id)
        # Equivalent-duplicate outputs covering this leaf without a distinct role.
        eq_by_role: dict[tuple[str, str], int] = {}
        for edge in leaf_edges:
            edge_chunk = chunk_by_id.get(edge.chunk_id)
            if edge_chunk is None:
                continue
            key = (normalize(edge_chunk.content).casefold(), edge.role)
            eq_by_role[key] = eq_by_role.get(key, 0) + 1
        for (_, role), count in eq_by_role.items():
            if count > 1 and not role_allows_overlap.get(role, False):
                duplications.append(f"{leaf_id}:{role}")

    return ReconciliationFindings(
        gaps=tuple(dict.fromkeys(gaps)),
        overlaps=tuple(dict.fromkeys(overlaps)),
        orphans=tuple(dict.fromkeys(orphans)),
        duplications=tuple(dict.fromkeys(duplications)),
        unresolved=(),  # filled by reconcile() from dispositions
    )


def reconcile(
    ledger: SourceLedger,
    members: CorpusBundleMembers,
    policy: ReconciliationPolicy,
) -> ReconciliationMember:
    """Apply the frozen policy to the ledger and corpus output (K a3)."""
    leaves_by_id = {leaf.leaf_id: leaf for leaf in ledger.leaves}
    container_labels = {c.container_id: c.label for c in ledger.containers}
    edges = _full_coverage_edges(members.chunks, leaves_by_id)
    projected_leaf_ids = {e.leaf_id for e in edges}

    dispositions: list[LeafDisposition] = []
    represented: set[str] = set()
    unresolved: list[str] = []
    n_repr = n_excl = n_unres = 0

    for leaf in ledger.leaves:
        reason = exclusion_reason_for(leaf, container_labels)
        if leaf.leaf_id in projected_leaf_ids:
            # Represented. If it also matched an exclusion reason the transform
            # should have skipped it; represented wins only when no reason applies.
            if reason is not None:
                dispositions.append(
                    LeafDisposition(leaf.leaf_id, Disposition.UNRESOLVED, None)
                )
                unresolved.append(leaf.leaf_id)
                n_unres += 1
            else:
                dispositions.append(
                    LeafDisposition(leaf.leaf_id, Disposition.REPRESENTED, None)
                )
                represented.add(leaf.leaf_id)
                n_repr += 1
        elif reason is not None and leaf.leaf_type in reason.eligible_leaf_types:
            dispositions.append(
                LeafDisposition(leaf.leaf_id, Disposition.EXCLUDED, reason.code)
            )
            n_excl += 1
        else:
            # Neither represented nor validly excluded → unresolved.
            dispositions.append(
                LeafDisposition(leaf.leaf_id, Disposition.UNRESOLVED, None)
            )
            unresolved.append(leaf.leaf_id)
            n_unres += 1

    findings = compute_findings(
        leaves_by_id, edges, members.chunks, policy, represented
    )
    findings = ReconciliationFindings(
        gaps=findings.gaps,
        overlaps=findings.overlaps,
        orphans=findings.orphans,
        duplications=findings.duplications,
        unresolved=tuple(unresolved),
    )

    return ReconciliationMember(
        policy_version=policy.policy_version,
        policy_hash=policy_hash(policy),
        dispositions=tuple(dispositions),
        projections=edges,
        findings=findings,
        inventoried_leaves=len(ledger.leaves),
        represented_leaves=n_repr,
        excluded_leaves=n_excl,
        unresolved_leaves=n_unres,
    )
