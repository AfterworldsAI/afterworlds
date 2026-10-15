"""CRD Issue 15c — every admitted Multiattack composition shape, run whole
in one turn through the real adjudication service.

Each C5-positive Multiattack selection is classified by its typed
composition; one representative per shape runs its printed alternative's
entries, in order and with full multiplicity, as consecutive
``creature_attack`` proposals marked ``multiattack``. Each part resolves
against the state the earlier parts left; the Multiattack's once-per-turn
use is spent once; an invalid count, a second Multiattack and a part outside
the creature's own turn refuse before any die.
"""

from __future__ import annotations

import json
from collections import Counter
from typing import Any
from unittest.mock import MagicMock

import pytest

from afterworlds.ingestion.mechanical.representation import (
    CreatureAttackFact,
    CreatureAttackRange,
    CreatureEntryUsageFact,
    CreatureMultiattackFact,
    CreatureSize,
    UsageKind,
)
from afterworlds.models.dnd5e_state import (
    ActiveTurn,
    HitPoints,
    SubjectReference,
    TurnCoordination,
    TurnUse,
)
from afterworlds.models.enums import DiceHandling
from afterworlds.models.rpg import DiceResult
from afterworlds.pipeline.rpg.adapter import D20RulesSystemAdapter
from afterworlds.pipeline.rpg.capability import AdjudicationRefusal, RefusalKind
from afterworlds.pipeline.rpg.creature_attacks import multiattack_key
from afterworlds.pipeline.rpg.defense import facts_of
from afterworlds.pipeline.rpg.service import RpgAdjudicationPassService
from afterworlds.services.dnd5e_state.coordination import StoredCoordination
from afterworlds.services.dnd5e_state.turn import TurnCharacter, TurnCreature
from tests.pipeline.rpg.test_adjudication_service import (
    _STORY_ID,
    _TURN_ID,
    _FakeProvider,
    _make_assembled,
    _make_session,
)
from tests.pipeline.rpg.test_creature_attacks import _bite, _ref
from tests.pipeline.rpg.test_creature_roster import CAPABILITY
from tests.pipeline.rpg.test_weapon_attacks import _attacker, _creature
from tests.services.dnd5e_state.builders import real_index

_HP = 400


def _selections() -> dict[str, dict[str, Any]]:
    """``template | selection`` for every C5-positive Multiattack selection
    (as the roster harness reads them), with its capability record."""
    out = {}
    for key, entry in json.loads(CAPABILITY.read_bytes())["entries"].items():
        if entry.get("entry_kind") != "multiattack":
            continue
        for selection in entry["selections"]:
            if selection.get("executable_once_accepted"):
                out[f"{key.split('#')[0]} | {selection['selection']}"] = selection
    return out


def _facts(template: str) -> tuple[CreatureMultiattackFact, dict[str, Any]]:
    facts = facts_of(real_index(), template)
    (multiattack,) = [f for f in facts if isinstance(f, CreatureMultiattackFact)]
    return multiattack, {f.entry: f for f in facts if isinstance(f, CreatureAttackFact)}


def _alternative(template: str, label: str) -> Any:
    multiattack, _ = _facts(template)
    return multiattack.alternatives[int(label.split()[1]) - 1]


def shape(key: str) -> str:
    """A selection's composition shape, from its typed Multiattack."""
    template, label = key.split(" | ")
    alternative = _alternative(template, label)
    _, attacks = _facts(template)
    limited = {
        f.entry
        for f in facts_of(real_index(), template)
        if isinstance(f, CreatureEntryUsageFact)
        and f.kind in (UsageKind.RECHARGE, UsageKind.PER_DAY)
    }
    required = [p for p in alternative.parts if not p.optional]
    names = {n for p in required for n in ({p.attack} if p.attack else p.any_of)}
    if any(n not in attacks or n in limited for n in names):
        return "save_effect_or_limited_part"
    if " with replacement " in label:
        return "replacement"
    if not label.startswith("alternative 1"):
        return "later_alternative"
    if len(required) < len(alternative.parts):
        return "optional_use_omitted"
    if any(p.any_of for p in required):
        return "any_of"
    riders = [attacks[n].hit_effect for n in names]
    if len(required) > 1:
        return "mixed_linked" if any(r and r.linked for r in riders) else "mixed"
    return (
        "repeated_with_rider"
        if any(r and r.condition for r in riders)
        else ("repeated")
    )


