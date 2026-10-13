"""Creature and animal attacks — CRD Issue 15c.

A continuing creature of the story makes one printed attack entry of its own
template (``creature_attack``) against a character or creature. Every number
comes from typed authority under the attacker's exact binding, the target's
own binding and the GameMaster's approved contextual facts (OD-15c-1):

* the attack: the entry's typed ``creature_attack`` (printed bonus, reach or
  ranges, hit damage terms); the natural 1/20 rule; Advantage/Disadvantage
  from both subjects' conditions (reviewed per component, as for weapon
  attacks), the range band, close combat for a ranged attack, and a standing
  trait whose predicate the GameMaster's facts settle (Pack Tactics: an ally
  within 5 feet of the target that isn't Incapacitated);
* the target's AC and damage consequences, in its own binding;
* the hit effect: a typed condition (a size limit, Grappled's escape DC and
  grappler, a turn-bounded duration), or a typed save against one.

Anything printed that is not executed here refuses before any die: a
formula bonus, automatic hits, conditional advantage, damage by size or by
choice, runtime addends, speed changes, forced movement, conditional damage,
linked conditions, save exclusions by creature type, and usage limits
(Recharge, X/Day), which wait on usage-counter execution.
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from uuid import uuid4

from afterworlds.ingestion.mechanical.representation import (
    AdvantageFact,
    AdvantageState,
    ConditionEffectKind,
    ConditionKind,
    CreatureAttackFact,
    CreatureAttackRange,
    CreatureEntryUsageFact,
    CreatureMultiattackFact,
    CreatureRollModifierFact,
    DamageType,
    EntrySection,
    EntrySubject,
    NaturalRollOutcomeFact,
    RecurrenceBoundary,
    Rider,
    RiderSubject,
    RollActor,
    RollContext,
    TurnBoundary,
    TurnOwner,
    TurnWhich,
)
from afterworlds.models.dnd5e_state import TurnCoordination
from afterworlds.models.enums import ConditionVisibility
from afterworlds.models.rpg import CreatureAttackSelection, RollProposal, SheetEffect
from afterworlds.pipeline.rpg import creature_effects
from afterworlds.pipeline.rpg.attacks import (
    _SIGHT_LIGHT,
    _SIZES_UP_TO,
    _conditions,
    _Modifiers,
    _size,
    subject_key,
)
from afterworlds.pipeline.rpg.capability import (
    AdjudicationRefusal,
    Certificate,
    Operation,
    RefusalKind,
    certify,
    governing_fingerprint,
)
from afterworlds.pipeline.rpg.damage import DamageTaken, preflight, take_damage
from afterworlds.pipeline.rpg.defense import (
    armor_class,
    condition_immune,
    facts_of,
    template_digests,
)
from afterworlds.pipeline.rpg.defense import template as template_of
from afterworlds.pipeline.rpg.dice import DiceService
from afterworlds.pipeline.rpg.mastery import other_effects, reference
from afterworlds.pipeline.rpg.saves import PreparedSave, RolledSave
from afterworlds.pipeline.rpg.saves import prepare as prepare_save
from afterworlds.pipeline.rpg.saves import roll as roll_save
from afterworlds.services.dnd5e_state.turn import (
    TurnCharacter,
    TurnCreature,
    TurnSubject,
    with_effects,
)

__all__ = [
    "PreparedCreatureAttack",
    "RolledCreatureAttack",
    "check_multiattack",
    "multiattack_key",
    "possible_conditions",
    "prepare",
    "roll",
]


def _refuse(kind: RefusalKind, detail: str) -> AdjudicationRefusal:
    return AdjudicationRefusal(kind, detail)


@dataclass(frozen=True)
class PreparedCreatureAttack:
    selection: CreatureAttackSelection
    attacker: TurnCreature
    target: TurnSubject
    fact: CreatureAttackFact
    attack_bonus: int
    target_ac: int
    advantage_sources: tuple[str, ...]
    disadvantage_sources: tuple[str, ...]
    automatic_critical: tuple[str, ...]
    certificate: Certificate
    rider_save: PreparedSave | None = None
    ac_breakdown: dict[str, int] = field(default_factory=dict)
    usage: CreatureEntryUsageFact | None = None
    #: Each creature subject's certified template digest.
    templates: dict[str, str] = field(default_factory=dict)

    @property
    def expression(self) -> str:
        adv, dis = bool(self.advantage_sources), bool(self.disadvantage_sources)
        if adv and not dis:
            return "2d20kh1"
        if dis and not adv:
            return "2d20kl1"
        return "1d20"


@dataclass(frozen=True)
class RolledCreatureAttack:
    prepared: PreparedCreatureAttack
    raw_rolls: tuple[int, ...]
    chosen: int
    hit: bool
    critical: bool
    damage_rolls: tuple[int, ...] = ()
    damage: tuple[DamageTaken, ...] = ()
    rider_effects: tuple[SheetEffect, ...] = ()
    rider: dict[str, object] | None = None

    @property
    def total(self) -> int:
        return self.chosen + self.prepared.attack_bonus

    @property
    def outcome(self) -> str:
        if self.critical:
            return "critical_success"
        return "success" if self.hit else "failure"

    @property
    def effects(self) -> tuple[SheetEffect, ...]:
        return (*(e for d in self.damage for e in d.effects), *self.rider_effects)

    def provenance_json(self) -> str:
        p = self.prepared
        return json.dumps(
            {
                "operation": Operation.CREATURE_ATTACK.value,
                "attacker": {
                    "kind": "creature",
                    "subject_id": str(p.attacker.subject_id),
                },
                "entry": p.fact.entry,
                "target": {
                    "kind": p.selection.target.kind,
                    "subject_id": str(p.selection.target.subject_id),
                },
                "visible_total": p.attack_bonus,
                "target_ac": p.target_ac,
                "ac_breakdown": p.ac_breakdown,
                "contextual_facts": p.selection.model_dump(
                    mode="json", exclude={"attacker", "target", "entry"}
                ),
                "advantage_sources": list(p.advantage_sources),
                "disadvantage_sources": list(p.disadvantage_sources),
                "automatic_critical": list(p.automatic_critical),
                "hit": self.hit,
                "critical": self.critical,
                "damage_rolls": list(self.damage_rolls),
                "damage": [d.provenance() for d in self.damage],
                "rider": self.rider,
                "certificate": p.certificate.as_json(),
                "templates": p.templates,
            },
            sort_keys=True,
        )


def _attack_fact(attacker: TurnCreature, entry: str) -> CreatureAttackFact:
    assert attacker.index is not None
    template = template_of(attacker)
    found = [
        f
        for f in facts_of(attacker.index, template)
        if isinstance(f, CreatureAttackFact) and f.entry == entry
    ]
    if len(found) != 1:
        raise _refuse(
            RefusalKind.INVALID_SELECTION,
            f"{template} prints no single attack entry {entry!r}",
        )
    fact = found[0]
    if fact.section is EntrySection.LEGENDARY_ACTION:
        raise _refuse(
            RefusalKind.UNSUPPORTED_CAPABILITY,
            "legendary actions are not executable here",
        )
    unexecuted = [
        name
        for name, value in (
            ("a formula attack bonus", fact.attack_bonus_formula),
            ("an automatic hit", fact.automatic_hit),
            ("conditional Advantage", fact.advantage_when),
            ("damage by size", fact.hit_damage_by_size),
            ("a size input", fact.size_input),
        )
        if value is not None
    ]
    if unexecuted or fact.attack_bonus is None:
        raise _refuse(
            RefusalKind.UNSUPPORTED_CAPABILITY,
            f"{template}/{entry} prints {unexecuted[0] if unexecuted else 'no bonus'}, "
            "which is not executable here",
        )
    for term in fact.hit_damage:
        if term.dice is None and term.constant is None:
            raise _refuse(RefusalKind.MISSING_AUTHORITY, f"{entry}: untyped damage")
        if term.addends or term.damage_type is None:
            raise _refuse(
                RefusalKind.UNSUPPORTED_CAPABILITY,
                f"{template}/{entry}: damage by choice or formula is not executable "
                "here",
            )
    return fact


def _standing_traits(
    attacker: TurnCreature,
    target: TurnSubject,
    sel: CreatureAttackSelection,
    out: _Modifiers,
) -> None:
    """Standing traits that change this attack roll: the attacker's own
    (subject ``self``), settled by the GameMaster's facts, or refused."""
    assert attacker.index is not None
    template = template_of(attacker)
    for fact in facts_of(attacker.index, template):
        if not isinstance(fact, CreatureRollModifierFact):
            continue
        rolls = [
            e
            for e in fact.effects
            if e.roll.context in (RollContext.ATTACK_ROLL, RollContext.D20_TEST)
        ]
        if not rolls:
            continue
        where = f"{template}/{fact.entry}"
        if fact.subject is not EntrySubject.SELF or any(
            e.roll.actor is not RollActor.SUBJECT for e in rolls
        ):
            raise _refuse(
                RefusalKind.UNSUPPORTED_CAPABILITY,
                f"{where} changes other creatures' rolls and is not executable here",
            )
        when = fact.applies_when
        if when is None:
            applies = True
        elif (
            when.ally_within_ft_of_target == 5
            and when.ally_not is ConditionKind.INCAPACITATED
            and all(
                getattr(when, name) is None
                for name in (
                    "stated",
                    "subject_not",
                    "subject_bloodied",
                    "target_missing_hit_points",
                    "attack",
                )
            )
        ):
            if sel.ally_within_5_feet_of_target is None:
                raise _refuse(
                    RefusalKind.MISSING_STATE,
                    f"{where} turns on whether an ally of the attacker that isn't "
                    "Incapacitated is within 5 feet of the target",
                )
            applies = sel.ally_within_5_feet_of_target
        else:
            raise _refuse(
                RefusalKind.UNSUPPORTED_CAPABILITY,
                f"{where}'s circumstance is not executable here",
            )
        if applies:
            for e in rolls:
                if not isinstance(e, AdvantageFact):
                    continue
                (
                    out.advantage
                    if e.state is AdvantageState.ADVANTAGE
                    else out.disadvantage
                ).append(where)
    del target


