"""Creature usage limits and save effects — CRD Issue 15c.

**Usage.** A printed entry's typed ``creature_entry_usage`` is executed for two
kinds, as a usage counter on the creature's own state:

* Recharge X–6: the entry is spent when used, and at the start of each of the
  creature's turns (``begin_turn``, contract G1) code rolls a d6 for it,
  recharging it on X or more;
* X/Day: the entry is spent once per use, up to X. Regaining uses needs a
  rest, which is not executed here.

Any other usage kind (legendary action uses, form-only, a required entry)
refuses.

**Save effects.** A creature's typed ``creature_save_effect`` forces each
target the GameMaster selects (area membership, OD-15c-1) to save against
the printed DC. The damage is rolled once for all targets. A failure takes it
and the failure effect; on a success it is halved per the typed
``half_damage`` rule when the entry prints *"Half damage"*. Target predicates
that need state not recorded here (creature types, sight, environment,
triggers, exclusions) refuse before any die.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass, field

from afterworlds.ingestion.mechanical.representation import (
    ConditionEffectKind,
    ConditionKind,
    CreatureEntryUsageFact,
    CreatureSaveEffectFact,
    DamageModificationFact,
    DamageType,
    EntrySection,
    SaveSuccess,
    UsageKind,
)
from afterworlds.models.dnd5e_state import (
    GrantSource,
    TurnCoordination,
    UsageCounter,
)
from afterworlds.models.enums import RollPurpose
from afterworlds.models.rpg import (
    CreatureSaveEffectSelection,
    RollProposal,
    SheetEffect,
)
from afterworlds.pipeline.rpg import familiars
from afterworlds.pipeline.rpg.attacks import _SIZES_UP_TO, _size, subject_key
from afterworlds.pipeline.rpg.capability import (
    AdjudicationRefusal,
    Certificate,
    Operation,
    RefusalKind,
    certify,
    governing_fingerprint,
)
from afterworlds.pipeline.rpg.conditions import established
from afterworlds.pipeline.rpg.damage import (
    DamageTaken,
    fixed_part,
    preflight,
    take_damage,
)
from afterworlds.pipeline.rpg.defense import (
    condition_immune,
    facts_of,
    template_digests,
)
from afterworlds.pipeline.rpg.defense import template as template_of
from afterworlds.pipeline.rpg.dice import DiceService, RollRequest, request
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
    "PreparedSaveEffect",
    "RolledSaveEffect",
    "possible_conditions",
    "limited_entries",
    "prepare",
    "remaining",
    "recharge",
    "roll",
    "spend",
    "usable",
]


def _refuse(kind: RefusalKind, detail: str) -> AdjudicationRefusal:
    return AdjudicationRefusal(kind, detail)


# ---------------------------------------------------------------------------
# Usage
# ---------------------------------------------------------------------------


def _usage(creature: TurnCreature, entry: str) -> CreatureEntryUsageFact | None:
    assert creature.index is not None
    template = template_of(creature)
    found = [
        f
        for f in facts_of(creature.index, template)
        if isinstance(f, CreatureEntryUsageFact) and f.entry == entry
    ]
    if len(found) > 1:
        raise _refuse(RefusalKind.MISSING_AUTHORITY, f"{template}/{entry}: two usages")
    return found[0] if found else None


def _counter_id(creature: TurnCreature, entry: str) -> str:
    return f"{creature.stored.state.template_record_key}/{entry}"


def _expended(creature: TurnCreature, entry: str) -> int:
    counters = creature.stored.state.usage_counters
    if counters is None:
        raise _refuse(
            RefusalKind.MISSING_STATE, "the creature records no usage counters"
        )
    found = [c for c in counters if c.counter_id == _counter_id(creature, entry)]
    return found[0].expended if found else 0


def usable(creature: TurnCreature, entry: str) -> CreatureEntryUsageFact | None:
    """Refuse unless *entry*'s printed usage leaves a use; returns the usage
    (``None``: no limit)."""
    usage = _usage(creature, entry)
    if usage is None:
        return None
    template = creature.stored.state.template_record_key
    if usage.kind is UsageKind.RECHARGE:
        if usage.minimum_d6 is None:
            raise _refuse(RefusalKind.MISSING_AUTHORITY, f"{template}/{entry}: no X")
        if _expended(creature, entry):
            raise _refuse(
                RefusalKind.INVALID_SELECTION,
                f"{template}/{entry} has not recharged",
            )
        return usage
    if usage.kind is UsageKind.PER_DAY:
        if usage.uses is None or usage.in_lair is not None or usage.forms:
            raise _refuse(
                RefusalKind.UNSUPPORTED_CAPABILITY,
                f"{template}/{entry}'s daily uses are qualified; not executable here",
            )
        if _expended(creature, entry) >= usage.uses:
            raise _refuse(
                RefusalKind.INVALID_SELECTION,
                f"{template}/{entry}'s {usage.uses} daily uses are spent",
            )
        return usage
    raise _refuse(
        RefusalKind.UNSUPPORTED_CAPABILITY,
        f"{template}/{entry}'s usage ({usage.kind.value}) is not executable here",
    )


def _counter(
    creature: TurnCreature, entry: str, maximum: int, expended: int
) -> SheetEffect:
    counter = UsageCounter(
        counter_id=_counter_id(creature, entry),
        source=GrantSource(record_key=creature.stored.state.template_record_key),
        maximum=maximum,
        expended=expended,
    )
    return SheetEffect(
        target="usage_counter",
        operation="set",
        value_json=counter.model_dump_json(),
        subject_kind="creature",
        subject_id=creature.subject_id,
    )


def spend(
    creature: TurnCreature, entry: str, usage: CreatureEntryUsageFact | None
) -> tuple[SheetEffect, ...]:
    """The effect that spends one use of *entry*, if it is limited."""
    if usage is None:
        return ()
    maximum = 1 if usage.kind is UsageKind.RECHARGE else usage.uses or 0
    return (_counter(creature, entry, maximum, _expended(creature, entry) + 1),)


def recharge(
    creature: TurnCreature, dice: DiceService
) -> tuple[tuple[SheetEffect, ...], list[dict[str, object]]]:
    """At the start of *creature*'s turn: a d6 for each spent Recharge entry,
    recharging it on its printed minimum or more."""
    assert creature.index is not None
    template = template_of(creature)
    effects: list[SheetEffect] = []
    rolls: list[dict[str, object]] = []
    if creature.stored.state.usage_counters is None:
        return (), rolls  # nothing recorded spent, so nothing to recharge
    for usage in facts_of(creature.index, template):
        if not (
            isinstance(usage, CreatureEntryUsageFact)
            and usage.kind is UsageKind.RECHARGE
            and _expended(creature, usage.entry)
        ):
            continue
        if usage.minimum_d6 is None:
            raise _refuse(RefusalKind.MISSING_AUTHORITY, f"{template}: no Recharge X")
        drawn = request(
            dice,
            "1d6",
            RollRequest(
                purpose=RollPurpose.RECHARGE,
                roller=("creature", str(creature.subject_id)),
                label=f"{usage.entry} recharge",
                dc=usage.minimum_d6,
                source_refs=(f"{template}/{usage.entry}",),
            ),
        )
        recharged = drawn.chosen >= usage.minimum_d6
        rolls.append(
            {
                "entry": usage.entry,
                "minimum": usage.minimum_d6,
                "raw_rolls": list(drawn.raw_rolls),
                "recharged": recharged,
            }
        )
        if recharged:
            effects.append(_counter(creature, usage.entry, 1, 0))
    return tuple(effects), rolls


# ---------------------------------------------------------------------------
# Save effects
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PreparedSaveEffect:
    source: TurnCreature
    fact: CreatureSaveEffectFact
    targets: tuple[TurnSubject, ...]
    saves: tuple[PreparedSave, ...]
    usage: CreatureEntryUsageFact | None
    certificate: Certificate
    half: DamageModificationFact | None = None
    #: Each creature subject's certified template digest.
    templates: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class RolledSaveEffect:
    prepared: PreparedSaveEffect
    damage_rolls: tuple[int, ...]
    saves: tuple[RolledSave, ...]
    damage: tuple[DamageTaken | None, ...]
    effects: tuple[SheetEffect, ...]
    results: tuple[dict[str, object], ...] = field(default=())

    def provenance_json(self) -> str:
        p = self.prepared
        return json.dumps(
            {
                "operation": Operation.CREATURE_SAVE_EFFECT.value,
                "source": {"kind": "creature", "subject_id": str(p.source.subject_id)},
                "entry": p.fact.entry,
                "save": p.fact.save.value,
                "dc": p.fact.dc,
                "damage_rolls": list(self.damage_rolls),
                "targets": list(self.results),
                "certificate": p.certificate.as_json(),
                "templates": p.templates,
            },
            sort_keys=True,
        )


def _subject(
    subjects: dict[tuple[str, str], TurnSubject], actor: TurnCharacter, ref: object
) -> TurnSubject | None:
    key = (ref.kind, str(ref.subject_id))  # type: ignore[attr-defined]
    if key == ("character", str(actor.subject_id)):
        return actor
    return subjects.get(key)


def _fact(source: TurnCreature, entry: str) -> CreatureSaveEffectFact:
    assert source.index is not None
    template = template_of(source)
    found = [
        f
        for f in facts_of(source.index, template)
        if isinstance(f, CreatureSaveEffectFact) and f.entry == entry
    ]
    if len(found) != 1:
        raise _refuse(
            RefusalKind.INVALID_SELECTION,
            f"{template} prints no single save effect {entry!r}",
        )
    fact = found[0]
    where = f"{template}/{entry}"
    from afterworlds.pipeline.rpg import roster

    roster.require(template, entry)
    from afterworlds.ingestion.mechanical.representation import (
        ClauseDamageQualificationFact,
        TargetTag,
    )
    from afterworlds.pipeline.rpg.creature_clauses import clauses

    # The one clause read here: underwater not granting Fire Resistance,
    # which nothing grants (underwater Resistance is not executed). Every
    # other clause refuses.
    printed = [
        c
        for c in clauses(source, entry)
        if not (
            isinstance(c, ClauseDamageQualificationFact)
            and not c.underwater_fire_resistance_applies
        )
    ]
    if printed:
        family = printed[0].FAMILY.value  # type: ignore[attr-defined]
        raise _refuse(
            RefusalKind.UNSUPPORTED_CAPABILITY,
            f"{where} prints a {family} clause, which is not executable here",
        )
    if fact.section is EntrySection.LEGENDARY_ACTION:
        raise _refuse(
            RefusalKind.UNSUPPORTED_CAPABILITY, "legendary actions are not executable"
        )
    if fact.dc is None:
        raise _refuse(RefusalKind.UNSUPPORTED_CAPABILITY, f"{where}'s DC is a formula")
    t = fact.targets
    unexecuted = [
        name
        for name, value in (
            # "each enemy": the GameMaster identifies who is an enemy
            # (bystanders). A creature type or species is typed nowhere.
            (
                "creature types",
                any(tag is not TargetTag.ENEMY for tag in t.types) or t.excludes_types,
            ),
            ("sight", t.requires_source_sees_target or t.requires_source_sees_point),
            ("the target's sight", t.requires_target_sees_source),
            ("the environment", t.source_environment),
            ("swallowing", t.swallow_capacity),
            ("a trigger", t.trigger),
            ("an exclusion", t.excludes),
            ("living targets", t.living),
            ("a reuse limit", fact.reuse_limit),
        )
        if value
    ]
    if unexecuted:
        raise _refuse(
            RefusalKind.UNSUPPORTED_CAPABILITY,
            f"{where} turns on {unexecuted[0]}, which is not executable here",
        )
    for term in fact.failure_damage:
        if term.addends or term.damage_type is None or fixed_part(term) is None:
            raise _refuse(
                RefusalKind.UNSUPPORTED_CAPABILITY,
                f"{where}: damage by choice or formula is not executable here",
            )
    rider = fact.failure_effect
    if rider is not None and any(
        v is not None
        for v in (
            rider.speed,
            rider.conditional_damage,
            rider.forced_movement,
            rider.linked,
            rider.rider_save,
            rider.escape_dc,
        )
    ):
        raise _refuse(
            RefusalKind.UNSUPPORTED_CAPABILITY,
            f"{where}'s failure effect is not executable here",
        )
    if (
        rider is not None
        and rider.condition is not None
        and (rider.condition.effect is not ConditionEffectKind.APPLIES)
    ):
        raise _refuse(RefusalKind.UNSUPPORTED_CAPABILITY, f"{where}: effect untyped")
    if rider is not None:
        from afterworlds.pipeline.rpg.creature_attacks import _rider_turn

        _rider_turn(rider.duration)  # a turn-bounded end, or a refusal
    return fact


def enemy_only(fact: CreatureSaveEffectFact) -> bool:
    """Whether the entry affects "each enemy" in its area."""
    from afterworlds.ingestion.mechanical.representation import TargetTag

    return TargetTag.ENEMY in fact.targets.types


def _enemy_cohort(
    sel: CreatureSaveEffectSelection,
    fact: CreatureSaveEffectFact,
    source: TurnCreature,
    keys: Sequence[tuple[str, str]],
    actor: TurnCharacter,
    subjects: dict[tuple[str, str], TurnSubject],
) -> None:
    """An "each enemy" entry's targets are exactly the creatures in its area
    the GameMaster names as the source's enemies, each read under its own
    binding and none the source; any other entry names no enemy cohort."""
    if not enemy_only(fact):
        if sel.enemies_in_area is not None:
            raise _refuse(
                RefusalKind.INVALID_SELECTION,
                f"{sel.entry} affects no enemy cohort; name its targets only",
            )
        return
    if sel.enemies_in_area is None:
        raise _refuse(
            RefusalKind.MISSING_STATE,
            f"{sel.entry} affects each enemy in its area: name the enemies in it "
            "(an empty list if none)",
        )
    enemies = [(r.kind, str(r.subject_id)) for r in sel.enemies_in_area]
    if len(set(enemies)) != len(enemies):
        raise _refuse(RefusalKind.INVALID_SELECTION, "an enemy is named twice")
    for key in enemies:
        if key == ("creature", str(source.subject_id)):
            raise _refuse(
                RefusalKind.INVALID_SELECTION, "a creature is not its own enemy"
            )
        found = (
            actor if key == ("character", str(actor.subject_id)) else subjects.get(key)
        )
        if found is None or found.index is None:
            raise _refuse(RefusalKind.MISSING_STATE, f"{key[0]} {key[1]} was not read")
    if set(keys) != set(enemies):
        raise _refuse(
            RefusalKind.INVALID_SELECTION,
            f"{sel.entry} affects exactly the enemies named in its area",
        )


def _imposed(fact: CreatureSaveEffectFact) -> frozenset[ConditionKind]:
    rider = fact.failure_effect
    if rider is None or rider.condition is None:
        return frozenset()
    return frozenset({rider.condition.condition})


def prepare(
    proposal: RollProposal,
    actor: TurnCharacter,
    subjects: dict[tuple[str, str], TurnSubject],
) -> PreparedSaveEffect:
    """Validate a ``creature_save_effect`` and prepare every target's save,
    or refuse (typed)."""
    sel = proposal.creature_save_effect
    if sel is None:
        raise _refuse(RefusalKind.INVALID_SELECTION, "a save effect names no source")
    source = _subject(subjects, actor, sel.source)
    if not isinstance(source, TurnCreature) or source.index is None:
        raise _refuse(RefusalKind.MISSING_STATE, "the source creature was not read")
    certificate = certify(Operation.CREATURE_SAVE_EFFECT, source.index)
    death = source.stored.state.death_state
    if death is not None and death.dead:
        raise _refuse(RefusalKind.INVALID_SELECTION, "a dead creature cannot act")
    if other_effects(source):
        raise _refuse(
            RefusalKind.UNSUPPORTED_CAPABILITY,
            "an active effect on the source can change this and is not executable",
        )
    fact = _fact(source, sel.entry)
    usage = usable(source, sel.entry)
    keys = [(r.kind, str(r.subject_id)) for r in sel.targets]
    if len(set(keys)) != len(keys):
        raise _refuse(RefusalKind.INVALID_SELECTION, "a target is named twice")
    _enemy_cohort(sel, fact, source, keys, actor, subjects)
    t = fact.targets
    if t.count is not None and len(keys) > t.count:
        raise _refuse(
            RefusalKind.INVALID_SELECTION, f"{sel.entry} affects up to {t.count}"
        )
    targets: list[TurnSubject] = []
    saves: list[PreparedSave] = []
    template = source.stored.state.template_record_key
    familiars.require_present(source)
    for ref in sel.targets:
        target = _subject(subjects, actor, ref)
        if target is not None:
            familiars.require_present(target)
        if target is None or target.index is None:
            raise _refuse(RefusalKind.MISSING_STATE, "a target was not read")
        if subject_key(target) == subject_key(source) and not t.in_source_space:
            raise _refuse(RefusalKind.INVALID_SELECTION, "the source is not a target")
        certify(Operation.CREATURE_SAVE_EFFECT, target.index)
        if target.index.binding != source.index.binding and governing_fingerprint(
            target.index, Operation.CREATURE_SAVE_EFFECT
        ) != governing_fingerprint(source.index, Operation.CREATURE_SAVE_EFFECT):
            raise _refuse(
                RefusalKind.INCOMPATIBLE_CERTIFICATION,
                "the source's and a target's bindings disagree on this procedure",
            )
        for kind in t.related_to_source:
            # "a creature Grappled by the glabrezu": a recorded instance of
            # the condition whose referent is the source.
            recorded = target.stored.state.conditions
            if recorded is None:
                raise _refuse(
                    RefusalKind.MISSING_STATE, "a target records no conditions"
                )
            if not any(
                c.condition.value == kind.value and c.referent == reference(source)
                for c in recorded
            ):
                raise _refuse(
                    RefusalKind.INVALID_SELECTION,
                    f"{sel.entry} targets a creature {kind.value} by its source",
                )
        if t.maximum_size is not None:
            size = _size(target)
            if size is None:
                raise _refuse(RefusalKind.MISSING_STATE, "a target's size is unknown")
            if size not in _SIZES_UP_TO(t.maximum_size):
                raise _refuse(
                    RefusalKind.INVALID_SELECTION,
                    f"a target is larger than {t.maximum_size.value}",
                )
        for term in fact.failure_damage:
            assert term.damage_type is not None
            preflight(target, term.damage_type)
        # The target's immunity to each condition a failure imposes, read
        # before any die (it can refuse for an unvalidated recorded one).
        # "a creature that has the Prone condition" (Trample): read from the
        # target's established conditions. A condition an earlier operation
        # of this turn only might apply (the Gore's Prone) does not establish
        # it: such an independent composition refuses before any die.
        if t.has_conditions:
            held = {e.condition for e in established(target)}
            missing = [c for c in t.has_conditions if c not in held]
            if missing:
                raise _refuse(
                    RefusalKind.INVALID_SELECTION,
                    f"{sel.entry} targets a creature with the {missing[0].value} "
                    "condition",
                )
        rider = fact.failure_effect
        if rider is not None and (
            rider.maximum_size is None
            or _size(target) in _SIZES_UP_TO(rider.maximum_size)
        ):
            for kind in _imposed(fact):
                condition_immune(target, kind)
        assert fact.dc is not None
        saves.append(
            prepare_save(
                target, fact.save, fact.dc, f"{template}/{sel.entry}", _imposed(fact)
            )
        )
        targets.append(target)
    if not targets:
        raise _refuse(RefusalKind.INVALID_SELECTION, "a save effect names no target")
    half = None
    if fact.success in (SaveSuccess.HALF_DAMAGE, SaveSuccess.HALF_DAMAGE_ONLY):
        found = [
            f
            for f in facts_of(source.index, "play.damage_and_healing", "half_damage")
            if isinstance(f, DamageModificationFact)
        ]
        if len(found) != 1:
            raise _refuse(RefusalKind.MISSING_AUTHORITY, "no typed half damage rule")
        half = found[0]
    return PreparedSaveEffect(
        source,
        fact,
        tuple(targets),
        tuple(saves),
        usage,
        certificate,
        half,
        template_digests(source, *targets),
    )


def roll(
    prepared: PreparedSaveEffect,
    dice: DiceService,
    coordination: TurnCoordination | None = None,
) -> RolledSaveEffect:
    """Roll the damage once, each target's save, and apply the outcome."""
    from afterworlds.pipeline.rpg.creature_attacks import _condition_value

    fact = prepared.fact
    rolls: list[int] = []
    parts: list[tuple[int, DamageType]] = []
    for term in fact.failure_damage:
        amount = fixed_part(term) or 0
        if term.dice is not None:
            drawn = request(
                dice,
                f"{term.dice.count}{term.dice.die.value}",
                RollRequest(
                    purpose=RollPurpose.DAMAGE,
                    roller=("creature", str(prepared.source.subject_id)),
                    label=f"{fact.entry} damage",
                    modifiers=(
                        (
                            (
                                "Damage",
                                term.dice.modifier + (fixed_part(term) or 0),
                                fact.entry,
                            ),
                        )
                        if term.dice.modifier or fixed_part(term)
                        else ()
                    ),
                    source_refs=(fact.entry,),
                ),
            )
            rolls.extend(drawn.raw_rolls)
            amount += drawn.chosen + term.dice.modifier
        assert term.damage_type is not None
        parts.append((max(0, amount), term.damage_type))
    effects: list[SheetEffect] = list(
        spend(prepared.source, fact.entry, prepared.usage)
    )
    saves: list[RolledSave] = []
    taken: list[DamageTaken | None] = []
    results: list[dict[str, object]] = []
    for target, save in zip(prepared.targets, prepared.saves, strict=True):
        rolled = roll_save(save, dice)
        saves.append(rolled)
        result: dict[str, object] = {"save": rolled.provenance()}
        own = parts
        if rolled.succeeded:
            if prepared.half is None:
                own = []
            else:
                f = prepared.half.factor
                own = [(a * f.numerator // f.denominator, t) for a, t in parts]
        hit: DamageTaken | None = None
        if own:
            (first, first_type), *rest = own
            hit = take_damage(
                target, first, first_type, critical=False, more=tuple(rest)
            )
            effects.extend(hit.effects)
            result["damage"] = hit.provenance()
            target = with_effects(target, list(hit.effects))
        taken.append(hit)
        rider = fact.failure_effect
        died = target.stored.state.death_state is not None and (
            target.stored.state.death_state.dead
        )
        if not rolled.succeeded and rider is not None and rider.condition and not died:
            kind = rider.condition.condition
            size_ok = rider.maximum_size is None or _size(target) in _SIZES_UP_TO(
                rider.maximum_size
            )
            if condition_immune(target, kind) or not size_ok:
                result["condition"] = "immune" if size_ok else "too_large"
            else:
                effects.append(
                    SheetEffect(
                        target=kind.value,
                        operation="apply_condition",
                        value_json=json.dumps(
                            _condition_value(
                                prepared.source,
                                target,
                                kind,
                                rider.duration,
                                coordination,
                            )
                        ),
                        subject_kind=subject_key(target)[0],  # type: ignore[arg-type]
                        subject_id=target.subject_id,
                    )
                )
                result["condition"] = kind.value
        results.append({"subject": reference(target).model_dump(mode="json"), **result})
    return RolledSaveEffect(
        prepared,
        tuple(rolls),
        tuple(saves),
        tuple(taken),
        tuple(effects),
        tuple(results),
    )


def possible_conditions(
    proposal: RollProposal,
    actor: TurnCharacter,
    subjects: dict[tuple[str, str], TurnSubject],
) -> dict[tuple[str, str], frozenset[ConditionKind]]:
    """Every condition this effect could apply, by target, whatever the dice."""
    from afterworlds.pipeline.rpg.damage import possible_conditions as damage_kinds

    sel = proposal.creature_save_effect
    if sel is None:
        return {}
    source = _subject(subjects, actor, sel.source)
    if not isinstance(source, TurnCreature):
        return {}
    try:
        imposed = _imposed(_fact(source, sel.entry))
    except AdjudicationRefusal:
        imposed = frozenset()
    out: dict[tuple[str, str], frozenset[ConditionKind]] = {}
    for ref in sel.targets:
        target = _subject(subjects, actor, ref)
        if target is not None:
            out[(ref.kind, str(ref.subject_id))] = damage_kinds(target) | imposed
    return out


def remaining(creature: TurnCreature, entry: str) -> int | None:
    """The uses *entry* has left (``None``: no limit), without refusing."""
    usage = _usage(creature, entry)
    if usage is None:
        return None
    spent = _expended(creature, entry)
    if usage.kind is UsageKind.RECHARGE:
        return 0 if spent else 1
    if usage.kind is UsageKind.PER_DAY and usage.uses is not None:
        return max(0, usage.uses - spent)
    return None  # other kinds refuse in usable()


def limited_entries(proposal: RollProposal) -> list[tuple[tuple[str, str], str]]:
    """The creature entries *proposal* would spend a use of."""
    attack = proposal.creature_attack
    if attack is not None:
        return [((attack.attacker.kind, str(attack.attacker.subject_id)), attack.entry)]
    area = proposal.creature_save_effect
    if area is not None:
        return [((area.source.kind, str(area.source.subject_id)), area.entry)]
    return []
