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

Identity is derived from accepted semantic content only. Reviewer names and
acceptance timestamps travel in the ledger but never reach the payload, so
re-reviewing an unchanged classification does not mint a new projection
(#137 acceptance criterion 11).
"""

from __future__ import annotations

from afterworlds.ingestion.corpus.hashing import content_id, hash_obj
from afterworlds.ingestion.mechanical.models import (
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


def validate_acceptance(ledger: ClassificationLedger) -> tuple[str, ...]:
    """Return violations of the explicit-acceptance rule (#137 contract 2).

    Blocks publication on unreviewed residue, unresolved classification,
    acceptance records pointing at spans that do not exist, and batch
    acceptances that fail to record the rule, scope, or semantic diff that
    would let a reviewer re-derive them.
    """
    findings: list[str] = []
    span_ids = {s.span_id for s in ledger.spans}
    batch_ids = {b.batch_id for b in ledger.batches}
    accepted: set[str] = set()

    for batch in ledger.batches:
        if not batch.rule.strip():
            findings.append(f"batch {batch.batch_id}: no acceptance rule recorded")
        if not batch.scope:
            findings.append(f"batch {batch.batch_id}: no acceptance scope recorded")
        if not batch.semantic_diff_hash.strip():
            findings.append(f"batch {batch.batch_id}: no semantic diff recorded")

    for record in ledger.acceptances:
        if record.span_id not in span_ids:
            findings.append(f"acceptance for unknown span {record.span_id}")
        if record.batch_id is not None and record.batch_id not in batch_ids:
            findings.append(
                f"span {record.span_id}: acceptance names unknown batch "
                f"{record.batch_id}"
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

    Carries accepted semantic content and the batch rules that produced it.
    Excludes reviewer identity and acceptance timestamps: audit metadata, not
    meaning.
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
        "batches": sorted(
            (
                {
                    "batch_id": b.batch_id,
                    "rule": b.rule,
                    "scope": list(b.scope),
                    "semantic_diff_hash": b.semantic_diff_hash,
                }
                for b in ledger.batches
            ),
            key=lambda d: str(d["batch_id"]),
        ),
        "acceptances": sorted(
            (
                {"span_id": a.span_id, "batch_id": a.batch_id}
                for a in ledger.acceptances
            ),
            key=lambda d: str(d["span_id"]),
        ),
    }


def classification_identity(ledger: ClassificationLedger) -> str:
    """SHA-256 of the accepted classification payload."""
    return hash_obj(classification_payload(ledger))
