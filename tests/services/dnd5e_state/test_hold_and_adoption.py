"""Shared-rule-change holds and deliberate adoption on a real database (2b)."""

from __future__ import annotations

from dataclasses import replace
from uuid import UUID

import pytest
import sqlalchemy as sa

from afterworlds.models.dnd5e_state import CreatureState, HitPoints
from afterworlds.models.enums import OverrideOperationEnum
from afterworlds.persistence.orm.rules_authority import (
    MechanicalOverrideORM,
    SharedRuleChangeORM,
)
from afterworlds.services.dnd5e_state import adoption, leases, service, store
from afterworlds.services.dnd5e_state.adoption import AdoptionStatus
from afterworlds.services.dnd5e_state.authority import current_binding, require_current
from afterworlds.services.dnd5e_state.errors import (
    BindingRefusedError,
    StaleRevisionError,
)
from afterworlds.services.dnd5e_state.shared_changes import (
    ChangeStatus,
    OverrideSpec,
    SharedChangeError,
    activate,
    request_change,
    withdraw,
)
from afterworlds.services.dnd5e_state.turn import after_events
from afterworlds.services.rules_authority.outcomes import AuthorityOutcome
from tests.services.dnd5e_state.conftest import (
    CREATURE_KEY,
    NOW,
    Table,
    add_pending_roll,
    new_character,
    new_story,
    resolve_pending_roll,
    wizardish,
)
from tests.services.rules_authority.conftest import (
    DISABLE_PAYLOAD,
    PROSE_COMPONENT_TARGET,
    SPELL_RECORD_TARGET,
)

HOUSE_RULE = OverrideSpec(
    override_id="house-prose",
    target=PROSE_COMPONENT_TARGET,
    operation=OverrideOperationEnum.DISABLE,
    payload=DISABLE_PAYLOAD,
)
DISABLE_SPELL = OverrideSpec(
    override_id="house-no-wish",
    target=SPELL_RECORD_TARGET,
    operation=OverrideOperationEnum.DISABLE,
    payload=DISABLE_PAYLOAD,
)


def _story_with_character(table: Table) -> tuple[UUID, UUID]:
    with table.factory() as s, s.begin():
        story = new_story(s)
        sheet = new_character(s, story)
        service.create_character(s, sheet, table.package, wizardish(), now=NOW)
    return story, sheet


def _request(table: Table, *specs: OverrideSpec) -> str:
    with table.factory() as s, s.begin():
        return request_change(
            s,
            table.package,
            table.runtime.release_version,
            specs,
            requested_by="owner",
            now=NOW,
        )


def _activate(table: Table, change_id: str):  # type: ignore[no-untyped-def]
    with table.factory() as s, s.begin():
        return activate(s, change_id, now=NOW)


def _override_rows(table: Table) -> int:
    with table.factory() as s:
        return int(
            s.execute(
                sa.select(sa.func.count()).select_from(MechanicalOverrideORM)
            ).scalar_one()
        )


def test_a_requested_change_stays_out_of_current_override_rows(table: Table) -> None:
    _story_with_character(table)
    with table.factory() as s:
        before = current_binding(s, table.package, now=NOW)
    _request(table, HOUSE_RULE)
    assert _override_rows(table) == 0
    with table.factory() as s:
        assert current_binding(s, table.package, now=NOW) == before


def test_a_change_waits_for_a_pending_roll_then_activates_to_its_exact_target(
    table: Table,
) -> None:
    story, sheet = _story_with_character(table)
    with table.factory() as s, s.begin():
        roll = add_pending_roll(s, story, sheet)
    change = _request(table, HOUSE_RULE)
    held = _activate(table, change)
    assert (held.status, held.blocking) == (ChangeStatus.HELD, 1)
    assert _override_rows(table) == 0
    with table.factory() as s, s.begin():
        resolve_pending_roll(s, roll)
    assert _activate(table, change).status is ChangeStatus.ACTIVE
    with table.factory() as s:
        row = s.get(SharedRuleChangeORM, change)
        assert row is not None
        assert str(current_binding(s, table.package, now=NOW).override_set_uuid) == (
            row.target_override_set_uuid
        )


