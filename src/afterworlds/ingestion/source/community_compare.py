"""Compare the pinned community Markdown against the official SRD 5.2.1 PDF.

Step 2 of the Recorded Owner Decision of 21 September 2026 requires the pinned
community snapshot to be checked against the official PDF over the whole
document before it can be used to build a fresh 5c corpus. This module is that
instrument. It decides nothing: it reports where official text is present in the
snapshot, where the snapshot carries text the document does not, and — explicitly
— what it cannot decide at all.

What it checks
--------------
Character-level containment of one source's text in the other's, after the
repository's frozen normalization (:func:`policy.compact`, which folds ligatures,
the minus sign and typographic punctuation, then removes whitespace and hyphens
and case-folds). Removing whitespace is what makes the comparison usable: the PDF
renders small-caps ability abbreviations as ``S tr``, hyphenates across line ends,
and flows two columns, and none of those survive as token boundaries.

What it cannot check
--------------------
**Characters the normalization removes.** Compaction is not lossless, and an
earlier version of this docstring wrongly claimed it was. ``compact`` folds the
minus sign to a hyphen and then removes hyphens, so ``modifier -2`` and
``modifier 2`` compact to the same string: a dropped or inverted sign is
invisible here. The same removal erases the boundary between a number and the
word beside it, so a differing footnote marker or qualifier adjacent to a value
can survive as a match. Signs, numbers and qualifiers are therefore an open
qualification item, not something a coverage fraction from this module clears.

**Whether a table cell is in the right row or column.** A window containing
``chainshirt1350lb.`` proves those characters are adjacent in both sources; it
does not prove the snapshot associates 13 with Chain Shirt's AC rather than its
cost. Every named check therefore reports ``table_association_checked: false``.

**Which record a passage belongs to.** Two adjacent stat blocks read as one
continuous stream after compaction, so nothing here distinguishes one creature's
trait from its neighbour's on the same spread.

Table-structure qualification is a later increment, and no result here may be
read as supplying it.

Noise floor
-----------
The two sources order the same text differently: the PDF flows a table header
straight on from the sentence above it, while the snapshot separates them with
markup. Where **one isolated** joint is the only difference, the sole unmatched
windows are those straddling it, so that run cannot exceed ``2 * WINDOW - 1``
characters. :data:`NOISE_FLOOR` is ``2 * WINDOW`` on that basis — derived from
the window size rather than tuned until the output looked acceptable.

The bound is not universal, and an earlier version of this docstring overstated
it. It holds for a single separated junction; several reordered joints within
``2 * WINDOW`` of each other merge their unmatched windows into one longer run,
and a genuine omission adjacent to a junction is likewise absorbed. So a run
below the floor is **unresolved, not harmless**: it is where this instrument
stops being able to tell its own reordering artefact from a real difference. Such
runs are inventoried by count and character total in the ``discrepancies`` block
and carried into full-source qualification; the verdict for a region holding only
sub-floor runs is ``below_floor_unresolved``, which is not a pass.

The Owner-supplied positive controls bound the artefact empirically -- their
longest runs are 93 and 60 characters, both exactly such junctions -- and the
tests re-measure them, so a degraded instrument fails a control instead of
quietly raising the floor.
"""

from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass
from importlib.metadata import version as _pkg_version
from pathlib import Path

from afterworlds.ingestion.corpus.pdf_source import (
    PDF_REPO_PATH,
    PDF_SHA256,
    ExtractedPage,
    extract_pages,
)
from afterworlds.ingestion.corpus.policy import NORMALIZATION_VERSION, compact

#: Pinned community snapshot, established by Step 2 of the Owner Decision.
PIN_DIR = "docs/sources/community/dnd-5e-srd-markdown"

#: Upstream files holding rules content. The snapshot also vendors ``LICENSE``,
#: ``README.md`` and ``CHANGELOG.md`` (upstream project material, not SRD text)
#: and this repository's own ``PINNED-SOURCE.md``/``source_pin.json``; comparing
#: those against the document would manufacture discrepancies out of files that
#: are not claiming to represent it.
CONTENT_FILES: tuple[str, ...] = (
    "animals.md",
    "character-creation.md",
    "character-origins.md",
    "classes.md",
    "equipment.md",
    "feats.md",
    "gameplay-toolbox.md",
    "magic-items.md",
    "monsters-A-Z.md",
    "monsters.md",
    "playing-the-game.md",
    "rules-glossary.md",
    "spells.md",
)

