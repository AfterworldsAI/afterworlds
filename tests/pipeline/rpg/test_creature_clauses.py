"""Creature attack entries' typed clauses — CRD Issue 15c
(codex-c7-recert-coverage-review): every clause is executed or the attack
refuses before any die."""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock

import pytest

from afterworlds.models.dnd5e_state import (
    ActiveTurn,
    SubjectReference,
    TurnCoordination,
)
from afterworlds.models.enums import DiceHandling
from afterworlds.models.rpg import DiceResult
from afterworlds.pipeline.rpg.capability import AdjudicationRefusal, RefusalKind
from afterworlds.services.dnd5e_state.coordination import StoredCoordination
from tests.pipeline.rpg.test_creature_attacks import (
    _bite,
    _medium_wizard,
    _refused,
    _resolve,
    _subjects,
)
from tests.pipeline.rpg.test_weapon_attacks import _creature, _dice


def _attack(creature: Any, target: Any, entry: str, **facts: Any) -> Any:
    return _bite(creature, target, entry=entry, **facts)


def _provenance(record: Any) -> dict[str, Any]:
    return dict(json.loads(record.modifiers_json))


def test_an_unexecuted_clause_refuses_before_any_die() -> None:
    """The Rakshasa's Cursed Touch prints a named curse: it used to roll and
    drop it; now it refuses."""
    rakshasa, wizard = _creature("monsters.rakshasa.rakshasa", hp=110), _medium_wizard()
    caught = _refused(
        RefusalKind.UNSUPPORTED_CAPABILITY,
        _attack(rakshasa, wizard, "Cursed Touch"),
        wizard,
        _subjects(rakshasa),
    )
    assert "Cursed Touch" in caught.detail


@pytest.mark.parametrize(("charged", "prone"), [(True, "applied"), (False, None)])
def test_a_charge_knocks_prone_only_when_the_gamemaster_selects_it(
    charged: bool, prone: str | None
) -> None:
    elephant, wizard = _creature("animals.elephant", hp=76), _medium_wizard()
    record = _resolve(
        _attack(elephant, wizard, "Gore", moved_straight_toward_target=charged),
        wizard,
        _subjects(elephant),
        _dice((18,), (1, 1)),
    )
    clauses = _provenance(record)["clauses"]
    assert clauses["predicate"] is charged
    assert clauses.get("prone") == prone
    assert any(e.target == "prone" for e in record.sheet_effects) is charged


def test_a_charge_entry_needs_the_selection_and_no_other_entry_takes_it() -> None:
    elephant, wolf, wizard = (
        _creature("animals.elephant", hp=76),
        _creature(),
        _medium_wizard(),
    )
    caught = _refused(
        RefusalKind.MISSING_STATE,
        _attack(elephant, wizard, "Gore"),
        wizard,
        _subjects(elephant),
    )
    assert "20+ feet" in caught.detail
    _refused(
        RefusalKind.INVALID_SELECTION,
        _bite(wolf, wizard, moved_straight_toward_target=True),
        wizard,
        _subjects(wolf),
    )


def test_a_charge_against_a_too_large_target_does_not_knock_it_prone() -> None:
    elephant, mammoth = (
        _creature("animals.elephant", hp=76),
        _creature("animals.mammoth", hp=126),
    )
    gorgon = _creature("monsters.gorgon.gorgon", hp=114)  # Large or smaller
    record = _resolve(
        _attack(gorgon, mammoth, "Gore", moved_straight_toward_target=True),
        _medium_wizard(),
        _subjects(gorgon, mammoth, elephant),
        _dice((18,), (5, 5)),
    )
    assert _provenance(record)["clauses"]["predicate"] is False
    assert not any(e.target == "prone" for e in record.sheet_effects)


@pytest.mark.parametrize(("d20s", "dice_expr"), [((5, 18), "4d6"), ((18,), "2d6")])
def test_the_chimeras_bite_does_more_damage_with_advantage(
    d20s: tuple[int, ...], dice_expr: str
) -> None:
    chimera, wizard = _creature("monsters.chimera.chimera", hp=114), _medium_wizard()
    if dice_expr == "4d6":
        # A Prone target within 5 feet: Advantage on the attack roll.
        wizard = _prone(wizard)
    dice = _dice(d20s, (3, 3, 3, 3))
    record = _resolve(
        _attack(chimera, wizard, "Bite"), wizard, _subjects(chimera), dice
    )
    assert dice.calls[1] == dice_expr
    assert _provenance(record)["clauses"]["advantage_damage"] is (dice_expr == "4d6")


