"""Shared builders for the CRD Issue 5d representation suite.

One small honest candidate: a spell record with a structured descriptor
component and a prose-bound open-ended clause, plus a scoped creature record —
the shape the Wish and spell-scoped-creature canaries exercise, small enough
that each negative control can perturb exactly one thing.

The same content appears twice on purpose, and the duplication is the point:

* :func:`build_candidate` is what a **build** produces from the accepted
  inputs; and
* ``data/bounded_oracle.json`` is the committed **accepted authority** stating
  the same content independently, loaded through the production
  :func:`load_oracle` path.

Negative controls perturb the candidate or the persisted rows and never the
oracle, so every one of them is a comparison against authority that did not
move. :func:`accepted_oracle` builds the equivalent in memory purely so the
committed file can be checked for drift in one place with a clear message.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from afterworlds.ingestion.corpus.bundle import (
    build_bundle,
    reconciliation_hash,
    transform_config_payload,
)
from afterworlds.ingestion.corpus.concordance import (
    VERSION_CANARIES,
    CanaryResult,
    ConcordanceResult,
)
from afterworlds.ingestion.corpus.hashing import hash_obj
from afterworlds.ingestion.corpus.ledger import ledger_hash
from afterworlds.ingestion.corpus.models import (
    CorpusBundleMembers,
    CorpusChunk,
    Disposition,
    Leaf,
    LeafDisposition,
    LeafType,
    ProjectionEdge,
    ReconciliationFindings,
    ReconciliationMember,
    SourceLedger,
)
from afterworlds.ingestion.corpus.pdf_source import extraction_config
from afterworlds.ingestion.corpus.persistence import (
    _load_ledger,
    _load_members,
    _load_policy,
    _load_reconciliation,
    _persist_bundle_rows,
    _persist_package_and_source,
    _persist_release_record,
)
from afterworlds.ingestion.corpus.policy import (
    FROZEN_POLICY,
    policy_hash,
)
from afterworlds.ingestion.corpus.report import (
    EvidenceReport as CorpusEvidenceReport,
)
from afterworlds.ingestion.corpus.report import (
    build_report,
)
from afterworlds.ingestion.corpus.report import (
    report_hash as corpus_report_hash,
)
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
from afterworlds.ingestion.mechanical.oracle import (
    AcceptedOracle,
    RecordObligation,
    load_oracle,
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
from afterworlds.models.retrieval import rules_corpus_vector_identity
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.persistence.orm.base import Base
from afterworlds.persistence.orm.corpus import CorpusReleaseORM
from afterworlds.persistence.orm.rules_package import RulesPackageORM
from afterworlds.pipeline.retrieval.config import RetrievalMemoryConfig

NOW = "2026-07-31T00:00:00Z"
DATA_DIR = Path(__file__).resolve().parent / "data"
BOUNDED_ORACLE_PATH = DATA_DIR / "bounded_oracle.json"

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


# ---------------------------------------------------------------------------
# The bound 5c release, as genuine CRD Issue 5c state
# ---------------------------------------------------------------------------
#
# Stated as real 5c model objects and persisted through 5c's own primitives,
# because CRD Issue 5d's publication gate now re-derives this release's recorded
# ledger, reconciliation, and bundle-root proof from the persisted rows. A
# hand-written release row carrying invented hashes is precisely what that gate
# exists to refuse, so a fixture built that way would no longer be a *published
# release* — it would be the forgery the negative controls are about.

SOURCE_DOCUMENT = "D&D SRD 5.2.1"
AUTHORITATIVE_SOURCE_HASH = "a" * 64
#: Opaque here on purpose: the persisted-corpus digest binds the actual
#: read-back vector state as well as SQL, so it is an exact recorded value the
#: 5d gate checks rather than one it can recompute from a session.
PERSISTED_CORPUS_DIGEST = "d" * 64

BOUND_LEDGER = SourceLedger(
    source_document=SOURCE_DOCUMENT,
    source_version="5.2.1",
    source_sha256=AUTHORITATIVE_SOURCE_HASH,
    extraction_config={"extractor": "bounded-fixture"},
    containers=(),
    leaves=tuple(
        Leaf(
            leaf_id=leaf_id,
            printed_page=1,
            page_index=0,
            leaf_type=LeafType.PARAGRAPH,
            content="x" * length,
            char_start=0,
            char_end=length,
            occurrence_index=index,
            container_path=(),
        )
        for index, (leaf_id, length) in enumerate(sorted(LEAF_LENGTHS.items()))
    ),
)

BOUND_MEMBERS = CorpusBundleMembers(
    chunks=tuple(
        CorpusChunk(
            chunk_id=chunk_id,
            subsystem="spells",
            content="x" * LEAF_LENGTHS[PROSE_LEAF],
            printed_page=1,
            section_label=None,
            container_path=(),
            source_leaf_ids=(PROSE_LEAF,),
            source_document=SOURCE_DOCUMENT,
            source_locator_type="page",
            source_locator_value="p. 1",
            source_id=PACKAGE_UUID,
        )
        # Order matters: reconstruction restores build order by the primary
        # leaf's occurrence index, and both chunks share one primary leaf, so
        # the stable order is the projection-edge order below.
        for chunk_id in (WISH_CHUNK, SECOND_CHUNK)
    ),
    derivative_notes=(),
)

BOUND_RECONCILIATION = ReconciliationMember(
    policy_version=FROZEN_POLICY.policy_version,
    policy_hash=policy_hash(FROZEN_POLICY),
    dispositions=tuple(
        LeafDisposition(leaf.leaf_id, Disposition.REPRESENTED, None)
        for leaf in BOUND_LEDGER.leaves
    ),
    projections=tuple(
        ProjectionEdge(
            projection_id=edge.projection_id,
            leaf_id=edge.leaf_id,
            chunk_id=edge.chunk_id,
            role=edge.role,
            cover_start=edge.cover_start,
            cover_end=edge.cover_end,
        )
        for edge in DEFAULT_COVERAGE
    ),
    findings=ReconciliationFindings((), (), (), (), ()),
    inventoried_leaves=len(BOUND_LEDGER.leaves),
    represented_leaves=len(BOUND_LEDGER.leaves),
    excluded_leaves=0,
    unresolved_leaves=0,
)

BOUND_BUNDLE = build_bundle(BOUND_LEDGER, BOUND_MEMBERS, BOUND_RECONCILIATION)

#: Built by 5c's own :func:`transform_config_payload`, not hand-written. The
#: recorded configuration is now proven to hash to the recorded
#: ``transform_config_hash``, so a thin stand-in would be exactly the forgery the
#: negative controls exist to catch.
BOUND_TRANSFORM_CONFIG: dict[str, object] = transform_config_payload(
    extraction_config(),
    FROZEN_POLICY,
    rules_corpus_vector_identity(RetrievalMemoryConfig().embedding_model_id),
)
#: **Derived**, never declared. Its predecessor was the constant ``"b" * 64``,
#: chosen when nothing recomputed it; under the published-release closure that
#: constant is a release whose configuration does not hash to its own recorded
#: hash — a forgery, correctly refused.
TRANSFORM_CONFIG_HASH = hash_obj(BOUND_TRANSFORM_CONFIG)

#: The full canonical canary population, derived from the committed definitions
#: rather than listed here, all passing. The bounded release is a *successful*
#: publication; an empty canary run is not one.
BOUND_CANARIES = tuple(
    CanaryResult(
        name=canary.name,
        printed_page=canary.printed_page,
        passed=True,
        missing=(),
        unexpected=(),
    )
    for canary in VERSION_CANARIES
)


def _build_bound_report(
    *,
    ledger: SourceLedger,
    members: CorpusBundleMembers,
    recon: ReconciliationMember,
    bundle_root_hash: str,
) -> CorpusEvidenceReport:
    """The 5c evidence report for the bound release, via 5c's own builder."""
    return build_report(
        ledger=ledger,
        members=members,
        recon=recon,
        policy=FROZEN_POLICY,
        authoritative_source_hash=AUTHORITATIVE_SOURCE_HASH,
        transform_config_hash=TRANSFORM_CONFIG_HASH,
        transform_config=BOUND_TRANSFORM_CONFIG,
        bundle_root_hash=bundle_root_hash,
        ledger_hash_value=ledger_hash(ledger),
        persisted_corpus_digest=PERSISTED_CORPUS_DIGEST,
        concordance=ConcordanceResult(
            chunks_checked=len(members.chunks),
            locator_failures=(),
            content_failures=(),
        ),
        canaries=BOUND_CANARIES,
        persisted=True,
    )


