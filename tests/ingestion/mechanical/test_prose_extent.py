"""Exact governing spans on prose bindings — CRD Issue 5d, #137 contract 3.

A prose-bound component resolves *its accepted governing span*, not the whole
passage that happens to contain it. The text still comes from the immutable 5c
``RuleChunk``; what narrows is which characters of that chunk this component
claims authority over.

The redundancy between the named span and the recorded chunk-relative offsets is
deliberate — runtime slices without re-reading the 5c projection relation — so
these tests exist to prove the build never lets that redundancy drift.
"""

from __future__ import annotations

from typing import Any

from afterworlds.ingestion.mechanical.accounting import derive_span_id
from afterworlds.ingestion.mechanical.models import (
    ClassificationLedger,
    ReviewState,
    SemanticDisposition,
    SemanticSpan,
)
from afterworlds.ingestion.mechanical.representation import (
    ProseBindingDraft,
    ProvenanceClaim,
    ProvenanceRole,
    ProvenanceTargetKind,
)
from afterworlds.ingestion.mechanical.validation import validate_representation
from tests.ingestion.mechanical.conftest import (
    PROSE_LEAF,
    PROSE_SPAN,
    SECOND_CHUNK,
    SPELL_KEY,
    SPELL_LEAF,
    SUPPORT_LEAF,
    WISH_CHUNK,
    binding_claim,
    bound_corpus,
    build_ledger,
    build_representation,
    coverage,
    prose_binding,
)


def _validate(
    binding: ProseBindingDraft,
    *,
    ledger: ClassificationLedger | None = None,
    extra_claims: tuple[ProvenanceClaim, ...] = (),
    **corpus_kwargs: Any,
) -> tuple[str, ...]:
    """Validate a candidate whose sole prose binding is *binding*."""
    base = build_representation()
    claims = tuple(c for c in base.provenance if c.target_kind.value != "prose_binding")
    draft = build_representation(
        prose_bindings=(binding,),
        provenance=claims + (binding_claim(binding, binding.span_id),) + extra_claims,
    )
    return validate_representation(
        draft, ledger or build_ledger(), bound_corpus(**corpus_kwargs)
    )


def _ledger_with(*prose_spans: SemanticSpan) -> ClassificationLedger:
    """The fixture ledger with the prose leaf's partition replaced."""
    kept = tuple(s for s in build_ledger().spans if s.leaf_id != PROSE_LEAF)
    return build_ledger(spans=kept + prose_spans)


def _record_context(span_id: str) -> ProvenanceClaim:
    return ProvenanceClaim(
        ProvenanceTargetKind.RECORD, (SPELL_KEY,), span_id, ProvenanceRole.CONTEXTUAL
    )


# -- the honest cases --------------------------------------------------------


def test_a_binding_whose_extent_matches_its_accepted_span_passes() -> None:
    assert _validate(prose_binding()) == ()


def test_a_binding_may_govern_a_subspan_of_its_chunk() -> None:
    """Half a leaf is a legitimate governing extent.

    This is the shape the feature exists for: one clause of a paragraph governs
    one component, and the neighbouring clause governs another or none.
    """
    clause = SemanticSpan(
        span_id=derive_span_id(PROSE_LEAF, 0, 12),
        leaf_id=PROSE_LEAF,
        char_start=0,
        char_end=12,
        disposition=SemanticDisposition.SUBSTANTIVE,
        review_state=ReviewState.ACCEPTED,
    )
    remainder = SemanticSpan(
        span_id=derive_span_id(PROSE_LEAF, 12, 30),
        leaf_id=PROSE_LEAF,
        char_start=12,
        char_end=30,
        disposition=SemanticDisposition.SUPPORTING_AUTHORITY,
        review_state=ReviewState.ACCEPTED,
    )
    findings = _validate(
        prose_binding(span_id=clause.span_id, chunk_char_start=0, chunk_char_end=12),
        ledger=_ledger_with(clause, remainder),
        # The other half of the leaf stays accounted for, as supporting
        # authority linked to the record it contextualizes.
        extra_claims=(_record_context(remainder.span_id),),
    )
    assert findings == ()


# -- the extent must be the span's, proved against the bound release ---------


def test_a_declared_extent_that_is_not_the_spans_extent_is_rejected() -> None:
    """Offsets are recomputed from the release, never trusted.

    A binding that names the whole clause but records offsets for half of it
    would resolve to half a sentence at runtime while every other check passed.
    """
    findings = _validate(prose_binding(chunk_char_end=17))
    assert any("is not the bound span's extent" in f for f in findings)


def test_a_binding_naming_an_unknown_span_is_rejected() -> None:
    findings = _validate(prose_binding(span_id="span:never-accepted"))
    assert any("unknown accepted span" in f for f in findings)


def test_a_binding_naming_a_span_of_another_leaf_is_rejected() -> None:
    """The chunk must actually contain the span it claims to govern."""
    findings = _validate(
        prose_binding(span_id=derive_span_id(SPELL_LEAF, 0, 40), chunk_char_end=40)
    )
    assert any("does not unambiguously contain span" in f for f in findings)


def test_a_binding_to_non_mechanical_text_is_rejected() -> None:
    """Governing prose resolves only to text the accounting found meaningful.

    Otherwise licensing or navigation text the classification deliberately set
    aside could return as a component's governing authority.
    """
    dismissed = SemanticSpan(
        span_id=PROSE_SPAN,
        leaf_id=PROSE_LEAF,
        char_start=0,
        char_end=30,
        disposition=SemanticDisposition.NON_MECHANICAL,
        review_state=ReviewState.ACCEPTED,
        non_mechanical_reason_code="legal_licensing",
    )
    findings = _validate(prose_binding(), ledger=_ledger_with(dismissed))
    assert any("governing prose resolves only to" in f for f in findings)


def test_a_chunk_spanning_two_leaves_cannot_supply_an_extent() -> None:
    """Fail closed where the coordinate mapping is genuinely unknown.

    A chunk assembled from several leaves has an unknown prefix before this
    leaf's text, so no offset can be derived. Guessing one would silently return
    the wrong sentence as governing authority.
    """
    findings = _validate(
        prose_binding(),
        chunk_coverage=(
            coverage(WISH_CHUNK, PROSE_LEAF, 0, 30),
            coverage(WISH_CHUNK, SUPPORT_LEAF, 0, 20),
            coverage(SECOND_CHUNK, PROSE_LEAF, 0, 30),
        ),
    )
    assert any("does not unambiguously contain span" in f for f in findings)
