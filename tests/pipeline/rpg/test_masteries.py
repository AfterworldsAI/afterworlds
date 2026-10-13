"""CRD Issue 15c — weapon masteries, on the recorded native C5 authority.

A mastery applies only when a validated Weapon Mastery choice covers the
weapon; optional ones only when selected. Standing effects (Sap, Slow, Vex)
are subject-addressed active effects bounded by the wielder's turn edges and
spent where they apply; every other roll still refuses unexecuted effects.
"""

from __future__ import annotations

import dataclasses
import json
from typing import Any
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from afterworlds.models.dnd5e_state import (
    ActiveEffect,
    ActiveTurn,
    EffectEnd,
    GrantSource,
    RecordChoice,
    SubjectReference,
    TurnBoundEnd,
    TurnCoordination,
    WeaponProficiencyGrant,
)
from afterworlds.models.enums import RollVisibility
from afterworlds.models.rpg import DiceResult, RollProposal, SubjectRef
from afterworlds.pipeline.rpg import checks
from afterworlds.pipeline.rpg.adapter import D20RulesSystemAdapter
from afterworlds.pipeline.rpg.capability import AdjudicationRefusal, RefusalKind
from afterworlds.services.dnd5e_state.holdings import ItemInstance
from afterworlds.services.dnd5e_state.turn import TurnCharacter, TurnCreature
from tests.pipeline.rpg.test_weapon_attacks import (
    _attacker,
    _creature,
    _dice,
    _proposal,
    _refused,
    _run,
)
from tests.rpg_characters import item, srd_character
from tests.services.dnd5e_state.builders import choice, complete_character, real_index


def _wielded(record: str) -> ItemInstance:
    return dataclasses.replace(item(f"equipment.weapons.{record}"), equipped=True)


MACE, STAFF, HANDAXE = _wielded("mace"), _wielded("quarterstaff"), _wielded("handaxe")
CLUB, GREATCLUB, DAGGER = _wielded("club"), _wielded("greatclub"), _wielded("dagger")
GREATSWORD = _wielded("greatsword")


def _fighter(*kinds: str, items: tuple[ItemInstance, ...] = ()) -> TurnCharacter:
    index = real_index()
    base = complete_character(index, "classes.fighter", 1)
    mastery = choice(
        index,
        "wm",
        "classes.fighter.weapon_mastery",
        "weapon_mastery",
        *(RecordChoice(record_key=f"equipment.weapons.{k}") for k in kinds),
    )
    martial = WeaponProficiencyGrant(
        category="martial",  # type: ignore[arg-type]
        source=GrantSource(record_key="classes.fighter", component_key="core_traits"),
    )
    state = base.model_copy(
        update={
            "choices": (*(base.choices or ()), mastery),
            "weapon_proficiencies": (*(base.weapon_proficiencies or ()), martial),
        }
    )
    return srd_character(state, items=items)


def _effects(record: Any, operation: str) -> list[Any]:
    return [
        json.loads(e.value_json)
        for e in record.sheet_effects
        if e.operation == operation
    ]


def _mastery(record: Any) -> Any:
    return json.loads(record.modifiers_json)["mastery"]


def _with_effect(subject: Any, effect: ActiveEffect) -> Any:
    state = subject.stored.state.model_copy(
        update={"active_effects": (*subject.stored.state.active_effects, effect)}
    )
    return dataclasses.replace(
        subject, stored=dataclasses.replace(subject.stored, state=state)
    )


def _standing(
    mastery: str, of: Any, boundary: str, targets: Any = None, created: Any = None
) -> ActiveEffect:
    kind = "creature" if isinstance(of, TurnCreature) else "character"
    return ActiveEffect(
        instance_id=f"{mastery}-1",
        source=GrantSource(
            record_key=f"equipment.weapons.{mastery}", component_key=mastery
        ),
        concentration=False,
        targets=targets,
        ends=EffectEnd(
            kind="special",  # type: ignore[arg-type]
            turn=TurnBoundEnd(
                boundary=boundary,  # type: ignore[arg-type]
                of=SubjectReference(kind=kind, subject_id=of.subject_id),
                created_in_turn=created,
            ),
        ),
    )