def _rider_turn(duration: TurnBoundary | None) -> str | None:
    if duration is None:
        return None
    if duration.turn_of not in (TurnOwner.SOURCE, TurnOwner.TARGET):
        raise _refuse(
            RefusalKind.UNSUPPORTED_CAPABILITY,
            f"a duration bounded by the {duration.turn_of.value}'s turn is not "
            "executable here",
        )
    if duration.turn is not TurnWhich.NEXT or duration.until not in (
        RecurrenceBoundary.START_OF_TURN,
        RecurrenceBoundary.END_OF_TURN,
    ):
        raise _refuse(
            RefusalKind.UNSUPPORTED_CAPABILITY,
            "a rider lasting other than to an edge of a next turn is not executable",
        )
    return "start" if duration.until is RecurrenceBoundary.START_OF_TURN else "end"


def _check_rider(
    rider: Rider | None, attacker: TurnCreature, target: TurnSubject, entry: str
) -> PreparedSave | None:
    """Validate the hit effect before any die; prepare its save, if any."""
    if rider is None:
        return None
    unexecuted = [
        name
        for name, value in (
            ("a speed change", rider.speed),
            ("conditional damage", rider.conditional_damage),
            ("forced movement", rider.forced_movement),
            ("a linked condition", rider.linked),
        )
        if value is not None
    ]
    if unexecuted:
        raise _refuse(
            RefusalKind.UNSUPPORTED_CAPABILITY,
            f"{entry}'s hit effect includes {unexecuted[0]}, not executable here",
        )
    if rider.applies_to not in (None, RiderSubject.TARGET):
        raise _refuse(
            RefusalKind.UNSUPPORTED_CAPABILITY,
            f"{entry}'s hit effect is not on the target",
        )
    if rider.maximum_size is not None and _size(target) is None:
        raise _refuse(
            RefusalKind.MISSING_STATE,
            f"{entry}'s hit effect turns on the target's size",
        )
    _rider_turn(rider.duration)
    if rider.condition is not None and (
        rider.condition.effect is not ConditionEffectKind.APPLIES
    ):
        raise _refuse(
            RefusalKind.UNSUPPORTED_CAPABILITY,
            f"{entry}'s hit effect is not executable",
        )
    if rider.rider_save is None:
        return None
    save = rider.rider_save
    if save.target_excludes:
        raise _refuse(
            RefusalKind.UNSUPPORTED_CAPABILITY,
            f"{entry}'s save excludes creature types, which is not executable here",
        )
    _rider_turn(save.duration)
    template = attacker.stored.state.template_record_key
    return prepare_save(
        target,
        save.save,
        save.dc,
        f"{template}/{entry}",
        frozenset({save.on_failure.condition}),
    )


