"""Shared builders for the CRD Issue 5d representation suite.

One small honest candidate: a spell record with a structured descriptor
component and a prose-bound open-ended clause, plus a scoped creature record —
the shape the Wish and spell-scoped-creature canaries exercise, small enough
that each negative control can perturb exactly one thing.
"""

from __future__ import annotations

from afterworlds.ingestion.mechanical.accounting import batch_diff_hash, derive_span_id
from afterworlds.ingestion.mechanical.bound_corpus import (
    BoundCorpusSnapshot,
    ChunkCoverage,
)
from afterworlds.ingestion.mechanical.models import (
    AcceptanceBatch,
    AcceptanceRecord,
    ClassificationLedger,
    ComponentHandling,
    ReviewState,
    SemanticDiffEntry,
    SemanticDisposition,
    SemanticSpan,
)
from afterworlds.ingestion.mechanical.policy import (
    SEMANTIC_POLICY_VERSION,
    semantic_policy_hash,
)
from afterworlds.ingestion.mechanical.projection import (
    ProjectionCandidate,
    ReleaseBinding,
)
from afterworlds.ingestion.mechanical.representation import (
    ComponentDraft,
    ProseBindingDraft,
    ProvenanceClaim,
    ProvenanceRole,
    ProvenanceTargetKind,
    RecordDraft,
    RecordKind,
    ReferenceDraft,
    RelationshipDraft,
    RelationshipKind,
    RepresentationDraft,
    SpellDescriptorFact,
    SpellSchool,
    fact_key,
    prose_binding_target_key,
    reference_target_key,
    relationship_target_key,
)

SPELL_LEAF = "leaf-spell"
PROSE_LEAF = "leaf-prose"
SUPPORT_LEAF = "leaf-support"

LEAF_LENGTHS = {SPELL_LEAF: 40, PROSE_LEAF: 30, SUPPORT_LEAF: 20}

PACKAGE_UUID = "pkg-5c"
RELEASE_VERSION = "rel-5c"
WISH_CHUNK = "chunk-wish-0001"
SECOND_CHUNK = "chunk-wish-0002"


def coverage(
    chunk_id: str,
    leaf_id: str,
    cover_start: int,
    cover_end: int,
    role: str = "authoritative",
) -> ChunkCoverage:
    """One synthetic 5c projection edge."""
    return ChunkCoverage(
        chunk_id=chunk_id,
        leaf_id=leaf_id,
        cover_start=cover_start,
        cover_end=cover_end,
        role=role,
        projection_id=f"proj-{chunk_id}-{leaf_id}-{cover_start}",
    )


#: Default synthetic coverage. Stated explicitly per chunk and leaf rather than
#: defaulting every chunk to every leaf, so a cross-chunk claim is actually
#: wrong here instead of accidentally allowed. Both chunks legitimately cover
#: the prose leaf — different chunks may cover the same source range.
DEFAULT_COVERAGE = (
    coverage(WISH_CHUNK, PROSE_LEAF, 0, 30),
    coverage(SECOND_CHUNK, PROSE_LEAF, 0, 30),
)


def bound_corpus(
    *,
    leaf_lengths: dict[str, int] | None = None,
    chunk_coverage: tuple[ChunkCoverage, ...] | None = None,
    package_uuid: str = PACKAGE_UUID,
    release_version: str = RELEASE_VERSION,
) -> BoundCorpusSnapshot:
    """The resolved 5c release the synthetic candidate is validated against."""
    return BoundCorpusSnapshot(
        package_uuid=package_uuid,
        release_version=release_version,
        leaf_lengths=dict(LEAF_LENGTHS if leaf_lengths is None else leaf_lengths),
        chunk_coverage=(DEFAULT_COVERAGE if chunk_coverage is None else chunk_coverage),
    )


SPELL_SPAN = derive_span_id(SPELL_LEAF, 0, 40)
PROSE_SPAN = derive_span_id(PROSE_LEAF, 0, 30)
SUPPORT_SPAN = derive_span_id(SUPPORT_LEAF, 0, 20)

