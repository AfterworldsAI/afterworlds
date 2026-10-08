"""Coherent units of the pinned community source — CRD Issue 5c/5d clean restart.

Step 3 of the Recorded Owner Decision of 21 September 2026 builds the fresh 5c
corpus from the qualified Markdown snapshot rather than from PDF geometry. This
module is the front end: it reads the pinned files and cuts each one into the
units a consumer actually wants to read — a whole paragraph, a whole list, a
whole table with its caption, a stat block's field group, one heading.

Why units and not leaves
------------------------
The retired path emitted one chunk per geometric leaf, so a table arrived as
eighty disconnected cells and a spell as a handful of line fragments. Unit size
here is chosen for consumption and citation: the smallest thing that still reads
correctly on its own. A table is one unit because a row without its header means
nothing; a list is one unit because item three is a continuation of item one.

Tiling
------
Units tile their file. Every character belongs to exactly one unit span, which
is asserted directly: the concatenation of the units' compacted text must equal
the file's compacted text, computed by the same normalization the source
qualification used. That single equality is the completeness guarantee — no unit
can be dropped, duplicated, reordered or silently truncated without breaking it.
It is the Markdown analogue of the retired path's per-page span tiling, and it
is the reason this module needs no separate coverage report.

``Leaf.char_start``/``char_end`` are therefore a half-open span in the *file's*
compacted text, not in a page's canonical text. That is what makes citation a
lookup rather than a search: :mod:`afterworlds.ingestion.corpus.source_citations`
runs the same partition the qualification ran and reads each unit's official
page straight off those offsets.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from afterworlds.ingestion.corpus.hashing import content_id
from afterworlds.ingestion.corpus.models import (
    Container,
    ContainerType,
    Leaf,
    LeafType,
)
from afterworlds.ingestion.source.community_compare import markdown_text
from afterworlds.ingestion.source.community_tokens import normalized

#: The thirteen upstream content files plus the controlled attribution addition,
#: page 1 first. Citation needs only within-file order — the partition enforces
#: document order per file — but the tuple is also the release's reading order:
#: each leaf's ``occurrence_index`` follows it, and direct reads order passages
#: by that index. The official Monsters rules (pp.254-257) therefore precede
#: Monsters A-Z (p.258 onward), which the alphabetical ``CONTENT_FILES`` reverses.
#: The tuple is also what the transform identity records.
CORPUS_FILES: tuple[str, ...] = (
    "legal-information.md",
    "animals.md",
    "character-creation.md",
    "character-origins.md",
    "classes.md",
    "equipment.md",
    "feats.md",
    "gameplay-toolbox.md",
    "magic-items.md",
    "monsters.md",
    "monsters-A-Z.md",
    "playing-the-game.md",
    "rules-glossary.md",
    "spells.md",
)

#: ``legal-information.md`` reproduces official page 1 and carries the CC-BY-4.0
#: attribution the licence requires to travel with any derived work. Its units
#: are attribution leaves, the only overlap-eligible type in the frozen policy:
#: the attribution is allowed to be repeated, not merely present once.
ATTRIBUTION_FILE = "legal-information.md"

#: A byte-order mark survives ``utf-8`` decoding as a character, and the source
#: qualification compared the files that way. It stays in the bytes and is only
#: skipped when a line is classified; stripping it would silently change the
#: compacted text this module has to reproduce.
_BOM = "﻿"
_EDGE = " \t\r" + _BOM

_HEADING = re.compile(r"^[" + _BOM + r"\s]*(#{1,6})\s+(.*?)\s*$")
_LIST_ITEM = re.compile(r"^\s{0,3}(?:[-*+]\s|\d+\.\s)")
_CAPTION = re.compile(r"^\*\*[^*]+\*\*$")
#: A stat block's field group: ``**AC** 17 **Initiative** +7 (17) <br>``. The
#: mark is the ``<br>`` the conversion uses to hold the group on one printed
#: line, which ordinary prose with a bold lead-in does not carry.
_STAT_FIELD = re.compile(r"^\*\*[^*]+\*\*")

_TABLE_OPEN = "<table>"
_TABLE_CLOSE = "</table>"


class SourceTilingError(RuntimeError):
    """A file's units do not reproduce the file's compacted text."""


@dataclass(frozen=True)
class SourceUnit:
    """One coherent unit of one source file, with its place in the file."""

    file: str
    file_index: int
    leaf_type: LeafType
    #: Heading labels from the file's title down to the unit's own section.
    heading_path: tuple[str, ...]
    #: Container ids for the same path, which is what a leaf carries.
    container_path: tuple[str, ...]
    #: The container this unit's own heading opened, if it is a heading.
    opened_container: str | None
    content: str
    line: int
    #: Half-open span in the file's compacted text.
    compact_start: int
    compact_end: int

    @property
    def section_label(self) -> str:
        return " > ".join(self.heading_path)


@dataclass(frozen=True)
class SourceStructure:
    """Every unit of every file, with the containers the headings opened."""

    containers: tuple[Container, ...]
    units: tuple[SourceUnit, ...]

    def units_for(self, file: str) -> tuple[SourceUnit, ...]:
        return tuple(u for u in self.units if u.file == file)


# ---------------------------------------------------------------------------
# Block scanning
# ---------------------------------------------------------------------------


def _line_starts(text: str) -> list[int]:
    starts, at = [0], 0
    for line in text.split("\n")[:-1]:
        at += len(line) + 1
        starts.append(at)
    return starts


def _bare(line: str) -> str:
    return line.strip(_EDGE).strip()


def _block_ranges(lines: list[str]) -> list[tuple[int, int]]:
    """Cut *lines* into block line ranges: heading, table, or blank-separated.

    Blank lines are not attached here. The caller tiles the file by extending
    each block's span to the start of the next, so a blank run belongs to the
    block above it and contributes nothing to the compacted text either way.
    """
    ranges: list[tuple[int, int]] = []
    i, n = 0, len(lines)
    while i < n:
        if not _bare(lines[i]):
            i += 1
            continue
        if _HEADING.match(lines[i]):
            ranges.append((i, i + 1))
            i += 1
            continue
        if _bare(lines[i]) == _TABLE_OPEN:
            j = i
            while j < n and _bare(lines[j]) != _TABLE_CLOSE:
                j += 1
            ranges.append((i, min(j + 1, n)))
            i = j + 1
            continue
        j = i
        while j < n:
            nxt = _bare(lines[j])
            if not nxt or _HEADING.match(lines[j]) or nxt == _TABLE_OPEN:
                break
            j += 1
        ranges.append((i, j))
        i = j
    return ranges


#: A table footnote defines a mark used inside the table above it:
#: ``\*Halve the value for a consumable item...``. A single leading marker,
#: escaped or not. ``**`` is a caption or a stat field, not a footnote.
_FOOTNOTE_MARKS = ("*", "†", "‡")


def _is_footnote(bare: str) -> bool:
    """True for a block that opens with one footnote marker."""
    mark = bare.lstrip(chr(92))
    return mark.startswith(_FOOTNOTE_MARKS) and not mark.startswith(("**", "††"))


def _merge_table_context(
    lines: list[str], ranges: list[tuple[int, int]]
) -> list[tuple[int, int]]:
    """Bind a table's caption above it and its footnote below it into its unit.

    123 of the 579 tables are named by a bold-only line above them and are
    unreadable without it. The rest are named by the heading above them, which
    every unit already carries.

    Five tables are followed by a footnote that defines a marker used inside
    the table -- Magic Item Rarities and Values in ``magic-items.md`` is the
    representative case. Served apart from its table, the table offers starred
    values and no rule for the star, so the footnote is part of the table's
    logical unit rather than a sibling that happens to share a section label.

    Merging is span-contiguous, so the file still tiles.
    """
    merged: list[tuple[int, int]] = []
    index, count = 0, len(ranges)
    while index < count:
        lo, hi = ranges[index]
        if (
            index + 1 < count
            and hi - lo == 1
            and _CAPTION.fullmatch(_bare(lines[lo]))
            and _bare(lines[ranges[index + 1][0]]) == _TABLE_OPEN
        ):
            index += 1
            hi = ranges[index][1]
        if (
            _bare(lines[hi - 1]) == _TABLE_CLOSE
            and index + 1 < count
            and _is_footnote(_bare(lines[ranges[index + 1][0]]))
        ):
            index += 1
            hi = ranges[index][1]
        merged.append((lo, hi))
        index += 1
    return merged


def _classify(lines: list[str], *, attribution: bool) -> LeafType:
    if lines and _HEADING.match(lines[0]):
        return LeafType.HEADING
    body = [ln for ln in lines if _bare(ln)]
    if any(_bare(ln) == _TABLE_OPEN for ln in body):
        return LeafType.TABLE
    if attribution:
        return LeafType.ATTRIBUTION
    if any(_LIST_ITEM.match(ln) for ln in body) and all(
        _LIST_ITEM.match(ln) or ln.startswith((" ", "\t")) for ln in body
    ):
        return LeafType.LIST
    if (
        body
        and _STAT_FIELD.match(_bare(body[0]))
        and any(ln.rstrip().endswith("<br>") for ln in body)
    ):
        return LeafType.STAT_FIELD
    return LeafType.PARAGRAPH


def _container_type(depth: int) -> ContainerType:
    if depth <= 1:
        return ContainerType.SECTION
    if depth == 2:
        return ContainerType.SUBSECTION
    return ContainerType.ENTRY


# ---------------------------------------------------------------------------
# Units
# ---------------------------------------------------------------------------


def parse_file(
    file: str, file_index: int, text: str
) -> tuple[list[Container], list[SourceUnit], list[tuple[int, int]]]:
    """Cut one file into containers, units, and the raw spans that tile it.

    The returned spans tile ``text`` exactly and are one longer than the units
    when the file opens with a byte-order mark or blank lines: that leading
    filler carries no unit and no compacted characters, but it must still belong
    to a span for the tiling to hold.
    """
    lines = text.split("\n")
    starts = _line_starts(text)
    blocks = _merge_table_context(lines, _block_ranges(lines))

    spans: list[tuple[int, int]] = []
    if not blocks:
        return [], [], [(0, len(text))]
    if blocks[0][0] > 0:
        spans.append((0, starts[blocks[0][0]]))
    for index, (lo, _hi) in enumerate(blocks):
        end = starts[blocks[index + 1][0]] if index + 1 < len(blocks) else len(text)
        spans.append((starts[lo], end))

    containers: list[Container] = []
    units: list[SourceUnit] = []
    stack: list[tuple[int, str, str]] = []  # (depth, container_id, label)
    attribution = file == ATTRIBUTION_FILE

    for lo, hi in blocks:
        block = lines[lo:hi]
        heading = _HEADING.match(block[0])
        opened: str | None = None
        if heading is not None:
            depth, label = len(heading.group(1)), heading.group(2)
            # A heading closes every open section at its own depth or above.
            # That rule is the whole of what Markdown says about which entry a
            # record belongs to, and it is what the source correction restored.
            while stack and stack[-1][0] >= depth:
                stack.pop()
            opened = content_id("container", file, depth, label, lo)
            containers.append(
                Container(
                    container_id=opened,
                    container_type=_container_type(depth),
                    label=label,
                    printed_page=0,  # resolved once citations are known
                    parent_id=stack[-1][1] if stack else None,
                )
            )
            stack.append((depth, opened, label))
        units.append(
            SourceUnit(
                file=file,
                file_index=file_index,
                leaf_type=_classify(block, attribution=attribution),
                heading_path=tuple(label for _d, _c, label in stack),
                container_path=tuple(cid for _d, cid, _l in stack),
                opened_container=opened,
                content="\n".join(block).strip(_EDGE).strip(),
                line=lo + 1,
                compact_start=0,
                compact_end=0,
            )
        )
    return containers, units, spans


def build_structure(sources: dict[str, str]) -> SourceStructure:
    """Parse every file into containers and units, asserting the tiling.

    *sources* maps file name to decoded text, in build order. The tiling
    assertion is the completeness guarantee and is not optional: a build that
    cannot reproduce its own source's compacted text refuses rather than
    reporting partial coverage.
    """
    containers: list[Container] = []
    units: list[SourceUnit] = []
    for file_index, (file, text) in enumerate(sources.items()):
        file_containers, file_units, spans = parse_file(file, file_index, text)

        pieces = [normalized(markdown_text(text[lo:hi])).compact for lo, hi in spans]
        whole = normalized(markdown_text(text)).compact
        if "".join(pieces) != whole:
            raise SourceTilingError(
                f"{file}: the units do not tile the file's compacted text "
                f"({len(''.join(pieces))} characters over {len(spans)} spans "
                f"against {len(whole)} in the file)"
            )

        lead = len(spans) - len(file_units)
        offset = sum(len(p) for p in pieces[:lead])
        for unit, piece in zip(file_units, pieces[lead:], strict=True):
            # A rule line between stat-block sections is a separator, not
            # content: it carries no compacted character, so dropping it leaves
            # the tiling above untouched and keeps 660 empty chunks out of the
            # corpus. Anything that *does* carry text stays, whatever it is.
            if not piece:
                offset += len(piece)
                continue
            units.append(
                SourceUnit(
                    file=unit.file,
                    file_index=unit.file_index,
                    leaf_type=unit.leaf_type,
                    heading_path=unit.heading_path,
                    container_path=unit.container_path,
                    opened_container=unit.opened_container,
                    content=unit.content,
                    line=unit.line,
                    compact_start=offset,
                    compact_end=offset + len(piece),
                )
            )
            offset += len(piece)
        containers.extend(file_containers)
    return SourceStructure(containers=tuple(containers), units=tuple(units))


def build_leaves(
    structure: SourceStructure, cited: dict[int, tuple[int, ...]]
) -> tuple[Leaf, ...]:
    """Turn units into ledger leaves once their official pages are known.

    *cited* maps a unit's index in ``structure.units`` to its official pages,
    primary first. A unit with no resolved page never reaches here: an
    unresolved citation is a build refusal, not a leaf with a guessed page.

    ``occurrence_index`` is the leaf's global emission order, which is the
    contract the reconstruction reads it under: persistence restores canonical
    chunk order by sorting on it, so anything short of a total order over the
    leaves silently reorders the rebuilt corpus.
    """
    leaves: list[Leaf] = []
    for index, unit in enumerate(structure.units):
        leaves.append(
            Leaf(
                leaf_id=content_id(
                    "source-leaf", unit.file, unit.compact_start, unit.compact_end
                ),
                printed_page=cited[index][0],
                page_index=unit.file_index,
                leaf_type=unit.leaf_type,
                content=unit.content,
                char_start=unit.compact_start,
                char_end=unit.compact_end,
                occurrence_index=index,
                container_path=unit.container_path,
            )
        )
    return tuple(leaves)


def resolve_container_pages(
    structure: SourceStructure, cited: dict[int, tuple[int, ...]]
) -> tuple[Container, ...]:
    """Give each container the official page its own heading resolved to."""
    page_for: dict[str, int] = {
        unit.opened_container: cited[index][0]
        for index, unit in enumerate(structure.units)
        if unit.opened_container is not None
    }
    return tuple(
        Container(
            container_id=c.container_id,
            container_type=c.container_type,
            label=c.label,
            printed_page=page_for.get(c.container_id, 0),
            parent_id=c.parent_id,
        )
        for c in structure.containers
    )
