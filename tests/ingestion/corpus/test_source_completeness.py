"""Authoritative-source completeness proof tests — Issue 5c, Component A, PR #134.

The completeness proof binds the ordered per-page extraction *geometry* (not just
page text), so a geometry-only change — a moved coordinate, a resized font, a
shifted word span, an added/removed rectangle — that leaves the page text
unchanged still fails authoritative completeness (R15 F2). It could otherwise
silently alter headings and table cells while passing the proof.

These assert about the PDF *extraction*, not about the retired transform's
corpus, and ``finalize_source_release`` still runs this proof on the pages its
citations point at -- so they take the source-built candidate's pages and stay
live. The quarantined product is the PDF-geometric transform, not the extractor
every path still depends on.
"""

from __future__ import annotations

import dataclasses

import pytest

from afterworlds.ingestion.corpus.source_completeness import (
    EXPECTED_PAGE_COUNT,
    verify_source_completeness,
)


def test_clean_pages_pass_completeness(source_candidate):
    assert verify_source_completeness(source_candidate.pages) == ()
    assert len(source_candidate.pages) == EXPECTED_PAGE_COUNT


def _pages_with_first_line_replaced(pages, **line_fields):
    """Return a copy of *pages* with page[0]'s first line mutated (text kept)."""
    pg = pages[0]
    new_line = dataclasses.replace(pg.lines[0], **line_fields)
    new_pg = dataclasses.replace(pg, lines=(new_line, *pg.lines[1:]))
    return [new_pg, *pages[1:]]


def test_moved_line_coordinate_fails_completeness(source_candidate):
    pages = _pages_with_first_line_replaced(
        source_candidate.pages, top=source_candidate.pages[0].lines[0].top + 5.0
    )
    failures = verify_source_completeness(pages)
    assert any("extraction hash" in f for f in failures)


def test_resized_font_fails_completeness(source_candidate):
    pages = _pages_with_first_line_replaced(
        source_candidate.pages, size=source_candidate.pages[0].lines[0].size + 3.0
    )
    assert any("extraction hash" in f for f in verify_source_completeness(pages))


def test_shifted_word_span_fails_completeness(source_candidate):
    pg = source_candidate.pages[0]
    line = pg.lines[0]
    w0 = line.words[0]
    moved_word = dataclasses.replace(w0, x0=w0.x0 + 4.0)  # text unchanged
    new_line = dataclasses.replace(line, words=(moved_word, *line.words[1:]))
    pages = [
        dataclasses.replace(pg, lines=(new_line, *pg.lines[1:])),
        *source_candidate.pages[1:],
    ]
    # page text is identical; only word geometry changed.
    assert pages[0].canonical_text() == pg.canonical_text()
    assert any("extraction hash" in f for f in verify_source_completeness(pages))


@pytest.mark.parametrize("mutation", ["add", "remove", "move"])
def test_rectangle_change_fails_completeness(source_candidate, mutation):
    # Find a page that actually has rects so add/remove/move is meaningful.
    pg = next(p for p in source_candidate.pages if p.rects)
    idx = source_candidate.pages.index(pg)
    if mutation == "add":
        rects = (*pg.rects, dataclasses.replace(pg.rects[0], x0=pg.rects[0].x0 + 1.0))
    elif mutation == "remove":
        rects = pg.rects[1:]
    else:  # move
        rects = (
            dataclasses.replace(pg.rects[0], top=pg.rects[0].top + 2.0),
            *pg.rects[1:],
        )
    new_pg = dataclasses.replace(pg, rects=rects)
    pages = [*source_candidate.pages[:idx], new_pg, *source_candidate.pages[idx + 1 :]]
    assert pages[idx].canonical_text() == pg.canonical_text()  # text unchanged
    assert any("extraction hash" in f for f in verify_source_completeness(pages))