def _agreeing(attacker: TurnSubject, target: TurnSubject) -> None:
    assert attacker.index is not None and target.index is not None
    if attacker.index.binding == target.index.binding:
        return
    mine = governing_fingerprint(attacker.index, Operation.CREATURE_ATTACK)
    theirs = governing_fingerprint(target.index, Operation.CREATURE_ATTACK)
    if mine != theirs:
        raise _refuse(
            RefusalKind.INCOMPATIBLE_CERTIFICATION,
            "the attacker's and target's bindings disagree on the attack procedure",
        )


def _subject(
    subjects: dict[tuple[str, str], TurnSubject], actor: TurnCharacter, ref: object
) -> TurnSubject | None:
    key = (ref.kind, str(ref.subject_id))  # type: ignore[attr-defined]
    if key == ("character", str(actor.subject_id)):
        return actor
    return subjects.get(key)


def prepare(
    proposal: RollProposal,
    actor: TurnCharacter,
    subjects: dict[tuple[str, str], TurnSubject],
) -> PreparedCreatureAttack:
    """Validate a ``creature_attack`` and derive every input, or refuse."""
    sel = proposal.creature_attack
    if sel is None:
        raise _refuse(
            RefusalKind.INVALID_SELECTION,
            "a creature attack names no attacker or entry",
        )
    attacker = _subject(subjects, actor, sel.attacker)
    target = _subject(subjects, actor, sel.target)
    if not isinstance(attacker, TurnCreature) or attacker.index is None:
        raise _refuse(
            RefusalKind.MISSING_STATE, "the attacker was not read for this turn"
        )
    if target is None or target.index is None:
        raise _refuse(
            RefusalKind.MISSING_STATE, "the target was not read for this turn"
        )
    if subject_key(attacker) == subject_key(target):
        raise _refuse(RefusalKind.INVALID_SELECTION, "a creature cannot attack itself")
    certificate = certify(Operation.CREATURE_ATTACK, attacker.index)
    certify(Operation.CREATURE_ATTACK, target.index)
    _agreeing(attacker, target)
    if (
        attacker.stored.state.death_state is not None
        and attacker.stored.state.death_state.dead
    ):
        raise _refuse(RefusalKind.INVALID_SELECTION, "a dead creature cannot attack")
    unexecuted = other_effects(attacker)
    if unexecuted:
        raise _refuse(
            RefusalKind.UNSUPPORTED_CAPABILITY,
            f"active effect {unexecuted[0].source.record_key} can change this attack "
            "and is not executable here",
        )
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
    fact = _attack_fact(attacker, sel.entry)
    index = attacker.index

    # Range: melee within reach, or a ranged band.
    melee = sel.range == "within_reach"
    if fact.kind is CreatureAttackRange.MELEE and not melee:
        raise _refuse(RefusalKind.INVALID_SELECTION, f"{fact.entry} is a melee attack")
    if fact.kind is CreatureAttackRange.RANGED and melee:
        raise _refuse(
            RefusalKind.INVALID_SELECTION, f"{fact.entry} is made at a range band"
        )
    within_5_feet = sel.target_within_5_feet
    mods = _Modifiers()
    if melee:
        if fact.reach_ft is None:
            raise _refuse(
                RefusalKind.MISSING_AUTHORITY, f"{fact.entry} prints no reach"
            )
        if fact.reach_ft == 5:
            if within_5_feet is False:
                raise _refuse(
                    RefusalKind.INVALID_SELECTION,
                    "a 5-foot reach attack is made from within 5 feet",
                )
            within_5_feet = True
    else:
        if fact.normal_range_ft is None:
            raise _refuse(
                RefusalKind.MISSING_AUTHORITY, f"{fact.entry} prints no range"
            )
        if sel.range == "beyond_long_range" or (
            sel.range == "beyond_normal_within_long_range"
            and fact.long_range_ft is None
        ):
            raise _refuse(RefusalKind.INVALID_SELECTION, "the target is out of range")
        if sel.range == "beyond_normal_within_long_range":
            if not any(
                isinstance(f, AdvantageFact)
                for f in facts_of(index, "play.combat", "long_range")
            ):
                raise _refuse(RefusalKind.MISSING_AUTHORITY, "no typed long-range rule")
            mods.disadvantage.append("play.combat/long_range")
        if sel.hostile_within_5_feet is None:
            raise _refuse(
                RefusalKind.MISSING_STATE,
                "a ranged attack needs whether a hostile creature is within 5 feet",
            )
        if sel.hostile_within_5_feet:
            mods.disadvantage.append("play.combat/close_combat")

    _conditions(attacker, RollActor.SUBJECT, target, within_5_feet, mods)
    _conditions(target, RollActor.AGAINST_SUBJECT, attacker, within_5_feet, mods)
    _standing_traits(attacker, target, sel, mods)

    ac = armor_class(target)
    ac_breakdown = dict(ac.breakdown)
    if sel.cover != "none":
        from afterworlds.ingestion.mechanical.representation import (
            CoverDefensiveBonusFact,
        )

        bonuses = [
            f
            for f in facts_of(index, "play.combat", "cover_degrees")
            if isinstance(f, CoverDefensiveBonusFact) and f.degree.value == sel.cover
        ]
        if len(bonuses) != 1:
            raise _refuse(RefusalKind.MISSING_AUTHORITY, f"no typed {sel.cover} cover")
        ac_breakdown["cover"] = bonuses[0].bonus
    for term in fact.hit_damage:
        assert term.damage_type is not None
        preflight(target, term.damage_type)
    rider_save = _check_rider(fact.hit_effect, attacker, target, fact.entry)
    assert fact.attack_bonus is not None
    return PreparedCreatureAttack(
        selection=sel,
        attacker=attacker,
        target=target,
        fact=fact,
        attack_bonus=fact.attack_bonus,
        target_ac=sum(ac_breakdown.values()),
        advantage_sources=tuple(mods.advantage),
        disadvantage_sources=tuple(mods.disadvantage),
        automatic_critical=tuple(mods.automatic_critical),
        certificate=certificate,
        templates=template_digests(attacker, target),
        rider_save=rider_save,
        ac_breakdown=ac_breakdown,
        usage=creature_effects.usable(attacker, fact.entry),
    )


