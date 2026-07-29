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

* the ordered per-page extraction manifest — page ordinals plus the complete
  **normalized extraction geometry** every page contributes (per-line
  ``top``/``x0``/``x1``/``size`` + char span + text, per-word ``text``/``x0``/
  ``x1`` + char span, and each rect's rounded geometry) — is hashed to a single
  ``source_extraction_hash``;
* that hash is compared to :data:`AUTHORITATIVE_SOURCE_EXTRACTION_HASH`, a golden
  constant derived once from a full extraction of the committed PDF (the same
  hardcoded-verified-fact pattern as ``PDF_SHA256`` and the version canaries);
* structural checks assert the page sequence is exactly ``1..364`` contiguous
  with ``page_index == printed_page - 1``, so each corruption mode — an omitted,
  duplicated, reordered, or substituted page — yields a *diagnosable* failure.

Binding geometry (not just page text) means a geometry-only change — a moved
coordinate, a resized font, a shifted word span, an added/removed rect — that
leaves the page text unchanged still fails completeness, because such a change
can silently alter headings and table cells (R15 F2). The manifest is over
**extraction** output (pre-segmentation), so it remains stable across downstream
leaf/chunk/table *segmentation* changes: it attests exhaustive ordered source
extraction, while concordance and the table oracle separately attest structural
fidelity.

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
    "f22f711e56e37057c3122f3dc54b8fc96684020e66c1d2c0db116a2eba4fc291"
)


def _page_geometry(pg: ExtractedPage) -> dict[str, object]:
    """The full normalized extraction geometry a page contributes to the manifest.

    Binds exactly the extraction fields heading/table/ledger construction consumes
    (PR #134 R15 F2): per-line ``top``/``x0``/``x1``/``size`` + char span + text,
    per-word ``text``/``x0``/``x1`` + char span, and each rect's rounded geometry.
    So a geometry-only change (a moved coordinate, a resized font, a shifted word
    span, an added/removed rect) that leaves the page *text* unchanged still moves
    the manifest — it could otherwise silently alter headings and table cells while
    passing authoritative-source completeness. Rect *type* is not bound because
    detection never reads it. All floats are already geometry-rounded at extraction.
    """
    return {
        "page_index": pg.page_index,
        "printed_page": pg.printed_page,
        "width": pg.width,
        "height": pg.height,
        "text_sha256": sha256_hex(pg.canonical_text().encode("utf-8")),
        "lines": [
            {
                "top": ln.top,
                "x0": ln.x0,
                "x1": ln.x1,
                "size": ln.size,
                "char_start": ln.char_start,
                "char_end": ln.char_end,
                "text": ln.text,
                "words": [
                    {
                        "text": w.text,
                        "x0": w.x0,
                        "x1": w.x1,
                        "char_start": w.char_start,
                        "char_end": w.char_end,
                    }
                    for w in ln.words
                ],
            }
            for ln in pg.lines
        ],
        "rects": [
            {"x0": r.x0, "top": r.top, "x1": r.x1, "bottom": r.bottom} for r in pg.rects
        ],
    }


def source_extraction_manifest(pages: list[ExtractedPage]) -> list[dict[str, object]]:
    """The ordered per-page extraction manifest (pre-segmentation).

    One entry per page in extraction order, binding the page's ordinal identity
    and its complete normalized extraction geometry (:func:`_page_geometry`).
    Omitting, duplicating, reordering, or substituting a page — or changing any
    consumed line/word/rect geometry while leaving the page text unchanged —
    changes this manifest. It remains pre-segmentation, so downstream leaf/table
    segmentation changes do not perturb it.
    """
    return [_page_geometry(pg) for pg in pages]


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
