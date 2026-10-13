"""The zero-HP lifecycle's death save — CRD Issue 15c.

A subject at the typed hit points (``DeathSavingThrowFact.timing``) that is
dying — treated as a character, not Stable, not dead — makes a death save
when its turn begins (``begin_turn``, contract G1). Every number and result is
typed authority:

* the die and the success minimum (``death_saving_throws``); Advantage or
  Disadvantage from typed condition facts on saves that name no ability;
* a natural 1 counts two failures, a natural 20 regains 1 Hit Point
  (``death_save_natural_roll``); regaining Hit Points resets the counters,
  ends the Unconscious that falling to 0 applied (``falling_unconscious``
  lasts *until* the subject regains Hit Points) and leaves it Prone
  (``glossary.unconscious/remains_prone``);
* three successes: Stable, counters reset, and code rolls the recovery
  interval (``StableStateFact.recovery``, OD-15c-2); three failures: dead.

Anything that could change the save and is not executed refuses
(:func:`.saves.refuse_contributors`, plus Survivor's Defy Death).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from uuid import uuid4

from afterworlds.ingestion.mechanical.representation import (
    ConditionEffectFact,
    ConditionEffectKind,
    ConditionKind,
    DeathSaveNaturalRollFact,
    DeathSavingThrowFact,
    LifecycleEvent,
    StableStateFact,
    ZeroHitPointOutcomeFact,
)
from afterworlds.models.dnd5e_state import DeathState, StableRecovery
from afterworlds.models.enums import ConditionVisibility
from afterworlds.models.rpg import SheetEffect
from afterworlds.pipeline.rpg.capability import (
    AdjudicationRefusal,
    Certificate,
    Operation,
    RefusalKind,
    certify,
)
from afterworlds.pipeline.rpg.defense import facts_of
from afterworlds.pipeline.rpg.dice import DiceService
from afterworlds.pipeline.rpg.saves import condition_modifiers, refuse_contributors
from afterworlds.services.dnd5e_state.turn import TurnCreature, TurnSubject

__all__ = [
    "DEATH_SAVE_CONTRIBUTORS",
    "PreparedDeathSave",
    "RolledDeathSave",
    "dying",
    "prepare",
    "roll",
]

_RULES = "play.damage_and_healing"
#: Features that change their holder's death saves (``classes.md``
#: Survivor's Defy Death: Advantage, and 18-20 counts as a 20).
DEATH_SAVE_CONTRIBUTORS: frozenset[str] = frozenset(
    {"classes.fighter.champion.survivor"}
)


def _refuse(kind: RefusalKind, detail: str) -> AdjudicationRefusal:
    return AdjudicationRefusal(kind, detail)


def _one[T](subject: TurnSubject, component: str, family: type[T]) -> T:
    assert subject.index is not None
    found = [
        f for f in facts_of(subject.index, _RULES, component) if isinstance(f, family)
    ]
    if len(found) != 1:
        raise _refuse(
            RefusalKind.MISSING_AUTHORITY,
            f"{_RULES}/{component} states no single {family.__name__}",
        )
    return found[0]


def dying(subject: TurnSubject) -> bool:
    """Whether *subject* makes a death save when its turn begins."""
    state = subject.stored.state
    hp, death = state.hit_points, state.death_state
    if hp is None or death is None or subject.index is None:
        raise _refuse(
            RefusalKind.MISSING_STATE,
            "the subject records no hit points or death state",
        )
    rule = _one(subject, "death_saving_throws", DeathSavingThrowFact)
    if hp.current > rule.timing.at_hit_points or death.dead or death.stable:
        return False
    if isinstance(subject, TurnCreature):
        treatment = state.zero_hit_point_treatment  # type: ignore[union-attr]
        if treatment is None:
            raise _refuse(
                RefusalKind.MISSING_STATE,
                f"creature {subject.subject_id} at 0 Hit Points has no recorded "
                "zero-HP treatment",
            )
        return bool(treatment.as_character)
    return True


@dataclass(frozen=True)
class PreparedDeathSave:
    subject: TurnSubject
    rule: DeathSavingThrowFact
    naturals: dict[int, DeathSaveNaturalRollFact]
    stable: StableStateFact
    advantage_sources: tuple[str, ...]
    disadvantage_sources: tuple[str, ...]
    certificate: Certificate

    @property
    def expression(self) -> str:
        adv, dis = bool(self.advantage_sources), bool(self.disadvantage_sources)
        die = self.rule.die.value
        if adv and not dis:
            return f"2{die}kh1"
        if dis and not adv:
            return f"2{die}kl1"
        return f"1{die}"


@dataclass(frozen=True)
class RolledDeathSave:
    prepared: PreparedDeathSave
    raw_rolls: tuple[int, ...]
    chosen: int
    outcome: str
    effects: tuple[SheetEffect, ...]
    recovery_rolls: tuple[int, ...] = field(default=())

    def provenance_json(self) -> str:
        p = self.prepared
        return json.dumps(
            {
                "operation": Operation.DEATH_SAVING_THROW.value,
                "subject": {
                    "kind": _kind(p.subject),
                    "subject_id": str(p.subject.subject_id),
                },
                "success_minimum": p.rule.success_minimum,
                "result": self.outcome,
                "recovery_rolls": list(self.recovery_rolls),
                "advantage_sources": list(p.advantage_sources),
                "disadvantage_sources": list(p.disadvantage_sources),
                "certificate": p.certificate.as_json(),
            },
            sort_keys=True,
        )


def _kind(subject: TurnSubject) -> str:
    return "creature" if isinstance(subject, TurnCreature) else "character"


def prepare(subject: TurnSubject) -> PreparedDeathSave:
    """Validate the death save *subject* makes now, or refuse (typed)."""
    index = subject.index
    if index is None:
        raise _refuse(
            RefusalKind.MISSING_AUTHORITY, "the subject's authority is not resolved"
        )
    certificate = certify(Operation.DEATH_SAVING_THROW, index)
    rule = _one(subject, "death_saving_throws", DeathSavingThrowFact)
    if rule.ability is not None:
        raise _refuse(
            RefusalKind.UNSUPPORTED_CAPABILITY,
            f"a death save of {rule.ability.value} is not executable here",
        )
    naturals = {
        f.face: f
        for f in facts_of(index, _RULES, "death_saving_throws")
        if isinstance(f, DeathSaveNaturalRollFact)
    }
    if set(naturals) != {1, 20}:
        raise _refuse(RefusalKind.MISSING_AUTHORITY, "natural 1 and 20 are not typed")
    stable = _one(subject, "stable", StableStateFact)
    refuse_contributors(
        subject, index, None, frozenset(), extra=DEATH_SAVE_CONTRIBUTORS
    )
    advantage, disadvantage, failure = condition_modifiers(subject, index, None)
    if failure:
        raise _refuse(
            RefusalKind.UNSUPPORTED_CAPABILITY,
            f"{failure[0]} makes a death save fail automatically, which is not "
            "executable here",
        )
    if subject.stored.state.conditions is None:
        raise _refuse(RefusalKind.MISSING_STATE, "the subject records no conditions")
    return PreparedDeathSave(
        subject=subject,
        rule=rule,
        naturals=naturals,
        stable=stable,
        advantage_sources=tuple(advantage),
        disadvantage_sources=tuple(disadvantage),
        certificate=certificate,
    )


def _effect(subject: TurnSubject, target: str, op: str, value: object) -> SheetEffect:
    return SheetEffect(
        target=target,
        operation=op,  # type: ignore[arg-type]
        value_json=json.dumps(value),
        subject_kind=_kind(subject),  # type: ignore[arg-type]
        subject_id=subject.subject_id,
    )


def _regain(prepared: PreparedDeathSave, amount: int) -> list[SheetEffect]:
    """Regaining Hit Points at 0: counters reset, the falling Unconscious ends,
    and the subject stays Prone."""
    subject = prepared.subject
    state = subject.stored.state
    assert state.hit_points is not None and state.conditions is not None
    if LifecycleEvent.REGAINS_HIT_POINTS not in prepared.rule.reset_on:
        raise _refuse(RefusalKind.MISSING_AUTHORITY, "no typed counter reset")
    falling = [
        f
        for f in facts_of(subject.index, _RULES, "falling_unconscious")  # type: ignore[arg-type]
        if isinstance(f, ZeroHitPointOutcomeFact)
        and f.until is LifecycleEvent.REGAINS_HIT_POINTS
    ]
    remains = [
        f
        for f in facts_of(subject.index, "glossary.unconscious", "remains_prone")  # type: ignore[arg-type]
        if isinstance(f, ConditionEffectFact)
        and f.effect is ConditionEffectKind.APPLIES
        and f.condition is ConditionKind.PRONE
    ]
    if not falling or not remains:
        raise _refuse(
            RefusalKind.MISSING_AUTHORITY,
            "what regaining Hit Points ends, and Prone after Unconscious, are not "
            "typed",
        )
    effects = [
        _effect(subject, "current_hp", "set", state.hit_points.current + amount),
        _effect(
            subject,
            "death_state",
            "set",
            DeathState(successes=0, failures=0, stable=False, dead=False).model_dump(
                mode="json"
            ),
        ),
    ]
    for instance in state.conditions:
        if (
            instance.condition is ConditionKind.UNCONSCIOUS
            and instance.source is not None
            and (instance.source.record_key, instance.source.component_key)
            == (_RULES, "falling_unconscious")
        ):
            effects.append(
                _effect(
                    subject,
                    "unconscious",
                    "clear_condition",
                    {"instance_id": instance.instance_id},
                )
            )
    if not any(c.condition is ConditionKind.PRONE for c in state.conditions):
        effects.append(
            _effect(
                subject,
                "prone",
                "apply_condition",
                {
                    "instance_id": str(uuid4()),
                    "condition": ConditionKind.PRONE.value,
                    "visibility": ConditionVisibility.VISIBLE.value,
                    "source": {
                        "record_key": "glossary.unconscious",
                        "component_key": "remains_prone",
                    },
                },
            )
        )
    return effects


def roll(prepared: PreparedDeathSave, dice: DiceService) -> RolledDeathSave:
    subject = prepared.subject
    death = subject.stored.state.death_state
    assert death is not None
    result = dice.roll(prepared.expression)
    face = result.chosen
    rule = prepared.rule
    natural = prepared.naturals.get(face)
    if natural is not None and natural.regain_hit_points:
        effects = _regain(prepared, natural.regain_hit_points)
        return RolledDeathSave(
            prepared, result.raw_rolls, face, "regained_hit_points", tuple(effects)
        )
    successes, failures = death.successes, death.failures
    if natural is not None and natural.failures:
        failures += natural.failures
    elif face >= rule.success_minimum:
        successes += 1
    else:
        failures += 1
    recovery_rolls: tuple[int, ...] = ()
    if failures >= rule.failures_to_die:
        after = DeathState(successes=successes, failures=3, stable=False, dead=True)
        outcome = "died"
    elif successes >= rule.successes_to_stable:
        if LifecycleEvent.BECOMES_STABLE not in rule.reset_on:
            raise _refuse(RefusalKind.MISSING_AUTHORITY, "no typed counter reset")
        recovery = prepared.stable.recovery
        dice_expr = recovery.dice
        drawn = dice.roll(f"{dice_expr.count}{dice_expr.die.value}")
        recovery_rolls = drawn.raw_rolls
        after = DeathState(
            successes=0,
            failures=0,
            stable=True,
            dead=False,
            stable_recovery=StableRecovery(
                instance_id=str(uuid4()),
                interval=drawn.chosen + dice_expr.modifier,
                unit=recovery.unit,
            ),
        )
        outcome = "stable"
    else:
        after = DeathState(
            successes=successes, failures=failures, stable=False, dead=False
        )
        outcome = "success" if successes > death.successes else "failure"
    final = (_effect(subject, "death_state", "set", after.model_dump(mode="json")),)
    return RolledDeathSave(
        prepared, result.raw_rolls, face, outcome, final, recovery_rolls
    )
