"""Saving throws a subject makes against a typed DC — CRD Issue 15c.

A save is never an operation of its own: it is made against a DC that a
causing effect fixes (a mastery's typed DC, a creature save effect's printed
DC), and that operation certifies :data:`SAVE_PROCEDURE` with its own. Every
number is derived from the saver's own exact binding and state before any die
is rolled; anything that could change the save and is not executed refuses.

* a character: ability modifier from validated scores; the Proficiency Bonus
  when a validated grant gives the save (``play.proficiency/
  saving_throw_proficiency``); Disadvantage on Strength and Dexterity saves in
  armor it lacks training with (``equipment.armor``);
* a creature: its template's printed saving-throw column (the Mummy's Wisdom
  ``+3`` is not derivable from its score, so no other column substitutes);
* both: Advantage/Disadvantage and automatic failure from typed facts of the
  saver's recorded conditions (Paralyzed, Petrified, Stunned and Unconscious
  fail Strength and Dexterity saves; Restrained has Disadvantage on Dexterity
  saves).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from afterworlds.ingestion.mechanical.models import ComponentHandling
from afterworlds.ingestion.mechanical.representation import (
    AbilityScore,
    AdvantageFact,
    AdvantageState,
    ArmorTrainingPenaltyFact,
    AutomaticOutcome,
    AutomaticOutcomeFact,
    ConditionKind,
    CreatureAbilityScoreFact,
    CreatureRollModifierFact,
    CreatureSaveOverrideFact,
    ProficiencyApplicationFact,
    ProficiencyKind,
    RecordKind,
    RollActor,
    RollContext,
)
from afterworlds.pipeline.rpg.capability import AdjudicationRefusal, RefusalKind
from afterworlds.pipeline.rpg.conditions import effective
from afterworlds.pipeline.rpg.dice import DiceService
from afterworlds.pipeline.rpg.grants import ability_score, save_proficiency
from afterworlds.services.dnd5e_state.authority import AuthorityIndex
from afterworlds.services.dnd5e_state.turn import (
    TurnCharacter,
    TurnCreature,
    TurnSubject,
)

__all__ = [
    "SAVE_CONTRIBUTORS",
    "SAVE_CONTRIBUTING_TRAITS",
    "SAVE_PROCEDURE",
    "PreparedSave",
    "RolledSave",
    "prepare",
    "roll",
]

#: The save procedure (prose-bound universal components, certified with the
#: operation that causes the save) and the typed rules it reads.
SAVE_PROCEDURE: tuple[tuple[str, str], ...] = (
    ("play.d20_tests", "saving_throws"),
    ("play.d20_tests", "save_ability_modifier"),
    ("play.d20_tests", "save_proficiency"),
    ("play.d20_tests", "save_dc"),
    ("play.proficiency", "saving_throw_proficiency"),
    ("glossary.saving_throw", "saving_throw"),
)

#: Class features and feats that change their holder's own saving throws or
#: their outcome, read entry by entry from a phrase scan of the pinned source
#: (``classes.md`` and ``feats.md``, "saving throw" and "D20 Test" language;
#: ``saves/save-contributor-scan.md`` in the 15c review notes). Reactive
#: choices after a failed save (Indomitable, Disciplined Survivor's reroll,
#: Dark One's Own Luck) belong to the saver and are refused, not skipped.
#:
#: Each is mapped to when it is relevant, as its entry states: the save's
#: abilities, or the conditions the causing effect imposes (Fey Ancestry is
#: *"saving throws you make to avoid or end the Charmed condition"*). ``None``
#: means any save. A contributor is refused only when relevant. Death-save and
#: zero-HP features (Survivor, Relentless Rage) are their own operations'.
_Relevance = tuple[frozenset[AbilityScore] | None, frozenset[ConditionKind] | None]
_ANY: _Relevance = (None, None)
_DEX: _Relevance = (frozenset({AbilityScore.DEXTERITY}), None)


def _avoiding(condition: ConditionKind) -> _Relevance:
    return (None, frozenset({condition}))


SAVE_CONTRIBUTORS: dict[str, _Relevance] = {
    "classes.barbarian.danger_sense": _DEX,
    "classes.fighter.indomitable": _ANY,
    "classes.monk.evasion": _DEX,
    "classes.monk.disciplined_survivor": _ANY,
    "classes.paladin.aura_of_protection": _ANY,
    "classes.paladin.aura_of_courage": _avoiding(ConditionKind.FRIGHTENED),
    "classes.paladin.oath_of_devotion.aura_of_devotion": _avoiding(
        ConditionKind.CHARMED
    ),
    "classes.paladin.oath_of_devotion.holy_nimbus": _ANY,
    "classes.rogue.evasion": _DEX,
    "classes.warlock.fiend_patron.dark_ones_own_luck": _ANY,
    "feats.boon_of_fate": _ANY,
}
SAVE_CONTRIBUTING_TRAITS: dict[tuple[str, str], _Relevance] = {
    ("character_origins.dwarf", "dwarven_resilience"): _avoiding(
        ConditionKind.POISONED
    ),
    ("character_origins.elf", "fey_ancestry"): _avoiding(ConditionKind.CHARMED),
    ("character_origins.gnome", "gnomish_cunning"): (
        frozenset(
            {AbilityScore.INTELLIGENCE, AbilityScore.WISDOM, AbilityScore.CHARISMA}
        ),
        None,
    ),
    ("character_origins.halfling", "brave"): _avoiding(ConditionKind.FRIGHTENED),
    ("character_origins.halfling", "luck"): _ANY,
}


def _relevant(
    relevance: _Relevance, ability: AbilityScore, imposes: frozenset[ConditionKind]
) -> bool:
    abilities, conditions = relevance
    if abilities is not None and ability not in abilities:
        return False
    return conditions is None or bool(conditions & imposes)


_PB = ("play.proficiency.proficiency_bonus", "proficiency_bonus_bands")
_SAVE_CONTEXTS = (RollContext.SAVING_THROW, RollContext.D20_TEST)


def _refuse(kind: RefusalKind, detail: str) -> AdjudicationRefusal:
    return AdjudicationRefusal(kind, detail)


@dataclass(frozen=True)
class PreparedSave:
    """A fully derived save: every input fixed, no die rolled yet."""

    subject_kind: str
    subject_id: str
    ability: AbilityScore
    dc: int
    dc_source: str
    modifier: int
    advantage_sources: tuple[str, ...]
    disadvantage_sources: tuple[str, ...]
    #: Typed automatic failures; when present, no die is rolled.
    automatic_failure: tuple[str, ...]
    breakdown: dict[str, int] = field(default_factory=dict)

    @property
    def expression(self) -> str:
        adv, dis = bool(self.advantage_sources), bool(self.disadvantage_sources)
        if adv and not dis:
            return "2d20kh1"
        if dis and not adv:
            return "2d20kl1"
        return "1d20"


@dataclass(frozen=True)
class RolledSave:
    prepared: PreparedSave
    raw_rolls: tuple[int, ...]
    chosen: int | None

    @property
    def total(self) -> int | None:
        return None if self.chosen is None else self.chosen + self.prepared.modifier

    @property
    def succeeded(self) -> bool:
        total = self.total
        return total is not None and total >= self.prepared.dc

    def provenance(self) -> dict[str, object]:
        p = self.prepared
        return {
            "subject_kind": p.subject_kind,
            "subject_id": p.subject_id,
            "ability": p.ability.value,
            "dc": p.dc,
            "dc_source": p.dc_source,
            "modifier": p.modifier,
            "breakdown": p.breakdown,
            "raw_rolls": list(self.raw_rolls),
            "total": self.total,
            "outcome": "success" if self.succeeded else "failure",
            "advantage_sources": list(p.advantage_sources),
            "disadvantage_sources": list(p.disadvantage_sources),
            "automatic_failure": list(p.automatic_failure),
        }

    def provenance_json(self) -> str:
        return json.dumps(self.provenance(), sort_keys=True)


def _conditions(
    subject: TurnSubject, index: AuthorityIndex, ability: AbilityScore
) -> tuple[list[str], list[str], list[str]]:
    advantage: list[str] = []
    disadvantage: list[str] = []
    failure: list[str] = []
    # Recorded and implied conditions (Unconscious gives Incapacitated).
    for instance in effective(subject, index):
        if instance.condition is ConditionKind.EXHAUSTION:
            raise _refuse(
                RefusalKind.UNSUPPORTED_CAPABILITY,
                "Exhaustion's D20 Test reduction is not executable here",
            )
        record = index.record(f"glossary.{instance.condition.value}")
        if record is None:
            raise _refuse(
                RefusalKind.MISSING_AUTHORITY,
                f"condition {instance.condition.value} has no governing record",
            )
        for component in record.components:
            for ef in component.facts:
                fact = ef.fact
                if not isinstance(fact, (AdvantageFact, AutomaticOutcomeFact)):
                    continue
                spec = fact.roll
                if (
                    spec.actor is not RollActor.SUBJECT
                    or spec.context not in _SAVE_CONTEXTS
                    or spec.ability not in (None, ability)
                ):
                    continue
                where = f"{record.semantic_key}/{component.semantic_key}"
                if (
                    component.handling is not ComponentHandling.STRUCTURED
                    or component.applies_when is not None
                    or ef.qualifier is not None
                ):
                    raise _refuse(
                        RefusalKind.UNSUPPORTED_CAPABILITY,
                        f"{where} can affect this save under circumstances that "
                        "need judgement and is not executable here",
                    )
                if isinstance(fact, AutomaticOutcomeFact):
                    if fact.outcome is not AutomaticOutcome.FAILURE:
                        raise _refuse(
                            RefusalKind.UNSUPPORTED_CAPABILITY,
                            f"{where}: automatic {fact.outcome.value}",
                        )
                    failure.append(where)
                elif fact.state is AdvantageState.ADVANTAGE:
                    advantage.append(where)
                else:
                    disadvantage.append(where)
    return advantage, disadvantage, failure


def _held_keys(character: TurnCharacter, index: AuthorityIndex) -> set[str]:
    state = character.stored.state
    held = {f.feat_record_key for f in state.feats or ()}
    for cl in state.classes or ():
        held |= {
            e.entitlement_key
            for e in index.progression(cl.class_record_key)
            if e.level <= cl.level
        }
        if cl.subclass_record_key:
            prefix = cl.subclass_record_key + "."
            held |= {k for k in SAVE_CONTRIBUTORS if k.startswith(prefix)}
    return held


def _character(
    character: TurnCharacter,
    index: AuthorityIndex,
    ability: AbilityScore,
    imposes: frozenset[ConditionKind],
) -> tuple[int, dict[str, int], list[str]]:
    from afterworlds.pipeline.rpg.checks import proficiency_bonus
    from afterworlds.pipeline.rpg.defense import facts_of, untrained_armor

    state = character.stored.state
    missing = [
        name
        for name, value in (
            ("ability_scores", state.ability_scores),
            ("ability_adjustments", state.ability_adjustments),
            ("classes", state.classes),
            ("saving_throw_proficiencies", state.saving_throw_proficiencies),
            ("active_effects", state.active_effects),
            ("feats", state.feats),
            ("species", state.species),
        )
        if value is None
    ]
    if missing:
        raise _refuse(
            RefusalKind.MISSING_STATE, f"the saver records no {', '.join(missing)}"
        )

    def unsupported(what: str) -> AdjudicationRefusal:
        return _refuse(
            RefusalKind.UNSUPPORTED_CAPABILITY,
            f"{what} can change this save and is not executable here",
        )

    if state.active_effects:
        raise unsupported(f"active effect {state.active_effects[0].source.record_key}")
    found = sorted(
        k
        for k in _held_keys(character, index) & SAVE_CONTRIBUTORS.keys()
        if _relevant(SAVE_CONTRIBUTORS[k], ability, imposes)
    )
    if found:
        raise unsupported(f"feature or feat {found[0]}")
    assert state.species is not None
    for (record, trait), relevance in sorted(SAVE_CONTRIBUTING_TRAITS.items()):
        if record == state.species.record_key and _relevant(
            relevance, ability, imposes
        ):
            raise unsupported(f"species trait {record}/{trait}")
    if any(h.kind == "contagion" for h in state.hazards or ()):
        raise unsupported("a magical contagion")
    for item in character.items:
        if index.kind(item.record_key) is RecordKind.MAGIC_ITEM and (
            item.equipped or item.attuned_subject_id
        ):
            raise unsupported(f"magic item {item.record_key}")

    score, _ = ability_score(index, state, ability)
    modifier = (score - 10) // 2
    breakdown = {f"{ability.value}_modifier": modifier}
    if save_proficiency(index, state, ability):
        component = index.component("play.proficiency", "saving_throw_proficiency")
        if not any(
            isinstance(f.fact, ProficiencyApplicationFact)
            and f.fact.proficiency is ProficiencyKind.SAVING_THROW
            for f in (component.facts if component else ())
        ):
            raise _refuse(
                RefusalKind.MISSING_AUTHORITY,
                "saving-throw proficiency's application is absent",
            )
        level = sum(c.level for c in state.classes or ())
        if level < 1:
            raise _refuse(RefusalKind.MISSING_STATE, "the saver records no level")
        bonus = proficiency_bonus(index, level)
        modifier += bonus
        breakdown["proficiency_bonus"] = bonus
    disadvantage: list[str] = []
    if untrained_armor(character, index):
        for f in facts_of(index, "equipment.armor", "light_medium_or_heavy_armor"):
            if isinstance(f, ArmorTrainingPenaltyFact) and ability in f.abilities:
                if f.d20_tests is not AdvantageState.DISADVANTAGE:
                    raise _refuse(
                        RefusalKind.MISSING_AUTHORITY,
                        "the armor training penalty is not typed as Disadvantage",
                    )
                disadvantage.append("equipment.armor/light_medium_or_heavy_armor")
    return modifier, breakdown, disadvantage


def _creature(
    creature: TurnCreature, index: AuthorityIndex, ability: AbilityScore
) -> tuple[int, dict[str, int]]:
    from afterworlds.pipeline.rpg.defense import facts_of

    state = creature.stored.state
    template = state.template_record_key
    if index.record(template) is None:
        raise _refuse(RefusalKind.MISSING_AUTHORITY, f"template {template} is absent")
    if state.active_effects:
        raise _refuse(
            RefusalKind.UNSUPPORTED_CAPABILITY,
            f"active effect {state.active_effects[0].source.record_key} can change "
            "this save and is not executable here",
        )
    facts = facts_of(index, template)
    for fact in facts:
        if isinstance(fact, CreatureSaveOverrideFact):
            raise _refuse(
                RefusalKind.UNSUPPORTED_CAPABILITY,
                f"{template}/{fact.entry}: a save override is a choice not "
                "executable here",
            )
        if isinstance(fact, CreatureRollModifierFact) and any(
            e.roll.context in _SAVE_CONTEXTS for e in fact.effects
        ):
            raise _refuse(
                RefusalKind.UNSUPPORTED_CAPABILITY,
                f"{template}/{fact.entry} can change this save and is not "
                "executable here",
            )
    rows = [
        f
        for f in facts
        if isinstance(f, CreatureAbilityScoreFact) and f.ability is ability
    ]
    if len(rows) != 1 or rows[0].save_modifier is None:
        raise _refuse(
            RefusalKind.MISSING_AUTHORITY,
            f"{template} prints no single {ability.value} saving-throw column",
        )
    return rows[0].save_modifier, {f"{ability.value}_save": rows[0].save_modifier}


def prepare(
    subject: TurnSubject,
    ability: AbilityScore,
    dc: int,
    dc_source: str,
    imposes: frozenset[ConditionKind] = frozenset(),
) -> PreparedSave:
    """Derive *subject*'s save of *ability* against *dc*, or refuse (typed).

    *imposes* is every condition the causing effect applies on a failure, so
    a contributor limited to avoiding a condition is refused when relevant."""
    index = subject.index
    if index is None:
        raise _refuse(
            RefusalKind.MISSING_AUTHORITY, "the saver's authority is not resolved"
        )
    disadvantage: list[str] = []
    if isinstance(subject, TurnCreature):
        modifier, breakdown = _creature(subject, index, ability)
        kind = "creature"
    else:
        modifier, breakdown, disadvantage = _character(subject, index, ability, imposes)
        kind = "character"
    advantage, dis2, failure = _conditions(subject, index, ability)
    return PreparedSave(
        subject_kind=kind,
        subject_id=str(subject.subject_id),
        ability=ability,
        dc=dc,
        dc_source=dc_source,
        modifier=modifier,
        advantage_sources=tuple(advantage),
        disadvantage_sources=tuple(disadvantage + dis2),
        automatic_failure=tuple(failure),
        breakdown=breakdown,
    )


def roll(prepared: PreparedSave, dice: DiceService) -> RolledSave:
    if prepared.automatic_failure:
        return RolledSave(prepared, (), None)
    result = dice.roll(prepared.expression)
    return RolledSave(prepared, result.raw_rolls, result.chosen)
