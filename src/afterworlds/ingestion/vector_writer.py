"""Vector write path — ChromaDB interim implementation.

INTERIM COLLECTION SCHEMA — subject to revision in CRD Issue 18
================================================================
Collection: "rp_chunks_interim_{package_id_short}"
  where package_id_short = first 8 chars of the package UUID (no hyphens).

Metadata per document:
  - package_id      : str  — full rules_package_id UUID string
  - chunk_id        : str  — full chunk_id UUID string
  - subsystem       : str  — RuleSubsystemEnum value
  - source_document : str  — source document name

Embedding model: ChromaDB default (all-MiniLM-L6-v2)

KNOWN UNKNOWN: collection naming convention, metadata field set, embedding
model selection, chunking strategy, and retrieval scoring thresholds are all
designated for revision in CRD Issue 18.  The schema here is intentionally
minimal to unblock CRD Issue 5b testing without pre-empting Issue 18 design
decisions.  Do not build downstream logic that depends on the collection name
format or metadata field names defined in this file — treat both as unstable
until CRD Issue 18 is complete.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

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

    KNOWN UNKNOWN: naming convention — see module docstring.
    """
    full_hex = package_id.replace("-", "")
    return f"{_COLLECTION_PREFIX}{full_hex}"


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------


@dataclass
class QueryResult:
    """Result of a semantic query against a package's vector collection."""

    chunk_ids: list[str]
    distances: list[float]
    documents: list[str]


# ---------------------------------------------------------------------------
# VectorWriter
# ---------------------------------------------------------------------------


class VectorWriter:
    """Interim ChromaDB write/query path for rule chunks.

    KNOWN UNKNOWN: collection schema, naming, metadata fields, and embedding
    model are all designated for CRD Issue 18 revision.

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
        self, chunks: list[ParsedChunk], package_id: str, chunk_ids: list[str]
    ) -> None:
        """Upsert parsed chunks into the interim ChromaDB collection.

        Parameters
        ----------
        chunks:
            List of ParsedChunk records to write.
        package_id:
            The rules_package_id string (UUID format).
        chunk_ids:
            Parallel list of chunk UUIDs (as strings) corresponding to each
            entry in *chunks*.  Must be the same length as *chunks*.

        Notes
        -----
        Uses ChromaDB ``upsert`` so re-running ingestion is idempotent at
        the vector layer — existing documents are overwritten rather than
        duplicated.

        KNOWN UNKNOWN: See module docstring for schema caveats.
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
                "source_document": chunk.section_path,
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
        source_locators: list[str],
    ) -> None:
        """Upsert chunk data supplied as plain lists (no ParsedChunk required).

        Used by the re-ingest repopulation path, which reads data from SQL rows
        rather than from a fresh parse.  Metadata fields mirror ``write_chunks``.

        KNOWN UNKNOWN: See module docstring for schema caveats.
        """
        if not chunk_ids:
            return
        collection = self._get_or_create_collection(package_id)
        metadatas: list[_Metadata] = [
            {
                "package_id": package_id,
                "chunk_id": cid,
                "subsystem": sub,
                "source_document": loc,
            }
            for cid, sub, loc in zip(
                chunk_ids, subsystems, source_locators, strict=True
            )
        ]
        collection.upsert(documents=contents, metadatas=metadatas, ids=chunk_ids)

    def query(
        self,
        query_text: str,
        package_id: str,
        n_results: int = 5,
    ) -> QueryResult:
        """Basic semantic query against the package's interim collection.

        Returns up to *n_results* nearest neighbours.

        KNOWN UNKNOWN: scoring thresholds and retrieval strategy — see module
        docstring.
        """
        collection = self._get_or_create_collection(package_id)
        count = collection.count()
        if count == 0:
            return QueryResult(chunk_ids=[], distances=[], documents=[])
        actual_n = min(n_results, count)
        results = collection.query(
            query_texts=[query_text],
            n_results=actual_n,
        )
        chunk_ids: list[str] = []
        distances: list[float] = []
        documents: list[str] = []
        if results["ids"] and results["ids"][0]:
            chunk_ids = list(results["ids"][0])
        if results["distances"] and results["distances"][0]:
            distances = [float(d) for d in results["distances"][0]]
        if results["documents"] and results["documents"][0]:
            documents = [str(d) for d in results["documents"][0]]
        return QueryResult(
            chunk_ids=chunk_ids, distances=distances, documents=documents
        )

    def has_chunks(self, package_id: str) -> bool:
        """Return True if the collection for *package_id* has any documents."""
        try:
            collection = self._client.get_collection(_collection_name(package_id))
            return int(collection.count()) > 0
        except Exception:
            return False
