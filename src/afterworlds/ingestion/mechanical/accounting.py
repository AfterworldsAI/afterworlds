"""Span-exact semantic accounting — CRD Issue 5d, Decision 2.

Two things happen here and nowhere else:

* **partition validation** — every represented leaf's canonical text is covered
  gap-free and overlap-free by accepted spans, so no text is silently dropped
  and no text is claimed twice; and
* **acceptance validation** — every span carries explicit review acceptance,
  with batch acceptances required to record their rule, scope, and semantic
  diff.

Both return violation strings rather than raising, matching the CRD Issue 5c
``verify_*`` convention: a caller collects every violation in one pass instead
of discovering them one exception at a time, and the gate reports all of them.

Identity is derived from the accepted semantic *result* only — span boundaries,
dispositions, reason assignments, and the identity-bound semantic policy. The
acceptance *process* is not identity-bearing: individual versus batch review,
batch grouping, batch rule wording, resolved scope, reviewer, timestamp, and
acceptance history all stay out of the payload. Two ledgers that reviewed their
way to the same accepted classification are the same authority
(#137 acceptance criterion 11).

That is a boundary, not an exemption. Acceptance evidence is validated here as
strictly as the result — a batch retains the canonical diff it claims, not just
a digest of it — and it is retained for audit. If a batch rule should govern
future classification, it is promoted into the frozen semantic policy
explicitly, where it *is* identity-bearing, rather than leaking in through
acceptance history.
"""

from __future__ import annotations

from afterworlds.ingestion.corpus.hashing import content_id, hash_obj
from afterworlds.ingestion.mechanical.models import (
    AcceptanceBatch,
    ClassificationLedger,
    ReviewState,
    SemanticDisposition,
    SemanticSpan,
)
from afterworlds.ingestion.mechanical.policy import (
    SEMANTIC_POLICY_VERSION,
    non_mechanical_reason_for,
    semantic_policy_hash,
)

__all__ = [
    "batch_diff_hash",
    "batch_diff_payload",
    "classification_identity",
    "classification_payload",
    "derive_span_id",
    "validate_acceptance",
    "validate_partition",
    "validate_reason_codes",
]


def derive_span_id(leaf_id: str, char_start: int, char_end: int) -> str:
    """Content-derived identity for one leaf subspan.

    Derived from the leaf and its exact range, never from a position in a list,
    so inserting an unrelated span elsewhere cannot churn it.
    """
    return content_id("semantic_span", leaf_id, char_start, char_end)


def validate_partition(
    leaf_id: str, leaf_length: int, spans: tuple[SemanticSpan, ...]
) -> tuple[str, ...]:
    """Return violations of the gap-free, non-overlapping partition rule.

    *spans* are the spans claimed for ``leaf_id``; ``leaf_length`` is the length
    of that leaf's canonical text. A leaf with no spans is a violation, not an
    empty success — unclassified text is the failure this check exists for.
    """
    findings: list[str] = []
    mine = sorted(
        (s for s in spans if s.leaf_id == leaf_id),
        key=lambda s: (s.char_start, s.char_end),
    )

    if not mine:
        return (f"leaf {leaf_id}: no semantic spans",)

    cursor = 0
    for span in mine:
        if span.span_id != derive_span_id(span.leaf_id, span.char_start, span.char_end):
            findings.append(
                f"leaf {leaf_id}: span {span.span_id} id does not match its range"
            )
        if span.char_start < 0 or span.char_end > leaf_length:
            findings.append(
                f"leaf {leaf_id}: span [{span.char_start},{span.char_end}) "
                f"outside leaf text [0,{leaf_length})"
            )
        if span.char_end <= span.char_start:
            findings.append(
                f"leaf {leaf_id}: span [{span.char_start},{span.char_end}) is empty"
            )
        if span.char_start > cursor:
            findings.append(
                f"leaf {leaf_id}: uncovered text [{cursor},{span.char_start})"
            )
        elif span.char_start < cursor:
            findings.append(
                f"leaf {leaf_id}: overlapping span at [{span.char_start},"
                f"{span.char_end}) (covered through {cursor})"
            )
        cursor = max(cursor, span.char_end)

    if cursor < leaf_length:
        findings.append(f"leaf {leaf_id}: uncovered text [{cursor},{leaf_length})")

    return tuple(findings)


