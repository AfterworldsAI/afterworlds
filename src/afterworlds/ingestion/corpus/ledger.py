"""Frozen pre-transform source ledger — CRD Issue 5c, Component C.

Derives, directly and exhaustively from every page of the authoritative PDF and
independent of any transformed corpus output, a machine-readable ledger that
partitions every page-content occurrence into exactly one atomic coverage leaf
with a stable identity and a locator/span, plus the structural containers that
supply each leaf's nested path.

The ledger owns only source-side facts. It carries no dispositions, no exclusion
reasons, and no policy — those belong to reconciliation (D) and the frozen
policy (B). It is frozen and hashed (K a1) before any output-dependent
reconciliation, and neither the transform nor the reconciler may mutate a leaf.

Segmentation is deterministic and geometry-driven:

* A line matching the running-header/footer pattern is a ``HEADER_FOOTER`` leaf.
* A line at heading font size (>= 12pt) is a ``HEADING`` leaf and updates the
  section/subsection/entry container stack by size tier.
* Within a stat-block entry, a field-labelled line is a ``STAT_FIELD`` leaf.
* A line opening with a list marker is a ``LIST_ITEM`` leaf (wrapped
  continuation lines merge into it).
* Remaining body lines merge into ``PARAGRAPH`` leaves, breaking on any
  classified line, a column/block break (top decrease), or a paragraph gap;
  wrapped lines are de-hyphenated on merge (Component F line-wrap repair).

Leaf char-spans are half-open ranges within each page's canonical text and are
guaranteed disjoint and exhaustive (they tile the page).
"""

from __future__ import annotations

import re

from afterworlds.ingestion.corpus.hashing import content_id, hash_obj
from afterworlds.ingestion.corpus.models import (
    Container,
    ContainerType,
    Leaf,
    LeafType,
    SourceLedger,
)
from afterworlds.ingestion.corpus.pdf_source import (
    PDF_SHA256,
    SOURCE_DOCUMENT,
    SOURCE_VERSION,
    ExtractedPage,
    PageLine,
    extraction_config,
)
from afterworlds.ingestion.corpus.tables import DetectedTable, detect_page_tables

# Running header/footer: "N System Reference Document 5.2.1" (bottom) and
# "System Reference Document 5.2.1 N" (top). Verified present on all 364 pages.
_HF_RE = re.compile(
    r"^(?:\d+ System Reference Document 5\.2\.1"
    r"|System Reference Document 5\.2\.1 \d+)$"
)

# Heading font-size floor and container tier boundaries (from the document's
# size histogram: body 9-10pt; headings 12/14/15/18/26pt).
_HEADING_MIN_SIZE = 11.5
_SECTION_MIN_SIZE = 22.0
_SUBSECTION_MIN_SIZE = 15.5

# List markers at the start of a line.
_LIST_MARKER_RE = re.compile(
    r"^(?:[•‣◦·•▪]|[-–—]\s|\(?[0-9]{1,2}[.)]\s|\(?[a-z][.)]\s)"
)

# Stat-block field labels (D&D 5.2.1 stat block). A body line beginning with one
# of these, inside an entry container, is a discrete stat field.
_STAT_FIELD_RE = re.compile(
    r"^(?:AC|HP|Speed|Initiative|Str|Dex|Con|Int|WIS|Wis|Cha|MOD SAVE|"
    r"Skills|Gear|Senses|Languages|Immunities|Resistances|Vulnerabilities|"
    r"CR|PB|Saving Throws|Damage Immunities|Condition Immunities)\b"
)

# Attribution / licensing units.
_ATTRIBUTION_RE = re.compile(r"Creative Commons|CC BY 4\.0|Wizards of the Coast")

# A paragraph continues only when the next line steps down by a small gap.
_PARA_GAP_MAX = 18.0


def _is_header_footer(line: PageLine) -> bool:
    return bool(_HF_RE.match(line.text))


def _is_heading(line: PageLine) -> bool:
    return line.size >= _HEADING_MIN_SIZE


def _container_type_for_size(size: float) -> ContainerType:
    if size >= _SECTION_MIN_SIZE:
        return ContainerType.SECTION
    if size >= _SUBSECTION_MIN_SIZE:
        return ContainerType.SUBSECTION
    return ContainerType.ENTRY


