"""RulesCorpusService — CRD Issue 18 / ADR-018 D10/D11.

Finalizes the rules-corpus Chroma schema and reindexes the CRD Issue 5b
interim collection (``rp_chunks_interim_{package_id_hex}``,
``ingestion/vector_writer.py``) into the finalized per-Rules-Package
``rules_corpus_{package_id_hex}`` collection, rebuilt from the SQLite
``rp_chunks`` ground truth — never from the interim Chroma collection
itself (Central Invariant: Chroma is a rebuildable SQLite-derived
projection).

The diagnostic query exposed here is internal/admin-only in v1 (D10): no
Context Builder, RPG adjudication loop, Writer, Planner, pass service, or
runtime mechanical decision may consume it. Runtime rule inclusion remains
exclusively ``get_active_rule_slice`` (CLAUDE.md invariant 8).
"""

from __future__ import annotations

from collections.abc import Mapping
from uuid import UUID

from chromadb.api import ClientAPI
from sqlalchemy import select
from sqlalchemy.orm import Session

from afterworlds.models.enums import SourceLocatorTypeEnum
from afterworlds.models.retrieval import (
    RulesCorpusChunkMetadata,
    build_rules_corpus_chunk_id,
    rules_corpus_collection_name,
)
from afterworlds.persistence.orm.rules_package import RuleChunkORM
from afterworlds.pipeline.retrieval.collections import (
    delete_collection_ignoring_absence,
    get_rules_corpus_collection,
)
from afterworlds.pipeline.retrieval.config import RetrievalMemoryConfig
from afterworlds.pipeline.retrieval.embedding import RetrievalEmbeddingFunction

#: Maximum documents per Chroma add/upsert call. Chroma enforces its own
#: ``max_batch_size`` (5461 on the pinned build); staying under it lets a
#: full-corpus reindex (~13.6k chunks) proceed in bounded batches. Chunking the
#: write does not change stored IDs, content, or metadata.
_MAX_UPSERT_BATCH = 5000


class RulesCorpusService:
    """Reindex/diagnostic-query path for the finalized rules_corpus collections."""

    def __init__(
        self,
        client: ClientAPI,
        config: RetrievalMemoryConfig,
        embedding_function: RetrievalEmbeddingFunction | None = None,
    ) -> None:
        self._client = client
        self._config = config
        self._embedding_function = embedding_function

    def reindex_from_sql(self, session: Session, rules_package_id: UUID) -> int:
        """Rebuild the finalized rules_corpus collection from SQL ground truth.

        Wipes the collection first (surplus removal) then re-upserts every
        enabled ``RuleChunk`` row for *rules_package_id*. This absorbs the
        CRD Issue 5b interim collection without mutating any 5a source
        record. Returns the number of chunks written.

        Raises:
            Whatever ``delete_collection_ignoring_absence`` propagates (any
                operational Chroma failure besides a genuinely absent
                collection) — rebuild must never proceed past a wipe that
                may not have actually happened (Codex review, PR #119 round
                7), since stale disabled/deleted chunks would then remain
                silently retrievable through the diagnostic query.
        """
        collection_name = rules_corpus_collection_name(rules_package_id)
        delete_collection_ignoring_absence(self._client, collection_name)
        collection = get_rules_corpus_collection(
            self._client, collection_name, self._config, self._embedding_function
        )

        rows = (
            session.execute(
                select(RuleChunkORM)
                .where(RuleChunkORM.rules_package_id == str(rules_package_id))
                .where(RuleChunkORM.is_enabled.is_(True))
            )
            .scalars()
            .all()
        )
        if not rows:
            return 0

        ids: list[str] = []
        documents: list[str] = []
        metadatas: list[Mapping[str, str | int | float | bool | None]] = []
        for row in rows:
            locator_type = SourceLocatorTypeEnum(row.source_locator_type)
            metadata = RulesCorpusChunkMetadata(
                rules_package_id=rules_package_id,
                subsystem=row.subsystem,
                source_document=row.source_document,
                source_locator_type=locator_type,
                source_locator_value=row.source_locator_value,
                embedding_model_id=self._config.embedding_model_id,
            )
            # ID derives from RuleChunkORM.chunk_id -- the row's own durable
            # primary key -- not a per-run occurrence index (Codex review,
            # PR #119 round 4): stable regardless of SQL row-iteration order
            # or how many chunks share the same source locator.
            ids.append(
                build_rules_corpus_chunk_id(rules_package_id, UUID(row.chunk_id))
            )
            documents.append(row.content)
            metadatas.append(metadata.model_dump(mode="json"))

        # Chroma caps a single add/upsert at ``max_batch_size`` (a few thousand);
        # a full Rules Package corpus (CRD Issue 5c: ~13.6k chunks) exceeds it in
        # one call. Upsert in bounded batches so a large package reindexes without
        # a ValueError. Schema, deterministic IDs, and metadata are unchanged —
        # only the write is chunked (Codex review, PR #134).
        for start in range(0, len(ids), _MAX_UPSERT_BATCH):
            stop = start + _MAX_UPSERT_BATCH
            collection.upsert(
                documents=documents[start:stop],
                metadatas=metadatas[start:stop],  # type: ignore[arg-type]
                ids=ids[start:stop],
            )
        return len(rows)

    def diagnostic_query(
        self, rules_package_id: UUID, query_text: str, n_results: int = 5
    ) -> list[str]:
        """Internal/admin-only semantic lookup. Never consumed by a runtime pass.

        Returns raw matched documents with no threshold filtering — this is
        a discovery/diagnostic surface, not a retrieval-eligibility path.
        """
        collection_name = rules_corpus_collection_name(rules_package_id)
        collection = get_rules_corpus_collection(
            self._client, collection_name, self._config, self._embedding_function
        )
        count = collection.count()
        if count == 0:
            return []
        results = collection.query(
            query_texts=[query_text], n_results=min(n_results, count)
        )
        documents_lists = results.get("documents") or []
        if not documents_lists or not documents_lists[0]:
            return []
        return [str(d) for d in documents_lists[0]]
