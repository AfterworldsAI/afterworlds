"""RPG sheet-effect application over CRD Issue 2b typed state (Fork B→B1)."""

from __future__ import annotations

import json
from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
from sqlalchemy.orm import Session

from afterworlds.ingestion.mechanical.representation import ConditionKind
from afterworlds.models.dnd5e_state import (
    ConditionInstance,
    Dnd5eCharacterState,
    GrantSource,
    HitPoints,
    SlotLevel,
    SpellSlotPool,
)
from afterworlds.models.rpg import SheetEffect
from afterworlds.pipeline.orchestrator.service import OrchestratorService
from afterworlds.services.dnd5e_state import store
from afterworlds.services.dnd5e_state.effects import apply_effects
from afterworlds.services.dnd5e_state.errors import StaleRevisionError
from afterworlds.services.dnd5e_state.turn import TurnCharacter
from tests.rpg_characters import BINDING

_NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _pool(pool_id: str, *levels: tuple[int, int, int]) -> SpellSlotPool:
    return SpellSlotPool(
        pool_id=pool_id,
        source=GrantSource(record_key="classes.wizard"),
        levels=tuple(SlotLevel(level=lv, total=t, expended=e) for lv, t, e in levels),
    )


def _state(
    *,
    current_hp: int = 30,
    maximum_hp: int = 40,
    pools: tuple[SpellSlotPool, ...] = (),
    conditions: tuple[ConditionInstance, ...] = (),
) -> Dnd5eCharacterState:
    return Dnd5eCharacterState(
        hit_points=HitPoints(current=current_hp, maximum=maximum_hp, temporary=0),
        spell_slot_pools=pools,
        conditions=conditions,
    )


def _effect(target: str, operation: str, value: object) -> SheetEffect:
    return SheetEffect(
        target=target,
        operation=operation,  # type: ignore[arg-type]
        value_json=json.dumps(value),
    )


def _hp(state: Dnd5eCharacterState) -> int:
    assert state.hit_points is not None
    return state.hit_points.current


# -- pure application ---------------------------------------------------------


def test_hp_delta_applies_without_any_floor() -> None:
    # ADR-0003 Decision 2: what happens below zero is adjudication's, so the
    # stored value is not floored.
    assert (
        _hp(apply_effects(_state(current_hp=5), (_effect("current_hp", "delta", -9),)))
        == -4
    )


def test_hp_never_exceeds_the_stored_maximum() -> None:
    assert _hp(apply_effects(_state(), (_effect("current_hp", "delta", 25),))) == 40
    assert _hp(apply_effects(_state(), (_effect("current_hp", "set", 12),))) == 12


def test_slot_effects_adjust_expended_slots_in_their_one_pool() -> None:
    state = _state(pools=(_pool("spellcasting", (1, 4, 0), (2, 3, 0)),))
    after = apply_effects(state, (_effect("spell_slot.1", "delta", 2),))
    (pool,) = after.spell_slot_pools or ()
    assert [(s.level, s.expended) for s in pool.levels] == [(1, 2), (2, 0)]
    after = apply_effects(state, (_effect("spell_slot.1", "set", 99),))
    (pool,) = after.spell_slot_pools or ()
    assert pool.levels[0].expended == 4  # structural: never beyond the total


def test_a_slot_level_held_by_two_pools_is_refused_not_guessed() -> None:
    state = _state(
        pools=(_pool("spellcasting", (1, 4, 0)), _pool("pact_magic", (1, 1, 0)))
    )
    with pytest.raises(ValueError, match="2 pools hold level 1"):
        apply_effects(state, (_effect("spell_slot.1", "delta", 1),))


@pytest.mark.parametrize(
    "effect",
    [
        _effect("spell_slot.7", "delta", 1),
        _effect("armor_class", "set", 18),
        _effect("current_hp", "delta", "3"),
    ],
)
def test_unknown_or_malformed_targets_fail_closed(effect: SheetEffect) -> None:
    with pytest.raises(ValueError):
        apply_effects(_state(pools=(_pool("spellcasting", (1, 2, 0)),)), (effect,))