# Tier ordering for popping the container stack: SECTION outranks SUBSECTION
# outranks ENTRY. A new heading pops all containers at its tier or below.
_TIER_RANK = {
    ContainerType.SECTION: 0,
    ContainerType.SUBSECTION: 1,
    ContainerType.ENTRY: 2,
}


def _dehyphenate_join(acc: str, nxt: str) -> str:
    """Join a wrapped continuation line, repairing hyphenation (Component F)."""
    if acc.endswith("-") and not acc.endswith(("--", "- ")):
        return acc[:-1] + nxt
    return f"{acc} {nxt}" if acc else nxt


class _LedgerBuilder:
    def __init__(self) -> None:
        self.containers: list[Container] = []
        self._seen_container_ids: set[str] = set()
        self.leaves: list[Leaf] = []
        self._stack: list[Container] = []
        self._occurrence = 0

    def _push_container(self, line: PageLine) -> None:
        ctype = _container_type_for_size(line.size)
        rank = _TIER_RANK[ctype]
        while self._stack and _TIER_RANK[self._stack[-1].container_type] >= rank:
            self._stack.pop()
        parent = self._stack[-1].container_id if self._stack else None
        cid = content_id("container", ctype.value, line.text, line.printed_page, parent)
        container = Container(
            container_id=cid,
            container_type=ctype,
            label=line.text,
            printed_page=line.printed_page,
            parent_id=parent,
        )
        self._stack.append(container)
        if cid not in self._seen_container_ids:
            self._seen_container_ids.add(cid)
            self.containers.append(container)

    def _path(self) -> tuple[str, ...]:
        return tuple(c.container_id for c in self._stack)

    def _in_stat_entry(self) -> bool:
        return (
            bool(self._stack) and self._stack[-1].container_type is ContainerType.ENTRY
        )

    def _emit(
        self, leaf_type: LeafType, content: str, anchor: PageLine, end: int
    ) -> None:
        """Record a leaf spanning [anchor.char_start, end) on anchor's page."""
        self._emit_span(
            leaf_type,
            content,
            anchor.printed_page,
            anchor.page_index,
            anchor.char_start,
            end,
        )

    def _emit_span(
        self,
        leaf_type: LeafType,
        content: str,
        printed_page: int,
        page_index: int,
        char_start: int,
        char_end: int,
        *,
        table_id: str | None = None,
        table_row: int | None = None,
        table_col: int | None = None,
    ) -> None:
        """Record a leaf spanning [char_start, char_end) with optional table pos."""
        leaf_id = content_id(
            "leaf", printed_page, char_start, char_end, leaf_type.value, content
        )
        self.leaves.append(
            Leaf(
                leaf_id=leaf_id,
                printed_page=printed_page,
                page_index=page_index,
                leaf_type=leaf_type,
                content=content,
                char_start=char_start,
                char_end=char_end,
                occurrence_index=self._occurrence,
                container_path=self._path(),
                table_id=table_id,
                table_row=table_row,
                table_col=table_col,
            )
        )
        self._occurrence += 1

    def _emit_table(self, page: ExtractedPage, table: DetectedTable) -> None:
        """Emit a TABLE container + one TABLE_CELL leaf per cell (Component F).

        The table nests under the current container stack; each cell's char span
        comes from the reconstructed grid, so the cells tile exactly the same
        characters the region's lines would otherwise occupy (no cell also becomes
        a paragraph leaf). Cells are emitted in (row, col) order.
        """
        cid = table.table_id
        container = Container(
            container_id=cid,
            container_type=ContainerType.TABLE,
            label=self._table_label(page, table),
            printed_page=table.printed_page,
            parent_id=self._stack[-1].container_id if self._stack else None,
        )
        self._stack.append(container)
        if cid not in self._seen_container_ids:
            self._seen_container_ids.add(cid)
            self.containers.append(container)
        for cell in table.cells:
            self._emit_span(
                LeafType.TABLE_CELL,
                cell.text,
                table.printed_page,
                page.page_index,
                cell.char_start,
                cell.char_end,
                table_id=cid,
                table_row=cell.row,
                table_col=cell.col,
            )
        self._stack.pop()

    @staticmethod
    def _table_label(page: ExtractedPage, table: DetectedTable) -> str:
        """Deterministic table label: its header (row-0) cell texts joined."""
        header = [c.text for c in table.cells if c.row == 0]
        return " | ".join(header) if header else f"table p{table.printed_page}"

    def add_page(self, page: ExtractedPage) -> None:
        lines = page.lines
        # Reconstructed tables map to contiguous line-index ranges; a table's
        # lines are consumed as TABLE_CELL leaves and skipped by the paragraph/
        # list/stat branches so no cell also becomes a paragraph leaf.
        detected = detect_page_tables(page)
        tables_by_start = {t.start_line: t for t in detected}
        table_end_by_start = {t.start_line: t.end_line for t in detected}
        table_lines = {
            idx for t in detected for idx in range(t.start_line, t.end_line + 1)
        }
        i = 0
        n = len(lines)
        while i < n:
            if i in tables_by_start:
                self._emit_table(page, tables_by_start[i])
                i = table_end_by_start[i] + 1
                continue
            line = lines[i]
            if _is_header_footer(line):
                self._emit(LeafType.HEADER_FOOTER, line.text, line, line.char_end)
                i += 1
                continue
            if _is_heading(line):
                self._push_container(line)
                self._emit(LeafType.HEADING, line.text, line, line.char_end)
                i += 1
                continue
            if _ATTRIBUTION_RE.search(line.text):
                self._emit(LeafType.ATTRIBUTION, line.text, line, line.char_end)
                i += 1
                continue
            if self._in_stat_entry() and _STAT_FIELD_RE.match(line.text):
                self._emit(LeafType.STAT_FIELD, line.text, line, line.char_end)
                i += 1
                continue
            is_list = bool(_LIST_MARKER_RE.match(line.text))
            leaf_type = LeafType.LIST_ITEM if is_list else LeafType.PARAGRAPH
            # Merge wrapped continuation lines into this block.
            content = line.text
            end = line.char_end
            prev = line
            j = i + 1
            while j < n:
                nxt = lines[j]
                if (
                    j in table_lines
                    or _is_header_footer(nxt)
                    or _is_heading(nxt)
                    or _ATTRIBUTION_RE.search(nxt.text)
                    or _LIST_MARKER_RE.match(nxt.text)
                    or (self._in_stat_entry() and _STAT_FIELD_RE.match(nxt.text))
                ):
                    break
                step = nxt.top - prev.top
                if step <= 0 or step > _PARA_GAP_MAX:
                    break
                content = _dehyphenate_join(content, nxt.text)
                end = nxt.char_end
                prev = nxt
                j += 1
            self._emit(leaf_type, content, line, end)
            i = j

    def build(self) -> SourceLedger:
        return SourceLedger(
            source_document=SOURCE_DOCUMENT,
            source_version=SOURCE_VERSION,
            source_sha256=PDF_SHA256,
            extraction_config=extraction_config(),
            containers=tuple(self.containers),
            leaves=tuple(self.leaves),
        )


