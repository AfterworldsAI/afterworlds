"""Typed D&D 5e character and continuing-creature state — CRD Issue 2b.

One authoritative, schema-versioned document per character or creature. It
stores **primitive inputs and choices with exact identities and provenance**;
it computes nothing. Modifiers, totals, AC, DCs, legality and eligibility are
CRD Issue 15c derivations, and recorded state never claims them.

Missing versus empty
--------------------
Every state family is optional and defaults to ``None``. ``None`` means *the
family has not been recorded*; an explicit empty tuple, zero or ``False`` means
*recorded as empty*. Nothing here supplies an empty default, so a fresh read
cannot manufacture state. Whether a missing family is a failure is decided by
:mod:`afterworlds.services.dnd5e_state.validation` against the bound authority.

Identities
----------
Rules identities are exact accepted semantic keys of the bound Rules Package
(``classes.wizard``, ``spells.fireball``, ``equipment.weapons.dart``) or, where
the source states the thing as an accepted closed vocabulary, that vocabulary
(:class:`~afterworlds.ingestion.mechanical.representation.Skill`, ...). The few
vocabularies the accepted schema lacks are in :mod:`.dnd5e_vocabulary`, each
source-cited and checked against the pinned source by test.

ADR-0003
--------
Maximum hit points and spell-slot totals are stored, authoritative values.
``current`` has no floor; ``current <= maximum`` is retained as the D&D
5e-scoped data-integrity rule. ``expended <= total`` is structural.
"""

from __future__ import annotations

from typing import Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from afterworlds.ingestion.mechanical.representation import (
    AbilityScore,
    ConditionKind,
    CreatureSize,
    Currency,
    DamageResponseKind,
    DamageType,
    DieSize,
    MovementMode,
    Skill,
    WeaponCategory,
)
from afterworlds.models.dnd5e_vocabulary import (
    Alignment,
    ArmorCategory,
    CreatureType,
    Language,
)
from afterworlds.models.enums import ConditionVisibility

__all__ = [
    "STATE_SCHEMA_VERSION",
    "AbilityAdjustment",
    "Dnd5eAbilityScores",
    "ActiveEffect",
    "ArmorTrainingGrant",
    "ChoiceRecord",
    "ClassLevel",
    "ConditionInstance",
    "CreatureState",
    "DamageResponseGrant",
    "DeathState",
    "Dnd5eCharacterState",
    "FeatSelection",
    "GrantSource",
    "HitPointDicePool",
    "HitPoints",
    "LanguageGrant",
    "OriginSelection",
    "RestAnchors",
    "SavingThrowGrant",
    "SenseGrant",
    "SkillGrant",
    "SlotLevel",
    "SpeedGrant",
    "SpellAccess",
    "SpellSlotPool",
    "SummonOrigin",
    "ToolGrant",
    "UsageCounter",
    "WeaponProficiencyGrant",
]

#: The state document's own contract version. Independent of the Rules
#: Package schema; a document declaring another version is refused on read.
STATE_SCHEMA_VERSION: Literal[1] = 1

_STRICT = ConfigDict(extra="forbid", frozen=True)


class _Model(BaseModel):
    model_config = _STRICT


# ---------------------------------------------------------------------------
# Provenance and choices
# ---------------------------------------------------------------------------


class GrantSource(_Model):
    """Where a recorded grant, choice or effect came from.

    ``record_key`` is an accepted semantic key; ``component_key`` narrows it to
    the component that states the grant when the grant has one. ``choice_id``
    links a grant to the :class:`ChoiceRecord` that produced it, so the chain
    *choice -> grant* stays explicit.
    """

    record_key: str = Field(min_length=1)
    component_key: str | None = Field(default=None, min_length=1)
    choice_id: str | None = Field(default=None, min_length=1)