def test_an_in_flight_turn_lease_holds_activation_until_released(table: Table) -> None:
    story, _ = _story_with_character(table)
    lease = leases.acquire(table.factory, story, now=NOW)
    change = _request(table, HOUSE_RULE)
    assert _activate(table, change).status is ChangeStatus.HELD
    leases.release_committed(table.factory, lease)
    assert _activate(table, change).status is ChangeStatus.ACTIVE


def test_events_in_unaffected_stories_do_not_hold_a_change(table: Table) -> None:
    _story_with_character(table)
    with table.factory() as s, s.begin():
        other = new_story(s)  # no subject bound to the package
    leases.acquire(table.factory, other, now=NOW)
    change = _request(table, HOUSE_RULE)
    assert _activate(table, change).status is ChangeStatus.ACTIVE


def test_a_creature_alone_makes_its_story_affected(table: Table) -> None:
    with table.factory() as s, s.begin():
        story = new_story(s)
        service.create_creature(
            s,
            story,
            "Servant",
            table.package,
            CreatureState(
                template_record_key=CREATURE_KEY,
                hit_points=HitPoints(current=5, maximum=5, temporary=0),
                conditions=(),
                active_effects=(),
            ),
            now=NOW,
        )
    leases.acquire(table.factory, story, now=NOW)
    change = _request(table, HOUSE_RULE)
    assert _activate(table, change).status is ChangeStatus.HELD


def test_a_turn_that_starts_after_activation_refuses_the_stale_binding(
    table: Table,
) -> None:
    _, sheet = _story_with_character(table)
    with table.factory() as s:
        read_before = service.read_character(s, sheet).binding
    change = _request(table, HOUSE_RULE)
    assert _activate(table, change).status is ChangeStatus.ACTIVE
    with table.factory() as s, pytest.raises(BindingRefusedError) as exc:
        require_current(s, read_before, now=NOW)
    assert exc.value.outcome is AuthorityOutcome.STALE


def test_a_change_whose_base_moved_is_rejected_not_retargeted(table: Table) -> None:
    _story_with_character(table)
    first = _request(table, HOUSE_RULE)
    second = _request(table, DISABLE_SPELL)
    assert _activate(table, first).status is ChangeStatus.ACTIVE
    result = _activate(table, second)
    assert result.status is ChangeStatus.REJECTED
    assert "cannot be produced" in result.detail
    assert _override_rows(table) == 1


def test_adoption_rebinds_the_character_only_and_preserves_its_state(
    table: Table,
) -> None:
    story, sheet = _story_with_character(table)
    with table.factory() as s, s.begin():
        creature = service.create_creature(
            s,
            story,
            "Servant",
            table.package,
            CreatureState(
                template_record_key=CREATURE_KEY,
                hit_points=HitPoints(current=5, maximum=5, temporary=0),
                conditions=(),
                active_effects=(),
            ),
            now=NOW,
        ).creature_id
        before = service.read_character(s, sheet)
    change = _request(table, HOUSE_RULE)
    assert _activate(table, change).status is ChangeStatus.ACTIVE
    with table.factory() as s, s.begin():
        outcome = adoption.request_adoption(
            s, "character", sheet, change_id=change, now=NOW
        )
    assert outcome.status is AdoptionStatus.APPLIED
    with table.factory() as s:
        after = service.read_character(s, sheet)
        assert after.state == before.state
        assert after.binding == current_binding(s, table.package, now=NOW)
        assert [e for e, _, _ in store.binding_history(s, sheet)] == [
            "bound",
            "adopted",
        ]
        # The character's creature keeps its own binding until it adopts.
        assert service.read_creature(s, creature).binding == before.binding


