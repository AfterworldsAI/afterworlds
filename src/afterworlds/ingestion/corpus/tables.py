"""Deterministic table reconstruction — CRD Issue 5c, Component F, PR #134.

The extractor collapses each visual line into a single string, so the ledger
emitted multi-column table rows as ``PARAGRAPH`` leaves and discarded cell
boundaries. This module reconstructs table structure geometrically:

* SRD tables shade their cells with filled rectangles; a shaded row's per-column
  rects give deterministic **column boundaries** and a y-band anchor. (Only
  alternating rows are shaded, so rects anchor the *grid*, not the rows.)
* The **rows** come from the text lines that align to those columns: a line with
  words in ≥2 columns (including the first) starts a row; a following line whose
  words all fall in a later single column is a wrapped continuation of it.
* Each row's canonical-text char span is partitioned at the column boundaries
  into ``TABLE_CELL`` sub-spans — so the cells exactly tile the same characters
  the row would otherwise occupy, preserving the ledger's disjoint+exhaustive
  page tiling. A cell is emitted exactly once; wrapped continuation text folds
  into the last column's cell rather than duplicating it.

Detection only ever consumes a **maximal contiguous run** of table-aligned lines
(in extraction/flow order), so a table maps to a contiguous ``page.lines`` index
range and its cell spans form one contiguous char range. A region that does not
form such a clean run is left to normal paragraph segmentation — the tiling
invariant is never sacrificed for table fidelity.
"""

from __future__ import annotations

from dataclasses import dataclass

from afterworlds.ingestion.corpus.hashing import content_id
from afterworlds.ingestion.corpus.pdf_source import ExtractedPage, PageLine, Rect
from afterworlds.ingestion.corpus.policy import compact

# A word's left edge must sit within this many points of a column's [left,right)
# to be assigned to it.
_COL_TOLERANCE = 3.0
# Max vertical gap (points) between stacked shaded rows still considered one
# table, and the band by which a table's text extent may exceed its rect anchor.
_ROW_GAP = 8.0
_BAND_PAD = 20.0
# Heading font floor: a line at/above this size is a heading, never a table row
# (mirrors ledger._HEADING_MIN_SIZE), so a section/subsection heading sharing a
# body column with a table is never folded into a cell.
_HEADING_SIZE = 11.5


@dataclass(frozen=True)
class DetectedCell:
    """One reconstructed table cell occurrence."""

    row: int
    col: int
    text: str
    char_start: int
    char_end: int


@dataclass(frozen=True)
class DetectedTable:
    """A reconstructed table over a contiguous ``page.lines`` index range."""

    table_id: str
    printed_page: int
    start_line: int  # inclusive index into page.lines
    end_line: int  # inclusive
    column_count: int
    row_count: int
    cells: tuple[DetectedCell, ...]


def _rect_column_anchors(rects: tuple[Rect, ...]) -> list[list[float]]:
    """Cluster shaded rects into per-table column boundary lists.

    Groups rects into rows by (top, bottom) band, keeps rows with ≥2 column
    cells, then clusters vertically-adjacent rows sharing a left-edge signature
    into one table. Returns one ``[b0, b1, ..., bN]`` boundary list per table.
    """
    rows: dict[tuple[float, float], list[tuple[float, float]]] = {}
    for r in rects:
        rows.setdefault((r.top, r.bottom), []).append((r.x0, r.x1))
    multi = []
    for (top, bottom), cells in rows.items():
        uniq = sorted(set(cells))
        if len(uniq) >= 2:
            multi.append((top, bottom, uniq))
    multi.sort()

    anchors: list[list[float]] = []
    cur: list[tuple[float, float, list[tuple[float, float]]]] = []

    def signature(cells: list[tuple[float, float]]) -> tuple[float, ...]:
        return tuple(c[0] for c in cells)

    for row in multi:
        if (
            cur
            and signature(row[2]) == signature(cur[-1][2])
            and row[0] - cur[-1][1] < _ROW_GAP
        ):
            cur.append(row)
        else:
            if cur:
                anchors.append(_boundaries(cur[0][2]))
            cur = [row]
    if cur:
        anchors.append(_boundaries(cur[0][2]))
    return anchors


def _boundaries(cells: list[tuple[float, float]]) -> list[float]:
    """Column boundaries from a signature row's cells: [left0..leftN, rightN]."""
    lefts = [c[0] for c in cells]
    return lefts + [cells[-1][1]]


