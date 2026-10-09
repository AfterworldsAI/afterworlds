"""Bounded embedding documents for a rules corpus -- CRD Issue 5c / ADR-018 D11.

The local ONNX MiniLM embedding function truncates its own input: the installed
``chromadb/utils/embedding_functions/onnx_mini_lm_l6_v2.py`` calls
``tokenizer.enable_truncation(max_length=256)`` before it encodes. A chunk sent
whole is therefore embedded from its opening alone, and everything past the
ceiling is unreachable by any query -- silently, because the stored document
still reads back complete. 494 of the 10,465 units in the SRD 5.2.1 corpus are
over that ceiling; Weapons is 2,865 tokens and stops embedding at character 644
of 7,154.

This module derives the embedding input rather than changing what is stored.
Two steps, both deterministic:

* :func:`visible_text` reduces a unit to the text a reader sees. Most of the
  cost in a long unit is markup -- stripping the HTML table tags alone takes the
  over-ceiling count from 494 to 24 -- and a ``<td>`` boundary carries no
  meaning an embedding can use.
* :func:`derive_windows` packs that text into windows small enough to survive
  the ceiling, breaking on line boundaries so a table row stays whole, and
  prefixes each with the chunk's section label so a window taken from the middle
  of a long unit still says what it is about.

The authoritative unit is untouched. Every window names the chunk it came from,
and the query path hydrates the stored ``content`` back out of SQL, so a hit on
window 9 of Trinkets returns Trinkets with its own citation.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from uuid import UUID

from afterworlds.models.enums import SourceLocatorTypeEnum
from afterworlds.models.retrieval import (
    RulesCorpusChunkMetadata,
    build_rules_corpus_window_id,
)
from afterworlds.persistence.orm.rules_package import RuleChunkORM

#: Total character ceiling for one embedding document, section label included.
#:
#: ponytail: a character budget, not a token count. The writer has no tokenizer
#: -- the embedding function owns it, and the deterministic fake used by the
#: lifecycle tests has none at all -- so counting tokens here would either
#: import a second copy of the model's tokenizer or couple the writer to one
#: embedder's internals. The number is chosen by measurement, not arithmetic:
#: at 448 the densest of the corpus's 11,076 windows encodes to 189 tokens, a
#: 26% margin under the ceiling, and only 499 of 10,465 units need more than
#: one window at all. 700 was measured too (10,569 windows, densest 246) and
#: rejected -- ten tokens of margin is not margin. ``test_corpus_windows.py``
#: re-measures every window through the real tokenizer; that test, not this
#: constant, is the guarantee.
#:
#: Ceiling: this bounds SRD-like prose and tables. A custom Rules Package whose
#: text is denser than anything in the SRD (dense punctuation or symbol runs
#: approach one token per character) could still exceed 256 tokens in one
#: window. Lower the budget, or tokenize at write time behind an optional
#: embedder capability, if such a package ever appears.
WINDOW_CHAR_BUDGET: int = 448

#: Block-level closers become a line break so a table row, list item or
#: paragraph survives as one line and the packer never splits inside one.
_ROW_END = re.compile(r"</(?:tr|h[1-6]|p|li|div|caption)>")
_TAG = re.compile(r"<[^>]*>")
_SPACES = re.compile(r"[ \t]+")


@dataclass(frozen=True)
class RetrievalWindow:
    """One bounded embedding document derived from one chunk."""

    #: Position within the chunk's own windows, counting from zero.
    index: int
    #: How many windows the chunk produced, so a consumer knows what it has.
    count: int
    #: The text actually sent to the embedding function.
    text: str


def visible_text(content: str) -> str:
    """Reduce a chunk to the text a reader sees, one block per line.

    Tags become whitespace rather than nothing so ``<td>a</td><td>b</td>`` does
    not fuse into ``ab``. Blank lines are dropped; line breaks between blocks
    are what the packer breaks on.
    """
    text = _ROW_END.sub("\n", content)
    text = _TAG.sub(" ", text)
    text = _SPACES.sub(" ", text)
    return "\n".join(line.strip() for line in text.split("\n") if line.strip())


def _split_oversized(line: str, budget: int) -> list[str]:
    """Break one over-budget line on word boundaries, then hard if it has none."""
    if len(line) <= budget:
        return [line]
    pieces: list[str] = []
    current = ""
    for word in line.split(" "):
        while len(word) > budget:
            if current:
                pieces.append(current)
                current = ""
            pieces.append(word[:budget])
            word = word[budget:]
        if current and len(current) + 1 + len(word) > budget:
            pieces.append(current)
            current = ""
        current = f"{current} {word}" if current else word
    if current:
        pieces.append(current)
    return pieces


def derive_windows(
    content: str,
    section_label: str | None = None,
    budget: int = WINDOW_CHAR_BUDGET,
) -> list[RetrievalWindow]:
    """Derive the bounded embedding documents for one chunk's *content*.

    Deterministic in ``(content, section_label, budget)`` alone: the same chunk
    yields the same windows in the same order on every rebuild, so a window's
    index is part of a stable identity rather than a per-run ordinal.

    Always returns at least one window, even for empty content, so every chunk
    stays represented in the collection and the count check downstream is a
    simple equality rather than a special case.
    """
    prefix = (section_label or "").strip()
    body_budget = max(budget - len(prefix) - 1, 1) if prefix else budget

    lines = visible_text(content).split("\n") if content.strip() else []
    packed: list[str] = []
    current: list[str] = []
    size = 0
    for line in lines:
        for piece in _split_oversized(line, body_budget):
            if current and size + 1 + len(piece) > body_budget:
                packed.append("\n".join(current))
                current, size = [], 0
            size += len(piece) + (1 if current else 0)
            current.append(piece)
    if current:
        packed.append("\n".join(current))
    if not packed:
        packed = [""]

    count = len(packed)
    return [
        RetrievalWindow(
            index=index,
            count=count,
            text=f"{prefix}\n{body}" if prefix else body,
        )
        for index, body in enumerate(packed)
    ]


def derive_retrieval_documents(
    row: RuleChunkORM,
    rules_package_id: UUID,
    embedding_model_id: str,
    budget: int = WINDOW_CHAR_BUDGET,
) -> list[tuple[str, str, RulesCorpusChunkMetadata]]:
    """Every ``(doc_id, document, metadata)`` one persisted chunk contributes.

    The single place the SQL row -> Chroma document mapping is defined. The
    reindex writer and ``vector_publication.expected_vector_state_from_sql``
    both call it, so the published state and the state it is verified against
    cannot drift apart into a tautology -- they agree because they are the same
    function, not because two hand-written loops were kept in step.
    """
    windows = derive_windows(row.content, row.source_section_label, budget)
    return [
        (
            build_rules_corpus_window_id(
                rules_package_id, UUID(row.chunk_id), window.index
            ),
            window.text,
            RulesCorpusChunkMetadata(
                rules_package_id=rules_package_id,
                subsystem=row.subsystem,
                source_document=row.source_document,
                source_locator_type=SourceLocatorTypeEnum(row.source_locator_type),
                source_locator_value=row.source_locator_value,
                embedding_model_id=embedding_model_id,
                source_chunk_id=row.chunk_id,
                window_index=window.index,
                window_count=window.count,
            ),
        )
        for window in windows
    ]
