"""Test builders for CRD Issue 2b state.

``real_index`` builds the exact effective authority of the committed accepted
successor offline (no database): the committed candidate with the empty
override set. Leaf order only orders governing prose, which validation does not
read, so a synthetic order is enough.

``complete_character`` builds a complete, valid character for any class and
level, deriving every structured requirement (usage counters, slot pools,
choice schemas) from the authority rather than restating it.
"""

from __future__ import annotations

import copy
import hashlib
import json
from functools import lru_cache
from pathlib import Path
from uuid import UUID

from afterworlds.ingestion.mechanical.oracle import (
    AcceptedInputs,
    candidate_from_accepted_inputs,
    committed_inputs_for,
)
from afterworlds.ingestion.mechanical.projection import identify_projection
from afterworlds.ingestion.mechanical.representation import (
    AbilityScore,
    ConditionKind,
    CreatureSize,
    Currency,
    DieSize,
    MovementMode,
    Skill,
    WeaponCategory,
)
from afterworlds.models.dnd5e_state import (
    BaseArmorClass,
    ChoiceRecord,
    ClassLevel,
    ConditionInstance,
    CreatureState,
    DeathState,
    Dnd5eAbilityScores,
    Dnd5eCharacterState,
    FeatSelection,
    GrantSource,
    HitPointDicePool,
    HitPoints,
    LanguageGrant,
    OptionChoice,
    OriginSelection,
    RecordChoice,
    RestAnchors,
    SavingThrowGrant,
    SenseGrant,
    SkillGrant,
    SlotLevel,
    SpeedGrant,
    SpellAccess,
    SpellSlotPool,
    UsageCounter,
    VocabularyChoice,
    WeaponProficiencyGrant,
)
from afterworlds.models.dnd5e_vocabulary import Alignment, CreatureType, Language
from afterworlds.models.enums import (
    ConditionVisibility,
    OverrideOperationEnum,
    OverrideOriginEnum,
)
from afterworlds.models.rules_package import RulesPackageBinding
from afterworlds.services.dnd5e_state.authority import (
    AuthorityIndex,
    component_schema_id,
)
from afterworlds.services.dnd5e_state.validation import KNOWN_COUNT_ENTITLEMENTS
from afterworlds.services.rules_authority.application import apply_override_set
from afterworlds.services.rules_authority.override_set import (
    EMPTY_OVERRIDE_SET_UUID,
    EffectiveOverrideEntry,
    EffectiveOverrideSet,
    override_set_identity,
)
from afterworlds.services.rules_authority.patches import (
    patch_from_payload,
    patch_payload,
)
from afterworlds.services.rules_authority.targets import (
    MechanicalTarget,
    MechanicalTargetKind,
)

PACKAGE = "1299484e-c72d-509b-bd8d-d0169ee1f8d2"
RELEASE = "5.2.1-corpus.8781d4e0-a3b"

#: (class record, a subclass catalogued under it, its Hit Die) for all twelve.
CLASSES: tuple[tuple[str, str, DieSize], ...] = (
    ("classes.barbarian", "classes.barbarian.path_of_the_berserker", DieSize.D12),
    ("classes.bard", "classes.bard.college_of_lore", DieSize.D8),
    ("classes.cleric", "classes.cleric.life_domain", DieSize.D8),
    ("classes.druid", "classes.druid.circle_of_the_land", DieSize.D8),
    ("classes.fighter", "classes.fighter.champion", DieSize.D10),
    ("classes.monk", "classes.monk.warrior_of_the_open_hand", DieSize.D8),
    ("classes.paladin", "classes.paladin.oath_of_devotion", DieSize.D10),
    ("classes.ranger", "classes.ranger.hunter", DieSize.D10),
    ("classes.rogue", "classes.rogue.thief", DieSize.D8),
    ("classes.sorcerer", "classes.sorcerer.draconic_sorcery", DieSize.D6),
    ("classes.warlock", "classes.warlock.fiend_patron", DieSize.D8),
    ("classes.wizard", "classes.wizard.evoker", DieSize.D6),
)

ELF = "character_origins.elf"
SAGE = "character_origins.sage"


@lru_cache(maxsize=1)
def real_index() -> AuthorityIndex:
    inputs = committed_inputs_for(PACKAGE, RELEASE)
    assert inputs is not None
    return index_for(inputs)


