"""Armor Class and damage responses of an attack's target — CRD Issue 15c.

Every number comes from the target's own exact binding and recorded state:

* a character's AC: the worn armor's typed ``armor_class_formula`` (or the
  typed ``base_armor_class`` with no armor), the validated Dexterity modifier
  within the formula's cap, and a held Shield's typed ``shield_bonus`` when the
  character has validated Shield training (``shield_training_requirement``:
  an untrained Shield gives no AC benefit);
* a creature's AC: its template's typed ``creature_defense``;
* damage responses: a creature template's typed, unconditional
  ``damage_response`` facts.

Anything that could change these and is not executed here refuses rather than
being ignored:
- a recorded alternative base AC (Unarmored Defense, Draconic Resilience,
  Mage Armor);
- an active effect or an equipped or attuned magic item;
- AC-contributing features and feats;
- a parameterized or conditional creature defense;
- a character's recorded damage response whose grant entitlement is not
  validated here.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from afterworlds.ingestion.mechanical.representation import (
    AbilityScore,
    ArmorClassFormulaFact,
    BaseArmorClassFact,
    ConditionEffectFact,
    ConditionEffectKind,
    ConditionKind,
    CreatureConditionalDefenseFact,
    CreatureDefenseFact,
    CreatureDefenseParameterizedFact,
    DamageResponseFact,
    DamageResponseKind,
    DamageScope,
    DamageType,
    RecordKind,
    ShieldBonusFact,
)
from afterworlds.models.dnd5e_state import Dnd5eCharacterState
from afterworlds.models.dnd5e_vocabulary import ArmorCategory
from afterworlds.pipeline.rpg.capability import (
    AdjudicationRefusal,
    RefusalKind,
    certify_template,
)
from afterworlds.pipeline.rpg.grants import ability_score, armor_training
from afterworlds.pipeline.rpg.mastery import other_effects
from afterworlds.services.dnd5e_state.authority import AuthorityIndex
from afterworlds.services.dnd5e_state.turn import (
    TurnCharacter,
    TurnCreature,
    TurnSubject,
)

__all__ = [
    "ARMOR_CLASS_CONTRIBUTORS",
    "ArmorClass",
    "armor_class",
    "damage_responses",
    "facts_of",
    "untrained_armor",
]

#: Features and feats that change their holder's Armor Class or the attacks
#: against them, read entry by entry from the pinned source (CRD Issue 15c
#: attack-contributor scan): Defense (+1 AC in armor), Unarmored Defense and
#: Draconic Resilience (alternative bases), Uncanny Dodge (halve an attack's
#: damage), Elusive (no Advantage against), Deflect Attacks (reduce damage),
#: Defensive Tactics. A target holding one refuses until it is executed.
ARMOR_CLASS_CONTRIBUTORS: frozenset[str] = frozenset(
    {
        "feats.defense",
        "classes.barbarian.unarmored_defense",
        "classes.monk.unarmored_defense",
        "classes.sorcerer.draconic_sorcery.draconic_resilience",
        "classes.rogue.uncanny_dodge",
        "classes.rogue.elusive",
        "classes.monk.deflect_attacks",
        "classes.ranger.hunter.defensive_tactics",
    }
)

_BASE_AC = ("play.d20_tests", "base_ac")


def facts_of(
    index: AuthorityIndex, record: str, component: str | None = None
) -> list[object]:
    """The typed facts of a record (all components) or of one component."""
    found = index.record(record)
    if found is None:
        return []
    return [
        f.fact
        for c in found.components
        if component is None or c.semantic_key == component
        for f in c.facts
    ]


def _refuse(kind: RefusalKind, detail: str) -> AdjudicationRefusal:
    return AdjudicationRefusal(kind, detail)


@dataclass(frozen=True)
class ArmorClass:
    value: int
    source: str
    breakdown: dict[str, int] = field(default_factory=dict)


def _held_features(character: TurnCharacter, index: AuthorityIndex) -> set[str]:
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
            held |= {k for k in index.records if k.startswith(prefix)}
    return held


def untrained_armor(character: TurnCharacter, index: AuthorityIndex) -> str | None:
    """The worn armor the character lacks training with, if any."""
    state = character.stored.state
    for record, formula in _worn_armor(character, index):
        if not armor_training(index, state, ArmorCategory(formula.category.value)):
            return record
    return None


def _worn_armor(
    character: TurnCharacter, index: AuthorityIndex
) -> list[tuple[str, ArmorClassFormulaFact]]:
    worn = []
    for item in character.items:
        if not item.equipped or not item.record_key.startswith("equipment.armor."):
            continue
        formulas = [
            f
            for f in facts_of(index, item.record_key)
            if isinstance(f, ArmorClassFormulaFact)
        ]
        if formulas:
            worn.append((item.record_key, formulas[0]))
    return worn


def _character_ac(character: TurnCharacter, index: AuthorityIndex) -> ArmorClass:
    state: Dnd5eCharacterState = character.stored.state
    if state.base_armor_class is not None and state.base_armor_class.source is not None:
        raise _refuse(
            RefusalKind.UNSUPPORTED_CAPABILITY,
            "the target's recorded base AC "
            f"({state.base_armor_class.source.record_key}) is not executable here",
        )
    unexecuted = other_effects(character)
    if unexecuted:
        raise _refuse(
            RefusalKind.UNSUPPORTED_CAPABILITY,
            f"the target's active effect {unexecuted[0].source.record_key} "
            "can change its Armor Class and is not executable here",
        )
    for item in character.items:
        if index.kind(item.record_key) is RecordKind.MAGIC_ITEM and (
            item.equipped or item.attuned_subject_id
        ):
            raise _refuse(
                RefusalKind.UNSUPPORTED_CAPABILITY,
                f"the target's magic item {item.record_key} is not executable here",
            )
    found = sorted(_held_features(character, index) & ARMOR_CLASS_CONTRIBUTORS)
    if found:
        raise _refuse(
            RefusalKind.UNSUPPORTED_CAPABILITY,
            f"the target's {found[0]} can change attacks against it and is not "
            "executable here",
        )
    dex = (ability_score(index, state, AbilityScore.DEXTERITY)[0] - 10) // 2
    worn = _worn_armor(character, index)
    if len(worn) > 1:
        raise _refuse(
            RefusalKind.INVALID_SELECTION, "the target wears more than one armor"
        )
    if worn:
        record, formula = worn[0]
        add = dex if formula.adds_dexterity_modifier else 0
        if formula.dexterity_maximum is not None:
            add = min(add, formula.dexterity_maximum)
        breakdown, source = {"armor_base": formula.base}, record
    else:
        bases = [
            f for f in facts_of(index, *_BASE_AC) if isinstance(f, BaseArmorClassFact)
        ]
        if len(bases) != 1:
            raise _refuse(RefusalKind.MISSING_AUTHORITY, "no typed base Armor Class")
        add = dex if bases[0].adds_dexterity_modifier else 0
        breakdown, source = (
            {"base": bases[0].base},
            "/".join(_BASE_AC),
        )
    if add:
        breakdown["dexterity_modifier"] = add
    shields = [
        i
        for i in character.items
        if i.equipped and i.record_key == "equipment.armor.shield"
    ]
    if len(shields) > 1:
        raise _refuse(
            RefusalKind.INVALID_SELECTION, "the target holds more than one Shield"
        )
    if shields and armor_training(index, state, ArmorCategory.SHIELD):
        bonus = [
            f
            for f in facts_of(index, "equipment.armor.shield")
            if isinstance(f, ShieldBonusFact)
        ]
        if len(bonus) != 1:
            raise _refuse(RefusalKind.MISSING_AUTHORITY, "no typed Shield bonus")
        breakdown["shield"] = bonus[0].bonus
    return ArmorClass(sum(breakdown.values()), source, breakdown)


def template(creature: TurnCreature) -> str:
    """*creature*'s template, certified under its own binding: every read of
    creature template authority goes through here (CRD Issue 15c)."""
    index = creature.index
    if index is None:
        raise _refuse(RefusalKind.MISSING_AUTHORITY, "the creature's authority")
    key = creature.stored.state.template_record_key
    certify_template(index, key)
    return key


def _template(creature: TurnCreature, index: AuthorityIndex) -> str:
    del index
    return template(creature)


def _creature_ac(creature: TurnCreature, index: AuthorityIndex) -> ArmorClass:
    template = _template(creature, index)
    if other_effects(creature):
        raise _refuse(
            RefusalKind.UNSUPPORTED_CAPABILITY,
            "the creature's active effect can change its Armor Class and is not "
            "executable here",
        )
    facts = facts_of(index, template)
    if any(isinstance(f, CreatureDefenseParameterizedFact) for f in facts):
        raise _refuse(
            RefusalKind.UNSUPPORTED_CAPABILITY,
            f"{template}'s Armor Class is parameterized by its summoning and is not "
            "executable here",
        )
    defenses = [f for f in facts if isinstance(f, CreatureDefenseFact)]
    if len(defenses) != 1:
        raise _refuse(RefusalKind.MISSING_AUTHORITY, f"{template} states no single AC")
    return ArmorClass(
        defenses[0].armor_class, template, {"armor_class": defenses[0].armor_class}
    )


def armor_class(target: TurnSubject) -> ArmorClass:
    """The target's Armor Class from its own exact binding, or a refusal."""
    index = target.index
    if index is None:
        raise _refuse(
            RefusalKind.MISSING_AUTHORITY, "the target's authority is not resolved"
        )
    if isinstance(target, TurnCreature):
        return _creature_ac(target, index)
    return _character_ac(target, index)


