"""Draft persistence and exact reconstruction — CRD Issue 5d, Decision 8.

Reconstruction reads only the database. Every negative control below perturbs
persisted state *after* the write and asserts the rebuild notices — omission,
tamper, and a corrupted derived identity that leaves every semantic value
intact.
"""

from __future__ import annotations

import pytest
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from afterworlds.ingestion.mechanical.persistence import (
    ProjectionNotPersistedError,
    compute_persisted_state_digest,
    delete_projection,
    persist_draft,
    reconstruct_candidate,
    record_persisted_state_digest,
    verify_reconstruction,
)
from afterworlds.ingestion.mechanical.projection import (
    identify_projection,
    projection_payload,
)
from afterworlds.ingestion.mechanical.representation import fact_from_payload
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.persistence.orm.base import Base
from afterworlds.persistence.orm.corpus import CorpusReleaseORM
from afterworlds.persistence.orm.mechanical import (
    MechanicalFactORM,
    MechanicalProjectionORM,
    MechanicalProvenanceORM,
    MechanicalRecordORM,
    MechanicalSpanORM,
)
from afterworlds.persistence.orm.rules_package import RulesPackageORM
from tests.ingestion.mechanical.conftest import SPELL_KEY, build_candidate

NOW = "2026-07-31T00:00:00Z"


@pytest.fixture()
def session(tmp_path) -> Session:  # type: ignore[no-untyped-def]
    engine = create_engine(f"sqlite:///{tmp_path / 'mech.db'}")
    Base.metadata.create_all(engine)
    factory = create_session_factory(engine)
    with factory() as s:
        # The projection FKs a real published 5c release row.
        s.add(
            RulesPackageORM(
                rules_package_id="pkg-5c",
                name="SRD 5.2.1",
                system="dnd5e",
                version="5.2.1",
                is_enabled=True,
                publication_status="published",
                created_at="2026-07-31T00:00:00Z",
                updated_at="2026-07-31T00:00:00Z",
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


def _persist(session: Session):  # type: ignore[no-untyped-def]
    identified = identify_projection(build_candidate())
    persist_draft(session, identified, now=NOW)
    return identified


def test_roundtrip_reconstructs_the_exact_candidate(session: Session) -> None:
    identified = _persist(session)
    rebuilt = reconstruct_candidate(session, identified.projection_uuid)
    assert projection_payload(rebuilt) == projection_payload(identified.candidate)
    assert identify_projection(rebuilt).projection_uuid == identified.projection_uuid


def test_reconstruction_of_an_honest_draft_has_no_findings(session: Session) -> None:
    identified = _persist(session)
    assert verify_reconstruction(session, identified) == ()


def test_persisted_draft_is_never_published(session: Session) -> None:
    identified = _persist(session)
    header = session.execute(
        select(MechanicalProjectionORM).where(
            MechanicalProjectionORM.projection_uuid == identified.projection_uuid
        )
    ).scalar_one()
    assert header.publication_status == "draft"
    assert header.persisted_state_digest is None


def test_facts_rebuild_into_their_declared_dataclass(session: Session) -> None:
    identified = _persist(session)
    row = session.execute(
        select(MechanicalFactORM).where(
            MechanicalFactORM.projection_uuid == identified.projection_uuid
        )
    ).scalar_one()
    rebuilt = fact_from_payload(row.payload)
    assert type(rebuilt).__name__ == "SpellDescriptorFact"
    assert rebuilt.level == 9


def test_digest_covers_reconstructed_state(session: Session) -> None:
    identified = _persist(session)
    first = compute_persisted_state_digest(session, identified.projection_uuid)
    assert first == compute_persisted_state_digest(session, identified.projection_uuid)


def test_digest_is_recorded_once(session: Session) -> None:
    identified = _persist(session)
    digest = compute_persisted_state_digest(session, identified.projection_uuid)
    record_persisted_state_digest(session, identified.projection_uuid, digest)
    with pytest.raises(ValueError):
        record_persisted_state_digest(session, identified.projection_uuid, digest)


# -- omission, tamper, corrupted identity ------------------------------------


def test_omitted_span_row_is_detected(session: Session) -> None:
    identified = _persist(session)
    before = compute_persisted_state_digest(session, identified.projection_uuid)
    session.execute(
        delete(MechanicalSpanORM).where(
            MechanicalSpanORM.projection_uuid == identified.projection_uuid,
            MechanicalSpanORM.leaf_id == "leaf-support",
        )
    )
    session.flush()
    assert verify_reconstruction(session, identified) != ()
    assert compute_persisted_state_digest(session, identified.projection_uuid) != before


def test_omitted_provenance_row_is_detected(session: Session) -> None:
    identified = _persist(session)
    session.execute(
        delete(MechanicalProvenanceORM).where(
            MechanicalProvenanceORM.projection_uuid == identified.projection_uuid
        )
    )
    session.flush()
    assert verify_reconstruction(session, identified) != ()


def test_tampered_fact_payload_is_detected(session: Session) -> None:
    identified = _persist(session)
    row = session.execute(
        select(MechanicalFactORM).where(
            MechanicalFactORM.projection_uuid == identified.projection_uuid
        )
    ).scalar_one()
    row.payload = {**row.payload, "level": 1}
    session.flush()
    findings = verify_reconstruction(session, identified)
    assert any("derives" in f for f in findings)


def test_corrupted_derived_record_id_is_detected(session: Session) -> None:
    # Every semantic value survives; only the stored identity is wrong. The
    # payload digest alone would miss this, which is why the digest and the
    # verification both cover persisted subidentities.
    identified = _persist(session)
    row = session.execute(
        select(MechanicalRecordORM).where(
            MechanicalRecordORM.projection_uuid == identified.projection_uuid,
            MechanicalRecordORM.semantic_key == SPELL_KEY,
        )
    ).scalar_one()
    before = compute_persisted_state_digest(session, identified.projection_uuid)
    row.record_id = "00000000-0000-0000-0000-000000000000"
    session.flush()
    findings = verify_reconstruction(session, identified)
    assert any("persisted id" in f for f in findings)
    assert compute_persisted_state_digest(session, identified.projection_uuid) != before


def test_missing_projection_raises(session: Session) -> None:
    with pytest.raises(ProjectionNotPersistedError):
        reconstruct_candidate(session, "no-such-projection")


def test_delete_removes_every_scoped_row(session: Session) -> None:
    identified = _persist(session)
    delete_projection(session, identified.projection_uuid)
    for model in (MechanicalSpanORM, MechanicalRecordORM, MechanicalFactORM):
        remaining = (
            session.execute(
                select(model).where(
                    model.projection_uuid == identified.projection_uuid  # type: ignore[attr-defined]
                )
            )
            .scalars()
            .all()
        )
        assert remaining == []


def test_two_projections_over_one_release_coexist(session: Session) -> None:
    first = _persist(session)
    other = identify_projection(build_candidate(references=()))
    second = identify_projection(
        build_candidate(provenance=build_candidate().representation.provenance[:2])
    )
    assert other.projection_uuid == first.projection_uuid  # references were empty
    persist_draft(session, second, now=NOW)
    assert second.projection_uuid != first.projection_uuid
    assert verify_reconstruction(session, first) == ()
