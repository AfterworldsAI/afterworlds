"""Retained-evidence persistence closure and transactional idempotency.

Codex review round 3. Two symptoms, one architectural family: **retained
evidence must be durable against every non-contractual path, and creating it
must be safe when two sessions do it at once.**

* A live scope association was directly deletable. Replay failed closed
  afterwards, but the evidence proving which package a retained version belonged
  to was gone and could not be reconstructed.
* ``retain_override_set`` established idempotency by querying for absence and
  inserting into the gap. Two sessions both observe absence, both insert, and the
  loser takes a uniqueness violation, a trigger abort, or a lock error for doing
  exactly what it was asked to.

The fix is one design, not two patches: content-aware ``BEFORE INSERT`` guards
plus ``INSERT ... ON CONFLICT DO NOTHING``, under one savepoint. Neither half is
safe alone — an existence-based guard aborts the upsert before conflict
resolution is reached, which is verified below rather than assumed.

Concurrency here is deterministic. Two real connections are driven through
``threading.Barrier`` so both are provably past the point where the old
query-then-insert had already decided the row was absent; there are no sleeps and
no timing assumptions.

Round 4 added the transactionality half of the same family. The savepoint is
only a *nested* savepoint if SQLite has issued a physical ``BEGIN``; after a
read-only prelude it had not, so releasing the savepoint committed the retained
rows out of the caller's control. Those controls assert from an independent
session, since that is the only way to distinguish "committed" from "pending in
this session's transaction".
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from typing import Any

import pytest
from sqlalchemy import Engine, delete, func, select, text
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session

from afterworlds.ingestion.mechanical.persistence import ProjectionNotPersistedError
from afterworlds.models.enums import OverrideOperationEnum
from afterworlds.persistence.database import create_session_factory
from afterworlds.persistence.orm.rules_authority import (
    MechanicalOverrideORM,
    OverrideSetEntryORM,
    OverrideSetScopeORM,
    OverrideSetVersionORM,
)
from afterworlds.persistence.orm.rules_package import RulesPackageORM
from afterworlds.services.rules_authority import (
    OverrideSetRetentionError,
    RulesAuthorityService,
    collect_current_override_state,
    retain_override_set,
)
from tests.services.rules_authority.conftest import (
    DESCRIPTOR_FACT_TARGET,
    NOW,
    RuntimeFixture,
    author_override,
    replace_fact_payload,
)

#: Every trigger migration 0024 installs on the retained-evidence tables.
EXPECTED_TRIGGERS = (
    "prevent_rp_override_set_versions_update",
    "prevent_rp_override_set_versions_delete",
    "prevent_rp_override_set_versions_reinsert",
    "prevent_rp_override_set_entries_update",
    "prevent_rp_override_set_entries_delete",
    "prevent_rp_override_set_entries_reinsert",
    "prevent_rp_override_set_scopes_update",
    "prevent_rp_override_set_scopes_delete",
    "seal_rp_override_set_entries",
)


def service(session: Session) -> RulesAuthorityService:
    return RulesAuthorityService(session, now=NOW)


# ---------------------------------------------------------------------------
# Deterministic concurrency harness
# ---------------------------------------------------------------------------


def _run_concurrently(
    engine: Engine, work: list[Callable[[Session], Any]]
) -> list[Any]:
    """Run *work* on one fresh session each, synchronised by a barrier.

    Each worker opens its own session, does its reads, waits at the barrier, and
    only then writes. That makes the interleaving the defect needs — every worker
    past its existence check before any worker inserts — a property of the test
    rather than of the scheduler. Results are returned in submission order;
    exceptions are returned rather than raised so a caller can assert on them.
    """
    factory = create_session_factory(engine)
    results: list[Any] = [None] * len(work)

    def _worker(index: int) -> None:
        with factory() as session:
            try:
                results[index] = work[index](session)
                session.commit()
            except Exception as exc:  # noqa: BLE001 - returned for assertion
                session.rollback()
                results[index] = exc

    threads = [
        threading.Thread(target=_worker, args=(i,), name=f"retain-{i}")
        for i in range(len(work))
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)
    assert not any(t.is_alive() for t in threads), "concurrency harness deadlocked"
    return results


def _retain_after_barrier(
    barrier: threading.Barrier, package_uuid: str, release_version: str
) -> Callable[[Session], str]:
    """Collect state, wait for every worker, then retain.

    The read happens before the barrier and the write after it, so both workers
    have provably observed the same absent state before either writes — the exact
    interleaving the removed query-then-insert could not survive.
    """

    def _work(session: Session) -> str:
        state = collect_current_override_state(session, package_uuid, release_version)
        barrier.wait(timeout=30)
        return retain_override_set(session, state, now=NOW)

    return _work


# ---------------------------------------------------------------------------
# 1. Concurrent first retention of the same version and the same scope
# ---------------------------------------------------------------------------


def test_concurrent_first_retention_of_identical_content_and_scope(
    runtime: RuntimeFixture,
) -> None:
    """Both callers converge on one valid result; neither sees a race error."""
    author_override(
        runtime.session,
        override_id="ov-concurrent",
        target=DESCRIPTOR_FACT_TARGET,
        operation=OverrideOperationEnum.REPLACE,
        payload=replace_fact_payload(),
    )
    runtime.session.commit()

    package = str(runtime.package_uuid)
    release = runtime.release_version
    barrier = threading.Barrier(2)
    results = _run_concurrently(
        runtime.engine,
        [_retain_after_barrier(barrier, package, release) for _ in range(2)],
    )

    for result in results:
        assert not isinstance(result, Exception), f"race surfaced as failure: {result}"
    assert results[0] == results[1]

    identity = results[0]
    runtime.session.rollback()
    assert _count(runtime.session, OverrideSetVersionORM, identity) == 1
    assert _count(runtime.session, OverrideSetScopeORM, identity) == 1
    assert _count(runtime.session, OverrideSetEntryORM, identity) == 1
    # And the converged evidence is usable, not merely present.
    binding = _binding_for(runtime, identity)
    assert service(runtime.session).replay(binding).binding == binding


def _count(session: Session, model: type, identity: str) -> int:
    return (
        session.execute(
            select(func.count())
            .select_from(model)
            .where(model.override_set_uuid == identity)  # type: ignore[attr-defined]
        ).scalar_one()
        or 0
    )


def _binding_for(runtime: RuntimeFixture, identity: str):  # type: ignore[no-untyped-def]
    from uuid import UUID

    from afterworlds.models.rules_package import RulesPackageBinding

    return RulesPackageBinding(
        package_uuid=runtime.package_uuid,
        release_version=runtime.release_version,
        mechanical_projection_uuid=runtime.projection_uuid,
        override_set_uuid=UUID(identity),
    )


# ---------------------------------------------------------------------------
# 2. Concurrent retention of shared content under different scopes
# ---------------------------------------------------------------------------


def test_concurrent_retention_of_shared_content_under_different_scopes(
    runtime: RuntimeFixture,
) -> None:
    """One immutable version, both valid associations.

    Both packages have no overrides, so both resolve the same empty override-set
    identity — the sharing case that makes the association table necessary in the
    first place.
    """
    runtime.session.commit()
    barrier = threading.Barrier(2)
    results = _run_concurrently(
        runtime.engine,
        [
            _retain_after_barrier(
                barrier, str(runtime.package_uuid), runtime.release_version
            ),
            _retain_after_barrier(
                barrier,
                str(runtime.rival_package_uuid),
                runtime.rival_release_version,
            ),
        ],
    )

    for result in results:
        assert not isinstance(result, Exception), f"race surfaced as failure: {result}"
    assert results[0] == results[1], "shared content must converge on one identity"

    identity = results[0]
    runtime.session.rollback()
    assert _count(runtime.session, OverrideSetVersionORM, identity) == 1
    scopes = {
        (row.package_uuid, row.release_version)
        for row in runtime.session.execute(
            select(OverrideSetScopeORM).where(
                OverrideSetScopeORM.override_set_uuid == identity
            )
        )
        .scalars()
        .all()
    }
    assert scopes == {
        (str(runtime.package_uuid), runtime.release_version),
        (str(runtime.rival_package_uuid), runtime.rival_release_version),
    }


def test_repeated_sequential_retention_stays_idempotent(
    runtime: RuntimeFixture,
) -> None:
    """The ordinary path must survive the guards that make the race safe.

    Binding resolution retains on every read, so a guard that refused the second
    identical write would break every second resolution. Asserted against the
    row counts, not just the absence of an exception.
    """
    author_override(
        runtime.session,
        override_id="ov-repeat",
        target=DESCRIPTOR_FACT_TARGET,
        operation=OverrideOperationEnum.REPLACE,
        payload=replace_fact_payload(),
    )
    identities = {
        service(runtime.session)
        .resolve(package_uuid=runtime.package_uuid)
        .binding.override_set_uuid  # type: ignore[union-attr]
        for _ in range(4)
    }
    assert len(identities) == 1
    identity = str(next(iter(identities)))
    assert _count(runtime.session, OverrideSetVersionORM, identity) == 1
    assert _count(runtime.session, OverrideSetScopeORM, identity) == 1
    assert _count(runtime.session, OverrideSetEntryORM, identity) == 1


# ---------------------------------------------------------------------------
# 3. A live scope association is not directly deletable
# ---------------------------------------------------------------------------


def test_direct_scope_deletion_is_rejected_while_the_package_lives(
    runtime: RuntimeFixture,
) -> None:
    """The evidence a binding depends on cannot be destroyed out from under it."""
    service(runtime.session).resolve(package_uuid=runtime.package_uuid)
    with pytest.raises((IntegrityError, OperationalError), match="append-only"):
        runtime.session.execute(delete(OverrideSetScopeORM))
    runtime.session.rollback()


def test_direct_scope_deletion_by_raw_sql_is_rejected(
    runtime: RuntimeFixture,
) -> None:
    """Guarded at the database, so an ORM-free path is refused too."""
    service(runtime.session).resolve(package_uuid=runtime.package_uuid)
    with pytest.raises((IntegrityError, OperationalError), match="append-only"):
        runtime.session.execute(text("DELETE FROM rp_override_set_scopes"))
    runtime.session.rollback()


def test_scope_mutation_is_rejected(runtime: RuntimeFixture) -> None:
    """Relabelling an association onto another package is a rewrite, not a move."""
    service(runtime.session).resolve(package_uuid=runtime.package_uuid)
    with pytest.raises((IntegrityError, OperationalError), match="append-only"):
        runtime.session.execute(
            text("UPDATE rp_override_set_scopes SET package_uuid = 'elsewhere'")
        )
    runtime.session.rollback()


# ---------------------------------------------------------------------------
# 4. Intentional package deletion keeps its contractual cascade
# ---------------------------------------------------------------------------


def test_package_deletion_still_cascades_its_own_association(
    runtime: RuntimeFixture,
) -> None:
    """The one contractual way an association goes away, still working.

    SQLite removes the parent row before cascading, so the delete guard's
    condition is already false by the time the child trigger fires. That is what
    lets the guard block a direct delete without also blocking this.
    """
    primary = service(runtime.session).resolve(package_uuid=runtime.package_uuid)
    rival = service(runtime.session).resolve(package_uuid=runtime.rival_package_uuid)
    assert primary.binding is not None and rival.binding is not None
    identity = str(primary.binding.override_set_uuid)
    assert _count(runtime.session, OverrideSetScopeORM, identity) == 2

    runtime.session.execute(
        delete(RulesPackageORM).where(
            RulesPackageORM.rules_package_id == str(runtime.rival_package_uuid)
        )
    )
    runtime.session.flush()

    # Only the deleted package's association went; the shared version and the
    # surviving package's association are untouched, and it still replays.
    assert _count(runtime.session, OverrideSetVersionORM, identity) == 1
    remaining = {
        row.package_uuid
        for row in runtime.session.execute(
            select(OverrideSetScopeORM).where(
                OverrideSetScopeORM.override_set_uuid == identity
            )
        )
        .scalars()
        .all()
    }
    assert remaining == {str(runtime.package_uuid)}
    assert service(runtime.session).replay(primary.binding).binding == primary.binding


def test_replay_for_a_deleted_package_fails_closed(
    runtime: RuntimeFixture,
) -> None:
    """Its own bindings die with it — reported, never replayed unscoped.

    Deleting a package cascades to its corpus release and therefore to its
    mechanical projection as well, so replay refuses at whichever proof it
    reaches first. The contract asserted here is that it *refuses*, never that a
    particular layer is the one to notice: both are typed defects, and neither
    returns authority.
    """
    rival = service(runtime.session).resolve(package_uuid=runtime.rival_package_uuid)
    assert rival.binding is not None
    runtime.session.execute(
        delete(RulesPackageORM).where(
            RulesPackageORM.rules_package_id == str(runtime.rival_package_uuid)
        )
    )
    runtime.session.flush()

    with pytest.raises((OverrideSetRetentionError, ProjectionNotPersistedError)):
        service(runtime.session).replay(rival.binding)


# ---------------------------------------------------------------------------
# 5. Partial failure rolls the whole retention unit back
# ---------------------------------------------------------------------------


def test_a_failure_part_way_through_retention_leaves_nothing_behind(
    runtime: RuntimeFixture,
) -> None:
    """No orphan snapshot, and the caller's transaction survives.

    The scope insert is made to fail by pointing the state at a package that does
    not exist, so the foreign key rejects it *after* the version and its entries
    have already been written inside the unit. Everything must unwind together.
    """
    from dataclasses import replace as dc_replace

    author_override(
        runtime.session,
        override_id="ov-partial",
        target=DESCRIPTOR_FACT_TARGET,
        operation=OverrideOperationEnum.REPLACE,
        payload=replace_fact_payload(),
    )
    state = collect_current_override_state(
        runtime.session, str(runtime.package_uuid), runtime.release_version
    )
    identity = state.override_set_uuid
    doomed = dc_replace(state, package_uuid="00000000-0000-0000-0000-000000000000")

    with pytest.raises((IntegrityError, OperationalError)):
        retain_override_set(runtime.session, doomed, now=NOW)

    # No full rollback here on purpose: the savepoint must have unwound the
    # retention unit *without* discarding the caller's transaction, so the
    # override authored above is still pending and the counts below are read
    # from a live session.
    assert _count(runtime.session, OverrideSetVersionORM, identity) == 0
    assert _count(runtime.session, OverrideSetEntryORM, identity) == 0
    assert _count(runtime.session, OverrideSetScopeORM, identity) == 0

    # The session is still usable, and a correct retention afterwards succeeds.
    good = collect_current_override_state(
        runtime.session, str(runtime.package_uuid), runtime.release_version
    )
    assert retain_override_set(runtime.session, good, now=NOW) == identity
    assert _count(runtime.session, OverrideSetVersionORM, identity) == 1
    assert _count(runtime.session, OverrideSetScopeORM, identity) == 1


# ---------------------------------------------------------------------------
# 6. Replay accepts only properly scoped retained evidence
# ---------------------------------------------------------------------------


def test_replay_accepts_only_properly_scoped_evidence(
    runtime: RuntimeFixture,
) -> None:
    """Cross-package and cross-release refused; the correct scope accepted."""
    from afterworlds.models.rules_package import RulesPackageBinding
    from afterworlds.services.rules_authority import load_override_set_version

    author_override(
        runtime.session,
        override_id="ov-scope-check",
        target=DESCRIPTOR_FACT_TARGET,
        operation=OverrideOperationEnum.REPLACE,
        payload=replace_fact_payload(),
    )
    primary = service(runtime.session).resolve(package_uuid=runtime.package_uuid)
    assert primary.binding is not None
    identity = str(primary.binding.override_set_uuid)

    # The scope it was retained under: accepted.
    assert service(runtime.session).replay(primary.binding).binding == primary.binding

    # Another package, carrying its own genuine projection: refused. Reachable
    # end to end because both projections share semantic keys, so the override
    # would otherwise find a live target and replay with the wrong provenance.
    cross_package = RulesPackageBinding(
        package_uuid=runtime.rival_package_uuid,
        release_version=runtime.rival_release_version,
        mechanical_projection_uuid=runtime.rival_projection_uuid,
        override_set_uuid=primary.binding.override_set_uuid,
    )
    with pytest.raises(OverrideSetRetentionError, match="was never retained for"):
        service(runtime.session).replay(cross_package)

    # The right package under a release it was never retained for: refused.
    # Asserted at the retention seam, because a binding naming a foreign release
    # is stopped earlier still by the projection coherence check.
    with pytest.raises(OverrideSetRetentionError, match="was never retained for"):
        load_override_set_version(
            runtime.session,
            identity,
            package_uuid=str(runtime.package_uuid),
            release_version="5.2.1-never-retained",
        )


# ---------------------------------------------------------------------------
# The guard shape and the insert shape are one design
# ---------------------------------------------------------------------------


def test_an_identical_reinsert_is_a_no_op_and_a_differing_one_is_refused(
    runtime: RuntimeFixture,
) -> None:
    """The property the whole concurrency fix rests on, asserted directly.

    An existence-based guard would abort both of these. Only a content-aware one
    distinguishes a benign repeat from a rewrite, which is what lets
    ``ON CONFLICT DO NOTHING`` carry the idempotency.
    """
    service(runtime.session).resolve(package_uuid=runtime.package_uuid)
    row = runtime.session.execute(select(OverrideSetVersionORM)).scalars().first()
    assert row is not None
    identity, count = row.override_set_uuid, row.entry_count

    runtime.session.execute(
        text(
            "INSERT INTO rp_override_set_versions (override_set_uuid, entry_count,"
            " recorded_at) VALUES (:i, :n, 'later') ON CONFLICT DO NOTHING"
        ),
        {"i": identity, "n": count},
    )
    runtime.session.flush()
    assert _count(runtime.session, OverrideSetVersionORM, identity) == 1

    with pytest.raises((IntegrityError, OperationalError), match="append-only"):
        runtime.session.execute(
            text(
                "INSERT INTO rp_override_set_versions (override_set_uuid, entry_count,"
                " recorded_at) VALUES (:i, :n, 'later') ON CONFLICT DO NOTHING"
            ),
            {"i": identity, "n": count + 1},
        )
    runtime.session.rollback()


# ---------------------------------------------------------------------------
# Retention participates in the caller's *physical* transaction
# ---------------------------------------------------------------------------
#
# Codex review round 4. The savepoint above is only a nested savepoint if SQLite
# has actually issued ``BEGIN``. Under ``sqlite3``'s legacy transaction control
# a session that has only read is still in autocommit, so the savepoint was the
# outermost one and releasing it committed the retained rows — a caller's later
# rollback could not take them back. These controls assert the boundary from a
# separate session, because rows already committed are visible from anywhere and
# rows merely pending in another session's transaction are visible from nowhere:
# a same-session assertion cannot tell the two apart.


def _retained_rows_elsewhere(engine: Engine, identity: str) -> tuple[int, int, int]:
    """Count retained rows for *identity* on a genuinely independent session."""
    with create_session_factory(engine)() as other:
        return (
            _count(other, OverrideSetVersionORM, identity),
            _count(other, OverrideSetEntryORM, identity),
            _count(other, OverrideSetScopeORM, identity),
        )


def _authored_state(session: Session, runtime: RuntimeFixture, override_id: str):  # type: ignore[no-untyped-def]
    """Author one override on *session* and collect the state it implies."""
    author_override(
        session,
        override_id=override_id,
        target=DESCRIPTOR_FACT_TARGET,
        operation=OverrideOperationEnum.REPLACE,
        payload=replace_fact_payload(),
    )
    return collect_current_override_state(
        session, str(runtime.package_uuid), runtime.release_version
    )


def test_retention_after_a_read_only_prelude_rolls_back_with_the_caller(
    runtime: RuntimeFixture,
) -> None:
    """The reported defect, asserted end to end on the ordinary path.

    No DML precedes the resolution, so before this fix SQLite had issued no
    ``BEGIN``, the retention savepoint was the outermost one, and releasing it
    committed. The rollback below is the caller changing its mind; nothing
    retained may survive it.
    """
    author_override(
        runtime.session,
        override_id="ov-txn",
        target=DESCRIPTOR_FACT_TARGET,
        operation=OverrideOperationEnum.REPLACE,
        payload=replace_fact_payload(),
    )
    runtime.session.commit()

    with create_session_factory(runtime.engine)() as session:
        # A read-only prelude, exactly as binding resolution performs it.
        result = service(session).resolve(package_uuid=runtime.package_uuid)
        assert result.binding is not None
        identity = str(result.binding.override_set_uuid)
        # Pending in this session, and nowhere else.
        assert _count(session, OverrideSetVersionORM, identity) == 1
        assert _retained_rows_elsewhere(runtime.engine, identity) == (0, 0, 0)
        session.rollback()

    assert _retained_rows_elsewhere(runtime.engine, identity) == (0, 0, 0)


def test_retention_rolls_back_when_later_work_in_an_explicit_block_raises(
    runtime: RuntimeFixture,
) -> None:
    """``with session.begin():`` must own the boundary, not the savepoint."""
    author_override(
        runtime.session,
        override_id="ov-txn-block",
        target=DESCRIPTOR_FACT_TARGET,
        operation=OverrideOperationEnum.REPLACE,
        payload=replace_fact_payload(),
    )
    runtime.session.commit()

    identity: str | None = None
    with (
        create_session_factory(runtime.engine)() as session,
        pytest.raises(RuntimeError, match="later work fails"),
        session.begin(),
    ):
        result = service(session).resolve(package_uuid=runtime.package_uuid)
        assert result.binding is not None
        identity = str(result.binding.override_set_uuid)
        raise RuntimeError("later work fails")

    assert identity is not None
    assert _retained_rows_elsewhere(runtime.engine, identity) == (0, 0, 0)


def test_retention_can_be_retried_and_committed_after_an_enclosing_rollback(
    runtime: RuntimeFixture,
) -> None:
    """A rolled-back retention is genuinely absent, not a poisoned identity."""
    author_override(
        runtime.session,
        override_id="ov-txn-retry",
        target=DESCRIPTOR_FACT_TARGET,
        operation=OverrideOperationEnum.REPLACE,
        payload=replace_fact_payload(),
    )
    runtime.session.commit()

    with create_session_factory(runtime.engine)() as session:
        first = service(session).resolve(package_uuid=runtime.package_uuid)
        assert first.binding is not None
        identity = str(first.binding.override_set_uuid)
        session.rollback()
    assert _retained_rows_elsewhere(runtime.engine, identity) == (0, 0, 0)

    with create_session_factory(runtime.engine)() as session:
        again = service(session).resolve(package_uuid=runtime.package_uuid)
        assert again.binding is not None
        assert str(again.binding.override_set_uuid) == identity
        session.commit()

    assert _retained_rows_elsewhere(runtime.engine, identity) == (1, 1, 1)

    # And the committed evidence replays, so the retry produced usable
    # provenance rather than merely the right number of rows.
    with create_session_factory(runtime.engine)() as session:
        binding = _binding_for(runtime, identity)
        assert service(session).replay(binding).binding == binding


def test_retention_does_not_commit_the_callers_earlier_work(
    runtime: RuntimeFixture,
) -> None:
    """Unrelated pending work must not be made durable by a retention.

    Stated as an invariant rather than as a reproduction: authoring an override
    is itself DML, so the driver has already opened a physical transaction by the
    time retention runs and this held even while the defect existed. It is the
    other half of the boundary — retention must neither commit its own rows nor
    anyone else's — and it is asserted because a future change that reached for a
    commit inside retention would break it and nothing else here would notice.
    """
    runtime.session.commit()
    with create_session_factory(runtime.engine)() as session:
        state = _authored_state(session, runtime, "ov-txn-bystander")
        identity = state.override_set_uuid
        retain_override_set(session, state, now=NOW)
        session.rollback()

    with create_session_factory(runtime.engine)() as other:
        assert (
            other.execute(
                select(func.count())
                .select_from(MechanicalOverrideORM)
                .where(MechanicalOverrideORM.override_id == "ov-txn-bystander")
            ).scalar_one()
            == 0
        )
    assert _retained_rows_elsewhere(runtime.engine, identity) == (0, 0, 0)


def test_the_fixture_installs_the_documented_trigger_set() -> None:
    """The fixture's mirror is the full set, named explicitly.

    ``create_all`` does not create triggers, so the suite installs them by hand
    and hand-mirroring is how a fixture drifts from production. This pins the
    names; ``tests/persistence/test_rules_authority_migration.py`` runs the real
    migration and asserts the database ends up with exactly these.
    """
    from tests.services.rules_authority.conftest import _trigger_names

    assert sorted(_trigger_names()) == sorted(EXPECTED_TRIGGERS)