#: Compacted-character window length. At ~5.2 compacted characters per word this
#: is roughly a nine-word phrase: long enough that an incidental match is not
#: credible, short enough that one reworded clause does not mask the sentence
#: around it.
WINDOW = 48

#: Minimum affected-character length before an unmatched run is *reported* as a
#: discrepancy. Below it, a run is unresolved rather than cleared.
#:
#: Derived, not tuned. When both sides hold the same text but join it in a
#: different order — the PDF flows a table header straight on from the sentence
#: above it, the snapshot separates them — the only absent windows are those
#: straddling the joint, so a **single isolated** junction cannot exceed
#: ``2 * WINDOW - 1``. That is the whole of the derivation: it is not a proof that
#: every sub-floor run is an artefact, because two junctions closer together than
#: ``2 * WINDOW``, or an omission sitting beside one, merge into a longer run.
#: Runs below the floor are counted in the evidence rather than dropped, and
#: qualification has to read them. The Owner-supplied positive controls bound the
#: single-junction artefact empirically: their longest runs are 93 and 60
#: characters, both junctions of exactly this kind, and
#: :func:`positive_control_floor` re-measures it.
NOISE_FLOOR = 2 * WINDOW

#: Printed pages carrying no rules content the snapshot claims to represent:
#: the licence notice and the three-page table of contents with its dot leaders.
#: They are reported separately rather than counted as missing content, because
#: a snapshot of the rules is not deficient for lacking a page-number index.
FRONT_MATTER: tuple[int, ...] = (1, 2, 3, 4)

#: The independent review that closed the source boundary. Recorded, not
#: performed, here: the passes in this module are the evidence the review read.
#: "Qualified" is of these bytes against the official document. It is not rules
#: authority, and it is not a semantic acceptance of what the rules mean -- both
#: belong to the Rules Package, not to a source snapshot.
QUALIFICATION_REVIEW: dict[str, str] = {
    "artifact": "source-structure-final-review.md",
    "reviewed_head": "b70d016",
    "reviewer": "Codex (independent)",
    "scope": "the corrected bytes against the official PDF",
    "not_established": (
        "rules authority, semantic acceptance, or any claim about a corpus "
        "built from these bytes"
    ),
}

#: The running header/footer, which prints on every page and exists in no
#: Markdown file. Stripped once and reported as a systematic non-discrepancy
#: rather than 364 identical runs.
_RUNNING = re.compile(
    r"^(?:\d+ System Reference Document 5\.2\.1|"
    r"System Reference Document 5\.2\.1 \d+)$"
)

_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
_TAG = re.compile(r"<[^>]*>")
_IMAGE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
_LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")
#: Glyphs that are markup on one side and literal text on the other: Markdown
#: writes emphasis with ``*`` and list items with ``-``, while the PDF renders a
#: bullet glyph and uses ``*`` for table footnote markers. Dropping the set from
#: *both* sides is what keeps the comparison symmetric; dropping it from the
#: Markdown alone made every bulleted list and every footnoted table read as
#: absent from the snapshot when the words were all present.
_SHARED_DROP = re.compile(r"[*•_`#|>]+")


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------


def markdown_text(raw: str) -> str:
    """Reduce Markdown with embedded HTML tables to its visible text.

    Tags become a space, which keeps the intermediate text readable; compaction
    removes whitespace afterwards, so a cell boundary leaves no trace either way
    -- the reason table association cannot be checked here. Entities are unescaped
    so ``&mdash;`` compares as the character the PDF renders, and link targets are
    dropped while their labels are kept, because a URL is the snapshot's own
    navigation rather than document text.
    """
    text = _COMMENT.sub(" ", raw)
    text = _IMAGE.sub(" ", text)
    text = _LINK.sub(r"\1", text)
    text = _TAG.sub(" ", text)
    text = html.unescape(text)
    return _SHARED_DROP.sub(" ", text)


