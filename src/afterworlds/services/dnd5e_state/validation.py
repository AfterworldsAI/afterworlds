"""Validate 2b state against its bound effective authority.

Two separate questions, both answered with typed :class:`StateFailure` values:

* :func:`validate_character` / :func:`validate_creature` — is every recorded
  identity an accepted identity of the right kind, was every recorded choice
  made under the source schema the authority still states, and does every
  value respect the bounds the **structured** authority states? Prose-bound
  limits are not invented: where a maximum is stated only in prose, nothing
  is checked against it.
* :func:`character_readiness` / :func:`creature_readiness` — is every family
  the authority makes applicable recorded? Explicit empty, zero or ``False``
  is recorded state; ``None`` is missing.

Neither certifies legality, eligibility or executable mechanics. A ready,
valid character is one whose recorded inputs are well-formed for its binding;
whether a choice was legal, and what any of it computes to, is CRD Issue 15c.
"""

from __future__ import annotations

from collections.abc import Iterator

from afterworlds.ingestion.mechanical.representation import RecordKind
from afterworlds.models.dnd5e_state import (
    VOCABULARIES,
    ChoiceRecord,
    CreatureState,
    Dnd5eCharacterState,
    GrantSource,
    OptionChoice,
    RecordChoice,
    UsageCounter,
    VocabularyChoice,
)
from afterworlds.models.dnd5e_vocabulary import ORIGIN_CHOICE_SOURCES
from afterworlds.services.dnd5e_state.authority import (
    AuthorityIndex,
    component_schema_id,
)
from afterworlds.services.dnd5e_state.errors import FailureCode, StateFailure

__all__ = [
    "FAMILIAR_SOURCES",
    "KNOWN_COUNT_ENTITLEMENTS",
    "character_readiness",
    "creature_readiness",
    "validate_character",
    "validate_creature",
]

#: Progression entitlements whose quantity counts things known or prepared,
#: not uses expended. Every other entitlement with a quantity is a usage
#: counter's structured maximum (``rages``, ``focus_points``, ...).
KNOWN_COUNT_ENTITLEMENTS = frozenset(
    {"cantrips", "prepared_spells", "weapon_mastery", "eldritch_invocations"}
)

_ITEM_KINDS = frozenset({RecordKind.EQUIPMENT, RecordKind.MAGIC_ITEM})


def _fail(code: FailureCode, path: str, detail: str) -> StateFailure:
    return StateFailure(code, path, detail)


def _identity(
    index: AuthorityIndex, key: str, kinds: frozenset[RecordKind], path: str
) -> Iterator[StateFailure]:
    kind = index.kind(key)
    if kind is None:
        yield _fail(
            FailureCode.INVALID_IDENTITY, path, f"{key!r} is not an accepted record"
        )
    elif kinds and kind not in kinds:
        allowed = sorted(k.value for k in kinds)
        yield _fail(
            FailureCode.WRONG_KIND, path, f"{key!r} is a {kind.value}, not {allowed}"
        )


def _source(
    index: AuthorityIndex, source: GrantSource, path: str
) -> Iterator[StateFailure]:
    yield from _identity(index, source.record_key, frozenset(), f"{path}.source")
    if (
        source.component_key is not None
        and index.record(source.record_key) is not None
        and index.component(source.record_key, source.component_key) is None
    ):
        yield _fail(
            FailureCode.INVALID_IDENTITY,
            f"{path}.source",
            f"{source.record_key!r} has no component {source.component_key!r}",
        )


#: Origin-choice vocabularies by name, with the component that offers each.
_SCOPED_VOCABULARIES = {
    name: ORIGIN_CHOICE_SOURCES[enum]
    for name, enum in VOCABULARIES.items()
    if enum in ORIGIN_CHOICE_SOURCES
}


