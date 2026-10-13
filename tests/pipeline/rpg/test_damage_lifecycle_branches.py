"""CRD Issue 15c — damage/lifecycle branches through a real weapon attack:
temporary Hit Points absorbing (and overflowing), damage to a Stable target
at 0 HP, and ordinary noncritical damage to a dying one. Every expectation is
read from the typed rules; every effect is applied through the state applier
the turn uses."""

from __future__ import annotations

import dataclasses
import json
from typing import Any

import pytest

from afterworlds.ingestion.mechanical.representation import (
    DamageAtZeroHitPointsFact,
    StableStateFact,
    TemporaryHitPointAbsorptionFact,
)
from afterworlds.models.dnd5e_state import HitPoints
from afterworlds.pipeline.rpg.defense import facts_of
from afterworlds.services.dnd5e_state.turn import TurnCreature, with_effects
from tests.pipeline.rpg.test_actor_turns import CHARACTER, _dying
from tests.pipeline.rpg.test_weapon_attacks import (
    CLUB,
    DAGGER,
    _attacker,
    _creature,
    _dice,
    _proposal,
    _run,
)
from tests.pipeline.rpg.test_zero_hp_lifecycle import _stable

_RULES = "play.damage_and_healing"


def _rule[T](subject: TurnCreature, component: str, family: type[T]) -> T:
    assert subject.index is not None
    (fact,) = [
        f for f in facts_of(subject.index, _RULES, component) if isinstance(f, family)
    ]
    return fact


def _club_hit(target: TurnCreature, damage: int) -> Any:
    """A Club hit (Str 8: -1) of ``damage + 1`` rolled, noncritical."""
    return _run(_attacker(CLUB), target, _proposal(target), _dice((15,), (damage + 1,)))


def _thrown_dagger(target: TurnCreature, d20: int = 15) -> Any:
    """A thrown Dagger from beyond 5 feet: no automatic Critical Hit on an
    Unconscious target (its Advantage and Prone's Disadvantage cancel)."""
    proposal = _proposal(
        target,
        DAGGER,
        range="within_normal_range",
        thrown=True,
        hostiles_within_5_feet=(),
        ability="dexterity",
        target_within_5_feet=False,
    )
    return _run(_attacker(DAGGER), target, proposal, _dice((d20,), (2,)))


def _targets(record: Any) -> list[str]:
    return [e.target for e in record.sheet_effects]


def _with_temporary(current: int, temporary: int) -> TurnCreature:
    wolf = _creature(hp=current, treatment=CHARACTER)
    state = wolf.stored.state.model_copy(
        update={
            "hit_points": HitPoints(
                current=current, maximum=current, temporary=temporary
            )
        }
    )
    return dataclasses.replace(
        wolf, stored=dataclasses.replace(wolf.stored, state=state)
    )


# ---------------------------------------------------------------------------
# Temporary Hit Points
# ---------------------------------------------------------------------------


def test_temporary_hit_points_absorb_damage_less_than_them() -> None:
    target = _with_temporary(current=20, temporary=5)
    rule = _rule(target, "lost_first", TemporaryHitPointAbsorptionFact)
    assert rule.absorbed_first
    record = _club_hit(target, damage=2)
    assert record.outcome == "success"
    assert _targets(record) == ["temporary_hp"]  # current is untouched
    damage = json.loads(record.modifiers_json)["damage"]
    assert (damage["taken"], damage["outcome"]) == (2, "absorbed")
    after = with_effects(target, list(record.sheet_effects))
    hp = after.stored.state.hit_points
    assert hp is not None and (hp.temporary, hp.current) == (3, 20)


def test_damage_beyond_temporary_hit_points_carries_over() -> None:
    target = _with_temporary(current=20, temporary=1)
    rule = _rule(target, "lost_first", TemporaryHitPointAbsorptionFact)
    assert rule.absorbed_first and rule.overflow_to_hit_points
    record = _club_hit(target, damage=3)
    assert _targets(record) == ["temporary_hp", "current_hp"]
    damage = json.loads(record.modifiers_json)["damage"]
    assert (damage["taken"], damage["outcome"]) == (3, "damaged")
    after = with_effects(target, list(record.sheet_effects))
    hp = after.stored.state.hit_points
    assert hp is not None and (hp.temporary, hp.current) == (0, 20 - (3 - 1))