def page_text(page: ExtractedPage) -> str:
    """Join one extracted page's lines, dropping the running header/footer.

    Reading order comes from :func:`pdf_source.extract_pages`, whose
    ``use_text_flow=True`` recipe follows this document's authored content stream
    and so already reads two-column pages in column order.
    """
    return _SHARED_DROP.sub(
        " ",
        " ".join(
            line.text for line in page.lines if not _RUNNING.match(line.text.strip())
        ),
    )


def running_lines(pages: list[ExtractedPage]) -> int:
    """Count the running header/footer lines stripped, for the evidence record."""
    return sum(
        1 for p in pages for line in p.lines if _RUNNING.match(line.text.strip())
    )


# ---------------------------------------------------------------------------
# Containment
# ---------------------------------------------------------------------------


def window_set(text: str, *, window: int = WINDOW) -> set[str]:
    """Every distinct ``window``-character substring of compacted ``text``."""
    return {text[i : i + window] for i in range(len(text) - window + 1)}


@dataclass(frozen=True)
class Run:
    """A maximal stretch of compacted text with no counterpart in the other side.

    ``length`` counts affected characters — the span the unmatched windows cover,
    not the number of windows — so it is comparable against
    :data:`NOISE_FLOOR` regardless of ``window``.
    """

    offset: int
    length: int
    excerpt: str


def unmatched_runs(
    text: str,
    haystack: set[str],
    *,
    window: int = WINDOW,
    excerpt_chars: int = 240,
) -> list[Run]:
    """Find every maximal run of windows of ``text`` absent from ``haystack``.

    Text shorter than one window yields nothing: there is no window to test, and
    inventing a shorter one for the tail would make the sensitivity of the last
    47 characters differ from the rest of the document.
    """
    runs: list[Run] = []
    start: int | None = None
    last = len(text) - window
    for i in range(last + 1):
        if text[i : i + window] in haystack:
            if start is not None:
                runs.append(_run(text, start, i - 1, window, excerpt_chars))
                start = None
        elif start is None:
            start = i
    if start is not None:
        runs.append(_run(text, start, last, window, excerpt_chars))
    return runs


def _run(text: str, first: int, final: int, window: int, excerpt: int) -> Run:
    length = final - first + window
    return Run(offset=first, length=length, excerpt=text[first : first + excerpt])


# ---------------------------------------------------------------------------
# Sources
# ---------------------------------------------------------------------------


def community_text(
    root: Path, *, files: tuple[str, ...] = CONTENT_FILES
) -> dict[str, str]:
    """Compacted text of each pinned content file, keyed by upstream path."""
    pin = root / PIN_DIR
    return {
        name: compact(markdown_text((pin / name).read_text(encoding="utf-8")))
        for name in files
    }


@dataclass(frozen=True)
class PageCoverage:
    """One page's containment in the community snapshot."""

    printed_page: int
    chars: int
    windows: int
    matched: int
    runs: tuple[Run, ...]
    first_line: str

    @property
    def coverage(self) -> float:
        """Fraction of this page's windows present in the snapshot."""
        return self.matched / self.windows if self.windows else 1.0

    @property
    def longest_run(self) -> int:
        return max((r.length for r in self.runs), default=0)


def page_coverage(
    page: ExtractedPage, haystack: set[str], *, window: int = WINDOW
) -> PageCoverage:
    """Measure one page against the community snapshot's windows."""
    text = compact(page_text(page))
    runs = unmatched_runs(text, haystack, window=window)
    total = max(len(text) - window + 1, 0)
    unmatched = sum(r.length - window + 1 for r in runs)
    return PageCoverage(
        printed_page=page.printed_page,
        chars=len(text),
        windows=total,
        matched=total - unmatched,
        runs=tuple(runs),
        first_line=next(
            (line.text for line in page.lines if not _RUNNING.match(line.text.strip())),
            "",
        ),
    )


# ---------------------------------------------------------------------------
# Named checks (Owner-supplied failure families and positive controls)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class NamedCheck:
    """One Owner-named region, with what this instrument can and cannot decide."""

    name: str
    printed_pages: tuple[int, ...]
    concern: str
    positive_control: bool = False


