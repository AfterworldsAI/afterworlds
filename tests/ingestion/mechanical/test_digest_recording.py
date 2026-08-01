"""The recording seam derives its own proof — CRD Issue 5d, review round 2.

``record_persisted_state_digest`` used to accept whatever digest a caller
handed it and freeze it under an exactly-once guard. A stale value, a value
computed before an intervening mutation, or another projection's value could
therefore become the immutable proof — and the guard then prevented correcting
it. The seam now computes the digest from the projection's own reconstructed
state inside the recording transaction.
"""

from __future__ import annotations

import inspect
from collections.abc import Iterator

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from afterworlds.ingestion.mechanical.persistence import (
    compute_persisted_state_digest,
    persist_draft,
    record_persisted_state_digest,
)
from afterworlds.ingestion.mechanical.projection import identify_projection
from afterworlds.ingestion.mechanical.raw_state import (
    PersistedStateReconstructionError,
)
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.persistence.orm.base import Base
from afterworlds.persistence.orm.corpus import CorpusReleaseORM
from afterworlds.persistence.orm.mechanical import (
    MechanicalAcceptanceORM,
    MechanicalFactORM,
    MechanicalProjectionORM,
)
from afterworlds.persistence.orm.rules_package import RulesPackageORM
from tests.ingestion.mechanical.conftest import (
    batch_accepted_ledger,
    build_candidate,
    build_representation,
)

NOW = "2026-07-31T00:00:00Z"


@pytest.fixture()
def session(tmp_path) -> Iterator[Session]:  # type: ignore[no-untyped-def]
    engine = create_engine(f"sqlite:///{tmp_path / 'digest.db'}")
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


def _header(session: Session, uuid_: str) -> MechanicalProjectionORM:
    return session.execute(
        select(MechanicalProjectionORM).where(
            MechanicalProjectionORM.projection_uuid == uuid_
        )
    ).scalar_one()


def test_recorded_value_equals_a_fresh_digest_of_current_state(
    session: Session,
) -> None:
    identified = _persist(session)
    recorded = record_persisted_state_digest(session, identified.projection_uuid)
    assert recorded == compute_persisted_state_digest(
        session, identified.projection_uuid
    )
    assert (
        _header(session, identified.projection_uuid).persisted_state_digest == recorded
    )


def test_the_seam_takes_no_caller_digest(session: Session) -> None:
    # The false-authority input is gone rather than merely discouraged.
    parameters = inspect.signature(record_persisted_state_digest).parameters
    assert list(parameters) == ["session", "projection_uuid"]
    identified = _persist(session)
    with pytest.raises(TypeError):
        record_persisted_state_digest(  # type: ignore[call-arg]
            session, identified.projection_uuid, "f" * 64
        )


def test_a_digest_computed_before_a_mutation_is_not_what_gets_recorded(
    session: Session,
) -> None:
    identified = _persist(session, ledger=batch_accepted_ledger())
    stale = compute_persisted_state_digest(session, identified.projection_uuid)

    # An acceptance row is edited between computing and recording — exactly the
    # window in which a caller-supplied value would freeze a false proof.
    row = session.execute(select(MechanicalAcceptanceORM)).scalars().first()
    assert row is not None
    row.reviewer = "someone-else"
    session.flush()

    recorded = record_persisted_state_digest(session, identified.projection_uuid)
    assert recorded != stale
    assert recorded == compute_persisted_state_digest(
        session, identified.projection_uuid
    )


def test_another_projections_digest_cannot_be_recorded(session: Session) -> None:
    first = _persist(session)
    second = _persist(session, provenance=build_representation().provenance[:2])
    assert first.projection_uuid != second.projection_uuid

    other_digest = compute_persisted_state_digest(session, second.projection_uuid)
    recorded = record_persisted_state_digest(session, first.projection_uuid)
    assert recorded != other_digest
    assert recorded == compute_persisted_state_digest(session, first.projection_uuid)


def test_reconstruction_failure_leaves_the_digest_unrecorded(
    session: Session,
) -> None:
    identified = _persist(session)
    row = session.execute(select(MechanicalFactORM)).scalars().one()
    row.family = "progression_entry"  # disagrees with its own payload
    session.flush()

    with pytest.raises(PersistedStateReconstructionError):
        record_persisted_state_digest(session, identified.projection_uuid)
    assert _header(session, identified.projection_uuid).persisted_state_digest is None


def test_mistyped_persisted_fact_blocks_recording(session: Session) -> None:
    identified = _persist(session)
    row = session.execute(select(MechanicalFactORM)).scalars().one()
    row.payload = {**row.payload, "ritual": "false"}
    session.flush()

    with pytest.raises(PersistedStateReconstructionError):
        record_persisted_state_digest(session, identified.projection_uuid)
    assert _header(session, identified.projection_uuid).persisted_state_digest is None


def test_second_recording_attempt_is_rejected(session: Session) -> None:
    identified = _persist(session)
    first = record_persisted_state_digest(session, identified.projection_uuid)
    with pytest.raises(ValueError, match="already recorded"):
        record_persisted_state_digest(session, identified.projection_uuid)
    assert _header(session, identified.projection_uuid).persisted_state_digest == first


def test_honest_recording_returns_and_stores_one_value(session: Session) -> None:
    identified = _persist(session, ledger=batch_accepted_ledger())
    recorded = record_persisted_state_digest(session, identified.projection_uuid)
    stored = _header(session, identified.projection_uuid).persisted_state_digest
    assert recorded == stored
    assert recorded
