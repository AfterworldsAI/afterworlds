"""CRD Issue 15c — saving throws against a typed DC, on the recorded native C5
authority: a character's validated proficiency, a creature's printed column,
and typed condition effects including automatic failure."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from afterworlds.ingestion.mechanical.representation import AbilityScore, ConditionKind
from afterworlds.models.dnd5e_state import ConditionInstance, OriginSelection
from afterworlds.models.enums import ConditionVisibility
from afterworlds.models.rpg import DiceResult
from afterworlds.pipeline.rpg import saves
from afterworlds.pipeline.rpg.capability import AdjudicationRefusal, RefusalKind
from afterworlds.services.dnd5e_state.turn import TurnCharacter, TurnCreature
from tests.pipeline.rpg.test_weapon_attacks import _creature
from tests.rpg_characters import srd_character
from tests.services.dnd5e_state.builders import complete_character, real_index


def _condition(kind: str, level: int | None = None) -> ConditionInstance:
    return ConditionInstance(
        instance_id=kind,
        condition=kind,  # type: ignore[arg-type]
        visibility=ConditionVisibility.VISIBLE,
        level=level,
    )


def _wizard(**state: Any) -> TurnCharacter:
    base = complete_character(real_index(), "classes.wizard", 3)
    return srd_character(base.model_copy(update=state))


def _with_conditions(creature: TurnCreature, *kinds: str) -> TurnCreature:
    state = creature.stored.state.model_copy(
        update={"conditions": tuple(_condition(k) for k in kinds)}
    )
    stored = creature.stored.__class__(**{**creature.stored.__dict__, "state": state})
    return TurnCreature(stored, (), (), creature.index)


def _dice(*raw: int) -> MagicMock:
    dice = MagicMock()

    def roll(expression: str) -> DiceResult:
        chosen = max(raw) if "kh" in expression else min(raw)
        return DiceResult(expression=expression, raw_rolls=raw, chosen=chosen)

    dice.roll.side_effect = roll
    return dice


def _refused(subject: Any, ability: AbilityScore) -> AdjudicationRefusal:
    with pytest.raises(AdjudicationRefusal) as caught:
        saves.prepare(subject, ability, 12, "test")
    return caught.value


def test_a_creature_saves_with_its_printed_column() -> None:
    prepared = saves.prepare(_creature(), AbilityScore.DEXTERITY, 12, "x/y")
    assert (prepared.modifier, prepared.expression) == (2, "1d20")
    assert saves.roll(prepared, _dice(10)).succeeded
    assert not saves.roll(prepared, _dice(9)).succeeded


def test_a_paralyzed_creature_fails_dexterity_saves_without_a_roll() -> None:
    prepared = saves.prepare(
        _with_conditions(_creature(), "paralyzed"), AbilityScore.DEXTERITY, 5, "x"
    )
    dice = _dice(20)
    rolled = saves.roll(prepared, dice)
    assert prepared.automatic_failure == ("glossary.paralyzed/saving_throws_affected",)
    assert not rolled.succeeded and rolled.total is None
    dice.roll.assert_not_called()


def test_restrained_gives_disadvantage_on_dexterity_saves_only() -> None:
    restrained = _with_conditions(_creature(), "restrained")
    dex = saves.prepare(restrained, AbilityScore.DEXTERITY, 12, "x")
    con = saves.prepare(restrained, AbilityScore.CONSTITUTION, 12, "x")
    assert dex.expression == "2d20kl1" and con.expression == "1d20"


def test_a_character_adds_proficiency_only_to_its_validated_saves() -> None:
    wizard = _wizard()
    intelligence = saves.prepare(wizard, AbilityScore.INTELLIGENCE, 12, "x")
    strength = saves.prepare(wizard, AbilityScore.STRENGTH, 12, "x")
    assert intelligence.breakdown.get("proficiency_bonus") == 2
    assert "proficiency_bonus" not in strength.breakdown


def test_a_held_save_contributor_refuses() -> None:
    base = complete_character(real_index(), "classes.barbarian", 2)
    barbarian = srd_character(base)
    refusal = _refused(barbarian, AbilityScore.DEXTERITY)
    assert refusal.kind is RefusalKind.UNSUPPORTED_CAPABILITY
    assert "danger_sense" in refusal.detail


def test_a_contributing_species_trait_refuses() -> None:
    halfling = _wizard(species=OriginSelection(record_key="character_origins.halfling"))
    refusal = _refused(halfling, AbilityScore.WISDOM)
    assert refusal.kind is RefusalKind.UNSUPPORTED_CAPABILITY
    assert "character_origins.halfling" in refusal.detail


def test_exhaustion_refuses_and_unrecorded_conditions_are_missing_state() -> None:
    tired = _wizard(conditions=(_condition("exhaustion", level=1),))
    assert _refused(tired, AbilityScore.WISDOM).kind is (
        RefusalKind.UNSUPPORTED_CAPABILITY
    )
    unknown = _wizard(conditions=None)
    assert _refused(unknown, AbilityScore.WISDOM).kind is RefusalKind.MISSING_STATE


def test_a_condition_limited_trait_refuses_only_against_that_condition() -> None:
    elf = _wizard(species=OriginSelection(record_key="character_origins.elf"))
    assert saves.prepare(elf, AbilityScore.WISDOM, 12, "x").modifier is not None
    with pytest.raises(AdjudicationRefusal) as caught:
        saves.prepare(
            elf, AbilityScore.WISDOM, 12, "x", frozenset({ConditionKind.CHARMED})
        )
    assert "fey_ancestry" in caught.value.detail