def _selections(
    index: AuthorityIndex,
    selected: tuple[object, ...],
    source: GrantSource,
    path: str,
) -> Iterator[StateFailure]:
    """Each selected identity exists. Whether it was a legal pick is 15c's.

    Checked from the values themselves, so state built without model
    validation (``model_copy``) still fails closed.
    """
    for i, sel in enumerate(selected):
        at = f"{path}.selected[{i}]"
        if isinstance(sel, RecordChoice):
            if index.record(sel.record_key) is None:
                yield _fail(
                    FailureCode.INVALID_IDENTITY,
                    at,
                    f"{sel.record_key!r} is not an accepted record",
                )
        elif isinstance(sel, OptionChoice):
            component = (
                None
                if source.component_key is None
                else index.component(source.record_key, source.component_key)
            )
            options = (
                {o.semantic_key for o in component.options} if component else set()
            )
            if sel.option_key not in options:
                yield _fail(
                    FailureCode.INVALID_IDENTITY,
                    at,
                    f"{source.record_key}/{source.component_key} states no option "
                    f"{sel.option_key!r}",
                )
        elif isinstance(sel, VocabularyChoice):
            enum = VOCABULARIES.get(sel.vocabulary)
            if enum is None or sel.value not in {m.value for m in enum}:
                yield _fail(
                    FailureCode.INVALID_IDENTITY,
                    at,
                    f"{sel.value!r} is not a {sel.vocabulary}",
                )
            elif (scope := _SCOPED_VOCABULARIES.get(sel.vocabulary)) is not None and (
                scope != (source.record_key, source.component_key)
            ):
                yield _fail(
                    FailureCode.INVALID_IDENTITY,
                    at,
                    f"a {sel.vocabulary} is chosen under {scope[0]}/{scope[1]}, "
                    f"not {source.record_key}/{source.component_key}",
                )
        else:
            yield _fail(
                FailureCode.INVALID_IDENTITY,
                at,
                f"{sel!r} is not a typed selection (record, option or vocabulary)",
            )


def _choices(
    index: AuthorityIndex, choices: tuple[ChoiceRecord, ...]
) -> Iterator[StateFailure]:
    for choice in choices:
        path = f"choices[{choice.choice_id}]"
        if choice.source.component_key is None:
            yield _fail(
                FailureCode.INVALID_IDENTITY,
                path,
                "a choice names the component that states it",
            )
            continue
        yield from _source(index, choice.source, path)
        component = index.component(
            choice.source.record_key, choice.source.component_key
        )
        if component is not None and component_schema_id(component) != choice.schema_id:
            yield _fail(
                FailureCode.SCHEMA_CHANGED,
                path,
                f"{choice.source.record_key}/{choice.source.component_key} no "
                "longer states the schema this choice was made under",
            )
        yield from _selections(index, choice.selected, choice.source, path)


def _counter_maximum(
    index: AuthorityIndex, counter: UsageCounter, class_levels: dict[str, int]
) -> Iterator[StateFailure]:
    path = f"usage_counters[{counter.counter_id}]"
    if counter.entitlement_key is None:
        return
    class_key = counter.source.record_key
    level = class_levels.get(class_key)
    if level is None:
        yield _fail(
            FailureCode.INCONSISTENT,
            path,
            f"entitlement {counter.entitlement_key!r} is sourced from "
            f"{class_key!r}, which the character has no levels in",
        )
        return
    entries = [
        e
        for e in index.progression(class_key)
        if e.entitlement_key == counter.entitlement_key
        and e.quantity is not None
        and e.level <= level
    ]
    if not entries or counter.entitlement_key in KNOWN_COUNT_ENTITLEMENTS:
        yield _fail(
            FailureCode.INVALID_IDENTITY,
            path,
            f"{class_key!r} states no usage entitlement "
            f"{counter.entitlement_key!r} at level {level}",
        )
        return
    expected = max(entries, key=lambda e: e.level).quantity
    if counter.maximum != expected:
        yield _fail(
            FailureCode.BOUND_EXCEEDED,
            path,
            f"maximum {counter.maximum} is not the stated {expected} at "
            f"{class_key} level {level}",
        )


