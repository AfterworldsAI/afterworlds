"""The built-app proof's scripted GM-led composer (``scripts/e2e_gm_led.py``):
it proposes only what the Sojourner stated, and clarifies everything else."""

from __future__ import annotations

from afterworlds.models.dnd5e_state import Dnd5eCharacterState
from afterworlds.services.dnd5e_state.validation import (
    character_readiness,
    validate_character,
)
from scripts.e2e_gm_led import REQUIRED, compose, responder
from tests.services.dnd5e_state.builders import complete_character, real_index

_STATED = [
    "Player: Class: wizard. Background: sage.",
    "Player: Species: elf. Lineage: high elf. Lineage ability: intelligence. "
    "Alignment: neutral good.",
    "Player: Ability scores: standard array, Str 8 Dex 14 Con 13 Int 15 Wis 12 "
    "Cha 10. Cantrip: fire bolt. Equipment: 15 gp. Backstory hooks: owes the "
    "Lamplighters a debt, hunts a drowned library.",
]


def test_missing_choices_are_asked_for_never_filled() -> None:
    character, questions = compose([_STATED[0]], real_index())
    assert character is None
    asked = " ".join(questions)
    for label in REQUIRED[2:]:
        assert f"your {label}?" in asked


def test_ambiguous_or_unsupported_choices_are_clarified() -> None:
    wrong = [
        *_STATED[:2],
        "Player: Ability scores: standard array, Str 8 Dex 14 Con 13 Int 15 Wis 12"
        " Cha 13. Cantrip: fire bolt. Equipment: 15 gp. Backstory hooks: a debt.",
    ]
    character, questions = compose(wrong, real_index())
    assert character is None
    assert any("once each" in q for q in questions)
    dwarf = [s.replace("Species: elf", "Species: dwarf") for s in _STATED]
    character, questions = compose(dwarf, real_index())
    assert character is None and any("'dwarf'" in q for q in questions)


def test_stated_choices_compose_a_valid_ready_character() -> None:
    index = real_index()
    character, questions = compose(_STATED, index)
    assert questions == [] and character is not None
    state = Dnd5eCharacterState.model_validate(character)
    assert validate_character(index, state) == ()
    assert character_readiness(index, state) == ()
    # Nothing beyond the stated choices and their rules consequences.
    assert state == complete_character(index, "classes.wizard", 1)


def test_different_stated_values_are_what_is_proposed() -> None:
    index = real_index()
    stated = [
        s.replace("Con 13 Int 15", "Con 15 Int 13").replace("15 gp", "12 gp")
        for s in _STATED
    ]
    character, _ = compose(stated, index)
    assert character is not None
    state = Dnd5eCharacterState.model_validate(character)
    assert state.ability_scores is not None
    assert (state.ability_scores.constitution, state.ability_scores.intelligence) == (
        15,
        13,
    )
    assert state.hit_points is not None and state.hit_points.maximum == 8
    assert validate_character(index, state) == ()


def test_responder_only_answers_gm_led_character_creation() -> None:
    respond = responder(real_index())
    assert respond(["phase: world_setup", *_STATED]) is None
    asked = respond(["phase: character_creation\nrules_package: SRD", _STATED[0]])
    assert asked is not None and asked.tool_input is not None
    assert asked.tool_input["result"]["kind"] == "clarification"
    proposed = respond(["phase: character_creation\nrules_package: SRD", *_STATED])
    assert proposed is not None and proposed.tool_input is not None
    assert proposed.tool_input["result"]["path"] == "gm_led"
    assert "hunts a drowned library" in proposed.tool_input["gm_text"]
