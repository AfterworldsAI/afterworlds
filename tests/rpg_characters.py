"""A turn-ready CRD Issue 2b character for pipeline unit tests (no database)."""

from __future__ import annotations

from uuid import UUID, uuid4, uuid5

from afterworlds.ingestion.mechanical.representation import AbilityScore, DieSize
from afterworlds.models.dnd5e_state import (
    AbilityAdjustment,
    ClassLevel,
    ConditionInstance,
    Dnd5eAbilityScores,
    Dnd5eCharacterState,
    GrantSource,
    HitPoints,
)
from afterworlds.models.rules_package import RulesPackageBinding
from afterworlds.services.dnd5e_state.errors import FailureCode, StateFailure
from afterworlds.services.dnd5e_state.holdings import Holder, HolderKind, ItemInstance
from afterworlds.services.dnd5e_state.store import StoredCharacter
from afterworlds.services.dnd5e_state.turn import TurnCharacter

_NS = UUID("6d5d2f2e-8d2b-4d2c-9a5d-2b1c0e9f7a11")
BINDING = RulesPackageBinding(
    package_uuid=uuid5(_NS, "package"),
    release_version="5.2.1-test",
    mechanical_projection_uuid=uuid5(_NS, "projection"),
    override_set_uuid=uuid5(_NS, "overrides"),
)


def turn_character(
    *,
    dex: int = 16,
    wis: int = 13,
    adjusted: tuple[AbilityScore, ...] = (),
    ready: bool = True,
    hp: tuple[int, int] = (30, 30),
    conditions: tuple[ConditionInstance, ...] = (),
    items: tuple[ItemInstance, ...] = (),
    sheet_id: UUID | None = None,
    story_id: UUID | None = None,
    revision: int = 1,
    name: str = "Test Hero",
) -> TurnCharacter:
    state = Dnd5eCharacterState(
        classes=(
            ClassLevel(class_record_key="classes.rogue", level=5, hit_die=DieSize.D8),
        ),
        ability_scores=Dnd5eAbilityScores(
            strength=10,
            dexterity=dex,
            constitution=14,
            intelligence=12,
            wisdom=wis,
            charisma=10,
        ),
        ability_adjustments=tuple(
            AbilityAdjustment(
                ability=a, amount=2, source=GrantSource(record_key="feats.alert")
            )
            for a in adjusted
        ),
        hit_points=HitPoints(current=hp[0], maximum=hp[1], temporary=0),
        conditions=conditions,
    )
    stored = StoredCharacter(
        sheet_id=sheet_id or uuid4(),
        story_id=story_id or uuid4(),
        character_name=name,
        revision=revision,
        binding=BINDING,
        state=state,
    )
    readiness = (
        ()
        if ready
        else (StateFailure(FailureCode.MISSING_STATE, "feats", "not recorded"),)
    )
    return TurnCharacter(stored, readiness, items)


def item(record_key: str, quantity: int = 1) -> ItemInstance:
    """An item instance held by some character (identity only)."""
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
        applied_poison_record_key=None,
        revision=1,
    )