#: Every C5-positive Multiattack selection by its composition shape. No
#: admitted selection has a save-effect, Recharge or X/Day part: a
#: replacement by one, or an alternative needing one, is not C5-positive.
SHAPES: dict[str, frozenset[str]] = {
    "repeated_with_rider": frozenset(
        {
            "animals.ankylosaurus | alternative 1",
            "monsters.water_elemental.water_elemental | alternative 1",
        }
    ),
    "repeated": frozenset(
        {
            "animals.ape | alternative 1",
            "animals.archelon | alternative 1",
            "animals.black_bear | alternative 1",
            "animals.elephant | alternative 1",
            "animals.giant_ape | alternative 1",
            "animals.giant_eagle | alternative 1",
            "animals.hippopotamus | alternative 1",
            "animals.mammoth | alternative 1",
            "animals.polar_bear | alternative 1",
            "animals.saber_toothed_tiger | alternative 1",
            "monsters.air_elemental.air_elemental | alternative 1",
            "monsters.animated_objects.animated_armor | alternative 1",
            "monsters.black_dragons.adult_black_dragon | alternative 1",
            "monsters.black_dragons.ancient_black_dragon | alternative 1",
            "monsters.black_dragons.black_dragon_wyrmling | alternative 1",
            "monsters.black_dragons.young_black_dragon | alternative 1",
            "monsters.blue_dragons.adult_blue_dragon | alternative 1",
            "monsters.blue_dragons.ancient_blue_dragon | alternative 1",
            "monsters.blue_dragons.blue_dragon_wyrmling | alternative 1",
            "monsters.blue_dragons.young_blue_dragon | alternative 1",
            "monsters.brass_dragons.adult_brass_dragon | alternative 1",
            "monsters.brass_dragons.ancient_brass_dragon | alternative 1",
            "monsters.brass_dragons.young_brass_dragon | alternative 1",
            "monsters.bronze_dragons.adult_bronze_dragon | alternative 1",
            "monsters.bronze_dragons.ancient_bronze_dragon | alternative 1",
            "monsters.bronze_dragons.bronze_dragon_wyrmling | alternative 1",
            "monsters.bronze_dragons.young_bronze_dragon | alternative 1",
            "monsters.bulette.bulette | alternative 1",
            "monsters.copper_dragons.adult_copper_dragon | alternative 1",
            "monsters.copper_dragons.ancient_copper_dragon | alternative 1",
            "monsters.copper_dragons.young_copper_dragon | alternative 1",
            "monsters.deva.deva | alternative 1",
            "monsters.dragon_turtle.dragon_turtle | alternative 1",
            "monsters.fungi.violet_fungus | alternative 1",
            "monsters.gargoyle.gargoyle | alternative 1",
            "monsters.ghost.ghost | alternative 1",
            "monsters.ghoul.ghoul | alternative 1",
            "monsters.gladiator.gladiator | alternative 1",
            "monsters.gold_dragons.adult_gold_dragon | alternative 1",
            "monsters.gold_dragons.ancient_gold_dragon | alternative 1",
            "monsters.gold_dragons.gold_dragon_wyrmling | alternative 1",
            "monsters.gold_dragons.young_gold_dragon | alternative 1",
            "monsters.green_dragons.adult_green_dragon | alternative 1",
            "monsters.green_dragons.ancient_green_dragon | alternative 1",
            "monsters.green_dragons.green_dragon_wyrmling | alternative 1",
            "monsters.green_dragons.young_green_dragon | alternative 1",
            "monsters.green_hag.green_hag | alternative 1",
            "monsters.guardian_naga.guardian_naga | alternative 1",
            "monsters.hezrou.hezrou | alternative 1",
            "monsters.hippogriff.hippogriff | alternative 1",
            "monsters.lamia.lamia | alternative 1",
            "monsters.mages.archmage | alternative 1",
            "monsters.mages.mage | alternative 1",
            "monsters.nalfeshnee.nalfeshnee | alternative 1",
            "monsters.night_hag.night_hag | alternative 1",
            "monsters.owlbear.owlbear | alternative 1",
            "monsters.pirates.pirate | alternative 1",
            "monsters.planetar.planetar | alternative 1",
            "monsters.pseudodragon.pseudodragon | alternative 1",
            "monsters.red_dragons.adult_red_dragon | alternative 1",
            "monsters.red_dragons.ancient_red_dragon | alternative 1",
            "monsters.red_dragons.red_dragon_wyrmling | alternative 1",
            "monsters.red_dragons.young_red_dragon | alternative 1",
            "monsters.roc.roc | alternative 1",
            "monsters.sahuagin.sahuagin_warrior | alternative 1",
            "monsters.salamander.salamander | alternative 1",
            "monsters.shield_guardian.shield_guardian | alternative 1",
            "monsters.silver_dragons.adult_silver_dragon | alternative 1",
            "monsters.silver_dragons.ancient_silver_dragon | alternative 1",
            "monsters.silver_dragons.silver_dragon_wyrmling | alternative 1",
            "monsters.silver_dragons.young_silver_dragon | alternative 1",
            "monsters.solar.solar | alternative 1",
            "monsters.sphinxes.sphinx_of_lore | alternative 1",
            "monsters.treant.treant | alternative 1",
            "monsters.troll.troll | alternative 1",
            "monsters.vrock.vrock | alternative 1",
            "monsters.white_dragons.adult_white_dragon | alternative 1",
            "monsters.white_dragons.ancient_white_dragon | alternative 1",
            "monsters.white_dragons.white_dragon_wyrmling | alternative 1",
            "monsters.white_dragons.young_white_dragon | alternative 1",
        }
    ),
    "mixed": frozenset(
        {
            "animals.brown_bear | alternative 1",
            "monsters.chimera.chimera | alternative 1",
            "monsters.medusa.medusa | alternative 1",
            "monsters.unicorn.unicorn | alternative 1",
            "monsters.xorn.xorn | alternative 1",
        }
    ),
    "any_of": frozenset(
        {
            "monsters.assassin.assassin | alternative 1",
            "monsters.bandits.bandit_captain | alternative 1",
            "monsters.bugbears.bugbear_stalker | alternative 1",
            "monsters.centaur.centaur_trooper | alternative 1",
            "monsters.cloud_giant.cloud_giant | alternative 1",
            "monsters.djinni.djinni | alternative 1",
            "monsters.druid.druid | alternative 1",
            "monsters.earth_elemental.earth_elemental | alternative 1",
            "monsters.efreeti.efreeti | alternative 1",
            "monsters.fire_giant.fire_giant | alternative 1",
            "monsters.frost_giant.frost_giant | alternative 1",
            "monsters.goblins.goblin_boss | alternative 1",
            "monsters.guards.guard_captain | alternative 1",
            "monsters.hill_giant.hill_giant | alternative 1",
            "monsters.horned_devil.horned_devil | alternative 1",
            "monsters.iron_golem.iron_golem | alternative 1",
            "monsters.knight.knight | alternative 1",
            "monsters.lich.lich | alternative 1",
            "monsters.manticore.manticore | alternative 1",
            "monsters.merrow.merrow | alternative 1",
            "monsters.oni.oni | alternative 1",
            "monsters.pirates.pirate_captain | alternative 1",
            "monsters.priests.priest | alternative 1",
            "monsters.scout.scout | alternative 1",
            "monsters.spirit_naga.spirit_naga | alternative 1",
            "monsters.stone_giant.stone_giant | alternative 1",
            "monsters.stone_golem.stone_golem | alternative 1",
            "monsters.storm_giant.storm_giant | alternative 1",
            "monsters.warriors.veteran_warrior | alternative 1",
            "monsters.wererat.wererat | alternative 1",
            "monsters.weretiger.weretiger | alternative 1",
        }
    ),
    "replacement": frozenset(
        {
            "monsters.dragon_turtle.dragon_turtle | alternative 1 with replacement 1: Tail",  # noqa: E501
        }
    ),
    "optional_use_omitted": frozenset(
        {
            "monsters.dryad.dryad | alternative 1",
            "monsters.erinyes.erinyes | alternative 1",
        }
    ),
    "later_alternative": frozenset(
        {
            "monsters.medusa.medusa | alternative 2",
        }
    ),
    "mixed_linked": frozenset(
        {
            "monsters.purple_worm.purple_worm | alternative 1",
        }
    ),
}


