"""Draft persistence and exact reconstruction — CRD Issue 5d, Decision 8.

The lifecycle #137 contract 5 requires is:

``build candidate → persist draft → reconstruct from persisted state →
compute persisted-state digest → run exact completeness gate → atomically
publish``

This module owns the middle three steps. It writes a **draft**, reads the
projection back out of the database with no help from the in-memory candidate,
and derives a digest from what it read. The gate and publication are the next
PR; nothing here activates anything, and ``publication_status`` never leaves
``draft``.

Reconstruction is deliberately blind. If it took the candidate as a hint, a row
that failed to persist or was altered afterwards could be silently repaired
from memory and the digest would still match — which is exactly the tamper and
omission case the reconstruct-before-publish step exists to catch.
"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from afterworlds.ingestion.corpus.hashing import hash_obj
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
from afterworlds.ingestion.mechanical.projection import (
    IdentifiedProjection,
    ProjectionCandidate,
    ReleaseBinding,
    identify_projection,
    projection_payload,
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
    fact_from_payload,
    fact_key,
    fact_payload,
)
from afterworlds.persistence.orm.mechanical import (
    MechanicalAcceptanceBatchORM,
    MechanicalAcceptanceORM,
    MechanicalBatchDiffORM,
    MechanicalBatchScopeORM,
    MechanicalComponentORM,
    MechanicalFactORM,
    MechanicalProjectionORM,
    MechanicalProseBindingORM,
    MechanicalProvenanceORM,
    MechanicalRecordORM,
    MechanicalReferenceORM,
    MechanicalRelationshipORM,
    MechanicalSpanORM,
)

__all__ = [
    "ProjectionNotPersistedError",
    "compute_persisted_state_digest",
    "delete_projection",
    "persist_draft",
    "reconstruct_candidate",
    "record_persisted_state_digest",
    "verify_reconstruction",
]


class ProjectionNotPersistedError(LookupError):
    """Raised when a projection UUID has no persisted header row."""


def persist_draft(
    session: Session, identified: IdentifiedProjection, *, now: str
) -> None:
    """Write the complete projection as a draft.

    Typed rows throughout: spans, acceptance evidence, records, components,
    facts, prose bindings, relationships, references, and provenance each get
    their own table, so the projection is reconstructable from the database
    rather than from one opaque payload column.
    """
    candidate = identified.candidate
    ledger = candidate.classification
    draft = candidate.representation
    uuid_ = identified.projection_uuid

    session.add(
        MechanicalProjectionORM(
            projection_uuid=uuid_,
            package_uuid=candidate.binding.package_uuid,
            release_version=candidate.binding.release_version,
            authoritative_source_hash=candidate.binding.authoritative_source_hash,
            transform_config_hash=candidate.binding.transform_config_hash,
            bundle_root_hash=candidate.binding.bundle_root_hash,
            persisted_corpus_digest=candidate.binding.persisted_corpus_digest,
            semantic_policy_version=ledger.policy_version,
            semantic_policy_hash=ledger.policy_hash,
            payload_hash=identified.payload_hash,
            persisted_state_digest=None,
            publication_status="draft",
            created_at=now,
        )
    )
    # The header lands before anything scoped to it: every child row carries a
    # real FK, so a partially written projection cannot exist without one.
    session.flush()

    for span in ledger.spans:
        session.add(
            MechanicalSpanORM(
                projection_uuid=uuid_,
                span_id=span.span_id,
                leaf_id=span.leaf_id,
                char_start=span.char_start,
                char_end=span.char_end,
                disposition=span.disposition.value,
                review_state=span.review_state.value,
                non_mechanical_reason_code=span.non_mechanical_reason_code,
            )
        )

    for batch in ledger.batches:
        session.add(
            MechanicalAcceptanceBatchORM(
                projection_uuid=uuid_,
                batch_id=batch.batch_id,
                rule=batch.rule,
                semantic_diff_hash=batch.semantic_diff_hash,
            )
        )
        # Scope order is retained: it is the reviewer's recorded scope, not a
        # set the build is free to re-derive.
        for ordinal, span_id in enumerate(batch.resolved_scope):
            session.add(
                MechanicalBatchScopeORM(
                    projection_uuid=uuid_,
                    batch_id=batch.batch_id,
                    span_id=span_id,
                    ordinal=ordinal,
                )
            )
        for entry in batch.diff:
            session.add(
                MechanicalBatchDiffORM(
                    projection_uuid=uuid_,
                    batch_id=batch.batch_id,
                    span_id=entry.span_id,
                    prior_disposition=(
                        entry.prior_disposition.value
                        if entry.prior_disposition
                        else None
                    ),
                    prior_reason_code=entry.prior_reason_code,
                    accepted_disposition=entry.accepted_disposition.value,
                    accepted_reason_code=entry.accepted_reason_code,
                )
            )

    for acceptance in ledger.acceptances:
        session.add(
            MechanicalAcceptanceORM(
                projection_uuid=uuid_,
                span_id=acceptance.span_id,
                batch_id=acceptance.batch_id,
                reviewer=acceptance.reviewer,
                accepted_at=acceptance.accepted_at,
            )
        )

    for record in draft.records:
        session.add(
            MechanicalRecordORM(
                projection_uuid=uuid_,
                record_id=identified.record_ids[record.semantic_key],
                semantic_key=record.semantic_key,
                kind=record.kind.value,
                parent_key=record.parent_key,
            )
        )

    for component in draft.components:
        key = (component.record_key, component.semantic_key)
        session.add(
            MechanicalComponentORM(
                projection_uuid=uuid_,
                component_id=identified.component_ids[key],
                record_key=component.record_key,
                semantic_key=component.semantic_key,
                handling=component.handling.value,
                irreducibility_reason_code=component.irreducibility_reason_code,
            )
        )
        for fact in component.facts:
            key_ = fact_key(fact)
            session.add(
                MechanicalFactORM(
                    projection_uuid=uuid_,
                    fact_id=identified.fact_ids[
                        (component.record_key, component.semantic_key, key_)
                    ],
                    record_key=component.record_key,
                    component_key=component.semantic_key,
                    fact_key=key_,
                    family=str(fact_payload(fact)["family"]),
                    payload=fact_payload(fact),
                )
            )

    for binding in draft.prose_bindings:
        session.add(
            MechanicalProseBindingORM(
                projection_uuid=uuid_,
                record_key=binding.record_key,
                component_key=binding.component_key,
                chunk_id=binding.chunk_id,
                irreducibility_reason_code=binding.irreducibility_reason_code,
            )
        )

    for relationship in draft.relationships:
        session.add(
            MechanicalRelationshipORM(
                projection_uuid=uuid_,
                source_record_key=relationship.source_record_key,
                target_record_key=relationship.target_record_key,
                kind=relationship.kind.value,
            )
        )

    for reference in draft.references:
        session.add(
            MechanicalReferenceORM(
                projection_uuid=uuid_,
                from_record_key=reference.from_record_key,
                from_component_key=reference.from_component_key,
                source_text=reference.source_text,
                scope_key=reference.scope_key,
                target_record_key=reference.target_record_key,
            )
        )

    for claim in draft.provenance:
        session.add(
            MechanicalProvenanceORM(
                projection_uuid=uuid_,
                target_kind=claim.target_kind.value,
                target_key=list(claim.target_key),
                span_id=claim.span_id,
                role=claim.role.value,
            )
        )

    session.flush()


def _header(session: Session, projection_uuid: str) -> MechanicalProjectionORM:
    row = session.execute(
        select(MechanicalProjectionORM).where(
            MechanicalProjectionORM.projection_uuid == projection_uuid
        )
    ).scalar_one_or_none()
    if row is None:
        raise ProjectionNotPersistedError(projection_uuid)
    return row


def reconstruct_candidate(
    session: Session, projection_uuid: str
) -> ProjectionCandidate:
    """Rebuild the complete candidate from persisted rows alone.

    Takes no in-memory candidate: what comes back is what the database holds,
    which is the only way the digest can prove persistence rather than prove
    that the builder still remembers what it meant to write.
    """
    header = _header(session, projection_uuid)

    def rows(model: type) -> list:  # type: ignore[type-arg]
        return list(
            session.execute(
                select(model).where(model.projection_uuid == projection_uuid)  # type: ignore[attr-defined]
            )
            .scalars()
            .all()
        )

    spans = tuple(
        SemanticSpan(
            span_id=r.span_id,
            leaf_id=r.leaf_id,
            char_start=r.char_start,
            char_end=r.char_end,
            disposition=SemanticDisposition(r.disposition),
            review_state=ReviewState(r.review_state),
            non_mechanical_reason_code=r.non_mechanical_reason_code,
        )
        for r in rows(MechanicalSpanORM)
    )

    scope_rows = rows(MechanicalBatchScopeORM)
    diff_rows = rows(MechanicalBatchDiffORM)
    batches = tuple(
        AcceptanceBatch(
            batch_id=b.batch_id,
            rule=b.rule,
            resolved_scope=tuple(
                s.span_id
                for s in sorted(
                    (s for s in scope_rows if s.batch_id == b.batch_id),
                    key=lambda s: s.ordinal,
                )
            ),
            diff=tuple(
                SemanticDiffEntry(
                    span_id=d.span_id,
                    prior_disposition=(
                        SemanticDisposition(d.prior_disposition)
                        if d.prior_disposition
                        else None
                    ),
                    prior_reason_code=d.prior_reason_code,
                    accepted_disposition=SemanticDisposition(d.accepted_disposition),
                    accepted_reason_code=d.accepted_reason_code,
                )
                for d in diff_rows
                if d.batch_id == b.batch_id
            ),
            semantic_diff_hash=b.semantic_diff_hash,
        )
        for b in rows(MechanicalAcceptanceBatchORM)
    )

    acceptances = tuple(
        AcceptanceRecord(
            span_id=a.span_id,
            batch_id=a.batch_id,
            reviewer=a.reviewer,
            accepted_at=a.accepted_at,
        )
        for a in rows(MechanicalAcceptanceORM)
    )

    fact_rows = rows(MechanicalFactORM)
    components = tuple(
        ComponentDraft(
            record_key=c.record_key,
            semantic_key=c.semantic_key,
            handling=ComponentHandling(c.handling),
            irreducibility_reason_code=c.irreducibility_reason_code,
            facts=tuple(
                fact_from_payload(f.payload)
                for f in fact_rows
                if (f.record_key, f.component_key) == (c.record_key, c.semantic_key)
            ),
        )
        for c in rows(MechanicalComponentORM)
    )

    representation = RepresentationDraft(
        records=tuple(
            RecordDraft(
                semantic_key=r.semantic_key,
                kind=RecordKind(r.kind),
                parent_key=r.parent_key,
            )
            for r in rows(MechanicalRecordORM)
        ),
        components=components,
        prose_bindings=tuple(
            ProseBindingDraft(
                component_key=p.component_key,
                record_key=p.record_key,
                chunk_id=p.chunk_id,
                irreducibility_reason_code=p.irreducibility_reason_code,
            )
            for p in rows(MechanicalProseBindingORM)
        ),
        relationships=tuple(
            RelationshipDraft(
                source_record_key=r.source_record_key,
                target_record_key=r.target_record_key,
                kind=RelationshipKind(r.kind),
            )
            for r in rows(MechanicalRelationshipORM)
        ),
        references=tuple(
            ReferenceDraft(
                from_record_key=r.from_record_key,
                from_component_key=r.from_component_key,
                source_text=r.source_text,
                scope_key=r.scope_key,
                target_record_key=r.target_record_key,
            )
            for r in rows(MechanicalReferenceORM)
        ),
        provenance=tuple(
            ProvenanceClaim(
                target_kind=ProvenanceTargetKind(p.target_kind),
                target_key=tuple(p.target_key),
                span_id=p.span_id,
                role=ProvenanceRole(p.role),
            )
            for p in rows(MechanicalProvenanceORM)
        ),
    )

    return ProjectionCandidate(
        binding=ReleaseBinding(
            package_uuid=header.package_uuid,
            release_version=header.release_version,
            authoritative_source_hash=header.authoritative_source_hash,
            transform_config_hash=header.transform_config_hash,
            bundle_root_hash=header.bundle_root_hash,
            persisted_corpus_digest=header.persisted_corpus_digest,
        ),
        classification=ClassificationLedger(
            package_uuid=header.package_uuid,
            release_version=header.release_version,
            policy_version=header.semantic_policy_version,
            policy_hash=header.semantic_policy_hash,
            spans=spans,
            batches=batches,
            acceptances=acceptances,
        ),
        representation=representation,
    )


def compute_persisted_state_digest(session: Session, projection_uuid: str) -> str:
    """Digest the reconstructed state, including the persisted derived IDs.

    The payload alone would not notice a corrupted ``record_id`` column, so the
    digest covers the stored subidentities too: a tampered derived ID changes
    the digest even when every semantic value survives intact.
    """
    candidate = reconstruct_candidate(session, projection_uuid)
    stored_ids = {
        "records": sorted(
            (r.semantic_key, r.record_id)
            for r in session.execute(
                select(MechanicalRecordORM).where(
                    MechanicalRecordORM.projection_uuid == projection_uuid
                )
            )
            .scalars()
            .all()
        ),
        "components": sorted(
            (c.record_key, c.semantic_key, c.component_id)
            for c in session.execute(
                select(MechanicalComponentORM).where(
                    MechanicalComponentORM.projection_uuid == projection_uuid
                )
            )
            .scalars()
            .all()
        ),
        "facts": sorted(
            (f.record_key, f.component_key, f.fact_key, f.fact_id)
            for f in session.execute(
                select(MechanicalFactORM).where(
                    MechanicalFactORM.projection_uuid == projection_uuid
                )
            )
            .scalars()
            .all()
        ),
    }
    return hash_obj(
        {
            "projection_uuid": projection_uuid,
            "payload": projection_payload(candidate),
            "derived_ids": stored_ids,
        }
    )


def verify_reconstruction(
    session: Session, identified: IdentifiedProjection
) -> tuple[str, ...]:
    """Return violations found by rebuilding the projection from the database.

    Catches omission (a row that never landed), tamper (a value changed after
    the fact), and stale reuse (a persisted projection whose content no longer
    derives its own identity).
    """
    findings: list[str] = []
    uuid_ = identified.projection_uuid

    try:
        header = _header(session, uuid_)
    except ProjectionNotPersistedError:
        return (f"projection {uuid_}: no persisted header row",)

    reconstructed = reconstruct_candidate(session, uuid_)
    reidentified = identify_projection(reconstructed)

    if reidentified.projection_uuid != uuid_:
        findings.append(
            f"projection {uuid_}: reconstructed state derives "
            f"{reidentified.projection_uuid}"
        )
    if header.payload_hash != reidentified.payload_hash:
        findings.append(
            f"projection {uuid_}: persisted payload hash does not match "
            f"reconstructed state"
        )
    if header.publication_status != "draft":
        findings.append(
            f"projection {uuid_}: expected a draft, found "
            f"{header.publication_status!r}"
        )

    # Derived IDs are stored, so a corrupted one must be caught rather than
    # recomputed away at read time.
    for row in (
        session.execute(
            select(MechanicalRecordORM).where(
                MechanicalRecordORM.projection_uuid == uuid_
            )
        )
        .scalars()
        .all()
    ):
        expected = reidentified.record_ids.get(row.semantic_key)
        if expected != row.record_id:
            findings.append(
                f"record {row.semantic_key}: persisted id {row.record_id} != "
                f"derived {expected}"
            )
    for crow in (
        session.execute(
            select(MechanicalComponentORM).where(
                MechanicalComponentORM.projection_uuid == uuid_
            )
        )
        .scalars()
        .all()
    ):
        expected = reidentified.component_ids.get((crow.record_key, crow.semantic_key))
        if expected != crow.component_id:
            findings.append(
                f"component {crow.record_key}/{crow.semantic_key}: persisted id "
                f"{crow.component_id} != derived {expected}"
            )
    for frow in (
        session.execute(
            select(MechanicalFactORM).where(MechanicalFactORM.projection_uuid == uuid_)
        )
        .scalars()
        .all()
    ):
        expected = reidentified.fact_ids.get(
            (frow.record_key, frow.component_key, frow.fact_key)
        )
        if expected != frow.fact_id:
            findings.append(
                f"fact {frow.record_key}/{frow.component_key}/{frow.fact_key}: "
                f"persisted id {frow.fact_id} != derived {expected}"
            )

    return tuple(findings)


def record_persisted_state_digest(
    session: Session, projection_uuid: str, digest: str
) -> None:
    """Record the digest computed from reconstructed state, exactly once."""
    header = _header(session, projection_uuid)
    if header.persisted_state_digest is not None:
        raise ValueError(
            f"projection {projection_uuid}: persisted-state digest already recorded"
        )
    header.persisted_state_digest = digest
    session.flush()


def delete_projection(session: Session, projection_uuid: str) -> None:
    """Remove a draft projection and every row scoped to it."""
    for model in (
        MechanicalSpanORM,
        MechanicalAcceptanceBatchORM,
        MechanicalBatchScopeORM,
        MechanicalBatchDiffORM,
        MechanicalAcceptanceORM,
        MechanicalRecordORM,
        MechanicalComponentORM,
        MechanicalFactORM,
        MechanicalProseBindingORM,
        MechanicalRelationshipORM,
        MechanicalReferenceORM,
        MechanicalProvenanceORM,
    ):
        session.execute(delete(model).where(model.projection_uuid == projection_uuid))
    session.execute(
        delete(MechanicalProjectionORM).where(
            MechanicalProjectionORM.projection_uuid == projection_uuid
        )
    )
    session.flush()