SPELL_KEY = "spell:wish"
CREATURE_KEY = "creature:wish-scoped-servant"
DESCRIPTOR_KEY = "descriptor"
OPEN_ENDED_KEY = "open-ended-clause"

DESCRIPTOR_FACT = SpellDescriptorFact(
    level=9, school=SpellSchool.CONJURATION, ritual=False, concentration=False
)
DESCRIPTOR_FACT_KEY = fact_key(DESCRIPTOR_FACT)


def build_ledger(
    spans: tuple[SemanticSpan, ...] | None = None,
) -> ClassificationLedger:
    if spans is None:
        spans = (
            SemanticSpan(
                span_id=SPELL_SPAN,
                leaf_id=SPELL_LEAF,
                char_start=0,
                char_end=40,
                disposition=SemanticDisposition.SUBSTANTIVE,
                review_state=ReviewState.ACCEPTED,
            ),
            SemanticSpan(
                span_id=PROSE_SPAN,
                leaf_id=PROSE_LEAF,
                char_start=0,
                char_end=30,
                disposition=SemanticDisposition.SUBSTANTIVE,
                review_state=ReviewState.ACCEPTED,
            ),
            SemanticSpan(
                span_id=SUPPORT_SPAN,
                leaf_id=SUPPORT_LEAF,
                char_start=0,
                char_end=20,
                disposition=SemanticDisposition.SUPPORTING_AUTHORITY,
                review_state=ReviewState.ACCEPTED,
            ),
        )
    return ClassificationLedger(
        package_uuid="pkg-5c",
        release_version="rel-5c",
        policy_version=SEMANTIC_POLICY_VERSION,
        policy_hash=semantic_policy_hash(),
        spans=spans,
        batches=(),
        acceptances=tuple(
            AcceptanceRecord(s.span_id, None, "owner", "2026-07-31T00:00:00Z")
            for s in spans
        ),
    )


def batch_accepted_ledger() -> ClassificationLedger:
    """The same accepted result, reached through one rule-scoped batch.

    Used to prove the retained evidence survives persistence, and that the
    review path does not change the projection identity.
    """
    base = build_ledger()
    diff = tuple(
        SemanticDiffEntry(
            span_id=s.span_id,
            prior_disposition=None,
            prior_reason_code=None,
            accepted_disposition=s.disposition,
            accepted_reason_code=s.non_mechanical_reason_code,
        )
        for s in base.spans
    )
    unhashed = AcceptanceBatch(
        batch_id="batch-wish",
        rule="every span of the Wish authority reviewed together",
        resolved_scope=tuple(s.span_id for s in base.spans),
        diff=diff,
        semantic_diff_hash="",
    )
    batch = AcceptanceBatch(
        batch_id=unhashed.batch_id,
        rule=unhashed.rule,
        resolved_scope=unhashed.resolved_scope,
        diff=unhashed.diff,
        semantic_diff_hash=batch_diff_hash(unhashed),
    )
    return ClassificationLedger(
        package_uuid=base.package_uuid,
        release_version=base.release_version,
        policy_version=base.policy_version,
        policy_hash=base.policy_hash,
        spans=base.spans,
        batches=(batch,),
        acceptances=tuple(
            AcceptanceRecord(s.span_id, batch.batch_id, "owner", "2026-07-31T00:00:00Z")
            for s in base.spans
        ),
    )


WISH_BINDING = ProseBindingDraft(
    component_key=OPEN_ENDED_KEY,
    record_key=SPELL_KEY,
    chunk_id=WISH_CHUNK,
    irreducibility_reason_code="open_ended_effect",
)

SCOPED_WITHIN = RelationshipDraft(
    source_record_key=CREATURE_KEY,
    target_record_key=SPELL_KEY,
    kind=RelationshipKind.SCOPED_WITHIN,
)


def binding_claim(
    binding: ProseBindingDraft,
    span_id: str = PROSE_SPAN,
    role: ProvenanceRole = ProvenanceRole.PRIMARY,
) -> ProvenanceClaim:
    """A provenance edge for one exact prose binding."""
    return ProvenanceClaim(
        ProvenanceTargetKind.PROSE_BINDING,
        prose_binding_target_key(binding),
        span_id,
        role,
    )


