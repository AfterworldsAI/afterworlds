"""2b state against the committed accepted authority (no database).

Every class, multiclassing, distinct spell pools, sourced choices, missing
versus explicitly empty state, and the typed failures: invalid identities,
wrong kinds, violated structured bounds and changed choice schemas.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from afterworlds.ingestion.mechanical.representation import (
    ConditionKind,
    DieSize,
    WeaponCategory,
)
from afterworlds.models.dnd5e_state import (
    ActiveEffect,
    ClassLevel,
    ConditionInstance,
    Dnd5eCharacterState,
    GrantSource,
    HitPoints,
    SlotLevel,
    SpellAccess,
    SpellSlotPool,
    UsageCounter,
    WeaponProficiencyGrant,
)
from afterworlds.models.enums import ConditionVisibility
from afterworlds.services.dnd5e_state.errors import FailureCode
from afterworlds.services.dnd5e_state.validation import (
    character_readiness,
    validate_character,
)
from tests.services.dnd5e_state.builders import (
    CLASSES,
    complete_character,
    counters_for,
    real_index,
    slots_for,
)

G1_WEAPONS = (
    "dart",
    "glaive",
    "halberd",
    "lance",
    "maul",
    "trident",
    "war_pick",
    "whip",
    "blowgun",
)


def _codes(state: Dnd5eCharacterState) -> list[tuple[FailureCode, str]]:
    index = real_index()
    return [
        (f.code, f.path)
        for f in validate_character(index, state) + character_readiness(index, state)
    ]


@pytest.mark.parametrize("level", (1, 3, 5, 20))
@pytest.mark.parametrize(
    ("class_key", "subclass", "die"), CLASSES, ids=[c[0] for c in CLASSES]
)
def test_every_class_is_complete_and_valid_at_every_tier(
    class_key: str, subclass: str, die: DieSize, level: int
) -> None:
    state = complete_character(
        real_index(),
        class_key,
        level,
        subclass=subclass if level >= 3 else None,
        hit_die=die,
    )
    assert _codes(state) == []


def test_a_multiclass_character_keeps_each_class_and_spell_pool_distinct() -> None:
    index = real_index()
    base = complete_character(
        index, "classes.wizard", 3, subclass="classes.wizard.evoker"
    )
    cleric = slots_for(index, "classes.cleric", 2)
    state = base.model_copy(
        update={
            "classes": (
                *base.classes,  # type: ignore[misc]
                ClassLevel(
                    class_record_key="classes.cleric", level=2, hit_die=DieSize.D8
                ),
            ),
            "level_history": ("classes.wizard",) * 3 + ("classes.cleric",) * 2,
            "usage_counters": counters_for(index, "classes.wizard", 3)
            + counters_for(index, "classes.cleric", 2),
            # A multiclass caster's combined slots are stored as recorded.
            "spell_slot_pools": (
                SpellSlotPool(
                    pool_id="spellcasting",
                    source=GrantSource(record_key="classes.wizard"),
                    levels=(
                        SlotLevel(level=1, total=4, expended=1),
                        SlotLevel(level=2, total=3, expended=0),
                        SlotLevel(level=3, total=2, expended=0),
                    ),
                ),
            ),
            "spell_access": (
                SpellAccess(
                    pool_id="classes.wizard:spells",
                    spell_record_key="spells.magic_missile",
                    mode="spellbook",
                    source=GrantSource(record_key="classes.wizard"),
                ),
                SpellAccess(
                    pool_id="classes.cleric:spells",
                    spell_record_key="spells.cure_wounds",
                    mode="prepared",
                    source=GrantSource(record_key="classes.cleric"),
                ),
            ),
        }
    )
    state = Dnd5eCharacterState.model_validate(state.model_dump())
    assert cleric  # the cleric has a structured slot table of its own
    assert _codes(state) == []
    assert {a.pool_id for a in state.spell_access or ()} == {
        "classes.wizard:spells",
        "classes.cleric:spells",
    }


def test_pact_magic_stays_a_pool_of_its_own() -> None:
    index = real_index()
    state = complete_character(index, "classes.warlock", 5)
    (pool,) = state.spell_slot_pools or ()
    assert pool.pool_id == "pact_magic"
    assert _codes(state) == []


def test_concurrent_effects_are_separate_instances() -> None:
    index = real_index()
    effect = ActiveEffect(
        instance_id="bless-1",
        source=GrantSource(record_key="spells.bless"),
        cast_level=1,
        concentration=True,
    )
    state = complete_character(index).model_copy(
        update={
            "active_effects": (
                effect,
                effect.model_copy(
                    update={"instance_id": "bless-2", "concentration": False}
                ),
            )
        }
    )
    assert _codes(state) == []
    with pytest.raises(ValidationError, match="repeats an identifier"):
        Dnd5eCharacterState.model_validate(
            {**state.model_dump(), "active_effects": [effect.model_dump()] * 2}
        )


def test_missing_state_is_a_typed_failure_and_explicit_empty_is_valid() -> None:
    index = real_index()
    empty = complete_character(index).model_copy(
        update={"conditions": (), "feats": (), "heroic_inspiration": False}
    )
    assert _codes(empty) == []
    missing = empty.model_copy(update={"hit_points": None, "feats": None})
    assert _codes(missing) == [
        (FailureCode.MISSING_STATE, "feats"),
        (FailureCode.MISSING_STATE, "hit_points"),
    ]


def test_a_structured_usage_entitlement_must_be_recorded() -> None:
    state = complete_character(
        real_index(), "classes.barbarian", 3, hit_die=DieSize.D12
    )
    without = state.model_copy(update={"usage_counters": ()})
    assert (
        FailureCode.MISSING_STATE,
        "usage_counters[classes.barbarian:rages]",
    ) in _codes(without)


def test_invalid_identities_and_wrong_kinds_are_typed() -> None:
    state = complete_character(real_index())
    assert state.species is not None and state.background is not None
    kender = state.species.model_copy(update={"record_key": "character_origins.kender"})
    assert _codes(state.model_copy(update={"species": kender})) == [
        (FailureCode.INVALID_IDENTITY, "species")
    ]
    wizard = state.background.model_copy(update={"record_key": "classes.wizard"})
    assert _codes(state.model_copy(update={"background": wizard})) == [
        (FailureCode.WRONG_KIND, "background")
    ]


def test_a_subclass_must_be_catalogued_under_its_class() -> None:
    state = complete_character(
        real_index(), "classes.wizard", 3, subclass="classes.cleric.life_domain"
    )
    assert _codes(state) == [(FailureCode.INCONSISTENT, "classes[classes.wizard]")]


def test_a_usage_maximum_must_equal_the_structured_entitlement() -> None:
    index = real_index()
    state = complete_character(index, "classes.barbarian", 3, hit_die=DieSize.D12)
    (rages,) = [c for c in state.usage_counters or () if c.entitlement_key == "rages"]
    wrong = rages.model_copy(update={"maximum": 9})
    state = state.model_copy(update={"usage_counters": (wrong,)})
    assert (
        FailureCode.BOUND_EXCEEDED,
        f"usage_counters[{rages.counter_id}]",
    ) in _codes(state)
    known = UsageCounter(
        counter_id="cantrips",
        source=GrantSource(record_key="classes.barbarian"),
        entitlement_key="cantrips",
        maximum=3,
        expended=0,
    )
    assert (FailureCode.INVALID_IDENTITY, "usage_counters[cantrips]") in _codes(
        state.model_copy(update={"usage_counters": (rages, known)})
    )


def test_single_class_slot_totals_must_equal_the_structured_table() -> None:
    state = complete_character(real_index(), "classes.wizard", 5)
    (pool,) = state.spell_slot_pools or ()
    inflated = pool.model_copy(
        update={"levels": (SlotLevel(level=1, total=9, expended=0), *pool.levels[1:])}
    )
    assert _codes(state.model_copy(update={"spell_slot_pools": (inflated,)})) == [
        (FailureCode.BOUND_EXCEEDED, f"spell_slot_pools[{pool.pool_id}]")
    ]


def test_a_choice_made_under_a_changed_source_schema_is_refused() -> None:
    state = complete_character(real_index())
    (choice,) = state.choices or ()
    stale = choice.model_copy(update={"schema_id": "0" * 64})
    assert _codes(state.model_copy(update={"choices": (stale,)})) == [
        (FailureCode.SCHEMA_CHANGED, "choices[elf-lineage]")
    ]


@pytest.mark.parametrize("weapon", G1_WEAPONS)
def test_the_g1_weapons_are_accepted_proficiency_identities(weapon: str) -> None:
    state = complete_character(real_index())
    grant = WeaponProficiencyGrant(
        weapon_record_key=f"equipment.weapons.{weapon}",
        source=GrantSource(record_key="classes.wizard"),
    )
    assert _codes(state.model_copy(update={"weapon_proficiencies": (grant,)})) == []


# -- the typed model itself ---------------------------------------------------


def test_current_hit_points_have_no_floor_but_never_exceed_the_maximum() -> None:
    assert HitPoints(current=-12, maximum=7, temporary=0).current == -12
    with pytest.raises(ValidationError, match="cannot exceed maximum"):
        HitPoints(current=8, maximum=7, temporary=0)


def test_a_fresh_document_manufactures_no_state() -> None:
    state = Dnd5eCharacterState()
    assert all(
        getattr(state, name) is None
        for name in Dnd5eCharacterState.model_fields
        if name != "state_schema_version"
    )


def test_closed_vocabularies_refuse_free_text() -> None:
    source = {"record_key": "x"}
    with pytest.raises(ValidationError):
        Dnd5eCharacterState.model_validate(
            {"languages": [{"language": "klingon", "source": source}]}
        )
    with pytest.raises(ValidationError, match="names a category or a weapon"):
        WeaponProficiencyGrant(
            category=WeaponCategory.SIMPLE,
            weapon_record_key="equipment.weapons.dart",
            source=GrantSource(record_key="x"),
        )


def test_structural_integrity_rules() -> None:
    with pytest.raises(ValidationError, match="records its level"):
        ConditionInstance(
            instance_id="e",
            condition=ConditionKind.EXHAUSTION,
            visibility=ConditionVisibility.VISIBLE,
        )
    with pytest.raises(ValidationError, match="exceeds total"):
        SlotLevel(level=1, total=2, expended=3)
    with pytest.raises(ValidationError, match="level_history"):
        Dnd5eCharacterState(
            classes=(
                ClassLevel(
                    class_record_key="classes.wizard", level=2, hit_die=DieSize.D6
                ),
            ),
            level_history=("classes.wizard",),
        )
    with pytest.raises(ValidationError, match="at most 20 levels"):
        Dnd5eCharacterState(
            classes=(
                ClassLevel(
                    class_record_key="classes.wizard", level=15, hit_die=DieSize.D6
                ),
                ClassLevel(
                    class_record_key="classes.cleric", level=6, hit_die=DieSize.D8
                ),
            )
        )
    with pytest.raises(ValidationError, match="cited but not recorded"):
        Dnd5eCharacterState(
            weapon_proficiencies=(
                WeaponProficiencyGrant(
                    category=WeaponCategory.MARTIAL,
                    source=GrantSource(record_key="classes.fighter", choice_id="ghost"),
                ),
            ),
            choices=(),
        )