def build_ledger(pages: list[ExtractedPage]) -> SourceLedger:
    """Build the frozen source ledger from extracted pages (Component C)."""
    builder = _LedgerBuilder()
    for page in pages:
        builder.add_page(page)
    return builder.build()


def ledger_payload(ledger: SourceLedger) -> dict[str, object]:
    """Canonical hashable representation of the ledger."""
    return {
        "source_document": ledger.source_document,
        "source_version": ledger.source_version,
        "source_sha256": ledger.source_sha256,
        "extraction_config": ledger.extraction_config,
        "containers": [
            {
                "container_id": c.container_id,
                "container_type": c.container_type.value,
                "label": c.label,
                "printed_page": c.printed_page,
                "parent_id": c.parent_id,
            }
            for c in ledger.containers
        ],
        "leaves": [
            {
                "leaf_id": leaf.leaf_id,
                "printed_page": leaf.printed_page,
                "page_index": leaf.page_index,
                "leaf_type": leaf.leaf_type.value,
                "content": leaf.content,
                "char_start": leaf.char_start,
                "char_end": leaf.char_end,
                "occurrence_index": leaf.occurrence_index,
                "container_path": list(leaf.container_path),
                "table_id": leaf.table_id,
                "table_row": leaf.table_row,
                "table_col": leaf.table_col,
            }
            for leaf in ledger.leaves
        ],
    }


def ledger_hash(ledger: SourceLedger) -> str:
    """SHA-256 of the ledger's canonical payload (frozen at K a1)."""
    return hash_obj(ledger_payload(ledger))
