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

Hash-shaped values in this package are not all the same kind of thing, and the
distinction decides which may be supplied by a caller:

* ``payload_hash`` — a *pre-persistence* hash of the candidate. Supplied at
  write time and later checked against reconstruction by
  :func:`verify_reconstruction`, so a wrong value is caught, not trusted.
* ``semantic_diff_hash`` — retained review evidence. Supplied with the batch
  and independently recomputed from the retained diff during acceptance
  validation, so it identifies evidence rather than asserting it.
* ``persisted_corpus_digest`` — CRD Issue 5c's own proof, carried in the
  binding as part of the projection's meaning. Equality against the bound 5c
  release is the publication gate's job, not this module's.
* ``persisted_state_digest`` — the only *post-persistence* proof this package
  records, and therefore the only one no caller may supply. It is derived at
  the seam that records it, from the state it claims to prove, and
  :func:`verify_reconstruction` re-derives it whenever one is present. What PR 1
  does *not* do is decide whether a proven projection may be published or
  activated; that gate is the next PR's.
"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from afterworlds.ingestion.corpus.hashing import hash_obj
from afterworlds.ingestion.mechanical.accounting import acceptance_evidence_payload
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
from afterworlds.ingestion.mechanical.raw_state import (
    PersistedStateReconstructionError,
    load_raw_state,
    parse_enum,
    validate_raw_closure,
)
from afterworlds.ingestion.mechanical.representation import (
    ComponentDraft,
    MalformedFactPayloadError,
    MechanicalFact,
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
    UnknownFactFamilyError,
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
    "PersistedStateReconstructionError",
    "ProjectionNotPersistedError",
    "compute_persisted_state_digest",
    "delete_projection",
    "persist_draft",
    "reconstruct_candidate",
    "record_persisted_state_digest",
    "verify_persisted_state",
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
                span_id=binding.span_id,
                chunk_char_start=binding.chunk_char_start,
                chunk_char_end=binding.chunk_char_end,
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


def _fact_from_row(row: MechanicalFactORM) -> MechanicalFact:
    """Rebuild one typed fact from its row, checking the duplicated columns.

    ``family`` and ``fact_key`` are stored alongside the payload for querying,
    which means they can be rewritten independently of it. Reconstruction
    checks both against the payload rather than trusting either: a row whose
    columns disagree with its own content has been altered, and picking a
    winner would be repair, not reconstruction.
    """
    try:
        fact = fact_from_payload(row.payload, declared_family=row.family)
    except (MalformedFactPayloadError, UnknownFactFamilyError) as exc:
        raise PersistedStateReconstructionError(
            f"rp_mech_facts {row.record_key}/{row.component_key}: {exc}"
        ) from exc
    recomputed = fact_key(fact)
    if row.fact_key != recomputed:
        raise PersistedStateReconstructionError(
            f"rp_mech_facts {row.record_key}/{row.component_key}: persisted "
            f"fact_key {row.fact_key!r} disagrees with payload ({recomputed!r})"
        )
    return fact


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

    Two stages, in this order: the complete raw row set is loaded and proven
    closed, and only then is semantic meaning imposed on it. Doing it the other
    way round is what let an orphan child row vanish during a join instead of
    failing - invisible to the candidate, and therefore invisible to the digest
    computed over it.

    Takes no in-memory candidate: what comes back is what the database holds,
    which is the only way the digest can prove persistence rather than prove
    that the builder still remembers what it meant to write. Every typed column
    is parsed strictly, so a corrupted enum raises
    PersistedStateReconstructionError rather than letting an unclassified
    exception escape an API whose contract is to report findings.
    """
    header = _header(session, projection_uuid)
    raw = load_raw_state(session, projection_uuid, header)
    validate_raw_closure(raw)

    spans = tuple(
        SemanticSpan(
            span_id=r.span_id,
            leaf_id=r.leaf_id,
            char_start=r.char_start,
            char_end=r.char_end,
            disposition=parse_enum(
                SemanticDisposition,
                r.disposition,
                "rp_mech_spans",
                r.span_id,
                "disposition",
            ),
            review_state=parse_enum(
                ReviewState, r.review_state, "rp_mech_spans", r.span_id, "review_state"
            ),
            non_mechanical_reason_code=r.non_mechanical_reason_code,
        )
        for r in raw.spans
    )

    batches = tuple(
        AcceptanceBatch(
            batch_id=b.batch_id,
            rule=b.rule,
            resolved_scope=tuple(
                s.span_id
                for s in sorted(
                    (s for s in raw.batch_scope if s.batch_id == b.batch_id),
                    key=lambda s: s.ordinal,
                )
            ),
            diff=tuple(
                SemanticDiffEntry(
                    span_id=d.span_id,
                    prior_disposition=(
                        parse_enum(
                            SemanticDisposition,
                            d.prior_disposition,
                            "rp_mech_batch_diff",
                            f"{d.batch_id}/{d.span_id}",
                            "prior_disposition",
                        )
                        if d.prior_disposition
                        else None
                    ),
                    prior_reason_code=d.prior_reason_code,
                    accepted_disposition=parse_enum(
                        SemanticDisposition,
                        d.accepted_disposition,
                        "rp_mech_batch_diff",
                        f"{d.batch_id}/{d.span_id}",
                        "accepted_disposition",
                    ),
                    accepted_reason_code=d.accepted_reason_code,
                )
                for d in raw.batch_diff
                if d.batch_id == b.batch_id
            ),
            semantic_diff_hash=b.semantic_diff_hash,
        )
        for b in raw.batches
    )

    acceptances = tuple(
        AcceptanceRecord(
            span_id=a.span_id,
            batch_id=a.batch_id,
            reviewer=a.reviewer,
            accepted_at=a.accepted_at,
        )
        for a in raw.acceptances
    )

    components = tuple(
        ComponentDraft(
            record_key=c.record_key,
            semantic_key=c.semantic_key,
            handling=parse_enum(
                ComponentHandling,
                c.handling,
                "rp_mech_components",
                f"{c.record_key}/{c.semantic_key}",
                "handling",
            ),
            irreducibility_reason_code=c.irreducibility_reason_code,
            facts=tuple(
                _fact_from_row(f)
                for f in raw.facts
                if (f.record_key, f.component_key) == (c.record_key, c.semantic_key)
            ),
        )
        for c in raw.components
    )

    representation = RepresentationDraft(
        records=tuple(
            RecordDraft(
                semantic_key=r.semantic_key,
                kind=parse_enum(
                    RecordKind, r.kind, "rp_mech_records", r.semantic_key, "kind"
                ),
                parent_key=r.parent_key,
            )
            for r in raw.records
        ),
        components=components,
        prose_bindings=tuple(
            ProseBindingDraft(
                component_key=p.component_key,
                record_key=p.record_key,
                chunk_id=p.chunk_id,
                span_id=p.span_id,
                chunk_char_start=p.chunk_char_start,
                chunk_char_end=p.chunk_char_end,
                irreducibility_reason_code=p.irreducibility_reason_code,
            )
            for p in raw.prose_bindings
        ),
        relationships=tuple(
            RelationshipDraft(
                source_record_key=r.source_record_key,
                target_record_key=r.target_record_key,
                kind=parse_enum(
                    RelationshipKind,
                    r.kind,
                    "rp_mech_relationships",
                    f"{r.source_record_key}->{r.target_record_key}",
                    "kind",
                ),
            )
            for r in raw.relationships
        ),
        references=tuple(
            ReferenceDraft(
                from_record_key=r.from_record_key,
                from_component_key=r.from_component_key,
                source_text=r.source_text,
                scope_key=r.scope_key,
                target_record_key=r.target_record_key,
            )
            for r in raw.references
        ),
        provenance=tuple(
            ProvenanceClaim(
                target_kind=parse_enum(
                    ProvenanceTargetKind,
                    p.target_kind,
                    "rp_mech_provenance",
                    str(p.row_id),
                    "target_kind",
                ),
                target_key=tuple(p.target_key),
                span_id=p.span_id,
                role=parse_enum(
                    ProvenanceRole, p.role, "rp_mech_provenance", str(p.row_id), "role"
                ),
            )
            for p in raw.provenance
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
    """Digest the reconstructed state: semantics, subidentities, and evidence.

    Three layers, because each covers what the others cannot:

    * the **semantic payload** — what the projection means;
    * the **persisted derived IDs** — a corrupted ``record_id`` leaves every
      semantic value intact and would otherwise pass; and
    * the **retained acceptance evidence** — reviewer, timestamp, batch rule,
      ordered scope, diff, and review state are deliberately outside semantic
      identity, so without this layer they could be rewritten after the digest
      was recorded and nothing would notice.

    The last layer is why this digest and the projection UUID are different
    things. The UUID answers "is this the same authority"; the digest answers
    "is this the same persisted state, including how it was reviewed".

    ``created_at`` is excluded: it is build wall-clock, and the CRD Issue 5c
    determinism rule keeps timestamps out of hashed artifacts so an identical
    rebuild stays comparable. ``accepted_at`` is different — it is reviewer-
    supplied evidence of an acceptance action, so it is covered above.

    Unlike :func:`verify_reconstruction`, this raises rather than reporting when
    the state will not rebuild. The asymmetry is intentional: verification
    collects findings for a caller deciding whether state is sound, whereas a
    digest of unreconstructable state would be a number that means nothing.
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
            "acceptance_evidence": acceptance_evidence_payload(
                candidate.classification
            ),
        }
    )


