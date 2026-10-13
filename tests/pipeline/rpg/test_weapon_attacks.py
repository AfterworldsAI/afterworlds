"""CRD Issue 15c — weapon attacks against independent targets, on the
recorded native C5 authority.

Every number comes from the attacker's and the target's own exact bindings,
recorded state and the GameMaster's approved contextual facts; every refusal
is typed and happens before any die is rolled.
"""

from __future__ import annotations

import dataclasses
import json
from typing import Any
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from afterworlds.models.dnd5e_state import (
    ConditionInstance,
    CreatureState,
    DeathState,
    FeatSelection,
    GrantSource,
    HitPoints,
    SubjectReference,
    ZeroHitPointTreatment,
)
from afterworlds.models.enums import ConditionVisibility, RollVisibility
from afterworlds.models.rpg import (
    DiceResult,
    HandFacts,
    HeldItem,
    RollProposal,
    SubjectRef,
    WeaponAttackSelection,
)
from afterworlds.pipeline.rpg import attacks
from afterworlds.pipeline.rpg.adapter import D20RulesSystemAdapter
from afterworlds.pipeline.rpg.capability import AdjudicationRefusal, RefusalKind
from afterworlds.services.dnd5e_state.holdings import ItemInstance
from afterworlds.services.dnd5e_state.store import StoredCreature
from afterworlds.services.dnd5e_state.turn import TurnCharacter, TurnCreature
from tests.rpg_characters import item, srd_character
from tests.services.dnd5e_state.builders import complete_character, real_index


def _wielded(record: str) -> ItemInstance:
    return dataclasses.replace(item(record), equipped=True)


CLUB = _wielded("equipment.weapons.club")
DAGGER = _wielded("equipment.weapons.dagger")
GREATCLUB = _wielded("equipment.weapons.greatclub")
LONGBOW = _wielded("equipment.weapons.longbow")
SHIELD = _wielded("equipment.armor.shield")
MONSTER = ZeroHitPointTreatment(subject="monster")


def _creature(
    template: str = "animals.wolf",
    hp: int = 11,
    treatment: ZeroHitPointTreatment | None = MONSTER,
) -> TurnCreature:
    index = real_index()
    state = CreatureState(
        template_record_key=template,
        hit_points=HitPoints(current=hp, maximum=hp, temporary=0),
        conditions=(),
        active_effects=(),
        death_state=DeathState(successes=0, failures=0, stable=False, dead=False),
        zero_hit_point_treatment=treatment,
    )
    stored = StoredCreature(
        creature_id=uuid4(),
        story_id=uuid4(),
        display_name="Wolf",
        revision=1,
        binding=index.binding,
        state=state,
    )
    return TurnCreature(stored, (), (), index)


def _attacker(*items: ItemInstance, **state: Any) -> TurnCharacter:
    base = complete_character(real_index(), "classes.wizard", 3)
    return srd_character(base.model_copy(update=state), items=items)


def hands_for(*weapons: ItemInstance, two_handed: bool = False) -> HandFacts:
    """Hand facts holding *weapons*: a lone Two-Handed (or two-handed
    Versatile) weapon in both hands, otherwise one hand each."""
    from afterworlds.ingestion.mechanical.representation import (
        WeaponProperty,
        WeaponPropertyFact,
    )
    from afterworlds.pipeline.rpg.defense import facts_of

    def grip(weapon: ItemInstance) -> int:
        props = {
            f.weapon_property
            for f in facts_of(real_index(), weapon.record_key)
            if isinstance(f, WeaponPropertyFact)
        }
        both = two_handed or WeaponProperty.TWO_HANDED in props
        return 2 if both and len(weapons) == 1 else 1

    held = tuple(HeldItem(item_id=w.item_id, hands=grip(w)) for w in weapons)
    return HandFacts(held=held, free_hands=2 - sum(h.hands for h in held))  # type: ignore[arg-type]


def _proposal(
    target: TurnCreature | TurnCharacter, weapon: ItemInstance = CLUB, **facts: Any
) -> RollProposal:
    kind = "creature" if isinstance(target, TurnCreature) else "character"
    selection = {
        "weapon_item_id": weapon.item_id,
        "target": SubjectRef(kind=kind, subject_id=target.subject_id),
        "range": "within_reach",
        "cover": "none",
        "attacker_light": "bright",
        "target_light": "bright",
        "hands": hands_for(weapon, two_handed=bool(facts.get("two_handed"))),
        **facts,
    }
    return RollProposal(
        check_label="Club attack",
        subsystem_tag="attack",
        visibility=RollVisibility.SHOWN,
        operation="weapon_attack",
        weapon_attack=WeaponAttackSelection(**selection),
    )


