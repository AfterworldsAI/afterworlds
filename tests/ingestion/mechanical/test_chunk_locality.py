"""Prose provenance is chunk-local — CRD Issue 5d, review round 4.

The round-3 correction closed provenance over element identity and span
admissibility, but not over the CRD Issue 5c projection relation. A prose
binding names an exact chunk and a provenance edge names an exact span; until
those two are joined, a binding to chunk A could cite a span that only ever
projected into chunk B and satisfy every check.

The join is possible because both coordinate systems are the same: 5c's
``cover_start``/``cover_end`` are offsets into the source leaf's content, and a
5d semantic span indexes that same text.
"""

from __future__ import annotations

import dataclasses

import pytest

from afterworlds.ingestion.mechanical.bound_corpus import BoundCorpusSnapshot
from afterworlds.ingestion.mechanical.representation import (
    ProseBindingDraft,
    ProvenanceRole,
)
from afterworlds.ingestion.mechanical.validation import validate_representation
from tests.ingestion.mechanical.conftest import (
    DEFAULT_COVERAGE,
    PROSE_LEAF,
    PROSE_SPAN,
    SECOND_CHUNK,
    SPELL_LEAF,
    WISH_CHUNK,
    binding_claim,
    bound_corpus,
    build_ledger,
    build_representation,
    coverage,
    prose_binding,
)

OTHER_CHUNK = "chunk-elsewhere"


def _findings(**overrides: object) -> tuple[str, ...]:
    corpus = overrides.pop("corpus", None)
    return validate_representation(
        build_representation(**overrides),
        build_ledger(),
        corpus if corpus is not None else bound_corpus(),  # type: ignore[arg-type]
    )


def _binding(chunk_id: str) -> ProseBindingDraft:
    return prose_binding(chunk_id)


def _with_binding(binding: ProseBindingDraft, **kwargs: object) -> tuple[str, ...]:
    """Findings for a candidate whose sole prose binding is *binding*."""
    claims = tuple(
        c
        for c in build_representation().provenance
        if c.target_kind.value != "prose_binding"
    ) + (binding_claim(binding),)
    return _findings(prose_bindings=(binding,), provenance=claims, **kwargs)


# -- negative controls -------------------------------------------------------


def test_span_projected_only_into_another_chunk_is_rejected() -> None:
    corpus = bound_corpus(chunk_coverage=(coverage(SECOND_CHUNK, PROSE_LEAF, 0, 30),))
    findings = _with_binding(_binding(WISH_CHUNK), corpus=corpus)
    assert any("is not covered by bound chunk" in f for f in findings)


def test_disjoint_chunks_on_one_leaf_cannot_borrow_each_others_range() -> None:
    # A covers [0,10); B covers [10,30). The binding to A claims B's range.
    corpus = bound_corpus(
        chunk_coverage=(
            coverage(WISH_CHUNK, PROSE_LEAF, 0, 10),
            coverage(SECOND_CHUNK, PROSE_LEAF, 10, 30),
        )
    )
    findings = _with_binding(_binding(WISH_CHUNK), corpus=corpus)
    assert any("is not covered by bound chunk" in f for f in findings)


def test_span_extending_beyond_the_chunk_range_is_rejected() -> None:
    corpus = bound_corpus(chunk_coverage=(coverage(WISH_CHUNK, PROSE_LEAF, 0, 20),))
    findings = _with_binding(_binding(WISH_CHUNK), corpus=corpus)
    assert any("is not covered by bound chunk" in f for f in findings)


def test_span_crossing_a_gap_between_two_ranges_is_rejected() -> None:
    corpus = bound_corpus(
        chunk_coverage=(
            coverage(WISH_CHUNK, PROSE_LEAF, 0, 10),
            coverage(WISH_CHUNK, PROSE_LEAF, 20, 30),
        )
    )
    findings = _with_binding(_binding(WISH_CHUNK), corpus=corpus)
    assert any("is not covered by bound chunk" in f for f in findings)


def test_coverage_on_the_wrong_leaf_is_rejected() -> None:
    corpus = bound_corpus(chunk_coverage=(coverage(WISH_CHUNK, SPELL_LEAF, 0, 40),))
    findings = _with_binding(_binding(WISH_CHUNK), corpus=corpus)
    assert any("is not covered by bound chunk" in f for f in findings)


def test_non_authoritative_chunk_is_rejected() -> None:
    findings = _with_binding(_binding(OTHER_CHUNK))
    assert any("is not authoritative prose of release" in f for f in findings)
    assert any("is not covered by bound chunk" in f for f in findings)


def test_cross_chunk_edge_cannot_satisfy_the_reverse_obligation() -> None:
    # The binding's only edge is the invalid one, so the reverse obligation
    # must remain unmet rather than being satisfied by a rejected claim.
    corpus = bound_corpus(chunk_coverage=(coverage(SECOND_CHUNK, PROSE_LEAF, 0, 30),))
    findings = _with_binding(_binding(WISH_CHUNK), corpus=corpus)
    assert any("prose_binding" in f and "no provenance" in f for f in findings)


def test_one_valid_edge_does_not_excuse_a_second_invalid_edge() -> None:
    # Chunk-locality is a property of every edge, not a box ticked once.
    binding = _binding(WISH_CHUNK)
    claims = build_representation().provenance + (
        binding_claim(binding, PROSE_SPAN, ProvenanceRole.CONTEXTUAL),
    )
    corpus = bound_corpus(chunk_coverage=(coverage(WISH_CHUNK, PROSE_LEAF, 0, 10),))
    findings = _findings(prose_bindings=(binding,), provenance=claims, corpus=corpus)
    assert any("is not covered by bound chunk" in f for f in findings)


