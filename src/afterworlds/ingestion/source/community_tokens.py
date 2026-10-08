"""Order-immune, sign-preserving comparison of the pinned snapshot with the PDF.

:mod:`community_compare` compacts whitespace and hyphens away, which makes it
blind to a sign and a spacing-only qualifier, and makes it report pure
reordering — a two-column table read column-down on one side and row-across on
the other — as a discrepancy. This module is its complement, not its
replacement:

* it keeps the minus sign apart from the dashes and tokenizes, so ``+2`` and
  ``-2`` are different tokens;
* it cuts the snapshot into per-official-page regions and compares *multisets*,
  so a reordering inside a page cancels and a changed number does not.

Neither pass clears anything on its own. The window pass sees order and misses
signs; this pass sees signs and misses order. A page is only quiet when both are
quiet, and quiet is where reading the document starts, not where it stops.

:func:`number_order` is the seam between them: it keeps this pass's tokens but
reads them in sequence, which is what tells a table row dropped under a header
the document repeats at a page break — the header's words still match, and the
multiset of the row's numbers cancels nowhere visible — from the reading-order
noise a two-column page produces on every page it touches.

Two deliberate repairs keep the pass honest rather than merely quiet:

``repair``
    The document sets headings and stat-block ability labels with a styled first
    letter, which the extractor emits as its own text run: ``STR`` arrives as
    ``s`` + ``tr``. The join is bounded by the snapshot region's own deficit, so
    it can only reunite fragments the region is actually short of. It has a known
    blind spot — two genuinely absent tokens whose concatenation is a word the
    region is short of would be joined and hidden — and the window pass, which is
    order-sensitive, is what covers it.

``slack``
    A snapshot has no page breaks, so a region boundary lands a line either side
    of the printed one. One page of slack absorbs that by cancelling a page's
    surplus against a neighbour's *matching deficit* — not by comparing against a
    neighbour's whole text, which would let its ordinary supply of a common word
    absorb a genuine omission. The comparison stays local to the page; it never
    falls back to the whole document.
"""

from __future__ import annotations

import re
import unicodedata
from bisect import bisect_right
from collections import Counter
from dataclasses import dataclass

from afterworlds.ingestion.corpus.pdf_source import ExtractedPage

from .community_compare import WINDOW, markdown_text, page_text

#: Folds the extractor and the snapshot onto one alphabet *without* collapsing
#: the minus sign into the dashes, which is exactly what ``policy.normalize``
#: does and why it cannot be reused here.
_FOLD = {
    "ﬀ": "ff",
    "ﬁ": "fi",
    "ﬂ": "fl",
    "ﬃ": "ffi",
    "ﬄ": "ffl",
    "‘": "'",
    "’": "'",
    "“": '"',
    "”": '"',
    "−": "-",  # minus sign onto hyphen-minus: the sign survives before a digit
    "–": "—",  # en dash onto em dash: a dash is punctuation, not a sign
}
_COMPACTABLE = re.compile(r"[\s\-—]")
#: A hyphen between two letters separates words. The document hyphenates
#: compounds the snapshot spaces or runs together — ``5-foot-radius`` against
#: ``5-foot radius`` — so joining across it would report the spacing as a
#: difference in both directions. Splitting is symmetric. A hyphen before a
#: digit is left alone: it is a sign, which is the point of this pass.
_LETTER_HYPHEN = re.compile(r"(?<=[A-Za-z])-[ ]?(?=[A-Za-z])")
_TOKEN = re.compile(r"[A-Za-z]+|[+-]?\d+|—|[.,:;()\"'/*%&!?]")
#: A split the extractor made, not one the document wrote. Either the fragments
#: were separated by a hyphen the renderer put at a line break, or the leading
#: fragment is the one-or-two-letter styled initial that opens a heading or a
#: stat-block ability label. Case is not the test — the document styles some of
#: those initials as lowercase (``d`` + ``ex``) — so length is, and the deficit
#: bound does the rest. Nothing else may be rejoined.
_STYLED = re.compile(r"[A-Za-z]{1,2}$")


