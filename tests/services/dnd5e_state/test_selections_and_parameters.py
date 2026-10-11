"""Typed selections and recorded state parameters (CRD Issue 2b, Codex review).

A choice's selected identities are typed - an accepted record, an option the
source component states, or a member of a closed source-backed vocabulary -
and each is checked to exist; legality stays 15c's. Conditions and effects
record the parameters the source says persist (who, which DC, which ability,
how long, which item), each story-scoped where it is a reference.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from afterworlds.ingestion.mechanical.representation import (
    ConditionKind,
    DurationKind,
    MovementMode,
    TimeUnit,
)
from afterworlds.models.dnd5e_state import (
    ActiveEffect,
    BaseArmorClass,
    ConditionInstance,
    CreaturePresence,
    CreatureState,
    Dnd5eCharacterState,
    EffectEnd,
    GrantSource,
    HitPoints,
    OptionChoice,
    RecordChoice,
    SenseGrant,
    SpeedGrant,
    SubjectReference,
    SummonOrigin,
    UsageCounter,
    VocabularyChoice,
)
from afterworlds.models.dnd5e_vocabulary import CreatureType
from afterworlds.models.enums import ConditionVisibility
from afterworlds.persistence.orm.story_bible import SBCastEntryORM
from afterworlds.services.dnd5e_state import holdings, service
from afterworlds.services.dnd5e_state.authority import AuthorityIndex
from afterworlds.services.dnd5e_state.errors import FailureCode, InvalidStateError
from afterworlds.services.dnd5e_state.holdings import Holder, HolderKind
from afterworlds.services.dnd5e_state.validation import validate_character
from tests.services.dnd5e_state.builders import choice, complete_character, real_index
from tests.services.dnd5e_state.conftest import (
    NOW,
    Table,
    new_character,
    new_story,
    wizardish,
)

Seeder = Callable[..., None]
ELF = "character_origins.elf"


def _codes(failures: tuple[object, ...]) -> set[FailureCode]:
    return {f.code for f in failures}  # type: ignore[attr-defined]


def _with_choice(
    *selected: object, record: str = ELF, component: str = "elven_lineage"
) -> tuple[AuthorityIndex, Dnd5eCharacterState]:
    index = real_index()
    state = complete_character(index, "classes.wizard", 1)
    made = choice(index, "c", record, component).model_copy(
        update={"selected": selected}
    )
    return index, state.model_copy(update={"choices": (made,)})


# ---------------------------------------------------------------------------
# Selections
# ---------------------------------------------------------------------------


def test_the_recorded_lineage_choice_is_valid() -> None:
    index = real_index()
    assert (
        validate_character(index, complete_character(index, "classes.wizard", 1)) == ()
    )


@pytest.mark.parametrize(
    "selected",
    [
        "nonexistent-option",  # free text, as Codex's probe wrote it
        RecordChoice(record_key="spells.nonexistent"),
        OptionChoice(option_key="high_elf"),  # the lineage has no structured options
        VocabularyChoice.model_construct(vocabulary="elven_lineage", value="sea_elf"),
        VocabularyChoice(
            vocabulary="gnomish_lineage", value="rock_gnome"
        ),  # wrong source
    ],
    ids=["free-text", "record", "option", "vocabulary-value", "vocabulary-source"],
)
def test_an_unknown_or_misplaced_selection_is_an_invalid_identity(
    selected: object,
) -> None:
    index, state = _with_choice(selected)
    assert FailureCode.INVALID_IDENTITY in _codes(validate_character(index, state))


def test_a_selection_vocabulary_member_is_checked_on_construction() -> None:
    with pytest.raises(ValidationError):
        VocabularyChoice(vocabulary="elven_lineage", value="sea_elf")
    with pytest.raises(ValidationError):
        VocabularyChoice(vocabulary="lineage", value="drow")


def test_a_structured_component_option_is_selectable() -> None:
    index, state = _with_choice(
        OptionChoice(option_key="assist_attack_roll"),
        record="glossary.help",
        component="assistance",
    )
    assert validate_character(index, state) == ()
    index, state = _with_choice(
        OptionChoice(option_key="assist_saving_throw"),
        record="glossary.help",
        component="assistance",
    )
    assert FailureCode.INVALID_IDENTITY in _codes(validate_character(index, state))


@pytest.mark.parametrize(
    ("record", "component", "selected"),
    [
        (  # class: Metamagic options are accepted records
            "classes.sorcerer.metamagic",
            "metamagic",
            (
                RecordChoice(
                    record_key="classes.sorcerer.metamagic_options.quickened_spell"
                ),
                RecordChoice(
                    record_key="classes.sorcerer.metamagic_options.subtle_spell"
                ),
            ),
        ),
        (  # class: a Fighting Style is a feat record
            "classes.fighter.fighting_style",
            "fighting_style",
            (RecordChoice(record_key="feats.archery"),),
        ),
        (  # feat: Skilled picks skills
            "feats.skilled",
            "skilled",
            tuple(
                VocabularyChoice(vocabulary="skill", value=v)
                for v in ("arcana", "stealth", "insight")
            ),
        ),
        (  # feat/spell: Magic Initiate picks a class list and its spells
            "feats.magic_initiate",
            "two_cantrips",
            (
                RecordChoice(record_key="classes.cleric"),
                RecordChoice(record_key="spells.guidance"),
                RecordChoice(record_key="spells.sacred_flame"),
            ),
        ),
    ],
    ids=["metamagic", "fighting-style", "skilled", "magic-initiate"],
)
def test_representative_class_feat_and_spell_choices(
    record: str, component: str, selected: tuple[object, ...]
) -> None:
    index, state = _with_choice(*selected, record=record, component=component)
    assert validate_character(index, state) == ()


def test_a_changed_source_schema_is_still_refused() -> None:
    index, state = _with_choice(
        VocabularyChoice(vocabulary="elven_lineage", value="drow")
    )
    drifted = state.choices[0].model_copy(update={"schema_id": "0" * 64})  # type: ignore[index]
    state = state.model_copy(update={"choices": (drifted,)})
    assert FailureCode.SCHEMA_CHANGED in _codes(validate_character(index, state))


# ---------------------------------------------------------------------------
# Structural rules of the recorded parameters
# ---------------------------------------------------------------------------


def test_parameter_structure_is_enforced() -> None:
    with pytest.raises(ValidationError):  # an escape DC is Grappled's
        ConditionInstance(
            instance_id="x",
            condition=ConditionKind.POISONED,
            visibility=ConditionVisibility.VISIBLE,
            escape_dc=13,
        )
    with pytest.raises(ValidationError):  # hover is a fly speed's
        SpeedGrant(
            mode=MovementMode.WALK,
            feet=30,
            source=GrantSource(record_key="animals.owl"),
            hover=True,
        )
    with pytest.raises(ValidationError):  # a timed end states its length
        EffectEnd(kind=DurationKind.TIMED)
    with pytest.raises(ValidationError):
        EffectEnd(kind=DurationKind.UNTIL_DISPELLED, amount=1, unit=TimeUnit.HOUR)


def test_telepathy_is_a_sense_grant_and_effect_parameters_are_validated() -> None:
    index = real_index()
    base = complete_character(index, "classes.wizard", 1)
    hex_effect = ActiveEffect(
        instance_id="hex",
        source=GrantSource(record_key="spells.hex"),
        cast_level=1,
        concentration=True,
        selections=(VocabularyChoice(vocabulary="ability", value="wisdom"),),
        ends=EffectEnd(kind=DurationKind.TIMED, amount=1, unit=TimeUnit.HOUR),
    )
    state = base.model_copy(
        update={
            "senses": (
                SenseGrant(
                    sense_record_key="glossary.telepathy",
                    range_feet=60,
                    source=GrantSource(record_key="feats.boon_of_the_night_spirit"),
                ),
            ),
            "active_effects": (hex_effect,),
        }
    )
    assert validate_character(index, state) == ()
    bad = hex_effect.model_copy(
        update={"selections": (RecordChoice(record_key="spells.no_such_spell"),)}
    )
    state = state.model_copy(update={"active_effects": (bad,)})
    assert FailureCode.INVALID_IDENTITY in _codes(validate_character(index, state))


# ---------------------------------------------------------------------------
# Real database: parameters persist, references stay story-scoped
# ---------------------------------------------------------------------------


def _cast_member(table: Table, story: UUID) -> UUID:
    cast_id = uuid4()
    with table.factory() as s, s.begin():
        s.add(
            SBCastEntryORM(
                cast_id=str(cast_id),
                story_id=str(story),
                static_name="Brakka the Ogre",
                static_role="antagonist",
                static_traits=[],
                static_goals=[],
                static_secrets=[],
                dynamic_is_alive=True,
                is_active=True,
                created_at=datetime(2026, 10, 11, tzinfo=UTC).isoformat(),
            )
        )
    return cast_id


def test_recorded_parameters_round_trip_through_the_database(
    table: Table, srd_content: Seeder
) -> None:
    with table.factory() as s, s.begin():
        story = new_story(s)
        sheet = new_character(s, story)
        stored = service.create_character(s, sheet, table.package, wizardish(), now=NOW)
    srd_content(stored.binding)
    ogre = _cast_member(table, story)
    with table.factory() as s, s.begin():
        index = holdings.holder_authority(
            s, Holder(HolderKind.CHARACTER, sheet), now=NOW
        )
        ring = holdings.create_item(
            s,
            index,
            Holder(HolderKind.CHARACTER, sheet),
            "magic_items.ring_of_feather_falling",
            now=NOW,
        )
    me = SubjectReference(kind="character", subject_id=sheet)
    state = wizardish(
        hit_points=HitPoints(
            current=6,
            maximum=9,
            temporary=4,
            maximum_reduction=3,
            temporary_source=GrantSource(record_key="spells.false_life"),
        ),
        conditions=(
            ConditionInstance(
                instance_id="grappled",
                condition=ConditionKind.GRAPPLED,
                visibility=ConditionVisibility.VISIBLE,
                source=GrantSource(record_key="glossary.grappled"),
                referent=SubjectReference(kind="cast_member", subject_id=ogre),
                escape_dc=14,
            ),
            ConditionInstance(
                instance_id="hidden",
                condition=ConditionKind.INVISIBLE,
                visibility=ConditionVisibility.VISIBLE,
                source=GrantSource(record_key="glossary.hide"),
                recorded_check_total=17,
            ),
        ),
        active_effects=(
            ActiveEffect(
                instance_id="hex",
                source=GrantSource(record_key="spells.hex"),
                cast_level=1,
                concentration=True,
                caster=me,
                targets=(SubjectReference(kind="cast_member", subject_id=ogre),),
                selections=(VocabularyChoice(vocabulary="ability", value="strength"),),
                ends=EffectEnd(
                    kind=DurationKind.TIMED,
                    amount=1,
                    unit=TimeUnit.HOUR,
                    expires_marker="day-2 dusk",
                ),
            ),
            ActiveEffect(
                instance_id="curse",
                source=GrantSource(record_key="magic_items.cursed_items"),
                concentration=False,
                item_id=ring.item_id,
                curse=True,
                ends=EffectEnd(kind=DurationKind.UNTIL_DISPELLED),
            ),
        ),
        usage_counters=(
            UsageCounter(
                counter_id="ring-use",
                source=GrantSource(record_key="magic_items.ring_of_feather_falling"),
                item_id=ring.item_id,
                expended=0,
            ),
        ),
    )
    with table.factory() as s, s.begin():
        service.update_character(s, sheet, state, expected_revision=1, now=NOW)
    with table.factory() as s:
        assert service.read_character(s, sheet).state == state


def test_references_outside_the_story_are_refused(table: Table) -> None:
    with table.factory() as s, s.begin():
        story, elsewhere = new_story(s), new_story(s)
        sheet = new_character(s, story)
        stranger = new_character(s, elsewhere, "Stranger")
        service.create_character(s, sheet, table.package, wizardish(), now=NOW)
    outsider = _cast_member(table, elsewhere)
    for bad in (
        ConditionInstance(
            instance_id="charmed",
            condition=ConditionKind.CHARMED,
            visibility=ConditionVisibility.VISIBLE,
            referent=SubjectReference(kind="cast_member", subject_id=outsider),
        ),
        ConditionInstance(
            instance_id="frightened",
            condition=ConditionKind.FRIGHTENED,
            visibility=ConditionVisibility.VISIBLE,
            referent=SubjectReference(kind="character", subject_id=stranger),
        ),
        ConditionInstance(
            instance_id="cursed",
            condition=ConditionKind.POISONED,
            visibility=ConditionVisibility.VISIBLE,
            item_id=uuid4(),
        ),
    ):
        with (
            table.factory() as s,
            s.begin(),
            pytest.raises(InvalidStateError) as refused,
        ):
            service.update_character(
                s, sheet, wizardish(conditions=(bad,)), expected_revision=1, now=NOW
            )
        assert refused.value.failures[0].code is FailureCode.INVALID_IDENTITY
    with table.factory() as s:
        assert service.read_character(s, sheet).revision == 1


def test_a_familiar_records_its_chosen_type_speed_and_presence(table: Table) -> None:
    from tests.services.rules_authority.conftest import CREATURE_KEY, SPELL_KEY

    with table.factory() as s, s.begin():
        story, elsewhere = new_story(s), new_story(s)
        sheet = new_character(s, story)
        stranger = new_character(s, elsewhere)
        familiar = CreatureState(
            template_record_key=CREATURE_KEY,
            hit_points=HitPoints(current=1, maximum=1, temporary=0),
            conditions=(),
            active_effects=(),
            creature_type=CreatureType.FEY,
            speeds=(
                SpeedGrant(
                    mode=MovementMode.FLY,
                    feet=40,
                    source=GrantSource(record_key=SPELL_KEY),
                    hover=False,
                ),
            ),
            presence=CreaturePresence.POCKET_DIMENSION,
            summon=SummonOrigin(
                source=GrantSource(record_key=SPELL_KEY),
                summoner_subject=sheet,
                controller_subject=sheet,
            ),
        )
        created = service.create_creature(
            s, story, "Familiar", table.package, familiar, now=NOW
        )
        # Advisor: summon references are story-scoped too.
        foreign = familiar.model_copy(
            update={
                "summon": SummonOrigin(
                    source=GrantSource(record_key=SPELL_KEY), summoner_subject=stranger
                )
            }
        )
        with pytest.raises(InvalidStateError):
            service.create_creature(s, story, "Stray", table.package, foreign, now=NOW)
    with table.factory() as s:
        assert service.read_creature(s, created.creature_id).state == familiar


def test_a_selected_base_armor_class_source_is_validated() -> None:
    index = real_index()
    state = complete_character(index, "classes.wizard", 1)
    ok = state.model_copy(
        update={
            "base_armor_class": BaseArmorClass(
                source=GrantSource(record_key="spells.mage_armor")
            )
        }
    )
    assert validate_character(index, ok) == ()
    bad = state.model_copy(
        update={
            "base_armor_class": BaseArmorClass(
                source=GrantSource(record_key="spells.no_armor")
            )
        }
    )
    assert FailureCode.INVALID_IDENTITY in _codes(validate_character(index, bad))