#: One representative per shape: its selection and its printed parts as
#: proposed, in order (an any-of part's picks among the certified options).
REPRESENTATIVES: dict[str, tuple[str, list[str]]] = {
    "repeated": ("monsters.troll.troll | alternative 1", ["Rend"] * 3),
    "repeated_with_rider": ("animals.ankylosaurus | alternative 1", ["Tail"] * 2),
    "mixed": ("monsters.xorn.xorn | alternative 1", ["Bite", "Claw", "Claw", "Claw"]),
    "mixed_linked": (
        "monsters.purple_worm.purple_worm | alternative 1",
        ["Bite", "Tail Stinger"],
    ),
    "any_of": (
        "monsters.bandits.bandit_captain | alternative 1",
        ["Scimitar", "Pistol"],
    ),
    "optional_use_omitted": (
        "monsters.erinyes.erinyes | alternative 1",
        ["Withering Sword"] * 3,
    ),
    "later_alternative": ("monsters.medusa.medusa | alternative 2", ["Poison Ray"] * 3),
    "replacement": (
        "monsters.dragon_turtle.dragon_turtle | alternative 1 with replacement 1: Tail",
        ["Bite", "Tail", "Bite"],
    ),
}

#: What an earlier part (by index) applies that the later parts' rolls
#: read: the condition, and the source of their Advantage.
LATER_ADVANTAGE: dict[str, tuple[int, str, str]] = {
    "repeated_with_rider": (0, "prone", "glossary.prone/attacks_against_affected"),
    "mixed_linked": (0, "restrained", "glossary.restrained/attacks_affected"),
    "replacement": (1, "prone", "glossary.prone/attacks_against_affected"),
}


