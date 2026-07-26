"""Deterministic table reconstruction oracles — Issue 5c, Component F, PR #134.

Exact ground-truth assertions on representative SRD tables (read off the actual
pages, not from what the extractor emits): the three-column Skills table on
printed page 9 and the page-spanning Actions table (page 9 → 10), including a
wrapped multi-line cell. A nonzero ``TABLE_CELL`` count is never treated as
proof; these pin identity, row/column position, and exact cell text, plus the
container relationships and the no-paragraph-overlap invariant.
"""

from __future__ import annotations

from afterworlds.ingestion.corpus.concordance import check_table_concordance
from afterworlds.ingestion.corpus.models import ContainerType, LeafType
from afterworlds.ingestion.corpus.tables import detect_page_tables


def _page(full_candidate, printed_page):  # type: ignore[no-untyped-def]
    return next(p for p in full_candidate.pages if p.printed_page == printed_page)


def _table_by_header(page, header):  # type: ignore[no-untyped-def]
    for t in detect_page_tables(page):
        if [c.text for c in t.cells if c.row == 0] == header:
            return t
    raise AssertionError(f"no table with header {header} on page {page.printed_page}")


def test_skills_table_reconstructs_three_columns_exactly(full_candidate):
    """Printed page 9 Skills table: 3 columns, header + 18 skill rows, exact
    cell identity/position/text for representative rows."""
    table = _table_by_header(
        _page(full_candidate, 9), ["Skill", "Ability", "Example Uses"]
    )
    assert table.column_count == 3
    assert table.row_count == 19  # header + 18 skills
    by_pos = {(c.row, c.col): c.text for c in table.cells}
    # Header
    assert by_pos[(0, 0)] == "Skill"
    assert by_pos[(0, 1)] == "Ability"
    assert by_pos[(0, 2)] == "Example Uses"
    # First data row
    assert by_pos[(1, 0)] == "Acrobatics"
    assert by_pos[(1, 1)] == "Dexterity"
    assert by_pos[(1, 2)] == (
        "Stay on your feet in a tricky situation, or perform an acrobatic stunt."
    )
    # A multi-word first-column cell (Sleight of Hand) stays one cell.
    assert any(c.col == 0 and c.text == "Sleight of Hand" for c in table.cells)
    # Each (row, col) occurs exactly once.
    positions = [(c.row, c.col) for c in table.cells]
    assert len(positions) == len(set(positions))


def _actions_logical_table(full_candidate):
    from afterworlds.ingestion.corpus.policy import compact
    from afterworlds.ingestion.corpus.tables import assemble_tables

    want = (compact("Action"), compact("Summary"))
    return next(lt for lt in assemble_tables(full_candidate.pages) if lt.header == want)


def test_actions_table_spans_pages_9_and_10_as_one_logical_table(full_candidate):
    """The Actions table continues from printed page 9 (header/Attack/Dash) to
    page 10 (Disengage…): one logical table, two segments sharing the logical
    identity, with continuous logical rows that do NOT restart at the page
    boundary and a repeated continuation header that is retained and flagged, not
    double-counted (R15 F3)."""
    lt = _actions_logical_table(full_candidate)
    assert lt.printed_pages == (9, 10)
    assert lt.column_count == 2
    assert len(lt.segments) == 2

    seg0, seg1 = lt.segments
    assert (
        seg0.printed_page == 9 and seg0.segment_index == 0 and not seg0.is_continuation
    )
    assert seg1.printed_page == 10 and seg1.segment_index == 1 and seg1.is_continuation

    def col0(seg):
        return {c.logical_row: c for c in seg.cells if c.col == 0}

    s0, s1 = col0(seg0), col0(seg1)
    # Page-9 segment: header (row 0) then Attack (1), Dash (2).
    assert s0[0].text == "Action" and not s0[0].is_continuation_header
    assert s0[1].text == "Attack"
    assert s0[2].text == "Dash"
    # Page-10 continuation: the repeated "Action" header keeps logical row 0 and
    # is flagged (retained, not a new data row); Disengage CONTINUES at row 3.
    assert s1[0].text == "Action" and s1[0].is_continuation_header
    assert s1[3].text == "Disengage"
    assert s1[4].text == "Dodge"
    # Every (segment, logical_row, col) occurrence is unique — nothing double-counted.
    occ = [
        (seg.segment_index, c.logical_row, c.col)
        for seg in lt.segments
        for c in seg.cells
    ]
    assert len(occ) == len(set(occ))


def test_no_cross_page_table_merges_across_a_section_heading(full_candidate):
    """A page-spanning link is only made when the continuation is genuinely the
    same table — never two tables that merely share a column header across a
    section break. Every spell list is ``spell/school/special``; the class/level
    lives in a heading above the table, so a continuation segment with any section
    heading physically above it would be a false merge (R15 F3 false-merge guard).
    """
    from afterworlds.ingestion.corpus.tables import (
        _has_heading_above,
        assemble_tables,
    )

    by_pp = {p.printed_page: p for p in full_candidate.pages}
    for lt in assemble_tables(full_candidate.pages):
        for seg in lt.segments[1:]:
            assert not _has_heading_above(by_pp[seg.printed_page], seg.start_line), (
                f"logical table {lt.printed_pages} continuation on page "
                f"{seg.printed_page} has a section heading above it (false merge)"
            )


