"""Persistence, exact binding and compare-and-swap on a real database (2b)."""

from __future__ import annotations

import threading
from uuid import UUID

import pytest

from afterworlds.models.enums import OverrideOperationEnum
from afterworlds.services.dnd5e_state import service, store
from afterworlds.services.dnd5e_state.authority import current_binding
from afterworlds.services.dnd5e_state.errors import (
    BindingRefusedError,
    FailureCode,
    InvalidStateError,
    StaleRevisionError,
)
from afterworlds.services.rules_authority.outcomes import AuthorityOutcome
from tests.services.dnd5e_state.conftest import (
    NOW,
    Table,
    new_character,
    new_story,
    poisoned,
    wizardish,
)
from tests.services.rules_authority.conftest import (
    DISABLE_PAYLOAD,
    PROSE_COMPONENT_TARGET,
    author_override,
)


def _character(table: Table, **state: object) -> tuple[UUID, UUID]:
    with table.factory() as s, s.begin():
        story = new_story(s)
        sheet = new_character(s, story)
        service.create_character(s, sheet, table.package, wizardish(**state), now=NOW)
    return story, sheet


def test_state_round_trips_through_a_fresh_session_with_its_exact_binding(
    table: Table,
) -> None:
    _, sheet = _character(table, heroic_inspiration=False)
    with table.factory() as s:
        current = current_binding(s, table.package, now=NOW)
        stored = service.read_character(s, sheet)
    assert stored.revision == 1
    assert stored.state == wizardish(heroic_inspiration=False)
    assert stored.binding.package_uuid == table.package
    assert stored.binding.mechanical_projection_uuid == table.runtime.projection_uuid
    assert current == stored.binding
    with table.factory() as s:
        assert store.binding_history(s, sheet) == (("bound", stored.binding, 1),)


def test_missing_and_explicitly_empty_state_stay_distinct_after_a_fresh_read(
    table: Table,
) -> None:
    _, sheet = _character(table)
    with table.factory() as s:
        state = service.read_character(s, sheet).state
    assert state.conditions == ()  # recorded: none
    assert state.feats is None  # never recorded
    assert state.heroic_inspiration is None
    assert state.currency is None


def test_an_invalid_identity_is_refused_and_nothing_is_written(table: Table) -> None:
    from afterworlds.models.dnd5e_state import GrantSource, SpellAccess

    bad = wizardish(
        spell_access=(
            SpellAccess(
                pool_id="wizard",
                spell_record_key="spell:not-accepted",
                mode="prepared",
                source=GrantSource(record_key="spell:wish"),
            ),
        )
    )
    with table.factory() as s, s.begin():
        story = new_story(s)
        sheet = new_character(s, story)
    with table.factory() as s, s.begin(), pytest.raises(InvalidStateError) as exc:
        service.create_character(s, sheet, table.package, bad, now=NOW)
    assert [f.code for f in exc.value.failures] == [FailureCode.INVALID_IDENTITY]
    with table.factory() as s:
        assert store.get_character(s, sheet) is None


def test_creation_against_an_unpublished_package_is_refused(table: Table) -> None:
    with table.factory() as s, s.begin():
        story = new_story(s)
        sheet = new_character(s, story)
    with table.factory() as s, pytest.raises(BindingRefusedError) as exc:
        service.create_character(
            s, sheet, table.runtime.bare_package_uuid, wizardish(), now=NOW
        )
    assert exc.value.outcome is AuthorityOutcome.UNPUBLISHED


def test_an_update_commits_only_against_the_revision_it_read(table: Table) -> None:
    _, sheet = _character(table)
    with table.factory() as s, s.begin():
        service.update_character(
            s,
            sheet,
            wizardish(conditions=(poisoned("a"),)),
            expected_revision=1,
            now=NOW,
        )
    with table.factory() as s, s.begin(), pytest.raises(StaleRevisionError):
        service.update_character(s, sheet, wizardish(), expected_revision=1, now=NOW)
    with table.factory() as s:
        stored = service.read_character(s, sheet)
    assert stored.revision == 2
    assert stored.state.conditions == (poisoned("a"),)


def test_concurrent_writers_on_separate_connections_cannot_both_commit(
    table: Table,
) -> None:
    _, sheet = _character(table)
    barrier = threading.Barrier(2)
    outcomes: list[str] = []

    def write(tag: str) -> None:
        with table.factory() as s:
            stored = service.read_character(s, sheet)
            barrier.wait()
            try:
                with s.begin_nested():
                    service.update_character(
                        s,
                        sheet,
                        wizardish(conditions=(poisoned(tag),)),
                        expected_revision=stored.revision,
                        now=NOW,
                    )
                s.commit()
                outcomes.append("committed")
            except StaleRevisionError:
                s.rollback()
                outcomes.append("stale")
            except Exception as exc:  # database is locked -> lost the race
                s.rollback()
                outcomes.append(type(exc).__name__)

    threads = [threading.Thread(target=write, args=(t,)) for t in ("a", "b")]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert outcomes.count("committed") == 1, outcomes
    with table.factory() as s:
        assert service.read_character(s, sheet).revision == 2


def test_a_rolled_back_update_leaves_the_prior_state(table: Table) -> None:
    _, sheet = _character(table)
    with table.factory() as s:
        s.begin()
        service.update_character(
            s,
            sheet,
            wizardish(conditions=(poisoned("x"),)),
            expected_revision=1,
            now=NOW,
        )
        s.rollback()
    with table.factory() as s:
        stored = service.read_character(s, sheet)
    assert stored.revision == 1
    assert stored.state.conditions == ()


def test_a_superseded_binding_refuses_production_writes_but_stays_readable(
    table: Table,
) -> None:
    _, sheet = _character(table)
    with table.factory() as s, s.begin():
        author_override(
            s,
            override_id="house-1",
            target=PROSE_COMPONENT_TARGET,
            operation=OverrideOperationEnum.DISABLE,
            payload=DISABLE_PAYLOAD,
        )
    with table.factory() as s, pytest.raises(BindingRefusedError) as exc:
        service.update_character(s, sheet, wizardish(), expected_revision=1, now=NOW)
    assert exc.value.outcome is AuthorityOutcome.STALE
    with table.factory() as s:
        stored = service.read_character(s, sheet)
        with pytest.raises(BindingRefusedError):
            service.readiness(s, stored, now=NOW)
        # Historical replay / recorded-binding maintenance still reads the
        # exact authority the character was bound to.
        index = service.recorded_authority(s, stored, now=NOW)
    assert index.binding == stored.binding
    assert index.record("spell:wish") is not None
