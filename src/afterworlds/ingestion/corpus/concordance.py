"""Source-to-corpus concordance and version canaries — Issue 5c, Components E, J.

Deterministic verification that persisted source-text records correspond to the
authoritative PDF: every chunk's content must actually appear at its declared
page locator, and six hardcoded version canaries must match SRD 5.2.1 content
(not the pre-5.2.1 / 2014 content the legacy artifact carried).

This is the independent honest check on the pipeline: the ledger and corpus are
derived from the PDF, but concordance re-reads the extracted page text and
confirms the correspondence against it — catching the exact defect family ADR-005c
found in the legacy artifact (wrong locators, obsolete wording).

The canary *expected values are hardcoded from the issue/spec's verified facts*,
never re-extracted from the document — otherwise a canary would compare the
extraction to itself and prove nothing.
"""

from __future__ import annotations

from dataclasses import dataclass

from afterworlds.ingestion.corpus.models import CorpusChunk
from afterworlds.ingestion.corpus.pdf_source import ExtractedPage
from afterworlds.ingestion.corpus.policy import compact, normalize
from afterworlds.ingestion.corpus.tables import _detect

# ``compact`` is re-exported from policy (shared with tables without an import
# cycle); kept importable from concordance for existing callers/tests.
__all__ = [
    "compact",
    "normalize",
    "ConcordanceResult",
    "check_concordance",
    "TableConcordanceResult",
    "check_table_concordance",
    "Canary",
    "VERSION_CANARIES",
    "check_canaries",
]


@dataclass(frozen=True)
class ConcordanceResult:
    """Outcome of the whole-corpus concordance check (Component E)."""

    chunks_checked: int
    locator_failures: tuple[str, ...]  # chunk ids whose page is out of range
    content_failures: tuple[str, ...]  # chunk ids not found at their page

    @property
    def passed(self) -> bool:
        return not self.locator_failures and not self.content_failures


def check_concordance(
    chunks: tuple[CorpusChunk, ...], pages: list[ExtractedPage]
) -> ConcordanceResult:
    """Verify every chunk's content appears at its declared page (Component E)."""
    page_compact: dict[int, str] = {
        pg.printed_page: compact(pg.canonical_text()) for pg in pages
    }
    locator_failures: list[str] = []
    content_failures: list[str] = []
    for chunk in chunks:
        haystack = page_compact.get(chunk.printed_page)
        if haystack is None:
            locator_failures.append(chunk.chunk_id)
            continue
        if compact(chunk.content) not in haystack:
            content_failures.append(chunk.chunk_id)
    return ConcordanceResult(
        chunks_checked=len(chunks),
        locator_failures=tuple(locator_failures),
        content_failures=tuple(content_failures),
    )


# ---------------------------------------------------------------------------
# Table row/cell accounting (Component E) — independent of generated RuleChunks.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TableConcordanceResult:
    """Whole-corpus table reconstruction check (Component E, PR #134).

    Verifies every emitted table cell's **structural consistency** — unique
    ``(row, col)`` per table, ``row``/``col`` within the declared grid, non-empty
    text — plus that each cell's text appears on its page, working directly from
    the reconstructed tables rather than the generated ``RuleChunk`` set (so a
    chunk-generation bug cannot mask a table regression). The structural checks
    catch failure modes the detection filter does **not** already guarantee (a
    duplicated/out-of-range/empty cell), so the result is not tautological.

    ``coverage`` surfaces the rect-anchor → emitted → dropped-to-paragraph tally:
    detection deliberately falls back to paragraph segmentation for a candidate
    region it cannot cleanly reconstruct (typically a shaded prose region
    spanning both body columns), and this makes that fallback explicit rather
    than a silent cap.
    """

    tables_checked: int
    cells_checked: int
    content_failures: tuple[str, ...]  # "p{page}:table{n}:r{row}c{col}" not on page
    structural_failures: tuple[str, ...]  # dup / out-of-range / empty cell
    coverage: dict[str, int]

    @property
    def passed(self) -> bool:
        return not self.content_failures and not self.structural_failures