def damage_responses(
    target: TurnSubject, damage_type: DamageType
) -> tuple[DamageResponseKind, ...]:
    """The target's responses to *damage_type*, each unconditional; a
    conditional or unvalidated response refuses."""
    index = target.index
    assert index is not None
    if isinstance(target, TurnCreature):
        template = _template(target, index)
        found = []
        for f in facts_of(index, template):
            if isinstance(f, CreatureConditionalDefenseFact) and (
                f.damage_type in (None, damage_type)
            ):
                raise _refuse(
                    RefusalKind.UNSUPPORTED_CAPABILITY,
                    f"{template} has a conditional defense ({f.kind.value}) that can "
                    "apply to this damage and is not executable here",
                )
            if isinstance(f, DamageResponseFact):
                applies = (
                    f.scope is DamageScope.ALL and damage_type not in f.except_types
                ) or (f.scope is DamageScope.SPECIFIC and f.damage_type is damage_type)
                if not applies:
                    continue
                if f.scope is DamageScope.SPECIFIC and f.except_types:
                    raise _refuse(
                        RefusalKind.UNSUPPORTED_CAPABILITY,
                        f"{template}'s qualified {f.response.value} is not "
                        "executable here",
                    )
                found.append(f.response)
        return tuple(found)
    state = target.stored.state
    if any(r.damage_type is damage_type for r in state.damage_responses or ()):
        raise _refuse(
            RefusalKind.UNSUPPORTED_CAPABILITY,
            f"the target's recorded {damage_type.value} damage response is not "
            "validated against its source here",
        )
    return ()