# ---------------------------------------------------------------------------
# Who may use a mastery
# ---------------------------------------------------------------------------


def test_a_mastery_needs_a_validated_choice_covering_the_weapon() -> None:
    wolf = _creature(hp=40)
    no_mastery = _fighter("mace", items=(STAFF,))
    _refused(
        RefusalKind.INVALID_SELECTION,
        no_mastery,
        wolf,
        _proposal(wolf, STAFF, mastery=True),
    )
    # Without a choice, the weapon's non-optional mastery simply doesn't apply.
    record = _run(_attacker(MACE), wolf, _proposal(wolf, MACE), _dice((15,), (3,)))
    assert _mastery(record) is None


def test_more_weapon_kinds_than_the_level_allows_refuses() -> None:
    wolf = _creature(hp=40)
    greedy = _fighter("mace", "club", "dagger", "spear", items=(MACE,))
    _refused(RefusalKind.INVALID_SELECTION, greedy, wolf, _proposal(wolf, MACE))


def test_nick_waits_on_the_action_economy_classification() -> None:
    wolf = _creature(hp=40)
    fighter = _fighter("dagger", items=(DAGGER,))
    refusal = _refused(
        RefusalKind.UNSUPPORTED_CAPABILITY,
        fighter,
        wolf,
        _proposal(wolf, DAGGER, mastery=True, ability="strength"),
    )
    assert "nick" in refusal.detail


# ---------------------------------------------------------------------------
# Each mastery
# ---------------------------------------------------------------------------


def test_sap_leaves_the_target_a_disadvantage_until_the_wielders_next_turn() -> None:
    wolf = _creature(hp=40)
    fighter = _fighter("mace", items=(MACE,))
    record = _run(fighter, wolf, _proposal(wolf, MACE), _dice((15,), (3,)))
    (effect,) = _effects(record, "apply_effect")
    assert effect["source"]["record_key"] == "equipment.weapons.sap"
    assert effect["ends"]["turn"]["boundary"] == "start"
    assert effect["ends"]["turn"]["of"]["subject_id"] == str(fighter.subject_id)


def test_a_sapped_attacker_rolls_with_disadvantage_and_spends_it() -> None:
    wolf = _creature(hp=40)
    sapped = _with_effect(_attacker(CLUB), _standing("sap", wolf, "start"))
    record = _run(sapped, wolf, _proposal(wolf, CLUB), _dice((15, 4), (3,)))
    provenance = json.loads(record.modifiers_json)
    assert provenance["disadvantage_sources"] == ["equipment.weapons.sap/sap"]
    assert _effects(record, "end_effect") == [{"instance_id": "sap-1"}]


def test_vex_gives_advantage_against_that_creature_only() -> None:
    wolf, other = _creature(hp=40), _creature(hp=40)
    target = SubjectReference(kind="creature", subject_id=wolf.subject_id)
    vexing = _with_effect(_attacker(CLUB), _standing("vex", wolf, "end", (target,)))
    against = _run(vexing, wolf, _proposal(wolf, CLUB), _dice((4, 15), (3,)))
    assert json.loads(against.modifiers_json)["advantage_sources"] == [
        "equipment.weapons.vex/vex"
    ]
    elsewhere = _run(vexing, other, _proposal(other, CLUB), _dice((15,), (3,)))
    assert json.loads(elsewhere.modifiers_json)["advantage_sources"] == []
    assert _effects(elsewhere, "end_effect") == []


def test_vex_is_applied_to_the_wielder_on_a_damaging_hit() -> None:
    wolf = _creature(hp=40)
    fighter = _fighter("handaxe", items=(HANDAXE,))
    record = _run(fighter, wolf, _proposal(wolf, HANDAXE), _dice((15,), (3,)))
    (effect,) = [e for e in record.sheet_effects if e.operation == "apply_effect"]
    assert effect.subject_id == fighter.subject_id
    assert json.loads(effect.value_json)["targets"][0]["subject_id"] == str(
        wolf.subject_id
    )


