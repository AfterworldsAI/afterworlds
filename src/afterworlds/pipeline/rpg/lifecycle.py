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

from afterworlds.ingestion.mechanical.models import ComponentHandling
from afterworlds.ingestion.mechanical.representation import (
    ActionCost,
    ActionRestrictionFact,
    ConditionEffectFact,
    ConditionEffectKind,
    ConditionKind,
    DeathSaveNaturalRollFact,
    DeathSavingThrowFact,
    KnockoutAlternativeFact,
    LifecycleEvent,
    RestKind,
    StabilizationFact,
    StabilizeOutcome,
    StableStateFact,
    ZeroHitPointOutcomeFact,
)
from afterworlds.models.dnd5e_state import DeathState, StableRecovery
from afterworlds.models.enums import ConditionVisibility
from afterworlds.models.rpg import RollProposal, SheetEffect
from afterworlds.pipeline.rpg import checks
from afterworlds.pipeline.rpg.capability import (
    AdjudicationRefusal,
    Certificate,
    Operation,
    RefusalKind,
    certify,
)
from afterworlds.pipeline.rpg.conditions import effective
from afterworlds.pipeline.rpg.defense import facts_of
from afterworlds.pipeline.rpg.dice import DiceService
from afterworlds.pipeline.rpg.saves import condition_modifiers, refuse_contributors
from afterworlds.services.dnd5e_state.turn import (
    TurnCharacter,
    TurnCreature,
    TurnSubject,
)