class ChoiceRecord(_Model):
    """One recorded choice and the exact source schema it was made under.

    ``schema_id`` is the content-derived identity of the source component in
    the bound effective authority when the choice was recorded. A target
    authority whose component differs no longer offers the same choice, and
    adoption refuses rather than applying the obsolete schema.

    ``selected`` holds the chosen identities: accepted record keys, component
    option keys, or accepted vocabulary values, as the source states them.
    """

    choice_id: str = Field(min_length=1)
    source: GrantSource
    schema_id: str = Field(min_length=1)
    selected: tuple[str, ...]


# ---------------------------------------------------------------------------
# F1-F4: alignment, origin, classes, abilities
# ---------------------------------------------------------------------------


class OriginSelection(_Model):
    """A species or background: its accepted record and lineage-type choices."""

    record_key: str = Field(min_length=1)
    choice_ids: tuple[str, ...] = ()


class ClassLevel(_Model):
    """Levels in one class, and its subclass once chosen.

    ``hit_die`` is recorded rather than derived: the class's die is printed in
    prose, so code does not invent it.
    """

    class_record_key: str = Field(min_length=1)
    level: int = Field(ge=1, le=20)
    subclass_record_key: str | None = Field(default=None, min_length=1)
    hit_die: DieSize


class Dnd5eAbilityScores(_Model):
    """Base ability scores before any sourced adjustment.

    The 1-30 range is D&D 5e-scoped (ADR-0003 Decision 1), not universal.
    """

    strength: int = Field(ge=1, le=30)
    dexterity: int = Field(ge=1, le=30)
    constitution: int = Field(ge=1, le=30)
    intelligence: int = Field(ge=1, le=30)
    wisdom: int = Field(ge=1, le=30)
    charisma: int = Field(ge=1, le=30)


class AbilityAdjustment(_Model):
    """One sourced change to an ability score, kept apart from the base.

    ``maximum`` is the cap the source states for this adjustment, if any;
    totals and caps are applied by 15c, never folded into the base here.
    """

    ability: AbilityScore
    amount: int
    maximum: int | None = Field(default=None, ge=1, le=30)
    source: GrantSource


# ---------------------------------------------------------------------------
# F5-F8: proficiencies, feats, feature choices, traits
# ---------------------------------------------------------------------------


class SkillGrant(_Model):
    skill: Skill
    expertise: bool
    source: GrantSource


class SavingThrowGrant(_Model):
    ability: AbilityScore
    source: GrantSource


class WeaponProficiencyGrant(_Model):
    """Proficiency with a weapon category, or with one accepted weapon."""

    category: WeaponCategory | None = None
    weapon_record_key: str | None = Field(default=None, min_length=1)
    source: GrantSource

    @model_validator(mode="after")
    def exactly_one_target(self) -> Self:
        if (self.category is None) == (self.weapon_record_key is None):
            raise ValueError("a weapon proficiency names a category or a weapon")
        return self


class ArmorTrainingGrant(_Model):
    category: ArmorCategory
    source: GrantSource


class ToolGrant(_Model):
    """Proficiency with a tool: an accepted record, or (record, component)."""

    record_key: str = Field(min_length=1)
    component_key: str | None = Field(default=None, min_length=1)
    expertise: bool
    source: GrantSource


class LanguageGrant(_Model):
    language: Language
    source: GrantSource


class FeatSelection(_Model):
    feat_record_key: str = Field(min_length=1)
    source: GrantSource
    choice_ids: tuple[str, ...] = ()


class SpeedGrant(_Model):
    mode: MovementMode
    feet: int = Field(ge=0)
    source: GrantSource


class SenseGrant(_Model):
    """A special sense, identified by its accepted Rules Glossary record."""

    sense_record_key: str = Field(min_length=1)
    range_feet: int = Field(ge=0)
    source: GrantSource


