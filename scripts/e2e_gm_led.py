"""Scripted GM-led character creation for the built-app proof (test double).

PR #204 P1: the GM-led browser path must build its proposal only from what
the Sojourner supplied or explicitly stated in the setup conversation. This
responder reads the ``Player:`` lines the setup Writer request renders,
collects labelled choices (``Class: wizard.``), asks again for anything
missing or ambiguous, and otherwise proposes a typed character whose every
recorded choice is one the Sojourner stated. Values derived by the rules from
those choices (saving throws, background grants, speeds, hit points) are
rendered from authority, not chosen. It is transport data like any scripted
reply: code still validates and binds the proposal on Accept character.

Scope is deliberately narrow (one supported build path, no general builder):
a choice outside it is answered with a clarification, never substituted.
"""

from __future__ import annotations

import re
from typing import Any

from scripts.scripted_provider import Reply

#: Labelled choices, in the order the GM asks for them. Backstory hooks are
#: narrative (Story Bible), not sheet fields: collected and acknowledged here.
REQUIRED = (
    "class",
    "background",
    "species",
    "lineage",
    "lineage ability",
    "alignment",
    "ability scores",
    "cantrip",
    "equipment",
    "backstory hooks",
)
_SUPPORTED = {
    "class": {"wizard": "classes.wizard"},
    "background": {"sage": "character_origins.sage"},
    "species": {"elf": "character_origins.elf"},
    "lineage": {"high elf": "high_elf", "wood elf": "wood_elf", "drow": "drow"},
    "lineage ability": {a: a for a in ("intelligence", "wisdom", "charisma")},
    "cantrip": {"fire bolt": "spells.fire_bolt"},
}
_ABILITIES = ("str", "dex", "con", "int", "wis", "cha")
_STANDARD_ARRAY = [8, 10, 12, 13, 14, 15]
_LABEL = re.compile(
    r"(" + "|".join(sorted(REQUIRED, key=len, reverse=True)) + r")\s*:\s*([^.;\n]+)",
    re.IGNORECASE,
)


def stated_choices(texts: list[str]) -> dict[str, str]:
    """The latest value the Sojourner gave for each label, in their words."""
    found: dict[str, str] = {}
    for text in texts:
        for line in text.splitlines():
            if not line.startswith("Player: "):
                continue
            for label, value in _LABEL.findall(line.removeprefix("Player: ")):
                found[label.lower()] = value.strip()
    return found


def _scores(value: str) -> tuple[dict[str, int] | None, str | None]:
    if not value.lower().startswith("standard array"):
        return None, "Which method? I can use the standard array or results you supply."
    pairs = dict(re.findall(r"\b(str|dex|con|int|wis|cha)\s+(\d+)", value.lower()))
    if set(pairs) != set(_ABILITIES):
        return None, "Assign a standard-array score to each of the six abilities."
    scores = {k: int(v) for k, v in pairs.items()}
    if sorted(scores.values()) != _STANDARD_ARRAY:
        return None, "The standard array uses 15, 14, 13, 12, 10 and 8 once each."
    return scores, None


def compose(texts: list[str], index: Any) -> tuple[dict[str, Any] | None, list[str]]:
    """``(character, [])`` from the stated choices, or ``(None, questions)``."""
    from afterworlds.models.dnd5e_state import (
        Currency,
        Dnd5eAbilityScores,
        HitPoints,
        SpellAccess,
        VocabularyChoice,
    )
    from afterworlds.models.dnd5e_vocabulary import Alignment
    from tests.services.dnd5e_state.builders import choice, complete_character

    stated = stated_choices(texts)
    questions = [f"What is your {label}?" for label in REQUIRED if label not in stated]
    picked: dict[str, str] = {}
    for label, options in _SUPPORTED.items():
        if label in stated:
            key = options.get(stated[label].lower())
            if key is None:
                questions.append(
                    f"I can't build {label} {stated[label]!r} here; choose one of: "
                    + ", ".join(options)
                    + "."
                )
            else:
                picked[label] = key
    alignment = None
    if "alignment" in stated:
        try:
            alignment = Alignment(stated["alignment"].lower().replace(" ", "_"))
        except ValueError:
            questions.append(f"{stated['alignment']!r} is not one of the alignments.")
    scores, problem = _scores(stated.get("ability scores", "standard array"))
    if "ability scores" in stated and problem:
        questions.append(problem)
    gold = re.fullmatch(r"(\d+)\s*gp", stated.get("equipment", "").lower())
    if "equipment" in stated and gold is None:
        questions.append("For equipment, take the starting gold as '<amount> gp'.")
    if questions or scores is None or alignment is None or gold is None:
        return None, questions

    base = complete_character(index, picked["class"], 1)
    elf, cls = picked["species"], picked["class"]
    con_mod = (scores["con"] - 10) // 2
    character = base.model_copy(
        update={
            "alignment": alignment,
            "ability_scores": Dnd5eAbilityScores(
                strength=scores["str"],
                dexterity=scores["dex"],
                constitution=scores["con"],
                intelligence=scores["int"],
                wisdom=scores["wis"],
                charisma=scores["cha"],
            ),
            "choices": (
                choice(
                    index,
                    "elf-lineage",
                    elf,
                    "elven_lineage",
                    VocabularyChoice(
                        vocabulary="elven_lineage", value=picked["lineage"]
                    ),
                    VocabularyChoice(
                        vocabulary="ability", value=picked["lineage ability"]
                    ),
                ),
            ),
            # Wizard level 1: the d6 maximum plus the Constitution modifier.
            "hit_points": HitPoints(
                current=6 + con_mod, maximum=6 + con_mod, temporary=0
            ),
            "spell_access": tuple(
                SpellAccess(
                    pool_id=a.pool_id,
                    spell_record_key=picked["cantrip"],
                    mode=a.mode,
                    source=a.source,
                )
                for a in base.spell_access or ()
            )
            or None,
            "currency": {Currency.GP: int(gold.group(1))},
        }
    )
    assert (
        character.classes is not None and character.classes[0].class_record_key == cls
    )
    return character.model_dump(mode="json"), []


def responder(index: Any):  # type: ignore[no-untyped-def]
    """The ``rpg_setup_writer`` responder: GM-led character creation only."""

    def respond(texts: list[str]) -> Reply | None:
        joined = "\n".join(texts)
        if "phase: character_creation" not in joined:
            return None
        if "rules_package: not selected" in joined:
            return None
        character, questions = compose(texts, index)
        stated = stated_choices(texts)
        if character is None:
            return Reply(
                tool_input={
                    "schema_version": 1,
                    "gm_text": "To build your character I still need: "
                    + " ".join(questions),
                    "result": {"kind": "clarification", "questions": questions},
                }
            )
        summary = "; ".join(f"{k}: {stated[k]}" for k in REQUIRED)
        return Reply(
            tool_input={
                "schema_version": 1,
                "gm_text": f"Here is your character from what you told me. {summary}.",
                "result": {
                    "kind": "character_proposal",
                    "path": "gm_led",
                    "character": character,
                    "unresolved": [],
                },
            }
        )

    return respond