def check_table_concordance(pages: list[ExtractedPage]) -> TableConcordanceResult:
    """Verify reconstructed table cells and report detection coverage (E)."""
    content_failures: list[str] = []
    structural_failures: list[str] = []
    tables = 0
    cells = 0
    anchors = emitted = drop_no_run = drop_span = drop_off = 0
    for page in pages:
        haystack = compact(page.canonical_text())
        detected, cov = _detect(page)
        anchors += cov.anchors
        emitted += cov.emitted
        drop_no_run += cov.dropped_no_run
        drop_span += cov.dropped_span_invalid
        drop_off += cov.dropped_off_page
        for ti, table in enumerate(detected):
            tables += 1
            seen: set[tuple[int, int]] = set()
            for cell in table.cells:
                cells += 1
                tag = f"p{page.printed_page}:table{ti}:r{cell.row}c{cell.col}"
                if (cell.row, cell.col) in seen:
                    structural_failures.append(f"{tag}:duplicate")
                seen.add((cell.row, cell.col))
                if not (0 <= cell.row < table.row_count):
                    structural_failures.append(f"{tag}:row-out-of-range")
                if not (0 <= cell.col < table.column_count):
                    structural_failures.append(f"{tag}:col-out-of-range")
                if not cell.text.strip():
                    structural_failures.append(f"{tag}:empty")
                elif compact(cell.text) not in haystack:
                    content_failures.append(tag)
    return TableConcordanceResult(
        tables_checked=tables,
        cells_checked=cells,
        content_failures=tuple(content_failures),
        structural_failures=tuple(structural_failures),
        coverage={
            "anchors": anchors,
            "emitted": emitted,
            "dropped_no_run": drop_no_run,
            "dropped_span_invalid": drop_span,
            "dropped_off_page": drop_off,
        },
    )


# ---------------------------------------------------------------------------
# Version canaries (Component J) — expected facts hardcoded from the spec.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Canary:
    """A single version canary: verified SRD 5.2.1 facts at a verified page."""

    name: str
    printed_page: int
    must_contain: tuple[str, ...]  # compact substrings that MUST be present
    must_not_contain: tuple[str, ...]  # pre-5.2.1 markers that must be ABSENT


VERSION_CANARIES: tuple[Canary, ...] = (
    Canary(
        name="core_attack_ac_dc",
        printed_page=7,
        must_contain=(
            compact("Attack Roll"),
            compact("Armor Class"),
            compact("Difficulty Class"),
        ),
        must_not_contain=(),
    ),
    Canary(
        name="cure_wounds",
        printed_page=121,
        # 5.2.1: heals 2d8, no undead/construct exclusion.
        must_contain=(compact("2d8"), compact("regains a number of Hit Points")),
        must_not_contain=(compact("no effect on undead or constructs"),),
    ),
    Canary(
        name="counterspell",
        printed_page=120,
        # 5.2.1: target makes a Constitution saving throw.
        must_contain=(compact("Counterspell"), compact("Constitution saving throw")),
        must_not_contain=(),
    ),
    Canary(
        name="exhaustion",
        printed_page=181,
        # 5.2.1 Rules Glossary: one cumulative formula, death at level 6.
        must_contain=(
            compact("Exhaustion"),
            compact("cumulative"),
            compact("You die if your Exhaustion level is 6"),
        ),
        must_not_contain=(),
    ),
    Canary(
        name="goblin_minion_statblock",
        printed_page=290,
        must_contain=(compact("Goblin Minion"), compact("CR 1/8")),
        must_not_contain=(),
    ),
    Canary(
        name="fireball_save_for_half",
        printed_page=131,
        # 5.2.1: Dexterity save, 8d6, half on success; flashes "from you".
        must_contain=(
            compact("Fireball"),
            compact("Dexterity saving throw"),
            compact("8d6"),
            compact("half as much damage"),
        ),
        must_not_contain=(compact("from your pointing finger"),),
    ),
)


@dataclass(frozen=True)
class CanaryResult:
    name: str
    printed_page: int
    passed: bool
    missing: tuple[str, ...]
    unexpected: tuple[str, ...]


def check_canaries(pages: list[ExtractedPage]) -> tuple[CanaryResult, ...]:
    """Run all six version canaries against the extracted pages (Component J)."""
    page_compact = {pg.printed_page: compact(pg.canonical_text()) for pg in pages}
    results: list[CanaryResult] = []
    for canary in VERSION_CANARIES:
        haystack = page_compact.get(canary.printed_page, "")
        missing = tuple(s for s in canary.must_contain if s not in haystack)
        unexpected = tuple(s for s in canary.must_not_contain if s in haystack)
        results.append(
            CanaryResult(
                name=canary.name,
                printed_page=canary.printed_page,
                passed=not missing and not unexpected,
                missing=missing,
                unexpected=unexpected,
            )
        )
    return tuple(results)