def test_actions_wrapped_summary_folds_to_one_cell(full_candidate):
    """The Disengage summary wraps two visual lines but reconstructs as one
    de-hyphenated cell (continuation folded, not duplicated)."""
    lt = _actions_logical_table(full_candidate)
    seg1 = lt.segments[1]
    disengage_summary = next(
        c.text for c in seg1.cells if c.logical_row == 3 and c.col == 1
    )
    assert disengage_summary == (
        "Your movement doesn’t provoke Opportunity Attacks for the rest of the turn."
    )


def test_attack_roll_table_reconstructs_on_canary_page(full_candidate):
    """A third representative table (printed page 7, a version-canary page): the
    two-column attack-roll ability grid reconstructs from its column-header row
    down with exact header/row identity and text. (Its colored full-width title
    bar "Attack Roll Abilities" sits above the two-column shaded region and is
    inventoried as a caption/paragraph leaf, not a table row — see R15 log.)"""
    table = _table_by_header(_page(full_candidate, 7), ["Ability", "Attack Type"])
    assert table.column_count == 2
    by_pos = {(c.row, c.col): c.text for c in table.cells}
    assert by_pos[(0, 0)] == "Ability"
    assert by_pos[(0, 1)] == "Attack Type"
    assert by_pos[(1, 0)] == "Strength"
    assert by_pos[(1, 1)].startswith("Melee attack with a weapon")
    positions = [(c.row, c.col) for c in table.cells]
    assert len(positions) == len(set(positions))


def test_skills_table_container_nesting_and_cell_leaves(full_candidate):
    """The reconstructed Skills table is a TABLE container whose cell leaves are
    TABLE_CELL, carry the container in their path, and record row/col — proving
    the ledger records table identity/position and container relationships."""
    ledger = full_candidate.ledger
    # Find the Skills table container by its header label.
    skills = next(
        c
        for c in ledger.containers
        if c.container_type is ContainerType.TABLE
        and c.label.startswith("Skill | Ability | Example Uses")
    )
    cells = [lf for lf in ledger.leaves if lf.table_id == skills.container_id]
    assert cells, "expected TABLE_CELL leaves for the Skills table"
    for lf in cells:
        assert lf.leaf_type is LeafType.TABLE_CELL
        assert lf.table_row is not None and lf.table_col is not None
        assert skills.container_id in lf.container_path  # nested under the table
    # The table nests under a real section/subsection container (not the page).
    assert skills.parent_id is not None


def test_full_pdf_table_reconstruction_is_structurally_consistent(full_candidate):
    """Component E: every emitted table cell across the whole PDF is structurally
    consistent (unique row/col, in-range, non-empty) and on its page — verified
    from the reconstructed tables, independent of generated RuleChunks. The
    structural checks catch failure modes the detection filter does not itself
    guarantee, so this is not tautological."""
    result = check_table_concordance(full_candidate.pages)
    assert result.tables_checked > 0 and result.cells_checked > 0
    assert result.passed, (
        result.content_failures[:5],
        result.structural_failures[:5],
    )


def test_table_detection_coverage_is_reported_not_silently_capped(full_candidate):
    """Detection falls back to paragraph segmentation for candidate regions it
    cannot cleanly reconstruct (typically shaded prose spanning both body
    columns). Assert the fallback tally is surfaced and self-consistent, and that
    genuinely reconstructed tables dominate the discards (no silent cap)."""
    cov = check_table_concordance(full_candidate.pages).coverage
    assert cov["anchors"] == (
        cov["emitted"]
        + cov["dropped_no_run"]
        + cov["dropped_span_invalid"]
        + cov["dropped_off_page"]
    )
    assert cov["emitted"] > 0
    # Real tables outnumber the off-page (mixed-column prose) rejections.
    assert cov["emitted"] > cov["dropped_off_page"]


def test_table_cell_chars_have_no_paragraph_overlap(full_candidate):
    """No character owned by a TABLE_CELL leaf is also owned by a paragraph/list
    leaf on the same page — cells are not double-emitted as prose."""
    ledger = full_candidate.ledger
    # Group by page; table-cell char ranges must be disjoint from every other
    # leaf's range (the ledger partition test already proves global disjointness,
    # but this pins the table-vs-paragraph family specifically).
    by_page: dict[int, list] = {}
    for lf in ledger.leaves:
        by_page.setdefault(lf.page_index, []).append(lf)
    for leaves in by_page.values():
        cell_ranges = [
            (lf.char_start, lf.char_end)
            for lf in leaves
            if lf.leaf_type is LeafType.TABLE_CELL
        ]
        other_ranges = [
            (lf.char_start, lf.char_end)
            for lf in leaves
            if lf.leaf_type is not LeafType.TABLE_CELL
        ]
        for cs, ce in cell_ranges:
            for os_, oe in other_ranges:
                assert ce <= os_ or oe <= cs, "table cell overlaps a non-cell leaf"
