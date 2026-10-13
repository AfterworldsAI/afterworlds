"""Typed clauses printed in a creature's attack entry — CRD Issue 15c
(codex-c7-recert-coverage-review, "same-entry creature clause families").

An entry's hit text beyond its damage is typed as ``Clause*`` facts of the
same entry. :func:`plan` reads every one and either executes it here or
refuses, before any die: no clause is ever skipped. The shapes executed are
exactly those of the C5 capability-positive entries:

* a leading predicate on the target's size and, for a charge, on the
  attacker having moved a typed distance straight toward the target
  immediately before the hit (an OD-15c-1 spatial selection, required when
  printed); under it, the target has the Prone condition, and the attacker
  may make one printed follow-up attack against it (the next proposal);
* replacement damage when the attack roll had Advantage;
* the target dies if reduced to 0 Hit Points by this attack;
* clauses with no mechanical consequence here: a weapon that returns to the
  creature's hand (creature weapons are not tracked items), and underwater
  not granting Fire Resistance (underwater Resistance is not executed, so
  nothing grants it).

Every other clause family, field or link refuses as unsupported.
"""

from __future__ import annotations

from dataclasses import dataclass

from afterworlds.ingestion.mechanical.representation import (
    ClauseBranch,
    ClauseBranchFact,
    ClauseConditionalDamageFact,
    ClauseConditionFact,
    ClauseDamageQualificationFact,
    ClauseFollowUpAttackFact,
    ClausePart,
    ClausePredicateFact,
    ClauseReturningWeaponFact,
    ClauseZeroHitPointCause,
    ClauseZeroHitPointOutcomeFact,
    ConditionEffectKind,
    ConditionKind,
    CreatureAttackFact,
    CreatureSize,
    DamageMode,
    DamageTerm,
)
from afterworlds.ingestion.mechanical.representation import (
    ClauseZeroHitPointResult as ZeroResult,
)
from afterworlds.models.rpg import CreatureAttackSelection
from afterworlds.pipeline.rpg.capability import AdjudicationRefusal, RefusalKind
from afterworlds.pipeline.rpg.defense import facts_of
from afterworlds.pipeline.rpg.defense import template as template_of
from afterworlds.services.dnd5e_state.turn import TurnCreature

__all__ = ["HitClauses", "charged", "clauses", "plan"]

_PREDICATE_FIELDS = (
    "attack_roll_had_advantage",
    "target_is_creature",
    "target_type",
    "target_reduced_to_0_hit_points_by_this",
    "target_hit_points_at_most",
    "otherwise",
    "while_condition",
    "while_state",
)
_WHEN_FIELDS = (
    "source_bloodied",
    "target_bloodied",
    "target_grappled_by_source",
    "source_moved_straight_toward_target_ft_min",
    "target_maximum_size",
)


@dataclass(frozen=True)
class HitClauses:
    """What an entry's clauses do, read once before any die."""

    #: The predicate's typed limits; ``None``: not printed.
    maximum_size: CreatureSize | None = None
    charge_ft: int | None = None
    #: Under the predicate: the target has the Prone condition.
    prone: bool = False
    #: Under the predicate: the attacker may make one attack with this entry.
    follow_up: str | None = None
    #: Replacing ``hit_damage[index]`` when the roll had Advantage.
    advantage_damage: tuple[int, DamageTerm] | None = None
    dies_at_zero: bool = False
    #: Clauses read with no consequence here, for provenance.
    no_effect: tuple[str, ...] = ()

    @property
    def predicated(self) -> bool:
        return self.maximum_size is not None or self.charge_ft is not None


def clauses(creature: TurnCreature, entry: str) -> list[object]:
    """Every ``Clause*`` fact of *creature*'s *entry*."""
    assert creature.index is not None
    return [
        f
        for f in facts_of(creature.index, template_of(creature))
        if getattr(f, "entry", None) == entry
        and f.FAMILY.value.startswith("clause_")  # type: ignore[attr-defined]
    ]


def _unsupported(where: str, what: str) -> AdjudicationRefusal:
    return AdjudicationRefusal(
        RefusalKind.UNSUPPORTED_CAPABILITY,
        f"{where} prints {what}, which is not executable here",
    )