def validate_reason_codes(spans: tuple[SemanticSpan, ...]) -> tuple[str, ...]:
    """Return violations of the closed non-mechanical reason catalog."""
    findings: list[str] = []
    for span in spans:
        code = span.non_mechanical_reason_code
        if span.disposition is SemanticDisposition.NON_MECHANICAL:
            if code is None:
                findings.append(f"span {span.span_id}: non-mechanical without reason")
            elif non_mechanical_reason_for(code) is None:
                findings.append(
                    f"span {span.span_id}: reason {code!r} is not in the closed catalog"
                )
        elif code is not None:
            findings.append(
                f"span {span.span_id}: reason {code!r} on a "
                f"{span.disposition.value} span"
            )
    return tuple(findings)


def batch_diff_payload(batch: AcceptanceBatch) -> list[dict[str, object]]:
    """Canonical serialization of a batch's retained semantic diff."""
    return sorted(
        (
            {
                "span_id": e.span_id,
                "prior_disposition": (
                    e.prior_disposition.value if e.prior_disposition else None
                ),
                "prior_reason_code": e.prior_reason_code,
                "accepted_disposition": e.accepted_disposition.value,
                "accepted_reason_code": e.accepted_reason_code,
            }
            for e in batch.diff
        ),
        key=lambda d: str(d["span_id"]),
    )


def batch_diff_hash(batch: AcceptanceBatch) -> str:
    """SHA-256 over a batch's canonical retained diff."""
    return hash_obj(batch_diff_payload(batch))


def _validate_batch(
    batch: AcceptanceBatch,
    spans_by_id: dict[str, SemanticSpan],
) -> list[str]:
    """Return violations of one batch's retained acceptance evidence."""
    findings: list[str] = []
    tag = f"batch {batch.batch_id}"

    if not batch.rule.strip():
        findings.append(f"{tag}: no acceptance rule recorded")
    if not batch.resolved_scope:
        findings.append(f"{tag}: no resolved scope recorded")
    if not batch.diff:
        findings.append(f"{tag}: no semantic diff retained")

    scope = set(batch.resolved_scope)
    for span_id in sorted(scope - spans_by_id.keys()):
        findings.append(f"{tag}: scope names unknown span {span_id}")

    diff_ids: set[str] = set()
    for entry in batch.diff:
        if entry.span_id in diff_ids:
            findings.append(f"{tag}: duplicate diff entry for span {entry.span_id}")
        diff_ids.add(entry.span_id)

        if entry.span_id not in spans_by_id:
            findings.append(f"{tag}: diff names unknown span {entry.span_id}")
            continue
        if entry.span_id not in scope:
            findings.append(f"{tag}: diff entry {entry.span_id} outside resolved scope")

        span = spans_by_id[entry.span_id]
        if entry.accepted_disposition is not span.disposition:
            findings.append(
                f"{tag}: diff claims {entry.span_id} accepted as "
                f"{entry.accepted_disposition.value}, ledger has "
                f"{span.disposition.value}"
            )
        if entry.accepted_reason_code != span.non_mechanical_reason_code:
            findings.append(
                f"{tag}: diff claims {entry.span_id} reason "
                f"{entry.accepted_reason_code!r}, ledger has "
                f"{span.non_mechanical_reason_code!r}"
            )

    for span_id in sorted(scope - diff_ids):
        findings.append(f"{tag}: scope member {span_id} has no accepted diff entry")

    if batch.semantic_diff_hash != batch_diff_hash(batch):
        findings.append(f"{tag}: semantic diff digest does not match retained diff")

    return findings