BOUND_REPORT = _build_bound_report(
    ledger=BOUND_LEDGER,
    members=BOUND_MEMBERS,
    recon=BOUND_RECONCILIATION,
    bundle_root_hash=BOUND_BUNDLE.bundle_root_hash,
)
BOUND_EVIDENCE_REPORT_HASH = corpus_report_hash(BOUND_REPORT)


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


#: The six values a projection binds. ``bundle_root_hash`` is the real bundle
#: root of the seeded 5c release, not a placeholder: the gate re-derives it from
#: the persisted rows, so a made-up value would make every bounded projection
#: fail as bound to a release that does not derive its own proof.
RELEASE_BINDING = ReleaseBinding(
    package_uuid=PACKAGE_UUID,
    release_version=RELEASE_VERSION,
    authoritative_source_hash=AUTHORITATIVE_SOURCE_HASH,
    transform_config_hash=TRANSFORM_CONFIG_HASH,
    bundle_root_hash=BOUND_BUNDLE.bundle_root_hash,
    persisted_corpus_digest=PERSISTED_CORPUS_DIGEST,
)


def build_candidate(**overrides: object) -> ProjectionCandidate:
    ledger = overrides.pop("ledger", None)
    return ProjectionCandidate(
        binding=RELEASE_BINDING,
        classification=ledger if ledger is not None else build_ledger(),  # type: ignore[arg-type]
        representation=build_representation(**overrides),
    )


