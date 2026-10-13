"""CRD Issue 15c — creature attacks: a continuing creature's printed attack
entry against a character or creature, every number from typed authority
under each subject's own binding, refusals before any die."""

from __future__ import annotations

import json
from typing import Any

import pytest

from afterworlds.models.enums import RollVisibility
from afterworlds.models.rpg import CreatureAttackSelection, RollProposal, SubjectRef
from afterworlds.pipeline.rpg.adapter import D20RulesSystemAdapter
from afterworlds.pipeline.rpg.capability import AdjudicationRefusal, RefusalKind
from afterworlds.services.dnd5e_state.turn import TurnCharacter, TurnCreature
from tests.pipeline.rpg.test_weapon_attacks import _attacker, _creature, _dice


def _ref(subject: Any) -> SubjectRef:
    kind = "creature" if isinstance(subject, TurnCreature) else "character"
    return SubjectRef(kind=kind, subject_id=subject.subject_id)


def _bite(wolf: TurnCreature, target: Any, **facts: Any) -> RollProposal:
    selection = {
        "attacker": _ref(wolf),
        "entry": "Bite",
        "target": _ref(target),
        "range": "within_reach",
        "cover": "none",
        "attacker_light": "bright",
        "target_light": "bright",
        "allies_within_5_feet_of_target": (),
        **facts,
    }
    return RollProposal(
        check_label="Wolf bites",
        subsystem_tag="attack",
        visibility=RollVisibility.SHOWN,
        operation="creature_attack",
        creature_attack=CreatureAttackSelection(**selection),
    )


def _medium_wizard() -> TurnCharacter:
    return _attacker(size="medium")


def _subjects(*creatures: TurnCreature) -> dict[tuple[str, str], Any]:
    return {("creature", str(c.subject_id)): c for c in creatures}


def _resolve(
    proposal: RollProposal, actor: TurnCharacter, subjects: Any, dice: Any
) -> Any:
    return D20RulesSystemAdapter().resolve_roll(
        proposal, actor, None, dice, False, subjects
    )


def _refused(
    kind: RefusalKind, proposal: RollProposal, actor: Any, subjects: Any
) -> AdjudicationRefusal:
    with pytest.raises(AdjudicationRefusal) as caught:
        D20RulesSystemAdapter().require_supported(proposal, actor, subjects)
    assert caught.value.kind is kind, caught.value
    return caught.value


def test_a_wolf_bite_damages_and_knocks_a_medium_character_prone() -> None:
    wolf, wizard = _creature(), _medium_wizard()
    dice = _dice((18,), (3,))
    record = _resolve(_bite(wolf, wizard), wizard, _subjects(wolf), dice)
    provenance = json.loads(record.modifiers_json)
    assert dice.calls == ["1d20", "1d6"]
    assert record.total == 22 and record.outcome == "success"
    damage = provenance["damage"][0]
    assert damage["rolled"] == 5  # 1d6 (3) + 2, the printed Bite
    targets = {e.target: e for e in record.sheet_effects}
    assert targets["current_hp"].subject_id == wizard.subject_id
    assert json.loads(targets["prone"].value_json)["condition"] == "prone"
    assert provenance["rider"]["condition"] == "prone"
    # The Writer never sees the target's AC.
    assert D20RulesSystemAdapter().to_writer_view(record).dc is None


def test_a_miss_changes_nothing() -> None:
    wolf, wizard = _creature(), _medium_wizard()
    record = _resolve(_bite(wolf, wizard), wizard, _subjects(wolf), _dice((2,)))
    assert (record.outcome, record.sheet_effects) == ("failure", ())


def test_the_bites_prone_has_a_size_limit() -> None:
    wolf, elephant = _creature(), _creature("animals.elephant", hp=60)
    record = _resolve(
        _bite(wolf, elephant),
        _medium_wizard(),
        _subjects(wolf, elephant),
        _dice((18,), (3,)),
    )
    assert json.loads(record.modifiers_json)["rider"] == {"result": "too_large"}
    assert all(e.operation != "apply_condition" for e in record.sheet_effects)