# ---------------------------------------------------------------------------
# Damage at 0 Hit Points
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("within_5_feet", [False, True])
def test_damage_to_a_stable_target_ends_stability_and_its_recovery(
    within_5_feet: bool,
) -> None:
    """Damage while at 0 HP is a death-save failure (two for a Critical Hit:
    a Club from within 5 feet of an Unconscious target is one) and ends
    Stable; the pending recovery instance belongs to a Stable subject and
    goes with it."""
    stable = _stable()
    before = stable.stored.state.death_state
    assert before is not None and before.stable and before.stable_recovery
    at_zero = _rule(stable, "damage_at_0_hit_points", DamageAtZeroHitPointsFact)
    assert _rule(stable, "stable", StableStateFact).damage_ends_stable
    if within_5_feet:
        record = _run(_attacker(CLUB), stable, _proposal(stable), _dice((15,), (3,)))
        assert record.outcome == "critical_success"
        failures = at_zero.critical_hit_failures
    else:
        record = _thrown_dagger(stable)
        assert record.outcome == "success"
        failures = at_zero.failures
    assert _targets(record) == ["death_state"]  # no HP write below the bound
    assert json.loads(record.modifiers_json)["damage"]["outcome"] == (
        "death_save_failure"
    )
    after = with_effects(stable, list(record.sheet_effects)).stored.state
    assert after.death_state is not None
    assert after.death_state.model_dump() == {
        "successes": before.successes,
        "failures": before.failures + failures,
        "stable": False,
        "dead": False,
        "stable_recovery": None,
    }
    assert after.hit_points == stable.stored.state.hit_points
    assert after.conditions == stable.stored.state.conditions  # still Unconscious


@pytest.mark.parametrize(("failures", "dead"), [(0, False), (1, False), (2, True)])
def test_ordinary_noncritical_damage_at_0_hit_points_is_one_failure(
    failures: int, dead: bool
) -> None:
    dying = _dying(successes=1, failures=failures)
    at_zero = _rule(dying, "damage_at_0_hit_points", DamageAtZeroHitPointsFact)
    record = _thrown_dagger(dying)
    assert record.outcome == "success"  # a hit, not a Critical Hit
    assert json.loads(record.modifiers_json)["damage"]["outcome"] == (
        "died" if dead else "death_save_failure"
    )
    after = with_effects(dying, list(record.sheet_effects)).stored.state.death_state
    assert after is not None
    assert (after.successes, after.failures, after.dead) == (
        1,
        failures + at_zero.failures,
        dead,
    )


# ---------------------------------------------------------------------------
# Temporary Hit Points at 0 Hit Points (codex-zero-hp-temporary-damage-review)
# ---------------------------------------------------------------------------


def _at_zero(base: TurnCreature, temporary: int) -> TurnCreature:
    state = base.stored.state.model_copy(
        update={"hit_points": HitPoints(current=0, maximum=11, temporary=temporary)}
    )
    return dataclasses.replace(
        base, stored=dataclasses.replace(base.stored, state=state)
    )


def _hit(target: TurnCreature, amount: int, kind: str = "piercing") -> Any:
    from afterworlds.ingestion.mechanical.representation import DamageType
    from afterworlds.pipeline.rpg.damage import take_damage

    return take_damage(target, amount, DamageType(kind), critical=False)


def _death(taken: Any) -> Any:
    from afterworlds.models.dnd5e_state import DeathState

    (effect,) = [e for e in taken.effects if e.target == "death_state"]
    return DeathState.model_validate(json.loads(effect.value_json))


def _temporary(taken: Any) -> int | None:
    found = [e for e in taken.effects if e.target == "temporary_hp"]
    return json.loads(found[0].value_json) if found else None


def test_damage_temporary_hp_absorbs_at_zero_is_still_a_failure() -> None:
    taken = _hit(_at_zero(_dying(), 5), 3)
    assert (taken.outcome, _temporary(taken)) == ("death_save_failure", 2)
    assert _death(taken).failures == 1 and not _death(taken).dead


def test_absorbed_damage_ends_stability_at_zero() -> None:
    taken = _hit(_at_zero(_stable(), 5), 3)
    death = _death(taken)
    assert _temporary(taken) == 2
    assert (death.stable, death.failures, death.stable_recovery) == (False, 1, None)


def test_damage_at_zero_equal_to_the_maximum_kills_whatever_temporary_hp_took() -> None:
    taken = _hit(_at_zero(_dying(), 5), 11)
    assert taken.outcome == "died" and _death(taken).dead
    assert _temporary(taken) == 0


def test_damage_at_zero_below_the_maximum_after_temporary_hp_is_one_failure() -> None:
    taken = _hit(_at_zero(_dying(), 5), 9)
    assert taken.outcome == "death_save_failure" and not _death(taken).dead


@pytest.mark.parametrize("base", [_dying, _stable], ids=["dying", "stable"])
def test_damage_at_zero_without_temporary_hp_is_a_failure(base: Any) -> None:
    death = _death(_hit(_at_zero(base(), 0), 3))
    assert death.failures == 1 and not death.stable


def test_no_damage_taken_at_zero_changes_nothing() -> None:
    nothing = _hit(_at_zero(_dying(), 5), 0)
    assert (nothing.taken, nothing.effects) == (0, ())
    skeleton = _at_zero(
        _creature("monsters.skeletons.skeleton", hp=11, treatment=CHARACTER), 0
    )
    immune = _hit(skeleton, 3, "poison")
    assert (immune.taken, immune.effects) == (0, ())


def test_temporary_hp_above_zero_absorbs_without_a_failure() -> None:
    target = _with_temporary(current=7, temporary=5)
    taken = _hit(target, 3)
    assert taken.outcome == "absorbed" and _temporary(taken) == 2
    assert [e.target for e in taken.effects] == ["temporary_hp"]