def index_for(
    inputs: AcceptedInputs, entries: tuple[EffectiveOverrideEntry, ...] = ()
) -> AuthorityIndex:
    """The effective index of *inputs* under its own derived projection and
    the override set of *entries* (empty by default)."""
    candidate = candidate_from_accepted_inputs(inputs)
    projection = identify_projection(candidate).projection_uuid
    binding = RulesPackageBinding(
        package_uuid=UUID(PACKAGE),
        release_version=RELEASE,
        mechanical_projection_uuid=UUID(projection),
        override_set_uuid=UUID(
            override_set_identity(entries) if entries else EMPTY_OVERRIDE_SET_UUID
        ),
    )
    leaves = {s.leaf_id: i for i, s in enumerate(candidate.classification.spans)}
    authority = apply_override_set(
        candidate,
        EffectiveOverrideSet(PACKAGE, RELEASE, entries),
        binding,
        leaf_order=leaves,
    )
    return AuthorityIndex.from_authority(authority)


#: The Owner-accepted S1 contest supplement (ADR-015b Group 17), at its
#: accepted digest. Read-only; applied only in memory, never to a store.
S1_PATH = (
    Path(__file__).parents[3]
    / ".claude/review-notes/issue-15b-contest-authority/supplement-s1/s1.json"
)
S1_SHA256 = "c232a7863d3a31144ebb7fcdd2f7af6591b68b4f3cb096bf65ad6e6d3372c64a"  # noqa: E501  # pragma: allowlist secret


def s1_entry(**payload_changes: object) -> EffectiveOverrideEntry:
    """S1's override entry exactly as accepted; *payload_changes* alter the
    authored component's text, to model a changed supplement."""
    data = S1_PATH.read_bytes()
    assert hashlib.sha256(data).hexdigest() == S1_SHA256, "S1 is not the accepted one"
    override = json.loads(data)["override"]
    if payload_changes:
        override = copy.deepcopy(override)
        override["payload"] = _changed(override["payload"], payload_changes)
    target = MechanicalTarget(
        kind=MechanicalTargetKind(override["target"]["kind"]),
        record_key=override["target"]["record_key"],
    )
    operation = OverrideOperationEnum(override["operation"])
    patch = patch_from_payload(override["payload"], operation=operation, target=target)
    return EffectiveOverrideEntry(
        override_id=str(override["override_id"]),
        origin=OverrideOriginEnum(override["origin"]),
        target=target,
        operation=operation,
        precedence=int(override["precedence"]),
        apply_order=0,
        is_enabled=bool(override["is_enabled"]),
        payload=patch_payload(patch),
    )


def _changed(payload: object, changes: dict[str, object]) -> object:
    """*payload* with every string value under a key in *changes* replaced."""
    if isinstance(payload, dict):
        return {
            k: (
                changes[k]
                if k in changes and isinstance(v, str)
                else _changed(v, changes)
            )
            for k, v in payload.items()
        }
    if isinstance(payload, list):
        return [_changed(v, changes) for v in payload]
    return payload


@lru_cache(maxsize=1)
def s1_index() -> AuthorityIndex:
    """The certified C9 release with the accepted S1 supplement applied, in
    memory (ADR-015b Group 17: S1 is never activated in a store here)."""
    inputs = committed_inputs_for(PACKAGE, RELEASE)
    assert inputs is not None
    return index_for(inputs, (s1_entry(),))


def choice(
    index: AuthorityIndex,
    choice_id: str,
    record: str,
    component: str,
    *selected: RecordChoice | OptionChoice | VocabularyChoice,
) -> ChoiceRecord:
    found = index.component(record, component)
    assert found is not None, (record, component)
    return ChoiceRecord(
        choice_id=choice_id,
        source=GrantSource(record_key=record, component_key=component),
        schema_id=component_schema_id(found),
        selected=selected,
    )


def counters_for(
    index: AuthorityIndex, class_key: str, level: int
) -> tuple[UsageCounter, ...]:
    best: dict[str, tuple[int, int]] = {}
    for e in index.progression(class_key):
        due = (
            e.quantity
            and e.level <= level
            and e.entitlement_key not in KNOWN_COUNT_ENTITLEMENTS
        )
        newer = e.entitlement_key not in best or e.level > best[e.entitlement_key][0]
        if due and newer:
            best[e.entitlement_key] = (e.level, e.quantity)
    return tuple(
        UsageCounter(
            counter_id=f"{class_key}:{key}",
            source=GrantSource(record_key=class_key),
            entitlement_key=key,
            maximum=quantity,
            expended=0,
        )
        for key, (_, quantity) in sorted(best.items())
    )


def slots_for(
    index: AuthorityIndex, class_key: str, level: int
) -> tuple[SpellSlotPool, ...]:
    rows = [r for r in index.slot_progression(class_key) if r.character_level == level]
    if not rows:
        return ()
    pool_id = (
        "pact_magic" if class_key == "classes.warlock" else f"{class_key}:spellcasting"
    )
    return (
        SpellSlotPool(
            pool_id=pool_id,
            source=GrantSource(record_key=class_key),
            levels=tuple(
                SlotLevel(level=r.slot_level, total=r.slots, expended=0)
                for r in sorted(rows, key=lambda r: r.slot_level)
            ),
        ),
    )


