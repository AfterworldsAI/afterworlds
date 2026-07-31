"""Semantic accounting types — CRD Issue 5d, span-exact classification.

ADR-005d Decision 2 partitions every 5c ``REPRESENTED`` leaf into accepted
semantic spans. This module holds the frozen value types for that partition and
for the acceptance evidence that makes a span publishable. It holds no policy
(see :mod:`policy`) and performs no validation (see :mod:`accounting`).

Two separations are load-bearing and appear here as distinct fields rather than
as one status:

* **semantic disposition** — what the text *is* (substantive, supporting,
  non-mechanical, unresolved);
* **review state** — whether a human accepted that claim. A proposal is not an
  acceptance, and silence is never acceptance (#137 contract 2).

Reviewer identity, acceptance timestamps, and comments are audit metadata: they
travel with the record but are excluded from every identity payload, so a
re-review that changes nothing semantic does not mint a new projection
(#137 acceptance criterion 11).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class SemanticDisposition(StrEnum):
    """The mechanical role of one accepted span (#137 contract 2).

    ``UNRESOLVED`` is an honest "cannot classify safely yet" and blocks
    publication; it is not a bucket for text nobody looked at, which is what
    a missing span means instead.
    """

    SUBSTANTIVE = "substantive"
    SUPPORTING_AUTHORITY = "supporting_authority"
    NON_MECHANICAL = "non_mechanical"
    UNRESOLVED = "unresolved"


class ReviewState(StrEnum):
    """Whether a proposal has been explicitly accepted by review."""

    PROPOSED = "proposed"
    ACCEPTED = "accepted"


class ComponentHandling(StrEnum):
    """How a publishable component's meaning is represented (#137 contract 2).

    ``PROSE_BOUND`` is an affirmative judgement backed by a closed
    irreducibility reason — never a backlog state and never a synonym for
    "the adapter cannot execute it".
    """

    STRUCTURED = "structured"
    PROSE_BOUND = "prose_bound"
    MIXED = "mixed"


@dataclass(frozen=True)
class NonMechanicalReason:
    """One entry of the closed, identity-bound non-mechanical reason catalog."""

    code: str
    description: str


@dataclass(frozen=True)
class IrreducibilityReason:
    """One entry of the closed prose-bound irreducibility catalog."""

    code: str
    description: str


@dataclass(frozen=True)
class SemanticSpan:
    """One accepted-or-proposed classification of an exact leaf subspan.

    ``char_start``/``char_end`` are a half-open range over the leaf's canonical
    text, so a leaf's spans form a gap-free non-overlapping partition
    (validated in :mod:`accounting`, not here).

    ``span_id`` is content-derived from the leaf and range, so an unrelated
    edit elsewhere in the corpus never churns it (#137 acceptance criterion 6).
    """

    span_id: str
    leaf_id: str
    char_start: int
    char_end: int
    disposition: SemanticDisposition
    review_state: ReviewState
    # Required exactly when disposition is NON_MECHANICAL; must name a code in
    # the frozen catalog.
    non_mechanical_reason_code: str | None = None


@dataclass(frozen=True)
class AcceptanceBatch:
    """A rule-scoped batch acceptance (#137 contract 2).

    Batch acceptance is what makes full-corpus review tractable, but it must
    record *what rule was applied to what scope* and *what changed*, so a batch
    can be re-derived and audited rather than taken on trust. A batch whose
    recorded rule, scope, or semantic diff is missing is not an acceptance.

    ``semantic_diff_hash`` covers the exact set of (span, disposition, reason)
    transitions the batch produced.
    """

    batch_id: str
    rule: str
    scope: tuple[str, ...]
    semantic_diff_hash: str


@dataclass(frozen=True)
class AcceptanceRecord:
    """Evidence that one span's semantic claim was explicitly accepted.

    ``batch_id`` is ``None`` for an individually reviewed span and otherwise
    names an :class:`AcceptanceBatch`. ``reviewer`` and ``accepted_at`` are
    audit metadata excluded from identity.
    """

    span_id: str
    batch_id: str | None
    reviewer: str
    accepted_at: str


@dataclass(frozen=True)
class ClassificationLedger:
    """The complete accepted semantic accounting for one bound 5c release.

    This is a committed, meaning-bearing input to the build — never a product
    of it (#137 contract 4: the oracle is not regenerated from the output it
    checks).
    """

    package_uuid: str
    release_version: str
    policy_version: str
    spans: tuple[SemanticSpan, ...]
    batches: tuple[AcceptanceBatch, ...]
    acceptances: tuple[AcceptanceRecord, ...]