#: The accepted record that states each hazard kind; contagions are the
#: members of the accepted Magical Contagions catalogue.
_HAZARD_RECORDS = {
    "burning": "glossary.burning",
    "dehydration": "glossary.dehydration",
    "malnutrition": "glossary.malnutrition",
    "suffocation": "glossary.suffocation",
}
CONTAGION_CATALOGUE = "gameplay_toolbox.curses_and_magical_contagions"


def _hazard(index: AuthorityIndex, hazard: object, path: str) -> Iterator[StateFailure]:
    kind = getattr(hazard, "kind", None)
    source = getattr(hazard, "source", None)
    if not isinstance(source, GrantSource) or kind is None:
        yield _fail(FailureCode.INVALID_IDENTITY, path, "not a typed hazard entry")
        return
    yield from _source(index, source, path)
    key = source.record_key
    if kind == "contagion":
        if not index.is_member(CONTAGION_CATALOGUE, key):
            yield _fail(
                FailureCode.WRONG_KIND,
                path,
                f"{key!r} is not an accepted Magical Contagion",
            )
    elif _HAZARD_RECORDS.get(kind) != key:
        yield _fail(
            FailureCode.WRONG_KIND,
            path,
            f"a {kind} hazard is stated by {_HAZARD_RECORDS.get(kind)!r}, not {key!r}",
        )


def _shared(
    index: AuthorityIndex, state: Dnd5eCharacterState | CreatureState
) -> Iterator[StateFailure]:
    yield from _choices(index, state.choices or ())
    for adj in state.ability_adjustments or ():
        yield from _source(
            index, adj.source, f"ability_adjustments[{adj.ability.value}]"
        )
    if state.hit_points is not None and state.hit_points.temporary_source:
        yield from _source(
            index, state.hit_points.temporary_source, "hit_points.temporary_source"
        )
    for cond in state.conditions or ():
        if cond.source is not None:
            yield from _source(index, cond.source, f"conditions[{cond.instance_id}]")
    for effect in state.active_effects or ():
        path = f"active_effects[{effect.instance_id}]"
        yield from _source(index, effect.source, path)
        yield from _selections(index, effect.selections or (), effect.source, path)
        if effect.form_record_key is not None:
            yield from _identity(
                index, effect.form_record_key, frozenset({RecordKind.CREATURE}), path
            )
    for counter in state.usage_counters or ():
        yield from _source(
            index, counter.source, f"usage_counters[{counter.counter_id}]"
        )
    for i, hazard in enumerate(state.hazards or ()):
        yield from _hazard(index, hazard, f"hazards[{i}]")


