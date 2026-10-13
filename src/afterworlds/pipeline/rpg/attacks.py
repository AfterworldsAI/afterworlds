"""Weapon attacks — CRD Issue 15c.

:func:`prepare` validates a ``weapon_attack`` completely and derives every
number from exact typed authority, recorded state and the GameMaster's
approved contextual selections (OD-15c-1), before any die is rolled.
:func:`roll` rolls the attack and, on a hit, the damage; the damage's
consequences for the target are subject-addressed effects (:mod:`.damage`).

Numbers and their sources (attacker's binding unless stated):

* the weapon: a held, equipped item instance of one of the accepted weapon
  records; its typed category, range class, properties, damage and ranges;
* the ability: ``attack_roll_ability`` (Strength melee, Dexterity ranged), a
  Finesse weapon's ``attack_ability_option`` selected by the GameMaster, a
  thrown melee weapon's ``thrown_attack`` (same as melee); the score is the
  validated adjusted score (:mod:`.grants`);
* proficiency: the validated weapon grant and the typed weapon
  ``proficiency_application``, by the typed band;
* the target's AC, in the target's own binding (:mod:`.defense`), plus the
  typed cover bonus for the selected degree;
* Advantage/Disadvantage: typed condition facts on both subjects, the
  Heavy property's ability requirement, the range band, close combat for a
  ranged attack, and untrained armor; natural 1 and 20 per
  ``natural_roll_outcome``;
* damage: the weapon's dice (Versatile two-handed: its typed die), doubled
  dice on a Critical Hit (``critical_damage``), plus the ability modifier
  (``damage_roll_rule``), never below its typed minimum.

Contributors this adapter does not execute refuse (see
``ATTACK_CONTRIBUTORS`` and :mod:`.defense`): masteries are a separate
selection not yet executed here, as are ammunition expenditure, the Light
property's extra attack, and sight that needs a sense's range.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from afterworlds.ingestion.mechanical.models import ComponentHandling
from afterworlds.ingestion.mechanical.representation import (
    AbilityScore,
    AbilityScoreRequirementFact,
    AdvantageFact,
    AdvantageState,
    ArmorTrainingPenaltyFact,
    AttackAbilityOptionFact,
    AttackRollAbilityFact,
    AutomaticOutcomeFact,
    ConditionKind,
    CoverDefensiveBonusFact,
    CriticalDamageFact,
    DamageFact,
    DamageRollRuleFact,
    DamageType,
    DiceExpression,
    NaturalRollOutcomeFact,
    ProficiencyApplicationFact,
    ProficiencyKind,
    RangeBandRuleFact,
    RangeClass,
    RecordKind,
    RollActor,
    RollContext,
    WeaponCategory,
    WeaponCategoryFact,
    WeaponProperty,
    WeaponPropertyFact,
    WeaponRangeClassFact,
)
from afterworlds.models.dnd5e_state import Dnd5eCharacterState, RecordChoice
from afterworlds.models.rpg import RollProposal, SheetEffect, WeaponAttackSelection
from afterworlds.pipeline.rpg.capability import (
    AdjudicationRefusal,
    Certificate,
    Operation,
    RefusalKind,
    certify,
    governing_fingerprint,
)
from afterworlds.pipeline.rpg.checks import proficiency_bonus
from afterworlds.pipeline.rpg.damage import DamageTaken, preflight, take_damage
from afterworlds.pipeline.rpg.defense import armor_class, facts_of, untrained_armor
from afterworlds.pipeline.rpg.dice import DiceService
from afterworlds.pipeline.rpg.grants import ability_score, weapon_proficiency
from afterworlds.services.dnd5e_state.authority import AuthorityIndex
from afterworlds.services.dnd5e_state.holdings import ItemInstance
from afterworlds.services.dnd5e_state.turn import (
    TurnCharacter,
    TurnCreature,
    TurnSubject,
)

__all__ = [
    "ATTACK_CONTRIBUTORS",
    "PreparedAttack",
    "RolledAttack",
    "prepare",
    "roll",
]

#: Features, feats and traits that change their holder's weapon attack or
#: damage rolls automatically, read entry by entry from the pinned source
#: (``attack-contributor-scan.txt``). Optional activations a turn must choose
#: (Reckless Attack, Brutal Strike, Steady Aim, Sacred Weapon, Frenzy,
#: Stunning Strike) cannot be selected here and so never apply. A holder of
#: one of these refuses until it is executed.
ATTACK_CONTRIBUTORS: frozenset[str] = frozenset(
    {
        "classes.fighter.champion.improved_critical",
        "classes.fighter.champion.superior_critical",
        "classes.fighter.studied_attacks",
        "classes.rogue.sneak_attack",
        "classes.ranger.hunter.hunters_prey",
        "classes.ranger.hunter.superior_hunters_prey",
        "classes.paladin.radiant_strikes",
        "classes.cleric.blessed_strikes",
        "classes.cleric.improved_blessed_strikes",
        "classes.druid.elemental_fury",
        "classes.druid.improved_elemental_fury",
        "classes.monk.martial_arts",
        "classes.monk.empowered_strikes",
        "classes.warlock.eldritch_invocation_options.pact_of_the_blade",
        "classes.warlock.eldritch_invocation_options.lifedrinker",
        "classes.warlock.eldritch_invocation_options.eldritch_smite",
        "feats.archery",
        "feats.great_weapon_fighting",
        "feats.two_weapon_fighting",
        "feats.savage_attacker",
        "feats.grappler",
        "feats.boon_of_combat_prowess",
        "feats.boon_of_irresistible_offense",
        "character_origins.goliath",
    }
)

#: Procedure components the attack implements, beyond the check procedure.
ATTACK_PROCEDURE: tuple[tuple[str, str], ...] = (
    ("play.d20_tests", "attack_ability_modifier"),
    ("play.d20_tests", "natural_1"),
    ("play.d20_tests", "natural_20"),
    ("play.damage_and_healing", "damage_rolls"),
    ("play.damage_and_healing", "critical_hits"),
    ("play.proficiency", "weapon_proficiency"),
    ("play.combat", "cover_degrees"),
    ("play.combat", "close_combat"),
    ("play.combat", "unseen_attacker"),
    ("play.combat", "unseen_target"),
    ("equipment.weapons.range", "range"),
    ("equipment.weapons.finesse", "finesse"),
    ("equipment.weapons.heavy", "heavy"),
    ("equipment.weapons.thrown", "thrown"),
    ("equipment.weapons.two_handed", "two_handed"),
    ("equipment.weapons.versatile", "versatile"),
    ("equipment.weapons.reach", "reach"),
    ("equipment.armor", "light_medium_or_heavy_armor"),
    ("equipment.armor.shield", "shield"),
    ("play.d20_tests", "base_ac"),
)

_SIGHT_LIGHT = frozenset({"bright", "dim"})
_SIGHT_CONDITIONS = frozenset({ConditionKind.INVISIBLE, ConditionKind.BLINDED})


def _refuse(kind: RefusalKind, detail: str) -> AdjudicationRefusal:
    return AdjudicationRefusal(kind, detail)


@dataclass(frozen=True)
class _Weapon:
    record: str
    category: WeaponCategory
    range_class: RangeClass
    properties: dict[WeaponProperty, WeaponPropertyFact]
    damage: DamageFact


def _weapon(index: AuthorityIndex, item: ItemInstance) -> _Weapon:
    facts = facts_of(index, item.record_key)
    categories = [f for f in facts if isinstance(f, WeaponCategoryFact)]
    ranges = [f for f in facts if isinstance(f, WeaponRangeClassFact)]
    damages = [f for f in facts if isinstance(f, DamageFact)]
    if not item.record_key.startswith("equipment.weapons.") or len(categories) != 1:
        raise _refuse(
            RefusalKind.INVALID_SELECTION, f"{item.record_key} is not a weapon"
        )
    if len(ranges) != 1 or len(damages) != 1:
        raise _refuse(
            RefusalKind.MISSING_AUTHORITY,
            f"{item.record_key} states no single range class and damage",
        )
    return _Weapon(
        record=item.record_key,
        category=categories[0].category,
        range_class=ranges[0].range_class,
        properties={
            f.weapon_property: f for f in facts if isinstance(f, WeaponPropertyFact)
        },
        damage=damages[0],
    )


@dataclass(frozen=True)
class PreparedAttack:
    """A fully validated weapon attack: every input fixed, no die rolled."""

    selection: WeaponAttackSelection
    weapon: str
    target: TurnSubject
    ability: AbilityScore
    attack_modifier: int
    damage_dice: DiceExpression
    damage_type: DamageType
    damage_modifier: int
    minimum_damage: int
    critical_multiplier: int
    target_ac: int
    advantage_sources: tuple[str, ...]
    disadvantage_sources: tuple[str, ...]
    certificate: Certificate
    breakdown: dict[str, int] = field(default_factory=dict)
    ac_breakdown: dict[str, int] = field(default_factory=dict)

    @property
    def expression(self) -> str:
        adv, dis = bool(self.advantage_sources), bool(self.disadvantage_sources)
        if adv and not dis:
            return "2d20kh1"
        if dis and not adv:
            return "2d20kl1"
        return "1d20"


@dataclass(frozen=True)
class RolledAttack:
    prepared: PreparedAttack
    raw_rolls: tuple[int, ...]
    chosen: int
    hit: bool
    critical: bool
    damage_rolls: tuple[int, ...] = ()
    damage: DamageTaken | None = None

    @property
    def total(self) -> int:
        return self.chosen + self.prepared.attack_modifier

    @property
    def outcome(self) -> str:
        if self.critical:
            return "critical_success"
        return "success" if self.hit else "failure"

    @property
    def effects(self) -> tuple[SheetEffect, ...]:
        return self.damage.effects if self.damage else ()

    def provenance_json(self) -> str:
        p = self.prepared
        return json.dumps(
            {
                "operation": Operation.WEAPON_ATTACK.value,
                "weapon": p.weapon,
                "target": {
                    "kind": p.selection.target.kind,
                    "subject_id": str(p.selection.target.subject_id),
                },
                "ability": p.ability.value,
                "visible_total": p.attack_modifier,
                "breakdown": p.breakdown,
                "target_ac": p.target_ac,
                "ac_breakdown": p.ac_breakdown,
                "contextual_facts": p.selection.model_dump(
                    mode="json", exclude={"weapon_item_id", "target"}
                ),
                "advantage_sources": list(p.advantage_sources),
                "disadvantage_sources": list(p.disadvantage_sources),
                "hit": self.hit,
                "critical": self.critical,
                "damage_rolls": list(self.damage_rolls),
                "damage": self.damage.provenance() if self.damage else None,
                "certificate": p.certificate.as_json(),
            },
            sort_keys=True,
        )


def _held(index: AuthorityIndex, state: Dnd5eCharacterState) -> set[str]:
    held = {f.feat_record_key for f in state.feats or ()}
    for cl in state.classes or ():
        held |= {
            e.entitlement_key
            for e in index.progression(cl.class_record_key)
            if e.level <= cl.level
        }
        if cl.subclass_record_key:
            prefix = cl.subclass_record_key + "."
            held |= {k for k in index.records if k.startswith(prefix)}
    for choice in state.choices or ():
        held |= {s.record_key for s in choice.selected if isinstance(s, RecordChoice)}
    if state.species is not None:
        held.add(state.species.record_key)
    return held


def _condition_sources(
    subject: TurnSubject,
    actor: RollActor,
    ability: AbilityScore,
) -> tuple[list[str], list[str]]:
    """Advantage/Disadvantage that *subject*'s conditions give an attack roll
    made by (``SUBJECT``) or against (``AGAINST_SUBJECT``) it."""
    index = subject.index
    assert index is not None
    advantage: list[str] = []
    disadvantage: list[str] = []
    for instance in subject.stored.state.conditions or ():
        if instance.condition is ConditionKind.EXHAUSTION:
            raise _refuse(
                RefusalKind.UNSUPPORTED_CAPABILITY,
                "Exhaustion's D20 Test reduction is not executable here",
            )
        if instance.condition in _SIGHT_CONDITIONS:
            raise _refuse(
                RefusalKind.UNSUPPORTED_CAPABILITY,
                f"{instance.condition.value}: sight that depends on a sense's "
                "range is not executable here",
            )
        record = index.record(f"glossary.{instance.condition.value}")
        if record is None:
            raise _refuse(
                RefusalKind.MISSING_AUTHORITY,
                f"condition {instance.condition.value} has no governing record",
            )
        for component in record.components:
            for ef in component.facts:
                fact = ef.fact
                if not isinstance(fact, (AdvantageFact, AutomaticOutcomeFact)):
                    continue
                roll = fact.roll
                contexts = (RollContext.ATTACK_ROLL, RollContext.D20_TEST)
                if roll.actor is not actor or roll.context not in contexts:
                    continue
                if roll.ability not in (None, ability):
                    continue
                where = f"{record.semantic_key}/{component.semantic_key}"
                contextual = (
                    component.handling is not ComponentHandling.STRUCTURED
                    or component.applies_when is not None
                    or ef.qualifier is not None
                )
                if contextual or isinstance(fact, AutomaticOutcomeFact):
                    raise _refuse(
                        RefusalKind.UNSUPPORTED_CAPABILITY,
                        f"{where} can affect this attack under circumstances that "
                        "need judgement and is not executable here",
                    )
                if fact.state is AdvantageState.ADVANTAGE:
                    advantage.append(where)
                else:
                    disadvantage.append(where)
    return advantage, disadvantage


def _one[T](facts: list[object], family: type[T], where: str) -> T:
    found = [f for f in facts if isinstance(f, family)]
    if len(found) != 1:
        raise _refuse(
            RefusalKind.MISSING_AUTHORITY, f"{where}: no single {family.__name__}"
        )
    return found[0]


def _agreeing_bindings(actor: TurnCharacter, target: TurnSubject) -> None:
    """Every shared procedure this operation uses must agree under both
    bindings; no precedence is chosen."""
    assert actor.index is not None and target.index is not None
    if actor.index.binding == target.index.binding:
        return
    mine = governing_fingerprint(actor.index, Operation.WEAPON_ATTACK)
    theirs = governing_fingerprint(target.index, Operation.WEAPON_ATTACK)
    if mine != theirs:
        raise _refuse(
            RefusalKind.INCOMPATIBLE_CERTIFICATION,
            "the attacker's and target's bindings disagree on the attack procedure",
        )


def prepare(
    proposal: RollProposal,
    actor: TurnCharacter,
    subjects: dict[tuple[str, str], TurnSubject],
) -> PreparedAttack:
    """Validate a ``weapon_attack`` and derive every input, or refuse."""
    sel = proposal.weapon_attack
    if sel is None:
        raise _refuse(
            RefusalKind.INVALID_SELECTION, "a weapon attack names no weapon or target"
        )
    index = actor.index
    if index is None:
        raise _refuse(
            RefusalKind.MISSING_AUTHORITY, "the attacker's authority is not resolved"
        )
    certificate = certify(Operation.WEAPON_ATTACK, index)
    target = subjects.get((sel.target.kind, str(sel.target.subject_id)))
    if target is None or target.index is None:
        raise _refuse(
            RefusalKind.MISSING_STATE, "the target was not read for this turn"
        )
    if isinstance(target, TurnCharacter) and target.subject_id == actor.subject_id:
        raise _refuse(RefusalKind.INVALID_SELECTION, "an attacker cannot target itself")
    certify(Operation.WEAPON_ATTACK, target.index)
    _agreeing_bindings(actor, target)
    state = actor.stored.state

    # Contextual facts the attack needs (OD-15c-1).
    if sel.attacker_light not in _SIGHT_LIGHT or sel.target_light not in _SIGHT_LIGHT:
        raise _refuse(
            RefusalKind.UNSUPPORTED_CAPABILITY,
            "sight in darkness or heavy obscurement depends on a sense's range and "
            "is not executable here",
        )
    if sel.cover == "total":
        raise _refuse(
            RefusalKind.INVALID_SELECTION,
            "a target behind Total Cover can't be targeted",
        )

    # Contributors.
    if state.active_effects:
        raise _refuse(
            RefusalKind.UNSUPPORTED_CAPABILITY,
            f"active effect {state.active_effects[0].source.record_key} can change "
            "this attack and is not executable here",
        )
    found = sorted(_held(index, state) & ATTACK_CONTRIBUTORS)
    if found:
        raise _refuse(
            RefusalKind.UNSUPPORTED_CAPABILITY,
            f"{found[0]} can change this attack and is not executable here",
        )

    # The weapon.
    item = next((i for i in actor.items if i.item_id == sel.weapon_item_id), None)
    if item is None:
        raise _refuse(RefusalKind.MISSING_STATE, "the attacker holds no such weapon")
    if not item.equipped:
        raise _refuse(RefusalKind.MISSING_STATE, f"{item.record_key} is not wielded")
    for other in actor.items:
        if (other.equipped or other.attuned_subject_id) and index.kind(
            other.record_key
        ) is RecordKind.MAGIC_ITEM:
            raise _refuse(
                RefusalKind.UNSUPPORTED_CAPABILITY,
                f"magic item {other.record_key} is not executable here",
            )
    weapon = _weapon(index, item)
    props = weapon.properties
    if WeaponProperty.AMMUNITION in props:
        raise _refuse(
            RefusalKind.UNSUPPORTED_CAPABILITY,
            f"{weapon.record}: ammunition expenditure is not executed yet",
        )
    shield_held = any(
        i.equipped and i.record_key == "equipment.armor.shield" for i in actor.items
    )
    two_hands = WeaponProperty.TWO_HANDED in props or sel.two_handed
    if sel.two_handed and WeaponProperty.VERSATILE not in props:
        raise _refuse(
            RefusalKind.INVALID_SELECTION, f"{weapon.record} is not Versatile"
        )
    if two_hands and shield_held:
        raise _refuse(RefusalKind.INVALID_SELECTION, "a Shield leaves no second hand")

    ranged = weapon.range_class is RangeClass.RANGED or sel.thrown
    if sel.thrown and WeaponProperty.THROWN not in props:
        raise _refuse(RefusalKind.INVALID_SELECTION, f"{weapon.record} can't be thrown")

    # The ability.
    rules = facts_of(index, "play.d20_tests", "attack_ability_modifier")
    by_class = {
        f.range_class: f.ability for f in rules if isinstance(f, AttackRollAbilityFact)
    }
    ability = by_class.get(weapon.range_class)
    if ability is None:
        raise _refuse(RefusalKind.MISSING_AUTHORITY, "no typed attack ability")
    options = [
        f
        for f in facts_of(index, "equipment.weapons.finesse", "finesse")
        if isinstance(f, AttackAbilityOptionFact)
    ]
    if WeaponProperty.FINESSE in props:
        if not options:
            raise _refuse(
                RefusalKind.MISSING_AUTHORITY, "Finesse states no ability option"
            )
        if sel.ability is None:
            raise _refuse(
                RefusalKind.INVALID_SELECTION, "a Finesse attack names its ability"
            )
        try:
            chosen = AbilityScore(sel.ability)
        except ValueError:
            raise _refuse(
                RefusalKind.INVALID_SELECTION, f"{sel.ability!r} is not an ability"
            ) from None
        if chosen not in options[0].abilities:
            raise _refuse(
                RefusalKind.INVALID_SELECTION, f"Finesse does not admit {chosen.value}"
            )
        ability = chosen
    elif sel.ability is not None and AbilityScore(sel.ability) is not ability:
        raise _refuse(
            RefusalKind.INVALID_SELECTION, f"{weapon.record} uses {ability.value}"
        )

    score, _ = ability_score(index, state, ability)
    modifier = (score - 10) // 2
    level = sum(c.level for c in state.classes or ())
    breakdown = {f"{ability.value}_modifier": modifier}
    proficient = weapon_proficiency(
        index, state, weapon.record, weapon.category, frozenset(props)
    )
    if proficient:
        application = [
            f
            for f in facts_of(index, "play.proficiency", "weapon_proficiency")
            if isinstance(f, ProficiencyApplicationFact)
            and f.proficiency is ProficiencyKind.WEAPON
        ]
        if not application:
            raise _refuse(
                RefusalKind.MISSING_AUTHORITY, "no typed weapon proficiency rule"
            )
        breakdown["proficiency_bonus"] = proficiency_bonus(index, level)

    # Advantage and Disadvantage.
    advantage, disadvantage = _condition_sources(actor, RollActor.SUBJECT, ability)
    a2, d2 = _condition_sources(target, RollActor.AGAINST_SUBJECT, ability)
    advantage += a2
    disadvantage += d2
    if WeaponProperty.HEAVY in props:
        for req in facts_of(index, "equipment.weapons.heavy", "heavy"):
            if (
                isinstance(req, AbilityScoreRequirementFact)
                and req.range_class
                is (RangeClass.RANGED if ranged else RangeClass.MELEE)
                and ability_score(index, state, req.ability)[0] < req.minimum
            ):
                disadvantage.append("equipment.weapons.heavy/heavy")
    if untrained_armor(actor, index) and ability in (
        AbilityScore.STRENGTH,
        AbilityScore.DEXTERITY,
    ):
        penalty = [
            f
            for f in facts_of(index, "equipment.armor", "light_medium_or_heavy_armor")
            if isinstance(f, ArmorTrainingPenaltyFact)
        ]
        if not penalty:
            raise _refuse(
                RefusalKind.MISSING_AUTHORITY, "no typed armor training penalty"
            )
        disadvantage.append("equipment.armor/light_medium_or_heavy_armor")

    # Range.
    band = _one(
        facts_of(index, "equipment.weapons.range", "range"), RangeBandRuleFact, "range"
    )
    if not ranged:
        if sel.range != "within_reach":
            raise _refuse(
                RefusalKind.INVALID_SELECTION,
                "a melee attack needs its target within the weapon's reach",
            )
    else:
        if sel.range == "within_reach":
            raise _refuse(
                RefusalKind.INVALID_SELECTION, "a ranged attack is made at a range band"
            )
        if (
            sel.range == "beyond_long_range"
            and band.beyond_long.value == "cannot_attack"
        ):
            raise _refuse(
                RefusalKind.INVALID_SELECTION, "the target is beyond long range"
            )
        if sel.range == "beyond_normal_within_long_range":
            disadvantage.append("equipment.weapons.range/range")
        if sel.hostile_within_5_feet is None:
            raise _refuse(
                RefusalKind.MISSING_STATE,
                "a ranged attack needs whether a hostile creature is within 5 feet",
            )
        if sel.hostile_within_5_feet:
            disadvantage.append("play.combat/close_combat")

    # The target's AC, with cover.
    ac = armor_class(target)
    ac_breakdown = dict(ac.breakdown)
    if sel.cover != "none":
        bonuses = [
            f
            for f in facts_of(index, "play.combat", "cover_degrees")
            if isinstance(f, CoverDefensiveBonusFact) and f.degree.value == sel.cover
        ]
        if len(bonuses) != 1:
            raise _refuse(
                RefusalKind.MISSING_AUTHORITY, f"no typed {sel.cover} cover bonus"
            )
        ac_breakdown["cover"] = bonuses[0].bonus

    # Damage.
    dice = weapon.damage.dice
    if sel.two_handed:
        versatile = props[WeaponProperty.VERSATILE].versatile_damage
        if versatile is None:
            raise _refuse(
                RefusalKind.MISSING_AUTHORITY,
                f"{weapon.record} states no Versatile die",
            )
        dice = versatile
    if dice is None or weapon.damage.damage_type is None:
        raise _refuse(
            RefusalKind.MISSING_AUTHORITY, f"{weapon.record} states no damage dice"
        )
    preflight(target, weapon.damage.damage_type)
    rule = _one(
        facts_of(index, "play.damage_and_healing", "damage_rolls"),
        DamageRollRuleFact,
        "damage rolls",
    )
    critical = _one(
        facts_of(index, "play.damage_and_healing", "critical_hits"),
        CriticalDamageFact,
        "critical hits",
    )
    return PreparedAttack(
        selection=sel,
        weapon=weapon.record,
        target=target,
        ability=ability,
        attack_modifier=sum(breakdown.values()),
        damage_dice=dice,
        damage_type=weapon.damage.damage_type,
        damage_modifier=modifier if rule.adds_attack_ability_modifier else 0,
        minimum_damage=rule.minimum_damage,
        critical_multiplier=critical.damage_dice_multiplier,
        target_ac=sum(ac_breakdown.values()),
        advantage_sources=tuple(advantage),
        disadvantage_sources=tuple(disadvantage),
        certificate=certificate,
        breakdown=breakdown,
        ac_breakdown=ac_breakdown,
    )


def roll(
    prepared: PreparedAttack, dice: DiceService, actor: TurnCharacter
) -> RolledAttack:
    """Roll the attack; on a hit, roll damage and derive its effects."""
    index = actor.index
    assert index is not None
    attack = dice.roll(prepared.expression)
    natural = {
        f.face: f
        for f in facts_of(index, "play.d20_tests")
        if isinstance(f, NaturalRollOutcomeFact)
        and f.context is RollContext.ATTACK_ROLL
    }
    face = natural.get(attack.chosen)
    total = attack.chosen + prepared.attack_modifier
    if face is not None:
        hit = face.outcome.value == "hit"
        critical = hit and face.critical_hit
    else:
        hit, critical = total >= prepared.target_ac, False
    if not hit:
        return RolledAttack(prepared, attack.raw_rolls, attack.chosen, False, False)
    d = prepared.damage_dice
    count = d.count * (prepared.critical_multiplier if critical else 1)
    damage_roll = dice.roll(f"{count}{d.die.value}")
    amount = max(
        prepared.minimum_damage,
        damage_roll.chosen + d.modifier + prepared.damage_modifier,
    )
    taken = take_damage(
        prepared.target, amount, prepared.damage_type, critical=critical
    )
    return RolledAttack(
        prepared,
        attack.raw_rolls,
        attack.chosen,
        True,
        critical,
        damage_roll.raw_rolls,
        taken,
    )


def subject_key(subject: TurnSubject) -> tuple[str, str]:
    kind = "creature" if isinstance(subject, TurnCreature) else "character"
    return kind, str(subject.subject_id)
