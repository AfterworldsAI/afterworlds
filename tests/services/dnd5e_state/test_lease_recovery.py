"""Turn-lease recovery needs a proven-dead owner (CRD Issue 2b, Codex review).

Real processes on one SQLite file: a lease held by a live process survives
any other process's (or this process's) startup recovery, so a held shared
change stays held; a lease whose process died is recovered, after which the
change activates. A lease whose owner cannot be proven dead is kept.
"""

from __future__ import annotations

import subprocess
import sys
import textwrap
from collections.abc import Iterator
from pathlib import Path
from uuid import UUID, uuid4

import pytest
import sqlalchemy as sa

from afterworlds.persistence.orm.dnd5e_state import RpgTurnLeaseORM
from afterworlds.services.dnd5e_state import leases
from afterworlds.services.dnd5e_state.shared_changes import ChangeStatus
from tests.services.dnd5e_state.conftest import NOW, Table
from tests.services.dnd5e_state.test_hold_and_adoption import (
    HOUSE_RULE,
    _activate,
    _request,
    _story_with_character,
)

_CHILD = textwrap.dedent("""
    import os, sys
    from uuid import UUID
    from afterworlds.persistence.database import create_engine, create_session_factory
    import afterworlds.persistence.orm.story  # registers the FK target
    from afterworlds.services.dnd5e_state import leases

    factory = create_session_factory(create_engine(sys.argv[1]))
    leases.acquire(factory, UUID(sys.argv[2]), now="t")
    print("leased", flush=True)
    sys.stdin.readline()
    os._exit(0)  # a crash: no release, no cleanup
    """)


def _leases(table: Table) -> int:
    with table.factory() as s:
        return int(
            s.execute(
                sa.select(sa.func.count()).select_from(RpgTurnLeaseORM)
            ).scalar_one()
        )


@pytest.fixture()
def other_process(table: Table) -> Iterator[tuple[subprocess.Popen[str], UUID]]:
    story, _ = _story_with_character(table)
    child = subprocess.Popen(
        [sys.executable, "-c", _CHILD, str(table.runtime.engine.url), str(story)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
        cwd=Path(__file__).resolve().parents[3],
    )
    assert child.stdout is not None
    assert child.stdout.readline().strip() == "leased"
    try:
        yield child, story
    finally:
        if child.poll() is None:
            child.kill()
        child.wait(timeout=30)


def test_a_live_process_lease_survives_another_apps_startup_recovery(
    table: Table, other_process: tuple[subprocess.Popen[str], UUID]
) -> None:
    change = _request(table, HOUSE_RULE)
    assert _activate(table, change).status is ChangeStatus.HELD
    assert leases.clear_orphans(table.factory) == 0
    assert _leases(table) == 1
    assert _activate(table, change).status is ChangeStatus.HELD


def test_a_crashed_process_lease_is_recovered_then_activation_proceeds(
    table: Table, other_process: tuple[subprocess.Popen[str], UUID]
) -> None:
    child, _ = other_process
    change = _request(table, HOUSE_RULE)
    assert child.stdin is not None
    child.stdin.write("go\n")
    child.stdin.flush()
    child.wait(timeout=30)
    assert _activate(table, change).status is ChangeStatus.HELD  # not yet recovered
    assert leases.clear_orphans(table.factory) == 1
    assert _leases(table) == 0
    assert _activate(table, change).status is ChangeStatus.ACTIVE


def test_this_processs_own_live_lease_survives_recovery(table: Table) -> None:
    """Codex's probe: another app constructed in this process mid-turn."""
    story, _ = _story_with_character(table)
    lease = leases.acquire(table.factory, story, now=NOW)
    change = _request(table, HOUSE_RULE)
    assert _activate(table, change).status is ChangeStatus.HELD
    leases.clear_orphans(table.factory)
    assert _activate(table, change).status is ChangeStatus.HELD
    leases.release_committed(table.factory, lease)
    assert _activate(table, change).status is ChangeStatus.ACTIVE


def test_a_lease_whose_owner_cannot_be_proven_dead_is_kept(table: Table) -> None:
    story, _ = _story_with_character(table)
    with table.factory() as s, s.begin():
        s.add(
            RpgTurnLeaseORM(
                lease_id=str(uuid4()),
                story_id=str(story),
                owner_id=str(uuid4()),  # no owner file: unprovable
                started_at=NOW,
            )
        )
    leases.clear_orphans(table.factory)
    assert _leases(table) == 1
