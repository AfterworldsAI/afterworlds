"""Tests for RPG sheet-effect application (Fork B→B1) — CRD Issue 15."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import uuid4

import pytest

from afterworlds.models.character_sheet import (
    Dnd5eAbilityScores,
    Dnd5eActiveCondition,
    Dnd5eCharacterSheet,
    SpellSlotLevel,
)
from afterworlds.models.enums import ConditionVisibility
from afterworlds.models.rpg import SheetEffect
from afterworlds.pipeline.orchestrator.service import OrchestratorService

_NOW = datetime(2026, 1, 1, tzinfo=UTC)
_ABILITY_SCORES = Dnd5eAbilityScores(
    strength=10,
    dexterity=14,
    constitution=12,
    intelligence=10,
    wisdom=10,
    charisma=10,
)


def _make_sheet(
    *,
    current_hp: int = 30,
    maximum_hp: int = 40,
    spell_slots: dict[int, SpellSlotLevel] | None = None,
    conditions: list[Dnd5eActiveCondition] | None = None,
) -> Dnd5eCharacterSheet:
    return Dnd5eCharacterSheet(
        story_id=uuid4(),
        rules_package_id="dnd5e-v1",
        character_name="Aldric",
        character_class="Fighter",
        background="Soldier",
        level=5,
        ability_scores=_ABILITY_SCORES,
        current_hp=current_hp,
        maximum_hp=maximum_hp,
        spell_slots=spell_slots or {},
        active_conditions=conditions or [],
        created_at=_NOW,
        updated_at=_NOW,
    )


def _effect(
    target: str,
    operation: str,
    value: object,
) -> SheetEffect:
    return SheetEffect(
        target=target,
        operation=operation,  # type: ignore[arg-type]
        value_json=json.dumps(value),
    )


def _make_orchestrator() -> OrchestratorService:
    """Minimal OrchestratorService for calling _apply_rpg_sheet_effects."""

    from afterworlds.pipeline.orchestrator.service import OrchestratorService

    svc = OrchestratorService.__new__(OrchestratorService)
    svc._rpg_visible_state_service = None  # type: ignore[attr-defined]
    return svc


# ---------------------------------------------------------------------------
# Fixtures — in-memory DB session
# ---------------------------------------------------------------------------


@pytest.fixture()
def db_session():  # type: ignore[no-untyped-def]
    """Provide a SQLAlchemy session with sheet tables created."""
    import afterworlds.persistence.orm.character_sheet  # noqa: F401
    import afterworlds.persistence.orm.story  # noqa: F401
    from afterworlds.persistence.database import create_engine, create_session_factory
    from afterworlds.persistence.orm.base import Base

    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    factory = create_session_factory(engine)
    sess = factory()
    try:
        yield sess
    finally:
        sess.close()
    Base.metadata.drop_all(engine)
    engine.dispose()


def _persist_sheet(session: object, sheet: Dnd5eCharacterSheet) -> None:
    """Write base + dnd5e rows for the given sheet."""
    from afterworlds.models.character_sheet import RpgCharacterSheetBase
    from afterworlds.models.enums import StoryMode
    from afterworlds.models.story import Story
    from afterworlds.persistence.crud.character_sheet import (
        create_dnd5e_sheet,
        create_rpg_base_sheet,
    )
    from afterworlds.persistence.crud.story import create_story

    story = Story(
        story_id=sheet.story_id,
        title="Test",
        mode=StoryMode.RPG,
        created_at=_NOW,
        updated_at=_NOW,
    )
    create_story(session, story)
    base = RpgCharacterSheetBase(
        sheet_id=sheet.sheet_id,
        story_id=sheet.story_id,
        rules_package_id=sheet.rules_package_id,
        character_name=sheet.character_name,
        created_at=sheet.created_at,
        updated_at=sheet.updated_at,
    )
    create_rpg_base_sheet(session, base)
    create_dnd5e_sheet(session, sheet)
    session.commit()  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# delta / set — current_hp
# ---------------------------------------------------------------------------


def test_apply_hp_delta_decreases_hp(db_session) -> None:  # type: ignore[no-untyped-def]
    svc = _make_orchestrator()
    sheet = _make_sheet(current_hp=30, maximum_hp=40)
    _persist_sheet(db_session, sheet)

    result = svc._apply_rpg_sheet_effects(
        db_session, (_effect("current_hp", "delta", -5),), sheet
    )
    assert result.current_hp == 25


def test_apply_hp_delta_cannot_go_below_zero(db_session) -> None:  # type: ignore[no-untyped-def]
    svc = _make_orchestrator()
    sheet = _make_sheet(current_hp=3, maximum_hp=40)
    _persist_sheet(db_session, sheet)

    result = svc._apply_rpg_sheet_effects(
        db_session, (_effect("current_hp", "delta", -10),), sheet
    )
    assert result.current_hp == 0


def test_apply_hp_delta_cannot_exceed_maximum(db_session) -> None:  # type: ignore[no-untyped-def]
    svc = _make_orchestrator()
    sheet = _make_sheet(current_hp=38, maximum_hp=40)
    _persist_sheet(db_session, sheet)

    result = svc._apply_rpg_sheet_effects(
        db_session, (_effect("current_hp", "delta", 10),), sheet
    )
    assert result.current_hp == 40


def test_apply_hp_set(db_session) -> None:  # type: ignore[no-untyped-def]
    svc = _make_orchestrator()
    sheet = _make_sheet(current_hp=30, maximum_hp=40)
    _persist_sheet(db_session, sheet)

    result = svc._apply_rpg_sheet_effects(
        db_session, (_effect("current_hp", "set", 20),), sheet
    )
    assert result.current_hp == 20


# ---------------------------------------------------------------------------
# delta / set — spell slots
# ---------------------------------------------------------------------------


def test_apply_spell_slot_delta(db_session) -> None:  # type: ignore[no-untyped-def]
    svc = _make_orchestrator()
    sheet = _make_sheet(spell_slots={1: SpellSlotLevel(total=3, used=1)})
    _persist_sheet(db_session, sheet)

    result = svc._apply_rpg_sheet_effects(
        db_session, (_effect("spell_slot.1", "delta", 1),), sheet
    )
    assert result.spell_slots[1].used == 2


def test_apply_spell_slot_set(db_session) -> None:  # type: ignore[no-untyped-def]
    svc = _make_orchestrator()
    sheet = _make_sheet(spell_slots={2: SpellSlotLevel(total=2, used=0)})
    _persist_sheet(db_session, sheet)

    result = svc._apply_rpg_sheet_effects(
        db_session, (_effect("spell_slot.2", "set", 2),), sheet
    )
    assert result.spell_slots[2].used == 2


def test_apply_spell_slot_unknown_level_fails_closed(db_session) -> None:  # type: ignore[no-untyped-def]
    svc = _make_orchestrator()
    sheet = _make_sheet(spell_slots={})
    _persist_sheet(db_session, sheet)

    with pytest.raises(ValueError, match="spell slot level 3"):
        svc._apply_rpg_sheet_effects(
            db_session, (_effect("spell_slot.3", "delta", 1),), sheet
        )


# ---------------------------------------------------------------------------
# Unknown target fails closed
# ---------------------------------------------------------------------------


def test_apply_unknown_target_fails_closed(db_session) -> None:  # type: ignore[no-untyped-def]
    svc = _make_orchestrator()
    sheet = _make_sheet()
    _persist_sheet(db_session, sheet)

    with pytest.raises(ValueError, match="Unknown sheet-effect target"):
        svc._apply_rpg_sheet_effects(
            db_session, (_effect("wisdom_score", "delta", 2),), sheet
        )


# ---------------------------------------------------------------------------
# apply_condition / clear_condition
# ---------------------------------------------------------------------------


def test_apply_condition_adds_to_active_conditions(db_session) -> None:  # type: ignore[no-untyped-def]
    svc = _make_orchestrator()
    sheet = _make_sheet()
    _persist_sheet(db_session, sheet)

    cond_data = {
        "sheet_id": str(sheet.sheet_id),
        "identifier": "poisoned",
        "display_label": "Poisoned",
        "source": "goblin_attack",
        "visibility": "visible",
    }
    result = svc._apply_rpg_sheet_effects(
        db_session,
        (_effect("conditions", "apply_condition", cond_data),),
        sheet,
    )
    assert len(result.active_conditions) == 1
    assert result.active_conditions[0].identifier == "poisoned"


def test_clear_condition_removes_matching_identifier(db_session) -> None:  # type: ignore[no-untyped-def]
    svc = _make_orchestrator()
    cond = Dnd5eActiveCondition(
        sheet_id=uuid4(),
        identifier="poisoned",
        display_label="Poisoned",
        source="test",
        visibility=ConditionVisibility.VISIBLE,
    )
    sheet = _make_sheet(conditions=[cond])
    # Re-set sheet_id on condition
    cond2 = Dnd5eActiveCondition(
        sheet_id=sheet.sheet_id,
        identifier="poisoned",
        display_label="Poisoned",
        source="test",
        visibility=ConditionVisibility.VISIBLE,
    )
    sheet = sheet.model_copy(update={"active_conditions": [cond2]})
    _persist_sheet(db_session, sheet)

    result = svc._apply_rpg_sheet_effects(
        db_session,
        (_effect("conditions", "clear_condition", {"identifier": "poisoned"}),),
        sheet,
    )
    assert result.active_conditions == []


# ---------------------------------------------------------------------------
# Atomicity: rollback removes sheet mutation when transaction is aborted
# ---------------------------------------------------------------------------


def test_sheet_mutation_rolls_back_on_transaction_abort(db_session) -> None:  # type: ignore[no-untyped-def]
    """If the session is rolled back after _apply_rpg_sheet_effects, the
    sheet change must not be visible after a fresh load."""
    from afterworlds.persistence.crud.character_sheet import get_dnd5e_sheet

    svc = _make_orchestrator()
    sheet = _make_sheet(current_hp=30, maximum_hp=40)
    _persist_sheet(db_session, sheet)

    # Begin a nested savepoint for rollback testing
    db_session.begin_nested()
    svc._apply_rpg_sheet_effects(
        db_session, (_effect("current_hp", "delta", -15),), sheet
    )
    db_session.rollback()

    # After rollback, current_hp must still be 30
    refetched = get_dnd5e_sheet(db_session, sheet.sheet_id)
    assert refetched is not None
    assert refetched.current_hp == 30
