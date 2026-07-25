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
from chromadb.utils.batch_utils import create_batches
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

        The rebuild is exception-safe at this public boundary. The initial wipe
        stays outside the compensation scope (an operational wipe failure
        propagates without touching the old collection). Once the wipe succeeds,
        the old collection is gone, so every collection this method then creates
        or partially populates is this attempt's responsibility: if creation, row
        transformation, embedding/upsert, or any later batch fails before the
        complete rebuild lands, the attempt's (possibly partially populated)
        collection is removed and the failure propagates -- a partial collection
        that contradicts SQLite ground truth is never left queryable through the
        diagnostic surface (PR #134 P2, sibling of the finalize cross-store
        cleanup). Cleanup is disarmed only after every batch succeeds, or after a
        legitimate zero-row rebuild completes with an empty collection. This does
        not weaken ``finalize_release``'s outer boundary -- that redundant,
        absence-tolerant cleanup remains.

        Raises:
            Whatever ``delete_collection_ignoring_absence`` propagates (any
                operational Chroma failure besides a genuinely absent
                collection) — rebuild must never proceed past a wipe that
                may not have actually happened (Codex review, PR #119 round
                7), since stale disabled/deleted chunks would then remain
                silently retrievable through the diagnostic query.
            Whatever the create/transform/upsert raises, after this attempt's
                collection has been removed. A cleanup failure is not swallowed;
                it propagates (chained onto the originating failure), so a
                partial rebuild is never left behind under a clean-failure claim.
        """
        collection_name = rules_corpus_collection_name(rules_package_id)
        # Wipe first (surplus removal), OUTSIDE the compensation scope: an
        # operational wipe failure must propagate without any further deletion --
        # the old collection is untouched (PR #119 round 7).
        delete_collection_ignoring_absence(self._client, collection_name)

        # Wipe succeeded -> the old collection is gone. Arm cleanup: from here any
        # created/partial collection belongs to this rebuild attempt.
        cleanup_armed = True
        try:
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
                # A package with no enabled chunks rebuilds to an empty
                # collection -- the complete, correct end state, not a partial
                # one; disarm and keep it.
                cleanup_armed = False
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

            # Chroma caps a single add/upsert at the backend's ``max_batch_size``
            # (varies by Chroma/backend build); a full Rules Package corpus (CRD
            # Issue 5c: ~13.6k chunks) exceeds it in one call. Derive the batch
            # size from the ACTUAL client capability via Chroma's supported
            # ``create_batches`` helper (which slices by ``get_max_batch_size()``),
            # never a hard-coded limit that could exceed a smaller backend's cap
            # (PR #134 P1). Fail clearly if the client reports an invalid capability
            # rather than silently reverting to a fixed size. Order is preserved
            # (in-order slices) so stored IDs/content/metadata are unchanged; a
            # later-batch failure after an earlier batch landed is compensated by
            # the boundary below (PR #134 P2).
            max_batch = self._client.get_max_batch_size()
            if not isinstance(max_batch, int) or max_batch <= 0:
                raise RuntimeError(
                    f"Chroma reported an unusable max batch size: {max_batch!r}"
                )
            for batch_ids, _emb, batch_metadatas, batch_documents in create_batches(
                self._client,
                ids=ids,
                metadatas=metadatas,  # type: ignore[arg-type]
                documents=documents,
            ):
                collection.upsert(
                    documents=batch_documents,
                    metadatas=batch_metadatas,
                    ids=batch_ids,
                )
            # Every batch landed -- the rebuild is complete and consistent with
            # SQL ground truth; only now is it safe to disarm cleanup.
            cleanup_armed = False
            return len(rows)
        except Exception:
            # Create / transform / embedding / any batch failed before the
            # rebuild completed. Remove this attempt's (possibly partially
            # populated) collection and propagate. delete_collection_ignoring_
            # absence swallows only a genuinely absent collection; a real cleanup
            # failure propagates (chained onto the originating failure), so a
            # partial rebuild is never left behind under a clean-failure claim.
            if cleanup_armed:
                delete_collection_ignoring_absence(self._client, collection_name)
            raise

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