def test_pack_tactics_needs_a_named_ally_that_can_act() -> None:
    wolf, ally, wizard = _creature(), _creature(), _medium_wizard()
    _refused(
        RefusalKind.MISSING_STATE,
        _bite(wolf, wizard, allies_within_5_feet_of_target=None),
        wizard,
        _subjects(wolf, ally),
    )
    record = _resolve(
        _bite(wolf, wizard, allies_within_5_feet_of_target=(_ref(ally),)),
        wizard,
        _subjects(wolf, ally),
        _dice((5, 18), (3,)),
    )
    assert json.loads(record.modifiers_json)["advantage_sources"] == [
        "animals.wolf/Pack Tactics"
    ]
    from afterworlds.models.dnd5e_state import ConditionInstance
    from afterworlds.models.enums import ConditionVisibility

    stunned = ConditionInstance(
        instance_id="s",
        condition="stunned",  # type: ignore[arg-type]
        visibility=ConditionVisibility.VISIBLE,
    )
    state = ally.stored.state.model_copy(update={"conditions": (stunned,)})
    import dataclasses

    dazed = dataclasses.replace(
        ally, stored=dataclasses.replace(ally.stored, state=state)
    )
    record = _resolve(
        _bite(wolf, wizard, allies_within_5_feet_of_target=(_ref(dazed),)),
        wizard,
        _subjects(wolf, dazed),
        _dice((5, 18), (3,)),
    )
    assert json.loads(record.modifiers_json)["advantage_sources"] == []


@pytest.mark.parametrize(
    "facts",
    [
        {"entry": "Claw"},  # the Wolf prints no Claw
        {"range": "within_normal_range", "hostiles_within_5_feet": ()},
        {"cover": "total"},
    ],
)
def test_an_invalid_creature_attack_selection_refuses(facts: dict[str, Any]) -> None:
    wolf, wizard = _creature(), _medium_wizard()
    _refused(
        RefusalKind.INVALID_SELECTION,
        _bite(wolf, wizard, **facts),
        wizard,
        _subjects(wolf),
    )


def test_a_creature_attack_can_leave_its_target_prone_for_the_preflight() -> None:
    wolf, wizard = _creature(), _medium_wizard()
    possible = D20RulesSystemAdapter().possible_conditions(
        _bite(wolf, wizard), wizard, _subjects(wolf)
    )
    assert "prone" in {c.value for c in possible[("character", str(wizard.subject_id))]}


def test_a_turn_bounded_condition_ends_at_its_edge() -> None:
    import dataclasses

    from afterworlds.models.dnd5e_state import (
        ConditionInstance,
        EffectEnd,
        SubjectReference,
        TurnBoundEnd,
    )
    from afterworlds.models.enums import ConditionVisibility
    from afterworlds.pipeline.rpg.mastery import expiring

    wolf = _creature()
    source = SubjectReference(kind="creature", subject_id=wolf.subject_id)
    grabbed = ConditionInstance(
        instance_id="g1",
        condition="restrained",  # type: ignore[arg-type]
        visibility=ConditionVisibility.VISIBLE,
        ends=EffectEnd(
            kind="special",  # type: ignore[arg-type]
            turn=TurnBoundEnd(boundary="start", of=source),  # type: ignore[arg-type]
        ),
    )
    held = _creature()
    held = dataclasses.replace(
        held,
        stored=dataclasses.replace(
            held.stored,
            state=held.stored.state.model_copy(update={"conditions": (grabbed,)}),
        ),
    )
    (effect,) = expiring(held, "begin", source, 1)
    assert (effect.operation, json.loads(effect.value_json)) == (
        "clear_condition",
        {"instance_id": "g1"},
    )
    assert expiring(held, "end", source, 1) == []


# ---------------------------------------------------------------------------
# One hit, one damage: several damage terms judge zero-HP consequences once
# ---------------------------------------------------------------------------


def _at(hp: int, maximum: int, **death: Any) -> TurnCreature:
    import dataclasses

    from afterworlds.models.dnd5e_state import (
        DeathState,
        HitPoints,
        ZeroHitPointTreatment,
    )

    wolf = _creature(hp=maximum, treatment=ZeroHitPointTreatment(subject="character"))
    state = wolf.stored.state.model_copy(
        update={
            "hit_points": HitPoints(current=hp, maximum=maximum, temporary=0),
            "death_state": DeathState(
                **{
                    "successes": 0,
                    "failures": 0,
                    "stable": False,
                    "dead": False,
                    **death,
                }
            ),
        }
    )
    return dataclasses.replace(
        wolf, stored=dataclasses.replace(wolf.stored, state=state)
    )


def test_a_two_term_hit_falls_once() -> None:
    from afterworlds.ingestion.mechanical.representation import DamageType
    from afterworlds.pipeline.rpg.damage import take_damage

    hit = take_damage(
        _at(5, 20),
        4,
        DamageType.PIERCING,
        critical=False,
        more=((3, DamageType.POISON),),
    )
    assert hit.outcome == "unconscious_and_dying" and hit.taken == 7
    assert [e.target for e in hit.effects].count("death_state") == 1