def _condition_value(
    attacker: TurnCreature,
    target: TurnSubject,
    condition: ConditionKind,
    duration: TurnBoundary | None,
    coordination: TurnCoordination | None,
    escape_dc: int | None = None,
) -> dict[str, object]:
    """An applied condition's typed value: sourced to the creature's
    template, about the creature, with Grappled's escape DC and any
    turn-bounded end (contract G2)."""
    boundary = _rider_turn(duration)
    value: dict[str, object] = {
        "instance_id": str(uuid4()),
        "condition": condition.value,
        "visibility": ConditionVisibility.VISIBLE.value,
        "source": {
            "record_key": attacker.stored.state.template_record_key,
            "component_key": None,
        },
        "referent": reference(attacker).model_dump(mode="json"),
    }
    if condition is ConditionKind.GRAPPLED:
        value["escape_dc"] = escape_dc
    if boundary is not None and duration is not None:
        of = attacker if duration.turn_of is TurnOwner.SOURCE else target
        ref = reference(of)
        active = coordination.active if coordination is not None else None
        value["ends"] = {
            "kind": "special",
            "turn": {
                "boundary": boundary,
                "of": ref.model_dump(mode="json"),
                "created_in_turn": (
                    active.instance
                    if active is not None and active.subject == ref
                    else None
                ),
            },
        }
    return value