def reference_claim(
    reference: ReferenceDraft,
    span_id: str = SPELL_SPAN,
    role: ProvenanceRole = ProvenanceRole.CONTEXTUAL,
) -> ProvenanceClaim:
    """A provenance edge for one exact resolved reference."""
    return ProvenanceClaim(
        ProvenanceTargetKind.REFERENCE,
        reference_target_key(reference),
        span_id,
        role,
    )


#: Two references whose identical wording resolves per committed scope.
SCOPED_REFERENCES = (
    ReferenceDraft(
        from_record_key=SPELL_KEY,
        from_component_key=DESCRIPTOR_KEY,
        source_text="the servant",
        scope_key="spell:wish",
        target_record_key=CREATURE_KEY,
    ),
    ReferenceDraft(
        from_record_key=SPELL_KEY,
        from_component_key=DESCRIPTOR_KEY,
        source_text="the servant",
        scope_key="chapter:appendix",
        target_record_key=SPELL_KEY,
    ),
)


def build_representation(**overrides: object) -> RepresentationDraft:
    records = (
        RecordDraft(semantic_key=SPELL_KEY, kind=RecordKind.SPELL),
        RecordDraft(
            semantic_key=CREATURE_KEY, kind=RecordKind.CREATURE, parent_key=SPELL_KEY
        ),
    )
    components = (
        ComponentDraft(
            record_key=SPELL_KEY,
            semantic_key=DESCRIPTOR_KEY,
            handling=ComponentHandling.STRUCTURED,
            facts=(DESCRIPTOR_FACT,),
        ),
        ComponentDraft(
            record_key=SPELL_KEY,
            semantic_key=OPEN_ENDED_KEY,
            handling=ComponentHandling.PROSE_BOUND,
            irreducibility_reason_code="open_ended_effect",
        ),
    )
    prose_bindings = (WISH_BINDING,)
    relationships = (SCOPED_WITHIN,)
    provenance = (
        ProvenanceClaim(
            ProvenanceTargetKind.FACT,
            (SPELL_KEY, DESCRIPTOR_KEY, DESCRIPTOR_FACT_KEY),
            SPELL_SPAN,
            ProvenanceRole.PRIMARY,
        ),
        ProvenanceClaim(
            ProvenanceTargetKind.PROSE_BINDING,
            prose_binding_target_key(WISH_BINDING),
            PROSE_SPAN,
            ProvenanceRole.PRIMARY,
        ),
        ProvenanceClaim(
            ProvenanceTargetKind.RECORD,
            (SPELL_KEY,),
            SUPPORT_SPAN,
            ProvenanceRole.CONTEXTUAL,
        ),
        # Every authoritative element carries its own edge: the relationship is
        # stated by the spell text, contextually alongside the fact's primary
        # claim on the same span.
        ProvenanceClaim(
            ProvenanceTargetKind.RELATIONSHIP,
            relationship_target_key(SCOPED_WITHIN),
            SPELL_SPAN,
            ProvenanceRole.CONTEXTUAL,
        ),
    )
    draft = RepresentationDraft(
        records=records,
        components=components,
        prose_bindings=prose_bindings,
        relationships=relationships,
        references=(),
        provenance=provenance,
    )
    if not overrides:
        return draft
    fields = {
        "records": draft.records,
        "components": draft.components,
        "prose_bindings": draft.prose_bindings,
        "relationships": draft.relationships,
        "references": draft.references,
        "provenance": draft.provenance,
    }
    fields.update(overrides)  # type: ignore[arg-type]
    return RepresentationDraft(**fields)  # type: ignore[arg-type]


def build_candidate(**overrides: object) -> ProjectionCandidate:
    ledger = overrides.pop("ledger", None)
    return ProjectionCandidate(
        binding=ReleaseBinding(
            package_uuid="pkg-5c",
            release_version="rel-5c",
            authoritative_source_hash="a" * 64,
            transform_config_hash="b" * 64,
            bundle_root_hash="c" * 64,
            persisted_corpus_digest="d" * 64,
        ),
        classification=ledger if ledger is not None else build_ledger(),  # type: ignore[arg-type]
        representation=build_representation(**overrides),
    )