def test_adoption_waits_for_a_pending_roll_and_accepts_its_normal_results(
    table: Table,
) -> None:
    story, sheet = _story_with_character(table)
    with table.factory() as s, s.begin():
        roll = add_pending_roll(s, story, sheet)
    change = _request(table, HOUSE_RULE)
    with table.factory() as s, s.begin():
        held = adoption.request_adoption(
            s, "character", sheet, change_id=change, now=NOW
        )
    assert held.status is AdoptionStatus.HELD
    # The roll resolves and changes hit points: an ordinary new revision.
    with table.factory() as s, s.begin():
        resolve_pending_roll(s, roll)
        current = service.read_character(s, sheet)
        store.save_state(
            s,
            "character",
            sheet,
            wizardish(hit_points=HitPoints(current=4, maximum=9, temporary=0)),
            expected_revision=current.revision,
            expected_binding=current.binding,
            now=NOW,
        )
    after_events(table.factory, story, now=NOW)
    with table.factory() as s:
        assert adoption.status_of(s, held.request_id).status is AdoptionStatus.APPLIED
        stored = service.read_character(s, sheet)
        assert stored.state.hit_points == HitPoints(current=4, maximum=9, temporary=0)
        assert stored.binding == current_binding(s, table.package, now=NOW)


def test_an_incompatible_target_is_refused_without_any_change(table: Table) -> None:
    _, sheet = _story_with_character(table)
    change = _request(table, DISABLE_SPELL)  # the character prepares spell:wish
    assert _activate(table, change).status is ChangeStatus.ACTIVE
    with table.factory() as s:
        before = service.read_character(s, sheet)
    with table.factory() as s, s.begin():
        outcome = adoption.request_adoption(
            s, "character", sheet, change_id=change, now=NOW
        )
    assert outcome.status is AdoptionStatus.REFUSED
    assert outcome.reason is not None and "incompatible" in outcome.reason
    with table.factory() as s:
        after = service.read_character(s, sheet)
    assert (after.binding, after.revision, after.state) == (
        before.binding,
        before.revision,
        before.state,
    )


def test_a_target_superseded_before_processing_is_refused_not_substituted(
    table: Table,
) -> None:
    story, sheet = _story_with_character(table)
    with table.factory() as s, s.begin():
        roll = add_pending_roll(s, story, sheet)
    first = _request(table, HOUSE_RULE)
    with table.factory() as s, s.begin():
        held = adoption.request_adoption(
            s, "character", sheet, change_id=first, now=NOW
        )
    with table.factory() as s, s.begin():
        resolve_pending_roll(s, roll)
    assert _activate(table, first).status is ChangeStatus.ACTIVE
    # A newer house rule lands before the held adoption is processed.
    with table.factory() as s, s.begin():
        newer = request_change(
            s,
            table.package,
            table.runtime.release_version,
            (replace(DISABLE_SPELL, override_id="z"),),
            requested_by="owner",
            now=NOW,
        )
    assert _activate(table, newer).status is ChangeStatus.ACTIVE
    with table.factory() as s, s.begin():
        outcome = adoption.process(s, held.request_id, now=NOW)
    assert outcome.status is AdoptionStatus.REFUSED
    assert outcome.reason is not None and "no newer target" in outcome.reason


def test_withdrawing_a_change_refuses_the_adoption_waiting_on_it(table: Table) -> None:
    story, sheet = _story_with_character(table)
    with table.factory() as s, s.begin():
        add_pending_roll(s, story, sheet)
    change = _request(table, HOUSE_RULE)
    with table.factory() as s, s.begin():
        held = adoption.request_adoption(
            s, "character", sheet, change_id=change, now=NOW
        )
    with table.factory() as s, s.begin():
        result = withdraw(s, change, "owner changed their mind", now=NOW)
    assert result.status is ChangeStatus.WITHDRAWN
    after_events(table.factory, story, now=NOW)
    with table.factory() as s:
        outcome = adoption.status_of(s, held.request_id)
    assert outcome.status is AdoptionStatus.REFUSED
    assert outcome.reason is not None and "withdrawn" in outcome.reason