def _condition_effect(
    prepared: PreparedCreatureAttack,
    condition: ConditionKind,
    duration: TurnBoundary | None,
    coordination: TurnCoordination | None,
) -> SheetEffect:
    target = prepared.target
    rider = prepared.fact.hit_effect
    value = _condition_value(
        prepared.attacker,
        target,
        condition,
        duration,
        coordination,
        rider.escape_dc if rider is not None else None,
    )
    return SheetEffect(
        target=condition.value,
        operation="apply_condition",
        value_json=json.dumps(value),
        subject_kind=subject_key(target)[0],  # type: ignore[arg-type]
        subject_id=target.subject_id,
    )


def _rider(
    prepared: PreparedCreatureAttack,
    target: TurnSubject,
    dice: DiceService,
    coordination: TurnCoordination | None,
) -> tuple[list[SheetEffect], dict[str, object] | None]:
    rider = prepared.fact.hit_effect
    if rider is None:
        return [], None
    state = target.stored.state
    if state.death_state is not None and state.death_state.dead:
        return [], {"result": "target_died"}
    if rider.maximum_size is not None:
        size = _size(target)
        if size not in _SIZES_UP_TO(rider.maximum_size):
            return [], {"result": "too_large"}
    effects: list[SheetEffect] = []
    out: dict[str, object] = {}
    if rider.condition is not None:
        kind = rider.condition.condition
        if condition_immune(target, kind):
            out["condition"] = "immune"
        else:
            effects.append(
                _condition_effect(prepared, kind, rider.duration, coordination)
            )
            out["condition"] = kind.value
    if rider.rider_save is not None and prepared.rider_save is not None:
        saved: RolledSave = roll_save(prepared.rider_save, dice)
        out["save"] = saved.provenance()
        kind = rider.rider_save.on_failure.condition
        if not saved.succeeded and not condition_immune(target, kind):
            effects.append(
                _condition_effect(
                    prepared, kind, rider.rider_save.duration, coordination
                )
            )
            out["on_failure"] = kind.value
    return effects, {"result": "applied", **out}