def verify_reconstruction(
    session: Session,
    identified: IdentifiedProjection,
    *,
    expected_status: str = "draft",
) -> tuple[str, ...]:
    """Verify the persisted projection a build just identified.

    Thin alias for :func:`verify_persisted_state`: the identity is the only
    thing the verification needs from *identified*, because every value it
    compares is re-derived from the database. Kept as the build-time spelling
    so a caller holding an :class:`IdentifiedProjection` need not unwrap it.
    """
    return verify_persisted_state(
        session, identified.projection_uuid, expected_status=expected_status
    )


def verify_persisted_state(
    session: Session,
    projection_uuid: str,
    *,
    expected_status: str = "draft",
) -> tuple[str, ...]:
    """Return violations found by rebuilding the projection from the database.

    Catches omission (a row that never landed), tamper (a value changed after
    the fact), and stale reuse (a persisted projection whose content no longer
    derives its own identity).

    Takes only the projection's identity, so the publication gate — which has
    no in-memory build to compare against — verifies persisted state against
    the database's *own recorded claims*: the header's UUID, payload hash,
    recorded digest, and stored derived IDs are each re-derived from the rows
    and must agree.

    ``expected_status`` is explicit because the same verification runs before
    publication and, later, against a published projection; hard-coding
    ``draft`` here would make every post-publication check report a spurious
    finding.
    """
    findings: list[str] = []
    uuid_ = projection_uuid

    try:
        header = _header(session, uuid_)
    except ProjectionNotPersistedError:
        return (f"projection {uuid_}: no persisted header row",)

    try:
        reconstructed = reconstruct_candidate(session, uuid_)
    except PersistedStateReconstructionError as exc:
        # A row that cannot rebuild is tamper or omission, which is exactly
        # what this check reports — reporting it beats propagating an
        # exception to a caller collecting findings.
        return (f"projection {uuid_}: persisted state does not reconstruct: {exc}",)

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
    # Once a proof is recorded it is a claim about persisted state, so
    # verification re-derives it. Without this, evidence-only tamper after
    # recording would leave the recorded digest stale but unchallenged: the
    # payload hash and derived IDs do not cover review evidence.
    if header.persisted_state_digest is not None:
        current = compute_persisted_state_digest(session, uuid_)
        if current != header.persisted_state_digest:
            findings.append(
                f"projection {uuid_}: recorded persisted-state digest no longer "
                f"matches current persisted state"
            )

    if header.publication_status != expected_status:
        findings.append(
            f"projection {uuid_}: expected {expected_status!r}, found "
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


def record_persisted_state_digest(session: Session, projection_uuid: str) -> str:
    """Derive and record this projection's persisted-state digest, exactly once.

    The digest is computed *here*, from this projection's own reconstructed
    state inside the recording transaction, and returned. There is deliberately
    no digest parameter: a caller-supplied value can be stale, computed before
    an intervening mutation, or belong to a different projection, and the
    exactly-once guard would then freeze that false proof in place. A proof
    that does not derive from the state it claims to prove is not a proof.

    Pending session changes are flushed first so the reconstruction sees the
    same state the transaction holds. If reconstruction or digest computation
    fails, the exception propagates and the header keeps ``NULL`` — an
    unprovable projection must not carry a recorded proof.
    """
    header = _header(session, projection_uuid)
    if header.persisted_state_digest is not None:
        raise ValueError(
            f"projection {projection_uuid}: persisted-state digest already recorded"
        )
    session.flush()
    digest = compute_persisted_state_digest(session, projection_uuid)
    header.persisted_state_digest = digest
    session.flush()
    return digest


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
