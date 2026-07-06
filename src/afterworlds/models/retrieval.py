"""Pydantic models and deterministic ID scheme for Retrieval Memory.

CRD Issue 18 / ADR-018 (docs/decisions/adr-018-retrieval-memory.md).

ChromaDB is a rebuildable projection of SQLite-authoritative content — never
the sole home of any data, never an authority over narrative or mechanical
canon (CLAUDE.md invariant 8: ``get_active_rule_slice`` remains the sole
deterministic mechanical authority; vector rules retrieval is discovery-only).

All chunk IDs in this module are semantic and derived, never random UUIDs
(ADR-018 D11) — this is what makes upsert/delete/reindex idempotent and lets
every write path (ingest, backfill, reindex, turn-delete) resolve through a
single builder.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from afterworlds.models.enums import (
    RetrievalChunkKind,
    RetrievalSourceType,
    SourceLocatorTypeEnum,
)

# ---------------------------------------------------------------------------
# Deterministic ID builders (ADR-018 D11) — the single ID builder every
# write/delete path must resolve IDs through (sibling-audit checkpoint #1).
# ---------------------------------------------------------------------------


def build_story_memory_chunk_id(story_id: UUID, turn_id: UUID, chunk_index: int) -> str:
    """Deterministic chunk ID for a story-memory chunk.

    Format fixed by ADR-018 D11: ``story:{story_id}:turn:{turn_id}:chunk:{index}``.
    Re-ingesting the same turn produces byte-identical IDs (idempotent upsert).
    """
    return f"story:{story_id}:turn:{turn_id}:chunk:{chunk_index}"


def build_story_memory_chunk_id_prefix(story_id: UUID, turn_id: UUID) -> str:
    """Prefix shared by every chunk ID for one turn — used for delete-before-write.

    ADR-018 D11: turn-level chunk-set replacement must delete all existing
    chunks for ``turn_id`` before writing the current chunk set, because a
    deterministic-ID upsert alone cannot remove chunks whose index no longer
    exists in a shrunk chunk set.
    """
    return f"story:{story_id}:turn:{turn_id}:chunk:"


def build_rules_corpus_chunk_id(rules_package_id: UUID, chunk_id: UUID) -> str:
    """Deterministic chunk ID for a rules-corpus chunk.

    Derives from ``rules_package_id`` + the durable CRD Issue 5a
    ``RuleChunkORM.chunk_id`` primary key, per ADR-018 D11.

    Codex review (PR #119) round 4: an earlier version derived this ID from
    (source locator type/value, per-run occurrence index) — a per-locator
    ordinal assigned by SQL row-iteration order, not any durable property of
    the row. Since ``RuleChunkORM.chunk_id`` is already the row's own
    immutable primary key (assigned once, at CRD Issue 5a ingestion time),
    it is what makes reindex idempotent and stable regardless of row order
    or how many chunks share the same source locator — no synthetic
    per-locator index is needed or safe to reconstruct at reindex time.
    """
    return f"rules:{rules_package_id}:chunk:{chunk_id}"


# ---------------------------------------------------------------------------
# Collection naming (ADR-018 D1)
# ---------------------------------------------------------------------------

#: Single shared collection name for all story-memory chunks across all
#: stories.  Mandatory ``story_id`` metadata filter is required on every
#: query against this collection — leakage is a query-gate property, not a
#: topology property (ADR-018 D1 rationale).
STORY_MEMORY_COLLECTION_NAME = "story_memory"


def rules_corpus_collection_name(rules_package_id: UUID) -> str:
    """Collection name for the finalized per-Rules-Package rules corpus.

    One collection per published Rules Package (ADR-018 D1), absorbing the
    CRD Issue 5b interim ``rp_chunks_interim_{package_id_hex}`` collection.
    """
    return f"rules_corpus_{rules_package_id.hex}"


# ---------------------------------------------------------------------------
# Metadata DTOs (ADR-018 D2)
# ---------------------------------------------------------------------------


class StoryMemoryChunkMetadata(BaseModel):
    """Per-chunk metadata for the shared ``story_memory`` collection.

    ``source_type`` and ``chunk_kind`` are distinct typed fields and must not
    be collapsed into one (ADR-018 D2, Codex round-3 correction to the
    original issue spec, which omitted ``source_type``).
    """

    model_config = ConfigDict(frozen=True)

    schema_version: int = 1
    story_id: UUID
    node_id: UUID | None
    turn_id: UUID
    mode: str
    source_type: RetrievalSourceType = RetrievalSourceType.DELIVERED_TURN_PROSE
    chunk_kind: RetrievalChunkKind = RetrievalChunkKind.SCENE_PROSE
    chunk_index: int
    chunk_count: int
    created_at: str
    content_hash: str
    embedding_model_id: str


class RulesCorpusChunkMetadata(BaseModel):
    """Per-chunk metadata for a finalized ``rules_corpus_{package}`` collection.

    Carries the CRD Issue 5a provenance fields plus the Issue 18 additions
    (``rules_package_id``, ``subsystem``, ``embedding_model_id``,
    ``schema_version``) per ADR-018 D2.
    """

    model_config = ConfigDict(frozen=True)

    schema_version: int = 1
    rules_package_id: UUID
    subsystem: str
    source_document: str
    source_locator_type: SourceLocatorTypeEnum
    source_locator_value: str
    embedding_model_id: str


# ---------------------------------------------------------------------------
# Query request DTO (ADR-018 D8) — orchestrator-constructed, mirrors
# RuleSliceRequest (models/rules_package.py).  Context Builder gains no
# inference logic; this is built before context assembly and threaded through
# ContextBuilderService.assemble() / build_stable_prefix().
# ---------------------------------------------------------------------------


class RetrievalQueryRequest(BaseModel):
    """Typed parameter bundle for RetrievalMemoryProvider.retrieve().

    ``query_text`` is fully composed by ``RetrievalQueryBuilder`` before this
    request is constructed — the Context Builder does not compose or infer
    query text itself (ADR-018 D8).
    """

    model_config = ConfigDict(frozen=True)

    story_id: UUID
    query_text: str


class RetrievalMatch(BaseModel):
    """One normalized retrieval result, prior to StablePrefix rendering."""

    model_config = ConfigDict(frozen=True)

    chunk_id: str
    document: str
    normalized_similarity: float
    metadata: dict[str, object] = Field(default_factory=dict)