def validate_character(
    index: AuthorityIndex, state: Dnd5eCharacterState
) -> tuple[StateFailure, ...]:
    """Every identity, choice schema and structured bound of *state*."""
    out: list[StateFailure] = list(_shared(index, state))
    one = frozenset
    if state.species is not None:
        out += _identity(
            index, state.species.record_key, one({RecordKind.SPECIES}), "species"
        )
    if state.background is not None:
        out += _identity(
            index,
            state.background.record_key,
            one({RecordKind.BACKGROUND}),
            "background",
        )
    class_levels: dict[str, int] = {}
    for c in state.classes or ():
        path = f"classes[{c.class_record_key}]"
        out += _identity(index, c.class_record_key, one({RecordKind.CLASS}), path)
        class_levels[c.class_record_key] = c.level
        if c.subclass_record_key is not None:
            out += _identity(
                index, c.subclass_record_key, one({RecordKind.CLASS_FEATURE}), path
            )
            if index.record(c.subclass_record_key) is not None and not index.is_member(
                c.class_record_key, c.subclass_record_key
            ):
                out.append(
                    _fail(
                        FailureCode.INCONSISTENT,
                        path,
                        f"{c.subclass_record_key!r} is not catalogued under "
                        f"{c.class_record_key!r}",
                    )
                )
    for feat in state.feats or ():
        path = f"feats[{feat.feat_record_key}]"
        out += _identity(index, feat.feat_record_key, one({RecordKind.FEAT}), path)
        out += _source(index, feat.source, path)
    grant_lists: list[tuple[str, tuple[object, ...]]] = [
        ("skill_proficiencies", state.skill_proficiencies or ()),
        ("saving_throw_proficiencies", state.saving_throw_proficiencies or ()),
        ("weapon_proficiencies", state.weapon_proficiencies or ()),
        ("armor_training", state.armor_training or ()),
        ("tool_proficiencies", state.tool_proficiencies or ()),
        ("languages", state.languages or ()),
        ("speeds", state.speeds or ()),
        ("senses", state.senses or ()),
        ("damage_responses", state.damage_responses or ()),
        ("spell_slot_pools", state.spell_slot_pools or ()),
        ("spell_access", state.spell_access or ()),
    ]
    for name, grants in grant_lists:
        for i, grant in enumerate(grants):
            out += _source(index, grant.source, f"{name}[{i}]")  # type: ignore[attr-defined]
    for i, w in enumerate(state.weapon_proficiencies or ()):
        if w.weapon_record_key is not None:
            out += _identity(
                index, w.weapon_record_key, one({RecordKind.EQUIPMENT}),
                f"weapon_proficiencies[{i}]",
            )  # fmt: skip
    for i, t in enumerate(state.tool_proficiencies or ()):
        path = f"tool_proficiencies[{i}]"
        out += _identity(index, t.record_key, _ITEM_KINDS, path)
        if (
            t.component_key is not None
            and index.record(t.record_key) is not None
            and index.component(t.record_key, t.component_key) is None
        ):
            out.append(
                _fail(
                    FailureCode.INVALID_IDENTITY,
                    path,
                    f"{t.record_key!r} has no component {t.component_key!r}",
                )
            )
    for i, s in enumerate(state.senses or ()):
        out += _identity(
            index, s.sense_record_key, one({RecordKind.GLOSSARY_RULE}), f"senses[{i}]"
        )
    for i, a in enumerate(state.spell_access or ()):
        out += _identity(
            index, a.spell_record_key, one({RecordKind.SPELL}), f"spell_access[{i}]"
        )
    for counter in state.usage_counters or ():
        out += _counter_maximum(index, counter, class_levels)
    out += _slot_totals(index, state, class_levels)
    if state.base_armor_class is not None and state.base_armor_class.source:
        out += _source(index, state.base_armor_class.source, "base_armor_class")
    return tuple(out)


def _slot_totals(
    index: AuthorityIndex, state: Dnd5eCharacterState, class_levels: dict[str, int]
) -> Iterator[StateFailure]:
    """Single-class slot totals must equal the structured slot table.

    A multiclass caster's combined table is stated only in prose, so its
    stored totals are authoritative as recorded (ADR-0003) and not checked.
    """
    if len(class_levels) != 1:
        return
    ((class_key, level),) = class_levels.items()
    rows = [r for r in index.slot_progression(class_key) if r.character_level == level]
    if not rows:
        return
    expected = {r.slot_level: r.slots for r in rows}
    pools = [
        p for p in state.spell_slot_pools or () if p.source.record_key == class_key
    ]
    for pool in pools:
        got = {s.level: s.total for s in pool.levels}
        if got != expected:
            yield _fail(
                FailureCode.BOUND_EXCEEDED,
                f"spell_slot_pools[{pool.pool_id}]",
                f"totals {got} are not the stated {expected} at {class_key} "
                f"level {level}",
            )