@pytest.mark.parametrize(("save", "prone"), [(3, True), (20, False)])
def test_topple_forces_a_constitution_save_or_prone(save: int, prone: bool) -> None:
    wolf = _creature(hp=40)
    fighter = _fighter("quarterstaff", items=(STAFF,))
    d20s = [15, save]  # the attack roll, then the Constitution save

    def roll(expression: str) -> DiceResult:
        face = d20s.pop(0) if "d20" in expression else 3
        return DiceResult(expression=expression, raw_rolls=(face,), chosen=face)

    dice = MagicMock()
    dice.roll.side_effect = roll
    record = _run(fighter, wolf, _proposal(wolf, STAFF, mastery=True), dice)
    result = _mastery(record)
    assert result["save"]["ability"] == "constitution"
    # DC 8 + the attack's ability modifier + Proficiency Bonus; the Wolf saves
    # with its printed Constitution column, +1.
    strength = json.loads(record.modifiers_json)["breakdown"]["strength_modifier"]
    assert result["save"]["dc"] == 8 + strength + 2
    assert result["save"]["modifier"] == 1
    assert bool(_effects(record, "apply_condition")) is prone


def test_graze_deals_the_ability_modifier_on_a_miss() -> None:
    wolf = _creature(hp=40)
    fighter = _fighter("greatsword", items=(GREATSWORD,))
    record = _run(fighter, wolf, _proposal(wolf, GREATSWORD, mastery=True), _dice((2,)))
    result = _mastery(record)
    assert record.outcome == "failure" and result["result"] == "damaged"
    modifier = json.loads(record.modifiers_json)["breakdown"]["strength_modifier"]
    assert result["damage"]["taken"] == max(0, modifier)


def test_push_records_the_selected_distance_and_size_bounds_it() -> None:
    wolf = _creature(hp=40)
    fighter = _fighter("greatclub", items=(GREATCLUB,))
    record = _run(
        fighter,
        wolf,
        _proposal(wolf, GREATCLUB, mastery=True, push_ft=5),
        _dice((15,), (3,)),
    )
    assert _mastery(record) == {"mastery": "push", "result": "pushed", "feet": 5}
    elephant = _creature("animals.elephant", hp=40)
    _refused(
        RefusalKind.INVALID_SELECTION,
        fighter,
        elephant,
        _proposal(elephant, GREATCLUB, mastery=True, push_ft=5),
    )


def test_slow_does_not_stack() -> None:
    wolf = _creature(hp=40)
    fighter = _fighter("club", items=(CLUB,))
    record = _run(
        fighter, wolf, _proposal(wolf, CLUB, mastery=True), _dice((15,), (3,))
    )
    assert _mastery(record)["result"] == "applied"
    slowed = _with_effect(wolf, _standing("slow", fighter, "start"))
    again = _run(
        fighter, slowed, _proposal(slowed, CLUB, mastery=True), _dice((15,), (3,))
    )
    assert _mastery(again)["result"] == "already_slowed"


# ---------------------------------------------------------------------------
# Turn bounds (contract G2) and other rolls
# ---------------------------------------------------------------------------


def _edge(
    subject: Any, kind: str, holders: dict[tuple[str, str], Any], doc: Any
) -> Any:
    sk = "creature" if isinstance(subject, TurnCreature) else "character"
    proposal = RollProposal(
        check_label="Turn",
        subsystem_tag="turn",
        visibility=RollVisibility.SHOWN,
        operation=f"{kind}_turn",
        subject=SubjectRef(kind=sk, subject_id=subject.subject_id),
    )
    return D20RulesSystemAdapter().resolve_roll(
        proposal, _attacker(), None, _dice((10,)), False, holders, doc
    )


