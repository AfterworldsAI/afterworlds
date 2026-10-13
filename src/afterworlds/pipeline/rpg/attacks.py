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
from collections.abc import Callable
from dataclasses import dataclass, field
from uuid import uuid4

from afterworlds.ingestion.mechanical.models import ComponentHandling
from afterworlds.ingestion.mechanical.representation import (
    AbilityScore,
    AbilityScoreRequirementFact,
    AdvantageFact,
    AdvantageState,
    AmmunitionSupplyFact,
    ArmorTrainingPenaltyFact,
    AttackAbilityOptionFact,
    AttackRollAbilityFact,
    AutomaticOutcomeFact,
    ConditionEffectKind,
    ConditionKind,
    ContributorPredicate,
    CoverDefensiveBonusFact,
    CreatureRollModifierFact,
    CreatureSize,
    CreatureSizeFact,
    CriticalDamageFact,
    CriticalHitChange,
    CriticalHitRuleFact,
    DamageFact,
    DamageRollRuleFact,
    DamageType,
    DiceExpression,
    EntrySubject,
    FormulaTerm,
    LightExtraAttackFact,
    MasteryDamage,
    MasteryDamageType,
    MasteryEffectFact,
    MasteryTrigger,
    ModifierDamage,
    NaturalRollOutcomeFact,
    ProficiencyApplicationFact,
    ProficiencyKind,
    RangeBandRuleFact,
    RangeClass,
    RecordKind,
    RecurrenceBoundary,
    RollActor,
    RollContext,
    TurnWhich,
    WeaponCategory,
    WeaponCategoryFact,
    WeaponMastery,
    WeaponMasteryFact,
    WeaponProperty,
    WeaponPropertyFact,
    WeaponRangeClassFact,
)
from afterworlds.models.dnd5e_state import (
    ConditionInstance,
    Dnd5eCharacterState,
    RecordChoice,
    TurnCoordination,
)
from afterworlds.models.enums import ConditionVisibility
from afterworlds.models.rpg import RollProposal, SheetEffect, WeaponAttackSelection
from afterworlds.pipeline.rpg import bystanders
from afterworlds.pipeline.rpg.capability import (
    AdjudicationRefusal,
    Certificate,
    Operation,
    RefusalKind,
    certify,
    governing_fingerprint,
)
from afterworlds.pipeline.rpg.checks import proficiency_bonus
from afterworlds.pipeline.rpg.conditions import effective
from afterworlds.pipeline.rpg.damage import (
    DamageTaken,
    bloodied,
    knockout_rule,
    preflight,
    take_damage,
)
from afterworlds.pipeline.rpg.damage import possible_conditions as damage_conditions
from afterworlds.pipeline.rpg.defense import (
    armor_class,
    condition_immune,
    facts_of,
    template_digests,
    untrained_armor,
)
from afterworlds.pipeline.rpg.defense import template as template_of
from afterworlds.pipeline.rpg.dice import DiceService
from afterworlds.pipeline.rpg.grants import (
    ability_score,
    weapon_mastery,
    weapon_proficiency,
)
from afterworlds.pipeline.rpg.hands import check_weapon_grip
from afterworlds.pipeline.rpg.mastery import (
    attack_effects,
    new_effect,
    other_effects,
)
from afterworlds.pipeline.rpg.saves import PreparedSave
from afterworlds.pipeline.rpg.saves import prepare as prepare_save
from afterworlds.pipeline.rpg.saves import roll as roll_save
from afterworlds.services.dnd5e_state.authority import AuthorityIndex
from afterworlds.services.dnd5e_state.holdings import ItemInstance
from afterworlds.services.dnd5e_state.turn import (
    ITEM_QUANTITY,
    TurnCharacter,
    TurnCreature,
    TurnSubject,
)