def test_massive_damage_is_judged_on_the_whole_hit() -> None:
    from afterworlds.ingestion.mechanical.representation import DamageType
    from afterworlds.pipeline.rpg.damage import take_damage

    # Each term alone would overflow by 3; together by 11, past the maximum.
    hit = take_damage(
        _at(5, 10),
        8,
        DamageType.PIERCING,
        critical=False,
        more=((8, DamageType.POISON),),
    )
    assert hit.outcome == "died_massive_damage"


def test_a_two_term_critical_at_0_hit_points_counts_two_failures() -> None:
    from afterworlds.ingestion.mechanical.representation import DamageType
    from afterworlds.models.dnd5e_state import DeathState
    from afterworlds.pipeline.rpg.damage import take_damage

    hit = take_damage(
        _at(0, 20),
        2,
        DamageType.PIERCING,
        critical=True,
        more=((2, DamageType.POISON),),
    )
    (death,) = [e for e in hit.effects if e.target == "death_state"]
    assert DeathState.model_validate(json.loads(death.value_json)).failures == 2


# ---------------------------------------------------------------------------
# Multiattack: one printed alternative, on the creature's turn, once per turn
# ---------------------------------------------------------------------------


def _multiattack_turn(
    bear: TurnCreature, entries: list[str], *, active: bool = True, **facts: Any
) -> tuple[Any, Any]:
    from unittest.mock import MagicMock

    from afterworlds.models.dnd5e_state import (
        ActiveTurn,
        SubjectReference,
        TurnCoordination,
    )
    from afterworlds.models.enums import DiceHandling
    from afterworlds.models.rpg import DiceResult
    from afterworlds.pipeline.rpg.service import RpgAdjudicationPassService
    from afterworlds.services.dnd5e_state.coordination import StoredCoordination
    from tests.pipeline.rpg.test_adjudication_service import (
        _STORY_ID,
        _TURN_ID,
        _FakeProvider,
        _make_assembled,
        _make_session,
    )

    wizard = _medium_wizard()
    me = SubjectReference(kind="creature", subject_id=bear.subject_id)
    document = TurnCoordination(
        active=ActiveTurn(subject=me, instance=1) if active else None,
        next_instance=2,
    )
    proposals = [
        _bite(bear, wizard, entry=e, multiattack=True, **facts).model_dump(
            mode="json", exclude_none=True
        )
        for e in entries
    ]

    def roll(expression: str) -> DiceResult:
        face = 2 if "d20" in expression else 1
        return DiceResult(expression=expression, raw_rolls=(face,), chosen=face)

    dice = MagicMock()
    dice.roll.side_effect = roll
    result = RpgAdjudicationPassService(
        adapter=D20RulesSystemAdapter(),
        subject_loader=lambda _story, _ref: bear,
        coordination_loader=lambda _story: StoredCoordination(_STORY_ID, 1, document),
    ).adjudicate(
        _make_assembled(),
        _make_session(DiceHandling.AI_ROLLS),
        wizard,
        dice,
        provider=_FakeProvider(proposals),
        story_id=_STORY_ID,
        originating_turn_id=_TURN_ID,
    )
    return result, dice


def test_a_multiattack_is_one_printed_alternative_taking_one_use() -> None:
    bear = _creature("animals.brown_bear", hp=34)
    result, _ = _multiattack_turn(bear, ["Bite", "Claw"])
    first, second = result.proposals
    assert [u.key for u in first.turn_uses] == [
        "glossary.action/action",
        "animals.brown_bear/Multiattack",
    ]
    assert {u.by.subject_id for u in first.turn_uses} == {bear.subject_id}
    assert second.turn_uses == ()


@pytest.mark.parametrize(
    ("entries", "active"),
    [
        (["Bite", "Bite"], True),  # not a printed alternative
        (["Bite", "Claw"], False),  # not the bear's turn
        (["Bite", "Claw", "Bite", "Claw"], True),  # twice in one turn
    ],
)
def test_an_illegal_multiattack_refuses_before_any_die(
    entries: list[str], active: bool
) -> None:
    bear = _creature("animals.brown_bear", hp=34)
    with pytest.raises(AdjudicationRefusal) as caught:
        _multiattack_turn(bear, entries, active=active)
    assert caught.value.kind is RefusalKind.INVALID_SELECTION