def validate_acceptance(ledger: ClassificationLedger) -> tuple[str, ...]:
    """Return violations of the explicit-acceptance rule (#137 contract 2).

    Blocks publication on unreviewed residue, unresolved classification,
    acceptance records pointing at spans that do not exist, and batch
    acceptances whose retained evidence would not let a reviewer re-check what
    was accepted: a missing or forged diff, an acceptance outside the resolved
    scope, a scope member with nothing accepted for it, or a blank record of
    who accepted it and when.
    """
    findings: list[str] = []
    spans_by_id = {s.span_id: s for s in ledger.spans}
    span_ids = spans_by_id.keys()
    batch_ids: set[str] = set()
    accepted: set[str] = set()

    for batch in ledger.batches:
        if batch.batch_id in batch_ids:
            findings.append(f"batch {batch.batch_id}: duplicate batch id")
        batch_ids.add(batch.batch_id)
        findings.extend(_validate_batch(batch, spans_by_id))

    scope_by_batch = {b.batch_id: set(b.resolved_scope) for b in ledger.batches}

    for record in ledger.acceptances:
        if record.span_id not in span_ids:
            findings.append(f"acceptance for unknown span {record.span_id}")
        if not record.reviewer.strip() or not record.accepted_at.strip():
            findings.append(
                f"span {record.span_id}: acceptance without reviewer/timestamp evidence"
            )
        if record.batch_id is not None:
            if record.batch_id not in batch_ids:
                findings.append(
                    f"span {record.span_id}: acceptance names unknown batch "
                    f"{record.batch_id}"
                )
            elif record.span_id not in scope_by_batch[record.batch_id]:
                findings.append(
                    f"span {record.span_id}: acceptance outside the resolved scope "
                    f"of batch {record.batch_id}"
                )
        if record.span_id in accepted:
            findings.append(f"span {record.span_id}: duplicate acceptance record")
        accepted.add(record.span_id)

    for span in ledger.spans:
        if span.disposition is SemanticDisposition.UNRESOLVED:
            findings.append(f"span {span.span_id}: unresolved classification")
        # An accepted *review state* still requires the acceptance evidence that
        # produced it; a row that simply says "accepted" is the silence this
        # rule rejects.
        if span.span_id not in accepted:
            findings.append(f"span {span.span_id}: no acceptance record")
        elif span.review_state is not ReviewState.ACCEPTED:
            findings.append(
                f"span {span.span_id}: accepted evidence but review state "
                f"{span.review_state.value}"
            )

    return tuple(findings)


def classification_payload(ledger: ClassificationLedger) -> dict[str, object]:
    """Canonical, identity-bearing payload of the accepted classification.

    Carries the accepted semantic result and the identity-bound semantic
    policy — nothing about how review arrived there. Batches, acceptance
    records, batch grouping and wording, resolved scope, reviewers, and
    timestamps are all deliberately absent: they are retained, validated review
    evidence, not authority. Review state is likewise absent, because a
    publishable ledger has no unaccepted span left to distinguish.
    """
    return {
        "package_uuid": ledger.package_uuid,
        "release_version": ledger.release_version,
        "semantic_policy_version": SEMANTIC_POLICY_VERSION,
        "semantic_policy_hash": semantic_policy_hash(),
        "spans": sorted(
            (
                {
                    "span_id": s.span_id,
                    "leaf_id": s.leaf_id,
                    "char_start": s.char_start,
                    "char_end": s.char_end,
                    "disposition": s.disposition.value,
                    "non_mechanical_reason_code": s.non_mechanical_reason_code,
                }
                for s in ledger.spans
            ),
            key=lambda d: str(d["span_id"]),
        ),
    }


def classification_identity(ledger: ClassificationLedger) -> str:
    """SHA-256 of the accepted classification payload."""
    return hash_obj(classification_payload(ledger))