def _column_of(x0: float, bounds: list[float]) -> int | None:
    """The column index whose [left, right) contains word left-edge *x0*."""
    for c in range(len(bounds) - 1):
        if bounds[c] - _COL_TOLERANCE <= x0 < bounds[c + 1] - _COL_TOLERANCE:
            return c
    # Allow the last column to absorb a right-edge word slightly past bounds[-1].
    if bounds[-2] - _COL_TOLERANCE <= x0 <= bounds[-1] + _COL_TOLERANCE:
        return len(bounds) - 2
    return None


def _line_columns(line: PageLine, bounds: list[float]) -> list[int] | None:
    """Per-word column indices for *line*, or None if any word escapes the grid."""
    cols: list[int] = []
    for w in line.words:
        c = _column_of(w.x0, bounds)
        if c is None:
            return None
        cols.append(c)
    return cols


def _band(anchor_rows: list[float]) -> tuple[float, float]:
    return min(anchor_rows) - _BAND_PAD, max(anchor_rows) + _BAND_PAD


def detect_page_tables(page: ExtractedPage) -> tuple[DetectedTable, ...]:
    """Reconstruct every rect-anchored table on *page* as contiguous line runs."""
    anchors = _rect_column_anchors(page.rects)
    if not anchors:
        return ()

    page_compact = compact(page.canonical_text())
    tables: list[DetectedTable] = []
    used_lines: set[int] = set()
    for ai, bounds in enumerate(anchors):
        # y-band = vertical extent of the shaded rects whose left edge belongs to
        # this anchor's column signature (padded to catch header + trailing rows).
        sig = set(bounds[:-1])
        rect_ys = [r.top for r in page.rects if r.x0 in sig] + [
            r.bottom for r in page.rects if r.x0 in sig
        ]
        if not rect_ys:
            continue
        lo, hi = _band(rect_ys)
        col_count = len(bounds) - 1
        # Candidate table lines: within the y-band, every word fits the grid.
        run = _maximal_run(page, bounds, lo, hi, used_lines)
        if run is None:
            continue
        start, end = run
        cells, row_count = _build_cells(page, bounds, start, end)
        if not cells:
            continue
        # Span-validity: the cells must tile the table's char range monotonically —
        # adjacent within a row (gap 0), one "\n" between rows (gap 1), each span
        # non-empty. A spanning title row or mis-aligned header yields inverted/
        # overlapping spans; discard the whole table so those lines fall back to
        # paragraph segmentation and the page tiling stays disjoint+exhaustive.
        if not _spans_tile(page, cells, start, end):
            continue
        # Self-validation: every reconstructed cell's text must actually appear
        # (whitespace/hyphen-insensitively) on the page. A cell that fails is a
        # mis-reconstruction (e.g. an adjacent-column heading folded in on an
        # atypically-laid-out page); discard the whole table so those lines fall
        # back to normal paragraph segmentation rather than emit a false cell.
        if any(compact(c.text) not in page_compact for c in cells):
            continue
        table_id = content_id(
            "table", page.printed_page, ai, col_count, page.lines[start].char_start
        )
        tables.append(
            DetectedTable(
                table_id=table_id,
                printed_page=page.printed_page,
                start_line=start,
                end_line=end,
                column_count=col_count,
                row_count=row_count,
                cells=tuple(cells),
            )
        )
        used_lines.update(range(start, end + 1))
    tables.sort(key=lambda t: t.start_line)
    return tuple(tables)


def _line_kind(line: PageLine, bounds: list[float]) -> str | None:
    """Classify *line* against a table's column grid.

    Returns ``"row"`` (a genuine multi-column row / header: words in the first
    column and ≥2 distinct columns), ``"cont"`` (a wrapped continuation: every
    word in a *single non-first* column), or ``None`` (not a table line — a
    heading, a first-column-only paragraph/heading, or a word off the grid). The
    strictness is what keeps a heading or the adjacent body column out of the
    table (PR #134): only real rows and their indented wraps qualify.
    """
    if line.size >= _HEADING_SIZE:
        return None
    cols = _line_columns(line, bounds)
    if cols is None or not cols:
        return None
    distinct = set(cols)
    if 0 in distinct and len(distinct) >= 2:
        return "row"
    if 0 not in distinct and len(distinct) == 1:
        return "cont"
    return None


