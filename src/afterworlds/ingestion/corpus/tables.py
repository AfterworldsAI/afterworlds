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

Per-page detection consumes a **maximal contiguous run** of table-aligned lines
within the rect y-band (in extraction/flow order), so a segment maps to a
contiguous ``page.lines`` index range and its cell spans form one contiguous char
range. On-page row trimming drops any adjacent-column prose the band still admits
at the run boundary; a region that does not form a clean run is left to normal
paragraph segmentation — the tiling invariant is never sacrificed for fidelity.

:func:`assemble_tables` then links per-page segments into **cross-page logical
tables** (R15 F3): the geometrically lowest table on page ``N`` continues into the
geometrically highest table on page ``N+1`` iff they share column count and
normalized header. A logical table has a stable id (from its first segment),
continuous logical row numbering that does not restart at a page boundary, and
retains a repeated continuation header (flagged ``is_continuation_header``,
sharing logical row 0) without double-counting it as a data row.
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

    def header(self) -> tuple[str, ...]:
        """Normalized row-0 cell texts — the cross-page continuation key."""
        return tuple(compact(c.text) for c in self.cells if c.row == 0)


@dataclass(frozen=True)
class AssembledCell:
    """A cell with cross-page logical coordinates (Component F, R15 F3).

    ``logical_row`` continues across page segments and does not restart at a page
    boundary; a repeated continuation header keeps ``logical_row == 0`` (shared
    with the original header) and ``is_continuation_header`` set, so it is retained
    with its own page locator but never counted as a new data row.
    """

    logical_row: int
    col: int
    is_continuation_header: bool
    text: str
    char_start: int
    char_end: int


@dataclass(frozen=True)
class TableSegment:
    """One page's portion of a logical (possibly page-spanning) table."""

    logical_table_id: str
    segment_index: int  # 0 = first page, 1+ = continuation
    printed_page: int
    page_index: int
    start_line: int  # inclusive index into that page's lines
    end_line: int  # inclusive
    column_count: int
    is_continuation: bool  # segment_index > 0
    cells: tuple[AssembledCell, ...]


@dataclass(frozen=True)
class LogicalTable:
    """A logical table spanning one or more page segments with a stable identity.

    The identity is derived from the *first* segment's page + normalized header +
    column count, so continuation segments on later pages share it. Every source
    occurrence is retained (including a repeated continuation header); logical row
    numbering is continuous across segments.
    """

    logical_table_id: str
    header: tuple[str, ...]
    column_count: int
    logical_row_count: int
    segments: tuple[TableSegment, ...]

    @property
    def printed_pages(self) -> tuple[int, ...]:
        return tuple(s.printed_page for s in self.segments)


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


@dataclass(frozen=True)
class DetectionCoverage:
    """Per-page tally of rect anchors vs. tables emitted vs. dropped-to-paragraph.

    Detection deliberately falls back to normal paragraph segmentation for a
    candidate region it cannot cleanly reconstruct (no valid line run, inverted/
    overlapping spans, or a cell that isn't on the page — typically a shaded
    *prose* region spanning both body columns, not a real table). Surfacing these
    counts keeps the fallback explicit rather than a silent cap (PR #134).
    """

    anchors: int
    emitted: int
    dropped_no_run: int  # no clean contiguous row run (or no cells)
    dropped_span_invalid: int  # inverted/overlapping cell spans
    dropped_off_page: int  # a reconstructed cell isn't on the page


