"""Fixtures for the CRD Issue 5d runtime-authority suite.

The runtime layer needs something the earlier 5d suites did not: an *activated*
projection over a published 5c release, reached through the genuine
publish → activate path rather than by writing the rows publication would have
left behind. Activation is what binding resolution reads, so a fixture that
faked it would prove the resolver can read rows nobody proved.

The bounded release below is therefore built from real CRD Issue 5c model
objects and persisted through 5c's own primitives, exactly as
``tests/ingestion/mechanical/conftest.py`` does. It is a separate fixture rather
than an import of that one for one reason: **package identities here are real
UUIDs.** ``RulesPackageBinding`` types every component as a ``UUID``, which is
what makes a slug structurally incapable of being canonical authority, and the
bounded mechanical fixture uses the short string ``"pkg-5c"``. Changing that
fixture's package identity would remint its committed accepted oracle, so this
suite carries its own release instead.

Two packages are seeded. The second exists so slug ambiguity is a real
condition to resolve rather than a mocked one.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from uuid import UUID, uuid5

import pytest
from sqlalchemy import Engine, select
from sqlalchemy import text as sa_text
from sqlalchemy.orm import Session

from afterworlds.ingestion.corpus.bundle import build_bundle, reconciliation_hash
from afterworlds.ingestion.corpus.concordance import ConcordanceResult
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
from afterworlds.ingestion.corpus.operational import (
    CORPUS_CONTRACT_VERSION,
    build_operational_corpus_snapshot,
    operational_corpus_digest,
)
from afterworlds.ingestion.corpus.persistence import (
    _persist_bundle_rows,
    _persist_package_and_source,
    _persist_release_record,
)
from afterworlds.ingestion.corpus.policy import (
    FROZEN_POLICY,
    policy_hash,
    policy_payload,
)
from afterworlds.ingestion.corpus.report import (
    EVIDENCE_REPORT_SCHEMA_VERSION as CORPUS_EVIDENCE_REPORT_SCHEMA_VERSION,
)
from afterworlds.ingestion.corpus.report import build_report
from afterworlds.ingestion.corpus.report import report_hash as corpus_report_hash
from afterworlds.ingestion.mechanical.accounting import derive_span_id
from afterworlds.ingestion.mechanical.models import (
    AcceptanceRecord,
    ClassificationLedger,
    ComponentHandling,
    ReviewState,
    SemanticDisposition,
    SemanticSpan,
)
from afterworlds.ingestion.mechanical.oracle import AcceptedOracle, RecordObligation
from afterworlds.ingestion.mechanical.persistence import (
    persist_draft,
    record_persisted_state_digest,
)
from afterworlds.ingestion.mechanical.policy import (
    SEMANTIC_POLICY_VERSION,
    semantic_policy_hash,
)
from afterworlds.ingestion.mechanical.projection import (
    ProjectionCandidate,
    ReleaseBinding,
    identify_projection,
)
from afterworlds.ingestion.mechanical.publication import (
    PublicationOutcome,
    _publish_projection,
)
from afterworlds.ingestion.mechanical.representation import (
    AbilityCheckFact,
    AbilityScore,
    ComponentDraft,
    DcKind,
    ProseBindingDraft,
    ProvenanceClaim,
    ProvenanceRole,
    ProvenanceTargetKind,
    RecordDraft,
    RecordKind,
    RepresentationDraft,
    SpellDescriptorFact,
    SpellSchool,
    fact_key,
    fact_payload,
    prose_binding_target_key,
)
from afterworlds.models.enums import OverrideOperationEnum, OverrideOriginEnum
from afterworlds.models.rules_package import RulesPackageBinding
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.persistence.orm.base import Base
from afterworlds.persistence.orm.corpus import CorpusReleaseORM
from afterworlds.persistence.orm.rules_authority import MechanicalOverrideORM
from afterworlds.persistence.orm.rules_package import RulesPackageORM
from afterworlds.services.rules_authority.targets import (
    MechanicalTarget,
    MechanicalTargetKind,
)

NOW = "2026-08-08T00:00:00Z"

#: Deterministic, and real UUIDs. Derived rather than literal so the two
#: packages can never accidentally be written as the same value.
_NS = UUID("2f2b6d9c-0e2a-5f31-9a44-6b0c1d2e3f40")
PACKAGE_UUID = str(uuid5(_NS, "runtime-authority-primary"))
RIVAL_PACKAGE_UUID = str(uuid5(_NS, "runtime-authority-rival"))
#: A published 5c release carrying no mechanical projection at all, so
#: ``UNPUBLISHED`` stays a reachable state now that the rival package has one.
BARE_PACKAGE_UUID = str(uuid5(_NS, "runtime-authority-bare"))

RELEASE_VERSION = "5.2.1-runtime.fixture"
RIVAL_RELEASE_VERSION = "5.2.1-runtime.rival"
BARE_RELEASE_VERSION = "5.2.1-runtime.bare"

#: Both packages carry the same display name, so they slugify identically. That
#: is what an ambiguous human-facing slug actually is.
PACKAGE_NAME = "SRD 5.2.1 corpus"
#: The bare package is deliberately named differently: the ambiguous-slug
#: control needs exactly two packages sharing a slug, not three.
BARE_PACKAGE_NAME = "Bare corpus with no projection"

SPELL_LEAF = "leaf-spell"
PROSE_LEAF = "leaf-prose"
SUPPORT_LEAF = "leaf-support"
CHECK_LEAF = "leaf-check"
LEAF_LENGTHS = {SPELL_LEAF: 40, PROSE_LEAF: 30, SUPPORT_LEAF: 20, CHECK_LEAF: 25}

WISH_CHUNK = "chunk-wish-0001"
SUPPORT_CHUNK = "chunk-wish-0002"
SPELL_CHUNK = "chunk-wish-spell"
CHECK_CHUNK = "chunk-servant-check"

SPELL_SPAN = derive_span_id(SPELL_LEAF, 0, 40)
PROSE_SPAN = derive_span_id(PROSE_LEAF, 0, 30)
SUPPORT_SPAN = derive_span_id(SUPPORT_LEAF, 0, 20)
CHECK_SPAN = derive_span_id(CHECK_LEAF, 0, 25)

SPELL_KEY = "spell:wish"
CREATURE_KEY = "creature:wish-scoped-servant"
DESCRIPTOR_KEY = "descriptor"
OPEN_ENDED_KEY = "open-ended-clause"
CHECK_KEY = "servant-check"

DESCRIPTOR_FACT = SpellDescriptorFact(
    level=9, school=SpellSchool.CONJURATION, ritual=False, concentration=False
)
DESCRIPTOR_FACT_KEY = fact_key(DESCRIPTOR_FACT)

CHECK_FACT = AbilityCheckFact(
    ability=AbilityScore.WISDOM, dc_kind=DcKind.FIXED, dc_value=15
)
CHECK_FACT_KEY = fact_key(CHECK_FACT)

AUTHORITATIVE_SOURCE_HASH = "a" * 64
TRANSFORM_CONFIG_HASH = "b" * 64
PERSISTED_CORPUS_DIGEST = "d" * 64

PROSE_TEXT = "x" * 30


def _ledger() -> SourceLedger:
    return SourceLedger(
        source_document="D&D SRD 5.2.1",
        source_version="5.2.1",
        source_sha256=AUTHORITATIVE_SOURCE_HASH,
        extraction_config={"extractor": "runtime-authority-fixture"},
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


_EDGE_PAIRS = (
    (WISH_CHUNK, PROSE_LEAF),
    (SUPPORT_CHUNK, SUPPORT_LEAF),
    (SPELL_CHUNK, SPELL_LEAF),
    (CHECK_CHUNK, CHECK_LEAF),
)


def _edges(prefix: str = "") -> tuple[ProjectionEdge, ...]:
    return tuple(
        ProjectionEdge(
            projection_id=f"proj-{prefix}{chunk}",
            leaf_id=leaf,
            chunk_id=f"{prefix}{chunk}",
            role="authoritative",
            cover_start=0,
            cover_end=LEAF_LENGTHS[leaf],
        )
        for chunk, leaf in _EDGE_PAIRS
    )


def _members(package_uuid: str, prefix: str = "") -> CorpusBundleMembers:
    return CorpusBundleMembers(
        chunks=tuple(
            CorpusChunk(
                chunk_id=f"{prefix}{chunk}",
                subsystem="spells",
                content="x" * LEAF_LENGTHS[leaf],
                printed_page=1,
                section_label=None,
                container_path=(),
                source_leaf_ids=(leaf,),
                source_document="D&D SRD 5.2.1",
                source_locator_type="page",
                source_locator_value="p. 1",
                source_id=package_uuid,
            )
            for chunk, leaf in _EDGE_PAIRS
        ),
        derivative_notes=(),
    )


def _reconciliation(ledger: SourceLedger, prefix: str = "") -> ReconciliationMember:
    return ReconciliationMember(
        policy_version=FROZEN_POLICY.policy_version,
        policy_hash=policy_hash(FROZEN_POLICY),
        dispositions=tuple(
            LeafDisposition(leaf.leaf_id, Disposition.REPRESENTED, None)
            for leaf in ledger.leaves
        ),
        projections=_edges(prefix),
        findings=ReconciliationFindings((), (), (), (), ()),
        inventoried_leaves=len(ledger.leaves),
        represented_leaves=len(ledger.leaves),
        excluded_leaves=0,
        unresolved_leaves=0,
    )


_TRANSFORM_CONFIG: dict[str, object] = {
    "reconciliation_policy": policy_payload(FROZEN_POLICY),
    "evidence_report_schema_version": CORPUS_EVIDENCE_REPORT_SCHEMA_VERSION,
}


def _seed_release(
    session: Session,
    package_uuid: str,
    release_version: str,
    prefix: str = "",
    package_name: str = PACKAGE_NAME,
) -> str:
    """Persist one published 5c release, returning its bundle root hash.

    *prefix* scopes chunk identities. ``rp_chunks.chunk_id`` is globally unique,
    so two seeded packages cannot both carry a chunk called ``chunk-wish-0001``
    — the rival release exists to be a second package, not a second copy of the
    first one's authority.
    """
    ledger = _ledger()
    members = _members(package_uuid, prefix)
    recon = _reconciliation(ledger, prefix)
    bundle = build_bundle(ledger, members, recon)
    report = build_report(
        ledger=ledger,
        members=members,
        recon=recon,
        policy=FROZEN_POLICY,
        authoritative_source_hash=AUTHORITATIVE_SOURCE_HASH,
        transform_config_hash=TRANSFORM_CONFIG_HASH,
        transform_config=_TRANSFORM_CONFIG,
        bundle_root_hash=bundle.bundle_root_hash,
        ledger_hash_value=ledger_hash(ledger),
        persisted_corpus_digest=PERSISTED_CORPUS_DIGEST,
        concordance=ConcordanceResult(
            chunks_checked=len(members.chunks),
            locator_failures=(),
            content_failures=(),
        ),
        canaries=(),
        persisted=True,
    )

    _persist_package_and_source(session, package_uuid, release_version, now=NOW)
    _persist_release_record(
        session,
        package_uuid,
        release_version=release_version,
        authoritative_source_hash=AUTHORITATIVE_SOURCE_HASH,
        transform_config_hash=TRANSFORM_CONFIG_HASH,
        bundle_root_hash=bundle.bundle_root_hash,
        evidence_report_hash=corpus_report_hash(report),
        persisted_corpus_digest=PERSISTED_CORPUS_DIGEST,
        corpus_contract_version=CORPUS_CONTRACT_VERSION,
        operational_corpus_digest_value=None,
        ledger_hash=ledger_hash(ledger),
        policy_hash=policy_hash(FROZEN_POLICY),
        reconciliation_hash=reconciliation_hash(recon),
        corpus_report_reference=corpus_report_hash(report),
        transform_config=_TRANSFORM_CONFIG,
        report_payload=report.payload,
        now=NOW,
    )
    _persist_bundle_rows(
        session,
        package_uuid,
        package_uuid,
        ledger=ledger,
        recon=recon,
        policy=FROZEN_POLICY,
        members=members,
        now=NOW,
    )
    release = session.get(CorpusReleaseORM, package_uuid)
    assert release is not None
    release.operational_corpus_digest = operational_corpus_digest(
        build_operational_corpus_snapshot(
            session,
            package_uuid,
            corpus_contract_version=CORPUS_CONTRACT_VERSION,
            persisted_corpus_digest=PERSISTED_CORPUS_DIGEST,
        )
    )
    _mark_published(session, package_uuid, package_name)
    return bundle.bundle_root_hash


def _mark_published(
    session: Session, package_uuid: str, name: str = PACKAGE_NAME
) -> None:
    """Transition a seeded release to published, as ``finalize_release`` does."""
    session.execute(
        select(CorpusReleaseORM).where(CorpusReleaseORM.package_uuid == package_uuid)
    ).scalar_one().publication_status = "published"
    package = session.execute(
        select(RulesPackageORM).where(RulesPackageORM.rules_package_id == package_uuid)
    ).scalar_one()
    package.publication_status = "published"
    package.published_at = NOW
    package.name = name
    session.flush()


# ---------------------------------------------------------------------------
# The bounded mechanical projection
# ---------------------------------------------------------------------------


def _wish_binding(prefix: str = "") -> ProseBindingDraft:
    """The prose binding, scoped to the release's own chunk identities.

    Chunk ids are release-scoped (``rp_chunks.chunk_id`` is globally unique), so
    a projection over the rival release must bind that release's chunk. Semantic
    *keys* stay identical across both — which is the point: shared keys are what
    make a mis-scoped override set able to find live targets elsewhere.
    """
    return ProseBindingDraft(
        component_key=OPEN_ENDED_KEY,
        record_key=SPELL_KEY,
        chunk_id=f"{prefix}{WISH_CHUNK}",
        irreducibility_reason_code="open_ended_effect",
    )


WISH_BINDING = _wish_binding()


def _classification(package_uuid: str, release_version: str) -> ClassificationLedger:
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
        SemanticSpan(
            span_id=CHECK_SPAN,
            leaf_id=CHECK_LEAF,
            char_start=0,
            char_end=25,
            disposition=SemanticDisposition.SUBSTANTIVE,
            review_state=ReviewState.ACCEPTED,
        ),
    )
    return ClassificationLedger(
        package_uuid=package_uuid,
        release_version=release_version,
        policy_version=SEMANTIC_POLICY_VERSION,
        policy_hash=semantic_policy_hash(),
        spans=spans,
        batches=(),
        acceptances=tuple(
            AcceptanceRecord(s.span_id, None, "owner", NOW) for s in spans
        ),
    )


def _representation(prefix: str = "") -> RepresentationDraft:
    """A spell with structured and prose-bound authority, plus a scoped creature.

    Small on purpose, but not degenerate: two records, three components across
    two handling dispositions, and two typed facts of different families — which
    is the minimum that lets a replace, an append, and a disable each be aimed at
    something distinguishable.
    """
    return RepresentationDraft(
        records=(
            RecordDraft(semantic_key=SPELL_KEY, kind=RecordKind.SPELL),
            RecordDraft(
                semantic_key=CREATURE_KEY,
                kind=RecordKind.CREATURE,
                parent_key=SPELL_KEY,
            ),
        ),
        components=(
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
            ComponentDraft(
                record_key=CREATURE_KEY,
                semantic_key=CHECK_KEY,
                handling=ComponentHandling.STRUCTURED,
                facts=(CHECK_FACT,),
            ),
        ),
        prose_bindings=(_wish_binding(prefix),),
        relationships=(),
        references=(),
        provenance=(
            ProvenanceClaim(
                ProvenanceTargetKind.FACT,
                (SPELL_KEY, DESCRIPTOR_KEY, DESCRIPTOR_FACT_KEY),
                SPELL_SPAN,
                ProvenanceRole.PRIMARY,
            ),
            ProvenanceClaim(
                ProvenanceTargetKind.FACT,
                (CREATURE_KEY, CHECK_KEY, CHECK_FACT_KEY),
                CHECK_SPAN,
                ProvenanceRole.PRIMARY,
            ),
            ProvenanceClaim(
                ProvenanceTargetKind.PROSE_BINDING,
                prose_binding_target_key(_wish_binding(prefix)),
                PROSE_SPAN,
                ProvenanceRole.PRIMARY,
            ),
            ProvenanceClaim(
                ProvenanceTargetKind.RECORD,
                (SPELL_KEY,),
                SUPPORT_SPAN,
                ProvenanceRole.CONTEXTUAL,
            ),
        ),
    )


_OBLIGATIONS = (
    RecordObligation(
        record_key=SPELL_KEY,
        kind=RecordKind.SPELL,
        structured_fact_families=frozenset({DESCRIPTOR_FACT.FAMILY}),
        prose_bound_components=frozenset({OPEN_ENDED_KEY}),
    ),
    RecordObligation(
        record_key=CREATURE_KEY,
        kind=RecordKind.CREATURE,
        structured_fact_families=frozenset({CHECK_FACT.FAMILY}),
        prose_bound_components=frozenset(),
    ),
)


@dataclass(frozen=True)
class RuntimeFixture:
    """One published release with one activated mechanical projection."""

    session: Session
    #: The engine behind :attr:`session`, so a test can open genuinely
    #: independent connections for deterministic concurrency work.
    engine: Engine
    package_uuid: UUID
    release_version: str
    projection_uuid: UUID
    rival_package_uuid: UUID
    rival_release_version: str
    rival_projection_uuid: UUID
    #: Published release, no mechanical projection.
    bare_package_uuid: UUID

    def binding(self, override_set_uuid: UUID) -> RulesPackageBinding:
        return RulesPackageBinding(
            package_uuid=self.package_uuid,
            release_version=self.release_version,
            mechanical_projection_uuid=self.projection_uuid,
            override_set_uuid=override_set_uuid,
        )


def _publish_bounded_projection(
    session: Session,
    bundle_root_hash: str,
    package_uuid: str = PACKAGE_UUID,
    release_version: str = RELEASE_VERSION,
    chunk_prefix: str = "",
) -> str:
    """Build, persist, gate, publish, and activate the bounded projection.

    Goes through :func:`_publish_projection` with an in-memory accepted oracle
    rather than writing the rows a publication would have left behind. Binding
    resolution reads the activation row and the recorded evidence, so a fixture
    that faked them would let this suite pass against state no gate accepted.

    Parameterized by package so the rival package can carry its own published
    projection. Both projections use the same representation, and deliberately
    so: semantic keys are stable across SRD-derived releases by design, which is
    exactly why an override set retained for one package can find live targets
    in another and replay with false provenance if its scope is not verified.
    """
    binding = ReleaseBinding(
        package_uuid=package_uuid,
        release_version=release_version,
        authoritative_source_hash=AUTHORITATIVE_SOURCE_HASH,
        transform_config_hash=TRANSFORM_CONFIG_HASH,
        bundle_root_hash=bundle_root_hash,
        persisted_corpus_digest=PERSISTED_CORPUS_DIGEST,
    )
    classification = _classification(package_uuid, release_version)
    representation = _representation(chunk_prefix)
    identified = identify_projection(
        ProjectionCandidate(
            binding=binding,
            classification=classification,
            representation=representation,
        )
    )
    persist_draft(session, identified, now=NOW)
    record_persisted_state_digest(session, identified.projection_uuid)
    oracle = AcceptedOracle(
        binding=binding,
        policy_version=SEMANTIC_POLICY_VERSION,
        policy_hash=semantic_policy_hash(),
        spans=classification.spans,
        representation=representation,
        obligations=_OBLIGATIONS,
    )
    result = _publish_projection(session, identified.projection_uuid, oracle, now=NOW)
    assert result.outcome is PublicationOutcome.PUBLISHED, (
        result.outcome,
        result.gate.failures if result.gate else (),
    )
    return identified.projection_uuid


@pytest.fixture()
def runtime(tmp_path) -> Iterator[RuntimeFixture]:  # type: ignore[no-untyped-def]
    """A published release, an activated projection, and a rival package.

    Per-test rather than session-scoped: publication commits, and these tests
    author, edit, and delete override rows, so a shared database would let one
    test's override state decide another's binding identity.
    """
    engine = create_engine(f"sqlite:///{tmp_path / 'runtime.db'}")
    Base.metadata.create_all(engine)
    with create_session_factory(engine)() as session:
        bundle_root_hash = _seed_release(session, PACKAGE_UUID, RELEASE_VERSION)
        rival_root = _seed_release(
            session, RIVAL_PACKAGE_UUID, RIVAL_RELEASE_VERSION, prefix="rival-"
        )
        projection_uuid = _publish_bounded_projection(session, bundle_root_hash)
        rival_projection_uuid = _publish_bounded_projection(
            session, rival_root, RIVAL_PACKAGE_UUID, RIVAL_RELEASE_VERSION, "rival-"
        )
        _seed_release(
            session,
            BARE_PACKAGE_UUID,
            BARE_RELEASE_VERSION,
            prefix="bare-",
            package_name=BARE_PACKAGE_NAME,
        )
        install_append_only_triggers(session)
        yield RuntimeFixture(
            session=session,
            engine=engine,
            package_uuid=UUID(PACKAGE_UUID),
            release_version=RELEASE_VERSION,
            projection_uuid=UUID(projection_uuid),
            rival_package_uuid=UUID(RIVAL_PACKAGE_UUID),
            rival_release_version=RIVAL_RELEASE_VERSION,
            rival_projection_uuid=UUID(rival_projection_uuid),
            bare_package_uuid=UUID(BARE_PACKAGE_UUID),
        )
    engine.dispose()


# ---------------------------------------------------------------------------
# Override authoring
# ---------------------------------------------------------------------------


def author_override(
    session: Session,
    *,
    override_id: str,
    target: MechanicalTarget,
    operation: OverrideOperationEnum,
    payload: dict[str, object],
    precedence: int = 100,
    origin: OverrideOriginEnum = OverrideOriginEnum.HOUSE_RULE,
    is_enabled: bool = True,
    package_uuid: str = PACKAGE_UUID,
    release_version: str = RELEASE_VERSION,
    created_at: str = NOW,
    created_by: str | None = "owner",
    note: str | None = None,
) -> MechanicalOverrideORM:
    """Author one typed override row on the mutable authoring surface."""
    row = MechanicalOverrideORM(
        override_id=override_id,
        package_uuid=package_uuid,
        release_version=release_version,
        target_kind=target.kind.value,
        target_record_key=target.record_key,
        target_component_key=target.component_key,
        target_fact_key=target.fact_key,
        override_origin=origin.value,
        override_operation=operation.value,
        payload=payload,
        precedence=precedence,
        is_enabled=is_enabled,
        created_at=created_at,
        created_by=created_by,
        note=note,
    )
    session.add(row)
    session.flush()
    return row


#: The exact typed targets the bounded projection exposes.
DESCRIPTOR_COMPONENT_TARGET = MechanicalTarget(
    kind=MechanicalTargetKind.COMPONENT,
    record_key=SPELL_KEY,
    component_key=DESCRIPTOR_KEY,
)
DESCRIPTOR_FACT_TARGET = MechanicalTarget(
    kind=MechanicalTargetKind.FACT,
    record_key=SPELL_KEY,
    component_key=DESCRIPTOR_KEY,
    fact_key=DESCRIPTOR_FACT_KEY,
)
SPELL_RECORD_TARGET = MechanicalTarget(
    kind=MechanicalTargetKind.RECORD, record_key=SPELL_KEY
)
CREATURE_RECORD_TARGET = MechanicalTarget(
    kind=MechanicalTargetKind.RECORD, record_key=CREATURE_KEY
)
CHECK_COMPONENT_TARGET = MechanicalTarget(
    kind=MechanicalTargetKind.COMPONENT,
    record_key=CREATURE_KEY,
    component_key=CHECK_KEY,
)
PROSE_COMPONENT_TARGET = MechanicalTarget(
    kind=MechanicalTargetKind.COMPONENT,
    record_key=SPELL_KEY,
    component_key=OPEN_ENDED_KEY,
)

#: A different spell descriptor, used wherever a replacement must be visibly
#: different from what it replaces.
REPLACEMENT_DESCRIPTOR = SpellDescriptorFact(
    level=7, school=SpellSchool.ILLUSION, ritual=True, concentration=True
)
ADDED_CHECK = AbilityCheckFact(
    ability=AbilityScore.CHARISMA, dc_kind=DcKind.SPELL_SAVE_DC
)

DISABLE_PAYLOAD: dict[str, object] = {"patch": "disable"}


def replace_fact_payload(fact: object = REPLACEMENT_DESCRIPTOR) -> dict[str, object]:
    return {"patch": "replace_fact", "fact": fact_payload(fact)}


def append_fact_payload(fact: object = ADDED_CHECK) -> dict[str, object]:
    return {"patch": "append_fact", "fact": fact_payload(fact)}


def replace_component_payload(
    facts: tuple[object, ...] = (REPLACEMENT_DESCRIPTOR,),
) -> dict[str, object]:
    return {
        "patch": "replace_component",
        "component": {
            "handling": "structured",
            "facts": [fact_payload(f) for f in facts],
        },
    }


def append_component_payload(
    semantic_key: str = "house-rider",
    facts: tuple[object, ...] = (ADDED_CHECK,),
) -> dict[str, object]:
    return {
        "patch": "append_component",
        "component": {
            "semantic_key": semantic_key,
            "handling": "structured",
            "facts": [fact_payload(f) for f in facts],
        },
    }


def replace_record_payload(
    record_kind: str = "spell",
    semantic_key: str = DESCRIPTOR_KEY,
    facts: tuple[object, ...] = (REPLACEMENT_DESCRIPTOR,),
) -> dict[str, object]:
    return {
        "patch": "replace_record",
        "record_kind": record_kind,
        "components": [
            {
                "semantic_key": semantic_key,
                "handling": "structured",
                "facts": [fact_payload(f) for f in facts],
            }
        ],
    }


# ---------------------------------------------------------------------------
# Append-only enforcement
# ---------------------------------------------------------------------------
#
# ``Base.metadata.create_all`` does not create triggers, so a suite built that
# way would run without the protection production actually has and would prove
# nothing about it. These mirror migration 0024 exactly, following the pattern
# tests/persistence/test_rpg_roll_audit_db.py and tests/entitlement/conftest.py
# already use for the repository's other append-only evidence tables.

_RETAINED_TABLES = (
    "rp_override_set_versions",
    "rp_override_set_entries",
    "rp_override_set_scopes",
)

#: Migration 0024's trigger set, restated so the suite runs against the same
#: protection production has (``create_all`` does not create triggers). A test
#: asserts this set matches what the real migration installs, so the two cannot
#: drift silently — hand-mirroring is what made drift possible before.
_ENTRY_CONTENT_COLUMNS = (
    "override_id",
    "override_origin",
    "target_kind",
    "target_record_key",
    "target_component_key",
    "target_fact_key",
    "override_operation",
    "precedence",
    "is_enabled",
    "payload",
)


def _trigger_statements() -> list[str]:
    statements = [
        f"CREATE TRIGGER prevent_{table}_update BEFORE UPDATE ON {table} "
        f"BEGIN SELECT RAISE(ABORT, "
        f"'{table} is append-only: UPDATE is forbidden'); END"
        for table in _RETAINED_TABLES
    ]
    statements += [
        f"CREATE TRIGGER prevent_{table}_delete BEFORE DELETE ON {table} "
        f"BEGIN SELECT RAISE(ABORT, "
        f"'{table} is append-only: DELETE is forbidden'); END"
        for table in ("rp_override_set_versions", "rp_override_set_entries")
    ]
    statements.append(
        "CREATE TRIGGER prevent_rp_override_set_scopes_delete "
        "BEFORE DELETE ON rp_override_set_scopes "
        "WHEN EXISTS (SELECT 1 FROM rp_packages "
        "WHERE rules_package_id = OLD.package_uuid) "
        "BEGIN SELECT RAISE(ABORT, "
        "'rp_override_set_scopes is append-only while its package is live'); END"
    )
    statements.append(
        "CREATE TRIGGER prevent_rp_override_set_versions_reinsert "
        "BEFORE INSERT ON rp_override_set_versions "
        "WHEN EXISTS (SELECT 1 FROM rp_override_set_versions "
        "WHERE override_set_uuid = NEW.override_set_uuid "
        "AND entry_count IS NOT NEW.entry_count) "
        "BEGIN SELECT RAISE(ABORT, "
        "'rp_override_set_versions is append-only: rewrite refused'); END"
    )
    differs = " OR ".join(f"{c} IS NOT NEW.{c}" for c in _ENTRY_CONTENT_COLUMNS)
    statements.append(
        "CREATE TRIGGER prevent_rp_override_set_entries_reinsert "
        "BEFORE INSERT ON rp_override_set_entries "
        "WHEN EXISTS (SELECT 1 FROM rp_override_set_entries "
        "WHERE override_set_uuid = NEW.override_set_uuid "
        f"AND apply_order = NEW.apply_order AND ({differs})) "
        "BEGIN SELECT RAISE(ABORT, "
        "'rp_override_set_entries is append-only: rewrite refused'); END"
    )
    statements.append(
        "CREATE TRIGGER seal_rp_override_set_entries "
        "BEFORE INSERT ON rp_override_set_entries "
        "WHEN (SELECT COUNT(*) FROM rp_override_set_entries "
        "WHERE override_set_uuid = NEW.override_set_uuid) >= "
        "(SELECT entry_count FROM rp_override_set_versions "
        "WHERE override_set_uuid = NEW.override_set_uuid) "
        "AND NOT EXISTS (SELECT 1 FROM rp_override_set_entries "
        "WHERE override_set_uuid = NEW.override_set_uuid "
        "AND apply_order = NEW.apply_order) "
        "BEGIN SELECT RAISE(ABORT, "
        "'rp_override_set_entries is sealed: version already complete'); END"
    )
    return statements


def _trigger_names() -> list[str]:
    names = [f"prevent_{t}_update" for t in _RETAINED_TABLES]
    names += [
        f"prevent_{t}_delete"
        for t in (
            "rp_override_set_versions",
            "rp_override_set_entries",
            "rp_override_set_scopes",
        )
    ]
    names += [
        "prevent_rp_override_set_versions_reinsert",
        "prevent_rp_override_set_entries_reinsert",
        "seal_rp_override_set_entries",
    ]
    return names


def install_append_only_triggers(session: Session) -> None:
    """Install the migration's append-only triggers on the retained tables."""
    for statement in _trigger_statements():
        session.execute(sa_text(statement))
    session.flush()


@contextmanager
def without_append_only_triggers(session: Session) -> Iterator[None]:
    """Temporarily drop the append-only triggers, then restore them.

    Used only by the controls that must prove *read-time* verification still
    detects a rewritten retained row. The triggers stop the ordinary path; this
    models what is left — a database restored without them, or an out-of-band
    edit — and asserts that reconstruction refuses it anyway. Belt and braces
    are both load-bearing, so both are tested.
    """
    for name in _trigger_names():
        session.execute(sa_text(f"DROP TRIGGER IF EXISTS {name}"))
    session.flush()
    try:
        yield
    finally:
        install_append_only_triggers(session)
