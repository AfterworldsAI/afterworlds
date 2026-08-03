"""Raw persisted closure and typed columns — CRD Issue 5d, review round 5.

Two symptoms, one defect: persisted rows were projected into the semantic model
before anything proved the raw row set was a closed, typed aggregate. An orphan
child then vanished during a join — out of the candidate and out of the digest
computed over it — and a corrupted enum escaped as an unclassified exception
from an API whose contract is to report findings.

Every test here corrupts real persisted rows after a successful write, because
that is the only state this boundary exists to catch.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from afterworlds.ingestion.mechanical.persistence import (
    compute_persisted_state_digest,
    persist_draft,
    reconstruct_candidate,
    record_persisted_state_digest,
    verify_reconstruction,
)
from afterworlds.ingestion.mechanical.projection import (
    identify_projection,
    projection_payload,
)
from afterworlds.ingestion.mechanical.raw_state import (
    PersistedStateReconstructionError,
    RawProjectionState,
    validate_raw_closure,
)
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.persistence.orm.base import Base
from afterworlds.persistence.orm.corpus import CorpusReleaseORM
from afterworlds.persistence.orm.mechanical import (
    MechanicalAcceptanceBatchORM,
    MechanicalAcceptanceORM,
    MechanicalActiveProjectionORM,
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
from afterworlds.persistence.orm.rules_package import RulesPackageORM
from tests.ingestion.mechanical.conftest import (
    SCOPED_REFERENCES,
    batch_accepted_ledger,
    build_candidate,
    build_representation,
    reference_claim,
)

NOW = "2026-08-01T00:00:00Z"

#: Every rp_mech_* table, with how its rows participate in the proof. A new
#: table without a policy fails the inventory test below rather than quietly
#: sitting outside both reconstruction and the digest.
TABLE_POLICY: dict[type, str] = {
    MechanicalProjectionORM: "header",
    MechanicalSpanORM: "semantic",
    MechanicalAcceptanceBatchORM: "evidence",
    MechanicalBatchScopeORM: "evidence",
    MechanicalBatchDiffORM: "evidence",
    MechanicalAcceptanceORM: "evidence",
    MechanicalRecordORM: "semantic+derived_id",
    MechanicalComponentORM: "semantic+derived_id",
    MechanicalFactORM: "semantic+derived_id",
    MechanicalProseBindingORM: "semantic",
    MechanicalRelationshipORM: "semantic",
    MechanicalReferenceORM: "semantic",
    MechanicalProvenanceORM: "semantic",
    # Package-scoped, not projection-scoped: which projection a package has
    # activated is not part of any projection's reconstructed meaning, so it is
    # deliberately outside the raw row set and the persisted-state digest. A
    # projection's content must not change when it is activated.
    MechanicalActiveProjectionORM: "activation",
}


@pytest.fixture()
def session(tmp_path) -> Iterator[Session]:  # type: ignore[no-untyped-def]
    engine = create_engine(f"sqlite:///{tmp_path / 'raw.db'}")
    Base.metadata.create_all(engine)
    with create_session_factory(engine)() as s:
        s.add(
            RulesPackageORM(
                rules_package_id="pkg-5c",
                name="SRD 5.2.1",
                system="dnd5e",
                version="5.2.1",
                is_enabled=True,
                publication_status="published",
                created_at=NOW,
                updated_at=NOW,
            )
        )
        s.flush()
        s.add(
            CorpusReleaseORM(
                package_uuid="pkg-5c",
                release_version="rel-5c",
                authoritative_source_hash="a" * 64,
                transform_config_hash="b" * 64,
                bundle_root_hash="c" * 64,
                ledger_hash="1" * 64,
                policy_hash="2" * 64,
                reconciliation_hash="3" * 64,
                transform_config={},
                publication_status="published",
                created_at=NOW,
            )
        )
        s.flush()
        yield s


def _persist(session: Session, **overrides: object):  # type: ignore[no-untyped-def]
    identified = identify_projection(build_candidate(**overrides))
    persist_draft(session, identified, now=NOW)
    return identified


def _persist_batch(session: Session):  # type: ignore[no-untyped-def]
    return _persist(session, ledger=batch_accepted_ledger())


def _assert_rejected(session: Session, identified, fragment: str) -> None:  # type: ignore[no-untyped-def]
    """The corruption must be a finding, a digest failure, and unrecordable."""
    findings = verify_reconstruction(session, identified)
    assert any("does not reconstruct" in f for f in findings), findings
    assert any(fragment in f for f in findings), findings
    with pytest.raises(PersistedStateReconstructionError):
        compute_persisted_state_digest(session, identified.projection_uuid)
    with pytest.raises(PersistedStateReconstructionError):
        record_persisted_state_digest(session, identified.projection_uuid)
    header = session.execute(
        select(MechanicalProjectionORM).where(
            MechanicalProjectionORM.projection_uuid == identified.projection_uuid
        )
    ).scalar_one()
    assert header.persisted_state_digest is None


# -- orphan child rows -------------------------------------------------------


def test_orphan_batch_scope_row_is_rejected(session: Session) -> None:
    identified = _persist_batch(session)
    session.add(
        MechanicalBatchScopeORM(
            projection_uuid=identified.projection_uuid,
            batch_id="batch-that-never-existed",
            span_id="span-x",
            ordinal=0,
        )
    )
    session.flush()
    _assert_rejected(session, identified, "rp_mech_batch_scope")


def test_orphan_batch_diff_row_is_rejected(session: Session) -> None:
    identified = _persist_batch(session)
    session.add(
        MechanicalBatchDiffORM(
            projection_uuid=identified.projection_uuid,
            batch_id="batch-that-never-existed",
            span_id="span-x",
            prior_disposition=None,
            prior_reason_code=None,
            accepted_disposition="substantive",
            accepted_reason_code=None,
        )
    )
    session.flush()
    _assert_rejected(session, identified, "rp_mech_batch_diff")


def test_orphan_acceptance_naming_a_nonexistent_batch_is_rejected(
    session: Session,
) -> None:
    identified = _persist(session)
    row = session.execute(select(MechanicalAcceptanceORM)).scalars().first()
    assert row is not None
    row.batch_id = "batch-that-never-existed"
    session.flush()
    _assert_rejected(session, identified, "rp_mech_acceptances")


def test_batch_child_cannot_borrow_a_batch_from_another_projection(
    session: Session,
) -> None:
    # A batch with the same id exists — in a different projection. Matching on
    # batch_id alone would adopt this row; the relation is scoped, so it does
    # not.
    other = _persist_batch(session)
    plain = _persist(session, provenance=build_representation().provenance[:2])
    assert other.projection_uuid != plain.projection_uuid

    session.add(
        MechanicalBatchScopeORM(
            projection_uuid=plain.projection_uuid,
            batch_id="batch-wish",  # exists, but under `other`
            span_id="span-x",
            ordinal=0,
        )
    )
    session.flush()
    _assert_rejected(session, plain, "no header in this projection")


def test_orphan_fact_row_is_rejected(session: Session) -> None:
    identified = _persist(session)
    template = session.execute(select(MechanicalFactORM)).scalars().one()
    session.add(
        MechanicalFactORM(
            projection_uuid=identified.projection_uuid,
            fact_id="fact-orphan",
            record_key="record:that-never-existed",
            component_key="component:none",
            fact_key=template.fact_key,
            family=template.family,
            payload=dict(template.payload),
        )
    )
    session.flush()
    _assert_rejected(session, identified, "rp_mech_facts")


def test_orphan_component_and_binding_rows_are_rejected(session: Session) -> None:
    identified = _persist(session)
    session.add(
        MechanicalProseBindingORM(
            projection_uuid=identified.projection_uuid,
            record_key="record:that-never-existed",
            component_key="component:none",
            chunk_id="chunk-x",
            irreducibility_reason_code="open_ended_effect",
        )
    )
    session.flush()
    _assert_rejected(session, identified, "rp_mech_prose_bindings")


def test_orphan_relationship_row_is_rejected(session: Session) -> None:
    identified = _persist(session)
    session.add(
        MechanicalRelationshipORM(
            projection_uuid=identified.projection_uuid,
            source_record_key="record:that-never-existed",
            target_record_key="spell:wish",
            kind="grants",
        )
    )
    session.flush()
    _assert_rejected(session, identified, "rp_mech_relationships")


def test_orphan_reference_row_is_rejected(session: Session) -> None:
    identified = _persist(session)
    session.add(
        MechanicalReferenceORM(
            projection_uuid=identified.projection_uuid,
            from_record_key="record:that-never-existed",
            from_component_key="component:none",
            source_text="the servant",
            scope_key="spell:wish",
            target_record_key="spell:wish",
        )
    )
    session.flush()
    _assert_rejected(session, identified, "rp_mech_references")


def test_one_valid_row_plus_one_orphan_sibling_still_fails(session: Session) -> None:
    identified = _persist_batch(session)
    valid = session.execute(select(MechanicalBatchScopeORM)).scalars().first()
    assert valid is not None
    session.add(
        MechanicalBatchScopeORM(
            projection_uuid=identified.projection_uuid,
            batch_id="batch-that-never-existed",
            span_id=valid.span_id,
            ordinal=99,
        )
    )
    session.flush()
    _assert_rejected(session, identified, "rp_mech_batch_scope")


def test_orphan_rows_cannot_leave_the_digest_unchanged(session: Session) -> None:
    # The precise defect: before this correction the digest was computed over
    # the reconstructed ledger, so a dropped orphan left it identical.
    identified = _persist_batch(session)
    before = compute_persisted_state_digest(session, identified.projection_uuid)
    session.add(
        MechanicalBatchDiffORM(
            projection_uuid=identified.projection_uuid,
            batch_id="batch-that-never-existed",
            span_id="span-x",
            prior_disposition=None,
            prior_reason_code=None,
            accepted_disposition="substantive",
            accepted_reason_code=None,
        )
    )
    session.flush()
    with pytest.raises(PersistedStateReconstructionError):
        compute_persisted_state_digest(session, identified.projection_uuid)
    assert before  # the honest digest existed; the corrupted state has none


def test_duplicate_scope_ordinal_is_rejected(session: Session) -> None:
    identified = _persist_batch(session)
    existing = session.execute(select(MechanicalBatchScopeORM)).scalars().first()
    assert existing is not None
    session.add(
        MechanicalBatchScopeORM(
            projection_uuid=identified.projection_uuid,
            batch_id=existing.batch_id,
            span_id=existing.span_id,
            ordinal=existing.ordinal,
        )
    )
    session.flush()
    _assert_rejected(session, identified, "ordinal")


def test_malformed_provenance_target_key_is_rejected(session: Session) -> None:
    identified = _persist(session)
    row = session.execute(select(MechanicalProvenanceORM)).scalars().first()
    assert row is not None
    row.target_key = {"record": "spell:wish"}  # a dict, not a list of strings
    session.flush()
    _assert_rejected(session, identified, "not a list of strings")


def test_target_key_with_non_string_members_is_rejected(session: Session) -> None:
    identified = _persist(session)
    row = session.execute(select(MechanicalProvenanceORM)).scalars().first()
    assert row is not None
    row.target_key = ["spell:wish", 7]
    session.flush()
    _assert_rejected(session, identified, "not a list of strings")


# -- corrupted typed columns -------------------------------------------------

ENUM_CORRUPTIONS = [
    ("span disposition", MechanicalSpanORM, "disposition", "rp_mech_spans"),
    ("span review state", MechanicalSpanORM, "review_state", "rp_mech_spans"),
    (
        "prior batch disposition",
        MechanicalBatchDiffORM,
        "prior_disposition",
        "rp_mech_batch_diff",
    ),
    (
        "accepted batch disposition",
        MechanicalBatchDiffORM,
        "accepted_disposition",
        "rp_mech_batch_diff",
    ),
    ("component handling", MechanicalComponentORM, "handling", "rp_mech_components"),
    ("record kind", MechanicalRecordORM, "kind", "rp_mech_records"),
    (
        "relationship kind",
        MechanicalRelationshipORM,
        "kind",
        "rp_mech_relationships",
    ),
    (
        "provenance target kind",
        MechanicalProvenanceORM,
        "target_kind",
        "rp_mech_provenance",
    ),
    ("provenance role", MechanicalProvenanceORM, "role", "rp_mech_provenance"),
]


@pytest.mark.parametrize(
    ("label", "model", "field", "table"),
    ENUM_CORRUPTIONS,
    ids=[c[0] for c in ENUM_CORRUPTIONS],
)
def test_invalid_persisted_enum_is_reported_not_raised(
    session: Session, label: str, model: type, field: str, table: str
) -> None:
    identified = _persist_batch(session)
    row = session.execute(select(model)).scalars().first()  # type: ignore[arg-type]
    assert row is not None, label
    setattr(row, field, "corrupt")
    session.flush()
    _assert_rejected(session, identified, table)


def test_invalid_enum_message_names_field_and_value(session: Session) -> None:
    identified = _persist(session)
    row = session.execute(select(MechanicalSpanORM)).scalars().first()
    assert row is not None
    row.disposition = "corrupt"
    session.flush()
    (finding,) = verify_reconstruction(session, identified)
    assert "rp_mech_spans" in finding
    assert "disposition" in finding
    assert "'corrupt'" in finding
    assert "SemanticDisposition" in finding


# -- positive controls -------------------------------------------------------


def test_honest_batch_evidence_still_reconstructs(session: Session) -> None:
    identified = _persist_batch(session)
    rebuilt = reconstruct_candidate(session, identified.projection_uuid)
    assert projection_payload(rebuilt) == projection_payload(identified.candidate)
    assert rebuilt.classification.batches == (
        identified.candidate.classification.batches[0],
    )
    assert verify_reconstruction(session, identified) == ()


def test_honest_individual_acceptance_still_reconstructs(session: Session) -> None:
    identified = _persist(session)
    rebuilt = reconstruct_candidate(session, identified.projection_uuid)
    assert rebuilt.classification.acceptances == (
        identified.candidate.classification.acceptances
    )
    assert verify_reconstruction(session, identified) == ()


def test_honest_references_and_provenance_still_reconstruct(session: Session) -> None:
    reference = SCOPED_REFERENCES[0]
    identified = _persist(
        session,
        references=(reference,),
        provenance=build_representation().provenance + (reference_claim(reference),),
    )
    rebuilt = reconstruct_candidate(session, identified.projection_uuid)
    assert rebuilt.representation.references == (reference,)
    assert len(rebuilt.representation.provenance) == 5
    assert verify_reconstruction(session, identified) == ()


def test_recorded_digest_is_reverified(session: Session) -> None:
    # Evidence-only tamper after recording used to pass: the payload hash and
    # derived ids do not cover review evidence.
    identified = _persist_batch(session)
    record_persisted_state_digest(session, identified.projection_uuid)
    assert verify_reconstruction(session, identified) == ()

    row = session.execute(select(MechanicalAcceptanceORM)).scalars().first()
    assert row is not None
    row.reviewer = "someone-else"
    session.flush()
    findings = verify_reconstruction(session, identified)
    assert any(
        "recorded persisted-state digest no longer matches" in f for f in findings
    )


# -- sibling inventory -------------------------------------------------------


def test_every_rp_mech_table_has_a_proof_policy() -> None:
    declared = {name for name in Base.metadata.tables if name.startswith("rp_mech_")}
    classified = {model.__tablename__ for model in TABLE_POLICY}  # type: ignore[attr-defined]
    assert declared == classified, (
        "every rp_mech_* table needs a reconstruction/proof policy: "
        f"unclassified={sorted(declared - classified)}, "
        f"stale={sorted(classified - declared)}"
    )


def test_every_scoped_table_is_loaded_into_the_raw_state(session: Session) -> None:
    from afterworlds.ingestion.mechanical.raw_state import RawProjectionState

    identified = _persist_batch(session)
    header = session.execute(
        select(MechanicalProjectionORM).where(
            MechanicalProjectionORM.projection_uuid == identified.projection_uuid
        )
    ).scalar_one()
    from afterworlds.ingestion.mechanical.raw_state import load_raw_state

    raw = load_raw_state(session, identified.projection_uuid, header)
    loaded = {
        type(row).__tablename__  # type: ignore[attr-defined]
        for field in RawProjectionState.__dataclass_fields__
        if field not in {"projection_uuid", "header"}
        for row in getattr(raw, field)
    }
    scoped = {
        model.__tablename__  # type: ignore[attr-defined]
        for model, policy in TABLE_POLICY.items()
        if policy not in {"header", "activation"}
    }
    # The default batch-reviewed candidate populates every scoped table except
    # references, which the honest fixture leaves empty.
    assert loaded == scoped - {"rp_mech_references"}


# -- closure rules validated directly over a raw row set ---------------------
#
# These duplicates cannot be produced through the write path any more — the
# batch-identity constraint blocks one, and honest writes never emit the rest —
# but a corrupted database or one created with constraints disabled still can,
# which is precisely what the reconstruction check exists for. Validation is
# pure over the raw structure, so it is exercised directly.


def _raw(**overrides: object) -> RawProjectionState:
    empty: dict[str, object] = {
        "spans": (),
        "batches": (),
        "batch_scope": (),
        "batch_diff": (),
        "acceptances": (),
        "records": (),
        "components": (),
        "facts": (),
        "prose_bindings": (),
        "relationships": (),
        "references": (),
        "provenance": (),
    }
    empty.update(overrides)
    return RawProjectionState(
        projection_uuid="proj-1",
        header=MechanicalProjectionORM(projection_uuid="proj-1"),
        **empty,  # type: ignore[arg-type]
    )


def _closure_problem(raw: RawProjectionState) -> str:
    with pytest.raises(PersistedStateReconstructionError) as exc:
        validate_raw_closure(raw)
    return str(exc.value)


def test_duplicate_batch_id_makes_parentage_ambiguous() -> None:
    batch = MechanicalAcceptanceBatchORM(
        projection_uuid="proj-1", batch_id="b1", rule="r", semantic_diff_hash="h"
    )
    problem = _closure_problem(_raw(batches=(batch, batch)))
    assert "duplicate batch_id" in problem


def test_duplicate_diff_rows_for_one_span_are_rejected() -> None:
    batch = MechanicalAcceptanceBatchORM(
        projection_uuid="proj-1", batch_id="b1", rule="r", semantic_diff_hash="h"
    )
    diff = MechanicalBatchDiffORM(
        projection_uuid="proj-1",
        batch_id="b1",
        span_id="s1",
        prior_disposition=None,
        prior_reason_code=None,
        accepted_disposition="substantive",
        accepted_reason_code=None,
    )
    problem = _closure_problem(_raw(batches=(batch,), batch_diff=(diff, diff)))
    assert "duplicate diff rows" in problem


def test_duplicate_record_semantic_key_is_rejected() -> None:
    record = MechanicalRecordORM(
        projection_uuid="proj-1",
        record_id="r-1",
        semantic_key="spell:wish",
        kind="spell",
        parent_key=None,
    )
    problem = _closure_problem(_raw(records=(record, record)))
    assert "duplicate semantic_key" in problem


def test_duplicate_component_key_is_rejected() -> None:
    record = MechanicalRecordORM(
        projection_uuid="proj-1",
        record_id="r-1",
        semantic_key="spell:wish",
        kind="spell",
        parent_key=None,
    )
    component = MechanicalComponentORM(
        projection_uuid="proj-1",
        component_id="c-1",
        record_key="spell:wish",
        semantic_key="descriptor",
        handling="structured",
        irreducibility_reason_code=None,
    )
    problem = _closure_problem(
        _raw(records=(record,), components=(component, component))
    )
    assert "duplicate component" in problem


def test_component_naming_an_absent_record_is_rejected() -> None:
    component = MechanicalComponentORM(
        projection_uuid="proj-1",
        component_id="c-1",
        record_key="spell:ghost",
        semantic_key="descriptor",
        handling="structured",
        irreducibility_reason_code=None,
    )
    problem = _closure_problem(_raw(components=(component,)))
    assert "names record 'spell:ghost'" in problem


def test_an_empty_projection_is_closed() -> None:
    validate_raw_closure(_raw())
