"""Publication under genuine concurrency — CRD Issue 5d, PR #141 R3.

The activation key makes split authority impossible, but "impossible" is only
half a contract: the *losing* publisher has to receive a typed outcome, not a
driver exception. Sequential tests cannot show that, because the losing write
never happens — one call completes before the next begins.

So these run two workers on separate sessions and separate connections against a
**file-backed** SQLite database, and coordinate them at the one instant that
matters: both must be past the pre-insert active-row observation before either
writes. That is arranged by wrapping that observation with a barrier, so the
race is structural rather than a hope about timing.

``busy_timeout`` is set to 100 ms deliberately. At SQLite's default a losing
writer blocks long enough that the winner commits and the loser succeeds
serially — which looks like a pass while never exercising the contention path
at all. At zero the lock error is immediate but the winner can lose too. 100 ms
is short enough to surface contention and long enough that one worker reliably
wins.
"""

from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from afterworlds.ingestion.mechanical import publication
from afterworlds.ingestion.mechanical.oracle import AcceptedOracle, load_oracle
from afterworlds.ingestion.mechanical.persistence import (
    persist_draft,
    record_persisted_state_digest,
)
from afterworlds.ingestion.mechanical.projection import (
    ProjectionCandidate,
    identify_projection,
)
from afterworlds.ingestion.mechanical.publication import (
    PublicationOutcome,
    _publish_projection,
)
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.persistence.orm.base import Base
from afterworlds.persistence.orm.mechanical import (
    MechanicalActiveProjectionORM,
    MechanicalProjectionORM,
)
from tests.ingestion.mechanical.conftest import (
    BOUNDED_ORACLE_PATH,
    NOW,
    _seed_bound_release,
    build_candidate,
)
from tests.ingestion.mechanical.test_publication import a_different_projection

LATER = "2026-08-02T00:00:00Z"

#: How many times each race runs. A single green pass proves nothing about a
#: schedule-dependent defect; ten makes an interleaving that only sometimes
#: loses show up as a failure rather than as luck.
REPEATS = range(10)


@pytest.fixture()
def factory(tmp_path: Path) -> sessionmaker[Session]:
    """A file-backed database seeded with the bound 5c release.

    File-backed, not ``sqlite://``: an in-memory database is per-connection, so
    two workers would silently operate on two different databases and every race
    would "pass".
    """
    engine = create_engine(
        f"sqlite:///{tmp_path / 'race.db'}", connect_args={"timeout": 0.1}
    )
    Base.metadata.create_all(engine)
    made = create_session_factory(engine)
    with made() as session:
        _seed_bound_release(session)
        session.commit()
    return made


def _persist(factory: sessionmaker[Session], candidate: ProjectionCandidate) -> str:
    identified = identify_projection(candidate)
    with factory() as session:
        persist_draft(session, identified, now=NOW)
        record_persisted_state_digest(session, identified.projection_uuid)
        session.commit()
    return identified.projection_uuid


def _race(
    factory: sessionmaker[Session],
    monkeypatch: pytest.MonkeyPatch,
    jobs: list[tuple[str, AcceptedOracle]],
) -> list[Any]:
    """Run *jobs* concurrently, each on its own session, past a shared barrier.

    The barrier sits on the **pre-insert observation** — the active-row read
    every publisher performs before deciding to write — so both workers have
    provably seen the same "no incumbent" state before either writes anything.
    That is the instant the contract is about.

    It deliberately does *not* sit around activation. SQLite has one writer, so
    a worker parked mid-transaction holds the write lock; the other would fail
    its header flush, reattempt, fail again while the first is still parked, and
    both would deadlock on a barrier that can never fill. Blocking on a read
    keeps the race genuine without inventing a lock ordering the production path
    does not have.

    Each worker trips the barrier at most once, so the bounded settlement wait
    and one post-settlement re-entry run freely instead of waiting on a spent
    barrier.
    """
    barrier = threading.Barrier(len(jobs), timeout=10)
    original = publication._active_row
    tripped: set[int] = set()
    guard = threading.Lock()

    def observe(session: Session, package_uuid: str) -> Any:
        row = original(session, package_uuid)
        with guard:
            first = threading.get_ident() not in tripped
            tripped.add(threading.get_ident())
        if first:
            barrier.wait()
        return row

    monkeypatch.setattr(publication, "_active_row", observe)

    def work(job: tuple[str, AcceptedOracle]) -> Any:
        uuid, oracle = job
        with factory() as session:
            try:
                return _publish_projection(session, uuid, oracle, now=NOW)
            except BaseException as exc:  # returned, so the test can assert on it
                return exc

    with ThreadPoolExecutor(max_workers=len(jobs)) as pool:
        return list(pool.map(work, jobs))


def _active(factory: sessionmaker[Session]) -> list[MechanicalActiveProjectionORM]:
    with factory() as session:
        return list(
            session.execute(select(MechanicalActiveProjectionORM)).scalars().all()
        )


def _header(factory: sessionmaker[Session], uuid: str) -> MechanicalProjectionORM:
    with factory() as session:
        return session.execute(
            select(MechanicalProjectionORM).where(
                MechanicalProjectionORM.projection_uuid == uuid
            )
        ).scalar_one()


@pytest.fixture()
def committed() -> AcceptedOracle:
    return load_oracle(BOUNDED_ORACLE_PATH)


