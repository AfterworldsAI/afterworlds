"""Authoritative-source completeness proof — CRD Issue 5c, Component A.

The publication gate proved that a candidate's pages are internally consistent
and include the six version canaries — but *not* that the candidate exhausts the
exact 364-page authoritative PDF. A candidate carrying the real ``PDF_SHA256``
constant while covering only a subset of pages (the six canary pages, say) could
therefore pass finalization, because the source hash is a constant, not a
function of the pages actually extracted (PR #134 completeness defect).

This module closes that hole with an independent, reproducible proof that the
candidate's ordered page/content identity corresponds exhaustively to the
authoritative document:

* the ordered per-page extraction manifest — ``(page_index, printed_page,
  geometry, sha256(canonical_text))`` for every page in order — is hashed to a
  single ``source_extraction_hash``;
* that hash is compared to :data:`AUTHORITATIVE_SOURCE_EXTRACTION_HASH`, a golden
  constant derived once from a full extraction of the committed PDF (the same
  hardcoded-verified-fact pattern as ``PDF_SHA256`` and the version canaries);
* structural checks assert the page sequence is exactly ``1..364`` contiguous
  with ``page_index == printed_page - 1``, so each corruption mode — an omitted,
  duplicated, reordered, or substituted page — yields a *diagnosable* failure.

The proof is over **page** text (``canonical_text``), which is pre-segmentation,
so it is stable across legitimate downstream leaf/chunk/table segmentation
changes: it attests exhaustive ordered source *extraction*, while concordance and
the table/row accounting separately attest structural fidelity.

This is a verification module (like ``gate``/``concordance``): it never produces
candidate bytes, so it is deliberately excluded from the first-party transform
source manifest (``transform_identity``) and does not affect the package UUID.
"""

from __future__ import annotations

from afterworlds.ingestion.corpus.hashing import hash_obj, sha256_hex
from afterworlds.ingestion.corpus.pdf_source import ExtractedPage

# The authoritative PDF has exactly this many physical pages (Component A).
EXPECTED_PAGE_COUNT = 364

# Golden aggregate over the ordered full-PDF extraction manifest, derived once
# from a complete extraction of the committed authoritative PDF with the pinned
# extractor. Reproducible: re-running extraction on the exact PDF regenerates it.
# A bump of the pinned extractor (a transform-config change) can move extraction
# output and would require re-deriving this constant, exactly like PDF_SHA256.
AUTHORITATIVE_SOURCE_EXTRACTION_HASH = (
    "560367b48a13442299d43996dc5722fb3f423d5b60e882a12638eb088d250ec3"
)


def source_extraction_manifest(pages: list[ExtractedPage]) -> list[dict[str, object]]:
    """The ordered per-page extraction manifest (pre-segmentation).

    One entry per page in extraction order, binding the page's ordinal identity,
    geometry, and a digest of its full canonical text. Omitting, duplicating,
    reordering, or substituting any page changes this manifest.
    """
    return [
        {
            "page_index": pg.page_index,
            "printed_page": pg.printed_page,
            "width": pg.width,
            "height": pg.height,
            "text_sha256": sha256_hex(pg.canonical_text().encode("utf-8")),
        }
        for pg in pages
    ]


def source_extraction_hash(pages: list[ExtractedPage]) -> str:
    """SHA-256 over the ordered per-page extraction manifest."""
    return hash_obj(source_extraction_manifest(pages))


def verify_source_completeness(pages: list[ExtractedPage]) -> tuple[str, ...]:
    """Prove *pages* exhaustively match the authoritative PDF (Component A).

    Returns a tuple of diagnosable failures (empty iff the candidate exhausts the
    exact authoritative document). Detects omitted, duplicated, reordered, and
    substituted pages independently of the claimed PDF hash, aggregate counts,
    canary presence, or any candidate-supplied assertion.
    """
    failures: list[str] = []

    if len(pages) != EXPECTED_PAGE_COUNT:
        failures.append(
            f"expected {EXPECTED_PAGE_COUNT} extracted pages, found {len(pages)} "
            "(pages omitted or duplicated)"
        )

    # Ordered sequence must be exactly 1..N with page_index == printed_page - 1.
    expected_printed = list(range(1, EXPECTED_PAGE_COUNT + 1))
    actual_printed = [pg.printed_page for pg in pages]
    if actual_printed != expected_printed:
        seen: set[int] = set()
        dupes = sorted({p for p in actual_printed if p in seen or seen.add(p)})  # type: ignore[func-returns-value]
        missing = sorted(set(expected_printed) - set(actual_printed))
        detail = []
        if missing:
            detail.append(f"missing printed pages {missing[:8]}")
        if dupes:
            detail.append(f"duplicated printed pages {dupes[:8]}")
        if not detail:
            detail.append("printed-page order differs from 1..N (pages reordered)")
        failures.append("page sequence invalid: " + "; ".join(detail))
    for pg in pages:
        if pg.page_index != pg.printed_page - 1:
            failures.append(
                f"page_index {pg.page_index} != printed_page {pg.printed_page} - 1 "
                "(page ordinal identity corrupted)"
            )
            break

    # Content identity: substituted/altered page text changes the aggregate.
    actual_hash = source_extraction_hash(pages)
    if actual_hash != AUTHORITATIVE_SOURCE_EXTRACTION_HASH:
        failures.append(
            "source extraction hash mismatch: pages do not match the authoritative "
            f"PDF extraction ({actual_hash} != "
            f"{AUTHORITATIVE_SOURCE_EXTRACTION_HASH})"
        )

    return tuple(failures)