# ---------------------------------------------------------------------------
# The accepted authority, and the 5c release it was accepted over
# ---------------------------------------------------------------------------


#: The accepted per-record obligations. ``spell:wish`` must carry structured
#: spell-descriptor authority *and* keep its open-ended clause prose-bound —
#: which is what makes all-prose under-extraction and reference-only coverage
#: fail by name rather than only as an element difference.
OBLIGATIONS = (
    RecordObligation(
        record_key=SPELL_KEY,
        kind=RecordKind.SPELL,
        structured_fact_families=frozenset({DESCRIPTOR_FACT.FAMILY}),
        prose_bound_components=frozenset({OPEN_ENDED_KEY}),
    ),
    RecordObligation(
        record_key=CREATURE_KEY,
        kind=RecordKind.CREATURE,
        structured_fact_families=frozenset(),
        prose_bound_components=frozenset(),
    ),
)


def accepted_oracle() -> AcceptedOracle:
    """The accepted authority for the bounded fixture, in memory.

    Exists to check the committed JSON for drift in one place. Tests that gate
    or publish use :func:`committed_oracle`, which goes through the real
    committed-file path.
    """
    return AcceptedOracle(
        binding=RELEASE_BINDING,
        policy_version=SEMANTIC_POLICY_VERSION,
        policy_hash=semantic_policy_hash(),
        spans=build_ledger().spans,
        representation=build_representation(),
        obligations=OBLIGATIONS,
    )


@pytest.fixture()
def committed_oracle() -> AcceptedOracle:
    """The bounded accepted oracle, loaded from its committed JSON file."""
    return load_oracle(BOUNDED_ORACLE_PATH)


def mark_release_published(session: Session) -> None:
    """Transition the seeded release to published, as ``finalize_release`` does.

    5c's persistence primitives write both rows as drafts, because in 5c the
    transition to ``published`` is the *last* step of a gate that has already
    passed. Nothing published a release here, so the fixture states plainly
    that it is standing in for that step.
    """
    for row, extra in (
        (
            session.execute(
                select(CorpusReleaseORM).where(
                    CorpusReleaseORM.package_uuid == PACKAGE_UUID
                )
            ).scalar_one(),
            {},
        ),
        (
            session.execute(
                select(RulesPackageORM).where(
                    RulesPackageORM.rules_package_id == PACKAGE_UUID
                )
            ).scalar_one(),
            {"published_at": NOW},
        ),
    ):
        row.publication_status = "published"
        for field, value in extra.items():
            setattr(row, field, value)
    session.flush()