def _dice(attack: tuple[int, ...], damage: tuple[int, ...] = ()) -> MagicMock:
    dice = MagicMock()
    calls: list[str] = []

    def roll(expression: str) -> DiceResult:
        calls.append(expression)
        if "d20" in expression:
            chosen = max(attack) if "kh" in expression else min(attack)
            return DiceResult(expression=expression, raw_rolls=attack, chosen=chosen)
        return DiceResult(expression=expression, raw_rolls=damage, chosen=sum(damage))

    dice.roll.side_effect = roll
    dice.calls = calls
    return dice


def _subjects(target: TurnCreature | TurnCharacter) -> dict[tuple[str, str], Any]:
    return {attacks.subject_key(target): target}


def _resolve(attacker: TurnCharacter, proposal: RollProposal, dice: MagicMock) -> Any:
    target = proposal.weapon_attack
    assert target is not None
    return D20RulesSystemAdapter().resolve_roll(
        proposal,
        attacker,
        None,
        dice,
        gm_cheating=False,
        subjects=_SUBJECTS,
    )


_SUBJECTS: dict[tuple[str, str], Any] = {}


def _run(
    attacker: TurnCharacter, target: Any, proposal: RollProposal, dice: MagicMock
) -> Any:
    _SUBJECTS.clear()
    _SUBJECTS.update(_subjects(target))
    return _resolve(attacker, proposal, dice)


def _refused(
    kind: RefusalKind, attacker: TurnCharacter, target: Any, proposal: RollProposal
) -> AdjudicationRefusal:
    dice = MagicMock()
    with pytest.raises(AdjudicationRefusal) as caught:
        _run(attacker, target, proposal, dice)
    dice.roll.assert_not_called()
    assert caught.value.kind is kind, caught.value
    return caught.value


# ---------------------------------------------------------------------------
# Positive coverage
# ---------------------------------------------------------------------------


def test_a_hit_damages_the_creature_target_by_its_own_authority() -> None:
    """Wizard 3, Str 8 (-1), proficient with Simple weapons (PB 2): Club 1d4
    Bludgeoning against a Wolf (AC 12, HP 11)."""
    wolf = _creature()
    dice = _dice((15,), (3,))
    record = _run(_attacker(CLUB), wolf, _proposal(wolf), dice)
    assert dice.calls == ["1d20", "1d4"]
    assert (record.total, record.dc, record.outcome) == (16, 12, "success")
    (effect,) = record.sheet_effects
    assert (effect.target, effect.subject_kind, effect.subject_id) == (
        "current_hp",
        "creature",
        wolf.subject_id,
    )
    assert json.loads(effect.value_json) == 9  # 11 - (3 - 1)
    provenance = json.loads(record.modifiers_json)
    assert provenance["breakdown"] == {"strength_modifier": -1, "proficiency_bonus": 2}
    assert provenance["contextual_facts"]["range"] == "within_reach"


def test_a_miss_changes_nothing() -> None:
    wolf = _creature()
    record = _run(_attacker(CLUB), wolf, _proposal(wolf), _dice((5,)))
    assert (record.outcome, record.sheet_effects) == ("failure", ())


def test_a_natural_20_is_a_critical_hit_doubling_the_damage_dice() -> None:
    wolf = _creature()
    dice = _dice((20,), (2, 3))
    record = _run(_attacker(CLUB), wolf, _proposal(wolf), dice)
    assert dice.calls == ["1d20", "2d4"]
    assert record.outcome == "critical_success"
    assert json.loads(record.sheet_effects[0].value_json) == 11 - (5 - 1)


def test_a_natural_1_misses_whatever_the_total() -> None:
    wolf = _creature()
    record = _run(_attacker(CLUB), wolf, _proposal(wolf), _dice((1,)))
    assert record.outcome == "failure"


def test_cover_raises_the_targets_ac_by_its_typed_bonus() -> None:
    wolf = _creature()
    record = _run(
        _attacker(CLUB), wolf, _proposal(wolf, cover="three_quarters"), _dice((15,))
    )
    assert record.dc == 17 and record.outcome == "failure"


def test_vulnerability_doubles_the_damage() -> None:
    skeleton = _creature("monsters.skeletons.skeleton", hp=13)
    dice = _dice((18,), (4,))
    record = _run(_attacker(CLUB), skeleton, _proposal(skeleton), dice)
    damage = json.loads(record.modifiers_json)["damage"]
    assert (damage["rolled"], damage["taken"]) == (3, 6)
    assert damage["responses"] == ["vulnerability"]