def validate_creature(
    index: AuthorityIndex, state: CreatureState
) -> tuple[StateFailure, ...]:
    out = list(
        _identity(
            index,
            state.template_record_key,
            frozenset({RecordKind.CREATURE}),
            "template",
        )
    )
    out += _shared(index, state)
    if state.summon is not None:
        out += _source(index, state.summon.source, "summon")
    for i, speed in enumerate(state.speeds or ()):
        out += _source(index, speed.source, f"speeds[{i}]")
    return tuple(out)


#: Families every character records, whatever its classes.
_CHARACTER_FAMILIES = (
    "alignment",
    "species",
    "background",
    "classes",
    "level_history",
    "experience_points",
    "ability_scores",
    "ability_adjustments",
    "skill_proficiencies",
    "saving_throw_proficiencies",
    "weapon_proficiencies",
    "armor_training",
    "tool_proficiencies",
    "languages",
    "feats",
    "choices",
    "size",
    "creature_type",
    "speeds",
    "senses",
    "damage_responses",
    "condition_immunities",
    "hit_points",
    "hit_point_dice",
    "death_state",
    "hazards",
    "heroic_inspiration",
    "conditions",
    "active_effects",
    "usage_counters",
    "currency",
    "rest_anchors",
)


def character_readiness(
    index: AuthorityIndex, state: Dnd5eCharacterState
) -> tuple[StateFailure, ...]:
    """Missing applicable families. Readiness is not legality."""
    out = [
        _fail(FailureCode.MISSING_STATE, name, "not recorded")
        for name in _CHARACTER_FAMILIES
        if getattr(state, name) is None
    ]
    levels = {c.class_record_key: c.level for c in state.classes or ()}
    has_slots = any(
        r.slots > 0 and r.character_level == level
        for key, level in levels.items()
        for r in index.slot_progression(key)
    )
    if has_slots and state.spell_slot_pools is None:
        out.append(_fail(FailureCode.MISSING_STATE, "spell_slot_pools", "not recorded"))
    has_spells = has_slots or any(
        e.entitlement_key in {"cantrips", "prepared_spells"}
        and e.quantity
        and e.level <= level
        for key, level in levels.items()
        for e in index.progression(key)
    )
    if has_spells and state.spell_access is None:
        out.append(_fail(FailureCode.MISSING_STATE, "spell_access", "not recorded"))
    recorded = {
        (c.source.record_key, c.entitlement_key) for c in state.usage_counters or ()
    }
    for key, level in sorted(levels.items()):
        due = {
            e.entitlement_key
            for e in index.progression(key)
            if e.quantity
            and e.level <= level
            and e.entitlement_key not in KNOWN_COUNT_ENTITLEMENTS
        }
        for entitlement in sorted(due - {e for k, e in recorded if k == key}):
            out.append(
                _fail(
                    FailureCode.MISSING_STATE,
                    f"usage_counters[{key}:{entitlement}]",
                    "the class states this usage entitlement at its level",
                )
            )
    return tuple(out)


#: Sources that create a familiar through Find Familiar: the spell
#: (``spells.md`` "Find Familiar"), Wild Companion (``classes.md``:3511) and
#: Pact of the Chain (``classes.md``:9122). A familiar's chosen creature type
#: ("a Celestial, Fey, or Fiend ... instead of a Beast") and whether it is
#: present or dismissed to the pocket dimension are applicable state.
FAMILIAR_SOURCES = frozenset(
    {
        "spells.find_familiar",
        "classes.druid.wild_companion",
        "classes.warlock.eldritch_invocation_options.pact_of_the_chain",
    }
)


def creature_readiness(state: CreatureState) -> tuple[StateFailure, ...]:
    """Missing applicable families. Readiness is not legality."""
    required = ["hit_points", "conditions", "active_effects", "hazards"]
    if state.summon is not None and state.summon.source.record_key in FAMILIAR_SOURCES:
        required += ["creature_type", "presence"]
    return tuple(
        _fail(FailureCode.MISSING_STATE, name, "not recorded")
        for name in required
        if getattr(state, name) is None
    )
