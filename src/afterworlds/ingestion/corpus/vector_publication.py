"""Actual vector persistence + read-back verification for corpus publication.

CRD Issue 5c, Component K step c (persist into SQL **and required vector
storage**) and the vector half of the persisted-corpus digest (Component A).
PR #134 remediation, defect family 1: the production publication path must
perform a real vector write and prove the *actual* Chroma documents — exact
IDs, content, required metadata, count, and embedding-model consistency —
rather than passing ``vector_write_ok=True`` and synthesizing vector state from
SQL.

This module owns **no** Chroma schema, ID formula, metadata shape, or writer of
its own. It orchestrates the existing CRD Issue 18 rules-corpus seam:

* :class:`RulesCorpusService.reindex_from_sql` — the writer/reindex,
* :func:`rules_corpus_collection_name` / :func:`build_rules_corpus_chunk_id`
  / :class:`RulesCorpusChunkMetadata` — the canonical naming, deterministic
  IDs, and metadata builder,
* :func:`get_existing_rules_corpus_collection` — the **non-creating** read-back
  handle (with its embedding-model compatibility guard), so this read-only path
  never creates a canonical collection.

The digest binds the vector *logical* state (IDs / content / metadata / count /
model id), never the implementation-dependent embedding bytes (Component A).
"""

from __future__ import annotations

from dataclasses import dataclass
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
from afterworlds.persistence.orm.rules_package import RuleChunkORM, RuleSourceORM
from afterworlds.pipeline.retrieval.collections import (
    RetrievalCollectionReindexRequiredError,
    delete_collection_ignoring_absence,
    get_existing_rules_corpus_collection,
)
from afterworlds.pipeline.retrieval.config import RetrievalMemoryConfig
from afterworlds.pipeline.retrieval.embedding import RetrievalEmbeddingFunction
from afterworlds.pipeline.retrieval.rules_corpus_service import RulesCorpusService

# Metadata key Chroma stores the collection's embedding-model identity under
# (mirrors the private constant in ``collections.py``; read-only use here).
_EMBEDDING_MODEL_ID_METADATA_KEY = "embedding_model_id"


@dataclass(frozen=True)
class VectorDocumentState:
    """One rules-corpus document's logical (non-embedding) state."""

    doc_id: str
    content: str
    metadata: dict[str, object]


@dataclass(frozen=True)
class VectorLogicalState:
    """The logical projection of a rules-corpus collection (Component A).

    Deterministic and embedding-byte-free: exactly what the persisted-corpus
    digest binds. ``documents`` are sorted by ``doc_id`` so the state has a
    canonical order independent of Chroma's return order.
    """

    collection_name: str
    embedding_model_id: str | None
    count: int
    documents: tuple[VectorDocumentState, ...]

    def to_payload(self) -> dict[str, object]:
        return {
            "collection_name": self.collection_name,
            "embedding_model_id": self.embedding_model_id,
            "count": self.count,
            "documents": [
                {
                    "id": d.doc_id,
                    "content": d.content,
                    "metadata": d.metadata,
                }
                for d in self.documents
            ],
        }


def _enabled_chunk_rows(session: Session, pkg: str) -> list[RuleChunkORM]:
    """Enabled ``rp_chunks`` whose source is also enabled — exactly the rows
    ``RulesCorpusService.reindex_from_sql`` writes and runtime reads serve.

    ``reindex_from_sql`` filters on ``RuleChunkORM.is_enabled`` only; this
    expected-state builder additionally excludes chunks whose *source* is
    disabled so the expected set matches the runtime-visible set that
    ``verify_chunk_runtime_membership`` also enforces. A projected chunk whose
    source is disabled is caught by that membership gate independently; here it
    simply must not appear in the expected vector state.
    """
    enabled_source_ids = {
        sid
        for sid in session.execute(
            select(RuleSourceORM.source_id).where(
                RuleSourceORM.rules_package_id == pkg,
                RuleSourceORM.is_enabled.is_(True),
            )
        ).scalars()
    }
    return [
        row
        for row in session.execute(
            select(RuleChunkORM)
            .where(
                RuleChunkORM.rules_package_id == pkg,
                RuleChunkORM.is_enabled.is_(True),
            )
            .order_by(RuleChunkORM.chunk_id)
        ).scalars()
        if row.source_id in enabled_source_ids
    ]


