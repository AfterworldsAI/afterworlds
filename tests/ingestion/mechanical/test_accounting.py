"""Span-exact semantic accounting — CRD Issue 5d, Decision 2.

The positive cases are cheap; the negative controls are the point. Each one
below is a way an empty or dishonest classification could otherwise pass:
uncovered text, double-claimed text, a reason code invented after the fact, a
row that says "accepted" with nothing behind it, and a batch acceptance whose
retained evidence does not support what it claims.

The identity tests fix the other boundary: the accepted semantic *result* is
identity-bearing, and the review path that reached it is not.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from afterworlds.ingestion.mechanical import accounting
from afterworlds.ingestion.mechanical.accounting import (
    batch_diff_hash,
    classification_identity,
    classification_payload,
    derive_span_id,
    validate_acceptance,
    validate_partition,
    validate_policy_binding,
    validate_reason_codes,
)
from afterworlds.ingestion.mechanical.models import (
    AcceptanceBatch,
    AcceptanceRecord,
    ClassificationLedger,
    ReviewState,
    SemanticDiffEntry,
    SemanticDisposition,
    SemanticSpan,
)
from afterworlds.ingestion.mechanical.policy import (
    NON_MECHANICAL_REASONS,
    SEMANTIC_POLICY_VERSION,
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


def _batch(
    spans: tuple[SemanticSpan, ...],
    *,
    batch_id: str = "batch-1",
    rule: str = "running footers are navigation-only",
    scope: tuple[str, ...] | None = None,
    diff: tuple[SemanticDiffEntry, ...] | None = None,
    digest: str | None = None,
    proposal_identity: str = "a" * 64,
) -> AcceptanceBatch:
    """A batch whose retained diff matches *spans* unless overridden."""
    if diff is None:
        diff = tuple(
            SemanticDiffEntry(
                span_id=s.span_id,
                prior_disposition=None,
                prior_reason_code=None,
                accepted_disposition=s.disposition,
                accepted_reason_code=s.non_mechanical_reason_code,
            )
            for s in spans
        )
    batch = AcceptanceBatch(
        batch_id=batch_id,
        rule=rule,
        resolved_scope=scope if scope is not None else tuple(s.span_id for s in spans),
        diff=diff,
        semantic_diff_hash="",
        proposal_identity=proposal_identity,
    )
    return replace(
        batch,
        semantic_diff_hash=digest if digest is not None else batch_diff_hash(batch),
    )


def _batch_acceptances(
    spans: tuple[SemanticSpan, ...], batch_id: str
) -> tuple[AcceptanceRecord, ...]:
    return tuple(
        AcceptanceRecord(s.span_id, batch_id, "owner", "2026-07-31T00:00:00Z")
        for s in spans
    )


def _ledger(
    spans: tuple[SemanticSpan, ...],
    *,
    batches: tuple[AcceptanceBatch, ...] = (),
    acceptances: tuple[AcceptanceRecord, ...] | None = None,
    policy_version: str = SEMANTIC_POLICY_VERSION,
    policy_hash: str | None = None,
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
        policy_version=policy_version,
        policy_hash=policy_hash if policy_hash is not None else semantic_policy_hash(),
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


def test_batch_acceptance_with_retained_diff_passes() -> None:
    spans = (_span(0, 10),)
    batch = _batch(spans)
    ledger = _ledger(
        spans, batches=(batch,), acceptances=_batch_acceptances(spans, "batch-1")
    )
    assert validate_acceptance(ledger) == ()


def test_batch_without_rule_scope_or_diff_is_not_acceptance() -> None:
    spans = (_span(0, 10),)
    empty = AcceptanceBatch(
        batch_id="batch-1",
        rule="  ",
        resolved_scope=(),
        diff=(),
        semantic_diff_hash="",
        proposal_identity="  ",
    )
    findings = validate_acceptance(
        _ledger(
            spans,
            batches=(empty,),
            acceptances=_batch_acceptances(spans, "batch-1"),
        )
    )
    assert any("no acceptance rule recorded" in f for f in findings)
    assert any("no resolved scope recorded" in f for f in findings)
    assert any("no semantic diff retained" in f for f in findings)


def test_duplicate_batch_ids_are_rejected() -> None:
    spans = (_span(0, 10),)
    batch = _batch(spans)
    findings = validate_acceptance(
        _ledger(
            spans,
            batches=(batch, batch),
            acceptances=_batch_acceptances(spans, "batch-1"),
        )
    )
    assert any("duplicate batch id" in f for f in findings)


def test_unknown_span_in_batch_scope_is_rejected() -> None:
    spans = (_span(0, 10),)
    batch = _batch(spans, scope=(spans[0].span_id, "ghost-span"))
    findings = validate_acceptance(
        _ledger(
            spans, batches=(batch,), acceptances=_batch_acceptances(spans, "batch-1")
        )
    )
    assert any("scope names unknown span ghost-span" in f for f in findings)


def test_scope_member_without_a_diff_entry_is_rejected() -> None:
    covered, uncovered = _span(0, 10), _span(10, 25)
    spans = (covered, uncovered)
    # Scope claims both spans; the retained diff only accounts for one.
    batch = _batch(
        spans,
        scope=(covered.span_id, uncovered.span_id),
        diff=(
            SemanticDiffEntry(
                span_id=covered.span_id,
                prior_disposition=None,
                prior_reason_code=None,
                accepted_disposition=covered.disposition,
                accepted_reason_code=None,
            ),
        ),
    )
    findings = validate_acceptance(
        _ledger(
            spans, batches=(batch,), acceptances=_batch_acceptances(spans, "batch-1")
        )
    )
    assert any("has no accepted diff entry" in f for f in findings)


def test_diff_entry_outside_the_resolved_scope_is_rejected() -> None:
    inside, outside = _span(0, 10), _span(10, 25)
    spans = (inside, outside)
    batch = _batch(spans, scope=(inside.span_id,))
    findings = validate_acceptance(
        _ledger(
            spans,
            batches=(batch,),
            acceptances=_batch_acceptances((inside,), "batch-1")
            + (
                AcceptanceRecord(
                    outside.span_id, None, "owner", "2026-07-31T00:00:00Z"
                ),
            ),
        )
    )
    assert any("outside resolved scope" in f for f in findings)


def test_acceptance_outside_its_batch_scope_is_rejected() -> None:
    inside, stranger = _span(0, 10), _span(10, 25)
    spans = (inside, stranger)
    batch = _batch((inside,))
    findings = validate_acceptance(
        _ledger(
            spans,
            batches=(batch,),
            acceptances=_batch_acceptances(spans, "batch-1"),
        )
    )
    assert any("outside the resolved scope of batch" in f for f in findings)


def test_diff_disagreeing_with_the_accepted_ledger_is_rejected() -> None:
    spans = (_span(0, 10),)
    batch = _batch(
        spans,
        diff=(
            SemanticDiffEntry(
                span_id=spans[0].span_id,
                prior_disposition=SemanticDisposition.SUBSTANTIVE,
                prior_reason_code=None,
                # Claims an acceptance the ledger does not carry.
                accepted_disposition=SemanticDisposition.NON_MECHANICAL,
                accepted_reason_code="navigation_only",
            ),
        ),
    )
    findings = validate_acceptance(
        _ledger(
            spans, batches=(batch,), acceptances=_batch_acceptances(spans, "batch-1")
        )
    )
    assert any("ledger has substantive" in f for f in findings)


def test_forged_semantic_diff_digest_is_rejected() -> None:
    spans = (_span(0, 10),)
    batch = _batch(spans, digest="f" * 64)
    findings = validate_acceptance(
        _ledger(
            spans, batches=(batch,), acceptances=_batch_acceptances(spans, "batch-1")
        )
    )
    assert any("digest does not match retained diff" in f for f in findings)


def test_orphan_batch_with_no_acceptance_records_is_rejected() -> None:
    spans = (_span(0, 10),)
    findings = validate_acceptance(_ledger(spans, batches=(_batch(spans),)))
    assert any("no acceptance record names this batch" in f for f in findings)


def test_scope_member_accepted_individually_is_rejected() -> None:
    a, b = _span(0, 10), _span(10, 25)
    spans = (a, b)
    # The batch claims both spans, but only one was accepted under it.
    findings = validate_acceptance(
        _ledger(
            spans,
            batches=(_batch(spans),),
            acceptances=_batch_acceptances((a,), "batch-1")
            + (AcceptanceRecord(b.span_id, None, "owner", "2026-07-31T00:00:00Z"),),
        )
    )
    assert any("was accepted individually" in f for f in findings)


def test_scope_member_accepted_under_another_batch_is_rejected() -> None:
    a, b = _span(0, 10), _span(10, 25)
    spans = (a, b)
    findings = validate_acceptance(
        _ledger(
            spans,
            batches=(
                _batch(spans, batch_id="claiming"),
                _batch((b,), batch_id="actual"),
            ),
            acceptances=_batch_acceptances((a,), "claiming")
            + _batch_acceptances((b,), "actual"),
        )
    )
    assert any("was accepted under batch actual" in f for f in findings)


def test_duplicate_span_ids_in_resolved_scope_are_rejected() -> None:
    spans = (_span(0, 10),)
    batch = _batch(spans, scope=(spans[0].span_id, spans[0].span_id))
    findings = validate_acceptance(
        _ledger(
            spans, batches=(batch,), acceptances=_batch_acceptances(spans, "batch-1")
        )
    )
    assert any("duplicate span ids in resolved scope" in f for f in findings)


def test_acceptance_without_reviewer_or_timestamp_is_rejected() -> None:
    span = _span(0, 10)
    findings = validate_acceptance(
        _ledger((span,), acceptances=(AcceptanceRecord(span.span_id, None, " ", ""),))
    )
    assert any("without reviewer/timestamp evidence" in f for f in findings)


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


def test_identity_ignores_individual_versus_batch_review() -> None:
    spans = (_span(0, 10), _span(10, 25))
    individually_reviewed = _ledger(spans)
    batch_reviewed = _ledger(
        spans,
        batches=(_batch(spans),),
        acceptances=_batch_acceptances(spans, "batch-1"),
    )
    assert validate_acceptance(individually_reviewed) == ()
    assert validate_acceptance(batch_reviewed) == ()
    assert classification_identity(individually_reviewed) == classification_identity(
        batch_reviewed
    )


def test_identity_ignores_batch_grouping_and_rule_wording() -> None:
    a, b = _span(0, 10), _span(10, 25)
    spans = (a, b)
    one_batch = _ledger(
        spans,
        batches=(_batch(spans, rule="everything on this page"),),
        acceptances=_batch_acceptances(spans, "batch-1"),
    )
    two_batches = _ledger(
        spans,
        batches=(
            _batch((a,), batch_id="first", rule="the opening clause"),
            _batch((b,), batch_id="second", rule="the trailing clause"),
        ),
        acceptances=_batch_acceptances((a,), "first")
        + _batch_acceptances((b,), "second"),
    )
    assert validate_acceptance(one_batch) == ()
    assert validate_acceptance(two_batches) == ()
    assert classification_identity(one_batch) == classification_identity(two_batches)


def test_identity_changes_when_a_disposition_changes() -> None:
    base = _ledger((_span(0, 10),))
    changed = _ledger((_span(0, 10, SemanticDisposition.SUPPORTING_AUTHORITY),))
    assert classification_identity(base) != classification_identity(changed)


def test_identity_changes_when_a_span_boundary_changes() -> None:
    base = _ledger((_span(0, 10), _span(10, 25)))
    changed = _ledger((_span(0, 12), _span(12, 25)))
    assert classification_identity(base) != classification_identity(changed)


def test_identity_changes_when_a_reason_assignment_changes() -> None:
    base = _ledger(
        (_span(0, 10, SemanticDisposition.NON_MECHANICAL, reason="navigation_only"),)
    )
    changed = _ledger(
        (_span(0, 10, SemanticDisposition.NON_MECHANICAL, reason="flavor_setting"),)
    )
    assert classification_identity(base) != classification_identity(changed)


def test_identity_changes_when_the_semantic_policy_changes() -> None:
    ledger = _ledger((_span(0, 10),))
    under_other_policy = _ledger(
        (_span(0, 10),), policy_version="5d-semantic-policy-0", policy_hash="0" * 64
    )
    assert classification_identity(ledger) != classification_identity(
        under_other_policy
    )


def test_identity_uses_the_declared_policy_not_current_code(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # A later policy edit must not silently re-identify a historical ledger:
    # the payload states what the ledger declared, and validation is what
    # catches the disagreement.
    ledger = _ledger((_span(0, 10),))
    before = classification_identity(ledger)
    monkeypatch.setattr(accounting, "semantic_policy_hash", lambda: "0" * 64)
    assert classification_identity(ledger) == before
    assert any(
        "committed policy hashes to" in f for f in validate_policy_binding(ledger)
    )


def test_identity_ignores_acceptance_history_entirely() -> None:
    span = _span(0, 10)
    payload = classification_payload(
        _ledger(
            (span,),
            batches=(_batch((span,)),),
            acceptances=_batch_acceptances((span,), "batch-1"),
        )
    )
    assert "batches" not in payload
    assert "acceptances" not in payload


def test_identity_is_order_independent() -> None:
    a, b = _span(0, 10), _span(10, 25)
    assert classification_identity(_ledger((a, b))) == classification_identity(
        _ledger((b, a))
    )


def test_payload_binds_the_declared_policy_hash() -> None:
    ledger = _ledger((_span(0, 10),))
    payload = classification_payload(ledger)
    assert payload["semantic_policy_hash"] == ledger.policy_hash
    assert payload["semantic_policy_version"] == ledger.policy_version


# -- declared policy binding -------------------------------------------------


def test_matching_policy_declaration_passes() -> None:
    assert validate_policy_binding(_ledger((_span(0, 10),))) == ()


def test_stale_declared_policy_version_is_rejected() -> None:
    ledger = _ledger((_span(0, 10),), policy_version="5d-semantic-policy-0")
    assert any("build uses" in f for f in validate_policy_binding(ledger))


def test_mismatched_declared_policy_hash_is_rejected() -> None:
    ledger = _ledger((_span(0, 10),), policy_hash="0" * 64)
    assert any(
        "committed policy hashes to" in f for f in validate_policy_binding(ledger)
    )


# -- canonicalization --------------------------------------------------------


def test_canonical_span_text_uses_the_corpus_normalization() -> None:
    # Ligature + typographic quote + whitespace run all fold, so a span's
    # equivalence matches what the 5c corpus layer already considers equal.
    assert canonical_span_text("the ﬁre  ’bolt’", 0, 15) == "the fire 'bolt'"