def test_the_wielders_turn_edges_end_its_effects() -> None:
    wielder = _creature(hp=40)
    wielder_ref = SubjectReference(kind="creature", subject_id=wielder.subject_id)
    sapped = _with_effect(_creature(hp=40), _standing("sap", wielder, "start"))
    vexing = _with_effect(_creature(hp=40), _standing("vex", wielder, "end", created=3))
    holders = {("creature", str(c.subject_id)): c for c in (wielder, sapped, vexing)}
    begun = _edge(wielder, "begin", holders, TurnCoordination(next_instance=3))
    assert [json.loads(e.value_json) for e in begun.sheet_effects] == [
        {"instance_id": "sap-1"}
    ]
    # Vex began in the wielder's turn 3: that turn's end passes over it, the
    # next one's ends it.
    in_three = TurnCoordination(active=ActiveTurn(subject=wielder_ref, instance=3))
    assert _edge(wielder, "end", holders, in_three).sheet_effects == ()
    in_four = TurnCoordination(active=ActiveTurn(subject=wielder_ref, instance=4))
    ended = _edge(wielder, "end", holders, in_four)
    assert [json.loads(e.value_json) for e in ended.sheet_effects] == [
        {"instance_id": "vex-1"}
    ]


def test_a_mastery_effect_does_not_refuse_other_rolls() -> None:
    slowed = _with_effect(_attacker(), _standing("slow", _creature(), "start"))
    climb = RollProposal(
        check_label="Climb",
        subsystem_tag="climb",
        visibility=RollVisibility.SHOWN,
        operation="fixed_dc_check",
        check_identity="glossary.climbing/difficult_climb",
    )
    assert checks.prepare(climb, slowed).dc is not None
    other = ActiveEffect(
        instance_id=str(uuid4()),
        source=GrantSource(record_key="spells.bless"),
        concentration=True,
    )
    with pytest.raises(AdjudicationRefusal):
        checks.prepare(climb, _with_effect(_attacker(), other))


def test_a_later_operations_spatial_facts_about_a_pushed_target_refuse() -> None:
    """A push moves its target; facts the GameMaster stated about it for a
    later operation of the same turn predate the move (OD-15c-1)."""
    from afterworlds.models.enums import DiceHandling
    from afterworlds.pipeline.rpg.service import RpgAdjudicationPassService
    from tests.pipeline.rpg.test_adjudication_service import (
        _STORY_ID,
        _TURN_ID,
        _FakeProvider,
        _make_assembled,
        _make_session,
    )

    wolf = _creature(hp=40)
    fighter = _fighter("greatclub", items=(GREATCLUB,))
    push = _proposal(wolf, GREATCLUB, mastery=True, push_ft=10).model_dump(
        mode="json", exclude_none=True
    )
    follow = _proposal(wolf, GREATCLUB).model_dump(mode="json", exclude_none=True)
    dice = MagicMock()
    with pytest.raises(AdjudicationRefusal) as caught:
        RpgAdjudicationPassService(
            adapter=D20RulesSystemAdapter(),
            subject_loader=lambda _story, _ref: wolf,
        ).adjudicate(
            _make_assembled(),
            _make_session(DiceHandling.AI_ROLLS),
            fighter,
            dice,
            provider=_FakeProvider([push, follow]),
            story_id=_STORY_ID,
            originating_turn_id=_TURN_ID,
        )
    assert caught.value.kind is RefusalKind.INVALID_SELECTION
    assert "can move" in caught.value.detail
    dice.roll.assert_not_called()


# ---------------------------------------------------------------------------
# Cleave: an extra attack after a hit, once per turn
# ---------------------------------------------------------------------------

GREATAXE = _wielded("greataxe")