@pytest.mark.parametrize("role", [ProvenanceRole.PRIMARY, ProvenanceRole.CONTEXTUAL])
def test_both_roles_obey_chunk_locality(role: ProvenanceRole) -> None:
    binding = _binding(WISH_CHUNK)
    claims = tuple(
        c
        for c in build_representation().provenance
        if c.target_kind.value != "prose_binding"
    ) + (
        binding_claim(binding, PROSE_SPAN, role),
    )
    corpus = bound_corpus(chunk_coverage=(coverage(SECOND_CHUNK, PROSE_LEAF, 0, 30),))
    findings = _findings(prose_bindings=(binding,), provenance=claims, corpus=corpus)
    assert any("is not covered by bound chunk" in f for f in findings)


# -- positive controls -------------------------------------------------------


def test_exact_range_equality_passes() -> None:
    corpus = bound_corpus(chunk_coverage=(coverage(WISH_CHUNK, PROSE_LEAF, 0, 30),))
    assert _with_binding(_binding(WISH_CHUNK), corpus=corpus) == ()


def test_span_inside_a_larger_range_passes() -> None:
    corpus = bound_corpus(chunk_coverage=(coverage(WISH_CHUNK, PROSE_LEAF, 0, 100),))
    assert _with_binding(_binding(WISH_CHUNK), corpus=corpus) == ()


def test_span_spanning_adjacent_ranges_of_one_chunk_passes() -> None:
    # Adjacency is continuity: [0,10) then [10,30) has no hole between them.
    corpus = bound_corpus(
        chunk_coverage=(
            coverage(WISH_CHUNK, PROSE_LEAF, 0, 10),
            coverage(WISH_CHUNK, PROSE_LEAF, 10, 30),
        )
    )
    assert _with_binding(_binding(WISH_CHUNK), corpus=corpus) == ()


def test_overlapping_ranges_of_one_chunk_merge() -> None:
    corpus = bound_corpus(
        chunk_coverage=(
            coverage(WISH_CHUNK, PROSE_LEAF, 0, 20),
            coverage(WISH_CHUNK, PROSE_LEAF, 15, 30),
        )
    )
    assert _with_binding(_binding(WISH_CHUNK), corpus=corpus) == ()


def test_two_chunks_may_legitimately_cover_the_same_range() -> None:
    # Each binding claims only what its own chunk covers; overlapping source
    # coverage between chunks is legal (5c's attribution-repeat role, and
    # ordinary shared ranges), and neither binding borrows the other's.
    first, second = _binding(WISH_CHUNK), _binding(SECOND_CHUNK)
    claims = build_representation().provenance + (
        binding_claim(second, PROSE_SPAN, ProvenanceRole.CONTEXTUAL),
    )
    assert _findings(prose_bindings=(first, second), provenance=claims) == ()


def test_attribution_role_coverage_still_establishes_containment() -> None:
    # Role is retained but does not decide containment: chunk membership does.
    # Whether attribution text may serve as governing prose is already decided
    # by the span's own disposition, which rejects non-mechanical text.
    corpus = bound_corpus(
        chunk_coverage=(
            coverage(WISH_CHUNK, PROSE_LEAF, 0, 30, role="attribution_repeat"),
        )
    )
    assert _with_binding(_binding(WISH_CHUNK), corpus=corpus) == ()


def test_the_default_honest_candidate_is_unaffected() -> None:
    assert _findings() == ()


# -- the coverage primitive itself -------------------------------------------


@pytest.mark.parametrize(
    ("start", "end", "expected"),
    [
        (0, 10, True),  # exact
        (2, 8, True),  # inside
        (0, 11, False),  # extends past
        (10, 20, False),  # outside
        (5, 5, False),  # empty span is never covered
    ],
)
def test_covers_span_boundaries(start: int, end: int, expected: bool) -> None:
    snapshot = bound_corpus(chunk_coverage=(coverage(WISH_CHUNK, PROSE_LEAF, 0, 10),))
    assert snapshot.covers_span(WISH_CHUNK, PROSE_LEAF, start, end) is expected


def test_membership_is_derived_from_coverage() -> None:
    snapshot = bound_corpus()
    assert snapshot.authoritative_chunk_ids == frozenset({WISH_CHUNK, SECOND_CHUNK})
    # A snapshot cannot claim a chunk is authoritative while carrying no
    # coverage for it: there is only one place the answer comes from.
    empty = bound_corpus(chunk_coverage=())
    assert empty.authoritative_chunk_ids == frozenset()
    assert not empty.covers_span(WISH_CHUNK, PROSE_LEAF, 0, 30)


def test_default_coverage_is_stated_per_chunk_and_leaf() -> None:
    # Guards the fixture itself: defaulting every chunk to every leaf would
    # make the cross-chunk negatives above vacuous.
    assert {(c.chunk_id, c.leaf_id) for c in DEFAULT_COVERAGE} == {
        (WISH_CHUNK, PROSE_LEAF),
        (SECOND_CHUNK, PROSE_LEAF),
    }


def test_snapshot_is_frozen() -> None:
    snapshot: BoundCorpusSnapshot = bound_corpus()
    with pytest.raises(dataclasses.FrozenInstanceError):
        snapshot.package_uuid = "other"  # type: ignore[misc]