class DamageResponseGrant(_Model):
    damage_type: DamageType
    response: DamageResponseKind
    source: GrantSource

    @model_validator(mode="after")
    def a_damage_response(self) -> Self:
        allowed = {
            DamageResponseKind.RESISTANCE,
            DamageResponseKind.IMMUNITY,
            DamageResponseKind.VULNERABILITY,
        }
        if self.response not in allowed:
            raise ValueError(f"{self.response.value} is not a damage response")
        return self


# ---------------------------------------------------------------------------
# F9-F13: hit points, Hit Point Dice, death, inspiration, conditions
# ---------------------------------------------------------------------------


class HitPoints(_Model):
    """ADR-0003: ``maximum`` is authoritative and stored; ``current`` has no
    floor; ``current <= maximum`` is the retained D&D 5e integrity rule."""

    current: int
    maximum: int = Field(ge=0)
    temporary: int = Field(ge=0)

    @model_validator(mode="after")
    def current_within_maximum(self) -> Self:
        if self.current > self.maximum:
            raise ValueError(
                f"current ({self.current}) cannot exceed maximum ({self.maximum})"
            )
        return self


class HitPointDicePool(_Model):
    die: DieSize
    total: int = Field(ge=0)
    expended: int = Field(ge=0)

    @model_validator(mode="after")
    def expended_within_total(self) -> Self:
        if self.expended > self.total:
            raise ValueError(f"expended ({self.expended}) exceeds total ({self.total})")
        return self


class DeathState(_Model):
    successes: int = Field(ge=0, le=3)
    failures: int = Field(ge=0, le=3)
    stable: bool
    dead: bool


class ConditionInstance(_Model):
    """One applied condition. Instances are distinct, never merged by kind.

    ``level`` is the Exhaustion level and is set for Exhaustion only.
    ``source`` names what applied it (a hazard such as ``glossary.dehydration``,
    a spell, a feature) when known.
    """

    instance_id: str = Field(min_length=1)
    condition: ConditionKind
    #: Whether the Sojourner may see it (ADR-015 hidden-state handling).
    visibility: ConditionVisibility
    level: int | None = Field(default=None, ge=1, le=6)
    source: GrantSource | None = None
    applied_marker: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def level_only_for_exhaustion(self) -> Self:
        if self.condition is ConditionKind.EXHAUSTION and self.level is None:
            raise ValueError("an Exhaustion instance records its level")
        if self.condition is not ConditionKind.EXHAUSTION and self.level is not None:
            raise ValueError(f"{self.condition.value} carries no level")
        return self


# ---------------------------------------------------------------------------
# F14-F17: active effects, usage counters, slots, spell access
# ---------------------------------------------------------------------------


class ActiveEffect(_Model):
    """One active effect instance (a spell, feature or item in effect).

    Concurrent effects are separate instances. ``cast_level`` records the
    slot level a spell was cast with; what that level changes is not defined
    here (Known Unknown: upcasting). ``form_record_key`` names an assumed form
    (Wild Shape's Beast) without merging its statistics, which is 15c's.
    """

    instance_id: str = Field(min_length=1)
    source: GrantSource
    cast_level: int | None = Field(default=None, ge=0, le=9)
    concentration: bool
    started_marker: str | None = Field(default=None, min_length=1)
    form_record_key: str | None = Field(default=None, min_length=1)


class UsageCounter(_Model):
    """Expended uses of one resource.

    ``entitlement_key`` names the accepted ``progression_entry`` whose
    quantity is the maximum (``rages``, ``focus_points``, ...); validation
    checks ``maximum`` against it. Without one, ``maximum`` is ``None`` when
    the source states the maximum only in prose — no prose-derived limit is
    invented.
    """

    counter_id: str = Field(min_length=1)
    source: GrantSource
    entitlement_key: str | None = Field(default=None, min_length=1)
    maximum: int | None = Field(default=None, ge=0)
    expended: int = Field(ge=0)

    @model_validator(mode="after")
    def expended_within_maximum(self) -> Self:
        if self.maximum is not None and self.expended > self.maximum:
            raise ValueError(
                f"{self.counter_id}: expended ({self.expended}) exceeds "
                f"maximum ({self.maximum})"
            )
        return self