def test_every_admitted_selection_has_its_shape_and_each_shape_a_representative() -> (
    None
):
    selections = _selections()
    keys = [k for keys in SHAPES.values() for k in keys]
    assert len(keys) == len(set(keys)) == len(selections) == 123
    assert set(keys) == set(selections)
    for name, members in SHAPES.items():
        for key in members:
            assert shape(key) == name, key
    assert set(REPRESENTATIVES) == set(SHAPES)
    for name, (key, _) in REPRESENTATIVES.items():
        assert key in SHAPES[name]


def _printed(key: str, entries: list[str]) -> None:
    """*entries* are the selection's printed alternative: every fixed part's
    attack, its count of times, in printed order; an any-of part's count of
    certified options; a replacement's entry standing in for the attack it
    replaces."""
    template, label = key.split(" | ")
    multiattack, _ = _facts(template)
    alternative = _alternative(template, label)
    certified = {o for g in _selections()[key].get("certified_options", []) for o in g}
    fixed: list[str] = []
    picks = Counter(entries)
    for part in alternative.parts:
        if part.optional:
            continue
        if part.attack:
            fixed += [part.attack] * (part.count or 0)
        else:
            chosen = [e for e in entries if e in part.any_of]
            assert len(chosen) == part.count and set(chosen) <= certified
            picks -= Counter(chosen)
    if " with replacement " in label:
        n = int(label.split(" with replacement ")[1].split(":")[0])
        replacement = multiattack.replacements[n - 1]
        new = label.split(": ", 1)[1]
        assert new in {o.entry for o in replacement.with_one_of}
        fixed.remove(replacement.replaces_attack or fixed[-1])
        fixed.append(new)
        assert Counter(fixed) == picks
    elif any(p.any_of for p in alternative.parts):
        assert Counter(fixed) == picks
    else:
        assert fixed == entries


def _wizard() -> TurnCharacter:
    return _attacker(
        size=CreatureSize.MEDIUM,
        hit_points=HitPoints(current=_HP, maximum=_HP, temporary=0),
    )


def _part(creature: TurnCreature, wizard: TurnCharacter, entry: str) -> Any:
    """One part as the GameMaster proposes it: a melee attack from within 5
    feet, or a ranged one with the target, an enemy, within 5 feet."""
    _, attacks = _facts(creature.stored.state.template_record_key)
    facts: dict[str, Any] = {"target_within_5_feet": True, "multiattack": True}
    fact = attacks.get(entry)
    if fact is not None and fact.kind is CreatureAttackRange.RANGED:
        facts |= {
            "range": "within_normal_range",
            "hostiles_within_5_feet": (_ref(wizard),),
        }
    return _bite(creature, wizard, entry=entry, **facts).model_dump(
        mode="json", exclude_none=True
    )


