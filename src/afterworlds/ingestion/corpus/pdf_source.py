"""Authoritative PDF source binding and deterministic extraction — CRD Issue 5c.

Component A binds the corpus to the exact document identity of
``docs/sources/DnD5_5e_SRD_CC_v5_2_1.pdf``. Component B requires the transform to
be reproducible: given the pinned extractor version and the frozen extraction
configuration recorded here, extraction is byte-for-byte deterministic.

Reading-order recipe (established by direct spike against the six version-canary
pages, Component J): ``extract_words(use_text_flow=True)`` follows the PDF
content stream's authored reading order, which this document renders correctly
including two-column flow, full-width headings, and running headers/footers.
Words are grouped into visual lines by vertical proximity while preserving flow
order. No word in this document straddles the column gutter, so no line is ever
split across columns.

Page numbering: the printed page number equals the physical page index + 1
(verified: the running footer ``N System Reference Document 5.2.1`` prints ``N``
on physical index ``N-1``). All locators in the corpus use the printed page.

This module reads the PDF; it never writes canon and carries no dispositions —
those belong to the ledger (C), policy (B), and reconciliation (D).
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib.metadata import version as _pkg_version
from pathlib import Path

import pdfplumber

# ---------------------------------------------------------------------------
# Authoritative source identity (Component A) — verified against the repository.
# ---------------------------------------------------------------------------

PDF_REPO_PATH = "docs/sources/DnD5_5e_SRD_CC_v5_2_1.pdf"
PDF_SHA256 = "8974902d109d6e63672d7c490bde9ccf052410503d9cfa768237154fbc5e3d87"
PDF_BYTE_SIZE = 6031375
SOURCE_DOCUMENT = "D&D SRD 5.2.1"
SOURCE_VERSION = "5.2.1"
SOURCE_LICENSE = "CC BY 4.0"

# ---------------------------------------------------------------------------
# Frozen extraction configuration (Component B). Any change here is a
# transform-config change that yields a new draft release (Component A).
# ---------------------------------------------------------------------------

# Vertical tolerance (points) for grouping flow-ordered words into one visual
# line. Lines in this document are ~12pt apart; 3.0 groups a line without
# merging adjacent lines.
LINE_Y_TOLERANCE = 3.0
# Decimal places geometry is rounded to before it enters any hashed artifact,
# so float rendering can never perturb a proof identity.
GEOMETRY_DECIMALS = 2


def extraction_config() -> dict[str, object]:
    """Return the frozen transform/extraction identity (Component B).

    Recorded under the transform source/configuration hash so the release binds
    the exact tool and parameters that produced the corpus.
    """
    return {
        "tool": "pdfplumber",
        "tool_version": _pkg_version("pdfplumber"),
        "engine": "pdfminer.six",
        "engine_version": _pkg_version("pdfminer.six"),
        "use_text_flow": True,
        "keep_blank_chars": False,
        "line_y_tolerance": LINE_Y_TOLERANCE,
        "geometry_decimals": GEOMETRY_DECIMALS,
        "reading_order": "content-stream flow, lines grouped by top proximity",
    }


# ---------------------------------------------------------------------------
# Extracted structures — geometry-bearing but disposition-free.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PageLine:
    """One visual line of source text with its geometry.

    ``top``/``x0``/``x1``/``size`` support deterministic leaf segmentation in the
    ledger (headings by font size, list items by indent). ``char_start``/
    ``char_end`` are the half-open span of this line within the page's canonical
    text (see :meth:`ExtractedPage.canonical_text`).
    """

    page_index: int
    printed_page: int
    line_index: int
    text: str
    top: float
    x0: float
    x1: float
    size: float
    char_start: int
    char_end: int


@dataclass(frozen=True)
class ExtractedPage:
    """Deterministic extraction of one physical PDF page."""

    page_index: int
    printed_page: int
    width: float
    height: float
    lines: tuple[PageLine, ...]

    def canonical_text(self) -> str:
        """The page's full text as ``\\n``-joined lines, in reading order."""
        return "\n".join(line.text for line in self.lines)