def _detect(page: ExtractedPage) -> tuple[tuple[DetectedTable, ...], DetectionCoverage]:
    """Reconstruct tables and tally detection coverage in one pass."""
    anchors = _rect_column_anchors(page.rects)
    tables: list[DetectedTable] = []
    used_lines: set[int] = set()
    no_run = span_bad = off_page = 0
    if anchors:
        page_compact = compact(page.canonical_text())
        for ai, bounds in enumerate(anchors):
            # y-band = vertical extent of the shaded rects whose left edge belongs
            # to this anchor's signature (padded to catch header + trailing rows).
            sig = set(bounds[:-1])
            rect_ys = [r.top for r in page.rects if r.x0 in sig] + [
                r.bottom for r in page.rects if r.x0 in sig
            ]
            if not rect_ys:
                no_run += 1
                continue
            lo, hi = _band(rect_ys)
            col_count = len(bounds) - 1
            run = _maximal_run(page, bounds, lo, hi, used_lines)
            if run is None:
                no_run += 1
                continue
            start, end = run
            rows = _group_rows(page, bounds, start, end)
            # On-page row trimming: greedy growth can swallow adjacent-column prose
            # at the run's top/bottom. Drop off-page boundary rows (they are the
            # swallowed prose) so those lines fall back to paragraph segmentation,
            # keeping the valid table core. A table's own on-page title/header row
            # is retained; an interior off-page row (a genuine mis-reconstruction)
            # still drops the whole table.
            kept, interior_bad = _trim_offpage_rows(page, bounds, rows, page_compact)
            if interior_bad:
                off_page += 1
                continue
            if not kept:
                no_run += 1
                continue
            cells, row_count = _build_cells(page, bounds, kept)
            if not cells:
                no_run += 1
                continue
            t_start, t_end = kept[0][0], kept[-1][-1]
            # Span-validity: cells must tile the table's char range monotonically —
            # adjacent within a row (gap 0), one "\n" between rows (gap 1). A
            # spanning title/mis-aligned header yields inverted/overlapping spans;
            # discard so those lines fall back to paragraphs and page tiling stays
            # disjoint+exhaustive.
            if not _spans_tile(page, cells, t_start, t_end):
                span_bad += 1
                continue
            table_id = content_id(
                "table",
                page.printed_page,
                ai,
                col_count,
                page.lines[t_start].char_start,
            )
            tables.append(
                DetectedTable(
                    table_id=table_id,
                    printed_page=page.printed_page,
                    start_line=t_start,
                    end_line=t_end,
                    column_count=col_count,
                    row_count=row_count,
                    cells=tuple(cells),
                )
            )
            used_lines.update(range(t_start, t_end + 1))
    tables.sort(key=lambda t: t.start_line)
    coverage = DetectionCoverage(
        anchors=len(anchors),
        emitted=len(tables),
        dropped_no_run=no_run,
        dropped_span_invalid=span_bad,
        dropped_off_page=off_page,
    )
    return tuple(tables), coverage


def detect_page_tables(page: ExtractedPage) -> tuple[DetectedTable, ...]:
    """Reconstruct every rect-anchored table on *page* as contiguous line runs."""
    return _detect(page)[0]


def table_detection_coverage(page: ExtractedPage) -> DetectionCoverage:
    """The rect-anchor → emitted-table → dropped-to-paragraph tally for *page*."""
    return _detect(page)[1]


# A section/subsection/entry heading font floor for the cross-page continuation
# guard: above running-header/body size (~9-11pt) so class/section headings (14pt+
# — e.g. "Cleric Spell List", "Paladin Subclass") register while body text does not.
_SECTION_HEADING_SIZE = 12.0
# Running header/footer lines sit in the extreme top/bottom margins; the continuation
# guard ignores anything above this top margin so they never count as a heading.
_TOP_MARGIN = 40.0


def _has_heading_above(page: ExtractedPage, start_line: int) -> bool:
    """True iff a section heading sits physically above line *start_line* on *page*.

    Signals that the line begins a new section rather than continuing a table from
    the previous page (the cross-page false-merge guard). Ignores the top-margin
    running header.
    """
    seg_top = page.lines[start_line].top
    return any(
        ln.size >= _SECTION_HEADING_SIZE and _TOP_MARGIN < ln.top < seg_top
        for ln in page.lines
    )


def _logical_table_id(first: DetectedTable) -> str:
    """Stable logical id from the first segment's page + header + column count."""
    return content_id(
        "logical_table", first.printed_page, first.column_count, *first.header()
    )