@pytest.mark.parametrize("attempt", REPEATS)
def test_concurrent_identical_publication_is_published_then_already_published(
    factory: sessionmaker[Session],
    committed: AcceptedOracle,
    monkeypatch: pytest.MonkeyPatch,
    attempt: int,
) -> None:
    """Two workers, one content-derived identity, one active row.

    Identical builds are the *same* projection UUID, so this is the idempotence
    promise under contention: exactly one worker performs the publication and
    the other is told it already happened — after re-running the full proof, not
    by reading a status column.
    """
    uuid = _persist(factory, build_candidate())
    results = _race(factory, monkeypatch, [(uuid, committed), (uuid, committed)])

    for result in results:
        assert not isinstance(result, BaseException), result
    outcomes = sorted(r.outcome.value for r in results)
    assert outcomes == ["already_published", "published"]

    rows = _active(factory)
    assert len(rows) == 1
    assert rows[0].projection_uuid == uuid
    assert _header(factory, uuid).publication_status == "published"


@pytest.mark.parametrize("attempt", REPEATS)
def test_concurrent_competing_publication_leaves_the_loser_a_draft(
    factory: sessionmaker[Session],
    committed: AcceptedOracle,
    monkeypatch: pytest.MonkeyPatch,
    attempt: int,
) -> None:
    """Two different projections for one package: one wins, one is told so.

    Both pass their own gate — the challenger has its own accepted oracle — so
    nothing about either is wrong. The package can only have one active
    authority, and the loser must come back as ``ACTIVE_CONFLICT`` holding no
    publication evidence at all.
    """
    incumbent = _persist(factory, build_candidate())
    with factory() as session:
        challenger, challenger_oracle = a_different_projection(session, committed)
        session.commit()

    results = _race(
        factory,
        monkeypatch,
        [(incumbent, committed), (challenger, challenger_oracle)],
    )
    for result in results:
        assert not isinstance(result, BaseException), result
    by_uuid = {r.projection_uuid: r.outcome for r in results}

    rows = _active(factory)
    assert len(rows) == 1
    winner = rows[0].projection_uuid
    loser = challenger if winner == incumbent else incumbent

    assert by_uuid[winner] is PublicationOutcome.PUBLISHED
    assert by_uuid[loser] is PublicationOutcome.ACTIVE_CONFLICT

    losing_header = _header(factory, loser)
    assert losing_header.publication_status == "draft"
    assert losing_header.evidence_report_hash is None
    assert losing_header.report_payload is None
    assert losing_header.oracle_identity is None
    assert losing_header.published_at is None


def test_settlement_waits_until_a_winning_activation_is_visible(
    factory: sessionmaker[Session],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An immediate empty read is not evidence that the winner disappeared."""
    probes: list[int] = []

    def delayed_visibility(session: Session, package_uuid: str) -> Any:
        probes.append(1)
        return None if len(probes) < 3 else object()

    monkeypatch.setattr(publication, "_active_row", delayed_visibility)
    monkeypatch.setattr(publication, "_ACTIVATION_SETTLEMENT_POLL_SECONDS", 0.0)
    with factory() as session:
        assert publication._wait_for_activation_settlement(session, "package")

    assert len(probes) == 3


def test_an_unrelated_integrity_error_still_propagates(
    factory: sessionmaker[Session],
    committed: AcceptedOracle,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Only activation contention is a race; everything else is a defect.

    A blanket ``except IntegrityError`` would relabel an unrelated constraint
    violation as concurrency and quietly retry it, so this injects one that does
    not name the activation table and requires it to reach the caller.
    """
    uuid = _persist(factory, build_candidate())
    boom = IntegrityError(
        "INSERT INTO rp_mech_records ...",
        {},
        Exception("UNIQUE constraint failed: rp_mech_records.record_id"),
    )

    def explode(session: Session, projection_uuid: str, *, now: str) -> Any:
        raise boom

    monkeypatch.setattr(publication, "_activate_projection", explode)
    with factory() as session, pytest.raises(IntegrityError):
        _publish_projection(session, uuid, committed, now=NOW)

    assert _active(factory) == []
    assert _header(factory, uuid).publication_status == "draft"


def test_a_recurring_race_is_not_retried_forever(
    factory: sessionmaker[Session],
    committed: AcceptedOracle,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A missing winning activation cannot leave publication waiting forever.

    Activation is made to fail with a genuine activation-table conflict while
    no winner ever commits. The bounded settlement window expires and the
    original error propagates rather than spinning or manufacturing an outcome.
    """
    uuid = _persist(factory, build_candidate())
    calls: list[int] = []
    conflict = IntegrityError(
        "INSERT INTO rp_mech_active_projections ...",
        {},
        Exception("UNIQUE constraint failed: rp_mech_active_projections.package_uuid"),
    )

    def always_conflict(session: Session, projection_uuid: str, *, now: str) -> Any:
        calls.append(1)
        raise conflict

    monkeypatch.setattr(publication, "_activate_projection", always_conflict)
    monkeypatch.setattr(publication, "_ACTIVATION_SETTLEMENT_TIMEOUT_SECONDS", 0.0)
    with factory() as session, pytest.raises(IntegrityError):
        _publish_projection(session, uuid, committed, now=NOW)

    assert len(calls) == 1, "no retry is allowed before a winning row is visible"
    assert _active(factory) == []
    assert _header(factory, uuid).publication_status == "draft"