def roll(
    prepared: PreparedCreatureAttack,
    dice: DiceService,
    coordination: TurnCoordination | None = None,
) -> RolledCreatureAttack:
    """Roll the attack; on a hit, its damage terms in order, then its hit
    effect on the target as the damage left it."""
    index = prepared.attacker.index
    assert index is not None
    attack = dice.roll(prepared.expression)
    natural = {
        f.face: f
        for f in facts_of(index, "play.d20_tests")
        if isinstance(f, NaturalRollOutcomeFact)
        and f.context is RollContext.ATTACK_ROLL
    }
    face = natural.get(attack.chosen)
    total = attack.chosen + prepared.attack_bonus
    if face is not None:
        hit = face.outcome.value == "hit"
        critical = hit and face.critical_hit
    else:
        hit, critical = total >= prepared.target_ac, False
    if hit and prepared.automatic_critical:
        critical = True
    spent = creature_effects.spend(
        prepared.attacker, prepared.fact.entry, prepared.usage
    )
    if not hit:
        # A used limited entry is spent whether or not it hits.
        return RolledCreatureAttack(
            prepared, attack.raw_rolls, attack.chosen, False, False, rider_effects=spent
        )
    from afterworlds.ingestion.mechanical.representation import CriticalDamageFact

    multiplier = next(
        (
            f.damage_dice_multiplier
            for f in facts_of(index, "play.damage_and_healing", "critical_hits")
            if isinstance(f, CriticalDamageFact)
        ),
        None,
    )
    if multiplier is None:
        raise _refuse(RefusalKind.MISSING_AUTHORITY, "no typed critical damage rule")
    target = prepared.target
    rolls: list[int] = []
    parts: list[tuple[int, DamageType]] = []
    for term in prepared.fact.hit_damage:
        amount = term.constant or 0
        if term.dice is not None:
            count = term.dice.count * (multiplier if critical else 1)
            drawn = dice.roll(f"{count}{term.dice.die.value}")
            rolls.extend(drawn.raw_rolls)
            amount += drawn.chosen + term.dice.modifier
        assert term.damage_type is not None
        parts.append((max(0, amount), term.damage_type))
    # One hit, one damage: every term together (responses per type).
    (first, first_type), *rest = parts
    result = take_damage(target, first, first_type, critical=critical, more=tuple(rest))
    taken = [result]
    # The hit effect sees what the damage left.
    target = with_effects(target, list(result.effects))
    effects, rider = _rider(prepared, target, dice, coordination)
    return RolledCreatureAttack(
        prepared,
        attack.raw_rolls,
        attack.chosen,
        True,
        critical,
        tuple(rolls),
        tuple(taken),
        (*spent, *effects),
        rider,
    )