def _prone(character: Any) -> Any:
    import dataclasses

    from afterworlds.models.dnd5e_state import ConditionInstance
    from afterworlds.models.enums import ConditionVisibility

    prone = ConditionInstance(
        instance_id="p",
        condition="prone",  # type: ignore[arg-type]
        visibility=ConditionVisibility.VISIBLE,
    )
    state = character.stored.state.model_copy(update={"conditions": (prone,)})
    return dataclasses.replace(
        character, stored=dataclasses.replace(character.stored, state=state)
    )


def test_the_mouthers_bite_kills_a_character_it_reduces_to_0() -> None:
    mouther = _creature("monsters.gibbering_mouther.gibbering_mouther", hp=67)
    wizard = _medium_wizard()
    hp = wizard.stored.state.hit_points
    assert hp is not None
    record = _resolve(
        _attack(mouther, wizard, "Bite"),
        wizard,
        _subjects(mouther),
        _dice((19,), (hp.current, hp.current)),
    )
    provenance = _provenance(record)
    assert provenance["damage"][0]["outcome"] == "died_by_attack"
    assert provenance["clauses"]["dies_at_zero"] is True
    death = next(e for e in record.sheet_effects if e.target == "death_state")
    assert json.loads(death.value_json)["dead"] is True
    # Dead, not dying: no Unconscious; Prone is not applied to the dead.
    assert {e.target for e in record.sheet_effects} >= {"current_hp", "death_state"}
    assert "unconscious" not in {e.target for e in record.sheet_effects}
    assert provenance["clauses"]["prone"] == "target_died"


@pytest.mark.parametrize(
    ("template", "entry", "note"),
    [
        ("monsters.salamander.salamander", "Flame Spear", "returning_weapon"),
        (
            "monsters.dragon_turtle.dragon_turtle",
            "Bite",
            "underwater_fire_resistance_not_granted",
        ),
    ],
)
def test_clauses_without_a_consequence_are_recorded_hit_or_miss(
    template: str, entry: str, note: str
) -> None:
    creature, wizard = _creature(template, hp=200), _medium_wizard()
    for d20 in (19, 2):
        record = _resolve(
            _attack(creature, wizard, entry),
            wizard,
            _subjects(creature),
            _dice((d20,), (1,) * 8),
        )
        no_effect = _provenance(record)["clauses"]["no_effect"]
        if d20 == 2 and note != "returning_weapon":
            # Underwater Resistance concerns damage, which a miss deals none of.
            continue
        assert no_effect == [note]


# ---------------------------------------------------------------------------
# The allosaurus's follow-up Bite
# ---------------------------------------------------------------------------


def _allosaurus_turn(d20s: list[int], *proposals: dict[str, Any]) -> tuple[Any, Any]:
    from afterworlds.pipeline.rpg.adapter import D20RulesSystemAdapter
    from afterworlds.pipeline.rpg.service import RpgAdjudicationPassService
    from tests.pipeline.rpg.test_adjudication_service import (
        _STORY_ID,
        _TURN_ID,
        _FakeProvider,
        _make_assembled,
        _make_session,
    )

    allosaurus = ALLOSAURUS
    me = SubjectReference(kind="creature", subject_id=allosaurus.subject_id)
    document = TurnCoordination(
        active=ActiveTurn(subject=me, instance=2), next_instance=3
    )

    def roll(expression: str) -> DiceResult:
        face = d20s.pop(0) if "d20" in expression else 3
        return DiceResult(expression=expression, raw_rolls=(face,), chosen=face)

    dice = MagicMock()
    dice.roll.side_effect = roll
    result = RpgAdjudicationPassService(
        adapter=D20RulesSystemAdapter(),
        subject_loader=lambda _story, _ref: allosaurus,
        coordination_loader=lambda _story: StoredCoordination(_STORY_ID, 1, document),
    ).adjudicate(
        _make_assembled(),
        _make_session(DiceHandling.AI_ROLLS),
        WIZARD,
        dice,
        provider=_FakeProvider(list(proposals)),
        story_id=_STORY_ID,
        originating_turn_id=_TURN_ID,
    )
    return result, dice


ALLOSAURUS = _creature("animals.allosaurus", hp=51)
WIZARD = _medium_wizard()


def _json(entry: str, **facts: Any) -> dict[str, Any]:
    dumped: dict[str, Any] = _attack(ALLOSAURUS, WIZARD, entry, **facts).model_dump(
        mode="json", exclude_none=True
    )
    return dumped


def test_the_allosaurus_may_bite_after_a_charging_claw_hits() -> None:
    claws = _json("Claws", moved_straight_toward_target=True)
    bite = _json("Bite", follows_up=True)
    result, dice = _allosaurus_turn([18, 18], claws, bite)
    first, second = result.proposals
    assert _provenance(first)["clauses"]["follow_up"] == "may_follow_up"
    assert _provenance(second)["entry"] == "Bite"
    # Claws takes the action; the Bite is part of its hit.
    assert [u.key for u in first.turn_uses] == ["glossary.action/action"]
    assert second.turn_uses == ()


