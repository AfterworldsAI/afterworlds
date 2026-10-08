"""Official-page citations for source units — CRD Issue 5c/5d clean restart.

The source qualification cuts every snapshot file into contiguous
per-official-page regions (:func:`community_tokens.partition`): a position is
labelled only by a window unique to one official page, anchors that contradict
document order are dropped, and the rest inherit from the nearest kept anchor.
That partition makes "every snapshot character belongs to exactly one official
page" true, but it labels *positions*, and a window's label lands where the
window starts. So a window that begins in the last characters of one unit
labels that unit with the next unit's page, and a unit the document prints on
the page before or after its neighbours loses its own anchors as out of order.

A unit is therefore cited by its own wording first, and by the partition only
when its wording cannot place it. Each citation records which of these
established it, and nothing below claims more than that mechanism shows.

* ``located`` — the unit's whole compacted text is printed exactly once in the
  official page stream and is at least a window long, or it has exactly one
  printing within a page of the kept anchors bounding the unit (and, if the
  text is repeated, that printing lies inside them). Its pages are the pages
  that printing covers, so a multi-page unit still cites every page.
* ``placed`` — the text cannot be located, no window inside the unit anchors,
  and exactly one page between two differing bounding anchors carries every
  one of its tokens.
* ``anchored`` — otherwise, the partition's pages over the unit's span, with a
  kept unique window lying *wholly* inside the unit. A window that crosses the
  unit's boundary never counts.
* ``inherited`` — otherwise, the partition's pages by document order alone.
  Repeated wording that the bounds cannot separate stays here rather than
  acquiring one printing's page.
* ``unresolved`` — no position in the file anchored, so there is no page.

``located`` is a text match and ``placed`` a bounded token fit; ``anchored`` and
``inherited`` are inferred from the partition. None of them is a proof that the
page is right, and the report counts each separately so a consumer can weigh them.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from afterworlds.ingestion.corpus.pdf_source import ExtractedPage
from afterworlds.ingestion.corpus.source_units import SourceStructure
from afterworlds.ingestion.source.community_compare import (
    FRONT_MATTER,
    WINDOW,
    markdown_text,
    page_text,
)
from afterworlds.ingestion.source.community_tokens import (
    label_positions,
    normalized,
    tokens,
    window_pages,
)

#: Partition pages, with a kept unique window wholly inside the unit.
ANCHORED = "anchored"
#: Partition pages by document order alone.
INHERITED = "inherited"
#: No position in the whole file anchored, so there is no page to inherit.
UNRESOLVED = "unresolved"
#: The unit's whole text is printed on these pages.
LOCATED = "located"
#: The only bounded page carrying every token of the unit.
PLACED = "placed"


class CitationError(RuntimeError):
    """A unit could not be cited to any official page."""


@dataclass(frozen=True)
class UnitCitation:
    """One unit's official pages and how firmly they were established."""

    unit_index: int
    pages: tuple[int, ...]
    anchor: str

    @property
    def locator_value(self) -> str:
        return page_locator(self.pages)


def page_locator(pages: tuple[int, ...]) -> str:
    """Format official pages the way a citation prints them.

    One formatter, used by the build, by the persisted locator and by the
    verification that re-derives it, so the three cannot drift apart.
    """
    if not pages:
        return ""
    if len(pages) == 1:
        return f"p. {pages[0]}"
    if pages == tuple(range(pages[0], pages[-1] + 1)):
        return f"pp. {pages[0]}-{pages[-1]}"
    return "pp. " + ", ".join(str(p) for p in pages)


def cite_units(
    structure: SourceStructure,
    sources: dict[str, str],
    pages: list[ExtractedPage],
    *,
    window: int = WINDOW,
) -> tuple[UnitCitation, ...]:
    """Cite every unit to its official pages, as the module docstring describes."""
    normal = {p.printed_page: normalized(page_text(p)) for p in pages}
    stream = _PageStream(pages)
    index = window_pages(normal, window)
    citations: list[UnitCitation] = []
    for file_index, (_file, text) in enumerate(sources.items()):
        unit_slots = [
            (i, u) for i, u in enumerate(structure.units) if u.file_index == file_index
        ]
        if not unit_slots:
            continue
        unit_text = normalized(markdown_text(text))
        labels, anchored = label_positions(unit_text, index, window)
        kept = [
            page if hit else None for page, hit in zip(labels, anchored, strict=True)
        ]
        for slot, unit in unit_slots:
            start, end = unit.compact_start, unit.compact_end
            citations.append(
                _cite_one(
                    slot,
                    unit.content,
                    unit_text.compact[start:end],
                    labels[start:end],
                    certified=any(
                        p is not None
                        for p in kept[start : max(start, end - window + 1)]
                    ),
                    before=next(
                        (p for p in reversed(kept[:start]) if p is not None), None
                    ),
                    after=next((p for p in kept[end:] if p is not None), None),
                    stream=stream,
                    window=window,
                )
            )
    return tuple(sorted(citations, key=lambda c: c.unit_index))