def possible_conditions(
    proposal: RollProposal,
    actor: TurnCharacter,
    subjects: dict[tuple[str, str], TurnSubject],
) -> dict[tuple[str, str], frozenset[ConditionKind]]:
    """Every condition this attack could apply to its target, whatever the
    dice: falling Unconscious, and its hit effect's conditions."""
    from afterworlds.pipeline.rpg.damage import possible_conditions as damage_kinds

    sel = proposal.creature_attack
    if sel is None:
        return {}
    key = (sel.target.kind, str(sel.target.subject_id))
    # The target may be the acting character, which is not among *subjects*.
    target = _subject(subjects, actor, sel.target)
    attacker = _subject(subjects, actor, sel.attacker)
    if target is None or not isinstance(attacker, TurnCreature):
        return {}
    kinds = set(damage_kinds(target))
    try:
        rider = _attack_fact(attacker, sel.entry).hit_effect
    except AdjudicationRefusal:
        return {key: frozenset(kinds)}
    if rider is not None and rider.condition is not None:
        kinds.add(rider.condition.condition)
    if rider is not None and rider.rider_save is not None:
        kinds.add(rider.rider_save.on_failure.condition)
    return {key: frozenset(kinds)}


def multiattack_key(attacker: TurnCreature) -> str:
    """The once-per-turn use a Multiattack takes."""
    return f"{attacker.stored.state.template_record_key}/Multiattack"


def check_multiattack(attacker: TurnCreature, entries: list[str]) -> None:
    """Refuse unless *entries* (one Multiattack's attacks, in order) are one
    printed alternative of the attacker's Multiattack: every required part's
    count, optional parts up to theirs, and nothing else. Alternatives with a
    condition, a count formula, a spell use or an "if available" part, and
    replacements, are not executable here."""
    assert attacker.index is not None
    template = template_of(attacker)
    facts = [
        f
        for f in facts_of(attacker.index, template)
        if isinstance(f, CreatureMultiattackFact)
    ]
    if len(facts) != 1:
        raise _refuse(
            RefusalKind.INVALID_SELECTION, f"{template} prints no single Multiattack"
        )
    for alternative in facts[0].alternatives:
        if alternative.condition is not None or any(
            p.count_formula is not None or p.uses_one_of or p.if_available
            for p in alternative.parts
        ):
            continue
        remaining = Counter(entries)
        fits = True
        ordered = sorted(alternative.parts, key=lambda p: p.attack is None)
        for part in ordered:
            names = {part.attack} if part.attack else set(part.any_of)
            want = part.count or 0
            took = 0
            for name in sorted(names):
                step = min(want - took, remaining[name])
                remaining[name] -= step
                took += step
            if took < want and not part.optional:
                fits = False
        if fits and not +remaining:
            return
    raise _refuse(
        RefusalKind.INVALID_SELECTION,
        f"{entries} is not an executable alternative of {template}'s Multiattack",
    )