def test_the_follow_up_after_a_miss_rolls_nothing() -> None:
    claws = _json("Claws", moved_straight_toward_target=True)
    bite = _json("Bite", follows_up=True)
    result, dice = _allosaurus_turn([2], claws, bite)
    assert _provenance(result.proposals[1]) == {
        "operation": "creature_attack",
        "follow_up": "not_triggered",
    }
    assert dice.roll.call_count == 1


@pytest.mark.parametrize(
    "first",
    [
        _json("Claws", moved_straight_toward_target=False),  # no charge
        _json("Bite"),  # Bite allows no follow-up
    ],
)
def test_a_follow_up_the_hit_does_not_allow_refuses_before_any_die(
    first: dict[str, Any],
) -> None:
    with pytest.raises(AdjudicationRefusal) as caught:
        _allosaurus_turn([18, 18], first, _json("Bite", follows_up=True))
    assert caught.value.kind is RefusalKind.INVALID_SELECTION


# ---------------------------------------------------------------------------
# Multiattack replacements
# ---------------------------------------------------------------------------


def test_the_dragon_turtle_may_replace_a_bite_with_its_tail() -> None:
    from tests.pipeline.rpg.test_creature_attacks import _multiattack_turn

    turtle = _creature("monsters.dragon_turtle.dragon_turtle", hp=341)
    result, _ = _multiattack_turn(
        turtle, ["Bite", "Tail", "Bite"], target_within_5_feet=False
    )
    assert [_provenance(r)["entry"] for r in result.proposals] == [
        "Bite",
        "Tail",
        "Bite",
    ]
    assert [u.key for u in result.proposals[0].turn_uses] == [
        "glossary.action/action",
        "monsters.dragon_turtle.dragon_turtle/Multiattack",
    ]


@pytest.mark.parametrize(
    "entries",
    [
        ["Tail", "Tail", "Bite"],  # one replacement, once
        ["Bite", "Bite", "Bite", "Tail"],  # replaces, does not add
        ["Tail"],
    ],
)
def test_a_replacement_beyond_the_printed_one_refuses(entries: list[str]) -> None:
    from afterworlds.pipeline.rpg.creature_attacks import check_multiattack

    turtle = _creature("monsters.dragon_turtle.dragon_turtle", hp=341)
    with pytest.raises(AdjudicationRefusal):
        check_multiattack(turtle, entries)


def test_a_replacement_is_certified_by_its_own_part() -> None:
    """The roc's Talons replacement composes, but Talons itself (a grapple)
    is not executed here: the Multiattack refuses before any die."""
    from tests.pipeline.rpg.test_creature_attacks import _multiattack_turn

    roc = _creature("monsters.roc.roc", hp=248)
    with pytest.raises(AdjudicationRefusal) as caught:
        _multiattack_turn(roc, ["Beak", "Talons"])
    assert caught.value.kind is RefusalKind.UNSUPPORTED_CAPABILITY


def test_a_replacement_by_a_save_effect_is_not_an_attack_sequence() -> None:
    from afterworlds.pipeline.rpg.creature_attacks import check_multiattack

    dragon = _creature("monsters.brass_dragons.young_brass_dragon", hp=110)
    check_multiattack(dragon, ["Rend", "Rend", "Rend"])
    with pytest.raises(AdjudicationRefusal):
        check_multiattack(dragon, ["Rend"])  # Sleep Breath is not executed


# ---------------------------------------------------------------------------
# Standing traits, conditional and flat damage, targeting by condition
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("incapacitated", "expression"), [(False, "2d20kl1"), (True, "1d20")]
)
def test_blurred_form_hinders_attacks_against_the_mephit(
    incapacitated: bool, expression: str
) -> None:
    """A trait on attacks against its holder applies when the holder is the
    target (it used to be ignored), unless its circumstance fails."""
    import dataclasses

    from afterworlds.models.dnd5e_state import ConditionInstance
    from afterworlds.models.enums import ConditionVisibility
    from tests.pipeline.rpg.test_weapon_attacks import (
        DAGGER,
        _attacker,
        _proposal,
    )
    from tests.pipeline.rpg.test_weapon_attacks import _subjects as one

    mephit = _creature("monsters.mephits.steam_mephit", hp=21)
    if incapacitated:
        stunned = ConditionInstance(
            instance_id="s",
            condition="incapacitated",  # type: ignore[arg-type]
            visibility=ConditionVisibility.VISIBLE,
        )
        state = mephit.stored.state.model_copy(update={"conditions": (stunned,)})
        mephit = dataclasses.replace(
            mephit, stored=dataclasses.replace(mephit.stored, state=state)
        )
    dice = _dice((10, 15), (2,))
    from afterworlds.pipeline.rpg.adapter import D20RulesSystemAdapter

    D20RulesSystemAdapter().resolve_roll(
        _proposal(mephit, DAGGER, ability="dexterity"),
        _attacker(DAGGER),
        None,
        dice,
        False,
        one(mephit),
    )
    assert dice.calls[0] == expression