def test_a_monster_reduced_to_0_dies_and_a_character_style_one_falls() -> None:
    wolf = _creature(hp=2)
    record = _run(_attacker(CLUB), wolf, _proposal(wolf), _dice((15,), (4,)))
    by_target = {e.target: json.loads(e.value_json) for e in record.sheet_effects}
    assert by_target["current_hp"] == 0
    assert by_target["death_state"]["dead"] is True
    pet = _creature(
        hp=2,
        treatment=ZeroHitPointTreatment(
            subject="monster", gamemaster_exception="treat_as_character"
        ),
    )
    record = _run(_attacker(CLUB), pet, _proposal(pet), _dice((15,), (4,)))
    targets = [e.target for e in record.sheet_effects]
    assert targets == ["current_hp", "unconscious", "death_state"]
    assert (
        json.loads(record.modifiers_json)["damage"]["outcome"]
        == "unconscious_and_dying"
    )


def test_a_versatile_weapon_in_two_hands_uses_its_typed_die() -> None:
    quarterstaff = _wielded("equipment.weapons.quarterstaff")
    wolf = _creature()
    dice = _dice((15,), (5,))
    _run(
        _attacker(quarterstaff),
        wolf,
        _proposal(wolf, quarterstaff, two_handed=True),
        dice,
    )
    assert dice.calls == ["1d20", "1d8"]


@pytest.mark.parametrize(
    ("enemy_state", "disadvantaged"), [("", True), ("unconscious", False)]
)
def test_a_thrown_dagger_beside_a_named_enemy_has_disadvantage(
    enemy_state: str, disadvantaged: bool
) -> None:
    """Close combat names its enemy, read and checked: an Incapacitated
    enemy imposes nothing (``play.combat/close_combat``)."""
    wolf, enemy = _creature(), _creature()
    if enemy_state:
        state = enemy.stored.state.model_copy(
            update={"conditions": (_condition(enemy_state),)}
        )
        enemy = dataclasses.replace(
            enemy, stored=dataclasses.replace(enemy.stored, state=state)
        )
    proposal = _proposal(
        wolf,
        DAGGER,
        range="within_normal_range",
        thrown=True,
        ability="dexterity",
        hostiles_within_5_feet=(
            SubjectRef(kind="creature", subject_id=enemy.subject_id),
        ),
    )
    dice = _dice((4, 17), (2,))
    record = D20RulesSystemAdapter().resolve_roll(
        proposal,
        _attacker(DAGGER),
        None,
        dice,
        False,
        {**_subjects(wolf), **_subjects(enemy)},
    )
    assert (dice.calls[0] == "2d20kl1") is disadvantaged
    sources = json.loads(record.modifiers_json)["disadvantage_sources"]
    assert (sources == ["play.combat/close_combat"]) is disadvantaged


def test_an_unnamed_or_unread_enemy_refuses() -> None:
    wolf = _creature()
    facts = {"range": "within_normal_range", "thrown": True, "ability": "dexterity"}
    _refused(
        RefusalKind.MISSING_STATE,
        _attacker(DAGGER),
        wolf,
        _proposal(wolf, DAGGER, hostiles_within_5_feet=None, **facts),
    )
    ghost = SubjectRef(kind="creature", subject_id=uuid4())
    _refused(
        RefusalKind.MISSING_STATE,
        _attacker(DAGGER),
        wolf,
        _proposal(wolf, DAGGER, hostiles_within_5_feet=(ghost,), **facts),
    )


# ---------------------------------------------------------------------------
# Refusals, each before any die
# ---------------------------------------------------------------------------


def test_an_unrecorded_zero_hp_treatment_refuses_before_rolling() -> None:
    wolf = _creature(treatment=None)
    _refused(RefusalKind.MISSING_STATE, _attacker(CLUB), wolf, _proposal(wolf))


@pytest.mark.parametrize(
    ("kind", "facts"),
    [
        (RefusalKind.INVALID_SELECTION, {"range": "within_normal_range"}),
        (RefusalKind.INVALID_SELECTION, {"cover": "total"}),
        (RefusalKind.UNSUPPORTED_CAPABILITY, {"target_light": "darkness"}),
        (RefusalKind.INVALID_SELECTION, {"two_handed": True}),
        (RefusalKind.INVALID_SELECTION, {"thrown": True}),
    ],
    ids=[
        "melee-at-range",
        "total-cover",
        "darkness",
        "club-not-versatile",
        "club-not-thrown",
    ],
)
def test_an_invalid_attack_selection_refuses(
    kind: RefusalKind, facts: dict[str, Any]
) -> None:
    wolf = _creature()
    _refused(kind, _attacker(CLUB), wolf, _proposal(wolf, **facts))