def snorm(text: str) -> str:
    """Sign-preserving normalization: fold, NFKC, collapse whitespace.

    Case is kept, unlike ``policy.normalize``'s companion ``compact``. It is the
    only evidence that distinguishes the two ways this document splits a word: a
    styled capital, which the extractor emits as its own run (``Spellbook`` ->
    ``S`` + ``pellbook``), from an ordinary lowercase word that merely happens to
    sit next to another (``a long rest``). Rejoining the first is a repair;
    rejoining the second invents a word. Comparison case folds afterwards.
    """
    folded = "".join(_FOLD.get(ch, ch) for ch in text)
    return " ".join(unicodedata.normalize("NFKC", folded).split())


@dataclass(frozen=True)
class Normalized:
    """One unit of text in both representations, with an index between them."""

    strict: str
    compact: str
    #: ``compact[i]`` is ``strict[index[i]]``.
    index: tuple[int, ...]

    def slice(self, lo: int, hi: int) -> str:
        """Strict text for a compact span, both ends snapped to a word boundary.

        A page break falls wherever it falls, which — once whitespace is gone —
        is usually inside a word. Cutting there invents a fragment on one side
        and loses a whole word on the other. Snapping both ends rightwards keeps
        regions tiling without overlap: the word a boundary lands in belongs to
        the earlier region.
        """
        if not self.index:
            return ""
        lo = max(0, min(lo, len(self.index) - 1))
        hi = max(0, min(hi, len(self.index) - 1))
        start, end, size = self.index[lo], self.index[hi], len(self.strict)
        while 0 < start < size and not self.strict[start - 1].isspace():
            start += 1
        while end + 1 < size and not self.strict[end + 1].isspace():
            end += 1
        return self.strict[start : end + 1] if start <= end else ""


def normalized(raw: str) -> Normalized:
    """Normalize once and keep the compact-to-strict index."""
    strict = snorm(raw)
    compact, index = [], []
    for i, ch in enumerate(strict):
        if _COMPACTABLE.match(ch):
            continue
        compact.append(ch.lower())
        index.append(i)
    return Normalized(strict, "".join(compact), tuple(index))


def _sequence(text: str) -> tuple[list[str], list[bool]]:
    """Cased tokens, and for each whether it may be joined onto the one before it."""
    marked = _LETTER_HYPHEN.sub(" \x00", text)
    seq: list[str] = []
    joinable: list[bool] = [False]
    end = 0
    for match in _TOKEN.finditer(marked):
        if seq:
            between = marked[end : match.start()]
            joinable.append("\x00" in between or bool(_STYLED.match(seq[-1])))
        seq.append(match.group())
        end = match.end()
    return seq, joinable[: len(seq)]


def tokens(text: str) -> Counter[str]:
    """Word, signed-number, dash and punctuation multiset of normalized text."""
    return Counter(token.lower() for token in _sequence(text)[0])


def repair(text: str, theirs: Counter[str]) -> Counter[str]:
    """Token multiset of ``text`` with extractor-split words rejoined.

    A join needs three things at once: the split has to look like one the
    extractor made rather than one the document wrote (see ``_STYLED``), every
    piece after the first has to be marked joinable, and the counterpart region
    has to be short of the result. So the repair can neither invent a token beyond
    the deficit it is answering nor merge two words the document kept apart.
    """
    sequence, joinable = _sequence(text)
    folded = [token.lower() for token in sequence]
    deficit = theirs - Counter(folded)
    out: list[str] = []
    i = 0
    while i < len(sequence):
        joined = None
        for span in (3, 2):
            if i + span > len(sequence) or not all(joinable[i + 1 : i + span]):
                continue
            candidate = "".join(folded[i : i + span])
            if candidate.isalpha() and deficit.get(candidate, 0) > 0:
                joined = (candidate, span)
                break
        if joined is None:
            out.append(folded[i])
            i += 1
        else:
            out.append(joined[0])
            deficit[joined[0]] -= 1
            i += joined[1]
    return Counter(out)


@dataclass(frozen=True)
class PageTokens:
    """One official page measured against the snapshot region that carries it."""

    printed_page: int
    files: tuple[str, ...]
    spans: tuple[tuple[str, int, int], ...]
    pdf_tokens: int
    snapshot_tokens: int
    #: Tokens the page has that its region (widened by ``slack``) does not.
    pdf_only: Counter[str]
    #: Tokens the region has that the page and its neighbours do not.
    snapshot_only: Counter[str]

    @property
    def quiet(self) -> bool:
        return not self.pdf_only and not self.snapshot_only


