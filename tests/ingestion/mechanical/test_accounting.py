"""Span-exact semantic accounting — CRD Issue 5d, Decision 2.

The positive cases are cheap; the negative controls are the point. Each one
below is a way an empty or dishonest classification could otherwise pass:
uncovered text, double-claimed text, a reason code invented after the fact, a
row that says "accepted" with nothing behind it, and a batch acceptance that
records no rule, scope, or diff.
"""

from __future__ import annotations

from afterworlds.ingestion.mechanical.accounting import (
    classification_identity,
    classification_payload,
    derive_span_id,
    validate_acceptance,
    validate_partition,
    validate_reason_codes,
)
from afterworlds.ingestion.mechanical.models import (
    AcceptanceBatch,
    AcceptanceRecord,
    ClassificationLedger,
    ReviewState,
    SemanticDisposition,
    SemanticSpan,
)
from afterworlds.ingestion.mechanical.policy import (
    NON_MECHANICAL_REASONS,
    canonical_span_text,
    semantic_policy_hash,
)

LEAF = "leaf-0001"


def _span(
    start: int,
    end: int,
    disposition: SemanticDisposition = SemanticDisposition.SUBSTANTIVE,
    *,
    leaf_id: str = LEAF,
    review_state: ReviewState = ReviewState.ACCEPTED,
    reason: str | None = None,
) -> SemanticSpan:
    return SemanticSpan(
        span_id=derive_span_id(leaf_id, start, end),
        leaf_id=leaf_id,
        char_start=start,
        char_end=end,
        disposition=disposition,
        review_state=review_state,
        non_mechanical_reason_code=reason,
    )


def _ledger(
    spans: tuple[SemanticSpan, ...],
    *,
    batches: tuple[AcceptanceBatch, ...] = (),
    acceptances: tuple[AcceptanceRecord, ...] | None = None,
) -> ClassificationLedger:
    if acceptances is None:
        acceptances = tuple(
            AcceptanceRecord(
                span_id=s.span_id,
                batch_id=None,
                reviewer="owner",
                accepted_at="2026-07-31T00:00:00Z",
            )
            for s in spans
        )
    return ClassificationLedger(
        package_uuid="pkg-1",
        release_version="rel-1",
        policy_version="5d-semantic-policy-1",
        spans=spans,
        batches=batches,
        acceptances=acceptances,
    )


# -- partition ---------------------------------------------------------------


def test_gap_free_partition_passes() -> None:
    spans = (_span(0, 10), _span(10, 25))
    assert validate_partition(LEAF, 25, spans) == ()


def test_uncovered_text_is_a_violation() -> None:
    findings = validate_partition(LEAF, 25, (_span(0, 10), _span(15, 25)))
    assert any("uncovered text [10,15)" in f for f in findings)


def test_trailing_uncovered_text_is_a_violation() -> None:
    findings = validate_partition(LEAF, 25, (_span(0, 10),))
    assert any("uncovered text [10,25)" in f for f in findings)


def test_overlapping_spans_are_a_violation() -> None:
    findings = validate_partition(LEAF, 25, (_span(0, 15), _span(10, 25)))
    assert any("overlapping span" in f for f in findings)


def test_leaf_without_spans_is_a_violation() -> None:
    assert validate_partition(LEAF, 25, ()) == (f"leaf {LEAF}: no semantic spans",)


def test_span_id_must_match_its_range() -> None:
    forged = SemanticSpan(
        span_id=derive_span_id(LEAF, 0, 5),  # id for a different range
        leaf_id=LEAF,
        char_start=0,
        char_end=25,
        disposition=SemanticDisposition.SUBSTANTIVE,
        review_state=ReviewState.ACCEPTED,
    )
    findings = validate_partition(LEAF, 25, (forged,))
    assert any("does not match its range" in f for f in findings)


def test_span_id_does_not_churn_when_a_sibling_is_inserted() -> None:
    before = _span(10, 25)
    after = _span(10, 25)  # same leaf + range, unrelated sibling added elsewhere
    assert before.span_id == after.span_id


# -- reason codes ------------------------------------------------------------


def test_non_mechanical_requires_a_closed_reason() -> None:
    findings = validate_reason_codes(
        (_span(0, 10, SemanticDisposition.NON_MECHANICAL),)
    )
    assert any("without reason" in f for f in findings)


def test_reason_invented_after_the_fact_is_rejected() -> None:
    findings = validate_reason_codes(
        (_span(0, 10, SemanticDisposition.NON_MECHANICAL, reason="looked_boring"),)
    )
    assert any("not in the closed catalog" in f for f in findings)


def test_closed_reason_passes() -> None:
    code = NON_MECHANICAL_REASONS[0].code
    assert (
        validate_reason_codes(
            (_span(0, 10, SemanticDisposition.NON_MECHANICAL, reason=code),)
        )
        == ()
    )


def test_reason_on_a_substantive_span_is_rejected() -> None:
    findings = validate_reason_codes((_span(0, 10, reason="legal_licensing"),))
    assert any("on a substantive span" in f for f in findings)


