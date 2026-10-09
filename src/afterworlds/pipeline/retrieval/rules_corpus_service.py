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

from afterworlds.models.retrieval import rules_corpus_collection_name
from afterworlds.persistence.orm.corpus import CorpusReleaseORM
from afterworlds.persistence.orm.rules_package import RuleChunkORM, RulesPackageORM
from afterworlds.pipeline.retrieval.collections import (
    delete_collection_ignoring_absence,
    get_existing_rules_corpus_collection,
    get_rules_corpus_collection,
)
from afterworlds.pipeline.retrieval.config import RetrievalMemoryConfig
from afterworlds.pipeline.retrieval.corpus_windows import (
    derive_retrieval_documents,
)
from afterworlds.pipeline.retrieval.embedding import RetrievalEmbeddingFunction
from afterworlds.quarantine import refuse_quarantined


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
        enabled ``RuleChunk`` row for *rules_package_id*, as one or more
        bounded embedding windows each. This absorbs the CRD Issue 5b
        interim collection without mutating any 5a source record. Returns
        the number of **documents** written, which is the number of chunks
        only when no chunk needed more than one window.

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
        not weaken ``_finalize_core``'s outer boundary -- that redundant,
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
        refuse_quarantined("rules-corpus reindex", package_uuid=rules_package_id)
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
            # One row contributes one document per bounded window. Sending
            # row.content whole embedded only its first 256 tokens -- the local
            # ONNX MiniLM function truncates its own input -- so everything past
            # the ceiling in a long chunk was unreachable while still reading
            # back complete. derive_retrieval_documents is shared with
            # vector_publication.expected_vector_state_from_sql so the published
            # state and its verification cannot drift (see corpus_windows).
            for row in rows:
                for doc_id, document, metadata in derive_retrieval_documents(
                    row, rules_package_id, self._config.embedding_model_id
                ):
                    ids.append(doc_id)
                    documents.append(document)
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
            return len(ids)
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

    @staticmethod
    def _is_published_and_enabled(session: Session, rules_package_id: UUID) -> bool:
        """True iff the package is published+enabled and any Issue-5c corpus
        release it carries is itself published.

        This service is **package-generic** (Issue 18): it diagnostically serves
        *every* rules package published through any path — including the
        pre-existing generic ``IngestionService.publish`` path, which never
        creates an Issue-5c ``CorpusReleaseORM`` row. So the required condition is
        that the ``RulesPackageORM`` row is ``published`` + enabled; a corpus
        release row is only *additionally* required to be ``published`` **when one
        exists** (PR #134). Concretely:

        * package missing / disabled / not published  → False (no Chroma access);
        * published+enabled package, no corpus release → True (generic package);
        * published+enabled package, corpus release *not* published (a draft or
          otherwise-inconsistent Issue-5c release) → False — draft corpus vectors
          written in-place during a rebuild (ADR-018 D11, no staging) stay hidden
          until the release itself publishes.

        Completeness checks are Issue-5c publication concerns and deliberately
        live in ``finalize_source_release``, never in this generic surface.
        """
        pkg = str(rules_package_id)
        package = session.execute(
            select(RulesPackageORM).where(RulesPackageORM.rules_package_id == pkg)
        ).scalar_one_or_none()
        release = session.execute(
            select(CorpusReleaseORM).where(CorpusReleaseORM.package_uuid == pkg)
        ).scalar_one_or_none()
        return (
            package is not None
            and package.is_enabled
            and package.publication_status == "published"
            and (release is None or release.publication_status == "published")
        )

    def diagnostic_query(
        self,
        session: Session,
        rules_package_id: UUID,
        query_text: str,
        n_results: int = 5,
    ) -> list[str]:
        """Internal/admin-only semantic lookup. Never consumed by a runtime pass.

        Publication-aware and read-only: returns no results unless BOTH SQL
        publication records are in a mutually consistent published+enabled state
        (checked BEFORE any Chroma access), so a concurrent read during a draft
        multi-batch rebuild never observes ungated draft vectors (PR #134). Uses a
        **non-creating** collection lookup — a missing collection yields no
        results and is never created. No threshold filtering: a
        discovery/diagnostic surface, not a retrieval-eligibility path.

        Matches are **hydrated**, not returned raw. What Chroma stores is a
        bounded derived window (``corpus_windows``); what a caller needs is the
        authoritative chunk that window came from, with its own headers, notes
        and citation intact. Each match is therefore resolved through its
        ``source_chunk_id`` back to ``RuleChunkORM.content`` and returned in
        Chroma's own rank order, deduplicated so several windows of one long
        chunk do not fill the result list with the same chunk.
        """
        refuse_quarantined(
            "rules-corpus diagnostic query", package_uuid=rules_package_id
        )
        if not self._is_published_and_enabled(session, rules_package_id):
            return []
        collection_name = rules_corpus_collection_name(rules_package_id)
        collection = get_existing_rules_corpus_collection(
            self._client, collection_name, self._config, self._embedding_function
        )
        if collection is None:
            return []
        count = collection.count()
        if count == 0:
            return []
        # Over-fetch before deduplication: n adjacent windows of one long chunk
        # can occupy the whole top-n, which would return one chunk where the
        # caller asked for n. ponytail: a fixed multiple, not a per-chunk
        # window_count lookup -- a diagnostic surface does not need a guaranteed
        # full page, and the collection size still caps the request.
        results = collection.query(
            query_texts=[query_text], n_results=min(n_results * 4, count)
        )
        metadata_lists = results.get("metadatas") or []
        if not metadata_lists or not metadata_lists[0]:
            return []
        ranked: list[str] = []
        for metadata in metadata_lists[0]:
            chunk_id = str((metadata or {}).get("source_chunk_id") or "")
            if chunk_id and chunk_id not in ranked:
                ranked.append(chunk_id)
        if not ranked:
            return []
        contents = {
            row.chunk_id: row.content
            for row in session.execute(
                select(RuleChunkORM)
                .where(RuleChunkORM.rules_package_id == str(rules_package_id))
                .where(RuleChunkORM.chunk_id.in_(ranked))
                .where(RuleChunkORM.is_enabled.is_(True))
            )
            .scalars()
            .all()
        }
        # A window whose chunk is gone or has since been disabled is dropped
        # rather than served from the vector copy: SQL is the ground truth.
        return [contents[c] for c in ranked if c in contents][:n_results]
