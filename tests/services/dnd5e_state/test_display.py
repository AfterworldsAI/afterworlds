"""Live display reads through the exact binding; it never fills a family (2b)."""

from __future__ import annotations

from uuid import UUID

from afterworlds.api.visible_state import build_visible_state
from afterworlds.ingestion.mechanical.representation import DieSize
from afterworlds.models.dnd5e_state import ClassLevel
from afterworlds.models.enums import DiceHandling, StoryMode
from afterworlds.models.session import RpgSessionState
from afterworlds.persistence.crud.session_state import create_rpg_session_state
from afterworlds.services.dnd5e_state import service, store
from afterworlds.services.dnd5e_state.authority import current_binding
from afterworlds.services.dnd5e_state.shared_changes import ChangeStatus
from tests.services.dnd5e_state.conftest import (
    NOW,
    Table,
    new_character,
    new_story,
    wizardish,
)
from tests.services.dnd5e_state.test_hold_and_adoption import (
    HOUSE_RULE,
    _activate,
    _request,
)

_CLASSES = (ClassLevel(class_record_key="classes.wizard", level=1, hit_die=DieSize.D6),)


def _displayed(table: Table, **updates: object) -> tuple[UUID, UUID]:
    with table.factory() as s, s.begin():
        story = new_story(s)
        sheet = new_character(s, story)
        binding = current_binding(s, table.package, now=NOW)
        # Stored directly: the bounded projection has no class records, and
        # display reads identities, it does not validate them.
        store.create_character_state(
            s, sheet, wizardish(classes=_CLASSES, **updates), binding, now=NOW
        )
        create_rpg_session_state(
            s,
            RpgSessionState(
                story_id=story,
                character_sheet_id=sheet,
                dice_handling=DiceHandling.AI_ROLLS,
            ),
        )
    return story, sheet


def test_a_current_binding_is_displayed(table: Table) -> None:
    story, _ = _displayed(table)
    with table.factory() as s:
        visible = build_visible_state(s, story, StoryMode.RPG)
    assert visible is not None
    assert visible.character.active_conditions == ()  # recorded as empty


def test_a_stale_binding_is_unavailable_but_its_record_stays_readable(
    table: Table,
) -> None:
    story, sheet = _displayed(table)
    assert _activate(table, _request(table, HOUSE_RULE)).status is ChangeStatus.ACTIVE
    with table.factory() as s:
        assert build_visible_state(s, story, StoryMode.RPG) is None
        # Recorded-binding maintenance remains an explicit path.
        assert service.read_character(s, sheet).state.classes == _CLASSES


def test_unrecorded_conditions_are_not_displayed_as_none(table: Table) -> None:
    story, _ = _displayed(table, conditions=None)
    with table.factory() as s:
        assert build_visible_state(s, story, StoryMode.RPG) is None