def _turn(
    creature: TurnCreature,
    entries: list[str],
    *,
    whose: str = "creature",
    used: bool = False,
) -> tuple[Any, MagicMock, TurnCharacter]:
    wizard = _wizard()
    me = SubjectReference(kind="creature", subject_id=creature.subject_id)
    turn_of = (
        me
        if whose == "creature"
        else SubjectReference(kind="character", subject_id=wizard.subject_id)
    )
    document = TurnCoordination(
        active=ActiveTurn(subject=turn_of, instance=1),
        next_instance=2,
        uses=(
            (TurnUse(instance=1, subject=me, key=multiattack_key(creature)),)
            if used
            else ()
        ),
    )
    calls: list[str] = []

    def roll(expression: str) -> DiceResult:
        calls.append(expression)
        face = 15 if "d20" in expression else 1
        return DiceResult(expression=expression, raw_rolls=(face,), chosen=face)

    dice = MagicMock()
    dice.roll.side_effect = roll
    dice.calls = calls
    try:
        result = RpgAdjudicationPassService(
            adapter=D20RulesSystemAdapter(),
            subject_loader=lambda _story, _ref: creature,
            coordination_loader=lambda _story: StoredCoordination(
                _STORY_ID, 1, document
            ),
        ).adjudicate(
            _make_assembled(),
            _make_session(DiceHandling.AI_ROLLS),
            wizard,
            dice,
            provider=_FakeProvider([_part(creature, wizard, e) for e in entries]),
            story_id=_STORY_ID,
            originating_turn_id=_TURN_ID,
        )
    except AdjudicationRefusal:
        dice.roll.assert_not_called()  # refused before any die
        raise
    return result, dice, wizard


def _creature_of(key: str) -> TurnCreature:
    return _creature(key.split(" | ")[0], hp=500)


@pytest.mark.parametrize("name", sorted(REPRESENTATIVES))
def test_a_multiattack_runs_whole_in_one_turn(name: str) -> None:
    key, entries = REPRESENTATIVES[name]
    _printed(key, entries)
    creature = _creature_of(key)
    result, _, wizard = _turn(creature, entries)
    records = result.proposals
    provenance = [json.loads(r.modifiers_json) for r in records]
    # Each printed part, in order, with its multiplicity: one record each.
    assert [p["entry"] for p in provenance] == entries
    assert all(r.outcome == "success" for r in records)
    # The Multiattack (and the action it is) is spent once, by the creature.
    uses = [(u.by.subject_id, u.key) for r in records for u in r.turn_uses]
    assert uses == [
        (creature.subject_id, "glossary.action/action"),
        (creature.subject_id, multiattack_key(creature)),
    ]
    assert records[0].turn_uses and not any(r.turn_uses for r in records[1:])
    # Each part damages the target as the earlier parts left it.
    hp = _HP
    for record, p in zip(records, provenance, strict=True):
        taken = sum(d["taken"] for d in p["damage"])
        (current,) = [e for e in record.sheet_effects if e.target == "current_hp"]
        assert taken > 0 and current.subject_id == wizard.subject_id
        assert json.loads(current.value_json) == hp - taken
        hp -= taken
    # A condition an earlier part applied is present for the later ones.
    if name in LATER_ADVANTAGE:
        at, condition, source = LATER_ADVANTAGE[name]
        assert any(e.target == condition for e in records[at].sheet_effects)
        for i, p in enumerate(provenance):
            assert (source in p["advantage_sources"]) is (i > at), (i, p)


def _foreign(key: str, entries: list[str]) -> str | None:
    """An attack entry the creature prints outside this selection."""
    _, attacks = _facts(key.split(" | ")[0])
    others = sorted(set(attacks) - set(entries))
    return others[0] if others else None


_INVALID = [
    (name, case)
    for name in sorted(REPRESENTATIVES)
    for case in ("short", "long", "foreign", "second", "not_its_turn")
    if case != "foreign" or _foreign(*REPRESENTATIVES[name])
]