__all__ = [
    "ATTACK_CONTRIBUTORS",
    "possible_conditions",
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
    #: ``None`` for a weapon printing a flat amount (the Blowgun's 1).
    damage_dice: DiceExpression | None
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
    #: Rules that make any hit a Critical Hit (Paralyzed, Unconscious).
    automatic_critical: tuple[str, ...] = ()
    #: Each creature subject's certified template digest.
    templates: dict[str, str] = field(default_factory=dict)
    #: The attacker's mastery effects this roll spends (Sap, Vex).
    spent: tuple[SheetEffect, ...] = ()
    #: The weapon's mastery property this attack uses, if any.
    mastery: _Mastery | None = None
    #: A weapon's flat printed damage, when it prints no dice.
    flat_damage: int | None = None
    #: The ammunition fired: item, record, kind (CRD Issue 15c C7).
    ammunition: dict[str, object] | None = None

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
    mastery_effects: tuple[SheetEffect, ...] = ()
    mastery_result: dict[str, object] | None = None

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
        own = self.damage.effects if self.damage else ()
        return (*self.prepared.spent, *own, *self.mastery_effects)

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
                "automatic_critical": list(p.automatic_critical),
                "hit": self.hit,
                "critical": self.critical,
                "damage_rolls": list(self.damage_rolls),
                "damage": self.damage.provenance() if self.damage else None,
                "mastery": self.mastery_result,
                "ammunition": p.ammunition,
                "certificate": p.certificate.as_json(),
                "templates": p.templates,
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


#: How each Rules Glossary condition component bears on a weapon attack
#: between its attacker and target, reviewed component by component:
#:
#: * ``rolls``: its typed Advantage/automatic-outcome facts, applied by whose
#:   roll and which context they name;
#: * ``no_action``: an attacker that can't take actions can't attack;
#: * ``charmer``: a Charmed attacker can't attack its charmer;
#: * ``auto_critical``: a hit from within 5 feet is a Critical Hit;
#: * ``prone_against``: Advantage from within 5 feet, else Disadvantage
#:   (prose-bound, executed by hand and governed by the component);
#: * ``damage``: changes the damage; :func:`.damage.preflight` applies or
#:   refuses it for every damage caller;
#: * ``none``: reviewed as not bearing on the attack (movement, speech,
#:   concentration; implied conditions are read through
#:   :func:`.conditions.effective`; sight refuses separately).
#:
#: A component not listed refuses: a binding may never add one silently.
_G = "glossary."
_ATTACK_RULES: dict[tuple[str, str], str] = {
    (_G + "blinded", "cant_see"): "rolls",
    (_G + "blinded", "attacks_affected"): "rolls",
    (_G + "charmed", "cant_harm_the_charmer"): "charmer",
    (_G + "charmed", "social_advantage"): "none",
    (_G + "deafened", "cant_hear"): "rolls",
    (_G + "frightened", "ability_checks_and_attacks_affected"): "rolls",
    (_G + "frightened", "cant_approach"): "none",
    (_G + "grappled", "attacks_affected"): "rolls",
    (_G + "grappled", "movable"): "none",
    (_G + "grappled", "speed_0"): "none",
    (_G + "incapacitated", "inactive"): "no_action",
    (_G + "incapacitated", "no_concentration"): "none",
    (_G + "incapacitated", "speechless"): "none",
    (_G + "incapacitated", "surprised"): "rolls",
    (_G + "invisible", "attacks_affected"): "rolls",
    (_G + "invisible", "concealed"): "none",
    (_G + "invisible", "surprise"): "rolls",
    (_G + "paralyzed", "automatic_critical_hits"): "auto_critical",
    (_G + "paralyzed", "attacks_affected"): "rolls",
    (_G + "paralyzed", "incapacitated"): "none",
    (_G + "paralyzed", "saving_throws_affected"): "rolls",
    (_G + "paralyzed", "speed_0"): "none",
    (_G + "petrified", "turned_to_inanimate_substance"): "none",
    (_G + "petrified", "attacks_affected"): "rolls",
    (_G + "petrified", "incapacitated"): "none",
    (_G + "petrified", "poison_immunity"): "none",
    (_G + "petrified", "resist_damage"): "damage",
    (_G + "petrified", "saving_throws_affected"): "rolls",
    (_G + "petrified", "speed_0"): "none",
    (_G + "poisoned", "ability_checks_and_attacks_affected"): "rolls",
    (_G + "prone", "attacks_against_affected"): "prone_against",
    (_G + "prone", "own_attacks_affected"): "rolls",
    (_G + "prone", "restricted_movement"): "none",
    (_G + "restrained", "attacks_affected"): "rolls",
    (_G + "restrained", "saving_throws_affected"): "rolls",
    (_G + "restrained", "speed_0"): "none",
    (_G + "stunned", "attacks_affected"): "rolls",
    (_G + "stunned", "incapacitated"): "none",
    (_G + "stunned", "saving_throws_affected"): "rolls",
    (_G + "unconscious", "automatic_critical_hits"): "auto_critical",
    (_G + "unconscious", "attacks_affected"): "rolls",
    (_G + "unconscious", "inert"): "none",
    (_G + "unconscious", "remains_prone"): "none",
    (_G + "unconscious", "saving_throws_affected"): "rolls",
    (_G + "unconscious", "speed_0"): "none",
    (_G + "unconscious", "unaware"): "none",
}


def trait_applies(
    holder: TurnSubject,
    other: TurnSubject,
    when: ContributorPredicate | None,
    melee: bool,
    where: str,
    *,
    attacking: bool,
    allies: Callable[[], bool] | None = None,
) -> bool:
    """Whether a creature's standing trait applies to this attack: each
    stated circumstance derived in code, or refused. *holder* holds the trait
    and is attacking (*attacking*) or attacked; *other* is the attack's other
    subject. *allies* settles Pack Tactics' named allies when attacking."""
    if when is None:
        return True
    ally = when.ally_within_ft_of_target is not None or when.ally_not is not None
    if (
        when.stated is not None
        or (when.target_missing_hit_points and not attacking)
        or (
            ally
            and (
                allies is None
                or when.ally_within_ft_of_target != 5
                or when.ally_not is not ConditionKind.INCAPACITATED
            )
        )
    ):
        raise _refuse(
            RefusalKind.UNSUPPORTED_CAPABILITY,
            f"{where}'s circumstance is not executable here",
        )
    applies = True
    if when.subject_bloodied:
        applies = bloodied(holder)
    if when.subject_not is not None:
        assert holder.index is not None
        applies = applies and all(
            e.condition is not when.subject_not for e in effective(holder, holder.index)
        )
    if when.attack is not None:
        applies = applies and (when.attack is RangeClass.MELEE) is melee
    if when.target_missing_hit_points:
        hp = other.stored.state.hit_points
        if hp is None:
            raise _refuse(RefusalKind.MISSING_STATE, "the target records no hit points")
        applies = applies and hp.current < hp.maximum - (hp.maximum_reduction or 0)
    if ally and applies:
        assert allies is not None
        applies = allies()
    return applies


def creature_traits(
    holder: TurnSubject,
    other: TurnSubject,
    melee: bool,
    out: _Modifiers,
    *,
    attacking: bool,
    allies: Callable[[], bool] | None = None,
) -> None:
    """A creature's standing traits on an attack it makes (*attacking*) or
    that is made against it: Advantage/Disadvantage applied, anything else
    refused, never ignored."""
    if not isinstance(holder, TurnCreature):
        return
    assert holder.index is not None
    side = RollActor.SUBJECT if attacking else RollActor.AGAINST_SUBJECT
    template = template_of(holder)
    for fact in facts_of(holder.index, template):
        if not isinstance(fact, CreatureRollModifierFact):
            continue
        rolls = [
            e
            for e in fact.effects
            if e.roll.context in (RollContext.ATTACK_ROLL, RollContext.D20_TEST)
            and e.roll.actor is side
        ]
        if not rolls:
            continue
        where = f"{template}/{fact.entry}"
        if fact.subject is not EntrySubject.SELF or any(
            not isinstance(e, AdvantageFact) for e in rolls
        ):
            raise _refuse(
                RefusalKind.UNSUPPORTED_CAPABILITY,
                f"{where} changes this attack and is not executable here",
            )
        if trait_applies(
            holder,
            other,
            fact.applies_when,
            melee,
            where,
            attacking=attacking,
            allies=allies,
        ):
            for e in rolls:
                assert isinstance(e, AdvantageFact)
                (
                    out.advantage
                    if e.state is AdvantageState.ADVANTAGE
                    else out.disadvantage
                ).append(where)


@dataclass
class _Modifiers:
    advantage: list[str] = field(default_factory=list)
    disadvantage: list[str] = field(default_factory=list)
    automatic_critical: list[str] = field(default_factory=list)


def _conditions(
    subject: TurnSubject,
    actor: RollActor,
    other: TurnSubject,
    within_5_feet: bool | None,
    out: _Modifiers,
) -> None:
    """Apply *subject*'s conditions to an attack made by (``SUBJECT``) or
    against (``AGAINST_SUBJECT``) it; *other* is the attack's other subject."""
    index = subject.index
    assert index is not None
    attacking = actor is RollActor.SUBJECT
    for eff in effective(subject, index):
        if eff.condition is ConditionKind.EXHAUSTION:
            raise _refuse(
                RefusalKind.UNSUPPORTED_CAPABILITY,
                "Exhaustion's D20 Test reduction is not executable here",
            )
        if eff.condition in _SIGHT_CONDITIONS:
            raise _refuse(
                RefusalKind.UNSUPPORTED_CAPABILITY,
                f"{eff.condition.value}: sight that depends on a sense's "
                "range is not executable here",
            )
        record = index.record(f"glossary.{eff.condition.value}")
        assert record is not None  # effective() refuses an absent record
        for component in record.components:
            key = (record.semantic_key, component.semantic_key)
            where = "/".join(key)
            rule = _ATTACK_RULES.get(key)
            if rule is None:
                raise _refuse(
                    RefusalKind.UNSUPPORTED_CAPABILITY,
                    f"{where} has not been reviewed for weapon attacks",
                )
            if rule == "no_action" and attacking:
                raise _refuse(
                    RefusalKind.INVALID_SELECTION,
                    f"the attacker is {eff.condition.value} and can't take "
                    f"actions ({where})",
                )
            if rule == "charmer" and attacking:
                referent = eff.instance.referent if eff.instance else None
                if referent is None:
                    raise _refuse(
                        RefusalKind.MISSING_STATE,
                        "the attacker is Charmed and its charmer is not recorded",
                    )
                if str(referent.subject_id) == str(other.subject_id):
                    raise _refuse(
                        RefusalKind.INVALID_SELECTION,
                        f"a Charmed attacker can't attack its charmer ({where})",
                    )
            if rule in ("auto_critical", "prone_against") and not attacking:
                if within_5_feet is None:
                    raise _refuse(
                        RefusalKind.MISSING_STATE,
                        f"{where} turns on whether the attacker is within 5 feet "
                        "of the target",
                    )
                if rule == "auto_critical":
                    if not any(
                        isinstance(ef.fact, CriticalHitRuleFact)
                        and ef.fact.change is CriticalHitChange.AUTOMATIC_ON_HIT
                        for ef in component.facts
                    ):
                        raise _refuse(
                            RefusalKind.MISSING_AUTHORITY, f"{where} is not typed"
                        )
                    if within_5_feet:
                        out.automatic_critical.append(where)
                elif within_5_feet:
                    out.advantage.append(where)
                else:
                    out.disadvantage.append(where)
            if rule != "rolls":
                continue
            for ef in component.facts:
                fact = ef.fact
                if not isinstance(fact, (AdvantageFact, AutomaticOutcomeFact)):
                    continue
                spec = fact.roll
                contexts = (RollContext.ATTACK_ROLL, RollContext.D20_TEST)
                if spec.actor is not actor or spec.context not in contexts:
                    continue
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
                    out.advantage.append(where)
                else:
                    out.disadvantage.append(where)


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


@dataclass(frozen=True)
class _Mastery:
    """The mastery property this attack uses, fixed before any die."""

    name: WeaponMastery
    rule: MasteryEffectFact
    save: PreparedSave | None = None
    push_ft: int | None = None


#: Masteries whose use waits on a classification: Nick and the Light extra
#: attack need to know which attack is the Attack action's (action economy,
#: surfaced for Codex); Cleave's extra attack is its own operation.
#: Nick is not a selected property: it is the ``extra="nick"`` attack.
_HELD_MASTERIES: dict[WeaponMastery, str] = {}


def _mastery(
    sel: WeaponAttackSelection,
    actor: TurnCharacter,
    target: TurnSubject,
    weapon: _Weapon,
    ability_modifier: int,
    level: int,
) -> _Mastery | None:
    """The weapon's mastery property, when the wielder's validated Weapon
    Mastery choice covers the weapon and the property applies (optional ones
    only when selected); a selection it can't honour refuses."""
    index = actor.index
    assert index is not None
    printed = [
        f for f in facts_of(index, weapon.record) if isinstance(f, WeaponMasteryFact)
    ]
    has = len(printed) == 1 and weapon_mastery(
        index, actor.stored.state, weapon.record, weapon.category
    )
    if not has:
        if sel.mastery or sel.push_ft is not None:
            raise _refuse(
                RefusalKind.INVALID_SELECTION,
                f"the wielder can't use {weapon.record}'s mastery property",
            )
        return None
    name = printed[0].mastery
    record = f"equipment.weapons.{name.value}"
    rules = [f for f in facts_of(index, record) if isinstance(f, MasteryEffectFact)]
    if len(rules) != 1:
        raise _refuse(RefusalKind.MISSING_AUTHORITY, f"{record} is not typed")
    rule = rules[0]
    if rule.optional and not sel.mastery:
        if sel.push_ft is not None:
            raise _refuse(RefusalKind.INVALID_SELECTION, "a push needs Push selected")
        return None
    if not rule.optional and sel.mastery:
        raise _refuse(
            RefusalKind.INVALID_SELECTION, f"{name.value} is not a property to select"
        )
    if name is WeaponMastery.CLEAVE and (
        rule.trigger is not MasteryTrigger.HIT_MELEE_ATTACK_ROLL
        or weapon.range_class is not RangeClass.MELEE
        or sel.thrown
    ):
        raise _refuse(
            RefusalKind.INVALID_SELECTION, "Cleave follows a melee attack's hit"
        )
    if name is WeaponMastery.NICK:
        raise _refuse(
            RefusalKind.INVALID_SELECTION,
            "Nick is used as the Light property's extra attack (extra='nick'), not "
            "selected on an attack",
        )
    if name in _HELD_MASTERIES:
        raise _refuse(
            RefusalKind.UNSUPPORTED_CAPABILITY,
            f"{name.value} waits on {_HELD_MASTERIES[name]}",
        )
    if name is WeaponMastery.PUSH:
        if sel.push_ft is None or rule.distance_ft_up_to is None:
            raise _refuse(RefusalKind.INVALID_SELECTION, "a push names its distance")
        if sel.push_ft > rule.distance_ft_up_to:
            raise _refuse(
                RefusalKind.INVALID_SELECTION,
                f"Push moves a creature up to {rule.distance_ft_up_to} feet",
            )
        if rule.maximum_size is None or _size(target) not in _SIZES_UP_TO(
            rule.maximum_size
        ):
            raise _refuse(
                RefusalKind.INVALID_SELECTION,
                "Push moves a creature no larger than "
                f"{rule.maximum_size.value if rule.maximum_size else '?'}",
            )
        return _Mastery(name, rule, push_ft=sel.push_ft)
    if sel.push_ft is not None:
        raise _refuse(RefusalKind.INVALID_SELECTION, "only Push moves the target")
    if name is WeaponMastery.TOPPLE:
        if rule.save is None or rule.dc is None:
            raise _refuse(RefusalKind.MISSING_AUTHORITY, "Topple's save is not typed")
        terms = {
            FormulaTerm.ATTACK_ABILITY_MODIFIER: ability_modifier,
            FormulaTerm.PROFICIENCY_BONUS: proficiency_bonus(index, level),
        }
        if any(term not in terms for term in rule.dc.plus):
            raise _refuse(RefusalKind.MISSING_AUTHORITY, "Topple's DC is not typed")
        dc = rule.dc.base + sum(terms[term] for term in rule.dc.plus)
        imposes = frozenset(
            e.condition
            for e in rule.on_failure
            if e.effect is ConditionEffectKind.APPLIES
        )
        save = prepare_save(target, rule.save, dc, f"{record}/{name.value}", imposes)
        return _Mastery(name, rule, save=save)
    if name in (WeaponMastery.SAP, WeaponMastery.VEX, WeaponMastery.SLOW) and (
        rule.duration is None or rule.duration.turn is not TurnWhich.NEXT
    ):
        raise _refuse(
            RefusalKind.MISSING_AUTHORITY, f"{name.value}'s duration is not typed"
        )
    if name is WeaponMastery.GRAZE and (
        rule.damage is not MasteryDamage.ATTACK_ABILITY_MODIFIER
        or rule.damage_type is not MasteryDamageType.WEAPON
    ):
        raise _refuse(RefusalKind.MISSING_AUTHORITY, "Graze's damage is not typed")
    return _Mastery(name, rule)


def _cleave_rule(
    sel: WeaponAttackSelection, actor: TurnCharacter, weapon: _Weapon, ranged: bool
) -> MasteryEffectFact:
    """Validate Cleave's extra attack: a melee attack with a Cleave weapon the
    wielder's mastery covers, against a creature within reach and, on the
    GameMaster's fact, within 5 feet of the first (OD-15c-1)."""
    index = actor.index
    assert index is not None
    printed = [
        f for f in facts_of(index, weapon.record) if isinstance(f, WeaponMasteryFact)
    ]
    if (
        len(printed) != 1
        or printed[0].mastery is not WeaponMastery.CLEAVE
        or not weapon_mastery(index, actor.stored.state, weapon.record, weapon.category)
    ):
        raise _refuse(
            RefusalKind.INVALID_SELECTION,
            f"the wielder can't Cleave with {weapon.record}",
        )
    rules = [
        f
        for f in facts_of(index, "equipment.weapons.cleave", "cleave")
        if isinstance(f, MasteryEffectFact)
    ]
    if len(rules) != 1 or rules[0].second_target_within_ft != 5:
        raise _refuse(RefusalKind.MISSING_AUTHORITY, "Cleave is not typed")
    if ranged or sel.mastery:
        raise _refuse(
            RefusalKind.INVALID_SELECTION,
            "Cleave's extra attack is a melee attack using no further mastery",
        )
    if sel.cleave_within_5_feet is None:
        raise _refuse(
            RefusalKind.MISSING_STATE,
            "Cleave needs whether the second creature is within 5 feet of the first",
        )
    if not sel.cleave_within_5_feet:
        raise _refuse(
            RefusalKind.INVALID_SELECTION,
            "Cleave's second creature must be within 5 feet of the first",
        )
    return rules[0]


_ORDER = tuple(CreatureSize)


def _SIZES_UP_TO(maximum: CreatureSize) -> set[CreatureSize]:  # noqa: N802
    return set(_ORDER[: _ORDER.index(maximum) + 1])


def _size(subject: TurnSubject) -> CreatureSize | None:
    if isinstance(subject, TurnCreature):
        assert subject.index is not None
        sizes = [
            s
            for f in facts_of(subject.index, template_of(subject))
            if isinstance(f, CreatureSizeFact)
            for s in f.sizes
        ]
        return sizes[0] if len(sizes) == 1 else None
    return subject.stored.state.size


def _mastery_outcome(
    prepared: PreparedAttack,
    actor: TurnCharacter,
    dice: DiceService,
    hit: bool,
    taken: DamageTaken | None,
    coordination: TurnCoordination | None,
) -> tuple[list[SheetEffect], dict[str, object] | None]:
    """What the mastery does once the attack's dice are known."""
    m = prepared.mastery
    if m is None:
        return [], None
    target = prepared.target
    damaged = taken is not None and taken.taken > 0
    alive = taken is None or taken.outcome not in ("died", "died_massive_damage")
    trigger = m.rule.trigger
    applies = {
        MasteryTrigger.MISS_CREATURE: not hit,
        MasteryTrigger.HIT_CREATURE: hit,
        MasteryTrigger.HIT_AND_DAMAGE: hit and damaged,
        MasteryTrigger.HIT_MELEE_ATTACK_ROLL: hit,
    }.get(trigger)
    if applies is None:
        raise _refuse(RefusalKind.MISSING_AUTHORITY, f"{trigger.value} is not executed")
    if not applies:
        return [], {"mastery": m.name.value, "result": "not_triggered"}
    name = m.name
    if name is WeaponMastery.GRAZE:
        modifier = prepared.breakdown[f"{prepared.ability.value}_modifier"]
        grazed = take_damage(
            target, max(0, modifier), prepared.damage_type, critical=False
        )
        return list(grazed.effects), {
            "mastery": "graze",
            "result": "damaged",
            "damage": grazed.provenance(),
        }
    if name is WeaponMastery.PUSH:
        return [], {"mastery": "push", "result": "pushed", "feet": m.push_ft}
    if name is WeaponMastery.CLEAVE:
        # The extra attack is the next proposal (``cleave``).
        return [], {"mastery": "cleave", "result": "may_cleave"}
    if name is WeaponMastery.TOPPLE:
        assert m.save is not None
        if not alive:
            return [], {"mastery": "topple", "result": "target_died"}
        saved = roll_save(m.save, dice)
        out: dict[str, object] = {"mastery": "topple", "save": saved.provenance()}
        if saved.succeeded or condition_immune(target, ConditionKind.PRONE):
            return [], {**out, "result": "resisted" if saved.succeeded else "immune"}
        if any(c.condition is ConditionKind.PRONE for c in _conditions_of(target)):
            return [], {**out, "result": "already_prone"}
        return [
            SheetEffect(
                target="prone",
                operation="apply_condition",
                value_json=json.dumps(
                    {
                        "instance_id": str(uuid4()),
                        "condition": ConditionKind.PRONE.value,
                        "visibility": ConditionVisibility.VISIBLE.value,
                        "source": {
                            "record_key": "equipment.weapons.topple",
                            "component_key": "topple",
                        },
                    }
                ),
                subject_kind=subject_key(target)[0],  # type: ignore[arg-type]
                subject_id=target.subject_id,
            )
        ], {**out, "result": "prone"}
    if not alive:
        return [], {"mastery": name.value, "result": "target_died"}
    assert m.rule.duration is not None
    boundary = {
        RecurrenceBoundary.START_OF_TURN: "start",
        RecurrenceBoundary.END_OF_TURN: "end",
    }[m.rule.duration.until]
    if name is WeaponMastery.SAP:
        return [new_effect(target, "sap", actor, boundary, coordination)], {
            "mastery": "sap",
            "result": "applied",
        }
    if name is WeaponMastery.SLOW:
        if any(
            e.source.record_key == "equipment.weapons.slow"
            for e in target.stored.state.active_effects or ()
        ):
            return [], {"mastery": "slow", "result": "already_slowed"}
        return [new_effect(target, "slow", actor, boundary, coordination)], {
            "mastery": "slow",
            "result": "applied",
            "speed_reduction_ft": m.rule.speed_reduction_ft,
        }
    if name is WeaponMastery.VEX:
        return [new_effect(actor, "vex", actor, boundary, coordination, target)], {
            "mastery": "vex",
            "result": "applied",
        }
    raise _refuse(RefusalKind.UNSUPPORTED_CAPABILITY, f"{name.value} is not executed")


def _conditions_of(subject: TurnSubject) -> tuple[ConditionInstance, ...]:
    return subject.stored.state.conditions or ()


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

    # Contributors. Mastery effects are executed where they apply.
    unexecuted = other_effects(actor)
    if unexecuted:
        raise _refuse(
            RefusalKind.UNSUPPORTED_CAPABILITY,
            f"active effect {unexecuted[0].source.record_key} can change "
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
    if sel.two_handed and WeaponProperty.VERSATILE not in props:
        raise _refuse(
            RefusalKind.INVALID_SELECTION, f"{weapon.record} is not Versatile"
        )
    # The approved hand/grip facts establish that the weapon is in hand, and
    # how; equipped alone does not (Owner decision 2026-10-12).
    check_weapon_grip(actor, sel.hands, item, set(props), two_handed=sel.two_handed)
    ammunition: tuple[SheetEffect, dict[str, object]] | None = None
    if WeaponProperty.AMMUNITION in props:
        ammunition = _ammunition(actor, item, props[WeaponProperty.AMMUNITION], sel)
    elif sel.ammunition_item_id is not None:
        raise _refuse(
            RefusalKind.INVALID_SELECTION, f"{weapon.record} fires no ammunition"
        )

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

    # Advantage and Disadvantage. A melee attack with a 5-foot reach is made
    # from within 5 feet; otherwise the GameMaster's fact says (OD-15c-1).
    within_5_feet = sel.target_within_5_feet
    if not ranged and WeaponProperty.REACH not in props:
        if within_5_feet is False:
            raise _refuse(
                RefusalKind.INVALID_SELECTION,
                "a melee attack with a 5-foot reach is made from within 5 feet",
            )
        within_5_feet = True
    mods = _Modifiers()
    _conditions(actor, RollActor.SUBJECT, target, within_5_feet, mods)
    _conditions(target, RollActor.AGAINST_SUBJECT, actor, within_5_feet, mods)
    creature_traits(target, actor, not ranged, mods, attacking=False)
    advantage, disadvantage = mods.advantage, mods.disadvantage
    a3, d3, spent = attack_effects(actor, target)
    advantage += a3
    disadvantage += d3
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
        close = bystanders.enemies(sel.hostiles_within_5_feet, actor, actor, subjects)
        if close:
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
    if (
        dice is None and weapon.damage.flat_amount is None
    ) or weapon.damage.damage_type is None:
        raise _refuse(
            RefusalKind.MISSING_AUTHORITY, f"{weapon.record} states no damage dice"
        )
    preflight(target, weapon.damage.damage_type)
    if sel.knock_out:
        knockout = knockout_rule(target)
        if ranged or knockout.attack is not RangeClass.MELEE:
            raise _refuse(
                RefusalKind.INVALID_SELECTION,
                "only a melee attack can knock a creature out",
            )
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
    damage_modifier = modifier if rule.adds_attack_ability_modifier else 0
    mastery_used = _mastery(sel, actor, target, weapon, modifier, level)
    if sel.extra is not None:
        if sel.cleave or sel.mastery:
            raise _refuse(
                RefusalKind.INVALID_SELECTION,
                "Light's extra attack is neither Cleave's nor a mastery selection",
            )
        light = [
            f
            for f in facts_of(index, "equipment.weapons.light", "light")
            if isinstance(f, LightExtraAttackFact)
        ]
        if len(light) != 1:
            raise _refuse(RefusalKind.MISSING_AUTHORITY, "Light is not typed")
        if light[0].ability_modifier_damage is ModifierDamage.ONLY_IF_NEGATIVE:
            damage_modifier = min(0, damage_modifier)
    if sel.cleave:
        cleave = _cleave_rule(sel, actor, weapon, ranged)
        if cleave.ability_modifier_damage is ModifierDamage.ONLY_IF_NEGATIVE:
            damage_modifier = min(0, damage_modifier)
    return PreparedAttack(
        selection=sel,
        weapon=weapon.record,
        target=target,
        ability=ability,
        attack_modifier=sum(breakdown.values()),
        damage_dice=dice,
        flat_damage=weapon.damage.flat_amount if dice is None else None,
        damage_type=weapon.damage.damage_type,
        damage_modifier=damage_modifier,
        minimum_damage=rule.minimum_damage,
        critical_multiplier=critical.damage_dice_multiplier,
        target_ac=sum(ac_breakdown.values()),
        advantage_sources=tuple(advantage),
        disadvantage_sources=tuple(disadvantage),
        certificate=certificate,
        templates=template_digests(target),
        breakdown=breakdown,
        ac_breakdown=ac_breakdown,
        automatic_critical=tuple(mods.automatic_critical),
        spent=(*spent, *((ammunition[0],) if ammunition else ())),
        mastery=mastery_used,
        ammunition=ammunition[1] if ammunition else None,
    )


def _ammunition(
    actor: TurnCharacter,
    weapon: ItemInstance,
    rule: WeaponPropertyFact,
    sel: WeaponAttackSelection,
) -> tuple[SheetEffect, dict[str, object]]:
    """The ammunition this attack fires and the effect expending one, or a
    refusal: a held item whose typed ``ammunition_supply`` is the weapon's
    kind and, when narrowed, names this weapon (C7; firearm and sling
    bullets are distinct), with one left."""
    assert actor.index is not None
    if sel.ammunition_item_id is None:
        raise _refuse(
            RefusalKind.MISSING_STATE,
            f"{weapon.record_key} fires ammunition: name the held ammunition item",
        )
    ammo = next((i for i in actor.items if i.item_id == sel.ammunition_item_id), None)
    if ammo is None:
        raise _refuse(
            RefusalKind.INVALID_SELECTION, "the attacker holds no such ammunition"
        )
    supplies = [
        f
        for f in facts_of(actor.index, ammo.record_key)
        if isinstance(f, AmmunitionSupplyFact)
    ]
    if len(supplies) != 1:
        raise _refuse(
            RefusalKind.INVALID_SELECTION, f"{ammo.record_key} is not ammunition"
        )
    supply = supplies[0]
    record = actor.index.record(weapon.record_key)
    assert record is not None
    served = {
        (record.semantic_key, c.semantic_key)
        for c in record.components
        if any(
            isinstance(f.fact, WeaponPropertyFact)
            and f.fact.weapon_property is WeaponProperty.AMMUNITION
            for f in c.facts
        )
    }
    if supply.kind is not rule.ammunition or (
        supply.for_weapons is not None
        and not served & {(r.record_key, r.component_key) for r in supply.for_weapons}
    ):
        raise _refuse(
            RefusalKind.INVALID_SELECTION,
            f"{ammo.record_key} is not ammunition for {weapon.record_key}",
        )
    if ammo.quantity < 1:
        raise _refuse(RefusalKind.INVALID_SELECTION, f"no {ammo.record_key} is left")
    effect = SheetEffect(
        target=ITEM_QUANTITY,
        operation="delta",
        value_json=json.dumps({"item_id": str(ammo.item_id), "spend": 1}),
        subject_kind="character",
        subject_id=actor.subject_id,
    )
    return effect, {
        "item_id": str(ammo.item_id),
        "record": ammo.record_key,
        "kind": supply.kind.value,
        "quantity_before": ammo.quantity,
    }


def roll(
    prepared: PreparedAttack,
    dice: DiceService,
    actor: TurnCharacter,
    coordination: TurnCoordination | None = None,
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
    if hit and prepared.automatic_critical:
        critical = True
    if not hit:
        effects, result = _mastery_outcome(
            prepared, actor, dice, False, None, coordination
        )
        return RolledAttack(
            prepared,
            attack.raw_rolls,
            attack.chosen,
            False,
            False,
            mastery_effects=tuple(effects),
            mastery_result=result,
        )
    d = prepared.damage_dice
    if d is None:
        # A flat printed amount: no die to roll or to double on a Critical.
        rolled: tuple[int, ...] = ()
        base = prepared.flat_damage or 0
    else:
        count = d.count * (prepared.critical_multiplier if critical else 1)
        damage_roll = dice.roll(f"{count}{d.die.value}")
        rolled, base = damage_roll.raw_rolls, damage_roll.chosen + d.modifier
    amount = max(prepared.minimum_damage, base + prepared.damage_modifier)
    taken = take_damage(
        prepared.target,
        amount,
        prepared.damage_type,
        critical=critical,
        knock_out=prepared.selection.knock_out,
    )
    effects, result = _mastery_outcome(prepared, actor, dice, True, taken, coordination)
    return RolledAttack(
        prepared,
        attack.raw_rolls,
        attack.chosen,
        True,
        critical,
        rolled,
        taken,
        tuple(effects),
        result,
    )


def possible_conditions(
    proposal: RollProposal, subjects: dict[tuple[str, str], TurnSubject]
) -> dict[tuple[str, str], frozenset[ConditionKind]]:
    """Every condition this attack could apply, by subject, whatever the dice."""
    sel = proposal.weapon_attack
    if sel is None:
        return {}
    key = (sel.target.kind, str(sel.target.subject_id))
    target = subjects.get(key)
    if target is None:
        return {}
    knocked = {ConditionKind.UNCONSCIOUS} if sel.knock_out else set()
    if sel.mastery:
        # Topple's failed save leaves the target Prone.
        knocked.add(ConditionKind.PRONE)
    return {key: damage_conditions(target) | knocked}


def moved_subjects(proposal: RollProposal) -> set[tuple[str, str]]:
    """Subjects this attack could move (Push): a later operation's spatial
    facts about them, asserted before the move, are invalid (OD-15c-1)."""
    sel = proposal.weapon_attack
    if sel is None or sel.push_ft is None:
        return set()
    return {(sel.target.kind, str(sel.target.subject_id))}


def spatial_subjects(
    proposal: RollProposal, actor: TurnCharacter
) -> set[tuple[str, str]]:
    """The subjects this attack's spatial facts are about."""
    sel = proposal.weapon_attack
    if sel is None:
        return set()
    return {
        ("character", str(actor.subject_id)),
        (sel.target.kind, str(sel.target.subject_id)),
    }


def subject_key(subject: TurnSubject) -> tuple[str, str]:
    kind = "creature" if isinstance(subject, TurnCreature) else "character"
    return kind, str(subject.subject_id)


def topples(actor: TurnCharacter, sel: WeaponAttackSelection) -> bool:
    """Whether the selected weapon's printed mastery is Topple (a save)."""
    assert actor.index is not None
    item = next((i for i in actor.items if i.item_id == sel.weapon_item_id), None)
    if item is None:
        return False
    return any(
        isinstance(f, WeaponMasteryFact) and f.mastery is WeaponMastery.TOPPLE
        for f in facts_of(actor.index, item.record_key)
    )