def expected_vector_state_from_sql(
    session: Session, pkg: str, config: RetrievalMemoryConfig
) -> VectorLogicalState:
    """Build the vector logical state that *should* exist, from SQL ground truth.

    Uses the Issue 18 canonical ID/metadata builders so the expected state is
    computed the exact same way the reindex writes it — the comparison in
    :func:`verify_vector_state` is then a true SQL-vs-actual-Chroma check, not a
    tautology against a locally reinvented shape.
    """
    package_uuid = UUID(pkg)
    docs: list[VectorDocumentState] = []
    for row in _enabled_chunk_rows(session, pkg):
        metadata = RulesCorpusChunkMetadata(
            rules_package_id=package_uuid,
            subsystem=row.subsystem,
            source_document=row.source_document,
            source_locator_type=SourceLocatorTypeEnum(row.source_locator_type),
            source_locator_value=row.source_locator_value,
            embedding_model_id=config.embedding_model_id,
        )
        docs.append(
            VectorDocumentState(
                doc_id=build_rules_corpus_chunk_id(package_uuid, UUID(row.chunk_id)),
                content=row.content,
                metadata=metadata.model_dump(mode="json"),
            )
        )
    docs.sort(key=lambda d: d.doc_id)
    return VectorLogicalState(
        collection_name=rules_corpus_collection_name(package_uuid),
        embedding_model_id=config.embedding_model_id,
        count=len(docs),
        documents=tuple(docs),
    )


def read_actual_vector_state(
    client: ClientAPI,
    pkg: str,
    config: RetrievalMemoryConfig,
    embedding_function: RetrievalEmbeddingFunction | None = None,
) -> VectorLogicalState:
    """Read the actual rules-corpus collection back from Chroma (read-only).

    Uses a **non-creating** lookup (:func:`get_existing_rules_corpus_collection`),
    so the verify-only reuse path never creates an empty canonical collection as
    a side effect (PR #134). Returns an empty state (count 0, no documents) when
    the collection is genuinely absent or the embedding-model guard rejects it —
    both are publication-blocking conditions surfaced by
    :func:`verify_vector_state`, not silent successes, and neither creates, wipes,
    or rewrites anything. Any other operational Chroma error propagates.
    """
    package_uuid = UUID(pkg)
    collection_name = rules_corpus_collection_name(package_uuid)
    empty = VectorLogicalState(
        collection_name=collection_name,
        embedding_model_id=None,
        count=0,
        documents=(),
    )
    try:
        collection = get_existing_rules_corpus_collection(
            client, collection_name, config, embedding_function
        )
    except RetrievalCollectionReindexRequiredError:
        # A recorded embedding-model mismatch — the collection is not usable at
        # the configured model. Report as empty so verification fails closed
        # rather than trusting a mismatched store; nothing is created or mutated.
        return empty
    if collection is None:
        # Genuinely absent (NotFoundError): verification-blocking, Chroma left
        # exactly as it was — never created by this read-only path.
        return empty
    recorded_model = (
        collection.metadata.get(_EMBEDDING_MODEL_ID_METADATA_KEY)
        if collection.metadata
        else None
    )
    got = collection.get()
    ids = got.get("ids") or []
    documents = got.get("documents") or []
    metadatas = got.get("metadatas") or []
    docs: list[VectorDocumentState] = []
    for i, doc_id in enumerate(ids):
        raw_meta = metadatas[i] if i < len(metadatas) else {}
        content = documents[i] if i < len(documents) else ""
        docs.append(
            VectorDocumentState(
                doc_id=str(doc_id),
                content=str(content) if content is not None else "",
                metadata={str(k): v for k, v in dict(raw_meta or {}).items()},
            )
        )
    docs.sort(key=lambda d: d.doc_id)
    return VectorLogicalState(
        collection_name=collection_name,
        embedding_model_id=(
            str(recorded_model) if recorded_model is not None else None
        ),
        count=len(docs),
        documents=tuple(docs),
    )


