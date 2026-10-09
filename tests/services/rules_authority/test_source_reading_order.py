"""Source passages read in the release's printed order -- CRD Issue 5d.

A component bound to several passages must hand them to its consumers in the
order the source prints them: a heading before the body it labels, and two
clauses of one paragraph in their order within it. The authority for that
order is the persisted 5c ledger -- each leaf's ``occurrence_index``, then the
span's offset within its leaf. A ``chunk_id`` is an opaque identity, and so are
leaf and span ids; none of them says where a passage is printed.

The release here is seeded for that purpose, apart from the shared runtime
fixture (whose component sets other suites pin): chunk ids, leaf ids and the
order the bindings are declared in all disagree with the printed order, and a
rival package prints the same leaves in the reverse order.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Iterator
from uuid import UUID, uuid5

import pytest
from sqlalchemy import delete
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
from afterworlds.ingestion.corpus.policy import FROZEN_POLICY, policy_hash
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
    PersistedStateReconstructionError,
    persist_draft,
    reconstruct_candidate,
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
    REPRESENTATION_SCHEMA_VERSION,
    ComponentDraft,
    ProseBindingDraft,
    ProvenanceClaim,
    ProvenanceRole,
    ProvenanceTargetKind,
    RecordDraft,
    RecordKind,
    RepresentationDraft,
    prose_binding_target_key,
    representation_schema_hash,
)
from afterworlds.models.enums import OverrideOperationEnum
from afterworlds.models.rules_package import RuleSliceRequest
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.persistence.orm.base import Base
from afterworlds.persistence.orm.corpus import CorpusReleaseORM, LedgerLeafORM
from afterworlds.services.rules_authority import (
    AuthorityOutcome,
    MechanicalTarget,
    MechanicalTargetKind,
    RulesAuthorityService,
)
from afterworlds.services.rules_authority.application import AuthoredProse, SourceProse
from afterworlds.services.rules_authority.service import source_leaf_order
from tests.services.rules_authority.conftest import (
    _TRANSFORM_CONFIG,
    AUTHORITATIVE_SOURCE_HASH,
    NOW,
    PERSISTED_CORPUS_DIGEST,
    TRANSFORM_CONFIG_HASH,
    _mark_published,
    author_override,
)

_NS = UUID("5b0f3e2a-7c41-5d8e-9f10-2a3b4c5d6e7f")
PACKAGE_UUID = str(uuid5(_NS, "reading-order-primary"))
RIVAL_PACKAGE_UUID = str(uuid5(_NS, "reading-order-rival"))
RELEASE_VERSION = "5.2.1-reading-order"

RECORD_KEY = "rule:tiers"
COMPONENT_KEY = "tiers"

#: Leaf ids, chunk ids and printed position all disagree: sorted by leaf id the
#: tail comes first, sorted by chunk id the body does.
HEADING = ("leaf-z-heading", "chunk-z", "#### Tier 1 (Levels 1-4)")
BODY = ("leaf-m-body", "chunk-a", "First clause. Second clause.")
TAIL = ("leaf-a-tail", "chunk-m", "Tail passage.")
PRINTED = (HEADING, BODY, TAIL)

#: The four passages as printed: the body leaf holds two, split at offset 14.
HEADING_TEXT = HEADING[2]
FIRST_CLAUSE = "First clause. "
SECOND_CLAUSE = "Second clause."
TAIL_TEXT = TAIL[2]
EXTENTS = {
    HEADING_TEXT: (HEADING, 0, len(HEADING[2])),
    FIRST_CLAUSE: (BODY, 0, 14),
    SECOND_CLAUSE: (BODY, 14, len(BODY[2])),
    TAIL_TEXT: (TAIL, 0, len(TAIL[2])),
}
#: The order the projection declares its bindings in -- neither printed nor
#: any id order.
DECLARED = (SECOND_CLAUSE, TAIL_TEXT, HEADING_TEXT, FIRST_CLAUSE)


def _span_id(text: str) -> str:
    (leaf_id, _, _), start, end = EXTENTS[text]
    return derive_span_id(leaf_id, start, end)


def _seed(
    session: Session,
    package_uuid: str,
    prefix: str,
    printed: tuple[tuple[str, str, str], ...],
) -> str:
    """Persist one published release printing *printed* in that order."""
    ledger = SourceLedger(
        source_document="D&D SRD 5.2.1",
        source_version="5.2.1",
        source_sha256=AUTHORITATIVE_SOURCE_HASH,
        extraction_config={"extractor": "reading-order-fixture"},
        containers=(),
        leaves=tuple(
            Leaf(
                leaf_id=leaf_id,
                printed_page=1,
                page_index=0,
                leaf_type=LeafType.PARAGRAPH,
                content=content,
                char_start=0,
                char_end=len(content),
                occurrence_index=index,
                container_path=(),
            )
            for index, (leaf_id, _, content) in enumerate(printed)
        ),
    )
    members = CorpusBundleMembers(
        chunks=tuple(
            CorpusChunk(
                chunk_id=f"{prefix}{chunk_id}",
                subsystem="rules",
                content=content,
                printed_page=1,
                section_label=None,
                container_path=(),
                source_leaf_ids=(leaf_id,),
                source_document="D&D SRD 5.2.1",
                source_locator_type="page",
                source_locator_value="p. 1",
                source_id=package_uuid,
            )
            for leaf_id, chunk_id, content in printed
        ),
        derivative_notes=(),
    )
    recon = ReconciliationMember(
        policy_version=FROZEN_POLICY.policy_version,
        policy_hash=policy_hash(FROZEN_POLICY),
        dispositions=tuple(
            LeafDisposition(leaf.leaf_id, Disposition.REPRESENTED, None)
            for leaf in ledger.leaves
        ),
        projections=tuple(
            ProjectionEdge(
                projection_id=f"proj-{prefix}{chunk_id}",
                leaf_id=leaf_id,
                chunk_id=f"{prefix}{chunk_id}",
                role="authoritative",
                cover_start=0,
                cover_end=len(content),
            )
            for leaf_id, chunk_id, content in printed
        ),
        findings=ReconciliationFindings((), (), (), (), ()),
        inventoried_leaves=len(printed),
        represented_leaves=len(printed),
        excluded_leaves=0,
        unresolved_leaves=0,
    )
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
    _persist_package_and_source(session, package_uuid, RELEASE_VERSION, now=NOW)
    _persist_release_record(
        session,
        package_uuid,
        release_version=RELEASE_VERSION,
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
    _mark_published(session, package_uuid, f"Reading order {prefix or 'primary'}")
    _publish(session, package_uuid, prefix, bundle.bundle_root_hash)
    return bundle.bundle_root_hash


def _binding(text: str, prefix: str) -> ProseBindingDraft:
    (_, chunk_id, _), start, end = EXTENTS[text]
    return ProseBindingDraft(
        component_key=COMPONENT_KEY,
        record_key=RECORD_KEY,
        chunk_id=f"{prefix}{chunk_id}",
        span_id=_span_id(text),
        chunk_char_start=start,
        chunk_char_end=end,
        irreducibility_reason_code="open_ended_effect",
    )


def _publish(session: Session, package_uuid: str, prefix: str, root: str) -> None:
    """Persist, gate, publish and activate the one-component projection."""
    binding = ReleaseBinding(
        package_uuid=package_uuid,
        release_version=RELEASE_VERSION,
        authoritative_source_hash=AUTHORITATIVE_SOURCE_HASH,
        transform_config_hash=TRANSFORM_CONFIG_HASH,
        bundle_root_hash=root,
        persisted_corpus_digest=PERSISTED_CORPUS_DIGEST,
    )
    spans = tuple(
        SemanticSpan(
            span_id=_span_id(text),
            leaf_id=leaf[0],
            char_start=start,
            char_end=end,
            disposition=SemanticDisposition.SUBSTANTIVE,
            review_state=ReviewState.ACCEPTED,
        )
        for text, (leaf, start, end) in EXTENTS.items()
    )
    classification = ClassificationLedger(
        package_uuid=package_uuid,
        release_version=RELEASE_VERSION,
        policy_version=SEMANTIC_POLICY_VERSION,
        policy_hash=semantic_policy_hash(),
        spans=spans,
        batches=(),
        acceptances=tuple(
            AcceptanceRecord(s.span_id, None, "owner", NOW) for s in spans
        ),
    )
    bindings = tuple(_binding(text, prefix) for text in DECLARED)
    representation = RepresentationDraft(
        records=(RecordDraft(semantic_key=RECORD_KEY, kind=RecordKind.GENERAL_RULE),),
        components=(
            ComponentDraft(
                record_key=RECORD_KEY,
                semantic_key=COMPONENT_KEY,
                handling=ComponentHandling.PROSE_BOUND,
                irreducibility_reason_code="open_ended_effect",
            ),
        ),
        prose_bindings=bindings,
        relationships=(),
        references=(),
        provenance=tuple(
            ProvenanceClaim(
                ProvenanceTargetKind.PROSE_BINDING,
                prose_binding_target_key(b),
                b.span_id,
                ProvenanceRole.PRIMARY,
            )
            for b in bindings
        ),
    )
    identified = identify_projection(
        ProjectionCandidate(
            schema_version=REPRESENTATION_SCHEMA_VERSION,
            schema_hash=representation_schema_hash(),
            binding=binding,
            classification=classification,
            representation=representation,
        )
    )
    persist_draft(session, identified, now=NOW)
    record_persisted_state_digest(session, identified.projection_uuid)
    oracle = AcceptedOracle(
        schema_version=REPRESENTATION_SCHEMA_VERSION,
        schema_hash=representation_schema_hash(),
        binding=binding,
        policy_version=SEMANTIC_POLICY_VERSION,
        policy_hash=semantic_policy_hash(),
        spans=spans,
        representation=representation,
        obligations=(
            RecordObligation(
                record_key=RECORD_KEY,
                kind=RecordKind.GENERAL_RULE,
                structured_fact_families=frozenset(),
                prose_bound_components=frozenset({COMPONENT_KEY}),
            ),
        ),
    )
    result = _publish_projection(session, identified.projection_uuid, oracle, now=NOW)
    assert result.outcome is PublicationOutcome.PUBLISHED, (
        result.outcome,
        result.gate.failures if result.gate else (),
    )


@pytest.fixture()
def session(tmp_path) -> Iterator[Session]:  # type: ignore[no-untyped-def]
    engine = create_engine(f"sqlite:///{tmp_path / 'reading-order.db'}")
    Base.metadata.create_all(engine)
    with create_session_factory(engine)() as session:
        _seed(session, PACKAGE_UUID, "", PRINTED)
        # Same leaf and span ids, printed the other way round.
        _seed(session, RIVAL_PACKAGE_UUID, "rival-", PRINTED[::-1])
        yield session
    engine.dispose()


def _service(session: Session) -> RulesAuthorityService:
    return RulesAuthorityService(session, now=NOW)


def _request(package_uuid: str = PACKAGE_UUID) -> RuleSliceRequest:
    return RuleSliceRequest(package_id=UUID(package_uuid), whole_package=True)


def _read(session: Session, package_uuid: str = PACKAGE_UUID) -> list[str | None]:
    result = _service(session).gamemaster_view(_request(package_uuid))
    assert result.outcome is AuthorityOutcome.RESOLVED, result.detail
    assert result.gamemaster_view is not None
    (component,) = result.gamemaster_view.components
    return [e.text for e in component.governing_prose]


def test_the_gamemaster_reads_passages_as_printed(session: Session) -> None:
    assert _read(session) == [HEADING_TEXT, FIRST_CLAUSE, SECOND_CLAUSE, TAIL_TEXT]


def test_the_order_is_neither_declared_nor_any_identity_order(
    session: Session,
) -> None:
    result = _service(session).typed_view(_request())
    assert result.typed_view is not None
    (record,) = result.typed_view.records
    (component,) = record.components
    passages = [e for e in component.governing_prose if isinstance(e, SourceProse)]
    chunks = [e.chunk_id for e in passages]
    assert chunks == ["chunk-z", "chunk-a", "chunk-a", "chunk-m"]
    assert chunks != sorted(chunks)
    spans = [e.span_id for e in passages]
    assert spans != sorted(spans)
    assert spans != [_span_id(text) for text in DECLARED]
    # The typed consumer reads the same order the GameMaster does.
    assert spans == [
        _span_id(t) for t in (HEADING_TEXT, FIRST_CLAUSE, SECOND_CLAUSE, TAIL_TEXT)
    ]


def test_each_package_reads_in_its_own_release_order(session: Session) -> None:
    # The rival binds the same leaf and span ids; only its ledger differs.
    assert _read(session, RIVAL_PACKAGE_UUID) == [
        TAIL_TEXT,
        FIRST_CLAUSE,
        SECOND_CLAUSE,
        HEADING_TEXT,
    ]
    assert _read(session) == [HEADING_TEXT, FIRST_CLAUSE, SECOND_CLAUSE, TAIL_TEXT]


def test_replay_reads_the_same_order(session: Session) -> None:
    result = _service(session).gamemaster_view(_request())
    assert result.binding is not None
    replayed = _service(session).replay(result.binding)
    ((component,),) = [r.components for r in replayed.records]
    passages = [e for e in component.governing_prose if isinstance(e, SourceProse)]
    assert len(passages) == len(component.governing_prose)
    assert [e.span_id for e in passages] == [
        _span_id(t) for t in (HEADING_TEXT, FIRST_CLAUSE, SECOND_CLAUSE, TAIL_TEXT)
    ]


_PROSE_TARGET = MechanicalTarget(
    kind=MechanicalTargetKind.PROSE, record_key=RECORD_KEY, component_key=COMPONENT_KEY
)


def test_an_authored_append_follows_the_source_and_is_not_reordered(
    session: Session,
) -> None:
    for override_id, text, precedence in (
        ("ov-a", "authored first", 20),
        ("ov-b", "authored second", 10),
    ):
        author_override(
            session,
            override_id=override_id,
            target=_PROSE_TARGET,
            operation=OverrideOperationEnum.APPEND,
            payload={"patch": "append_prose", "text": text},
            precedence=precedence,
            package_uuid=PACKAGE_UUID,
            release_version=RELEASE_VERSION,
        )
    result = _service(session).gamemaster_view(_request())
    assert result.gamemaster_view is not None
    (component,) = result.gamemaster_view.components
    source = component.governing_prose[:4]
    authored = component.governing_prose[4:]
    assert [e.text for e in source] == [
        HEADING_TEXT,
        FIRST_CLAUSE,
        SECOND_CLAUSE,
        TAIL_TEXT,
    ]
    assert all(isinstance(e, AuthoredProse) for e in authored)
    # Authored passages keep the order overrides resolve in (precedence), which
    # a source reading order has nothing to say about.
    assert [e.text for e in authored] == ["authored second", "authored first"]


def test_an_authored_replace_reads_alone(session: Session) -> None:
    author_override(
        session,
        override_id="ov-r",
        target=_PROSE_TARGET,
        operation=OverrideOperationEnum.REPLACE,
        payload={"patch": "replace_prose", "text": "authored whole"},
        package_uuid=PACKAGE_UUID,
        release_version=RELEASE_VERSION,
    )
    assert _read(session) == ["authored whole"]


def test_a_cited_leaf_missing_from_the_release_fails_closed(
    session: Session,
) -> None:
    session.execute(
        delete(LedgerLeafORM).where(
            LedgerLeafORM.package_uuid == PACKAGE_UUID,
            LedgerLeafORM.leaf_id == TAIL[0],
        )
    )
    result = _service(session).gamemaster_view(_request())
    assert result.outcome is AuthorityOutcome.STALE
    assert result.gamemaster_view is None
    assert TAIL[0] in (result.detail or ""), result.detail
    # The rival release still holds the leaf; it must not stand in.
    assert _read(session, RIVAL_PACKAGE_UUID)[0] == TAIL_TEXT


def test_a_binding_citing_an_unclassified_span_fails_closed(
    session: Session,
) -> None:
    result = _service(session).gamemaster_view(_request())
    assert result.binding is not None
    candidate = reconstruct_candidate(
        session, str(result.binding.mechanical_projection_uuid)
    )
    stray = dataclasses.replace(
        candidate.representation.prose_bindings[0], span_id="span-unclassified"
    )
    broken = dataclasses.replace(
        candidate,
        representation=dataclasses.replace(
            candidate.representation, prose_bindings=(stray,)
        ),
    )
    with pytest.raises(PersistedStateReconstructionError, match="span-unclassified"):
        source_leaf_order(session, broken)
