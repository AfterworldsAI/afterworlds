"""Independent expected-table inventory — CRD Issue 5c, Component E/F, PR #134 R15 F4.

The Round-14/earlier table concordance re-ran the detector at gate time and
compared it to itself, so a table the detector *fails to emit* (suppressed or
flattened) was absent from both producer and checker and could never fail. This
module supplies a genuinely detector-independent oracle: a **committed, frozen
inventory** of every expected logical table (page span, header, column count,
logical row count, segment count, and a hash over the exact cell detail),
compared at gate/check time against the live reconstruction. Because the expected
set is frozen bytes on disk — not recomputed by :func:`assemble_tables` /
:func:`detect_page_tables` at check time — a detector regression that suppresses,
flattens, fragments, merges, or invents a table makes the live set diverge from
the committed one and fails.

Provenance / regeneration (recorded, not hand-authored): the inventory is the
deterministic output of :func:`build_table_inventory` over the committed
authoritative PDF with the frozen extraction + detection code, written to
:data:`INVENTORY_PATH`. Regenerate with ``python scripts/regen_table_inventory.py``
after an intentional, reviewed table-reconstruction change; the committed file is
then the reviewed expectation. Non-table shaded prose is excluded by construction
(detection drops it to paragraph segmentation, so it never enters the inventory),
which is how the oracle distinguishes expected tables from prose. The inventory
file's hash is bound into the transform/configuration identity
(``bundle.transform_config_payload``), so changing the expected tables mints a new
immutable release.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from afterworlds.ingestion.corpus.hashing import hash_obj
from afterworlds.ingestion.corpus.pdf_source import ExtractedPage
from afterworlds.ingestion.corpus.tables import LogicalTable, assemble_tables

INVENTORY_PATH = Path(__file__).with_name("srd_table_inventory.json")


def _cells_hash(lt: LogicalTable) -> str:
    """Hash over the exact cell detail of a logical table.

    Covers every cell's (segment, logical row, column, continuation-header flag,
    text), so flattening (lost/merged cells), fragmenting (changed rows), or any
    text change moves the hash even when the header/page/shape is unchanged.
    """
    return hash_obj(
        [
            [
                seg.segment_index,
                cell.logical_row,
                cell.col,
                cell.is_continuation_header,
                cell.text,
            ]
            for seg in lt.segments
            for cell in seg.cells
        ]
    )


def logical_table_record(lt: LogicalTable) -> dict[str, object]:
    """The committed inventory record for one logical table."""
    return {
        "logical_table_id": lt.logical_table_id,
        "printed_pages": list(lt.printed_pages),
        "header": list(lt.header),
        "column_count": lt.column_count,
        "logical_row_count": lt.logical_row_count,
        "segment_count": len(lt.segments),
        "cells_hash": _cells_hash(lt),
    }


def build_table_inventory(pages: list[ExtractedPage]) -> list[dict[str, object]]:
    """Deterministic expected-table inventory from *pages* (the regen procedure)."""
    records = [logical_table_record(lt) for lt in assemble_tables(pages)]
    records.sort(key=lambda r: str(r["logical_table_id"]))
    return records


def inventory_hash(inventory: list[dict[str, object]]) -> str:
    """Content hash of an inventory (order-independent; sorted by table id)."""
    return hash_obj(sorted(inventory, key=lambda r: str(r["logical_table_id"])))


def load_committed_inventory() -> list[dict[str, object]]:
    """Load the frozen committed expected-table inventory (fails closed if absent)."""
    data = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))
    return list(data["tables"])


def committed_inventory_hash() -> str:
    """Hash of the committed inventory — bound into the transform identity."""
    return inventory_hash(load_committed_inventory())


@dataclass(frozen=True)
class InventoryComparison:
    """Result of comparing the live reconstruction against the committed oracle."""

    expected: int
    live: int
    matched: int
    suppressed: tuple[str, ...]  # expected tables absent from the live set
    invented: tuple[str, ...]  # live tables absent from the expected set
    mismatched: tuple[str, ...]  # same id, differing structure/cells

    @property
    def passed(self) -> bool:
        return not self.suppressed and not self.invented and not self.mismatched


def compare_to_inventory(
    live: list[dict[str, object]], expected: list[dict[str, object]]
) -> InventoryComparison:
    """Compare a live inventory against the expected (committed) one.

    Keyed on ``logical_table_id``: a suppressed/flattened table is missing or
    differs (suppressed / mismatched), a fragmented one splits into a mismatched
    survivor plus an invented fragment, a merge yields invented + suppressed, and
    an invented table appears with an unknown id. Any of these fails ``passed``.
    """
    live_by_id = {str(r["logical_table_id"]): r for r in live}
    exp_by_id = {str(r["logical_table_id"]): r for r in expected}
    suppressed = tuple(sorted(set(exp_by_id) - set(live_by_id)))
    invented = tuple(sorted(set(live_by_id) - set(exp_by_id)))
    mismatched = tuple(
        sorted(
            tid
            for tid in set(exp_by_id) & set(live_by_id)
            if live_by_id[tid] != exp_by_id[tid]
        )
    )
    matched = len(set(exp_by_id) & set(live_by_id)) - len(mismatched)
    return InventoryComparison(
        expected=len(expected),
        live=len(live),
        matched=matched,
        suppressed=suppressed,
        invented=invented,
        mismatched=mismatched,
    )


def check_against_committed_inventory(
    pages: list[ExtractedPage],
) -> InventoryComparison:
    """Compare the live full-PDF reconstruction against the committed oracle."""
    return compare_to_inventory(
        build_table_inventory(pages), load_committed_inventory()
    )
