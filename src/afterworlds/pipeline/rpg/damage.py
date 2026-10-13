"""Damage to one subject and its zero-HP consequences — CRD Issue 15c.

:func:`take_damage` derives, from the target's own exact binding and state,
the subject-addressed effects of *amount* damage of one type. The source
rules it executes, each read from typed authority:

* damage responses: immunity takes none; resistance halves, rounding down
  (``glossary.resistance/halving``); vulnerability doubles
  (``glossary.vulnerability/doubling``). Both on one type refuses: the order
  of application is prose here (``play.damage_and_healing``);
* temporary hit points absorb damage first, the rest carrying over
  (``temporary_hit_point_absorption``);
* hit points: overflow is computed before the 0 bound, then ``current`` is
  written at the typed minimum (``hit_point_bound``); ADR-0003 keeps no
  persistence floor;
* reaching 0 HP, by the subject's treatment: a character (or a monster the
  GameMaster treats as one) falls Unconscious and dying unless the remaining
  damage is at least its HP maximum (massive damage); a monster dies. A
  creature without a recorded treatment refuses;
* damage while at 0 HP: a death-save failure (two for a Critical Hit), or
  death if the damage is at least the HP maximum; it ends Stable.

The knockout alternative, death saves, stabilizing and recovery are their own
operations.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from uuid import uuid4

from afterworlds.ingestion.mechanical.representation import (
    ConditionKind,
    DamageAtZeroHitPointsFact,
    DamageModificationFact,
    DamageResponseFact,
    DamageResponseKind,
    DamageType,
    HitPointBoundFact,
    KnockoutAlternativeFact,
    KnockoutTrigger,
    MassiveDamageFact,
    StableStateFact,
    TemporaryHitPointAbsorptionFact,
    ZeroHitPointOutcomeFact,
    ZeroHitPointResult,
)
from afterworlds.models.dnd5e_state import DeathState
from afterworlds.models.enums import ConditionVisibility
from afterworlds.models.rpg import SheetEffect
from afterworlds.pipeline.rpg.capability import AdjudicationRefusal, RefusalKind
from afterworlds.pipeline.rpg.conditions import effective
from afterworlds.pipeline.rpg.defense import damage_responses, facts_of
from afterworlds.pipeline.rpg.mastery import other_effects
from afterworlds.services.dnd5e_state.authority import AuthorityIndex
from afterworlds.services.dnd5e_state.turn import TurnCreature, TurnSubject

__all__ = [
    "DAMAGE_PROCEDURE",
    "DamageTaken",
    "knockout_rule",
    "possible_conditions",
    "preflight",
    "take_damage",
]

_RULES = "play.damage_and_healing"
#: Procedure components this module implements (certified with the operation).
DAMAGE_PROCEDURE: tuple[tuple[str, str], ...] = (
    ("glossary.resistance", "halving"),
    ("glossary.vulnerability", "doubling"),
    ("glossary.immunity", "no_effect"),
    (_RULES, "lost_first"),
    (_RULES, "hit_points"),
    (_RULES, "falling_unconscious"),
    (_RULES, "monster_death"),
    (_RULES, "massive_damage"),
    (_RULES, "damage_at_0_hit_points"),
    (_RULES, "stable"),
    (_RULES, "order_of_application"),
)


def _refuse(kind: RefusalKind, detail: str) -> AdjudicationRefusal:
    return AdjudicationRefusal(kind, detail)


def _one[T](index: AuthorityIndex, component: str, family: type[T]) -> T:
    found = [f for f in facts_of(index, _RULES, component) if isinstance(f, family)]
    if len(found) != 1:
        raise _refuse(
            RefusalKind.MISSING_AUTHORITY,
            f"{_RULES}/{component} states no single {family.__name__}",
        )
    return found[0]


def _modification(
    index: AuthorityIndex, record: str, component: str
) -> DamageModificationFact:
    found = [
        f
        for f in facts_of(index, record, component)
        if isinstance(f, DamageModificationFact)
    ]
    if len(found) != 1:
        raise _refuse(
            RefusalKind.MISSING_AUTHORITY, f"{record}/{component} is not typed"
        )
    return found[0]


def _modified(
    index: AuthorityIndex, amount: int, responses: tuple[DamageResponseKind, ...]
) -> int:
    if DamageResponseKind.IMMUNITY in responses:
        return 0
    resist = DamageResponseKind.RESISTANCE in responses
    vulnerable = DamageResponseKind.VULNERABILITY in responses
    if resist and vulnerable:
        raise _refuse(
            RefusalKind.UNSUPPORTED_CAPABILITY,
            "resistance and vulnerability to one damage type need the prose order "
            "of application",
        )
    if resist:
        f = _modification(index, "glossary.resistance", "halving")
        return amount * f.factor.numerator // f.factor.denominator
    if vulnerable:
        f = _modification(index, "glossary.vulnerability", "doubling")
        return amount * f.factor.numerator // f.factor.denominator
    return amount


@dataclass(frozen=True)
class DamageTaken:
    """What one subject took and what followed."""

    rolled: int
    taken: int
    responses: tuple[str, ...]
    outcome: str
    effects: tuple[SheetEffect, ...]

    def provenance(self) -> dict[str, object]:
        return {
            "rolled": self.rolled,
            "taken": self.taken,
            "responses": list(self.responses),
            "outcome": self.outcome,
        }


def _as_character(target: TurnSubject) -> bool:
    if not isinstance(target, TurnCreature):
        return True
    treatment = target.stored.state.zero_hit_point_treatment
    if treatment is None:
        raise _refuse(
            RefusalKind.MISSING_STATE,
            f"creature {target.subject_id} has no recorded zero-HP treatment "
            "(character or monster); its template's location does not decide it",
        )
    return treatment.as_character


def preflight(target: TurnSubject, damage_type: DamageType) -> None:
    """Every refusal :func:`take_damage` could raise for *target* and
    *damage_type*, raised now, before any die is rolled: the recorded state the
    lifecycle needs, the zero-HP treatment and the damage responses."""
    index = target.index
    if index is None:
        raise _refuse(
            RefusalKind.MISSING_AUTHORITY, "the target's authority is not resolved"
        )
    state = target.stored.state
    missing = [
        name
        for name, value in (
            ("hit_points", state.hit_points),
            ("conditions", state.conditions),
            ("death_state", state.death_state),
        )
        if value is None
    ]
    if missing:
        raise _refuse(
            RefusalKind.MISSING_STATE, f"the target records no {', '.join(missing)}"
        )
    _as_character(target)
    unexecuted = other_effects(target)
    if unexecuted:
        raise _refuse(
            RefusalKind.UNSUPPORTED_CAPABILITY,
            f"the target's active effect {unexecuted[0].source.record_key} can "
            "change the damage it takes and is not executable here",
        )
    _modified(index, 1, damage_responses(target, damage_type))
    for eff in effective(target, index):
        for fact in facts_of(index, f"glossary.{eff.condition.value}"):
            if isinstance(fact, DamageResponseFact):
                raise _refuse(
                    RefusalKind.UNSUPPORTED_CAPABILITY,
                    f"the target's {eff.condition.value} condition changes the "
                    "damage it takes and is not executable here",
                )
    for component, family in (
        ("lost_first", TemporaryHitPointAbsorptionFact),
        ("hit_points", HitPointBoundFact),
        ("massive_damage", MassiveDamageFact),
        ("damage_at_0_hit_points", DamageAtZeroHitPointsFact),
        ("stable", StableStateFact),
    ):
        _one(index, component, family)


def possible_conditions(target: TurnSubject) -> frozenset[ConditionKind]:
    """Every condition damage could apply to *target*: Unconscious on falling
    to 0 Hit Points, unless it is treated as a monster (which dies)."""
    if isinstance(target, TurnCreature):
        treatment = target.stored.state.zero_hit_point_treatment
        if treatment is not None and not treatment.as_character:
            return frozenset()
    return frozenset({ConditionKind.UNCONSCIOUS})


def knockout_rule(target: TurnSubject) -> KnockoutAlternativeFact:
    """The typed knockout alternative (``knocking_out``), or a refusal."""
    assert target.index is not None
    rule = _one(target.index, "knocking_out", KnockoutAlternativeFact)
    if (
        rule.trigger is not KnockoutTrigger.WOULD_REDUCE_TO_ZERO_HIT_POINTS
        or rule.condition is not ConditionKind.UNCONSCIOUS
    ):
        raise _refuse(RefusalKind.MISSING_AUTHORITY, "the knockout is not typed")
    return rule


def take_damage(
    target: TurnSubject,
    amount: int,
    damage_type: DamageType,
    *,
    critical: bool,
    knock_out: bool = False,
    more: tuple[tuple[int, DamageType], ...] = (),
) -> DamageTaken:
    """The effects on *target* of *amount* damage of *damage_type* (and of
    each further ``(amount, type)`` in *more*: one hit's other damage terms),
    or a typed refusal. Pure: nothing is written.

    Responses apply per type; the hit's damage is then one amount, so
    temporary hit points, the bound, massive damage and every zero-HP
    consequence are judged once per hit (``play.damage_and_healing``)."""
    index = target.index
    if index is None:
        raise _refuse(
            RefusalKind.MISSING_AUTHORITY, "the target's authority is not resolved"
        )
    state = target.stored.state
    hp = state.hit_points
    if hp is None:
        raise _refuse(RefusalKind.MISSING_STATE, "the target records no hit points")
    found: list[DamageResponseKind] = []
    taken = 0
    for part, part_type in ((amount, damage_type), *more):
        part_responses = damage_responses(target, part_type)
        found += part_responses
        taken += _modified(index, max(0, part), part_responses)
    responses = tuple(found)
    amount += sum(part for part, _ in more)
    kind: str = "character" if not isinstance(target, TurnCreature) else "creature"
    subject = {"subject_kind": kind, "subject_id": target.subject_id}

    def effect(target_field: str, operation: str, value: object) -> SheetEffect:
        return SheetEffect(
            target=target_field,
            operation=operation,  # type: ignore[arg-type]
            value_json=json.dumps(value),
            **subject,  # type: ignore[arg-type]
        )

    effects: list[SheetEffect] = []
    absorb = _one(index, "lost_first", TemporaryHitPointAbsorptionFact)
    remaining = taken
    if absorb.absorbed_first and hp.temporary:
        absorbed = min(hp.temporary, remaining)
        remaining -= absorbed
        effects.append(effect("temporary_hp", "set", hp.temporary - absorbed))
        if not absorb.overflow_to_hit_points:
            remaining = 0
    if remaining == 0:
        return DamageTaken(
            amount, taken, tuple(r.value for r in responses), "absorbed", tuple(effects)
        )

    floor = _one(index, "hit_points", HitPointBoundFact).minimum_current
    maximum = hp.maximum - (hp.maximum_reduction or 0)
    death = state.death_state

    if hp.current <= floor:
        # Already at 0 Hit Points.
        rule = _one(index, "damage_at_0_hit_points", DamageAtZeroHitPointsFact)
        if not _as_character(target):
            return DamageTaken(
                amount, taken, tuple(r.value for r in responses), "already_dead", ()
            )
        if death is None:
            raise _refuse(
                RefusalKind.MISSING_STATE, "the target records no death state"
            )
        if death.dead:
            return DamageTaken(
                amount, taken, tuple(r.value for r in responses), "already_dead", ()
            )
        stable = _one(index, "stable", StableStateFact)
        failures = death.failures + (
            rule.critical_hit_failures if critical else rule.failures
        )
        dead = remaining >= maximum or failures >= 3
        new = DeathState(
            successes=death.successes,
            failures=min(failures, 3),
            stable=death.stable and not stable.damage_ends_stable,
            dead=dead,
        )
        effects.append(effect("death_state", "set", new.model_dump()))
        outcome = "died" if dead else "death_save_failure"
        return DamageTaken(
            amount, taken, tuple(r.value for r in responses), outcome, tuple(effects)
        )

    new_current = hp.current - remaining
    if new_current > floor:
        effects.append(effect("current_hp", "set", new_current))
        return DamageTaken(
            amount, taken, tuple(r.value for r in responses), "damaged", tuple(effects)
        )

    if knock_out:
        # The attacker reduces it to the typed Hit Points instead, Unconscious;
        # it starts a Short Rest (its recovery instance is this condition).
        knockout = knockout_rule(target)
        effects.append(effect("current_hp", "set", knockout.set_hit_points))
        effects.append(
            effect(
                "unconscious",
                "apply_condition",
                {
                    "instance_id": str(uuid4()),
                    "condition": ConditionKind.UNCONSCIOUS.value,
                    "visibility": ConditionVisibility.VISIBLE.value,
                    "source": {"record_key": _RULES, "component_key": "knocking_out"},
                },
            )
        )
        return DamageTaken(
            amount,
            taken,
            tuple(r.value for r in responses),
            "knocked_out",
            tuple(effects),
        )

    # Reaching 0 Hit Points: overflow before the bound.
    overflow = floor - new_current
    effects.append(effect("current_hp", "set", floor))
    as_character = _as_character(target)
    outcomes = {
        f.subject.value: f
        for f in facts_of(index, _RULES)
        if isinstance(f, ZeroHitPointOutcomeFact) and f.trigger is None
    }
    if not as_character:
        if (
            outcomes.get("monster") is None
            or outcomes["monster"].outcome is not ZeroHitPointResult.DIES
        ):
            raise _refuse(RefusalKind.MISSING_AUTHORITY, "no typed monster death rule")
        effects.append(
            effect(
                "death_state",
                "set",
                DeathState(
                    successes=0, failures=0, stable=False, dead=True
                ).model_dump(),
            )
        )
        return DamageTaken(
            amount, taken, tuple(r.value for r in responses), "died", tuple(effects)
        )
    massive = _one(index, "massive_damage", MassiveDamageFact)
    if (
        overflow >= maximum
        and massive.dies_when_remainder_at_least.value == "hit_point_maximum"
    ):
        effects.append(
            effect(
                "death_state",
                "set",
                DeathState(
                    successes=0, failures=0, stable=False, dead=True
                ).model_dump(),
            )
        )
        return DamageTaken(
            amount,
            taken,
            tuple(r.value for r in responses),
            "died_massive_damage",
            tuple(effects),
        )
    falling = outcomes.get("character")
    if (
        falling is None
        or falling.outcome is not ZeroHitPointResult.UNCONSCIOUS_AND_DYING
    ):
        raise _refuse(
            RefusalKind.MISSING_AUTHORITY, "no typed falling-unconscious rule"
        )
    if state.conditions is None:
        raise _refuse(RefusalKind.MISSING_STATE, "the target records no conditions")
    effects.append(
        effect(
            "unconscious",
            "apply_condition",
            {
                "condition": "unconscious",
                "visibility": ConditionVisibility.VISIBLE.value,
                "source": {
                    "record_key": _RULES,
                    "component_key": "falling_unconscious",
                },
            },
        )
    )
    effects.append(
        effect(
            "death_state",
            "set",
            DeathState(successes=0, failures=0, stable=False, dead=False).model_dump(),
        )
    )
    return DamageTaken(
        amount,
        taken,
        tuple(r.value for r in responses),
        "unconscious_and_dying",
        tuple(effects),
    )