def current_release_binding(session: Session) -> ReleaseBinding:
    """The six values the persisted 5c release currently records.

    A control that changes the release and then wants to test something *other*
    than the binding must rebuild its projection against this, because every
    proof identity a release records moves when its content does — which is the
    property that makes a forged release detectable in the first place.
    """
    release = session.execute(
        select(CorpusReleaseORM).where(CorpusReleaseORM.package_uuid == PACKAGE_UUID)
    ).scalar_one()
    assert release.persisted_corpus_digest is not None
    return ReleaseBinding(
        package_uuid=release.package_uuid,
        release_version=release.release_version,
        authoritative_source_hash=release.authoritative_source_hash,
        transform_config_hash=release.transform_config_hash,
        bundle_root_hash=release.bundle_root_hash,
        persisted_corpus_digest=release.persisted_corpus_digest,
    )


def rerecord_release_proof(session: Session) -> None:
    """Re-record the 5c release's proof from whatever the rows now say.

    For controls that legitimately change the *release* rather than the
    projection. A release edited without this no longer derives its own
    recorded proof, so the gate refuses it as an unpublishable binding — which
    would silently replace the finding the control means to assert with a
    bound-release refusal.
    """
    release = session.execute(
        select(CorpusReleaseORM).where(CorpusReleaseORM.package_uuid == PACKAGE_UUID)
    ).scalar_one()
    policy = _load_policy(session, PACKAGE_UUID)
    ledger = _load_ledger(session, PACKAGE_UUID)
    recon = _load_reconciliation(session, PACKAGE_UUID, policy)
    members = _load_members(session, PACKAGE_UUID, ledger)
    bundle = build_bundle(ledger, members, recon)

    release.ledger_hash = ledger_hash(ledger)
    release.reconciliation_hash = reconciliation_hash(recon)
    release.bundle_root_hash = bundle.bundle_root_hash
    report = _build_bound_report(
        ledger=ledger,
        members=members,
        recon=recon,
        bundle_root_hash=bundle.bundle_root_hash,
    )
    release.report_payload = report.dump()
    release.evidence_report_hash = corpus_report_hash(report)
    release.corpus_report_reference = release.evidence_report_hash
    session.flush()


def _seed_bound_release(session: Session) -> None:
    """Persist the published 5c release the bounded fixture is bound to.

    Written through CRD Issue 5c's own persistence primitives from the genuine
    5c model objects above: the package, its single authoritative source, the
    release record the projection FKs, the ``REPRESENTED`` leaves that form the
    accounting population, and the chunk/projection edges that make exact
    governing prose resolvable. ``load_bound_corpus`` reads these, and the
    publication gate now also reconstructs them and re-derives the release's
    recorded proof — so the fixture has to be a release that survives its own
    proof, not a row set shaped like one.
    """
    _persist_package_and_source(session, PACKAGE_UUID, RELEASE_VERSION, now=NOW)
    _persist_release_record(
        session,
        PACKAGE_UUID,
        release_version=RELEASE_VERSION,
        authoritative_source_hash=RELEASE_BINDING.authoritative_source_hash,
        transform_config_hash=RELEASE_BINDING.transform_config_hash,
        bundle_root_hash=RELEASE_BINDING.bundle_root_hash,
        evidence_report_hash=BOUND_EVIDENCE_REPORT_HASH,
        persisted_corpus_digest=RELEASE_BINDING.persisted_corpus_digest,
        ledger_hash=ledger_hash(BOUND_LEDGER),
        policy_hash=policy_hash(FROZEN_POLICY),
        reconciliation_hash=reconciliation_hash(BOUND_RECONCILIATION),
        corpus_report_reference=BOUND_EVIDENCE_REPORT_HASH,
        transform_config=BOUND_TRANSFORM_CONFIG,
        report_payload=BOUND_REPORT.dump(),
        now=NOW,
    )
    _persist_bundle_rows(
        session,
        PACKAGE_UUID,
        PACKAGE_UUID,
        ledger=BOUND_LEDGER,
        recon=BOUND_RECONCILIATION,
        policy=FROZEN_POLICY,
        members=BOUND_MEMBERS,
        now=NOW,
    )
    mark_release_published(session)


@pytest.fixture()
def session(tmp_path) -> Session:  # type: ignore[no-untyped-def]
    """A fresh database holding the published 5c release, and nothing else.

    Per-test rather than session-scoped: publication commits, so a shared
    database would let one test's published projection decide another's
    activation outcome.
    """
    engine = create_engine(f"sqlite:///{tmp_path / 'mech.db'}")
    Base.metadata.create_all(engine)
    factory = create_session_factory(engine)
    with factory() as s:
        _seed_bound_release(s)
        yield s