class SlotLevel(_Model):
    level: int = Field(ge=1, le=9)
    total: int = Field(ge=0)
    expended: int = Field(ge=0)

    @model_validator(mode="after")
    def expended_within_total(self) -> Self:
        if self.expended > self.total:
            raise ValueError(
                f"level {self.level}: expended ({self.expended}) exceeds "
                f"total ({self.total})"
            )
        return self


class SpellSlotPool(_Model):
    """One distinct pool of spell slots (Spellcasting, Pact Magic, ...).

    ``total`` per level is stored and authoritative (ADR-0003). Pools are never
    merged: Pact Magic slots and Spellcasting slots stay apart.
    """

    pool_id: str = Field(min_length=1)
    source: GrantSource
    levels: tuple[SlotLevel, ...]

    @model_validator(mode="after")
    def one_row_per_level(self) -> Self:
        levels = [s.level for s in self.levels]
        if len(levels) != len(set(levels)):
            raise ValueError(f"pool {self.pool_id} repeats a slot level")
        return self


SpellAccessMode = Literal[
    "cantrip_known", "known", "prepared", "always_prepared", "spellbook", "granted"
]


class SpellAccess(_Model):
    """One spell a pool gives access to, and how.

    ``pool_id`` keeps each class's (or feature's) spells distinct: a
    multiclass character's Wizard and Cleric spells never share a list.
    """

    pool_id: str = Field(min_length=1)
    spell_record_key: str = Field(min_length=1)
    mode: SpellAccessMode
    source: GrantSource


# ---------------------------------------------------------------------------
# F20: rest anchors
# ---------------------------------------------------------------------------


class RestAnchors(_Model):
    """When rests last finished, as fiction-time markers.

    ``None`` inside a recorded anchor means *recorded: never*. What a rest
    restores is not a 2b operation.
    """

    last_short_rest_marker: str | None = Field(default=None, min_length=1)
    last_long_rest_marker: str | None = Field(default=None, min_length=1)


# ---------------------------------------------------------------------------
# Documents
# ---------------------------------------------------------------------------


def _unique(name: str, ids: list[str]) -> None:
    if len(ids) != len(set(ids)):
        raise ValueError(f"{name} repeats an identifier")


class _SharedState(_Model):
    """Families a character and a continuing creature both carry."""

    state_schema_version: Literal[1] = STATE_SCHEMA_VERSION
    hit_points: HitPoints | None = None
    conditions: tuple[ConditionInstance, ...] | None = None
    active_effects: tuple[ActiveEffect, ...] | None = None
    usage_counters: tuple[UsageCounter, ...] | None = None
    ability_adjustments: tuple[AbilityAdjustment, ...] | None = None
    choices: tuple[ChoiceRecord, ...] | None = None
    death_state: DeathState | None = None

    @model_validator(mode="after")
    def instance_ids_unique(self) -> Self:
        _unique("conditions", [c.instance_id for c in self.conditions or ()])
        _unique("active_effects", [e.instance_id for e in self.active_effects or ()])
        _unique("usage_counters", [c.counter_id for c in self.usage_counters or ()])
        _unique("choices", [c.choice_id for c in self.choices or ()])
        known = {c.choice_id for c in self.choices or ()}
        for cited in self._cited_choice_ids():
            if cited not in known:
                raise ValueError(f"choice {cited!r} is cited but not recorded")
        return self

    def _cited_choice_ids(self) -> list[str]:
        cited: list[str] = []
        for value in self.model_dump(mode="python").values():
            _collect_choice_ids(value, cited)
        return cited


def _collect_choice_ids(value: object, out: list[str]) -> None:
    if isinstance(value, dict):
        for k, v in value.items():
            if k == "choice_id" and isinstance(v, str) and "schema_id" not in value:
                out.append(v)
            elif k == "choice_ids" and isinstance(v, (list, tuple)):
                out.extend(str(x) for x in v)
            else:
                _collect_choice_ids(v, out)
    elif isinstance(value, (list, tuple)):
        for v in value:
            _collect_choice_ids(v, out)


