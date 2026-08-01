"""Canonical ordering for unordered semantic collections — CRD Issue 5d.

ADR-005d Decision 6 requires a projection identity that reproduces from
identical content. A collection whose meaning does not depend on order must
therefore hash the same however it was authored, and the only way to guarantee
that is to order by the element's *complete* canonical payload.

Hand-picked sort tuples cannot provide it. Any field left out of the tuple
makes two semantically different elements compare equal, and Python's stable
sort then preserves authoring order — so the identity silently depends on the
order someone happened to write things in. Worse, the defect returns every time
a field is added and the tuple is not, which is exactly how it arrived. Sorting
by the serialized payload has no such failure mode: a new field is inside the
bytes the moment it is inside the payload.

Duplicates are preserved rather than collapsed. Two identical entries are a
validation failure, not something canonicalization should quietly tidy away.
"""

from __future__ import annotations

from collections.abc import Iterable

from afterworlds.ingestion.corpus.hashing import canonical_bytes

__all__ = ["canonical_order"]


def canonical_order(
    payloads: Iterable[dict[str, object]],
) -> list[dict[str, object]]:
    """Return *payloads* in a total order derived from their whole content."""
    return sorted(payloads, key=canonical_bytes)