# -- acceptance --------------------------------------------------------------


def test_accepted_ledger_passes() -> None:
    assert validate_acceptance(_ledger((_span(0, 10),))) == ()


def test_span_without_acceptance_evidence_is_blocked() -> None:
    span = _span(0, 10)
    findings = validate_acceptance(_ledger((span,), acceptances=()))
    assert any("no acceptance record" in f for f in findings)


def test_proposed_span_is_blocked_even_with_an_acceptance_row() -> None:
    span = _span(0, 10, review_state=ReviewState.PROPOSED)
    findings = validate_acceptance(_ledger((span,)))
    assert any("review state proposed" in f for f in findings)


def test_unresolved_span_blocks_publication() -> None:
    findings = validate_acceptance(
        _ledger((_span(0, 10, SemanticDisposition.UNRESOLVED),))
    )
    assert any("unresolved classification" in f for f in findings)


def test_batch_acceptance_records_rule_scope_and_diff() -> None:
    span = _span(0, 10)
    batch = AcceptanceBatch(
        batch_id="batch-1",
        rule="running footers on every page are navigation-only",
        scope=("container:page-footer",),
        semantic_diff_hash="a" * 64,
    )
    ledger = _ledger(
        (span,),
        batches=(batch,),
        acceptances=(
            AcceptanceRecord(
                span_id=span.span_id,
                batch_id="batch-1",
                reviewer="owner",
                accepted_at="2026-07-31T00:00:00Z",
            ),
        ),
    )
    assert validate_acceptance(ledger) == ()


def test_batch_without_rule_scope_or_diff_is_not_acceptance() -> None:
    span = _span(0, 10)
    batch = AcceptanceBatch(
        batch_id="batch-1", rule="  ", scope=(), semantic_diff_hash=""
    )
    ledger = _ledger(
        (span,),
        batches=(batch,),
        acceptances=(
            AcceptanceRecord(
                span_id=span.span_id,
                batch_id="batch-1",
                reviewer="owner",
                accepted_at="2026-07-31T00:00:00Z",
            ),
        ),
    )
    findings = validate_acceptance(ledger)
    assert any("no acceptance rule recorded" in f for f in findings)
    assert any("no acceptance scope recorded" in f for f in findings)
    assert any("no semantic diff recorded" in f for f in findings)


def test_acceptance_naming_an_unknown_batch_is_rejected() -> None:
    span = _span(0, 10)
    ledger = _ledger(
        (span,),
        acceptances=(
            AcceptanceRecord(
                span_id=span.span_id,
                batch_id="ghost",
                reviewer="owner",
                accepted_at="2026-07-31T00:00:00Z",
            ),
        ),
    )
    assert any("unknown batch" in f for f in validate_acceptance(ledger))


# -- identity ----------------------------------------------------------------


def test_identity_ignores_reviewer_and_timestamp() -> None:
    span = _span(0, 10)
    first = _ledger(
        (span,),
        acceptances=(
            AcceptanceRecord(span.span_id, None, "alex", "2026-07-31T00:00:00Z"),
        ),
    )
    second = _ledger(
        (span,),
        acceptances=(
            AcceptanceRecord(span.span_id, None, "sam", "2026-08-02T12:34:56Z"),
        ),
    )
    assert classification_identity(first) == classification_identity(second)


def test_identity_changes_when_a_disposition_changes() -> None:
    base = _ledger((_span(0, 10),))
    changed = _ledger((_span(0, 10, SemanticDisposition.SUPPORTING_AUTHORITY),))
    assert classification_identity(base) != classification_identity(changed)


def test_identity_changes_when_a_batch_rule_changes() -> None:
    span = _span(0, 10)
    acceptances = (
        AcceptanceRecord(span.span_id, "b1", "owner", "2026-07-31T00:00:00Z"),
    )
    first = _ledger(
        (span,),
        batches=(AcceptanceBatch("b1", "rule A", ("s",), "a" * 64),),
        acceptances=acceptances,
    )
    second = _ledger(
        (span,),
        batches=(AcceptanceBatch("b1", "rule B", ("s",), "a" * 64),),
        acceptances=acceptances,
    )
    assert classification_identity(first) != classification_identity(second)


def test_identity_is_order_independent() -> None:
    a, b = _span(0, 10), _span(10, 25)
    assert classification_identity(_ledger((a, b))) == classification_identity(
        _ledger((b, a))
    )


def test_payload_binds_the_frozen_policy_hash() -> None:
    payload = classification_payload(_ledger((_span(0, 10),)))
    assert payload["semantic_policy_hash"] == semantic_policy_hash()


# -- canonicalization --------------------------------------------------------


def test_canonical_span_text_uses_the_corpus_normalization() -> None:
    # Ligature + typographic quote + whitespace run all fold, so a span's
    # equivalence matches what the 5c corpus layer already considers equal.
    assert canonical_span_text("the ﬁre  ’bolt’", 0, 15) == "the fire 'bolt'"