def verify_vector_state(
    expected: VectorLogicalState,
    actual: VectorLogicalState,
    config: RetrievalMemoryConfig,
) -> tuple[str, ...]:
    """Return the list of ways *actual* diverges from *expected* (empty == ok).

    Catches: empty/missing collection, count mismatch, missing/extra document
    IDs, stale content, metadata mismatch, and embedding-model inconsistency.
    Publication/reuse must fail closed whenever this is non-empty (Component I).
    """
    failures: list[str] = []
    if actual.embedding_model_id != config.embedding_model_id:
        failures.append(
            "vector collection embedding_model_id "
            f"{actual.embedding_model_id!r} != configured "
            f"{config.embedding_model_id!r}"
        )
    if actual.count != expected.count:
        failures.append(
            f"vector document count {actual.count} != expected {expected.count}"
        )
    expected_by_id = {d.doc_id: d for d in expected.documents}
    actual_by_id = {d.doc_id: d for d in actual.documents}
    for missing in sorted(set(expected_by_id) - set(actual_by_id)):
        failures.append(f"vector collection missing expected document {missing}")
    for extra in sorted(set(actual_by_id) - set(expected_by_id)):
        failures.append(f"vector collection has unexpected document {extra}")
    for doc_id in sorted(set(expected_by_id) & set(actual_by_id)):
        exp = expected_by_id[doc_id]
        act = actual_by_id[doc_id]
        if act.content != exp.content:
            failures.append(f"vector document {doc_id} has stale/altered content")
        if act.metadata != exp.metadata:
            failures.append(f"vector document {doc_id} has mismatched metadata")
    return tuple(failures)


@dataclass(frozen=True)
class VectorPublicationResult:
    """Outcome of a reindex-and-verify (fresh publish) or verify-only (reuse)."""

    state: VectorLogicalState
    failures: tuple[str, ...]
    written: int

    @property
    def ok(self) -> bool:
        return not self.failures


def reindex_and_verify(
    session: Session,
    pkg: str,
    client: ClientAPI,
    config: RetrievalMemoryConfig,
    embedding_function: RetrievalEmbeddingFunction | None = None,
) -> VectorPublicationResult:
    """Fresh-publish vector step: actually reindex, then read back and verify.

    Performs the real Chroma write via the Issue 18 ``RulesCorpusService``, then
    reads the collection back and verifies it against SQL ground truth. A write
    that raises, writes the wrong count, or produces any read-back discrepancy
    yields a non-empty ``failures`` (publication-blocking). ``written`` is the
    count ``reindex_from_sql`` reported.
    """
    service = RulesCorpusService(client, config, embedding_function)
    try:
        written = service.reindex_from_sql(session, UUID(pkg))
    except Exception as exc:  # noqa: BLE001 - any write failure blocks publication
        empty = VectorLogicalState(
            collection_name=rules_corpus_collection_name(UUID(pkg)),
            embedding_model_id=None,
            count=0,
            documents=(),
        )
        return VectorPublicationResult(
            state=empty,
            failures=(f"vector reindex failed: {exc}",),
            written=0,
        )
    expected = expected_vector_state_from_sql(session, pkg, config)
    actual = read_actual_vector_state(client, pkg, config, embedding_function)
    failures = list(verify_vector_state(expected, actual, config))
    if written != expected.count:
        failures.append(
            f"vector reindex wrote {written} documents, expected {expected.count}"
        )
    return VectorPublicationResult(
        state=actual, failures=tuple(failures), written=written
    )


def verify_only(
    session: Session,
    pkg: str,
    client: ClientAPI,
    config: RetrievalMemoryConfig,
    embedding_function: RetrievalEmbeddingFunction | None = None,
) -> VectorPublicationResult:
    """Reuse-path vector step: read back and verify **without** rewriting.

    A reuse of an already-published release must not silently rebuild the
    collection; it must confirm the existing vectors still match SQL ground
    truth and fail closed against a missing/stale/tampered collection.
    """
    expected = expected_vector_state_from_sql(session, pkg, config)
    actual = read_actual_vector_state(client, pkg, config, embedding_function)
    failures = verify_vector_state(expected, actual, config)
    return VectorPublicationResult(state=actual, failures=failures, written=0)


def cleanup_vector_collection(client: ClientAPI, pkg: str) -> None:
    """Remove this release's rules-corpus collection after a failed attempt.

    Chroma writes are not part of the SQL transaction, so a gate failure after a
    reindex must explicitly drop the collection this attempt created — otherwise
    a rolled-back (never-published) release would leave runtime-visible vectors.
    A genuinely absent collection is a no-op; any other operational error
    propagates (never swallow a failed cleanup).
    """
    delete_collection_ignoring_absence(client, rules_corpus_collection_name(UUID(pkg)))
