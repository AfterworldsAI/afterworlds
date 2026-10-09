"""Canonical ledger payload and hash — CRD Issue 5c, Component C.

The ledger is frozen and hashed (K a1) before any output-dependent
reconciliation; :func:`ledger_hash` is the identity that binds it into the
release. The current ledger is built from the qualified Markdown source by
:mod:`afterworlds.ingestion.corpus.source_ledger`.

The original PDF-geometric ledger builder that also lived here was retired with
its corpus under the Recorded Owner Decision of 21 September 2026; Git history
retains it. The payload keeps its table fields because they are part of the
canonical shape every recorded ledger hash was computed over.
"""

from __future__ import annotations

from afterworlds.ingestion.corpus.hashing import hash_obj
from afterworlds.ingestion.corpus.models import SourceLedger


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
                "table_segment": leaf.table_segment,
            }
            for leaf in ledger.leaves
        ],
    }


def ledger_hash(ledger: SourceLedger) -> str:
    """SHA-256 of the ledger's canonical payload (frozen at K a1)."""
    return hash_obj(ledger_payload(ledger))