def _assemble_segment(
    logical_id: str,
    segment_index: int,
    table: DetectedTable,
    page_index: int,
    header: tuple[str, ...],
    next_data_row: int,
) -> tuple[TableSegment, int]:
    """Build a TableSegment with continuous logical rows; return it + the updated
    running data-row counter.

    Row 0 is the header on the first segment, or a *repeated continuation header*
    on a later segment iff its normalized row-0 matches the logical header — in
    which case it keeps ``logical_row == 0`` and is flagged, neither discarded nor
    counted as a data row. Every other row is a data row that continues the
    running logical-row counter across the page boundary.
    """
    row0_is_header = segment_index == 0 or table.header() == header
    # Map each page-local row index to a logical row.
    logical_of_row: dict[int, tuple[int, bool]] = {}
    running = next_data_row
    for r in range(table.row_count):
        if r == 0 and row0_is_header:
            logical_of_row[r] = (0, segment_index > 0)
        else:
            logical_of_row[r] = (running, False)
            running += 1
    cells = tuple(
        AssembledCell(
            logical_row=logical_of_row[c.row][0],
            col=c.col,
            is_continuation_header=logical_of_row[c.row][1],
            text=c.text,
            char_start=c.char_start,
            char_end=c.char_end,
        )
        for c in table.cells
    )
    segment = TableSegment(
        logical_table_id=logical_id,
        segment_index=segment_index,
        printed_page=table.printed_page,
        page_index=page_index,
        start_line=table.start_line,
        end_line=table.end_line,
        column_count=table.column_count,
        is_continuation=segment_index > 0,
        cells=cells,
    )
    return segment, running


def assemble_tables(pages: list[ExtractedPage]) -> tuple[LogicalTable, ...]:
    """Assemble per-page detected tables into cross-page logical tables (R15 F3).

    Deterministic linking rule: the **first** table on page ``N+1`` continues the
    **last** table on page ``N`` iff they share column count and normalized header
    (row-0 cell texts). Continuation keys on header + structure, never on column
    x-positions — a table legitimately shifts body column between pages (the
    Actions table is the right body column on page 9, the left on page 10). Logical
    row numbering is continuous across segments; a repeated continuation header is
    retained and flagged, not double-counted.
    """
    # Accumulate segments per logical id in page order.
    segments_by_id: dict[str, list[TableSegment]] = {}
    header_by_id: dict[str, tuple[str, ...]] = {}
    running_by_id: dict[str, int] = {}
    order: list[str] = []  # logical ids in first-seen order

    # The logical table whose last segment was the last table on the previous
    # page — the only continuation candidate for the next page's first table.
    open_id: str | None = None

    for page in pages:
        tables = detect_page_tables(page)  # sorted by start_line (flow order)
        if not tables:
            open_id = None
            continue

        # Geometric top/bottom (flow order != y order on two-column pages): only
        # the page's geometrically lowest table can continue onto the next page,
        # and only the next page's geometrically highest table can be that
        # continuation. The page-9 Actions fragment is at the page bottom but has a
        # smaller flow index than the top-of-page Skills table, so keying on flow
        # order would miss the 9→10 continuation.
        def _top_y(t: DetectedTable, page: ExtractedPage = page) -> float:
            return page.lines[t.start_line].top

        def _bottom_y(t: DetectedTable, page: ExtractedPage = page) -> float:
            return page.lines[t.end_line].top

        top_table = min(tables, key=_top_y)
        bottom_table = max(tables, key=_bottom_y)
        lid_by_table: dict[int, str] = {}
        for table in tables:
            continues = (
                table is top_table
                and open_id is not None
                and header_by_id[open_id] == table.header()
                and segments_by_id[open_id][-1].column_count == table.column_count
                # ...and no section heading governs the continuation. Tables that
                # merely share a column header across a section break (every spell
                # list is `spell/school/special`; the level/class lives in a
                # heading above the table) must NOT merge — a heading physically
                # above the continuation segment means it begins a new section, not
                # a continuation of the previous page's table (R15 F3 false-merge
                # guard).
                and not _has_heading_above(page, table.start_line)
            )
            if continues:
                assert open_id is not None
                lid = open_id
                segment_index = len(segments_by_id[lid])
                segment, running_by_id[lid] = _assemble_segment(
                    lid,
                    segment_index,
                    table,
                    page.page_index,
                    header_by_id[lid],
                    running_by_id[lid],
                )
                segments_by_id[lid].append(segment)
            else:
                lid = _logical_table_id(table)
                # Distinct concurrent logical tables could theoretically collide on
                # (page, header, col count); disambiguate by start line so each gets
                # a distinct id.
                if lid in segments_by_id:
                    lid = content_id("logical_table", lid, table.start_line)
                header = table.header()
                header_by_id[lid] = header
                segment, running_by_id[lid] = _assemble_segment(
                    lid, 0, table, page.page_index, header, 1
                )
                segments_by_id[lid] = [segment]
                order.append(lid)
            lid_by_table[id(table)] = lid
        open_id = lid_by_table[id(bottom_table)]

    return tuple(
        LogicalTable(
            logical_table_id=lid,
            header=header_by_id[lid],
            column_count=segments_by_id[lid][0].column_count,
            logical_row_count=running_by_id[lid],
            segments=tuple(segments_by_id[lid]),
        )
        for lid in order
    )


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

    def in_band(i: int) -> bool:
        return lo <= page.lines[i].top <= hi

    # Grow a contiguous block of grid-fitting lines outward from the seed, staying
    # within the rect-anchored y-band. Adjacent-column *prose* above/below the
    # shaded region also fits the column grid *and* often reconstructs to on-page
    # text (so on-page trimming alone can't reject it); the band is what keeps it
    # out. The cost is that a colored title bar sitting well above the column-
    # header row (e.g. page-7 "Attack Roll Abilities", 27pt above the first shaded
    # rect) falls to a caption/paragraph leaf rather than a table row — an accepted
    # boundary (captions are inventoried as paragraph leaves; see the R15 log).
    # On-page row trimming (:func:`_detect`) then removes any residual boundary
    # prose the band still admits.
    s = seed
    while (
        s - 1 >= 0
        and s - 1 not in used
        and in_band(s - 1)
        and _line_kind(page.lines[s - 1], bounds)
    ):
        s -= 1
    e = seed
    while (
        e + 1 < n
        and e + 1 not in used
        and in_band(e + 1)
        and _line_kind(page.lines[e + 1], bounds)
    ):
        e += 1
    # Trim leading continuation lines so the run starts at a real row.
    while s <= e and _line_kind(page.lines[s], bounds) != "row":
        s += 1
    if s > e:
        return None
    return s, e


