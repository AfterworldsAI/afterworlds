"""Generic-ingestion vector projection — write-only, non-runtime, non-authoritative.

GitHub #121 disposition (after CRD Issue 18 / ADR-018 D10)
==========================================================
This is the retained CRD Issue 5b interim writer. It is **not** the rules
corpus and **not** a rules authority:

* It is write-only. It has no reader, and must never gain one: the superseded
  interim reader (``query()``) was removed under the pre-release clean baseline.
* Its only caller is the generic ``IngestionService``: ``ingest`` writes the
  projection and ``publish`` compares its document count to the SQL chunk count
  as an internal-consistency gate. No Context Builder, RPG adjudication,
  Planner, Writer or pass service imports it or reads its collections.
* The finalized rules corpus is ``rules_corpus_{package_id_hex}``, rebuilt only
  from ``rp_chunks`` SQLite ground truth by
  ``RulesCorpusService.reindex_from_sql``, independently of whether this
  projection exists or what it contains. Its only reader is the
  publication-gated ``RulesCorpusService.diagnostic_query``.
* Runtime mechanical rules authority is exclusively ``get_active_rule_slice``.

Collection: "rp_chunks_interim_{package_id_hex}" (full 32-hex-char UUID,
hyphens stripped). The name is kept so existing stores are not orphaned.
Metadata per document: ``package_id``, ``chunk_id``, ``subsystem``,
``source_document``. Embedding model: ChromaDB default.
"""

from __future__ import annotations

import contextlib
from collections.abc import Mapping

from chromadb.api import ClientAPI as ChromaClientAPI
from chromadb.api.models.Collection import Collection as ChromaCollection
from chromadb.base_types import SparseVector

from afterworlds.ingestion.srd_parser import ParsedChunk

# ChromaDB metadata value type for a single field
_ScalarList = list[str | int | float | bool]
_MetaValue = str | int | float | bool | SparseVector | _ScalarList | None
# ChromaDB metadata dict type
_Metadata = Mapping[str, _MetaValue]

# ---------------------------------------------------------------------------
# Collection naming helper
# ---------------------------------------------------------------------------

_COLLECTION_PREFIX = "rp_chunks_interim_"


def _collection_name(package_id: str) -> str:
    """Derive the interim collection name from a package UUID string.

    Uses the full 32-hex-char UUID (hyphens stripped) to guarantee
    collision-freedom across all packages.
    """
    full_hex = package_id.replace("-", "")
    return f"{_COLLECTION_PREFIX}{full_hex}"


# ---------------------------------------------------------------------------
# VectorWriter
# ---------------------------------------------------------------------------


class VectorWriter:
    """Write-only generic-ingestion projection of rule chunks (see module docstring).

    Deliberately exposes no query/read method: nothing may consume this
    projection as rules content. ``count_chunks``/``has_chunks`` exist only for
    the ``IngestionService`` consistency gate. The supported diagnostic reader
    is ``RulesCorpusService.diagnostic_query()`` over the finalized corpus.

    Parameters
    ----------
    client:
        A ChromaDB client instance (``chromadb.PersistentClient``,
        ``chromadb.EphemeralClient``, etc.).
    """

    def __init__(self, client: ChromaClientAPI) -> None:
        self._client = client

    def _get_or_create_collection(self, package_id: str) -> ChromaCollection:
        name = _collection_name(package_id)
        result: ChromaCollection = self._client.get_or_create_collection(name)
        return result

    def write_chunks(
        self,
        chunks: list[ParsedChunk],
        package_id: str,
        chunk_ids: list[str],
        source_document_name: str,
    ) -> None:
        """Upsert parsed chunks into the generic-ingestion projection.

        Parameters
        ----------
        chunks:
            List of ParsedChunk records to write.
        package_id:
            The rules_package_id string (UUID format).
        chunk_ids:
            Parallel list of chunk UUIDs (as strings) corresponding to each
            entry in *chunks*.  Must be the same length as *chunks*.
        source_document_name:
            The source file name stored in the ``source_document`` metadata
            field (e.g. ``"srd_5e.json"``).

        Notes
        -----
        Uses ChromaDB ``upsert`` so re-running ingestion is idempotent at
        the vector layer — existing documents are overwritten rather than
        duplicated.
        """
        if not chunks:
            return
        collection = self._get_or_create_collection(package_id)
        documents: list[str] = []
        metadatas: list[_Metadata] = []
        ids: list[str] = []
        for chunk, cid in zip(chunks, chunk_ids, strict=True):
            documents.append(chunk.content)
            meta: _Metadata = {
                "package_id": package_id,
                "chunk_id": cid,
                "subsystem": chunk.subsystem.value,
                "source_document": source_document_name,
            }
            metadatas.append(meta)
            ids.append(cid)
        collection.upsert(documents=documents, metadatas=metadatas, ids=ids)

    def write_chunks_raw(
        self,
        package_id: str,
        chunk_ids: list[str],
        contents: list[str],
        subsystems: list[str],
        source_documents: list[str],
    ) -> None:
        """Upsert chunk data supplied as plain lists (no ParsedChunk required).

        Used by the re-ingest repopulation path, which reads data from SQL rows
        rather than from a fresh parse.  Metadata fields mirror ``write_chunks``.

        Parameters
        ----------
        source_documents:
            Parallel list of source file names for the ``source_document``
            metadata field.  Must match the ``source_document`` column from
            the corresponding SQL rows.
        """
        if not chunk_ids:
            return
        collection = self._get_or_create_collection(package_id)
        metadatas: list[_Metadata] = [
            {
                "package_id": package_id,
                "chunk_id": cid,
                "subsystem": sub,
                "source_document": doc,
            }
            for cid, sub, doc in zip(
                chunk_ids, subsystems, source_documents, strict=True
            )
        ]
        collection.upsert(documents=contents, metadatas=metadatas, ids=chunk_ids)

    def count_chunks(self, package_id: str) -> int:
        """Return the number of documents in the collection for *package_id*.

        Returns 0 if the collection does not exist or cannot be accessed.
        """
        try:
            collection = self._client.get_collection(_collection_name(package_id))
            return int(collection.count())
        except Exception:
            return 0

    def has_chunks(self, package_id: str) -> bool:
        """Return True if the collection for *package_id* has any documents."""
        return self.count_chunks(package_id) > 0

    def delete_collection(self, package_id: str) -> None:
        """Delete the Chroma collection for *package_id* if it exists.

        Used by the repopulation path before rebuilding from SQL ground truth
        to ensure surplus documents are removed.  No-op if the collection does
        not exist.
        """
        with contextlib.suppress(Exception):
            self._client.delete_collection(_collection_name(package_id))
