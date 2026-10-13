"""Action accounting for admitted operations — CRD Issue 15c.

Each operation names the action instance it uses: the turn's one action, its
one Bonus Action, an attack roll the Attack action allows, a Light extra
attack, a Loading weapon's one piece per activation, and once-per-turn
features (Cleave, Nick, Multiattack). :func:`costs` derives those uses from
typed source authority and the actor's current turn; the service consumes them
in order on the coordination document before any die, and records each as a
``use`` event in the delivered transaction (contract G1). Consumption lasts
until the subject's next explicit ``begin_turn`` edge.

Source authority, each typed: ``glossary.attack/attack_roll`` (the Attack
action allows one attack roll), ``play.actions/one_bonus_action``, Light's
``light_extra_attack``, Nick's ``mastery_effect`` (``attack_action`` cost,
once per turn) and Loading's ``ammunition_per_activation``. The turn's one
action (``glossary.action/action``) is a prose universal procedure certified
with the operation.

Not executable, each refused before any die: a further attack roll in one
Attack action (Extra Attack is prose-bound in the accepted authority:
``missing_authority``); reactions, whose triggers are not validated; and any
second use of a once-per-turn slot.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from afterworlds.ingestion.mechanical.representation import (
    ActionAllowanceFact,
    ActionCost,
    AmmunitionPerActivationFact,
    EntrySection,
    GrantedActivity,
    LightExtraAttackFact,
    MasteryCost,
    MasteryEffectFact,
    WeaponMastery,
    WeaponMasteryFact,
    WeaponProperty,
    WeaponPropertyFact,
)
from afterworlds.models.dnd5e_state import SubjectReference, TurnCoordination
from afterworlds.models.rpg import RollProposal
from afterworlds.pipeline.rpg.capability import (
    AdjudicationRefusal,
    Operation,
    RefusalKind,
)
from afterworlds.pipeline.rpg.defense import facts_of
from afterworlds.pipeline.rpg.grants import weapon_mastery
from afterworlds.services.dnd5e_state.turn import (
    TurnCharacter,
    TurnCreature,
    TurnSubject,
)

__all__ = ["ACTION", "BONUS_ACTION", "Use", "costs"]

ACTION = "glossary.action/action"
BONUS_ACTION = "play.actions/one_bonus_action"
ATTACK_ROLL = "glossary.attack/attack_roll"
LIGHT = "equipment.weapons.light/light"
NICK = "equipment.weapons.nick/nick"
LOADING = "equipment.weapons.loading/loading"
CLEAVE = "equipment.weapons.cleave/cleave"


@dataclass(frozen=True)
class Use:
    """One use of an action instance or once-per-turn slot, by a subject."""

    by: SubjectReference
    key: str


def _refuse(kind: RefusalKind, detail: str) -> AdjudicationRefusal:
    return AdjudicationRefusal(kind, detail)


def _ref(subject: TurnSubject) -> SubjectReference:
    kind: Literal["character", "creature"] = (
        "creature" if isinstance(subject, TurnCreature) else "character"
    )
    return SubjectReference(kind=kind, subject_id=subject.subject_id)


def _used(document: TurnCoordination, by: SubjectReference) -> list[str]:
    active = document.active
    if active is None:
        return []
    return [
        u.key
        for u in document.uses
        if u.subject == by and u.instance == active.instance
    ]


def _weapon(actor: TurnCharacter, item_id: object) -> tuple[str, set[WeaponProperty]]:
    assert actor.index is not None
    item = next((i for i in actor.items if i.item_id == item_id), None)
    if item is None:
        raise _refuse(RefusalKind.MISSING_STATE, "the attacker holds no such weapon")
    props = {
        f.weapon_property
        for f in facts_of(actor.index, item.record_key)
        if isinstance(f, WeaponPropertyFact)
    }
    return item.record_key, props


def _one[T](actor: TurnCharacter, record: str, family: type[T]) -> T:
    assert actor.index is not None
    found = [f for f in facts_of(actor.index, record) if isinstance(f, family)]
    if len(found) != 1:
        raise _refuse(RefusalKind.MISSING_AUTHORITY, f"{record} is not typed")
    return found[0]


def _attack_costs(
    proposal: RollProposal, actor: TurnCharacter, document: TurnCoordination
) -> list[Use]:
    sel = proposal.weapon_attack
    assert sel is not None and actor.index is not None
    me = _ref(actor)
    used = _used(document, me)
    record, props = _weapon(actor, sel.weapon_item_id)
    if sel.cleave:
        return [Use(me, CLEAVE)]
    rolls = [k for k in used if k.startswith(f"{ATTACK_ROLL}#")]
    if sel.extra is None:
        allowance = _one(actor, "glossary.attack", ActionAllowanceFact)
        if allowance.activity is not GrantedActivity.ATTACK_ROLL:
            raise _refuse(RefusalKind.MISSING_AUTHORITY, "the Attack action is untyped")
        if len(rolls) >= allowance.count:
            raise _refuse(
                RefusalKind.MISSING_AUTHORITY,
                f"the Attack action allows {allowance.count} attack roll; a further "
                "one needs Extra Attack, which the accepted authority states only in "
                "prose",
            )
        # The weapon record and the individual item: Light needs a different
        # weapon, not a different kind (two Daggers are two weapons).
        uses = [
            Use(me, ACTION),
            Use(me, f"{ATTACK_ROLL}#1:{record}:{sel.weapon_item_id}"),
        ]
        activation = ActionCost.ACTION
    else:
        light = _one(actor, "equipment.weapons.light", LightExtraAttackFact)
        first = [k.split(":")[1:] for k in rolls]  # [record, item id]
        if not first:
            raise _refuse(
                RefusalKind.INVALID_SELECTION,
                "Light's extra attack follows an Attack action attack this turn",
            )
        first_props = {
            f.weapon_property
            for f in facts_of(actor.index, first[0][0])
            if isinstance(f, WeaponPropertyFact)
        }
        if (
            WeaponProperty.LIGHT not in first_props
            or WeaponProperty.LIGHT not in props
            or len(first[0]) != 2
            or first[0][1] == str(sel.weapon_item_id)
        ):
            raise _refuse(
                RefusalKind.INVALID_SELECTION,
                "Light's extra attack is made with a different Light weapon after "
                "an attack with a Light weapon",
            )
        uses = [Use(me, LIGHT)]
        if sel.extra == "light":
            if light.cost is not ActionCost.BONUS_ACTION:
                raise _refuse(RefusalKind.MISSING_AUTHORITY, "Light's cost is untyped")
            bonus = _one(actor, "play.actions", ActionAllowanceFact)
            if bonus.cost is not ActionCost.BONUS_ACTION or bonus.count != 1:
                raise _refuse(RefusalKind.MISSING_AUTHORITY, "Bonus Action untyped")
            uses.append(Use(me, BONUS_ACTION))
            activation = ActionCost.BONUS_ACTION
        else:  # Nick: part of the Attack action, once per turn
            printed = [
                f
                for f in facts_of(actor.index, record)
                if isinstance(f, WeaponMasteryFact)
            ]
            nick = _one(actor, "equipment.weapons.nick", MasteryEffectFact)
            if (
                len(printed) != 1
                or printed[0].mastery is not WeaponMastery.NICK
                or nick.cost is not MasteryCost.ATTACK_ACTION
                or not weapon_mastery(actor.index, actor.stored.state, record, None)
            ):
                raise _refuse(
                    RefusalKind.INVALID_SELECTION,
                    f"the wielder can't use Nick with {record}",
                )
            uses.append(Use(me, NICK))
            activation = ActionCost.ACTION
    if WeaponProperty.LOADING in props:
        loading = _one(actor, "equipment.weapons.loading", AmmunitionPerActivationFact)
        if activation not in loading.per or loading.maximum != 1:
            raise _refuse(RefusalKind.MISSING_AUTHORITY, "Loading is untyped")
        uses.append(Use(me, f"{LOADING}:{activation.value}:{record}"))
    return uses


def _section_costs(by: SubjectReference, section: EntrySection) -> list[Use]:
    if section is EntrySection.ACTION:
        return [Use(by, ACTION)]
    if section is EntrySection.BONUS_ACTION:
        return [Use(by, BONUS_ACTION)]
    raise _refuse(
        RefusalKind.UNSUPPORTED_CAPABILITY,
        f"a {section.value} entry's trigger and timing are not executable here",
    )


def costs(
    proposal: RollProposal,
    actor: TurnCharacter,
    subjects: dict[tuple[str, str], TurnSubject],
    document: TurnCoordination,
    *,
    in_multiattack: bool = False,
    opens_multiattack: str | None = None,
) -> list[Use]:
    """The uses *proposal* takes, in order, given the coordination so far."""
    operation = proposal.operation
    if operation == Operation.WEAPON_ATTACK.value:
        return _attack_costs(proposal, actor, document)
    if operation == Operation.STABILIZE.value:
        return [Use(_ref(actor), ACTION)]  # the Help action's first aid
    if operation == Operation.CREATURE_ATTACK.value:
        sel = proposal.creature_attack
        assert sel is not None
        by = SubjectReference(kind="creature", subject_id=sel.attacker.subject_id)
        if sel.follows_up:
            # Part of the hit it follows (validated adjacent to it).
            return []
        if in_multiattack:
            if opens_multiattack is None:
                return []
            return [Use(by, ACTION), Use(by, opens_multiattack)]
        from afterworlds.pipeline.rpg.creature_attacks import _attack_fact

        attacker = subjects.get((sel.attacker.kind, str(sel.attacker.subject_id)))
        if not isinstance(attacker, TurnCreature):
            raise _refuse(RefusalKind.MISSING_STATE, "the attacker was not read")
        return _section_costs(by, _attack_fact(attacker, sel.entry).section)
    if operation == Operation.CREATURE_SAVE_EFFECT.value:
        area = proposal.creature_save_effect
        assert area is not None
        by = SubjectReference(kind="creature", subject_id=area.source.subject_id)
        from afterworlds.pipeline.rpg.creature_effects import _fact

        source = subjects.get((area.source.kind, str(area.source.subject_id)))
        if not isinstance(source, TurnCreature):
            raise _refuse(RefusalKind.MISSING_STATE, "the source was not read")
        return _section_costs(by, _fact(source, area.entry).section)
    return []