def _group_rows(
    page: ExtractedPage, bounds: list[float], start: int, end: int
) -> list[list[int]]:
    """Group the run's line indices into rows: a ``"row"`` line starts a new row;
    a ``"cont"`` (wrapped continuation) line folds into the current row."""
    rows: list[list[int]] = []
    for i in range(start, end + 1):
        if _line_kind(page.lines[i], bounds) == "row" or not rows:
            rows.append([i])
        else:
            rows[-1].append(i)
    return rows


def _trim_offpage_rows(
    page: ExtractedPage,
    bounds: list[float],
    rows: list[list[int]],
    page_compact: str,
) -> tuple[list[list[int]], bool]:
    """Trim off-page rows from the run's top and bottom; report interior badness.

    Returns ``(kept_rows, interior_bad)``. A row is off-page iff any of its
    reconstructed cells' text is not on the page (the signature of swallowed
    adjacent-column prose). Contiguous off-page rows at either end are dropped;
    if an *interior* row is off-page after trimming, the whole table is a genuine
    mis-reconstruction (``interior_bad = True``) and is discarded by the caller.
    """

    def row_on_page(row: list[int]) -> bool:
        cells, _ = _build_cells(page, bounds, [row])
        return all(compact(c.text) in page_compact for c in cells)

    on = [row_on_page(r) for r in rows]
    a = 0
    while a < len(rows) and not on[a]:
        a += 1
    b = len(rows) - 1
    while b >= a and not on[b]:
        b -= 1
    if a > b:
        return [], False
    return rows[a : b + 1], not all(on[a : b + 1])


def _build_cells(
    page: ExtractedPage, bounds: list[float], rows: list[list[int]]
) -> tuple[list[DetectedCell], int]:
    """Partition each row's char span into per-column cell sub-spans.

    *rows* is the grouped line-index list (:func:`_group_rows`), possibly already
    trimmed of off-page boundary rows. Each row's ``[row_start.char_start,
    row_end.char_end)`` span is partitioned at the char position of the first word
    of each column>0 in the row-start line, so the cells exactly tile the row (no
    gap/overlap). Rows are renumbered ``0..len(rows)-1``.
    """
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