def test_a_finesse_attack_names_its_ability() -> None:
    wolf = _creature()
    _refused(
        RefusalKind.INVALID_SELECTION, _attacker(DAGGER), wolf, _proposal(wolf, DAGGER)
    )


def test_hand_facts_must_fit_the_weapon_and_two_hands() -> None:
    wolf = _creature()
    shielded = _attacker(GREATCLUB, SHIELD)
    both = HandFacts(
        held=(
            HeldItem(item_id=GREATCLUB.item_id, hands=2),
            HeldItem(item_id=SHIELD.item_id, hands=1),
        ),
        free_hands=0,
    )
    one = HandFacts(held=(HeldItem(item_id=GREATCLUB.item_id, hands=1),), free_hands=1)
    for hands in (both, one):  # three hands; a Two-Handed weapon in one
        _refused(
            RefusalKind.INVALID_SELECTION,
            shielded,
            wolf,
            _proposal(wolf, GREATCLUB, hands=hands),
        )


def test_loading_a_one_handed_ammunition_weapon_needs_a_free_hand() -> None:
    wolf = _creature()
    crossbow = _wielded("equipment.weapons.hand_crossbow")
    facts = {
        "range": "within_normal_range",
        "hostiles_within_5_feet": (),
    }
    full = HandFacts(
        held=(
            HeldItem(item_id=crossbow.item_id, hands=1),
            HeldItem(item_id=DAGGER.item_id, hands=1),
        ),
        free_hands=0,
    )
    attacker = _attacker(crossbow, DAGGER)
    _refused(
        RefusalKind.INVALID_SELECTION,
        attacker,
        wolf,
        _proposal(wolf, crossbow, hands=full, **facts),
    )
    # With a hand free, it waits only on the ammunition authority (C7).
    _refused(
        RefusalKind.MISSING_AUTHORITY,
        attacker,
        wolf,
        _proposal(wolf, crossbow, **facts),
    )


def test_an_ammunition_weapon_refuses_without_a_typed_ammunition_item() -> None:
    wolf = _creature()
    proposal = _proposal(
        wolf, LONGBOW, range="within_normal_range", hostiles_within_5_feet=()
    )
    refusal = _refused(
        RefusalKind.MISSING_AUTHORITY, _attacker(LONGBOW), wolf, proposal
    )
    assert "arrow" in refusal.detail


def test_an_attack_contributor_refuses() -> None:
    """Savage Attacker (Soldier's Origin feat) rerolls weapon damage."""
    feat = FeatSelection(
        feat_record_key="feats.savage_attacker",
        source=GrantSource(
            record_key="character_origins.soldier", component_key="feat"
        ),
    )
    wolf = _creature()
    refusal = _refused(
        RefusalKind.UNSUPPORTED_CAPABILITY,
        _attacker(CLUB, feats=(feat,)),
        wolf,
        _proposal(wolf),
    )
    assert "feats.savage_attacker" in refusal.detail


def test_a_weapon_not_held_or_not_in_hand_refuses() -> None:
    wolf = _creature()
    _refused(RefusalKind.MISSING_STATE, _attacker(), wolf, _proposal(wolf))
    _refused(
        RefusalKind.MISSING_STATE, _attacker(CLUB), wolf, _proposal(wolf, hands=None)
    )
    empty = HandFacts(held=(), free_hands=2)
    _refused(
        RefusalKind.INVALID_SELECTION,
        _attacker(CLUB),
        wolf,
        _proposal(wolf, hands=empty),
    )
    # Equipped is not proof of holding, and not required: the facts are.
    sheathed = dataclasses.replace(CLUB, equipped=False)
    record = _run(
        _attacker(sheathed), wolf, _proposal(wolf, sheathed), _dice((15,), (3,))
    )
    assert record.outcome == "success"


def test_an_unread_target_refuses() -> None:
    wolf = _creature()
    with pytest.raises(AdjudicationRefusal) as caught:
        D20RulesSystemAdapter().resolve_roll(
            _proposal(wolf), _attacker(CLUB), None, MagicMock(), gm_cheating=False
        )
    assert caught.value.kind is RefusalKind.MISSING_STATE


def test_a_non_proficient_attack_adds_no_proficiency_bonus() -> None:
    """Wizards have no Martial weapon training: a Longsword adds Str only."""
    longsword = _wielded("equipment.weapons.longsword")
    wolf = _creature()
    record = _run(_attacker(longsword), wolf, _proposal(wolf, longsword), _dice((10,)))
    assert json.loads(record.modifiers_json)["breakdown"] == {"strength_modifier": -1}