class Dnd5eCharacterState(_SharedState):
    """The complete persistent mechanical state of one D&D 5e character."""

    alignment: Alignment | None = None
    species: OriginSelection | None = None
    background: OriginSelection | None = None
    classes: tuple[ClassLevel, ...] | None = None
    #: Class record keys in the order levels were gained; the first is the
    #: initial class.
    level_history: tuple[str, ...] | None = None
    experience_points: int | None = Field(default=None, ge=0)
    ability_scores: Dnd5eAbilityScores | None = None
    skill_proficiencies: tuple[SkillGrant, ...] | None = None
    saving_throw_proficiencies: tuple[SavingThrowGrant, ...] | None = None
    weapon_proficiencies: tuple[WeaponProficiencyGrant, ...] | None = None
    armor_training: tuple[ArmorTrainingGrant, ...] | None = None
    tool_proficiencies: tuple[ToolGrant, ...] | None = None
    languages: tuple[LanguageGrant, ...] | None = None
    feats: tuple[FeatSelection, ...] | None = None
    size: CreatureSize | None = None
    creature_type: CreatureType | None = None
    speeds: tuple[SpeedGrant, ...] | None = None
    senses: tuple[SenseGrant, ...] | None = None
    damage_responses: tuple[DamageResponseGrant, ...] | None = None
    condition_immunities: tuple[ConditionKind, ...] | None = None
    hit_point_dice: tuple[HitPointDicePool, ...] | None = None
    heroic_inspiration: bool | None = None
    spell_slot_pools: tuple[SpellSlotPool, ...] | None = None
    spell_access: tuple[SpellAccess, ...] | None = None
    currency: dict[Currency, int] | None = None
    rest_anchors: RestAnchors | None = None

    @model_validator(mode="after")
    def character_invariants(self) -> Self:
        classes = self.classes or ()
        _unique("classes", [c.class_record_key for c in classes])
        _unique("spell_slot_pools", [p.pool_id for p in self.spell_slot_pools or ()])
        if self.level_history is not None and self.classes is not None:
            per_class: dict[str, int] = {}
            for key in self.level_history:
                per_class[key] = per_class.get(key, 0) + 1
            if per_class != {c.class_record_key: c.level for c in classes}:
                raise ValueError("level_history does not match the class levels")
        if sum(c.level for c in classes) > 20:
            raise ValueError("a character has at most 20 levels")
        if self.currency is not None and any(v < 0 for v in self.currency.values()):
            raise ValueError("currency amounts cannot be negative")
        return self


class SummonOrigin(_Model):
    """Source-specific origin of a summoned or created creature.

    ``source`` is the spell, feature or item that created it; ``item_id``
    names the item instance when an item did (Bag of Tricks).
    ``summoner_subject`` is the character or creature that created it and
    ``effect_instance_id`` the active effect on that subject that sustains it,
    if any. ``ends_marker``/``dismissed_marker`` record the source-stated end and
    a dismissal; ``controller_subject`` who currently controls it. Executing
    any of these lifecycle rules is not 2b's.
    """

    source: GrantSource
    item_id: UUID | None = None
    summoner_subject: UUID | None = None
    effect_instance_id: str | None = Field(default=None, min_length=1)
    controller_subject: UUID | None = None
    ends_marker: str | None = Field(default=None, min_length=1)
    dismissed_marker: str | None = Field(default=None, min_length=1)


class CreatureState(_SharedState):
    """The persistent mechanical state of one continuing creature instance.

    ``template_record_key`` is the accepted stat block it is an instance of;
    the template never holds mutable state. Two creatures of one template are
    two documents.
    """

    template_record_key: str = Field(min_length=1)
    summon: SummonOrigin | None = None