class PdfIdentityError(RuntimeError):
    """Raised when the on-disk PDF does not match the bound source identity."""


def verify_pdf_identity(pdf_path: Path) -> None:
    """Verify *pdf_path* matches the bound authoritative identity (Component A).

    Checks byte size and SHA-256. A mismatch fails closed — the corpus can only
    be built from the exact authoritative document.
    """
    from afterworlds.ingestion.corpus.hashing import sha256_hex

    data = pdf_path.read_bytes()
    if len(data) != PDF_BYTE_SIZE:
        raise PdfIdentityError(
            f"{pdf_path}: byte size {len(data)} != expected {PDF_BYTE_SIZE}"
        )
    digest = sha256_hex(data)
    if digest != PDF_SHA256:
        raise PdfIdentityError(f"{pdf_path}: SHA-256 {digest} != expected {PDF_SHA256}")


def _round(value: float) -> float:
    return round(value, GEOMETRY_DECIMALS)


def _group_lines(
    words: list[dict[str, object]], page_index: int, printed_page: int
) -> tuple[PageLine, ...]:
    """Group flow-ordered *words* into visual lines, preserving reading order."""
    lines: list[PageLine] = []
    cur_texts: list[str] = []
    cur_tops: list[float] = []
    cur_x0: list[float] = []
    cur_x1: list[float] = []
    cur_size: list[float] = []
    char_cursor = 0

    def flush() -> None:
        nonlocal char_cursor
        if not cur_texts:
            return
        text = " ".join(cur_texts)
        # +1 for the "\n" separator that joins lines in canonical_text, except
        # the accounting below is corrected once at the end for the final line.
        start = char_cursor
        end = start + len(text)
        lines.append(
            PageLine(
                page_index=page_index,
                printed_page=printed_page,
                line_index=len(lines),
                text=text,
                top=_round(min(cur_tops)),
                x0=_round(min(cur_x0)),
                x1=_round(max(cur_x1)),
                size=_round(max(cur_size)),
                char_start=start,
                char_end=end,
            )
        )
        char_cursor = end + 1  # account for the joining "\n"
        cur_texts.clear()
        cur_tops.clear()
        cur_x0.clear()
        cur_x1.clear()
        cur_size.clear()

    running_top: float | None = None
    for w in words:
        top = float(w["top"])  # type: ignore[arg-type]
        if running_top is not None and abs(top - running_top) > LINE_Y_TOLERANCE:
            flush()
            running_top = None
        if running_top is None:
            running_top = top
        cur_texts.append(str(w["text"]))
        cur_tops.append(top)
        cur_x0.append(float(w["x0"]))  # type: ignore[arg-type]
        cur_x1.append(float(w["x1"]))  # type: ignore[arg-type]
        cur_size.append(float(w.get("size", 0.0)))  # type: ignore[arg-type]
    flush()
    return tuple(lines)


def extract_pages(pdf_path: Path) -> list[ExtractedPage]:
    """Deterministically extract every page of the authoritative PDF.

    Verifies source identity first (Component A), then extracts in reading order
    using the frozen configuration (Component B). Output is stable across runs.
    """
    verify_pdf_identity(pdf_path)
    pages: list[ExtractedPage] = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page_index, page in enumerate(pdf.pages):
            printed_page = page_index + 1
            words = page.extract_words(
                use_text_flow=True,
                keep_blank_chars=False,
                extra_attrs=["size"],
            )
            lines = _group_lines(words, page_index, printed_page)
            pages.append(
                ExtractedPage(
                    page_index=page_index,
                    printed_page=printed_page,
                    width=_round(float(page.width)),
                    height=_round(float(page.height)),
                    lines=lines,
                )
            )
    return pages