def test_the_writer_never_sees_the_targets_armor_class() -> None:
    wolf = _creature()
    record = _run(_attacker(CLUB), wolf, _proposal(wolf), _dice((15,), (3,)))
    view = D20RulesSystemAdapter().to_writer_view(record)
    assert view.dc is None and "12" not in view.player_facing_summary
    assert view.outcome == "success"


# ---------------------------------------------------------------------------
# Conditions: every component is applied or reviewed; implied conditions
# (Unconscious gives Incapacitated and Prone) bind too
# ---------------------------------------------------------------------------


def _condition(kind: str, referent: Any = None) -> ConditionInstance:
    return ConditionInstance(
        instance_id=f"c-{kind}",
        condition=kind,  # type: ignore[arg-type]
        visibility=ConditionVisibility.VISIBLE,
        referent=referent,
    )


def _afflicted(creature: TurnCreature, *kinds: str) -> TurnCreature:
    state = creature.stored.state.model_copy(
        update={"conditions": tuple(_condition(k) for k in kinds)}
    )
    return dataclasses.replace(
        creature, stored=dataclasses.replace(creature.stored, state=state)
    )


def test_a_hit_on_an_unconscious_target_from_within_5_feet_is_critical() -> None:
    wolf = _afflicted(_creature(hp=40), "unconscious")
    dice = _dice((12, 3), (3, 1))
    record = _run(_attacker(CLUB), wolf, _proposal(wolf), dice)
    provenance = json.loads(record.modifiers_json)
    assert record.outcome == "critical_success"
    assert dice.calls == ["2d20kh1", "2d4"]
    assert provenance["automatic_critical"] == [
        "glossary.unconscious/automatic_critical_hits"
    ]
    # Unconscious's own Advantage, and implied Prone's from within 5 feet.
    assert set(provenance["advantage_sources"]) == {
        "glossary.unconscious/attacks_affected",
        "glossary.prone/attacks_against_affected",
    }


def test_a_prone_target_beyond_5_feet_imposes_disadvantage() -> None:
    wolf = _afflicted(_creature(), "prone")
    proposal = _proposal(
        wolf,
        DAGGER,
        range="within_normal_range",
        thrown=True,
        hostiles_within_5_feet=(),
        ability="dexterity",
        target_within_5_feet=False,
    )
    record = _run(_attacker(DAGGER), wolf, proposal, _dice((15, 2), (3,)))
    assert json.loads(record.modifiers_json)["disadvantage_sources"] == [
        "glossary.prone/attacks_against_affected"
    ]


def test_a_rule_that_turns_on_5_feet_refuses_without_the_fact() -> None:
    wolf = _afflicted(_creature(), "prone")
    proposal = _proposal(
        wolf,
        DAGGER,
        range="within_normal_range",
        thrown=True,
        hostiles_within_5_feet=(),
        ability="dexterity",
    )
    _refused(RefusalKind.MISSING_STATE, _attacker(DAGGER), wolf, proposal)


def test_a_5_foot_melee_attack_is_within_5_feet() -> None:
    wolf = _creature()
    proposal = _proposal(wolf, target_within_5_feet=False)
    _refused(RefusalKind.INVALID_SELECTION, _attacker(CLUB), wolf, proposal)


def test_an_incapacitated_attacker_cannot_attack() -> None:
    wolf = _creature()
    stunned = _attacker(CLUB, conditions=(_condition("stunned"),))
    refusal = _refused(RefusalKind.INVALID_SELECTION, stunned, wolf, _proposal(wolf))
    assert "glossary.incapacitated/inactive" in refusal.detail


def test_a_charmed_attacker_cannot_attack_its_charmer() -> None:
    wolf = _creature()
    charmer = SubjectReference(kind="creature", subject_id=wolf.subject_id)
    charmed = _attacker(CLUB, conditions=(_condition("charmed", charmer),))
    _refused(RefusalKind.INVALID_SELECTION, charmed, wolf, _proposal(wolf))
    unknown = _attacker(CLUB, conditions=(_condition("charmed"),))
    _refused(RefusalKind.MISSING_STATE, unknown, wolf, _proposal(wolf))


def test_damage_to_a_petrified_target_refuses() -> None:
    wolf = _afflicted(_creature(), "petrified")
    _refused(RefusalKind.UNSUPPORTED_CAPABILITY, _attacker(CLUB), wolf, _proposal(wolf))