def test_a_crash_before_commit_leaves_nothing_and_the_retry_applies_once(
    table: Table,
) -> None:
    _, sheet = _story_with_character(table)
    change = _request(table, HOUSE_RULE)
    assert _activate(table, change).status is ChangeStatus.ACTIVE
    request_id = "retry-me"

    class Crash(RuntimeError):
        pass

    with table.factory() as s, pytest.raises(Crash):
        s.begin()
        adoption.request_adoption(
            s, "character", sheet, change_id=change, request_id=request_id, now=NOW
        )
        raise Crash  # the process dies before the transaction commits
    with table.factory() as s:
        assert [e for e, _, _ in store.binding_history(s, sheet)] == ["bound"]
    for _ in range(2):  # the retry, then a duplicate retry
        with table.factory() as s, s.begin():
            outcome = adoption.request_adoption(
                s, "character", sheet, change_id=change, request_id=request_id, now=NOW
            )
        assert outcome.status is AdoptionStatus.APPLIED
    with table.factory() as s:
        assert [e for e, _, _ in store.binding_history(s, sheet)] == [
            "bound",
            "adopted",
        ]


def test_a_conflicting_write_during_the_final_commit_refuses_visibly(
    table: Table, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, sheet = _story_with_character(table)
    change = _request(table, HOUSE_RULE)
    assert _activate(table, change).status is ChangeStatus.ACTIVE

    def conflicting(*args: object, **kwargs: object) -> int:
        raise StaleRevisionError("another writer committed first")

    monkeypatch.setattr(store, "rebind", conflicting)
    with table.factory() as s, s.begin():
        outcome = adoption.request_adoption(
            s, "character", sheet, change_id=change, now=NOW
        )
    assert outcome.status is AdoptionStatus.REFUSED
    assert outcome.reason is not None and "conflicting write" in outcome.reason


def test_an_override_that_cannot_be_applied_is_refused_at_request(
    table: Table,
) -> None:
    """Advisor: the trial applies the whole effective set, not only resolves it."""
    from tests.services.rules_authority.conftest import replace_record_payload

    wrong_kind = OverrideSpec(
        override_id="house-wrong-kind",
        target=SPELL_RECORD_TARGET,
        operation=OverrideOperationEnum.REPLACE,
        payload=replace_record_payload(record_kind="creature"),
    )
    before = _override_rows(table)
    with pytest.raises(
        SharedChangeError, match=AuthorityOutcome.INVALID_OVERRIDE.value
    ):
        _request(table, wrong_kind)
    with table.factory() as s:
        changes = s.execute(
            sa.select(sa.func.count()).select_from(SharedRuleChangeORM)
        ).scalar_one()
    assert (changes, _override_rows(table)) == (0, before)


def test_adoption_processing_claims_the_write_lock_first(table: Table) -> None:
    """Advisor: no lease or activation can commit between check and rebind."""
    story, sheet = _story_with_character(table)
    with table.factory() as s, s.begin():
        roll = add_pending_roll(s, story, sheet)
    change = _request(table, HOUSE_RULE)
    with table.factory() as s, s.begin():
        held = adoption.request_adoption(
            s, "character", sheet, change_id=change, now=NOW
        )
    assert held.status is AdoptionStatus.HELD
    with table.factory() as s, s.begin():
        resolve_pending_roll(s, roll)
    assert _activate(table, change).status is ChangeStatus.ACTIVE
    statements: list[str] = []

    def record(*args: object) -> None:
        statements.append(str(args[2]).lstrip().split()[0].upper())

    sa.event.listen(table.runtime.engine, "before_cursor_execute", record)
    try:
        with table.factory() as s, s.begin():
            outcome = adoption.process(s, held.request_id, now=NOW)
    finally:
        sa.event.remove(table.runtime.engine, "before_cursor_execute", record)
    assert outcome.status is AdoptionStatus.APPLIED
    assert statements[0] == "UPDATE"