def test_the_mephits_own_claw_is_not_refused_for_its_defensive_trait() -> None:
    mephit, wizard = _creature("monsters.mephits.steam_mephit", hp=21), _medium_wizard()
    record = _resolve(
        _attack(mephit, wizard, "Claw"), wizard, _subjects(mephit), _dice((18,), (1,))
    )
    assert record.outcome in ("success", "critical_success")


@pytest.mark.parametrize(
    ("prone", "calls"), [(True, ["2d20kh1", "1d6", "1d4"]), (False, ["1d20", "1d6"])]
)
def test_a_goblin_adds_damage_only_with_advantage(
    prone: bool, calls: list[str]
) -> None:
    goblin, wizard = (
        _creature("monsters.goblins.goblin_warrior", hp=10),
        _medium_wizard(),
    )
    if prone:
        wizard = _prone(wizard)
    dice = _dice((18, 18), (1,))
    record = _resolve(
        _attack(goblin, wizard, "Scimitar"), wizard, _subjects(goblin), dice
    )
    assert dice.calls == calls
    assert _provenance(record)["rider"]["conditional_damage"] is prone


def test_flat_printed_damage_is_its_amount() -> None:
    badger, wizard = _creature("animals.badger", hp=5), _medium_wizard()
    dice = _dice((19,))
    record = _resolve(_attack(badger, wizard, "Bite"), wizard, _subjects(badger), dice)
    assert dice.calls == ["1d20"]  # "1 Piercing damage": no damage die
    assert _provenance(record)["damage"][0]["rolled"] == 1


@pytest.mark.parametrize(("hurt", "expression"), [(True, "2d20kh1"), (False, "1d20")])
def test_blood_frenzy_turns_on_the_targets_recorded_hit_points(
    hurt: bool, expression: str
) -> None:
    sahuagin = _creature("monsters.sahuagin.sahuagin_warrior", hp=22)
    wolf = _creature(hp=11)
    if hurt:
        import dataclasses

        hp = wolf.stored.state.hit_points
        assert hp is not None
        state = wolf.stored.state.model_copy(
            update={"hit_points": hp.model_copy(update={"current": 5})}
        )
        wolf = dataclasses.replace(
            wolf, stored=dataclasses.replace(wolf.stored, state=state)
        )
    dice = _dice((18, 18), (1,))
    _resolve(
        _attack(sahuagin, wolf, "Claw"),
        _medium_wizard(),
        _subjects(sahuagin, wolf),
        dice,
    )
    assert dice.calls[0] == expression


def test_pummel_targets_only_a_creature_its_source_grapples() -> None:
    from afterworlds.models.enums import RollVisibility
    from afterworlds.models.rpg import CreatureSaveEffectSelection, RollProposal
    from tests.pipeline.rpg.test_creature_attacks import _ref
    from tests.pipeline.rpg.test_creature_roster import _scenario

    glabrezu, wizard = _creature("monsters.glabrezu.glabrezu", hp=174), _medium_wizard()

    def pummel(target: Any) -> RollProposal:
        return RollProposal(
            check_label="Pummel",
            subsystem_tag="save",
            visibility=RollVisibility.SHOWN,
            operation="creature_save_effect",
            creature_save_effect=CreatureSaveEffectSelection(
                source=_ref(glabrezu),
                entry="Pummel",
                targets=(_ref(target),),
                auras_in_range=(),
            ),
        )

    _refused(RefusalKind.INVALID_SELECTION, pummel(wizard), wizard, _subjects(glabrezu))
    held = _scenario("monsters.glabrezu.glabrezu#4:Pummel", glabrezu, wizard)
    from afterworlds.pipeline.rpg.adapter import D20RulesSystemAdapter

    D20RulesSystemAdapter().require_supported(pummel(held), held, _subjects(glabrezu))


def test_an_optional_use_of_another_entry_is_simply_not_made() -> None:
    from afterworlds.pipeline.rpg.creature_attacks import check_multiattack

    erinyes = _creature("monsters.erinyes.erinyes", hp=178)
    check_multiattack(erinyes, ["Withering Sword"] * 3)
    with pytest.raises(AdjudicationRefusal):
        check_multiattack(erinyes, ["Withering Sword"] * 3 + ["Entangling Rope"])