def test_conditions_are_typed_instances_added_and_cleared() -> None:
    added = apply_effects(
        _state(),
        (
            _effect(
                "conditions",
                "apply_condition",
                {"condition": "poisoned", "visibility": "visible"},
            ),
            _effect(
                "conditions",
                "apply_condition",
                {"condition": "prone", "visibility": "hidden"},
            ),
        ),
    )
    assert [c.condition for c in added.conditions or ()] == [
        ConditionKind.POISONED,
        ConditionKind.PRONE,
    ]
    cleared = apply_effects(
        added, (_effect("conditions", "clear_condition", {"condition": "poisoned"}),)
    )
    assert [c.condition for c in cleared.conditions or ()] == [ConditionKind.PRONE]
    with pytest.raises(ValueError):
        apply_effects(
            _state(),
            (_effect("conditions", "apply_condition", {"condition": "sleepy"}),),
        )


# -- the orchestrator's compare-and-swap write --------------------------------


@pytest.fixture()
def db_session() -> Iterator[Session]:
    import afterworlds.persistence.orm.character_sheet  # noqa: F401
    import afterworlds.persistence.orm.story  # noqa: F401
    from afterworlds.persistence.database import create_engine, create_session_factory
    from afterworlds.persistence.orm.base import Base

    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with create_session_factory(engine)() as session:
        yield session
    engine.dispose()


def _persisted(session: Session, state: Dnd5eCharacterState) -> TurnCharacter:
    from afterworlds.models.character_sheet import RpgCharacterSheetBase
    from afterworlds.models.enums import StoryMode
    from afterworlds.models.story import Story
    from afterworlds.persistence.crud.character_sheet import create_rpg_base_sheet
    from afterworlds.persistence.crud.story import create_story

    story = Story(title="t", mode=StoryMode.RPG, created_at=_NOW, updated_at=_NOW)
    create_story(session, story)
    base = RpgCharacterSheetBase(
        story_id=story.story_id,
        character_name="Aldric",
        created_at=_NOW,
        updated_at=_NOW,
    )
    create_rpg_base_sheet(session, base)
    stored = store.create_character_state(
        session, base.sheet_id, state, BINDING, now="t"
    )
    session.commit()
    return TurnCharacter(stored, ())


def _orchestrator() -> OrchestratorService:
    return OrchestratorService.__new__(OrchestratorService)


def test_the_turn_writes_effects_by_cas_and_returns_the_new_revision(
    db_session: Session,
) -> None:
    character = _persisted(db_session, _state())
    after = _orchestrator()._apply_rpg_sheet_effects(
        db_session, (_effect("current_hp", "delta", -7),), character
    )
    db_session.commit()
    assert after.stored.revision == 2
    assert _hp(after.stored.state) == 23
    fresh = store.get_character(db_session, character.sheet_id)
    assert fresh is not None and _hp(fresh.state) == 23


def test_work_computed_against_a_superseded_revision_cannot_commit(
    db_session: Session,
) -> None:
    character = _persisted(db_session, _state())
    _orchestrator()._apply_rpg_sheet_effects(
        db_session, (_effect("current_hp", "delta", -1),), character
    )
    db_session.commit()
    with pytest.raises(StaleRevisionError):
        _orchestrator()._apply_rpg_sheet_effects(
            db_session, (_effect("current_hp", "delta", -1),), character
        )


def test_a_rolled_back_turn_leaves_no_mutation(db_session: Session) -> None:
    character = _persisted(db_session, _state())
    _orchestrator()._apply_rpg_sheet_effects(
        db_session, (_effect("current_hp", "delta", -10),), character
    )
    db_session.rollback()
    fresh = store.get_character(db_session, character.sheet_id)
    assert fresh is not None and (fresh.revision, _hp(fresh.state)) == (1, 30)
