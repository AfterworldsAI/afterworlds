"""Pure reconciliation-findings tests — Issue 5c, Component D.

Exercises :func:`compute_findings` directly with small synthetic inputs: gaps,
unauthorized overlap, orphans, duplicate projection identities, relabel-cannot-
legalize-duplicates, and the policy-authorized-overlap positive.
"""

from __future__ import annotations

from afterworlds.ingestion.corpus.hashing import content_id
from afterworlds.ingestion.corpus.models import (
    CorpusChunk,
    LeafType,
    ProjectionEdge,
)
from afterworlds.ingestion.corpus.policy import (
    ATTRIBUTION_ROLE,
    AUTHORITATIVE_ROLE,
    FROZEN_POLICY,
)
from afterworlds.ingestion.corpus.reconcile import compute_findings

from .conftest import make_leaf


def _chunk(content: str, leaf_ids: tuple[str, ...]) -> CorpusChunk:
    return CorpusChunk(
        chunk_id=content_id("chunk", content, leaf_ids),
        subsystem="general",
        content=content,
        printed_page=1,
        section_label=None,
        container_path=(),
        source_leaf_ids=leaf_ids,
    )


def _edge(
    leaf_id: str, chunk_id: str, role: str, start: int, end: int
) -> ProjectionEdge:
    return ProjectionEdge(
        projection_id=content_id("projection", leaf_id, chunk_id, role, start, end),
        leaf_id=leaf_id,
        chunk_id=chunk_id,
        role=role,
        cover_start=start,
        cover_end=end,
    )


def test_full_coverage_has_no_findings():
    leaf = make_leaf(1, LeafType.PARAGRAPH, "hello world", 0, 0)
    lbi = {leaf.leaf_id: leaf}
    chunk = _chunk("hello world", (leaf.leaf_id,))
    edges = (_edge(leaf.leaf_id, chunk.chunk_id, AUTHORITATIVE_ROLE, 0, 11),)
    findings = compute_findings(lbi, edges, (chunk,), FROZEN_POLICY, {leaf.leaf_id})
    assert not findings.gaps and not findings.overlaps
    assert not findings.orphans and not findings.duplications


def test_partial_coverage_is_a_gap():
    leaf = make_leaf(1, LeafType.PARAGRAPH, "hello world", 0, 0)
    lbi = {leaf.leaf_id: leaf}
    chunk = _chunk("hello", (leaf.leaf_id,))
    edges = (_edge(leaf.leaf_id, chunk.chunk_id, AUTHORITATIVE_ROLE, 0, 5),)
    findings = compute_findings(lbi, edges, (chunk,), FROZEN_POLICY, {leaf.leaf_id})
    assert leaf.leaf_id in findings.gaps


def test_unauthorized_overlap_is_flagged():
    leaf = make_leaf(1, LeafType.PARAGRAPH, "hello world", 0, 0)
    lbi = {leaf.leaf_id: leaf}
    c1 = _chunk("hello world", (leaf.leaf_id,))
    c2 = _chunk("hello there", (leaf.leaf_id,))
    edges = (
        _edge(leaf.leaf_id, c1.chunk_id, AUTHORITATIVE_ROLE, 0, 11),
        _edge(leaf.leaf_id, c2.chunk_id, AUTHORITATIVE_ROLE, 5, 11),
    )
    findings = compute_findings(lbi, edges, (c1, c2), FROZEN_POLICY, {leaf.leaf_id})
    assert leaf.leaf_id in findings.overlaps


def test_authorized_overlap_is_allowed():
    # Attribution content legitimately projected twice (two distinct output
    # records) under the overlap-authorized attribution_repeat role.
    leaf = make_leaf(1, LeafType.ATTRIBUTION, "attribution unit here", 0, 0)
    lbi = {leaf.leaf_id: leaf}
    c1 = _chunk("attribution record one", (leaf.leaf_id,))
    c2 = _chunk("attribution record two", (leaf.leaf_id,))
    edges = (
        _edge(leaf.leaf_id, c1.chunk_id, ATTRIBUTION_ROLE, 0, 21),
        _edge(leaf.leaf_id, c2.chunk_id, ATTRIBUTION_ROLE, 0, 21),
    )
    findings = compute_findings(lbi, edges, (c1, c2), FROZEN_POLICY, {leaf.leaf_id})
    # Overlap under the attribution_repeat role is authorized; no overlap finding.
    assert leaf.leaf_id not in findings.overlaps
    assert not findings.duplications


def test_orphan_chunk_with_no_leaf_link():
    leaf = make_leaf(1, LeafType.PARAGRAPH, "hello", 0, 0)
    lbi = {leaf.leaf_id: leaf}
    orphan = _chunk("stray", ("nonexistent-leaf",))
    findings = compute_findings(lbi, (), (orphan,), FROZEN_POLICY, set())
    assert orphan.chunk_id in findings.orphans


def test_duplicate_projection_identity_is_flagged():
    leaf = make_leaf(1, LeafType.PARAGRAPH, "hello world", 0, 0)
    lbi = {leaf.leaf_id: leaf}
    chunk = _chunk("hello world", (leaf.leaf_id,))
    edge = _edge(leaf.leaf_id, chunk.chunk_id, AUTHORITATIVE_ROLE, 0, 11)
    findings = compute_findings(
        lbi, (edge, edge), (chunk,), FROZEN_POLICY, {leaf.leaf_id}
    )
    assert edge.projection_id in findings.duplications


def test_relabel_cannot_legalize_equivalent_duplicate():
    # Two equivalent outputs covering the same leaf under the authoritative role
    # (no distinct policy role) are a duplicate; only casefold/whitespace differ.
    leaf = make_leaf(1, LeafType.PARAGRAPH, "hello world", 0, 0)
    lbi = {leaf.leaf_id: leaf}
    c1 = _chunk("hello world", (leaf.leaf_id,))
    c2 = _chunk("HELLO   world", (leaf.leaf_id,))
    edges = (
        _edge(leaf.leaf_id, c1.chunk_id, AUTHORITATIVE_ROLE, 0, 11),
        _edge(leaf.leaf_id, c2.chunk_id, AUTHORITATIVE_ROLE, 0, 11),
    )
    findings = compute_findings(lbi, edges, (c1, c2), FROZEN_POLICY, {leaf.leaf_id})
    assert any(leaf.leaf_id in d for d in findings.duplications)
