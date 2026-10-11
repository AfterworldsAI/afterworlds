"""A field's identity domain is narrower than its record kind (CRD Issue 2b).

Defect family (Codex final review): a broad accepted record kind mistaken for
a field's narrower structural identity domain. A weapon proficiency names a
weapon (a record the accepted authority states a weapon category for), a tool
proficiency names a member of the accepted Tools catalogue, and a sense grant
names a special sense the source defines, or Telepathy. Identity only: who may
hold the grant is not 2b's.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from pathlib import Path

import pytest

from afterworlds.ingestion.mechanical.representation import WeaponCategory
from afterworlds.models.dnd5e_state import (
    GrantSource,
    SenseGrant,
    ToolGrant,
    WeaponProficiencyGrant,
)
from afterworlds.services.dnd5e_state import adoption, service, store
from afterworlds.services.dnd5e_state.adoption import AdoptionStatus
from afterworlds.services.dnd5e_state.authority import current_binding
from afterworlds.services.dnd5e_state.errors import FailureCode, InvalidStateError
from afterworlds.services.dnd5e_state.shared_changes import ChangeStatus
from afterworlds.services.dnd5e_state.validation import (
    SENSE_RECORDS,
    validate_character,
)
from tests.services.dnd5e_state.builders import complete_character, real_index
from tests.services.dnd5e_state.conftest import (
    NOW,
    Table,
    new_character,
    new_story,
    wizardish,
)
from tests.services.dnd5e_state.test_hold_and_adoption import (
    HOUSE_RULE,
    _activate,
    _request,
)

Seeder = Callable[..., None]
FIGHTER = GrantSource(record_key="classes.fighter")
SRD = Path(__file__).resolve().parents[3] / "docs/sources/community/dnd-5e-srd-markdown"

ARMOR_AS_WEAPON = WeaponProficiencyGrant(
    weapon_record_key="equipment.armor.scale_mail", source=FIGHTER
)
WEAPON_AS_TOOL = ToolGrant(
    record_key="equipment.weapons.dart", expertise=False, source=FIGHTER
)
RULE_AS_SENSE = SenseGrant(
    sense_record_key="glossary.burning", range_feet=30, source=FIGHTER
)


def _fighter():  # type: ignore[no-untyped-def]
    index = real_index()
    state = complete_character(index, "classes.fighter", 1)
    assert validate_character(index, state) == ()
    return index, state


@pytest.mark.parametrize(
    ("field", "grant"),
    [
        ("weapon_proficiencies", ARMOR_AS_WEAPON),
        ("tool_proficiencies", WEAPON_AS_TOOL),
        ("senses", RULE_AS_SENSE),
    ],
    ids=["armor-as-weapon", "weapon-as-tool", "rule-as-sense"],
)
def test_an_identity_outside_the_fields_domain_is_wrong_kind(
    field: str, grant: object
) -> None:
    index, state = _fighter()
    failures = validate_character(index, state.model_copy(update={field: (grant,)}))
    assert [f.code for f in failures] == [FailureCode.WRONG_KIND]


def test_every_srd_weapon_category_tool_and_sense_stays_valid() -> None:
    index, state = _fighter()
    weapons = sorted(
        k for k in index.members["equipment.weapons"]
        if validate_character(
            index,
            state.model_copy(update={"weapon_proficiencies": (
                WeaponProficiencyGrant(weapon_record_key=k, source=FIGHTER),
            )}),
        ) == ()
    )  # fmt: skip
    assert len(weapons) == 38  # the SRD weapon table; rule records excluded
    grants = state.model_copy(
        update={
            "weapon_proficiencies": (
                WeaponProficiencyGrant(category=WeaponCategory.MARTIAL, source=FIGHTER),
                WeaponProficiencyGrant(
                    weapon_record_key="equipment.weapons.war_pick", source=FIGHTER
                ),
            ),
            "tool_proficiencies": (
                ToolGrant(
                    record_key="equipment.tools.gaming_set",
                    component_key="gaming_set",
                    expertise=False,
                    source=FIGHTER,
                ),
                ToolGrant(
                    record_key="equipment.tools.thieves_tools",
                    expertise=True,
                    source=FIGHTER,
                ),
            ),
            "senses": tuple(
                SenseGrant(sense_record_key=k, range_feet=60, source=FIGHTER)
                for k in sorted(SENSE_RECORDS)
            ),
        }
    )
    assert validate_character(index, grants) == ()
    empty = state.model_copy(
        update={"weapon_proficiencies": (), "tool_proficiencies": (), "senses": ()}
    )
    assert validate_character(index, empty) == ()


def test_the_sense_domain_is_the_sources_special_senses_and_telepathy() -> None:
    text = (SRD / "playing-the-game.md").read_text("utf-8")
    start = text.index("#### Special Senses")
    listed = re.findall(r"^- (\w+)$", text[start : text.index("###", start + 5)], re.M)
    assert {f"glossary.{n.lower()}" for n in listed} | {"glossary.telepathy"} == (
        SENSE_RECORDS
    )


def test_a_wrong_domain_grant_is_refused_by_the_service_and_by_adoption(
    table: Table, srd_content: Seeder
) -> None:
    with table.factory() as s, s.begin():
        sheet = new_character(s, new_story(s))
        stored = service.create_character(s, sheet, table.package, wizardish(), now=NOW)
    srd_content(stored.binding)
    with table.factory() as s, s.begin(), pytest.raises(InvalidStateError) as refused:
        service.update_character(
            s,
            sheet,
            wizardish(weapon_proficiencies=(ARMOR_AS_WEAPON,)),
            expected_revision=1,
            now=NOW,
        )
    assert refused.value.failures[0].code is FailureCode.WRONG_KIND
    # A record written before the domain check existed: adoption still refuses
    # rather than carrying the false identity to a new binding.
    with table.factory() as s, s.begin():
        store.save_state(
            s,
            "character",
            sheet,
            wizardish(tool_proficiencies=(WEAPON_AS_TOOL,)),
            expected_revision=1,
            expected_binding=stored.binding,
            now=NOW,
        )
    change = _request(table, HOUSE_RULE)
    assert _activate(table, change).status is ChangeStatus.ACTIVE
    with table.factory() as s, s.begin():  # resolution retains the version
        target = current_binding(s, table.package, now=NOW)
    srd_content(target)
    with table.factory() as s, s.begin():
        outcome = adoption.request_adoption(
            s, "character", sheet, change_id=change, now=NOW
        )
    assert outcome.status is AdoptionStatus.REFUSED
    assert outcome.reason is not None and "is not a tool" in outcome.reason
    with table.factory() as s:
        assert service.read_character(s, sheet).binding == stored.binding