NAMED_CHECKS: tuple[NamedCheck, ...] = (
    NamedCheck(
        name="skills-and-perception",
        printed_pages=(9,),
        concern="Skill rows and the Perception entry; row/ability association is "
        "table structure this instrument does not check.",
    ),
    NamedCheck(
        name="armor-and-chain-shirt",
        printed_pages=(92,),
        concern="Armor table values; whether 13 is Chain Shirt's AC rather than "
        "another column is table structure, not text presence.",
    ),
    NamedCheck(
        name="always-prepared-spells",
        printed_pages=(104,),
        concern="Always-prepared spell listing and the prose governing it.",
    ),
    NamedCheck(
        name="carpet-of-flying",
        printed_pages=(215,),
        concern="Carpet of Flying sizes, capacity and speed.",
    ),
    NamedCheck(
        name="vulture-pack-tactics",
        printed_pages=(364,),
        concern="Vulture stat block and its Pack Tactics trait.",
    ),
    NamedCheck(
        name="archelon-and-baboon",
        printed_pages=(344, 345),
        concern="Adjacent stat blocks; ability-grid row association is table "
        "structure this instrument does not check.",
    ),
    NamedCheck(
        name="barbarian-progression",
        printed_pages=(28,),
        concern="Barbarian level progression; per-level association is table "
        "structure, not text presence.",
    ),
    NamedCheck(
        name="sorcerer-lists",
        printed_pages=(67, 68),
        concern="Sorcerer spell and feature lists across a page break.",
    ),
    NamedCheck(
        name="rarity-value-and-command-word",
        printed_pages=(206,),
        concern="Rarity/value table and the Command Word text; rarity-to-value "
        "association is table structure, not text presence.",
    ),
    NamedCheck(
        name="actions",
        printed_pages=(9, 10),
        concern="Owner-supplied positive control: this region is known good, so "
        "any run it produces measures the instrument, not the snapshot.",
        positive_control=True,
    ),
    NamedCheck(
        name="multiclass-spellcaster",
        printed_pages=(26,),
        concern="Owner-supplied positive control: this region is known good, so "
        "any run it produces measures the instrument, not the snapshot.",
        positive_control=True,
    ),
)


def check_result(
    check: NamedCheck,
    coverages: dict[int, PageCoverage],
    *,
    floor: int = NOISE_FLOOR,
) -> dict[str, object]:
    """Report one named check without ever claiming table structure was proven.

    A region whose runs are all under the floor is ``below_floor_unresolved``,
    never ``pass``: the floor is where this instrument stops being able to tell a
    real omission from its own reordering artefacts, so those runs are carried
    forward rather than cleared. The structural question is separately and
    permanently open until a later increment answers it.
    """
    pages = [coverages[p] for p in check.printed_pages if p in coverages]
    over = [r for c in pages for r in c.runs if r.length >= floor]
    return {
        "name": check.name,
        "printed_pages": list(check.printed_pages),
        "concern": check.concern,
        "positive_control": check.positive_control,
        "verdict": "discrepancy" if over else "below_floor_unresolved",
        "table_association_checked": False,
        "coverage": [
            {
                "printed_page": c.printed_page,
                "windows": c.windows,
                "matched": c.matched,
                "longest_run": c.longest_run,
            }
            for c in pages
        ],
        "runs_over_floor": [{"length": r.length, "excerpt": r.excerpt} for r in over],
    }


def positive_control_floor(coverages: dict[int, PageCoverage]) -> int:
    """Longest unmatched run the positive controls produce.

    :data:`NOISE_FLOOR` must stay above this. Reporting it separately is what
    makes the floor a derivation rather than a tuning knob: if it rises, the
    honest response is to explain the new artefact or fix it, never to raise the
    constant to match.
    """
    pages = {p for c in NAMED_CHECKS if c.positive_control for p in c.printed_pages}
    return max(
        (r.length for page in pages if page in coverages for r in coverages[page].runs),
        default=0,
    )


# ---------------------------------------------------------------------------
# Evidence
# ---------------------------------------------------------------------------