def window_pages(pages: dict[int, Normalized], window: int) -> dict[str, set[int]]:
    index: dict[str, set[int]] = {}
    for page, unit in pages.items():
        text = unit.compact
        for i in range(len(text) - window + 1):
            index.setdefault(text[i : i + window], set()).add(page)
    return index


def _keep_in_order(labels: list[int | None]) -> int:
    """Drop anchors that contradict document order; return how many were dropped.

    A snapshot file transcribes the document front to back, so its page labels can
    only go up. An anchor that jumps backwards is a passage the document prints
    twice — the armor note that reappears in the glossary, a class spell list —
    whose wording happens to be unique to the *other* printing. Keeping the
    longest non-decreasing run of anchors and discarding the rest resolves that by
    position instead of by wording. If the assumption were wrong the kept run
    would be short, so the drop count is worth reporting.
    """
    anchored = [(i, page) for i, page in enumerate(labels) if page is not None]
    # Longest non-decreasing subsequence of the anchored page numbers.
    tails: list[int] = []
    tails_at: list[int] = []
    chain: list[int | None] = []
    for slot, (_i, page) in enumerate(anchored):
        at = bisect_right(tails, page)
        chain.append(tails_at[at - 1] if at else None)
        if at == len(tails):
            tails.append(page)
            tails_at.append(slot)
        else:
            tails[at] = page
            tails_at[at] = slot
    keep: set[int] = set()
    cursor: int | None = tails_at[-1] if tails_at else None
    while cursor is not None:
        keep.add(anchored[cursor][0])
        cursor = chain[cursor]
    dropped = 0
    for i, _page in anchored:
        if i not in keep:
            labels[i] = None
            dropped += 1
    return dropped


def label_positions(
    unit: Normalized, index: dict[str, set[int]], window: int
) -> tuple[list[int | None], list[bool]]:
    """Label every compact position of one file, and say which ones anchored.

    The second list marks the positions a window unique to one official page
    labelled directly and document order kept. Every other position inherits its
    page from the nearest anchor, which is a placement by position rather than by
    wording. The distinction is invisible in the partition — both kinds end up in
    a region — but a consumer citing a unit needs it: an inherited citation is
    correct by the file's order, not by anything the unit's own text proves, and
    that is exactly the reviewable exception a citation report must list.
    """
    text = unit.compact
    labels: list[int | None] = [None] * len(text)
    for i in range(len(text) - window + 1):
        pages = index.get(text[i : i + window])
        # Only a window unique to one official page may anchor. The document
        # repeats whole passages — a class's spell list, the ability-score-
        # improvement text — so a window carried by several pages says nothing
        # about which of them this position belongs to. Letting it guess assigns
        # a passage to a page fifty leaves away and then reports the whole
        # passage as a difference in both directions. Ambiguous positions inherit
        # from the nearest anchor instead.
        if pages and len(pages) == 1:
            labels[i] = next(iter(pages))
    _keep_in_order(labels)
    anchored = [page is not None for page in labels]
    for direction in (range(len(labels)), reversed(range(len(labels)))):
        running = None
        for i in direction:
            if labels[i] is None:
                labels[i] = running
            else:
                running = labels[i]
    return labels, anchored


def partition(
    pages: dict[int, Normalized],
    community: dict[str, Normalized],
    *,
    window: int = WINDOW,
) -> dict[int, list[tuple[str, int, int]]]:
    """Cut every snapshot file into contiguous per-official-page regions."""
    index = window_pages(pages, window)
    regions: dict[int, list[tuple[str, int, int]]] = {}
    for name, unit in community.items():
        labels, _anchored = label_positions(unit, index, window)
        if not labels:
            continue
        start, current = 0, labels[0]
        for i in range(1, len(labels)):
            if labels[i] == current:
                continue
            if current is not None:
                regions.setdefault(current, []).append((name, start, i - 1))
            start, current = i, labels[i]
        if current is not None:
            regions.setdefault(current, []).append((name, start, len(labels) - 1))
    return regions


