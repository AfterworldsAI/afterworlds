"""Hazard inputs and familiar completeness (CRD Issue 2b, Codex review).

Hazards persist the inputs the source says to track (inventory
``glossary-play-spells.md`` dehydration, malnutrition, suffocation, burning;
``remaining-records.md`` magical contagions), each sourced from its accepted
record. What they cause is 15c's. A Find Familiar familiar must record its
chosen creature type and presence before it is ready.
"""

from __future__ import annotations

from collections.abc import Callable
from decimal import Decimal

import pytest
from pydantic import ValidationError

from afterworlds.ingestion.mechanical.representation import ConditionKind, TimeUnit
from afterworlds.models.dnd5e_state import (
    BurningHazard,
    ConditionInstance,
    ContagionHazard,
    CreaturePresence,
    CreatureState,
    DehydrationHazard,
    GrantSource,
    HitPoints,
    MalnutritionHazard,
    SuffocationHazard,
    SummonOrigin,
)
from afterworlds.models.dnd5e_vocabulary import CreatureType
from afterworlds.models.enums import ConditionVisibility
from afterworlds.services.dnd5e_state import service
from afterworlds.services.dnd5e_state.errors import FailureCode
from afterworlds.services.dnd5e_state.validation import (
    character_readiness,
    creature_readiness,
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

Seeder = Callable[..., None]
CACKLE = "gameplay_toolbox.curses_and_magical_contagions.cackle_fever"
SIGHT_ROT = "gameplay_toolbox.curses_and_magical_contagions.sight_rot"


def _src(key: str) -> GrantSource:
    return GrantSource(record_key=key)


HAZARDS = (
    BurningHazard(source=_src("glossary.burning"), started_marker="round 3"),
    DehydrationHazard(
        source=_src("glossary.dehydration"),
        day_marker="day 4",
        water_gallons=Decimal("0.25"),
    ),
    MalnutritionHazard(
        source=_src("glossary.malnutrition"),
        day_marker="day 4",
        food_pounds=Decimal("0"),
        days_without_food=3,
    ),
    SuffocationHazard(
        source=_src("glossary.suffocation"),
        breath_remaining=2,
        breath_unit=TimeUnit.MINUTE,
        suffocating=False,
    ),
    ContagionHazard(
        source=_src(CACKLE),
        infected_marker="day 1",
        onset_marker="day 3",
        successful_saves=1,
    ),
    ContagionHazard(
        source=_src(SIGHT_ROT),
        infected_marker="day 2",
        successful_saves=0,
        suppression_hours=24,
        cured_marker="day 6",
    ),
)
#: Exhaustion a hazard caused names the hazard, so per-source removal works.
DEHYDRATED = ConditionInstance(
    instance_id="ex-dehydration",
    condition=ConditionKind.EXHAUSTION,
    visibility=ConditionVisibility.VISIBLE,
    level=1,
    source=_src("glossary.dehydration"),
)


def test_hazard_inputs_round_trip_and_update_on_a_real_database(
    table: Table, srd_content: Seeder
) -> None:
    with table.factory() as s, s.begin():
        sheet = new_character(s, new_story(s))
        stored = service.create_character(s, sheet, table.package, wizardish(), now=NOW)
    srd_content(stored.binding)
    state = wizardish(hazards=HAZARDS, conditions=(DEHYDRATED,))
    with table.factory() as s, s.begin():
        service.update_character(s, sheet, state, expected_revision=1, now=NOW)
    with table.factory() as s:
        assert service.read_character(s, sheet).state == state
    drank = (
        HAZARDS[1].model_copy(update={"water_gallons": Decimal("1")}),
        *HAZARDS[2:],
    )
    with table.factory() as s, s.begin():
        service.update_character(
            s,
            sheet,
            state.model_copy(update={"hazards": drank}),
            expected_revision=2,
            now=NOW,
        )
    with table.factory() as s:
        read = service.read_character(s, sheet)
    assert read.revision == 3
    assert read.state.hazards == drank  # burning ended; nothing else changed
    assert read.state.conditions == (DEHYDRATED,)


def test_missing_hazards_are_not_ready_and_explicit_none_is() -> None:
    index = real_index()
    state = complete_character(index, "classes.wizard", 1)
    assert character_readiness(index, state) == ()
    missing = state.model_copy(update={"hazards": None})
    assert [f.path for f in character_readiness(index, missing)] == ["hazards"]
    recorded = state.model_copy(update={"hazards": HAZARDS})
    assert validate_character(index, recorded) == ()


@pytest.mark.parametrize(
    "hazard",
    [
        DehydrationHazard(
            source=_src("glossary.burning"), day_marker="d", water_gallons=Decimal(1)
        ),
        ContagionHazard(
            source=_src("glossary.burning"), infected_marker="d", successful_saves=0
        ),
        BurningHazard(source=_src("glossary.no_such_hazard")),
    ],
    ids=["wrong-record", "not-a-contagion", "unknown-record"],
)
def test_a_hazard_sourced_from_the_wrong_record_is_refused(hazard: object) -> None:
    index = real_index()
    state = complete_character(index, "classes.wizard", 1).model_copy(
        update={"hazards": (hazard,)}
    )
    codes = {f.code for f in validate_character(index, state)}
    assert codes & {FailureCode.WRONG_KIND, FailureCode.INVALID_IDENTITY}


def test_hazard_input_structure_is_enforced() -> None:
    with pytest.raises(ValidationError):
        DehydrationHazard(
            source=_src("glossary.dehydration"),
            day_marker="d",
            water_gallons=Decimal("-1"),
        )
    with pytest.raises(ValidationError):
        SuffocationHazard(
            source=_src("glossary.suffocation"), breath_remaining=1, suffocating=False
        )
    with pytest.raises(ValidationError):
        MalnutritionHazard(
            source=_src("glossary.malnutrition"),
            day_marker="d",
            food_pounds=Decimal(0),
            days_without_food=-1,
        )


def _familiar(**updates: object) -> CreatureState:
    return CreatureState(
        template_record_key="animals.owl",
        hit_points=HitPoints(current=1, maximum=1, temporary=0),
        conditions=(),
        active_effects=(),
        hazards=(),
        summon=SummonOrigin(source=_src("spells.find_familiar")),
    ).model_copy(update=updates)


@pytest.mark.parametrize(
    "source",
    [
        "spells.find_familiar",
        "classes.druid.wild_companion",
        "classes.warlock.eldritch_invocation_options.pact_of_the_chain",
    ],
)
def test_a_familiar_without_its_chosen_type_or_presence_is_not_ready(
    source: str,
) -> None:
    familiar = _familiar(summon=SummonOrigin(source=_src(source)))
    assert {f.path for f in creature_readiness(familiar)} == {
        "creature_type",
        "presence",
    }
    complete = familiar.model_copy(
        update={
            "creature_type": CreatureType.FEY,
            "presence": CreaturePresence.PRESENT,
        }
    )
    assert creature_readiness(complete) == ()


def test_a_summon_that_is_not_a_familiar_needs_no_familiar_state() -> None:
    steed = _familiar(summon=SummonOrigin(source=_src("spells.find_steed")))
    assert creature_readiness(steed) == ()
    assert [
        f.path for f in creature_readiness(steed.model_copy(update={"hazards": None}))
    ] == ["hazards"]