class _PageStream:
    """Every official page's compact text, concatenated in document order."""

    def __init__(self, pages: list[ExtractedPage]) -> None:
        self.numbers = [p.printed_page for p in pages]
        parts = [normalized(page_text(p)).compact for p in pages]
        self.bounds: list[tuple[int, int]] = []
        at = 0
        for part in parts:
            self.bounds.append((at, at + len(part)))
            at += len(part)
        self.text = "".join(parts)
        self.tokens = {p.printed_page: tokens(page_text(p)) for p in pages}

    def printings(self, wording: str) -> set[tuple[int, ...]]:
        """The run of pages each printing of ``wording`` covers."""
        found: set[tuple[int, ...]] = set()
        at = self.text.find(wording)
        while at >= 0:
            end = at + len(wording)
            found.add(
                tuple(
                    n
                    for n, (s, e) in zip(self.numbers, self.bounds, strict=True)
                    if s < end and at < e
                )
            )
            at = self.text.find(wording, at + 1)
        return found


def _cite_one(
    slot: int,
    content: str,
    wording: str,
    span_labels: list[int | None],
    *,
    certified: bool,
    before: int | None,
    after: int | None,
    stream: _PageStream,
    window: int,
) -> UnitCitation:
    printings = stream.printings(wording) if wording else set()
    low = before if before is not None else -1
    high = after if after is not None else max(stream.numbers, default=0) + 1

    def within(run: tuple[int, ...], slack: int) -> bool:
        return low - slack <= run[0] and run[-1] <= high + slack

    # ponytail: one page of slack around the bounds admits the layout's own
    # relocations (a sidebar or feature set on the facing page); a printing
    # further away is not adopted and the unit keeps its partition pages.
    near = [run for run in printings if within(run, 1)]
    if len(printings) == 1 and len(wording) >= window:
        return UnitCitation(slot, next(iter(printings)), LOCATED)
    if len(near) == 1 and (len(printings) == 1 or within(near[0], 0)):
        return UnitCitation(slot, near[0], LOCATED)

    seen: list[int] = []
    for page in span_labels:
        if page is not None and page not in seen:
            seen.append(page)
    if not seen:
        return UnitCitation(slot, (), UNRESOLVED)
    if certified:
        return UnitCitation(slot, tuple(seen), ANCHORED)
    if before is not None and after is not None and before != after:
        wanted = tokens(markdown_text(content))
        fits = [
            page
            for page in range(min(before, after), max(before, after) + 1)
            if wanted and not wanted - stream.tokens.get(page, Counter())
        ]
        if len(fits) == 1:
            return UnitCitation(slot, (fits[0],), PLACED)
    return UnitCitation(slot, tuple(seen), INHERITED)


@dataclass(frozen=True)
class CitationReport:
    """Every citation counted by the mechanism that established it."""

    units: int
    located: int
    placed: int
    anchored: int
    inherited: int
    unresolved: tuple[int, ...]
    multi_page_units: int
    cited_pages: tuple[int, ...]
    uncited_body_pages: tuple[int, ...]

    @property
    def resolved(self) -> bool:
        return not self.unresolved and not self.uncited_body_pages

    def payload(self) -> dict[str, object]:
        return {
            "units": self.units,
            "located": self.located,
            "placed": self.placed,
            "anchored": self.anchored,
            "inherited": self.inherited,
            "statuses_are": (
                "the mechanism that established each citation, not a proof it "
                "is right. located: the unit's whole text is printed there; "
                "placed: the only bounded page carrying all its tokens; "
                "anchored: the partition's pages, with a unique window wholly "
                "inside the unit; inherited: the partition's pages by document "
                "order alone"
            ),
            "unresolved_units": list(self.unresolved),
            "multi_page_units": self.multi_page_units,
            "cited_official_pages": len(self.cited_pages),
            "uncited_body_pages": list(self.uncited_body_pages),
            "front_matter_pages": list(FRONT_MATTER),
        }


def build_report(
    citations: tuple[UnitCitation, ...], page_numbers: tuple[int, ...]
) -> CitationReport:
    """Summarize a citation pass, including the pages nothing cited."""
    cited = sorted({p for c in citations for p in c.pages})
    body = [p for p in page_numbers if p not in FRONT_MATTER]
    return CitationReport(
        units=len(citations),
        located=sum(1 for c in citations if c.anchor == LOCATED),
        placed=sum(1 for c in citations if c.anchor == PLACED),
        anchored=sum(1 for c in citations if c.anchor == ANCHORED),
        inherited=sum(1 for c in citations if c.anchor == INHERITED),
        unresolved=tuple(c.unit_index for c in citations if c.anchor == UNRESOLVED),
        multi_page_units=sum(1 for c in citations if len(c.pages) > 1),
        cited_pages=tuple(cited),
        uncited_body_pages=tuple(p for p in body if p not in set(cited)),
    )