def plan(creature: TurnCreature, fact: CreatureAttackFact) -> HitClauses:
    """The entry's clauses as one plan, or a refusal naming the first that
    is not executed here."""
    where = f"{template_of(creature)}/{fact.entry}"
    found = clauses(creature, fact.entry)
    for f in found:
        links = (
            f.bound_effect,  # type: ignore[attr-defined]
            f.lasts_while_effect,  # type: ignore[attr-defined]
            f.ends_effects,  # type: ignore[attr-defined]
            f.duration_of_effects,  # type: ignore[attr-defined]
        )
        if f.part is not ClausePart.HIT or any(links):  # type: ignore[attr-defined]
            raise _unsupported(where, "a linked or non-hit clause")
    predicates = [f for f in found if isinstance(f, ClausePredicateFact)]
    if len(predicates) > 1 or any(
        getattr(p, name) not in (None, False)
        for p in predicates
        for name in _PREDICATE_FIELDS
    ):
        raise _unsupported(where, "a predicate")
    scope = (predicates[0].piece,) if predicates else ()
    out: dict[str, object] = {}
    if predicates:
        out["maximum_size"] = predicates[0].target_maximum_size
        out["charge_ft"] = predicates[0].source_moved_straight_toward_target_ft_min
    no_effect: list[str] = []
    for f in found:
        if isinstance(f, ClausePredicateFact):
            continue
        if isinstance(f, ClauseConditionFact) and f.under_predicates == scope:
            if f.replaces_condition is None and [
                (e.condition, e.effect) for e in f.effects
            ] == [(ConditionKind.PRONE, ConditionEffectKind.APPLIES)]:
                out["prone"] = True
                continue
        elif isinstance(f, ClauseFollowUpAttackFact) and scope:
            if f.under_predicates == scope and f.count == 1 and f.optional:
                out["follow_up"] = f.attack
                continue
        elif isinstance(f, ClauseConditionalDamageFact) and not f.under_predicates:
            other = [getattr(f.when, name) for name in _WHEN_FIELDS]
            if (
                f.mode is DamageMode.INSTEAD
                and f.when.attack_roll_had_advantage
                and not any(v is not None for v in other)
                and f.replaces_hit_damage_index is not None
                and not f.unconditional_hit_damage_indices
                and f.replaces_hit_damage_index < len(fact.hit_damage)
                and f.term.damage_type is not None
                and not f.term.addends
            ):
                out["advantage_damage"] = (f.replaces_hit_damage_index, f.term)
                continue
        elif isinstance(f, ClauseZeroHitPointOutcomeFact) and not f.under_predicates:
            if (
                f.becomes is ZeroResult.DEAD
                and f.when is ClauseZeroHitPointCause.REDUCED_TO_ZERO_BY_THIS_ATTACK
            ):
                out["dies_at_zero"] = True
                continue
        elif isinstance(f, ClauseDamageQualificationFact):
            if not f.underwater_fire_resistance_applies:
                no_effect.append("underwater_fire_resistance_not_granted")
                continue
        elif (
            isinstance(f, ClauseReturningWeaponFact | ClauseBranchFact)
            and f.branch is ClauseBranch.HIT_OR_MISS
            and any(isinstance(g, ClauseReturningWeaponFact) for g in found)
        ):
            if isinstance(f, ClauseReturningWeaponFact):
                no_effect.append("returning_weapon")
            continue
        raise _unsupported(where, f"a {f.FAMILY.value} clause")  # type: ignore[attr-defined]
    if predicates and not (out.get("prone") or out.get("follow_up")):
        raise _unsupported(where, "a predicate scoping nothing executed")
    return HitClauses(no_effect=tuple(no_effect), **out)  # type: ignore[arg-type]


def charged(sel: CreatureAttackSelection, clauses_: HitClauses, where: str) -> bool:
    """Whether the GameMaster selected that the attacker moved at least the
    printed distance straight toward the target immediately before the hit
    (OD-15c-1); required when printed, refused when not."""
    if clauses_.charge_ft is None:
        if sel.moved_straight_toward_target is not None:
            raise AdjudicationRefusal(
                RefusalKind.INVALID_SELECTION,
                f"{where} prints no movement predicate",
            )
        return True
    if sel.moved_straight_toward_target is None:
        raise AdjudicationRefusal(
            RefusalKind.MISSING_STATE,
            f"{where}: did the attacker move {clauses_.charge_ft}+ feet straight "
            "toward the target immediately before the hit?",
        )
    return sel.moved_straight_toward_target
