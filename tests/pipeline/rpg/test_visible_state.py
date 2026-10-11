"""Unit tests for RpgVisibleStateService over CRD Issue 2b typed state."""

from __future__ import annotations

from uuid import uuid4

from afterworlds.ingestion.mechanical.representation import ConditionKind
from afterworlds.models.dnd5e_state import ConditionInstance
from afterworlds.models.enums import ConditionVisibility
from afterworlds.pipeline.rpg.visible_state import (
    RpgVisibleStateService,
    identity_label,
)
from afterworlds.services.dnd5e_state.holdings import Holder, HolderKind, ItemInstance
from tests.rpg_characters import turn_character


def _condition(
    kind: ConditionKind, visibility: ConditionVisibility
) -> ConditionInstance:
    return ConditionInstance(
        instance_id=str(uuid4()),
        condition=kind,
        visibility=visibility,
        level=2 if kind is ConditionKind.EXHAUSTION else None,
    )


def _item(record_key: str, quantity: int = 1) -> ItemInstance:
    return ItemInstance(
        item_id=uuid4(),
        story_id=uuid4(),
        record_key=record_key,
        component_key=None,
        quantity=quantity,
        holder=Holder(HolderKind.CHARACTER, uuid4()),
        equipped=False,
        attuned_subject_id=None,
        charges_remaining=None,
        revision=1,
    )


def test_build_maps_the_typed_character() -> None:
    character = turn_character(name="Aldric", hp=(-4, 38))
    visible = RpgVisibleStateService().build(character.stored, ())
    assert visible is not None
    assert visible.character.character_name == "Aldric"
    assert visible.character.character_class == "Rogue 5"
    assert visible.character.level == 5
    # No HP floor is applied on display either (ADR-0003).
    assert (visible.character.current_hp, visible.character.maximum_hp) == (-4, 38)


def test_hidden_conditions_are_excluded_by_construction() -> None:
    character = turn_character(
        conditions=(
            _condition(ConditionKind.POISONED, ConditionVisibility.VISIBLE),
            _condition(ConditionKind.CHARMED, ConditionVisibility.HIDDEN),
            _condition(ConditionKind.EXHAUSTION, ConditionVisibility.VISIBLE),
        )
    )
    visible = RpgVisibleStateService().build(character.stored, ())
    assert visible is not None
    assert visible.character.active_conditions == ("Poisoned", "Exhaustion 2")


def test_inventory_is_the_held_item_instances() -> None:
    character = turn_character()
    visible = RpgVisibleStateService().build(
        character.stored,
        (
            _item("equipment.weapons.war_pick"),
            _item("equipment.adventuring_gear.needles", 50),
        ),
    )
    assert visible is not None
    assert [(i.name, i.quantity) for i in visible.inventory] == [
        ("War Pick", 1),
        ("Needles", 50),
    ]


def test_unrecorded_hit_points_produce_no_snapshot() -> None:
    character = turn_character()
    state = character.stored.state.model_copy(update={"hit_points": None})
    stored = character.stored.__class__(**{**character.stored.__dict__, "state": state})
    assert RpgVisibleStateService().build(stored, ()) is None


def test_identity_labels_read_the_accepted_key() -> None:
    assert identity_label("equipment.weapons.war_pick") == "War Pick"
    assert identity_label("classes.wizard") == "Wizard"