def _cleave_turn(
    fighter: TurnCharacter,
    first: TurnCreature,
    second: TurnCreature,
    d20s: list[int],
    *extra: dict[str, Any],
    active: bool = True,
) -> tuple[Any, MagicMock]:
    from afterworlds.models.enums import DiceHandling
    from afterworlds.pipeline.rpg.service import RpgAdjudicationPassService
    from afterworlds.services.dnd5e_state.coordination import StoredCoordination
    from tests.pipeline.rpg.test_adjudication_service import (
        _STORY_ID,
        _TURN_ID,
        _FakeProvider,
        _make_assembled,
        _make_session,
    )

    me = SubjectReference(kind="character", subject_id=fighter.subject_id)
    document = TurnCoordination(
        active=ActiveTurn(subject=me, instance=2) if active else None,
        next_instance=3,
    )
    by_id = {str(c.subject_id): c for c in (first, second)}
    trigger = _proposal(first, GREATAXE, mastery=True).model_dump(
        mode="json", exclude_none=True
    )
    cleave = _proposal(
        second, GREATAXE, cleave=True, cleave_within_5_feet=True
    ).model_dump(mode="json", exclude_none=True)

    def roll(expression: str) -> DiceResult:
        face = d20s.pop(0) if "d20" in expression else 3
        return DiceResult(expression=expression, raw_rolls=(face,), chosen=face)

    dice = MagicMock()
    dice.roll.side_effect = roll
    result = RpgAdjudicationPassService(
        adapter=D20RulesSystemAdapter(),
        subject_loader=lambda _story, ref: by_id[str(ref.subject_id)],
        coordination_loader=lambda _story: StoredCoordination(_STORY_ID, 1, document),
    ).adjudicate(
        _make_assembled(),
        _make_session(DiceHandling.AI_ROLLS),
        fighter,
        dice,
        provider=_FakeProvider([trigger, cleave, *extra]),
        story_id=_STORY_ID,
        originating_turn_id=_TURN_ID,
    )
    return result, dice


def test_cleave_follows_a_hit_once_with_no_positive_ability_damage() -> None:
    fighter = _fighter("greataxe", items=(GREATAXE,))
    first, second = _creature(hp=40), _creature(hp=40)
    result, _ = _cleave_turn(fighter, first, second, [15, 15])
    trigger, extra = result.proposals
    assert _mastery(trigger)["result"] == "may_cleave"
    assert extra.turn_use == "equipment.weapons.cleave/cleave"
    provenance = json.loads(extra.modifiers_json)
    strength = provenance["breakdown"]["strength_modifier"]
    # The die, plus the ability modifier only if it is negative.
    assert provenance["damage"]["rolled"] == 3 + min(0, strength)


def test_cleave_after_a_miss_is_not_triggered_and_rolls_nothing() -> None:
    fighter = _fighter("greataxe", items=(GREATAXE,))
    first, second = _creature(hp=40), _creature(hp=40)
    result, dice = _cleave_turn(fighter, first, second, [2])
    assert json.loads(result.proposals[1].modifiers_json)["cleave"] == "not_triggered"
    assert result.proposals[1].turn_use is None
    assert dice.roll.call_count == 1


@pytest.mark.parametrize("case", ["no_turn", "twice"])
def test_cleave_is_once_in_the_attackers_turn(case: str) -> None:
    fighter = _fighter("greataxe", items=(GREATAXE,))
    first, second = _creature(hp=40), _creature(hp=40)
    again = [
        _proposal(first, GREATAXE, mastery=True).model_dump(
            mode="json", exclude_none=True
        ),
        _proposal(second, GREATAXE, cleave=True, cleave_within_5_feet=True).model_dump(
            mode="json", exclude_none=True
        ),
    ]
    with pytest.raises(AdjudicationRefusal) as caught:
        if case == "no_turn":
            _cleave_turn(fighter, first, second, [15, 15], active=False)
        else:
            _cleave_turn(fighter, first, second, [15, 15, 15, 15], *again)
    assert caught.value.kind is RefusalKind.INVALID_SELECTION


def test_cleave_needs_the_second_creature_within_5_feet_of_the_first() -> None:
    fighter = _fighter("greataxe", items=(GREATAXE,))
    wolf = _creature(hp=40)
    _refused(
        RefusalKind.MISSING_STATE,
        fighter,
        wolf,
        _proposal(wolf, GREATAXE, cleave=True),
    )
    _refused(
        RefusalKind.INVALID_SELECTION,
        fighter,
        wolf,
        _proposal(wolf, GREATAXE, cleave=True, cleave_within_5_feet=False),
    )