def condition_immune(target: TurnSubject, condition: ConditionKind) -> bool:
    """Whether *target* is immune to *condition*: a creature template's typed,
    unqualified immunity, or one its conditions state (Petrified: Poisoned).
    A character's recorded immunity is not validated against its source here,
    so it refuses."""
    from afterworlds.pipeline.rpg.conditions import effective

    index = target.index
    assert index is not None

    def immune(facts: list[object]) -> bool:
        return any(
            isinstance(f, ConditionEffectFact)
            and f.effect is ConditionEffectKind.IMMUNITY
            and f.condition is condition
            for f in facts
        )

    for eff in effective(target, index):
        if immune(facts_of(index, f"glossary.{eff.condition.value}")):
            return True
    if isinstance(target, TurnCreature):
        return immune(facts_of(index, _template(target, index)))
    if condition in (target.stored.state.condition_immunities or ()):
        raise _refuse(
            RefusalKind.UNSUPPORTED_CAPABILITY,
            f"the target's recorded {condition.value} immunity is not validated "
            "against its source here",
        )
    return False


def template_digests(*subjects: TurnSubject) -> dict[str, str]:
    """The certified template digest of every creature among *subjects*,
    keyed ``creature:<id>``, for the operation's certificate provenance."""
    out: dict[str, str] = {}
    for subject in subjects:
        if isinstance(subject, TurnCreature):
            assert subject.index is not None
            out[f"creature:{subject.subject_id}"] = certify_template(
                subject.index, template(subject)
            )
    return out