__all__ = [
    "DEATH_SAVE_CONTRIBUTORS",
    "PreparedDeathSave",
    "RolledDeathSave",
    "Attested",
    "PreparedFirstAid",
    "RolledFirstAid",
    "attest",
    "dying",
    "prepare",
    "prepare_first_aid",
    "roll",
    "roll_first_aid",
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


def _end_unconscious(
    subject: TurnSubject, instance_ids: list[str]
) -> list[SheetEffect]:
    """End the named Unconscious instances; the subject stays Prone
    (``glossary.unconscious/remains_prone``)."""
    state = subject.stored.state
    assert state.conditions is not None and subject.index is not None
    remains = [
        f
        for f in facts_of(subject.index, "glossary.unconscious", "remains_prone")
        if isinstance(f, ConditionEffectFact)
        and f.effect is ConditionEffectKind.APPLIES
        and f.condition is ConditionKind.PRONE
    ]
    if not remains:
        raise _refuse(
            RefusalKind.MISSING_AUTHORITY, "Prone after Unconscious is not typed"
        )
    effects = [
        _effect(subject, "unconscious", "clear_condition", {"instance_id": i})
        for i in instance_ids
    ]
    if instance_ids and not any(
        c.condition is ConditionKind.PRONE for c in state.conditions
    ):
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


def _sourced(subject: TurnSubject, component: str) -> list[str]:
    """The subject's Unconscious instances that *component* applied."""
    return [
        c.instance_id
        for c in subject.stored.state.conditions or ()
        if c.condition is ConditionKind.UNCONSCIOUS
        and c.source is not None
        and (c.source.record_key, c.source.component_key) == (_RULES, component)
    ]


def _regain(subject: TurnSubject, amount: int) -> list[SheetEffect]:
    """Regaining Hit Points at 0: counters reset (ending any Stable recovery),
    the falling Unconscious ends (it lasts *until* the subject regains Hit
    Points), and the subject stays Prone."""
    state = subject.stored.state
    assert state.hit_points is not None and subject.index is not None
    rule = _one(subject, "death_saving_throws", DeathSavingThrowFact)
    if LifecycleEvent.REGAINS_HIT_POINTS not in rule.reset_on:
        raise _refuse(RefusalKind.MISSING_AUTHORITY, "no typed counter reset")
    if not any(
        isinstance(f, ZeroHitPointOutcomeFact)
        and f.until is LifecycleEvent.REGAINS_HIT_POINTS
        for f in facts_of(subject.index, _RULES, "falling_unconscious")
    ):
        raise _refuse(
            RefusalKind.MISSING_AUTHORITY,
            "what regaining Hit Points ends is not typed",
        )
    return [
        _effect(subject, "current_hp", "set", state.hit_points.current + amount),
        _effect(
            subject,
            "death_state",
            "set",
            DeathState(successes=0, failures=0, stable=False, dead=False).model_dump(
                mode="json"
            ),
        ),
        *_end_unconscious(subject, _sourced(subject, "falling_unconscious")),
    ]


def _becomes_stable(
    subject: TurnSubject, dice: DiceService
) -> tuple[DeathState, tuple[int, ...]]:
    """Stable, counters reset, and the recovery interval code rolls from
    ``StableStateFact.recovery`` (OD-15c-2)."""
    rule = _one(subject, "death_saving_throws", DeathSavingThrowFact)
    if LifecycleEvent.BECOMES_STABLE not in rule.reset_on:
        raise _refuse(RefusalKind.MISSING_AUTHORITY, "no typed counter reset")
    recovery = _one(subject, "stable", StableStateFact).recovery
    expr = recovery.dice
    drawn = dice.roll(f"{expr.count}{expr.die.value}")
    after = DeathState(
        successes=0,
        failures=0,
        stable=True,
        dead=False,
        stable_recovery=StableRecovery(
            instance_id=str(uuid4()),
            interval=drawn.chosen + expr.modifier,
            unit=recovery.unit,
        ),
    )
    return after, drawn.raw_rolls


def roll(prepared: PreparedDeathSave, dice: DiceService) -> RolledDeathSave:
    subject = prepared.subject
    death = subject.stored.state.death_state
    assert death is not None
    result = dice.roll(prepared.expression)
    face = result.chosen
    rule = prepared.rule
    natural = prepared.naturals.get(face)
    if natural is not None and natural.regain_hit_points:
        effects = _regain(subject, natural.regain_hit_points)
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
        after, recovery_rolls = _becomes_stable(subject, dice)
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


# ---------------------------------------------------------------------------
# First aid (the Help action) and the recovery attestations (OD-15c-2)
# ---------------------------------------------------------------------------


def _named(
    proposal: RollProposal,
    actor: TurnCharacter,
    subjects: dict[tuple[str, str], TurnSubject],
) -> TurnSubject:
    ref = proposal.subject
    if ref is None:
        raise _refuse(
            RefusalKind.INVALID_SELECTION, f"{proposal.operation} names no subject"
        )
    key = (ref.kind, str(ref.subject_id))
    if key == ("character", str(actor.subject_id)):
        return actor
    subject = subjects.get(key)
    if subject is None or subject.index is None:
        raise _refuse(
            RefusalKind.MISSING_STATE, f"{ref.kind} {ref.subject_id} was not read"
        )
    return subject


def _cannot_act(subject: TurnSubject) -> str | None:
    """The condition component that keeps *subject* from taking actions."""
    assert subject.index is not None
    for eff in effective(subject, subject.index):
        record = subject.index.record(f"glossary.{eff.condition.value}")
        if record is None:
            continue
        for component in record.components:
            if (
                component.handling is ComponentHandling.STRUCTURED
                and component.applies_when is None
                and any(
                    isinstance(f.fact, ActionRestrictionFact)
                    and f.fact.cost is ActionCost.ACTION
                    for f in component.facts
                )
            ):
                return f"{record.semantic_key}/{component.semantic_key}"
    return None


@dataclass(frozen=True)
class PreparedFirstAid:
    subject: TurnSubject
    #: ``stabilizing`` (a dying subject) or ``knocking_out`` (a knockout).
    mode: str
    check: checks.PreparedCheck


def prepare_first_aid(
    proposal: RollProposal,
    actor: TurnCharacter,
    subjects: dict[tuple[str, str], TurnSubject],
) -> PreparedFirstAid:
    """The acting character's first aid on the named subject, or a typed
    refusal: the subject must be dying or knocked out."""
    subject = _named(proposal, actor, subjects)
    if subject is actor:
        raise _refuse(RefusalKind.INVALID_SELECTION, "first aid is given to another")
    blocked = _cannot_act(actor)
    if blocked:
        raise _refuse(
            RefusalKind.INVALID_SELECTION, f"the helper cannot act ({blocked})"
        )
    if dying(subject):
        mode = "stabilizing"
    elif _sourced(subject, "knocking_out"):
        mode = "knocking_out"
    else:
        raise _refuse(
            RefusalKind.INVALID_SELECTION,
            "first aid needs a dying or knocked-out subject",
        )
    check = checks.prepare(
        proposal.model_copy(update={"check_identity": f"{_RULES}/{mode}"}), actor
    )
    if mode == "stabilizing":
        stabilization = _one(subject, "stabilizing", StabilizationFact)
        if stabilization.on_success is not StabilizeOutcome.STABLE:
            raise _refuse(
                RefusalKind.MISSING_AUTHORITY, "the success of stabilizing is not typed"
            )
        _one(subject, "stable", StableStateFact)
    else:
        knockout = _one(subject, "knocking_out", KnockoutAlternativeFact)
        if LifecycleEvent.FIRST_AID_SUCCESS not in knockout.ends_early_on:
            raise _refuse(
                RefusalKind.MISSING_AUTHORITY, "first aid ending a knockout is untyped"
            )
    return PreparedFirstAid(subject, mode, check)


@dataclass(frozen=True)
class RolledFirstAid:
    prepared: PreparedFirstAid
    rolled: checks.RolledCheck
    effects: tuple[SheetEffect, ...]
    recovery_rolls: tuple[int, ...]

    def provenance_json(self) -> str:
        provenance = json.loads(self.rolled.provenance_json())
        provenance.update(
            {
                "first_aid": self.prepared.mode,
                "subject": {
                    "kind": _kind(self.prepared.subject),
                    "subject_id": str(self.prepared.subject.subject_id),
                },
                "recovery_rolls": list(self.recovery_rolls),
            }
        )
        return json.dumps(provenance, sort_keys=True)


def roll_first_aid(prepared: PreparedFirstAid, dice: DiceService) -> RolledFirstAid:
    rolled = checks.roll(prepared.check, dice)
    subject = prepared.subject
    if rolled.outcome != "success":
        return RolledFirstAid(prepared, rolled, (), ())
    if prepared.mode == "stabilizing":
        after, recovery_rolls = _becomes_stable(subject, dice)
        effect = _effect(subject, "death_state", "set", after.model_dump(mode="json"))
        return RolledFirstAid(prepared, rolled, (effect,), recovery_rolls)
    effects = _end_unconscious(subject, _sourced(subject, "knocking_out"))
    return RolledFirstAid(prepared, rolled, tuple(effects), ())


@dataclass(frozen=True)
class Attested:
    """The result of a recovery attestation: no die, typed effects."""

    subject: TurnSubject
    outcome: str
    effects: tuple[SheetEffect, ...]
    certificate: Certificate

    def provenance_json(self, proposal: RollProposal) -> str:
        assert proposal.attestation is not None
        return json.dumps(
            {
                "operation": proposal.operation,
                "subject": {
                    "kind": _kind(self.subject),
                    "subject_id": str(self.subject.subject_id),
                },
                "attestation": proposal.attestation.model_dump(mode="json"),
                "result": self.outcome,
                "certificate": self.certificate.as_json(),
            },
            sort_keys=True,
        )


def attest(
    proposal: RollProposal,
    actor: TurnCharacter,
    subjects: dict[tuple[str, str], TurnSubject],
) -> Attested:
    """Apply a ``stable_recovery`` or ``knockout_recovery`` attestation, or
    refuse (typed). The GameMaster attests time; code holds the interval and
    the consequence, and an instance is consumed once."""
    subject = _named(proposal, actor, subjects)
    assert subject.index is not None
    operation = Operation(proposal.operation or "")
    certificate = certify(operation, subject.index)
    attestation = proposal.attestation
    if attestation is None:
        raise _refuse(
            RefusalKind.INVALID_SELECTION, f"{operation.value} names no attestation"
        )
    state = subject.stored.state
    if operation is Operation.STABLE_RECOVERY:
        death = state.death_state
        recovery = death.stable_recovery if death is not None else None
        if recovery is None or recovery.instance_id != attestation.instance_id:
            raise _refuse(
                RefusalKind.INVALID_SELECTION,
                f"{attestation.instance_id!r} is not the current Stable recovery "
                "of the subject",
            )
        if attestation.elapsed_hours is None:
            raise _refuse(
                RefusalKind.INVALID_SELECTION, "a Stable recovery attests elapsed hours"
            )
        stable = _one(subject, "stable", StableStateFact).recovery
        if recovery.unit is not stable.unit or stable.unit.value != "hour":
            raise _refuse(
                RefusalKind.MISSING_AUTHORITY, "the recovery interval is not in hours"
            )
        if attestation.elapsed_hours < recovery.interval:
            return Attested(subject, "not_yet", (), certificate)
        effects = _regain(subject, stable.regain_hit_points)
        return Attested(subject, "recovered", tuple(effects), certificate)
    if operation is Operation.KNOCKOUT_RECOVERY:
        if attestation.elapsed_hours is not None:
            raise _refuse(
                RefusalKind.INVALID_SELECTION,
                "a knockout recovery attests the completed Short Rest only",
            )
        if attestation.instance_id not in _sourced(subject, "knocking_out"):
            raise _refuse(
                RefusalKind.INVALID_SELECTION,
                f"{attestation.instance_id!r} is not a knockout Unconscious on "
                "this subject",
            )
        knockout = _one(subject, "knocking_out", KnockoutAlternativeFact)
        if knockout.ends_after is not RestKind.SHORT_REST:
            raise _refuse(
                RefusalKind.MISSING_AUTHORITY, "the ending of a knockout is untyped"
            )
        effects = _end_unconscious(subject, [attestation.instance_id])
        return Attested(subject, "recovered", tuple(effects), certificate)
    raise _refuse(
        RefusalKind.UNSUPPORTED_CAPABILITY, f"{operation.value} is not an attestation"
    )