def compare(
    pages: list[ExtractedPage],
    community: dict[str, str],
    *,
    window: int = WINDOW,
    floor: int = NOISE_FLOOR,
    worst: int = 25,
    pin_commit: str = "",
) -> dict[str, object]:
    """Compare the given pages against the snapshot and return the evidence.

    Both directions are reported. PDF-to-snapshot answers "is the official text
    present"; snapshot-to-PDF answers "does the snapshot carry text the document
    does not", which is the direction that finds invented or imported content.
    """
    haystack: set[str] = set()
    for text in community.values():
        haystack |= window_set(text, window=window)

    coverages = {
        page.printed_page: page_coverage(page, haystack, window=window)
        for page in pages
    }
    pdf_windows: set[str] = set()
    for page in pages:
        pdf_windows |= window_set(compact(page_text(page)), window=window)

    additions = {
        name: [
            r
            for r in unmatched_runs(text, pdf_windows, window=window)
            if r.length >= floor
        ]
        for name, text in community.items()
    }
    ranked = sorted(coverages.values(), key=lambda c: (c.coverage, -c.windows))
    total_windows = sum(c.windows for c in coverages.values())
    total_matched = sum(c.matched for c in coverages.values())
    body = [c for c in coverages.values() if c.printed_page not in FRONT_MATTER]
    body_windows = sum(c.windows for c in body)
    body_matched = sum(c.matched for c in body)
    discrepancies = sorted(
        (
            {
                "printed_page": c.printed_page,
                "length": r.length,
                "front_matter": c.printed_page in FRONT_MATTER,
                "excerpt": r.excerpt,
            }
            for c in coverages.values()
            for r in c.runs
            if r.length >= floor
        ),
        key=lambda d: -int(str(d["length"])),
    )
    below_floor = [r for c in coverages.values() for r in c.runs if r.length < floor]

    return {
        "instrument": {
            "module": __name__,
            "extractor": f"pdfplumber {_pkg_version('pdfplumber')}",
            "reading_order": "pdf_source.extract_pages (use_text_flow=True)",
            "normalization": (
                f"policy.compact ({NORMALIZATION_VERSION}): NFKC + ligature and "
                "minus-sign folding, whitespace and hyphen removal, case fold. "
                "Not lossless: folding the minus sign and then removing hyphens "
                "makes 'modifier -2' and 'modifier 2' compare equal, so signs, "
                "footnote markers and adjacent qualifiers are not checked here"
            ),
            "comparison": "character-window containment, both directions",
            "window_chars": window,
            "noise_floor_chars": floor,
            "noise_floor_derivation": (
                "2 * window_chars, derived from one isolated same-text/"
                "different-order junction: it can only leave the windows "
                "straddling the joint unmatched. Not a universal bound -- two "
                "junctions closer together than 2 * window_chars merge their "
                "unmatched windows, and an omission beside a junction is "
                "absorbed -- so the floor is the reporting threshold, not a "
                "clearance. Runs under it are counted in "
                "discrepancies.runs_below_floor and remain unresolved. The "
                "Owner-supplied positive controls bound the single-junction "
                "artefact empirically; see positive_control_longest_run."
            ),
            "running_header_footer_lines_stripped": running_lines(pages),
            "table_association_checked": False,
        },
        "official_source": {
            "path": PDF_REPO_PATH,
            "sha256": PDF_SHA256,
            "pages_compared": len(pages),
        },
        "community_source": {
            "directory": PIN_DIR,
            "content_files": list(community),
            "pinned_commit": pin_commit,
            "status": "qualified",
            "qualification_review": QUALIFICATION_REVIEW,
        },
        "coverage": {
            "windows": total_windows,
            "matched": total_matched,
            "fraction": (total_matched / total_windows) if total_windows else 1.0,
            "front_matter_pages": list(FRONT_MATTER),
            "windows_excluding_front_matter": body_windows,
            "matched_excluding_front_matter": body_matched,
            "fraction_excluding_front_matter": (
                (body_matched / body_windows) if body_windows else 1.0
            ),
            "pages_fully_covered": sum(
                1 for c in coverages.values() if c.matched == c.windows
            ),
            "lowest_pages": [
                {
                    "printed_page": c.printed_page,
                    "coverage": round(c.coverage, 4),
                    "windows": c.windows,
                    "longest_run": c.longest_run,
                    "first_line": c.first_line,
                    "worst_excerpt": (
                        max(c.runs, key=lambda r: r.length).excerpt if c.runs else ""
                    ),
                }
                for c in ranked[:worst]
            ],
        },
        "community_additions": {
            "files_with_runs_over_floor": {
                name: [
                    {"offset": r.offset, "length": r.length, "excerpt": r.excerpt}
                    for r in runs
                ]
                for name, runs in additions.items()
                if runs
            },
            "note": (
                "Text present in the snapshot and absent from the document. Some "
                "is the snapshot's own navigation and heading scaffolding; each "
                "run still needs reading before the source can be qualified."
            ),
        },
        "discrepancies": {
            "runs_over_floor": len(discrepancies),
            "chars_over_floor": sum(int(str(d["length"])) for d in discrepancies),
            # Sub-floor runs are inventoried rather than dropped: the floor bounds
            # a single isolated reordering junction, not several merged ones, so
            # these are unresolved differences carried into full-source
            # qualification. Counts only -- the excerpts would balloon this record
            # without being readable, and qualification re-derives them.
            "runs_below_floor": len(below_floor),
            "chars_below_floor": sum(r.length for r in below_floor),
            "below_floor_note": (
                "Unresolved, not cleared. The 2 * window bound holds for one "
                "separated junction; adjacent junctions merge runs and can "
                "absorb a genuine omission, so these need reading at "
                "qualification."
            ),
            "runs": discrepancies,
        },
        "named_checks": [check_result(c, coverages, floor=floor) for c in NAMED_CHECKS],
        "positive_control_longest_run": positive_control_floor(coverages),
        "pending": [
            "Table row and column association, including colspan cells, empty "
            "cells and repeated ability-grid headers, is not checked here. It "
            "is checked by tests/ingestion/source/test_community_source_"
            "structure.py, which reads the cells; see docs/architecture/"
            "issue-5c-5d-community-source-corrections.md.",
            "Sign, number and qualifier differences are invisible to this "
            "normalization: compact() folds the minus sign to a hyphen and then "
            "removes hyphens, so 'modifier -2' and 'modifier 2' compare equal, "
            "and a footnote marker or qualifier beside a value can be absorbed. "
            "community_tokens keeps the sign and compares per-page token "
            "multisets, which is where that difference is read.",
            "Record ownership -- which stat block, spell or table entry a "
            "passage belongs to -- is invisible to a character-window "
            "comparison; adjacent entries read as one continuous stream. Heading "
            "ownership is checked against the official table of contents "
            "instead; see the qualification section of the evidence record.",
            "Runs below the noise floor are unresolved, not cleared: the bound "
            "covers a single isolated reordering junction, and merged junctions "
            "or an omission beside one can hide under it. Counted in "
            "discrepancies.runs_below_floor for qualification to read. Every run, "
            "over or under the floor, is dispositioned against the token "
            "pass in the qualification section of the evidence record.",
            "Community additions are reported, not adjudicated: each run still "
            "needs reading to say whether it is snapshot scaffolding, an "
            "editorial addition, or imported non-SRD text.",
            "Official page 1 attribution and licence text is excluded as front "
            "matter alongside the table of contents, but it is a distinct "
            "completeness item: the snapshot must carry the attribution the "
            "licence requires, which a page-number index is not. Carried as the "
            "controlled addition legal-information.md, which compacts "
            "identically to official page 1.",
            "A region reported as below the floor is not qualified; full-source "
            "qualification requires the structural pass.",
        ],
    }


def pin_commit(root: Path) -> str:
    """The upstream commit the snapshot is pinned to, read from its manifest."""
    manifest = json.loads(
        (root / PIN_DIR / "source_pin.json").read_text(encoding="utf-8")
    )
    return str(manifest["upstream_commit"])


def run(
    root: Path, *, printed_pages: tuple[int, ...] | None = None
) -> dict[str, object]:
    """Compare the document against the snapshot and return the evidence.

    ``printed_pages`` restricts the comparison so the tests can exercise the
    Owner-named regions without re-extracting all 364 pages. The committed
    evidence record is the unrestricted run; a restricted one is a probe and its
    coverage totals are not the document's.
    """
    pages = extract_pages(root / PDF_REPO_PATH)
    if printed_pages is not None:
        wanted = set(printed_pages)
        pages = [p for p in pages if p.printed_page in wanted]
    return compare(pages, community_text(root), pin_commit=pin_commit(root))


if __name__ == "__main__":  # pragma: no cover - operator entry point
    print(json.dumps(run(Path(".")), indent=2))
