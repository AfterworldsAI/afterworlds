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

import re
from dataclasses import dataclass

from afterworlds.ingestion.corpus.models import CorpusChunk
from afterworlds.ingestion.corpus.pdf_source import ExtractedPage
from afterworlds.ingestion.corpus.policy import normalize

_STRIP_RE = re.compile(r"[\s\-]+")


def compact(text: str) -> str:
    """Whitespace/hyphen-insensitive, case-folded comparison key.

    Removes spaces and hyphens (so line-wrap hyphenation and column flow can
    never cause a spurious mismatch) after unicode/ligature folding. Used for
    presence checks only, never to author content.
    """
    return _STRIP_RE.sub("", normalize(text)).casefold()


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