@pytest.mark.parametrize(("name", "case"), _INVALID)
def test_an_invalid_multiattack_refuses_before_any_die(name: str, case: str) -> None:
    key, entries = REPRESENTATIVES[name]
    creature = _creature_of(key)
    sequence = {
        "short": entries[:-1],
        "long": [*entries, entries[0]],
        "foreign": [_foreign(key, entries) or "", *entries[1:]],
    }.get(case, entries)
    with pytest.raises(AdjudicationRefusal) as caught:
        _turn(
            creature,
            sequence,
            whose="wizard" if case == "not_its_turn" else "creature",
            used=case == "second",
        )
    assert caught.value.kind is RefusalKind.INVALID_SELECTION, caught.value
    detail = caught.value.detail
    if case == "second":
        assert f"{multiattack_key(creature)} was already used" in detail
    elif case == "not_its_turn":
        assert f"not creature {creature.subject_id}'s turn" in detail
    else:
        assert "is not an executable alternative" in detail


@pytest.mark.parametrize("name", ["repeated", "mixed", "mixed_linked"])
def test_a_multiattack_in_a_sequence_is_ordered_linked_backend_steps(
    name: str,
) -> None:
    """CRD Issue 15b: in an action-resolution sequence of a player-rolled
    story, every die of a creature's Multiattack is a backend step (the
    creature's, not the Sojourner's), described per part in order: each
    part's attack die, then its damage dice. Replaying the accepted steps
    reproduces the same instructions without drawing again."""
    from uuid import uuid4

    from afterworlds.models.enums import ResolvedStepKind, RollPurpose
    from afterworlds.models.rpg import RollProposal
    from afterworlds.pipeline.rpg.steps import SequenceDice

    key, entries = REPRESENTATIVES[name]
    creature = _creature_of(key)
    wizard = _wizard()
    me = SubjectReference(kind="creature", subject_id=creature.subject_id)
    document = TurnCoordination(
        active=ActiveTurn(subject=me, instance=1), next_instance=2
    )
    service = RpgAdjudicationPassService(
        adapter=D20RulesSystemAdapter(),
        subject_loader=lambda _story, _ref: creature,
        coordination_loader=lambda _story: StoredCoordination(_STORY_ID, 1, document),
    )
    proposals = [
        RollProposal.model_validate(_part(creature, wizard, e)) for e in entries
    ]
    drawn: list[str] = []

    class Backend:
        def roll(self, expression: str) -> DiceResult:
            drawn.append(expression)
            count = int(expression.split("d")[0])
            face = 15 if "d20" in expression else 1
            return DiceResult(
                expression=expression, raw_rolls=(face,) * count, chosen=face * count
            )

    sequence_id = uuid4()
    actor = ("character", str(wizard.subject_id))
    dice = SequenceDice(Backend(), sequence_id, actor, player_rolls=True)
    prepared = service.prepare_turn(_STORY_ID, wizard, proposals)
    service.resolve_turn(prepared, False, dice, [])
    steps = [s.roll for s in dice.new_steps]
    assert all(s is not None and s.kind is ResolvedStepKind.AI_ROLL for s in steps)
    snapshots = [s.snapshot for s in steps if s is not None]
    assert len(drawn) == len(snapshots)
    order = [(s.operation_index, s.die_index) for s in snapshots]
    assert order == sorted(order) and len(set(order)) == len(order)
    assert sorted({op for op, _ in order}) == list(range(len(entries)))
    for op in range(len(entries)):
        purposes = [s.purpose for s in snapshots if s.operation_index == op]
        assert purposes[0] is RollPurpose.ATTACK
        assert purposes[1:] and set(purposes[1:]) <= {RollPurpose.DAMAGE}
    assert {s.roller.subject_id for s in snapshots} == {creature.subject_id}
    assert len({s.step_id for s in snapshots}) == len(snapshots)

    rolls: dict[int, list[Any]] = {}
    for step in steps:
        assert step is not None
        rolls.setdefault(step.snapshot.operation_index, []).append(step)

    class NoDice:
        def roll(self, expression: str) -> DiceResult:
            raise AssertionError(f"replay drew {expression}")

    replay = SequenceDice(NoDice(), sequence_id, actor, True, rolls=rolls)
    service.resolve_turn(prepared, False, replay, [])
    assert replay.new_steps == []