def _maximal_run(
    page: ExtractedPage,
    bounds: list[float],
    lo: float,
    hi: float,
    used: set[int],
) -> tuple[int, int] | None:
    """Maximal contiguous ``page.lines`` run of table lines seeded in the band.

    A run is a contiguous block of ``"row"``/``"cont"`` lines that begins at a
    ``"row"`` line and contains ≥1 row line whose top is inside the rect-anchored
    y-band. Contiguity + the strict per-line classification guarantee the run is
    a single real table and its cells tile one contiguous char range.
    """
    n = len(page.lines)
    seeds = [
        i
        for i, ln in enumerate(page.lines)
        if i not in used and lo <= ln.top <= hi and _line_kind(ln, bounds) == "row"
    ]
    if not seeds:
        return None
    seed = min(seeds)
    # Grow a contiguous block of table lines outward from the seed.
    s = seed
    while s - 1 >= 0 and s - 1 not in used and _line_kind(page.lines[s - 1], bounds):
        s -= 1
    e = seed
    while e + 1 < n and e + 1 not in used and _line_kind(page.lines[e + 1], bounds):
        e += 1
    # Trim leading continuation lines so the run starts at a real row.
    while s <= e and _line_kind(page.lines[s], bounds) != "row":
        s += 1
    if s > e:
        return None
    return s, e


def _build_cells(
    page: ExtractedPage, bounds: list[float], start: int, end: int
) -> tuple[list[DetectedCell], int]:
    """Partition each row's char span into per-column cell sub-spans.

    Rows are delimited by row-start lines; continuation lines fold into the
    preceding row (their single-column text extends that column's cell). Each
    row's ``[row_start.char_start, row_end.char_end)`` span is partitioned at the
    char position of the first word of each column>0 in the row-start line, so
    the cells exactly tile the row (no gap/overlap).
    """
    # Group the run's line indices into rows: a "row" line starts a new row; a
    # "cont" (wrapped continuation) line folds into the current row.
    rows: list[list[int]] = []
    for i in range(start, end + 1):
        if _line_kind(page.lines[i], bounds) == "row" or not rows:
            rows.append([i])
        else:
            rows[-1].append(i)

    cells: list[DetectedCell] = []
    for r_idx, line_idxs in enumerate(rows):
        head = page.lines[line_idxs[0]]
        head_cols = _line_columns(head, bounds) or []
        row_start = head.char_start
        row_end = page.lines[line_idxs[-1]].char_end
        # Boundary char position of each column present in the head line.
        col_boundary: dict[int, int] = {}
        for w, c in zip(head.words, head_cols, strict=True):
            col_boundary.setdefault(c, w.char_start)
        present = sorted(col_boundary)
        if not present or present[0] != 0:
            # Not a clean row (no first-column anchor); skip cell emission for it
            # by folding the whole row into a single col-0 cell span so tiling
            # still holds.
            cells.append(
                DetectedCell(
                    row=r_idx,
                    col=0,
                    text=_row_text(page, line_idxs, bounds, {0}),
                    char_start=row_start,
                    char_end=row_end,
                )
            )
            continue
        # Ordered boundaries → contiguous cell spans; last column runs to row_end.
        for k, c in enumerate(present):
            span_start = row_start if k == 0 else col_boundary[c]
            span_end = col_boundary[present[k + 1]] if k + 1 < len(present) else row_end
            cells.append(
                DetectedCell(
                    row=r_idx,
                    col=c,
                    text=_column_text(
                        page, line_idxs, bounds, c, last=k + 1 == len(present)
                    ),
                    char_start=span_start,
                    char_end=span_end,
                )
            )
    return cells, len(rows)


def _spans_tile(
    page: ExtractedPage,
    cells: tuple[DetectedCell, ...] | list[DetectedCell],
    start: int,
    end: int,
) -> bool:
    """True iff *cells* tile ``[lines[start].start, lines[end].end)`` cleanly:
    each span non-empty, adjacent within a row (gap 0) or split by one "\\n" at a
    row boundary (gap 1), covering the whole range with no overlap."""
    lo = page.lines[start].char_start
    hi = page.lines[end].char_end
    cursor = lo
    for c in sorted(cells, key=lambda c: c.char_start):
        if c.char_start not in (cursor, cursor + 1) or c.char_start >= c.char_end:
            return False
        cursor = c.char_end
    return cursor == hi


def _dehyphen(acc: str, nxt: str) -> str:
    if acc.endswith("-") and not acc.endswith(("--", "- ")):
        return acc[:-1] + nxt
    return f"{acc} {nxt}" if acc else nxt


def _column_text(
    page: ExtractedPage,
    line_idxs: list[int],
    bounds: list[float],
    col: int,
    *,
    last: bool,
) -> str:
    """Text of column *col* across a row's lines (continuations fold into last)."""
    out = ""
    for li in line_idxs:
        ln = page.lines[li]
        cols = _line_columns(ln, bounds) or []
        for w, c in zip(ln.words, cols, strict=True):
            if c == col or (last and c > col):
                out = _dehyphen(out, w.text)
    return out


def _row_text(
    page: ExtractedPage, line_idxs: list[int], bounds: list[float], _cols: set[int]
) -> str:
    out = ""
    for li in line_idxs:
        for w in page.lines[li].words:
            out = _dehyphen(out, w.text)
    return out
