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
from itertools import product
from uuid import uuid4

from afterworlds.ingestion.mechanical.representation import (
    AdvantageFact,
    ConditionEffectKind,
    ConditionKind,
    CreatureAttackFact,
    CreatureAttackRange,
    CreatureEntryUsageFact,
    CreatureMultiattackFact,
    DamageMode,
    DamageTerm,
    DamageType,
    EntrySection,
    MultiattackAlternative,
    MultiattackReplacement,
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
from afterworlds.pipeline.rpg import (
    bystanders,
    creature_clauses,
    creature_effects,
    roster,
)
from afterworlds.pipeline.rpg.attacks import (
    _SIGHT_LIGHT,
    _SIZES_UP_TO,
    _conditions,
    _Modifiers,
    _size,
    creature_traits,
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
from afterworlds.pipeline.rpg.damage import (
    DamageTaken,
    fixed_part,
    preflight,
    take_damage,
)
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
    clauses: creature_clauses.HitClauses = creature_clauses.HitClauses()
    #: Whether the clauses' predicate holds (size, charge), known pre-dice.
    predicate_holds: bool = False

    @property
    def advantaged(self) -> bool:
        return self.expression == "2d20kh1"

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
    clauses: dict[str, object] | None = None

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
                "clauses": self.clauses,
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
    roster.require(template, entry)
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
    creature_clauses.plan(attacker, fact)  # every clause executed, or refused
    for term in fact.hit_damage:
        if fixed_part(term) is None:
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
    actor: TurnCharacter,
    subjects: dict[tuple[str, str], TurnSubject],
    melee: bool,
) -> None:
    """Standing traits that change this attack roll: the attacker's own, and
    a creature target's on attacks against it (:func:`.attacks.creature_traits`);
    Pack Tactics' allies are the GameMaster's named, read subjects."""

    def allies() -> bool:
        return bool(
            bystanders.allies(
                sel.allies_within_5_feet_of_target, attacker, target, actor, subjects
            )
        )

    creature_traits(attacker, target, melee, out, attacking=True, allies=allies)
    creature_traits(target, attacker, melee, out, attacking=False)


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


def _check_conditional_damage(rider: Rider, entry: str, terms: int) -> None:
    """Admit damage stated under the attack roll having had Advantage (code
    knows the roll mode). Bloodied has no typed threshold in the accepted
    authority (``glossary.bloodied`` is prose-bound): it refuses."""
    extra = rider.conditional_damage
    if extra is None:
        return
    when = extra.when
    if when.source_bloodied or when.target_bloodied:
        raise _refuse(
            RefusalKind.MISSING_AUTHORITY,
            f"{entry}'s damage turns on Bloodied, which has no typed threshold "
            "(glossary.bloodied is prose-bound)",
        )
    others = (
        when.target_grappled_by_source,
        when.source_moved_straight_toward_target_ft_min,
        when.target_maximum_size,
    )
    instead = extra.mode is DamageMode.INSTEAD
    if (
        not when.attack_roll_had_advantage
        or any(v is not None for v in others)
        or extra.term.damage_type is None
        or extra.term.addends
        or fixed_part(extra.term) is None
        or (
            instead
            and (
                extra.replaces_hit_damage_index is None
                or extra.replaces_hit_damage_index >= terms
            )
        )
        or (not instead and extra.mode is not DamageMode.ADDITIONAL)
    ):
        raise _refuse(
            RefusalKind.UNSUPPORTED_CAPABILITY,
            f"{entry}'s hit effect includes conditional damage, not executable here",
        )


def _check_rider(
    rider: Rider | None,
    attacker: TurnCreature,
    target: TurnSubject,
    entry: str,
    hit_damage: tuple[DamageTerm, ...] = (),
) -> PreparedSave | None:
    """Validate the hit effect before any die; prepare its save, if any."""
    if rider is None:
        return None
    unexecuted = [
        name
        for name, value in (
            ("a speed change", rider.speed),
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
    _check_conditional_damage(rider, entry, len(hit_damage))
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
        close = bystanders.enemies(
            sel.hostiles_within_5_feet, attacker, actor, subjects
        )
        if close:
            mods.disadvantage.append("play.combat/close_combat")

    _conditions(attacker, RollActor.SUBJECT, target, within_5_feet, mods)
    _conditions(target, RollActor.AGAINST_SUBJECT, attacker, within_5_feet, mods)
    _standing_traits(attacker, target, sel, mods, actor, subjects, melee)

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
    hit_clauses = creature_clauses.plan(attacker, fact)
    holds = _predicate(sel, hit_clauses, target, f"{template_of(attacker)}/{sel.entry}")
    terms = [*fact.hit_damage]
    if hit_clauses.advantage_damage is not None:
        terms.append(hit_clauses.advantage_damage[1])
    for term in terms:
        assert term.damage_type is not None
        preflight(target, term.damage_type)
    rider_save = _check_rider(
        fact.hit_effect, attacker, target, fact.entry, fact.hit_damage
    )
    if fact.hit_effect is not None and fact.hit_effect.conditional_damage:
        damage_type = fact.hit_effect.conditional_damage.term.damage_type
        assert damage_type is not None
        preflight(target, damage_type)
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
        clauses=hit_clauses,
        predicate_holds=holds,
    )


def _predicate(
    sel: CreatureAttackSelection,
    hit_clauses: creature_clauses.HitClauses,
    target: TurnSubject,
    where: str,
) -> bool:
    """Whether the clauses' leading predicate holds: the target's size in
    its own binding, and the GameMaster's charge selection."""
    charged = creature_clauses.charged(sel, hit_clauses, where)
    if not hit_clauses.predicated:
        return False
    if hit_clauses.maximum_size is not None:
        size = _size(target)
        if size is None:
            raise _refuse(RefusalKind.MISSING_AUTHORITY, "the target has no size")
        if size not in _SIZES_UP_TO(hit_clauses.maximum_size):
            return False
    return charged


def check_follow_up(
    proposals: list[RollProposal],
    index: int,
    actor: TurnCharacter,
    subjects: dict[tuple[str, str], TurnSubject],
) -> None:
    """Refuse, before any die, a follow-up attack that does not directly
    follow an attack by the same creature against the same target whose
    entry allows it, with that entry's predicate holding."""
    sel = proposals[index].creature_attack
    before = proposals[index - 1].creature_attack if index else None
    allowed = None
    if sel is not None and before is not None and not before.follows_up:
        attacker = _subject(subjects, actor, before.attacker)
        target = _subject(subjects, actor, before.target)
        if isinstance(attacker, TurnCreature) and target is not None:
            plan = creature_clauses.plan(attacker, _attack_fact(attacker, before.entry))
            if _predicate(before, plan, target, before.entry):
                allowed = plan.follow_up
    if (
        sel is None
        or before is None
        or sel.multiattack
        or before.attacker != sel.attacker
        or before.target != sel.target
        or allowed != sel.entry
    ):
        raise _refuse(
            RefusalKind.INVALID_SELECTION,
            "a follow-up attack directly follows an attack by the same creature "
            "against the same target whose printed hit allows it",
        )


def follow_up_of(prepared: PreparedCreatureAttack) -> str | None:
    """The follow-up attack this attack's hit allows, if its predicate
    holds."""
    if prepared.predicate_holds:
        return prepared.clauses.follow_up
    return None


def _clause_effects(
    prepared: PreparedCreatureAttack,
    target: TurnSubject,
    taken: DamageTaken,
    coordination: TurnCoordination | None,
) -> tuple[list[SheetEffect], dict[str, object] | None]:
    """The executed clauses on a hit, on the target as the damage left it."""
    plan = prepared.clauses
    if plan == creature_clauses.HitClauses():
        return [], None
    out: dict[str, object] = {"no_effect": list(plan.no_effect)}
    if plan.advantage_damage is not None:
        out["advantage_damage"] = prepared.advantaged
    if plan.dies_at_zero:
        out["dies_at_zero"] = taken.outcome == "died_by_attack"
    if not plan.predicated:
        return [], out
    out["predicate"] = prepared.predicate_holds
    if plan.follow_up is not None:
        out["follow_up"] = "may_follow_up" if prepared.predicate_holds else None
    effects: list[SheetEffect] = []
    if plan.prone and prepared.predicate_holds:
        death = target.stored.state.death_state
        if death is not None and death.dead:
            out["prone"] = "target_died"
        elif condition_immune(target, ConditionKind.PRONE):
            out["prone"] = "immune"
        else:
            effects.append(
                _condition_effect(prepared, ConditionKind.PRONE, None, coordination)
            )
            out["prone"] = "applied"
    return effects, out


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
    if rider.conditional_damage is not None:
        out["conditional_damage"] = prepared.advantaged
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
        missed = prepared.clauses.no_effect
        return RolledCreatureAttack(
            prepared,
            attack.raw_rolls,
            attack.chosen,
            False,
            False,
            rider_effects=spent,
            clauses={"no_effect": list(missed)} if missed else None,
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
    terms = list(prepared.fact.hit_damage)
    replaced = prepared.clauses.advantage_damage
    if replaced is not None and prepared.advantaged:
        terms[replaced[0]] = replaced[1]
    effect = prepared.fact.hit_effect
    rider_damage = effect.conditional_damage if effect is not None else None
    if rider_damage is not None and prepared.advantaged:
        # Admitted only under "the attack roll had Advantage" (_check_rider).
        if rider_damage.mode is DamageMode.INSTEAD:
            assert rider_damage.replaces_hit_damage_index is not None
            terms[rider_damage.replaces_hit_damage_index] = rider_damage.term
        else:
            terms.append(rider_damage.term)
    for term in terms:
        amount = fixed_part(term) or 0
        if term.dice is not None:
            count = term.dice.count * (multiplier if critical else 1)
            drawn = dice.roll(f"{count}{term.dice.die.value}")
            rolls.extend(drawn.raw_rolls)
            amount += drawn.chosen + term.dice.modifier
        assert term.damage_type is not None
        parts.append((max(0, amount), term.damage_type))
    # One hit, one damage: every term together (responses per type).
    (first, first_type), *rest = parts
    result = take_damage(
        target,
        first,
        first_type,
        critical=critical,
        more=tuple(rest),
        dies_at_zero=prepared.clauses.dies_at_zero,
    )
    taken = [result]
    # The hit effect sees what the damage left.
    target = with_effects(target, list(result.effects))
    effects, rider = _rider(prepared, target, dice, coordination)
    more, clauses = _clause_effects(prepared, target, result, coordination)
    effects += more
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
        clauses,
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
        fact = _attack_fact(attacker, sel.entry)
        plan = creature_clauses.plan(attacker, fact)
        if plan.prone and _predicate(sel, plan, target, sel.entry):
            kinds.add(ConditionKind.PRONE)
    except AdjudicationRefusal:
        return {key: frozenset(kinds)}
    rider = fact.hit_effect
    if rider is not None and rider.condition is not None:
        kinds.add(rider.condition.condition)
    if rider is not None and rider.rider_save is not None:
        kinds.add(rider.rider_save.on_failure.condition)
    return {key: frozenset(kinds)}


def multiattack_key(attacker: TurnCreature) -> str:
    """The once-per-turn use a Multiattack takes."""
    return f"{attacker.stored.state.template_record_key}/Multiattack"


def _fits(
    alternative: MultiattackAlternative,
    entries: Counter[str],
    cuts: tuple[int, ...] = (),
) -> bool:
    """Whether *entries* make *alternative* exactly, with ``cuts[i]`` of
    part *i*'s required attacks replaced (not made)."""
    remaining = Counter(entries)
    order = sorted(
        range(len(alternative.parts)), key=lambda i: alternative.parts[i].attack is None
    )
    for i in order:
        part = alternative.parts[i]
        names = {part.attack} if part.attack else set(part.any_of)
        want = (part.count or 0) - (cuts[i] if cuts else 0)
        took = 0
        for name in sorted(names):
            step = min(want - took, remaining[name])
            remaining[name] -= step
            took += step
        if took < want and not part.optional:
            return False
    return not +remaining


def _replaced(
    alternative: MultiattackAlternative,
    replacement: MultiattackReplacement,
    entries: Counter[str],
    attack_entries: set[str],
) -> bool:
    """Whether *entries* make *alternative* with *replacement* used: each
    use of an attack option stands in for ``replaces`` (one if unprinted) of
    the alternative's required attacks (only ``replaces_attack``'s if
    printed); once, or any number of times for "any of these attacks". A
    spell or a non-attack option is not executable here."""
    options = {
        o.entry
        for o in replacement.with_one_of
        if o.spell is None and o.entry in attack_entries
    }
    used = sum(entries[o] for o in options)
    if not used or (used > 1 and not replacement.replaces_any):
        return False
    base = Counter({k: v for k, v in entries.items() if k not in options})
    need = used * (replacement.replaces or 1)
    eligible = [
        (
            0
            if part.optional
            or (
                replacement.replaces_attack is not None
                and replacement.replaces_attack != part.attack
            )
            else part.count or 0
        )
        for part in alternative.parts
    ]
    return any(
        sum(cuts) == need and _fits(alternative, base, cuts)
        for cuts in product(*(range(n + 1) for n in eligible))
    )


def check_multiattack(attacker: TurnCreature, entries: list[str]) -> None:
    """Refuse unless *entries* (one Multiattack's attacks, in order) are one
    printed alternative of the attacker's Multiattack: every required part's
    count, optional parts up to theirs, and nothing else, or that with a
    printed replacement by another attack entry. Alternatives with a
    condition, a count formula, a required use of another entry or an "if
    available" part, optional uses of another entry, and replacements by a
    spell or a non-attack entry, are not executable here."""
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
    attack_entries = {
        f.entry
        for f in facts_of(attacker.index, template)
        if isinstance(f, CreatureAttackFact)
    }
    made = Counter(entries)
    for alternative in facts[0].alternatives:
        # An optional use of another entry (a spell, Entangling Rope) is not
        # executed here: the alternative is made without it.
        if alternative.condition is not None or any(
            p.count_formula is not None
            or p.if_available
            or (p.uses_one_of and not p.optional)
            for p in alternative.parts
        ):
            continue
        if _fits(alternative, made) or any(
            _replaced(alternative, r, made, attack_entries)
            for r in facts[0].replacements
        ):
            return
    raise _refuse(
        RefusalKind.INVALID_SELECTION,
        f"{entries} is not an executable alternative of {template}'s Multiattack",
    )