def complete_character(
    index: AuthorityIndex,
    class_key: str = "classes.wizard",
    level: int = 1,
    *,
    subclass: str | None = None,
    hit_die: DieSize = DieSize.D6,
) -> Dnd5eCharacterState:
    """A complete, valid character of one class at *level*."""
    elf_source = GrantSource(record_key=ELF, component_key="darkvision")
    sage = GrantSource(record_key=SAGE, component_key="skill_proficiencies")
    pools = slots_for(index, class_key, level)
    return Dnd5eCharacterState(
        alignment=Alignment.NEUTRAL_GOOD,
        species=OriginSelection(record_key=ELF, choice_ids=("elf-lineage",)),
        background=OriginSelection(record_key=SAGE),
        classes=(
            ClassLevel(
                class_record_key=class_key,
                level=level,
                subclass_record_key=subclass,
                hit_die=hit_die,
            ),
        ),
        level_history=(class_key,) * level,
        experience_points=0,
        ability_scores=Dnd5eAbilityScores(
            strength=8,
            dexterity=14,
            constitution=13,
            intelligence=15,
            wisdom=12,
            charisma=10,
        ),
        ability_adjustments=(),
        choices=(
            choice(
                index,
                "elf-lineage",
                ELF,
                "elven_lineage",
                VocabularyChoice(vocabulary="elven_lineage", value="high_elf"),
                VocabularyChoice(vocabulary="ability", value="intelligence"),
            ),
        ),
        skill_proficiencies=(
            SkillGrant(skill=Skill.ARCANA, expertise=False, source=sage),
            SkillGrant(skill=Skill.HISTORY, expertise=False, source=sage),
        ),
        saving_throw_proficiencies=(
            SavingThrowGrant(
                ability=AbilityScore.INTELLIGENCE,
                source=GrantSource(record_key=class_key, component_key="core_traits"),
            ),
        ),
        weapon_proficiencies=(
            WeaponProficiencyGrant(
                category=WeaponCategory.SIMPLE,
                source=GrantSource(record_key=class_key, component_key="core_traits"),
            ),
        ),
        armor_training=(),
        tool_proficiencies=(),
        languages=(
            LanguageGrant(
                language=Language.COMMON,
                source=GrantSource(record_key="character_creation.character_creation"),
            ),
            LanguageGrant(language=Language.ELVISH, source=GrantSource(record_key=ELF)),
        ),
        feats=(
            FeatSelection(
                feat_record_key="feats.magic_initiate",
                source=GrantSource(record_key=SAGE, component_key="feat"),
            ),
        ),
        size=CreatureSize.MEDIUM,
        creature_type=CreatureType.HUMANOID,
        speeds=(
            SpeedGrant(
                mode=MovementMode.WALK,
                feet=30,
                source=GrantSource(record_key=ELF, component_key="speed"),
            ),
        ),
        senses=(
            SenseGrant(
                sense_record_key="glossary.darkvision", range_feet=60, source=elf_source
            ),
        ),
        damage_responses=(),
        condition_immunities=(),
        hit_points=HitPoints(current=7, maximum=7, temporary=0),
        hit_point_dice=(HitPointDicePool(die=hit_die, total=level, expended=0),),
        death_state=DeathState(successes=0, failures=0, stable=False, dead=False),
        heroic_inspiration=False,
        conditions=(),
        active_effects=(),
        usage_counters=counters_for(index, class_key, level),
        spell_slot_pools=pools or None,
        spell_access=(
            (
                SpellAccess(
                    pool_id=f"{class_key}:spells",
                    spell_record_key="spells.fire_bolt",
                    mode="cantrip_known",
                    source=GrantSource(record_key=class_key),
                ),
            )
            if pools or _casts(index, class_key, level)
            else None
        ),
        currency={Currency.GP: 15},
        rest_anchors=RestAnchors(),
        base_armor_class=BaseArmorClass(),  # recorded: the default calculation
        hazards=(),
    )


def _casts(index: AuthorityIndex, class_key: str, level: int) -> bool:
    return any(
        e.entitlement_key in {"cantrips", "prepared_spells"}
        and e.quantity
        and e.level <= level
        for e in index.progression(class_key)
    )


def cat(**updates: object) -> CreatureState:
    base = CreatureState(
        template_record_key="animals.cat",
        hit_points=HitPoints(current=2, maximum=2, temporary=0),
        conditions=(),
        active_effects=(),
        hazards=(),
    )
    return base.model_copy(update=updates)


def prone(instance_id: str = "c1") -> ConditionInstance:
    return ConditionInstance(
        instance_id=instance_id,
        condition=ConditionKind.PRONE,
        visibility=ConditionVisibility.VISIBLE,
    )