def inventory(
    pages: list[ExtractedPage],
    community_raw: dict[str, str],
    *,
    window: int = WINDOW,
    slack: int = 1,
) -> list[PageTokens]:
    """Two-way per-page token comparison over the whole document."""
    normal = {p.printed_page: normalized(page_text(p)) for p in pages}
    snapshot = {n: normalized(markdown_text(t)) for n, t in community_raw.items()}
    regions = partition(normal, snapshot, window=window)

    region_tokens: dict[int, Counter[str]] = {}
    for page in normal:
        counted: Counter[str] = Counter()
        for name, lo, hi in regions.get(page, []):
            counted += tokens(snapshot[name].slice(lo, hi))
        region_tokens[page] = counted

    # The repair deficit is the page's own region first. Widening it to a
    # neighbour's whole text would let that neighbour's ordinary supply of a word
    # authorise a join here, and the join would then be reported as a difference
    # on both pages. But a word hyphen-broken across a printed page break has its
    # two halves on this page and its snapshot copy in the neighbour's region, so
    # a second round offers each page whatever its neighbours were left short of —
    # a small, specific set that cannot authorise anything else.
    page_repaired = {
        page: repair(normal[page].strict, region_tokens[page]) for page in normal
    }
    leftover = {p: region_tokens[p] - page_repaired[p] for p in normal}
    for page in normal:
        borrowed: Counter[str] = Counter()
        for offset in range(1, slack + 1):
            for other in (page - offset, page + offset):
                borrowed += leftover.get(other, Counter())
        if borrowed:
            page_repaired[page] = repair(
                normal[page].strict, region_tokens[page] + borrowed
            )

    pdf_only = {p: page_repaired[p] - region_tokens[p] for p in normal}
    snapshot_only = {p: region_tokens[p] - page_repaired[p] for p in normal}

    # A page's surplus cancels a neighbour's matching deficit and nothing else.
    # Widening the compared *text* by a page instead would let a neighbour's
    # ordinary supply of a common word absorb a genuine omission of it: a dropped
    # "or" would go unreported because the page next door has plenty. Netting the
    # residues keeps the cancellation to what a boundary slip actually looks like
    # — the same token short here and over next door.
    for page in sorted(normal):
        for offset in range(1, slack + 1):
            for other in (page - offset, page + offset):
                if other not in normal:
                    continue
                slipped = pdf_only[page] & snapshot_only[other]
                pdf_only[page] -= slipped
                snapshot_only[other] -= slipped
                slipped = snapshot_only[page] & pdf_only[other]
                snapshot_only[page] -= slipped
                pdf_only[other] -= slipped

    return [
        PageTokens(
            printed_page=page,
            files=tuple(sorted({s[0] for s in regions.get(page, [])})),
            spans=tuple(regions.get(page, [])),
            pdf_tokens=sum(page_repaired[page].values()),
            snapshot_tokens=sum(region_tokens[page].values()),
            pdf_only=pdf_only[page],
            snapshot_only=snapshot_only[page],
        )
        for page in sorted(normal)
    ]


@dataclass(frozen=True)
class PageNumbers:
    """One official page's numbers, in the order each side prints them."""

    printed_page: int
    pdf: tuple[str, ...]
    snapshot: tuple[str, ...]

    @property
    def same_order(self) -> bool:
        return self.pdf == self.snapshot


def numbers(text: str) -> tuple[str, ...]:
    """Just the numeric tokens, in order, signs kept."""
    return tuple(t for t in _sequence(text)[0] if t.lstrip("+-")[:1].isdigit())


def number_order(
    pages: list[ExtractedPage],
    community_raw: dict[str, str],
    *,
    window: int = WINDOW,
) -> list[PageNumbers]:
    """Per page, the sequence of numbers each side prints.

    :func:`inventory` compares multisets, which cancels a difference that stays
    on one page: two cells of a table row exchanged hold the same bag of
    numbers, and so does a row dropped under a header the document repeats at a
    page break while the header's own words go on matching. Reading the numbers
    *in order* separates those from each other and from ordinary reading-order
    noise, because most prose reordering carries no numbers at all.

    This is a reading aid, not a verdict: a two-column page legitimately reads
    in a different order on each side, so a page whose sequences differ has to
    be looked at rather than counted as wrong.
    """
    normal = {p.printed_page: normalized(page_text(p)) for p in pages}
    snapshot = {n: normalized(markdown_text(t)) for n, t in community_raw.items()}
    regions = partition(normal, snapshot, window=window)
    out = []
    for page in sorted(normal):
        theirs: tuple[str, ...] = ()
        for name, lo, hi in regions.get(page, []):
            theirs += numbers(snapshot[name].slice(lo, hi))
        out.append(
            PageNumbers(
                printed_page=page,
                pdf=numbers(normal[page].strict),
                snapshot=theirs,
            )
        )
    return out
