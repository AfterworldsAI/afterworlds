"""CRD Issue 15c semantic candidate C5 — source-derived content (REVIEW MATERIAL).

Candidate only. Nothing here is accepted, recorded, minted, published or
activated, and nothing is written outside this directory. C5 supersedes the
unaccepted final C3 (``../candidate-c3/``) after Codex's independent review
(``../codex-c3-review.md``). C1, C2 and C3 are read, never written; their
digests are checked before and after every run. ``derive_c5.py`` is a fork of
``derive_c4.py``; ``derive_c5.diff`` shows every change.

C5 keeps C4's settled source/capability contract:

* **Source parts** (``c5a.json``, ``c5b.json``, ``c5c.json``) carry only
  source facts, formulas and participant predicates, which are what a native
  mint would contain.
* **Capability** (``capability.json``) carries everything about execution:
  classification, dependency kind (missing source authority, missing runtime
  input, missing state, unsupported mechanic), blockers, selection
  certification, execution exclusions and adapter procedures.

Run from the repository root with the clone venv::

    venv/Scripts/python.exe .claude/review-notes/issue-15c-implementation/candidate-c5/derive_c5.py
"""

from __future__ import annotations

import collections
import hashlib
import html
import importlib.util
import json
import re
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

sys.dont_write_bytecode = True  # never write caches into preserved C1/C2/C3 directories
REPO = Path.cwd()
sys.path.insert(0, str(REPO / "src"))
SRC = REPO / "docs/sources/community/dnd-5e-srd-markdown"
HERE = Path(__file__).parent
NOTES = HERE.parent
ORACLE = (
    REPO
    / "src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-8781d4e0-a3b-g1.json"
)
ORACLE_SHA256 = "2ccbaeba6de75d9787fbdd407e42dc2425fa20d4d26bcc298b681b550bd11258"  # pragma: allowlist secret
#: Preserved predecessors (read only; checked before and after).
PRESERVED = {
    "candidate/candidate-c1.json": "9e9645e89c622cc86c73ce9dae9e475aa6d3a879b79eb55cc99bbd62f0693d38",  # pragma: allowlist secret
    "candidate/candidate-c1b.json": "fbabf91a3ea9d613036aad1bb70354f1c4e560ecd6d12af688225f3356699e8e",  # pragma: allowlist secret
    "candidate/candidate-c1c.json": "82cfb6b93783b64a019d6066aaf5a7f6822d3c8213e52b31fc9d6efcaebad92f",  # pragma: allowlist secret
    "candidate-c2/c2a.json": "a15aab1839d6f86cc1fd4241b30b58dbdf9fa5d51cf2a8abd26ba48798df70d3",  # pragma: allowlist secret
    "candidate-c2/c2b.json": "0dd7538f3efd1b63832ba5d1963d175a2f6c0cd7addd19c2ca19cff9114f65ed",  # pragma: allowlist secret
    "candidate-c2/c2c.json": "a21a5e893f8710fa9d109c1d84166571e264197979c98c8a62d89e58d3326f5a",  # pragma: allowlist secret
    "candidate-c3/c3a.json": "aaa5a20fa59c8e4d9dbbd10120aa0b91e968cdb1bcd3616cb8b28632c2e49ff9",  # pragma: allowlist secret
    "candidate-c3/c3b.json": "bb086082b02e879706218a4ad016110d3c6d5b3f9cc095076adec1cc89095524",  # pragma: allowlist secret
    "candidate-c3/c3c.json": "36be82a04ff2c587af754ed9430dfdfeb9b6053b8073d80add716313069e422b",  # pragma: allowlist secret
    "candidate-c3/derive_c3.py": "88ddb75a9a82249c3d35afe48f23e0f24ebdfe998eb056a8573cf9d26d9a972a",  # pragma: allowlist secret
    "candidate-c4/c4a.json": "901083ec3c8c25e9cd95a638a537cf3db41d8277420e07f0fc2b5d023cd15e62",  # pragma: allowlist secret
    "candidate-c4/c4b.json": "f679b06c7e8e3513b9886716754db78b5a28c8cf254cb09d1e195b4f30765c08",  # pragma: allowlist secret
    "candidate-c4/c4c.json": "2c34a6f03fc081a0adbe3abf8f9e50f0dcad55e9c07469cf3204ccb36e68fb5f",  # pragma: allowlist secret
    "candidate-c4/capability.json": "2d884ffbb254af6849a8bd0b61cc5f2f2c4a84dd568f664e3606fb02cb783a8e",  # pragma: allowlist secret
    "candidate-c4/derive_c4.py": "319919c641deab501c2e187e0e50457a75b9a15422e4e9beea8263131e5994f0",  # pragma: allowlist secret
}
PROPOSED_SCHEMA = "5d-representation-schema-19 (proposed; not minted)"
STATUS = "CANDIDATE ONLY - not accepted, recorded, minted, published or activated"
#: Accepted families C3 claims to reuse unchanged; every such payload is run
#: through the accepted ``fact_from_payload`` (reuse-validation.json).
REUSED = {"damage", "ability_check", "condition_effect", "advantage", "effect_duration",
          "creature_defense", "speed_modification"}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load(name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, NOTES / "candidate" / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


c1a = load("derive_candidate")  # weapon rows, slug, locate (reviewed correct)
c1b = load("derive_creatures")  # vocabularies only
c1c = load("derive_armor")  # armor table reader (reviewed correct)
slug = c1a.slug
locate = c1a.locate


def lines(file: str) -> list[str]:
    return (SRC / file).read_text("utf-8").splitlines()


def write(name: str, body: Any) -> str:
    data = (json.dumps(body, indent=1, sort_keys=True, ensure_ascii=False) + "\n").encode()
    (HERE / name).write_bytes(data)
    return sha(data)


def located(file: str, quote: str) -> dict[str, Any]:
    return {"file": file, "line": locate(file, quote), "quote": quote}


# ===========================================================================
# Rules (C3-owned). Each quote must occur on its line; each fact states the
# full source sentence's qualifications (review residue: Light, Graze, armor
# training, Cobbler's Tools, and the sibling audit recorded in
# rules-disposition.json).
# ===========================================================================

PTG, EQ, GL, MON = "playing-the-game.md", "equipment.md", "rules-glossary.md", "monsters.md"
#: A turn boundary owned by a named participant. C3-local shape, declared new:
#: the accepted ``effect_duration.whose`` is subject-relative and cannot name
#: the other participant's clock (see README "Reuse").
#: Closed ``turn_of`` vocabulary, relative to the rule or entry:
#:   ``source``  the creature making the attack/using the entry or weapon;
#:   ``target``  the creature the effect is applied to;
#:   ``subject`` the creature a self-directed rule is about (death saves,
#:               Recharge);
#:   ``caster``  the creature whose spell or feature created the subject
#:               ("until the end of your next turn" in a summon's stat block).
TURN_OF = ("source", "target", "subject", "caster")


def turn(until: str, of: str, possessor: str | None = None) -> dict[str, str]:
    assert of in TURN_OF, of
    out = {"until": until, "turn_of": of, "turn": "next"}
    if possessor:
        out["possessor"] = possessor  # checked against the block's subject
    return out


RULES: list[tuple[str, str, str, str, dict[str, Any]]] = [
    *[
        ("play.d20_tests", "typical_dcs", PTG, f"<td>{label}</td>",
         {"family": "difficulty_band", "difficulty": slug(label), "dc": dc,
          "applies_to": "ability_check"})
        for label, dc in (("Very easy", 5), ("Easy", 10), ("Medium", 15),
                          ("Hard", 20), ("Very hard", 25), ("Nearly impossible", 30))
    ],
    ("play.d20_tests", "attack_ability_modifier", PTG,
     "Melee attack with a weapon or an Unarmed Strike",
     {"family": "attack_roll_ability", "range_class": "melee", "ability": "strength"}),
    ("play.d20_tests", "attack_ability_modifier", PTG, "Ranged attack with a weapon",
     {"family": "attack_roll_ability", "range_class": "ranged", "ability": "dexterity"}),
    ("play.d20_tests", "natural_20", PTG, "the attack hits regardless of any modifiers",
     {"family": "natural_roll_outcome", "context": "attack_roll", "face": 20,
      "outcome": "hit", "critical_hit": True}),
    ("play.d20_tests", "natural_1", PTG, "the attack misses regardless of any modifiers",
     {"family": "natural_roll_outcome", "context": "attack_roll", "face": 1,
      "outcome": "miss", "critical_hit": False}),
    ("play.combat", "initiative_roll", PTG, "they make a Dexterity check",
     {"family": "initiative_roll", "ability": "dexterity", "context": "ability_check"}),
    ("play.damage_and_healing", "damage_rolls", PTG,
     "you add your ability modifier—the same modifier used for the attack roll",
     {"family": "damage_roll_rule", "adds_attack_ability_modifier": True,
      "fixed_amount_adds_modifier": False, "minimum_damage": 0}),
    ("play.damage_and_healing", "critical_hits", PTG, "Roll the attack's damage dice twice",
     {"family": "critical_damage", "damage_dice_multiplier": 2,
      "applies_to": "every damage die of the attack", "modifiers": "added once"}),
    ("play.damage_and_healing", "temporary_hit_points", PTG,
     "those points are lost first, and any leftover damage carries over",
     {"family": "temporary_hit_point_absorption", "absorbed_first": True,
      "overflow_to_hit_points": True}),
    ("play.damage_and_healing", "hit_points", PTG, "which is the lowest Hit Points can go",
     {"family": "hit_point_bound", "minimum_current": 0}),
    ("play.damage_and_healing", "monster_death", PTG,
     "A monster dies the instant it drops to 0 Hit Points",
     {"family": "zero_hit_point_outcome", "subject": "monster", "outcome": "dies",
      "gamemaster_exception": "treat_as_character", "exception_scope": "individual monster"}),
    ("play.damage_and_healing", "hit_point_maximum_of_0", PTG,
     "A creature dies if its Hit Point maximum reaches 0",
     {"family": "zero_hit_point_outcome", "subject": "any",
      "trigger": "hit_point_maximum_zero", "outcome": "dies"}),
    ("play.damage_and_healing", "massive_damage", PTG,
     "the character dies if the remainder equals or exceeds their Hit Point maximum",
     {"family": "massive_damage", "subject": "character",
      "dies_when_remainder_at_least": "hit_point_maximum"}),
    ("play.damage_and_healing", "falling_unconscious", PTG,
     "you now face making Death Saving Throws",
     {"family": "zero_hit_point_outcome", "subject": "character",
      "outcome": "unconscious_and_dying", "until": "regains_hit_points"}),
    ("play.damage_and_healing", "death_saving_throws", PTG,
     "Roll 1d20. If the roll is 10 or higher, you succeed.",
     {"family": "death_saving_throw", "die": "d20", "success_minimum": 10,
      "successes_to_stable": 3, "failures_to_die": 3,
      "timing": {"when": "start_of_turn", "turn_of": "subject", "at_hit_points": 0},
      "ability": None, "reset_on": ["regains_hit_points", "becomes_stable"]}),
    ("play.damage_and_healing", "death_saving_throws", PTG,
     "When you roll a 1 on the d20 for a Death Saving Throw, you suffer two failures",
     {"family": "death_save_natural_roll", "face": 1, "failures": 2}),
    ("play.damage_and_healing", "death_saving_throws", PTG,
     "If you roll a 20 on the d20, you regain 1 Hit Point",
     {"family": "death_save_natural_roll", "face": 20, "regain_hit_points": 1}),
    ("play.damage_and_healing", "damage_at_0_hit_points", PTG,
     "If the damage is from a Critical Hit, you suffer two failures instead",
     {"family": "damage_at_zero_hit_points", "failures": 1, "critical_hit_failures": 2,
      "dies_when_damage_at_least": "hit_point_maximum"}),
    ("play.damage_and_healing", "stabilizing", PTG,
     "You can take the Help action to try to stabilize a creature with 0 Hit Points",
     {"family": "stabilization", "action": "help", "on_success": "stable",
      "target_at_hit_points": 0}),
    ("play.damage_and_healing", "stable", PTG,
     "A Stable creature that isn't healed regains 1 Hit Point after 1d4 hours",
     {"family": "stable_state", "makes_death_saves": False, "remains_unconscious": True,
      "damage_ends_stable": True,
      "recovery": {"dice": {"count": 1, "die": "d4"}, "unit": "hour",
                   "regain_hit_points": 1, "unless": "healed"}}),
    ("play.damage_and_healing", "knocking_out", PTG,
     "you can instead reduce the creature to 1 Hit Point",
     {"family": "knockout_alternative", "attack": "melee", "optional": True,
      "trigger": "would_reduce_to_0_hit_points", "set_hit_points": 1,
      "condition": "unconscious", "starts": "short_rest", "ends_after": "short_rest",
      "ends_early_on": ["regains_hit_points", "first_aid_success"]}),
    ("glossary.short_rest", "short_rest", GL, "A Short Rest is a 1-hour period",
     {"family": "rest_duration", "rest": "short_rest", "hours": 1}),
    # -- Weapon properties ---------------------------------------------------
    ("equipment.weapons.finesse", "finesse", EQ, "use your choice of your Strength or Dexterity",
     {"family": "attack_ability_option", "abilities": ["strength", "dexterity"],
      "same_for_damage": True}),
    ("equipment.weapons.heavy", "heavy", EQ, "your Strength score isn't at least 13",
     {"family": "ability_score_requirement", "range_class": "melee",
      "ability": "strength", "minimum": 13, "unmet": "attack_disadvantage"}),
    ("equipment.weapons.heavy", "heavy", EQ, "your Dexterity score isn't at least 13",
     {"family": "ability_score_requirement", "range_class": "ranged",
      "ability": "dexterity", "minimum": 13, "unmet": "attack_disadvantage"}),
    ("equipment.weapons.light", "light", EQ, "you can make one extra attack as a Bonus Action",
     {"family": "light_extra_attack", "trigger": "attack_action_on_own_turn",
      "first_attack": "with_a_light_weapon", "when": "later_on_the_same_turn",
      "cost": "bonus_action", "requires": "different_light_weapon", "limit": "once_per_turn",
      "ability_modifier_damage": "only_if_negative", "optional": True}),
    ("equipment.weapons.loading", "loading", EQ, "You can fire only one piece of ammunition",
     {"family": "ammunition_per_activation", "maximum": 1,
      "per": ["action", "bonus_action", "reaction"]}),
    ("equipment.weapons.range", "range", EQ, "you have Disadvantage on the attack roll",
     {"family": "range_band_rule", "beyond_normal": "attack_disadvantage",
      "beyond_long": "cannot_attack"}),
    ("equipment.weapons.reach", "reach", EQ, "adds 5 feet to your reach",
     {"family": "reach_extension", "feet": 5,
      "applies_to": ["attacks_with_it", "opportunity_attack_reach"]}),
    ("equipment.weapons.thrown", "thrown", EQ, "you can throw the weapon to make a ranged attack",
     {"family": "thrown_attack", "attack": "ranged", "draw_as_part_of_attack": True,
      "melee_weapon_ability": "as_melee_attack"}),
    ("equipment.weapons.two_handed", "two_handed", EQ, "requires two hands",
     {"family": "hands_required", "hands": 2, "when": "attacking"}),
    ("equipment.weapons.versatile", "versatile", EQ, "when used with two hands to make a melee attack",
     {"family": "versatile_damage", "hands": 2, "attack": "melee"}),
    ("equipment.weapons.ammunition", "ammunition", EQ, "Each attack expends one piece of ammunition",
     {"family": "ammunition_expenditure", "per_attack": 1,
      "requires": "ammunition_of_the_printed_type",
      "drawing_is_part_of_the_attack": True,
      "loading_requires_free_hand": {"when": "the weapon is one-handed"},
      "recovery": {"after": "fight", "minutes": 1, "fraction": {"numerator": 1,
                   "denominator": 2}, "rounding": "down", "remainder": "lost"}}),
    # -- Masteries (optional choices marked; durations owned explicitly) -----
    ("equipment.weapons.cleave", "cleave", EQ, "against a second creature within 5 feet of the first",
     {"family": "mastery_effect", "mastery": "cleave", "trigger": "hit_melee_attack_roll",
      "optional": True, "second_target_within_ft": 5, "second_target_within_reach": True,
      "ability_modifier_damage": "only_if_negative", "limit": "once_per_turn"}),
    ("equipment.weapons.graze", "graze", EQ, "equal to the ability modifier you used to make the attack roll",
     {"family": "mastery_effect", "mastery": "graze", "trigger": "miss_creature",
      "optional": True, "damage": "attack_ability_modifier", "damage_type": "weapon",
      "increase": "only_by_increasing_the_ability_modifier"}),
    ("equipment.weapons.nick", "nick", EQ, "as part of the Attack action instead of as a Bonus Action",
     {"family": "mastery_effect", "mastery": "nick", "trigger": "light_extra_attack",
      "optional": True, "cost": "attack_action", "limit": "once_per_turn"}),
    ("equipment.weapons.push", "push", EQ, "push the creature up to 10 feet straight away",
     {"family": "mastery_effect", "mastery": "push", "trigger": "hit_creature",
      "optional": True, "distance_ft_up_to": 10, "direction": "straight_away",
      "maximum_size": "large"}),
    ("equipment.weapons.sap", "sap", EQ, "Disadvantage on its next attack roll before the start of your next turn",
     {"family": "mastery_effect", "mastery": "sap", "trigger": "hit_creature",
      "optional": False, "applies_to": "hit_creature",
      "effect": {"family": "advantage", "state": "disadvantage",
                 "roll": {"actor": "subject", "context": "attack_roll", "ability": None},
                 "use_limit": "next_qualifying_roll"},
      "duration": turn("start_of_turn", "source")}),
    ("equipment.weapons.slow", "slow", EQ, "reduce its Speed by 10 feet until the start of your next turn",
     {"family": "mastery_effect", "mastery": "slow", "trigger": "hit_and_damage",
      "optional": True, "applies_to": "hit_creature", "speed_reduction_ft": 10,
      "maximum_reduction_ft": 10, "duration": turn("start_of_turn", "source")}),
    ("equipment.weapons.topple", "topple", EQ, "DC 8 plus the ability modifier used to make the attack roll",
     {"family": "mastery_effect", "mastery": "topple", "trigger": "hit_creature",
      "optional": True, "save": "constitution", "applies_to": "hit_creature",
      "dc": {"base": 8, "plus": ["attack_ability_modifier", "proficiency_bonus"]},
      "on_failure": [{"family": "condition_effect", "condition": "prone",
                      "effect": "applies"}]}),
    ("equipment.weapons.vex", "vex", EQ, "Advantage on your next attack roll against that creature",
     {"family": "mastery_effect", "mastery": "vex", "trigger": "hit_and_damage",
      "optional": False, "applies_to": "wielder",
      "effect": {"family": "advantage", "state": "advantage",
                 "roll": {"actor": "subject", "context": "attack_roll", "ability": None},
                 "use_limit": "next_qualifying_roll"},
      "against": "the_hit_creature", "duration": turn("end_of_turn", "source")}),
]

STAT_BLOCK_RULES: list[tuple[str, str, str, str, dict[str, Any]]] = [
    ("monsters.parts_of_a_stat_block", "attack_notation", MON,
     "An attack is against one target unless its entry says",
     {"family": "creature_attack_notation", "targets": 1,
      "sections": ["hit", "miss", "hit_or_miss"]}),
    ("monsters.parts_of_a_stat_block", "saving_throw_effect_notation", MON,
     "\"Half damage only\" on a successful save means the target takes half as much damage",
     {"family": "creature_save_notation", "half_damage_rounding": "down",
      "half_damage_only_ignores_other_effects": True}),
    ("monsters.parts_of_a_stat_block", "damage_notation", MON,
     "You decide whether to use the number or the die expression",
     {"family": "damage_notation_option", "options": ["average", "dice"],
      "selected_by": "gamemaster", "exclusive": True}),
    ("monsters.parts_of_a_stat_block", "multiattack", MON,
     "Some creatures can make more than one attack when they take the Attack action",
     {"family": "multiattack_rule", "action": "attack", "composition": "per_entry"}),
    ("monsters.parts_of_a_stat_block", "limited_usage", MON, "**X/Day.** This notation means",
     {"family": "usage_limit_rule", "kind": "per_day", "regain": "long_rest"}),
    ("monsters.parts_of_a_stat_block", "limited_usage", MON, "**Recharge X–Y.** This notation means",
     {"family": "usage_limit_rule", "kind": "recharge", "die": "d6",
      "roll_at": "start_of_turn", "turn_of": "subject",
      "also_regain": ["short_rest", "long_rest"]}),
    ("monsters.parts_of_a_stat_block", "limited_usage", MON, "**Recharge after a Short or Long Rest.**",
     {"family": "usage_limit_rule", "kind": "recharge_after_rest",
      "regain": ["short_rest", "long_rest"]}),
    ("monsters.parts_of_a_stat_block", "legendary_actions", MON,
     "it regains all expended uses at the start of each of its turns",
     {"family": "legendary_action_rule", "timing": "after_another_creatures_turn",
      "one_at_a_time": True, "regain": "start_of_own_turn",
      "not_while_has_conditions": ["incapacitated"]}),
]


def _armor_rules() -> list[tuple[str, str, str, str, dict[str, Any]]]:
    """C1-C's armor rules, with the training penalty's full condition stated
    (untrained armor causes it; trained armor does not)."""
    out = []
    for record, component, file, quote, fact in c1c.RULES:
        fact = dict(fact)
        if fact["family"] == "armor_training_penalty":
            fact["applies_when"] = "the wearer lacks training with the worn armor's category"
            fact["cannot_cast_spells"] = True
        out.append((record, component, file, quote, fact))
    return out


ARMOR_RULES = _armor_rules()


#: The formulas a summon's "your spell attack modifier" / "your spell save DC"
#: name, and the class spellcasting abilities they read. Source authority,
#: typed so a summon's formula reference resolves; the caster's level, class
#: and scores are runtime input.
SPELLS, CLASSES = "spells.md", "classes.md"
SPELLCASTING_RULES: list[tuple[str, str, str, str, dict[str, Any]]] = [
    ("spells.attack_rolls", "spell_attack_modifier", SPELLS,
     "**Spell attack modifier** = your spellcasting ability modifier + your Proficiency Bonus",
     {"family": "spell_attack_modifier_formula",
      "sum": ["spellcasting_ability_modifier", "proficiency_bonus"]}),
    ("spells.saving_throws", "spell_save_dc", SPELLS,
     "**Spell save DC** = 8 + your spellcasting ability modifier + your Proficiency Bonus",
     {"family": "spell_save_dc_formula", "base": 8,
      "plus": ["spellcasting_ability_modifier", "proficiency_bonus"]}),
    *[
        (f"classes.{cls}.{feature}", "spellcasting_ability", CLASSES,
         f"{ability.title()} {verb} spellcasting ability for your {cls.title()} spells.",
         {"family": "spellcasting_ability", "ability": ability})
        for cls, feature, ability, verb in (
            ("bard", "spellcasting", "charisma", "is your"),
            ("cleric", "spellcasting", "wisdom", "is your"),
            ("druid", "spellcasting", "wisdom", "is your"),
            ("paladin", "spellcasting", "charisma", "is your"),
            ("ranger", "spellcasting", "wisdom", "is your"),
            ("sorcerer", "spellcasting", "charisma", "is your"),
            ("warlock", "pact_magic", "charisma", "is the"),
            ("wizard", "spellcasting", "intelligence", "is your"),
        )
    ],
]


# ===========================================================================
# Grant / selection authority (codex-grant-trust-review.md). What each
# contributing source *entitles* — counts, eligible lists, levels, caps — as
# printed. Whether a recorded grant matches it is runtime validation (held).
# ===========================================================================

ORIGINS, FEATS = "character-origins.md", "feats.md"
_CLASSES12 = ("barbarian", "bard", "cleric", "druid", "fighter", "monk", "paladin", "ranger",
              "rogue", "sorcerer", "warlock", "wizard")
_ALL_SKILLS = sorted(s_.value for s_ in __import__(
    "afterworlds.ingestion.mechanical.representation", fromlist=["Skill"]).Skill)


def _skill_list(text: str) -> list[str]:
    return [slug(x) for x in re.split(r",? or |, ", text) if x.strip()]


_ARMOR = ("light", "medium", "heavy")
def _tool(slug_: str) -> dict[str, str]:
    return {"record_key": f"equipment.tools.{slug_}", "component_key": slug_}


_TOOL_KEYS = {"Calligrapher's Supplies": _tool("calligraphers_supplies"),
              "Thieves' Tools": _tool("thieves_tools"),
              "Herbalism Kit": _tool("herbalism_kit")}


def _weapons(text: str) -> dict[str, Any]:
    """Weapon proficiency as printed: categories, or a category qualified by
    weapon properties."""
    if text == "Simple and Martial weapons":
        return {"categories": ["simple", "martial"]}
    if text == "Simple weapons":
        return {"categories": ["simple"]}
    if text == "Martial weapons":
        return {"categories": ["martial"]}
    m = re.fullmatch(r"Simple weapons and Martial weapons that have the (\w+)(?: or (\w+))? "
                     r"property", text)
    assert m, text
    return {"categories": ["simple"],
            "qualified": [{"category": "martial", "with_any_property":
                           [p.lower() for p in m.groups() if p]}]}


def _armor(text: str) -> dict[str, Any]:
    if text == "None":
        return {"armor": [], "shields": False}
    words = re.findall(r"Light|Medium|Heavy|Shields", text)
    assert words and re.sub(r"Light|Medium|Heavy|Shields|armor|and|,|\s", "", text) == "", text
    return {"armor": [w.lower() for w in words if w != "Shields"], "shields": "Shields" in words}


def _tools(text: str) -> dict[str, Any]:
    if text in _TOOL_KEYS:
        return {"family": "tool_proficiency_grant", "tools": [_TOOL_KEYS[text]]}
    if m := re.fullmatch(r"Choose (\d+) Musical Instruments \(see Equipment\)", text):
        return {"family": "tool_proficiency_choice", "count": int(m[1]),
                "from": {"tool_variants_of": _tool("musical_instrument")}}
    if text == "Choose one type of Artisan's Tools or Musical Instrument (see Equipment)":
        return {"family": "tool_proficiency_choice", "count": 1,
                "from": [{"tool_category": "artisans_tools"},
                         {"tool_variants_of": _tool("musical_instrument")}]}
    raise AssertionError(text)


def proficiency_and_training_grants(add: Any) -> None:
    """Who earns saving-throw, weapon, armor, tool and Weapon Mastery
    entitlements, as printed (Codex C5 grant-family addendum)."""
    src = lines(CLASSES)
    rows = {}
    for i, l in enumerate(src):
        m = re.match(r"\s*<td>(Saving Throw Proficiencies|Weapon Proficiencies|Tool "
                     r"Proficiencies|Armor Training)</td>", l)
        if m:
            rows.setdefault(m[1], []).append((i + 2, re.sub(r"<[^>]+>", "", src[i + 1]).strip()))
    assert [len(rows[k]) for k in ("Saving Throw Proficiencies", "Weapon Proficiencies",
                                   "Armor Training")] == [12, 12, 12], rows.keys()
    tools_by_line = dict(rows["Tool Proficiencies"])
    weapon_lines = [n for n, _ in rows["Weapon Proficiencies"]]
    for idx, cls in enumerate(_CLASSES12):
        record = f"classes.{cls}"
        n, sv = rows["Saving Throw Proficiencies"][idx]
        add(record, "core_traits", CLASSES, sv,
            {"family": "saving_throw_proficiency_grant", "context": "level_1_character",
             "abilities": [a.lower() for a in re.split(r" and ", sv)]}, line=n)
        n, wp = rows["Weapon Proficiencies"][idx]
        add(record, "core_traits", CLASSES, wp,
            {"family": "weapon_proficiency_grant", "context": "level_1_character",
             **_weapons(wp)}, line=n)
        n, ar = rows["Armor Training"][idx]
        add(record, "core_traits", CLASSES, ar,
            {"family": "armor_training_grant", "context": "level_1_character", **_armor(ar)},
            line=n)
        # The class's own tool row, when its table prints one (between its
        # weapon row and the next class's weapon row).
        nxt = weapon_lines[idx + 1] if idx + 1 < 12 else 10 ** 9
        for tn, tv in tools_by_line.items():
            if weapon_lines[idx] < tn < nxt:
                add(record, "core_traits", CLASSES, tv,
                    {**_tools(tv), "context": "level_1_character"}, line=tn)
    # Multiclass: only the listed traits (no saving throws).
    heads = [i for i, l in enumerate(src) if l == "#### As a Multiclass Character"]
    for cls, i in zip(_CLASSES12, heads, strict=True):
        n = next(j for j in range(i, i + 6) if re.search(r"Core \w+ Traits table", src[j]))
        text = src[n].lstrip("•- ").strip()
        listed = text.split(": ", 1)[1].rstrip(".") if ": " in text else ""
        fact: dict[str, Any] = {"family": "multiclass_proficiency_grant",
                                "saving_throws": []}
        if m := re.search(r"proficiency with (Simple and Martial|Martial|Simple) weapons", listed):
            fact["weapons"] = _weapons(f"{m[1]} weapons")
        else:
            fact["weapons"] = {"categories": []}
        if m := re.search(r"training with ((?:Light|Medium|Heavy|Shields)[\w ,]*?)(?:,|$| and "
                          r"(?=proficiency))", listed):
            fact["armor_training"] = _armor(m[1].strip())
        else:
            fact["armor_training"] = {"armor": [], "shields": False}
        if "one Musical Instrument of your choice" in listed:
            fact["tools"] = {"family": "tool_proficiency_choice", "count": 1,
                             "from": {"tool_variants_of": _tool("musical_instrument")}}
        elif "Thieves' Tools" in listed:
            fact["tools"] = {"family": "tool_proficiency_grant",
                             "tools": [_tool("thieves_tools")]}
        add(f"classes.{cls}.as_a_multiclass_character", "as_a_multiclass_character",
            CLASSES, text, fact, line=n + 1)
    # Feature grants with their exact G1 progression entries.
    for record, component, quote, fact in (
            ("classes.monk.disciplined_survivor", "disciplined_survivor",
             "Your physical and mental discipline grant you proficiency in all saving throws.",
             {"family": "saving_throw_proficiency_grant", "abilities": list(ABILITY)}),
            ("classes.rogue.slippery_mind", "slippery_mind",
             "You gain proficiency in Wisdom and Charisma saving throws.",
             {"family": "saving_throw_proficiency_grant", "abilities": ["wisdom", "charisma"]}),
            ("classes.cleric.divine_order", "protector",
             "_Protector._ Trained for battle, you gain proficiency with Martial weapons and "
             "training with Heavy armor.",
             {"family": "weapon_and_armor_grant", "weapons": {"categories": ["martial"]},
              "armor_training": {"armor": ["heavy"], "shields": False},
              "chosen_option_of": "classes.cleric.divine_order"}),
            ("classes.druid.primal_order", "warden",
             "_Warden._ Trained for battle, you gain proficiency with Martial weapons and "
             "training with Medium armor.",
             {"family": "weapon_and_armor_grant", "weapons": {"categories": ["martial"]},
              "armor_training": {"armor": ["medium"], "shields": False},
              "chosen_option_of": "classes.druid.primal_order"})):
        add(record, component, CLASSES, quote,
            {**fact, "gain_levels": {"family": "progression_entry", "entitlement_key": record}})
    # Weapon Mastery: count, eligible kinds, gain levels and the rest-swap
    # qualifier as printed. Barbarian and Fighter counts come from their own
    # Features tables (G1's quantity-bearing entry is keyed for neither class).
    for cls, quote, restriction, swap in (
            ("barbarian", "Your training with weapons allows you to use the mastery properties of "
             "two kinds of Simple or Martial Melee weapons of your choice",
             {"categories": ["simple", "martial"], "melee_only": True}, "one"),
            ("fighter", "Your training with weapons allows you to use the mastery properties of "
             "three kinds of Simple or Martial weapons of your choice",
             {"categories": ["simple", "martial"]}, "one"),
            ("paladin", "Your training with weapons allows you to use the mastery properties of "
             "two kinds of weapons of your choice with which you have proficiency",
             {"requires_weapon_proficiency": True}, "any"),
            ("ranger", "Your training with weapons allows you to use the mastery properties of "
             "two kinds of weapons of your choice with which you have proficiency",
             {"requires_weapon_proficiency": True}, "any"),
            ("rogue", "Your training with weapons allows you to use the mastery properties of "
             "two kinds of weapons of your choice with which you have proficiency",
             {"requires_weapon_proficiency": True}, "any")):
        head = next(i for i, l in enumerate(src) if l == "#### Level 1: Weapon Mastery"
                    and i > next(j for j, x in enumerate(src)
                                 if x.startswith(f"## {cls.title()}")))
        n = next(j for j in range(head, head + 4) if src[j].startswith("Your training"))
        count = {"two": 2, "three": 3}[re.search(r"of (two|three) kinds", quote)[1]]
        fact = {"family": "weapon_mastery_choice", "kinds_of_weapons": count, **restriction,
                "rest_swap": {"after": "long_rest", "change": swap},
                "gain_levels": {"family": "progression_entry",
                                "entitlement_key": f"classes.{cls}.weapon_mastery"}}
        if cls in ("barbarian", "fighter"):
            fact["count_by_level"] = _mastery_column(src, cls)
        add(f"classes.{cls}.weapon_mastery", "weapon_mastery", CLASSES, quote, fact,
            line=n + 1)
    # Background tools (the Soldier chooses one kind of Gaming Set).
    o = lines(ORIGINS)
    for bg in ("acolyte", "criminal", "sage", "soldier"):
        head = next(i for i, l in enumerate(o) if re.match(rf"#{{3,4}} {bg.title()}\b", l))
        n = next(j for j in range(head, len(o)) if o[j].startswith("**Tool Proficiency:**"))
        value = o[n].split("**", 2)[2].strip()
        if value.startswith("_Choose one kind of_ Gaming Set"):
            fact = {"family": "tool_proficiency_choice", "count": 1,
                    "from": {"tool_variants_of": _tool("gaming_set")}}
        else:
            fact = {"family": "tool_proficiency_grant", "tools": [_TOOL_KEYS[value]]}
        add(f"character_origins.{bg}", "tool_proficiency", ORIGINS, o[n].strip(), fact,
            line=n + 1)


def _mastery_column(src: list[str], cls: str) -> dict[str, int]:
    """The Weapon Mastery column of a class's Features table, by level."""
    start = src.index(f"**{cls.title()} Features**")
    i = next(j for j in range(start, start + 40) if "<table" in src[j])
    end = next(j for j in range(i, len(src)) if "</table>" in src[j])
    rows, cur = [], None
    for line in src[i:end]:
        if "<tr>" in line:
            cur = []
        if cur is not None:
            cur += re.findall(r"<t[hd]>(.*?)</t[hd]>", line)
        if "</tr>" in line:
            rows.append(cur)
            cur = None
    col = rows[0].index("Weapon Mastery")
    out = {r[0]: int(r[col]) for r in rows[1:]}
    assert sorted(map(int, out)) == list(range(1, 21)), out
    return out


def grant_facts(comps: set[tuple[str, str]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []

    def add(record: str, component: str, file: str, quote: str, fact: dict[str, Any],
            line: int | None = None) -> None:
        """``line`` (1-based) pins provenance when the same quote recurs."""
        assert (record, component) in comps, (record, component)
        if line is not None and quote not in lines(file)[line - 1]:
            # A sentence wrapped onto the next physical line: quote the joined
            # logical text and record both lines.
            joined = lines(file)[line - 1].strip() + " " + lines(file)[line].strip()
            assert quote in joined, (file, line, quote)
            out.append({"record_key": record, "component_key": component, "fact": fact,
                        "source": {"file": file, "line": line, "last_line": line + 1,
                                   "quote": quote}})
            return
        src_ = located(file, quote)
        if line is not None:
            assert quote in lines(file)[line - 1], (file, line, quote)
            src_["line"] = line
        out.append({"record_key": record, "component_key": component, "fact": fact,
                    "source": src_})

    # Class skill-proficiency choice: the "Skill Proficiencies" row of each
    # class's Core Traits table, in class order.
    src = lines(CLASSES)
    rows = [src[i + 1] for i, l in enumerate(src) if "<td>Skill Proficiencies</td>" in l]
    assert len(rows) == 12, len(rows)
    for cls, row in zip(_CLASSES12, rows, strict=True):
        text = re.sub(r"<[^>]+>", "", row).strip()
        if m := re.fullmatch(r"Choose any (\d+) skills \(see Playing the Game\)", text):
            fact = {"family": "skill_proficiency_choice", "count": int(m.group(1)),
                    "from": _ALL_SKILLS, "context": "level_1_character"}
        else:
            m = re.fullmatch(r"Choose (\d+): (.+)", text)
            assert m, text
            fact = {"family": "skill_proficiency_choice", "count": int(m.group(1)),
                    "from": _skill_list(m.group(2)), "context": "level_1_character"}
        assert set(fact["from"]) <= set(_ALL_SKILLS), fact
        add(f"classes.{cls}", "core_traits", CLASSES, text, fact)
    # Backgrounds: fixed skills and the three listed abilities.
    for bg in ("acolyte", "criminal", "sage", "soldier"):
        o = lines(ORIGINS)
        head = next(i for i, l in enumerate(o) if l.startswith(f"### {bg.title()}")
                    or l.startswith(f"#### {bg.title()}"))
        ab = next(l for l in o[head:] if l.startswith("**Ability Scores:**"))
        sk = next(l for l in o[head:] if l.startswith("**Skill Proficiencies:**"))
        add(f"character_origins.{bg}", "ability_scores", ORIGINS, ab,
            {"family": "ability_increase_choice", "abilities":
             [a.strip().lower() for a in ab.split("**")[2].split(",")],
             "rule": "character_origins.backgrounds/ability_scores"})
        add(f"character_origins.{bg}", "skill_proficiencies", ORIGINS, sk,
            {"family": "skill_proficiency_grant", "skills":
             [slug(x) for x in sk.split("**")[2].strip().split(" and ")]})
    add("character_origins.backgrounds", "ability_scores", ORIGINS,
        "Increase one by 2 and another one by 1, or increase all three by 1. None of these "
        "increases can raise a score above 20.",
        {"family": "ability_increase_rule", "patterns": [[2, 1], [1, 1, 1]],
         "distinct_abilities": True, "maximum_score": 20})
    # Feats.
    add("feats.ability_score_improvement", "ability_score_improvement", FEATS,
        "Increase one ability score of your choice by 2, or increase two ability scores of "
        "your choice by 1. This feat can't increase an ability score above 20.",
        {"family": "ability_increase_choice", "abilities": "any",
         "patterns": [[2], [1, 1]], "distinct_abilities": True, "maximum_score": 20,
         "repeatable": True})
    f = lines(FEATS)
    contributing = ["ability_score_improvement"]
    for i, l in enumerate(f):
        m = re.match(r"_Ability Score Increase\._ Increase (one ability score of your choice|"
                     r"your (.+?) score) by 1, to a maximum of (\d+)\.", l)
        if not m:
            continue
        feat = slug(next(f[j] for j in range(i, 0, -1) if f[j].startswith("#### "))[5:])
        abilities = ("any" if m.group(2) is None else
                     [a.lower() for a in re.split(r",? or |, ", m.group(2))])
        add(f"feats.{feat}", "ability_score_increase", FEATS, l.strip(),
            {"family": "ability_increase_choice", "abilities": abilities, "patterns": [[1]],
             "maximum_score": int(m.group(3))}, line=i + 1)
        contributing.append(feat)
    # Prerequisites of every feat whose adjustment contributes (C4 review P1).
    for feat in contributing:
        head = next(j for j, l in enumerate(f) if l.startswith("#### ")
                    and slug(l[5:]) == feat)
        cat = next(l for l in f[head:head + 4] if l.startswith("_") and "Feat" in l)
        m = re.fullmatch(r"_(?P<cat>[\w ]+?) Feat(?: \(Prerequisite: (?P<pre>.+)\))?_", cat)
        assert m, cat
        fact: dict[str, Any] = {"family": "feat_prerequisite",
                                "category": slug(m["cat"])}
        for part in (m["pre"] or "").split(", "):
            if lm := re.fullmatch(r"Level (\d+)\+", part):
                fact["minimum_character_level"] = int(lm[1])
            elif am := re.fullmatch(r"(\w+) or (\w+) (\d+)\+", part):
                fact["minimum_ability_score"] = {"any_of": [am[1].lower(), am[2].lower()],
                                                 "score": int(am[3])}
            elif part == "Spellcasting Feature":
                fact["requires_feature"] = "spellcasting"
            else:
                assert not part, part
        add(f"feats.{feat}", "category", FEATS, cat, fact, line=head + 3)
    add("feats.skilled", "skilled", FEATS,
        "You gain proficiency in any combination of three skills or tools of your choice.",
        {"family": "skill_proficiency_choice", "count": 3, "from": _ALL_SKILLS,
         "or_tools": {"from": {"any_tool_entry": True}}, "repeatable": True})
    # Species.
    add("character_origins.elf", "keen_senses", ORIGINS,
        "You have proficiency in the Insight, Perception, or Survival skill.",
        {"family": "skill_proficiency_choice", "count": 1,
         "from": ["insight", "perception", "survival"]})
    add("character_origins.human", "skillful", ORIGINS,
        "You gain proficiency in one skill of your choice.",
        {"family": "skill_proficiency_choice", "count": 1, "from": _ALL_SKILLS})
    # Class ASI and Epic Boon features: the feat each gain entitles (C4 review
    # P1). Gain levels reuse the accepted progression_entry facts.
    for feature, default, category in (
            ("ability_score_improvement", "feats.ability_score_improvement", None),
            ("epic_boon", None, "epic_boon")):
        pat = ('You gain the Ability Score Improvement feat (see "Feats") or another feat '
               'of your choice for which you qualify.' if default else
               'You gain an Epic Boon feat (see "Feats") or another feat of your choice for '
               'which you qualify.')
        at = [i for i, l in enumerate(lines(CLASSES)) if l.startswith(pat)]
        assert len(at) == 12, (feature, len(at))
        for cls, i in zip(_CLASSES12, at, strict=True):
            add(f"classes.{cls}.{feature}", feature, CLASSES, pat,
                {"family": "feat_choice", "count_per_gain": 1,
                 **({"named_feat": default} if default else {"category": category}),
                 "or_any_feat_whose_prerequisites_are_met": True,
                 "gain_levels": {"family": "progression_entry",
                                 "entitlement_key": f"classes.{cls}.{feature}"}},
                line=i + 1)
    add("classes.barbarian.primal_knowledge", "primal_knowledge", CLASSES,
        "You gain proficiency in another skill of your choice from the skill list available "
        "to Barbarians at level 1.",
        {"family": "skill_proficiency_choice", "count": 1,
         "from": "classes.barbarian/core_traits",
         "gain_levels": {"family": "progression_entry",
                         "entitlement_key": "classes.barbarian.primal_knowledge"}})
    lore_q = "You gain proficiency with three skills of your choice."
    src_l = lines(CLASSES)
    at = next(i for i, l in enumerate(src_l) if l == lore_q)
    lvl = next(src_l[j] for j in range(at, 0, -1) if src_l[j].startswith("#### "))
    sub = next(src_l[j] for j in range(at, 0, -1) if src_l[j].startswith("### "))
    assert lvl == "#### Level 3: Bonus Proficiencies", lvl
    assert sub == "### Bard Subclass: College of Lore", sub
    add("classes.bard.college_of_lore.bonus_proficiencies", "bonus_proficiencies", CLASSES,
        lore_q,
        {"family": "skill_proficiency_choice", "count": 3, "from": _ALL_SKILLS,
         "eligibility": {"class": "classes.bard", "subclass": "classes.bard.college_of_lore",
                         "minimum_class_level": int(re.search(r"Level (\d+)", lvl)[1]),
                         "source_headings": [sub, lvl]}}, line=at + 1)
    # Multiclass entry grants (only Bard, Ranger and Rogue grant a skill).
    src_c = lines(CLASSES)
    heads = [i for i, l in enumerate(src_c) if l == "#### As a Multiclass Character"]
    assert len(heads) == 12, len(heads)
    for cls, i in zip(_CLASSES12, heads, strict=True):
        line = next(l for l in src_c[i:i + 6] if l.lstrip("•- ").startswith("Gain the")
                    and ("traits" in l or "Trait" in l or "Hit Point Die" in l))
        quote = line.lstrip("•- ").strip()
        if "one skill of your choice from the" in quote:
            fact = {"family": "multiclass_skill_proficiency_choice", "count": 1,
                    "from": f"classes.{cls}/core_traits"}
        elif "one skill of your choice" in quote:
            fact = {"family": "multiclass_skill_proficiency_choice", "count": 1,
                    "from": _ALL_SKILLS}
        else:
            fact = {"family": "multiclass_skill_proficiency_choice", "count": 0}
        add(f"classes.{cls}.as_a_multiclass_character", "as_a_multiclass_character",
            CLASSES, quote, fact)
    proficiency_and_training_grants(add)
    # Origin feats granted by backgrounds; Human Versatile's origin-feat choice.
    o = lines(ORIGINS)
    for bg in ("acolyte", "criminal", "sage", "soldier"):
        head = next(i for i, l in enumerate(o) if l.startswith(f"### {bg.title()}")
                    or l.startswith(f"#### {bg.title()}"))
        ft = next(l for l in o[head:] if l.startswith("**Feat:**"))
        name = re.sub(r"_|\(see .*?\)|\s+$", "", ft.split("**")[2]).strip()
        base = re.sub(r" \(.*\)$", "", name)
        add(f"character_origins.{bg}", "feat", ORIGINS, ft,
            {"family": "feat_grant", "feat": f"feats.{slug(base)}",
             **({"qualifier": re.search(r"\((.*)\)", name).group(1)} if "(" in name
                else {})})
    add("character_origins.human", "versatile", ORIGINS,
        "You gain an Origin feat of your choice (see \"Feats\").",
        {"family": "feat_choice", "category": "origin", "count": 1})
    # Expertise: the glossary rule and every feature granting it.
    add("glossary.expertise", "gaining_expertise", GL,
        "If you gain Expertise, you gain it in one skill in which you have proficiency.",
        {"family": "expertise_rule", "requires_skill_proficiency": True,
         "no_duplicate": True, "proficiency_bonus_multiplier": 2})
    for record, component, quote, fact in (
        ("classes.bard.expertise", "expertise",
         "You gain Expertise (see \"Rules Glossary\") in two of your skill proficiencies",
         {"count_per_gain": 2}),
        ("classes.rogue.expertise", "expertise",
         "You gain Expertise in two of your skill proficiencies of your choice.",
         {"count_per_gain": 2}),
        ("classes.ranger.deft_explorer", "expertise",
         "Choose one of your skill proficiencies with which you lack Expertise.",
         {"count_per_gain": 1}),
        ("classes.ranger.expertise", "expertise",
         "Choose two of your skill proficiencies with which you lack Expertise.",
         {"count_per_gain": 2}),
        ("classes.wizard.scholar", "scholar",
         "Choose one of the following skills in which you have proficiency: Arcana, History, "
         "Investigation, Medicine, Nature, or Religion.",
         {"count_per_gain": 1,
          "from": ["arcana", "history", "investigation", "medicine", "nature", "religion"]}),
    ):
        add(record, component, CLASSES, quote,
            {"family": "expertise_choice", "from_proficient_skills": True,
             # Gain levels reuse the accepted progression_entry facts.
             "gain_levels": {"family": "progression_entry", "entitlement_key": record},
             **fact})
    return out


def rule_facts(table: list[Any], comps: set[tuple[str, str]]) -> list[dict[str, Any]]:
    out = []
    for record, component, file, quote, fact in table:
        assert (record, component) in comps, (record, component)
        out.append({"record_key": record, "component_key": component, "fact": fact,
                    "source": located(file, quote)})
    return out


def rules_disposition() -> list[dict[str, Any]]:
    """Per hand-authored rule: unchanged, or the qualifier C3 added.

    ``RULES`` is compared with C1/C2 (C2 imported C1's list unchanged);
    ``STAT_BLOCK_RULES`` with C2's; armor rules with C1-C/C2-C.
    """
    spec = importlib.util.spec_from_file_location(
        "derive_c2_ro", NOTES / "candidate-c2" / "derive_c2.py")
    assert spec and spec.loader
    c2 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(c2)
    old = {(r, c, q): f for r, c, _, q, f in c1a.RULES}
    old |= {(r, c, q): f for r, c, _, q, f in c2.STAT_BLOCK_RULES}
    old |= {(r, c, q): f for r, c, _, q, f in c1c.RULES}
    out = []
    for record, component, _, quote, fact in RULES + STAT_BLOCK_RULES + ARMOR_RULES + SPELLCASTING_RULES:
        before = old.get((record, component, quote))
        if before is None:
            disposition = "new in C4 (kept in C5)"
        elif before == fact:
            disposition = "unchanged"
        else:
            added = sorted(set(fact) - set(before))
            changed = sorted(k for k in set(fact) & set(before) if fact[k] != before[k])
            disposition = f"qualified: added {added}, changed {changed}"
        out.append({"rule": f"{record}/{component}", "quote": quote,
                    "disposition": disposition})
    return out


# ===========================================================================
# C3-A tools: every printed tool, option identity outside the fact payload.
# ===========================================================================


def _utilize_options(text: str) -> list[tuple[str, int]]:
    """Split a Utilize line on its ``(DC N)`` boundaries; the option text is
    everything since the previous boundary, never cut at an inner comma."""
    out = []
    for m in re.finditer(r"(.+?) \(DC (\d+)\)(?:, or |, |$)", text):
        out.append((re.sub(r"^or ", "", m.group(1).strip()), int(m.group(2))))
    return out


def tools(records: set[str], comps: set[tuple[str, str]]) -> tuple[list[Any], list[Any]]:
    src = lines(EQ)
    start = src.index("#### Artisan's Tools")
    other = src.index("#### Other Tools")
    end = src.index("## Adventuring Gear")
    facts: list[Any] = []
    concord: list[Any] = []
    for i in range(start, end):
        m = re.match(r"^\*\*(.+?) \((?:[\d,]+ [GS]P|Varies)\)\*\*$", src[i])
        if not m:
            continue
        name, key = m.group(1), slug(m.group(1))
        identity = ((f"equipment.tools.{key}", key) if f"equipment.tools.{key}" in records
                    else ("equipment.tools", key))
        assert identity in comps, identity
        j = i + 1 + (src[i + 1] == "")
        ability = re.match(r"^\*\*Ability:\*\* (\w+)", src[j])
        assert ability, src[j]
        ab = ability.group(1).lower()
        rows: list[dict[str, Any]] = [{
            "fact": {"family": "tool_entry", "ability": ab,
                     "category": "artisans_tools" if i < other else "other_tools"},
            "source": {"file": EQ, "line": i + 1, "quote": src[i]}}]
        k = j + 1
        while k < len(src) and src[k].startswith("**") and not src[k].endswith(")**"):
            if src[k].startswith("**Utilize:**"):
                text = src[k].removeprefix("**Utilize:** ")
                options = _utilize_options(text)
                rebuilt = ", or ".join(f"{o} (DC {dc})" for o, dc in options)
                assert rebuilt.replace(", or ", ", ") == text.replace(", or ", ", "), (text, rebuilt)
                for opt, dc in options:
                    row: dict[str, Any] = {
                        # Native option identity (ComponentOption.semantic_key);
                        # the fact is the accepted ability_check payload, unchanged.
                        "option": {"semantic_key": slug(opt), "text": opt},
                        "fact": {"family": "ability_check", "ability": ab,
                                 "context": "ability_check", "dc_kind": "fixed",
                                 "dc_value": dc},
                        "source": {"file": EQ, "line": k + 1, "quote": f"{opt} (DC {dc})"}}
                    if opt.startswith("Modify footwear to give Advantage"):
                        row["option"]["effect_on_success"] = {
                            "applies_to": "wearer_of_the_modified_footwear",
                            "effect": {"family": "advantage", "state": "advantage",
                                       "roll": {"actor": "subject", "context": "ability_check",
                                                "ability": "dexterity", "skill": "acrobatics"},
                                       "use_limit": "next_qualifying_roll"}}
                    rows.append(row)
            if src[k].startswith("**Variants:**"):
                variants = [slug(re.sub(r" \(.*", "", v)) for v in
                            re.split(r", (?![^()]*\))", src[k].removeprefix("**Variants:** "))]
                rows.append({"fact": {"family": "tool_variants", "variants": variants,
                                      "separate_proficiency": True},
                             "source": {"file": EQ, "line": k + 1, "quote": src[k],
                                        "variants_rule": located(EQ, "Each requires a separate proficiency")}})
            k += 1
        for r in rows:
            facts.append({"record_key": identity[0], "component_key": identity[1], **r})
        concord.append({"tool": name, "identity": "/".join(identity),
                        "grain": "record" if identity[0] != "equipment.tools" else "component",
                        "options": [r["option"]["text"] for r in rows if "option" in r]})
    return facts, concord


# ===========================================================================
# C3-B creatures
# ===========================================================================

SIZES = c1b.SIZES
DAMAGE = c1b.DAMAGE
CONDITIONS = c1b.CONDITIONS
ABILITY = c1b.ABILITY
NUM = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6}
_DMG = re.compile(r"(?P<avg>\d+) \((?P<n>\d+)d(?P<d>\d+)(?: (?P<sign>[+−-]) (?P<mod>\d+))?\) "
                  r"(?P<type>[A-Z][a-z]+) damage")
_FLAT = re.compile(r"(?P<avg>\d+) (?P<type>[A-Z][a-z]+) damage")
#: Entry heads as printed: ``**_Name._**``, ``_Name._`` and the malformed
#: ``_Name. Melee…`` (spells.md), all read alike.
_ENTRY = re.compile(r"^(?:\*\*_(?P<a>.+?)\._\*\*|_(?P<b>[^_]+?)\._|_(?P<c>[^_.]+?)\. (?=[A-Z]))"
                    r" ?(?P<text>.*)$")
_USAGE = re.compile(r"^(?P<base>.+?) \((?P<usage>[^)]*)\)$")
_SECTIONS = {"actions": "action", "bonus actions": "bonus_action",
             "reactions": "reaction", "legendary actions": "legendary_action",
             "traits": "trait"}
_ANCHOR = {"trait": "traits", "action": "actions", "bonus_action": "bonus_actions",
           "reaction": "reactions", "legendary_action": "legendary_actions"}


def _damage_terms(text: str) -> tuple[list[dict[str, Any]], str]:
    terms: list[dict[str, Any]] = []
    rest = text.strip()
    while True:
        m = _DMG.match(rest) or _FLAT.match(rest)
        if not m or m.group("type").lower() not in DAMAGE:
            break
        g = m.groupdict()
        mod = int(g.get("mod") or 0) * (-1 if g.get("sign") in ("−", "-") else 1)
        terms.append({"average": int(g["avg"]),
                      "dice": ({"count": int(g["n"]), "die": f"d{g['d']}", "modifier": mod}
                               if g.get("n") else None),
                      "damage_type": g["type"].lower()})
        rest = rest[m.end():]
        nxt = re.match(r"^ plus ", rest)
        if not nxt:
            break
        rest = rest[nxt.end():]
    return terms, rest.strip()


def _whose(phrase: str) -> str:
    """``its next turn`` belongs to the condition's subject (the target);
    ``the giant's next turn`` to the creature using the entry (the source)."""
    return {"its": "target", "your": "caster"}.get(phrase, "source")


def _possessor(phrase: str) -> str | None:
    """``the giant's`` → ``giant``; ``its`` → None (the target owns it)."""
    m = re.fullmatch(r"the ([\w' -]+?)'s", phrase)
    return m.group(1) if m else None


def _check_possessors(heading: str, block: list[dict[str, Any]]) -> None:
    """A source-owned turn must name this block's own creature; anything else
    is not silently attributed to the source (it becomes ``unresolved``)."""
    words = {w.rstrip("s") for w in heading.lower().replace("-", " ").split()}

    def visit(node: Any, entry: dict[str, Any]) -> None:
        if isinstance(node, dict):
            if "turn_of" in node and node.get("possessor"):
                last = node["possessor"].lower().split()[-1].rstrip("s")
                if last not in words:
                    node["turn_of"] = "unresolved"
                    entry["reasons"].append(f"turn owner {node['possessor']!r} is not this "
                                            "creature; not attributed")
                    entry["classification"] = "conditional"
            for v in node.values():
                visit(v, entry)
        elif isinstance(node, list):
            for v in node:
                visit(v, entry)

    for e in block:
        visit({k: v for k, v in e.items() if k not in ("reasons",)}, e)


_COND = r"the (\w+) condition(?: \(escape DC (\d+)\))?"
_UNTIL = r"until the (start|end) of (its|your|the [\w' -]+?'s) next turn"


_DICE = r"(?P<avg>\d+) \((?P<n>\d+)d(?P<d>\d+)(?: (?P<sg>[+−-]) (?P<mod>\d+))?\)"


def _dice_term(m: re.Match[str], damage_type: str) -> dict[str, Any]:
    mod = int(m["mod"] or 0) * (-1 if m["sg"] in ("−", "-") else 1)
    return {"average": int(m["avg"]), "dice": {"count": int(m["n"]), "die": f"d{m['d']}",
                                               "modifier": mod},
            "damage_type": damage_type.lower()}


def _rider_shapes(rest: str) -> dict[str, Any] | None:
    """Bounded rider shapes beyond a single condition (C4)."""
    if m := re.match(rf"^(?:,? |—)(?P<mode>plus|or) {_DICE} (?P<type>[A-Z][a-z]+) damage if "
                     r"(?P<when>the attack roll had Advantage|the target is Bloodied|"
                     r"the [\w' -]+? is Bloodied|the [\w' -]+? moved (?P<ft>\d+)\+ feet "
                     r"straight toward the target immediately before the hit)"
                     r"(?P<tail>[.—].*)$", rest):
        # A trailing sentence or em-dash clause must itself be typed, or the
        # whole rider stays untyped.
        tail, extra = m["tail"], {}
        if tail.startswith("—"):
            t = re.fullmatch(rf"—plus {_DICE} (?P<type>[A-Z][a-z]+) damage\.", tail)
            if not t:
                return None
            extra = {"additional_damage": [_dice_term(t, t["type"])]}
        elif tail != ".":
            sub, res = _rider(tail)
            if res or not sub:
                return None
            extra = sub
        when = m["when"]
        cond = ({"attack_roll_had_advantage": True} if "Advantage" in when else
                {"target_bloodied": True} if when.startswith("the target") else
                {"source_moved_straight_toward_target_ft_min": int(m["ft"])} if m["ft"] else
                {"source_bloodied": True})
        out_ = {"conditional_damage": {"mode": "additional" if m["mode"] == "plus" else "instead",
                                       "term": _dice_term(m, m["type"]), "when": cond},
                "needs_position": bool(m["ft"])}
        assert not set(out_) & set(extra) - {"needs_position"}, (out_, extra)
        out_["needs_position"] = out_["needs_position"] or extra.pop("needs_position", False)
        return {**out_, **extra}
    if m := re.match(rf"^\. If (?:the )?target is (?:a )?(?P<size>\w+) or smaller(?: creature)? "
                     r"and the [\w' -]+? moved (?P<ft>\d+)\+ feet straight toward it "
                     rf"immediately before the hit, the target takes an extra {_DICE} "
                     r"(?P<type>[A-Z][a-z]+) damage and has the (?P<cond>\w+) condition\.$",
                     rest):
        return {"conditional_damage": {"mode": "additional", "term": _dice_term(m, m["type"]),
                                       "when": {"source_moved_straight_toward_target_ft_min":
                                                int(m["ft"]),
                                                "target_maximum_size": m["size"].lower()}},
                "effect": {"family": "condition_effect", "condition": m["cond"].lower(),
                           "effect": "applies"},
                "applies_to": "target", "needs_position": True}
    if m := re.match(r"^(?:\. If the target is a (?P<size>\w+) or smaller creature, it|"
                     r"(?:,? and |\. )?[Tt]he target) has the Grappled condition \(escape DC "
                     r"(?P<esc>\d+)\), and it has the (?P<cond>\w+) condition until the grapple "
                     r"ends\.$", rest):
        return {"effect": {"family": "condition_effect", "condition": "grappled",
                           "effect": "applies"},
                "escape_dc": int(m["esc"]), "applies_to": "target",
                "maximum_size": m["size"].lower() if m["size"] else None,
                "linked": {"effect": {"family": "condition_effect",
                                      "condition": m["cond"].lower(), "effect": "applies"},
                           "until": "the grapple ends"}}
    if m := re.match(r"^(?:,? and the target|The target) is pushed up to (?P<ft>\d+) feet "
                     r"straight away from the [\w' -]+?(?: and has the (?P<cond>\w+) "
                     r"condition)?\.$", rest):
        out: dict[str, Any] = {"forced_movement": {"distance_ft_up_to": int(m["ft"]),
                                                   "direction": "straight_away"},
                               "applies_to": "target", "needs_position": True}
        if m["cond"]:
            out["effect"] = {"family": "condition_effect", "condition": m["cond"].lower(),
                             "effect": "applies"}
        return out
    return None


def _rider(rest: str) -> tuple[dict[str, Any] | None, str | None]:
    """Typed hit/failure riders; anything else is verbatim residue."""
    rest = rest.strip()
    if rest in ("", "."):
        return None, None
    if shaped := _rider_shapes(rest):
        return shaped, None
    patterns = [
        (rf"^(?:,? and |\. )?[Tt]he target has {_COND}(?: {_UNTIL})?\.$", None),
        (rf"^(?:\. )?If the target is a (\w+) or smaller creature, it has {_COND}"
         rf"(?: {_UNTIL})?\.$", "size"),
    ]
    for pattern, kind in patterns:
        m = re.match(pattern, rest)
        if not m:
            continue
        g = m.groups()
        if kind == "size":
            size, cond, esc, edge, owner = g
        else:
            size, (cond, esc, edge, owner) = None, g
        if cond.lower() not in CONDITIONS:
            return None, rest
        effect: dict[str, Any] = {
            "effect": {"family": "condition_effect", "condition": cond.lower(),
                       "effect": "applies"},
            "applies_to": "target",
            "escape_dc": int(esc) if esc else None,
            "maximum_size": size.lower() if size else None,
            "duration": turn(f"{edge}_of_turn", _whose(owner), _possessor(owner)) if edge else None,
        }
        return effect, None
    m = re.match(r"^\. If the target is (?:a non-(\w+) creature|a creature that isn't an (\w+) "
                 r"or (\w+)), it is subjected to the following effect\. _(\w+) Saving Throw:_ "
                 rf"DC (\d+)\. _Failure:_ The target has {_COND} {_UNTIL}\.$", rest)
    if m:
        excluded = [x.lower() for x in m.groups()[:3] if x]
        ability, dc, cond, esc, edge, owner = m.groups()[3:]
        return {"rider_save": {"save": ability.lower(), "dc": int(dc),
                               "target_excludes": excluded,
                               "on_failure": {"family": "condition_effect",
                                              "condition": cond.lower(), "effect": "applies"},
                               "duration": turn(f"{edge}_of_turn", _whose(owner), _possessor(owner))},
                "applies_to": "target"}, None
    return None, rest


_TYPES = ("aberration", "beast", "celestial", "construct", "dragon", "elemental", "fey",
          "fiend", "giant", "humanoid", "monstrosity", "ooze", "plant", "undead", "demon",
          "elf")
_AREA = (r"(?:a|an) (?P<size>\d+)-foot(?P<radius>-radius)?(?:-long, (?P<width>\d+)-foot-wide)?"
         r"(?:, (?P<height>\d+)-foot-high)? (?P<shape>Cone|Line|Cube|Sphere|Cylinder|Emanation)")
#: Target clauses, order-independent. Each consumes its words and sets fields;
#: whatever no clause consumes is residue, never silently dropped.
_TARGET_CLAUSES: list[tuple[str, Any]] = [
    (r"\((?P<types>[A-Z][\w, ]+?) automatically fail the save\)",
     lambda m: {"automatic_failure_types": [t.strip().lower().rstrip("s") for t in
                                            re.split(r",? and |, ", m["types"])]}),
    (r"\((?P<types>\w+) succeed automatically\)",
     lambda m: {"automatic_success_types": [m["types"].lower().rstrip("s")]}),
    (r"\((?:the [\w' -]+?|it) can have (?:only )?(?:up to )?(?P<n>\w+) creatures? swallowed "
     r"at a time\)",
     lambda m: {"swallow_capacity": NUM.get(m["n"], m["n"])}),
    (r"in " + _AREA, lambda m: {"area": {
        "shape": m["shape"].lower(), "size_ft": int(m["size"]), "radius": bool(m["radius"]),
        "width_ft": int(m["width"]) if m["width"] else None,
        "height_ft": int(m["height"]) if m["height"] else None}}),
    (r"(?:originating from|centered on) a point (?:the [\w' -]+? |it )?can see within "
     r"(?P<n>\d+) feet(?: of (?:itself|it))?",
     lambda m: {"origin": {"point_within_ft": int(m["n"])},
                "requires_source_sees_point": True}),
    (r"(?:originating from|centered on) a point within (?P<n>\d+) feet(?: of (?:itself|it))?",
     lambda m: {"origin": {"point_within_ft": int(m["n"])}}),
    (r"while it is underwater", lambda m: {"source_environment": "underwater"}),
    (r"originating from (?:itself|the [\w' -]+?)(?= |$|,)", lambda m: {"origin": "source"}),
    (r"(?:and )?(?:that )?can see the [\w' -]+?(?:'s true form)?(?= |$|,)",
     lambda m: {"requires_target_sees_source": True}),
    (r"(?:that )?(?:the [\w' -]+?|it) can see(?= |$|,)",
     lambda m: {"requires_source_sees_target": True}),
    (r"within (?P<n>\d+) feet(?: of (?:itself|it|the [\w' -]+?))?(?= |$|,)",
     lambda m: {"within_ft": int(m["n"])}),
    (r"in the [\w' -]+?'s space", lambda m: {"in_source_space": True}),
    (r"(?:that is )?(?P<c>Charmed|Grappled)(?: or (?P<c2>Charmed|Grappled))? by the [\w' -]+?"
     r"(?= |$|,|\()",
     lambda m: {"related_to_source": [c.lower() for c in (m["c"], m["c2"]) if c]}),
    (r"that is willing or that has the (?P<cs>[\w, ]+?) condition",
     lambda m: {"willing_or_conditions": [c.strip().lower() for c in
                                          re.split(r",? or |, ", m["cs"])]}),
    (r"that has the (?P<c>\w+) condition", lambda m: {"has_conditions": [m["c"].lower()]}),
    (r"that has 0 Hit Points", lambda m: {"at_hit_points": 0}),
    (r"that isn't currently affected by this breath",
     lambda m: {"excludes": "currently affected by this effect"}),
    (r"(?:that|and) isn't (?!being\b)(?:an? )?(?P<t>\w+)(?: or (?:an? )?(?P<t2>\w+))?(?= |$|,)",
     lambda m: {"excludes_types": [t.lower() for t in (m["t"], m["t2"]) if t]}),
    (r"that starts its turn", lambda m: {"trigger": {"when": "start_of_turn",
                                                     "turn_of": "target"}}),
    (r"^(?:(?P<count>one|each|any)|up to (?P<n>\w+)) "
     r"(?:(?P<size>\w+) or smaller )?(?P<adj>living |Frightened )?"
     r"(?P<noun>creature|enemy|Beast or Humanoid|Humanoid and Giant|Humanoid)s?(?= |$|,)",
     lambda m: {"count": ("each" if m["count"] in ("each", "any") else
                          1 if m["count"] == "one" else NUM.get(m["n"], m["n"])),
                "maximum_size": m["size"].lower() if m["size"] else None,
                "living": m["adj"] == "living ",
                "has_conditions": ["frightened"] if m["adj"] == "Frightened " else [],
                "types": ([] if m["noun"] == "creature" else
                          ["enemy"] if m["noun"] == "enemy" else
                          [t.lower() for t in re.split(r" or | and ", m["noun"])])}),
]
_FILLER = re.compile(r"^(?:[,.;]|and|in|that|a|the)$")


def _predicates(targets: str) -> tuple[dict[str, Any], str | None]:
    """Typed save-target predicates by clause; residue is what no clause read."""
    rest = " " + targets.strip() + " "
    out: dict[str, Any] = {}
    # Object targeting is a named boundary: kept verbatim, never read as a
    # creature-type predicate.
    kept = None
    if om := re.search(r"(?:,? and |, )?(each object that isn't being worn or carried)", rest):
        kept, rest = om.group(1), rest[: om.start()] + " " + rest[om.end():]
    for pattern, build in _TARGET_CLAUSES:
        anchored = pattern.startswith("^")
        if anchored:
            m = re.match(pattern[1:], rest.strip())
        else:
            m = re.search(pattern, rest)
        if not m:
            continue
        for k, v in build(m).items():
            if isinstance(v, list) and isinstance(out.get(k), list):
                out[k] = sorted(set(out[k]) | set(v))
            elif k not in out or not out[k]:
                out[k] = v
        if anchored:
            rest = " " + rest.strip()[m.end():] + " "
        else:
            rest = rest[: m.start()] + " " + rest[m.end():]
    words = [w for w in re.split(r"(\s+|[,.;])", rest) if w.strip()]
    residue = ""
    if any(not _FILLER.match(w) for w in words):
        residue = re.sub(r"\s+", " ", rest).strip(" ,;.")
        residue = re.sub(r"\s+([,.;])", r"\1", residue)
    residue = "; ".join(x for x in (kept, residue) if x)
    return out, residue or None


def _attack(text: str) -> dict[str, Any] | None:
    text = text.replace("Melee or _Ranged Attack Roll:_", "_Melee or Ranged Attack Roll:_")
    m = re.match(
        r"^_(?P<kind>Melee|Ranged|Melee or Ranged) Attack Roll:_ (?P<bonus>[+−-]\d+)"
        r"(?: to hit)?(?: \((?P<adv>with Advantage [^)]*)\))?, "
        r"(?P<reach>.+?)\. _Hit:_ (?P<hit>.*?)(?: _Miss:_ (?P<miss>.*))?$", text)
    if not m:
        return None
    reach = m.group("reach")
    rm = re.fullmatch(r"(?:reach (\d+) (?:ft\.?|feet))?(?: or )?(?:range (\d+)(?:/(\d+))? "
                      r"(?:ft|feet))?", reach)
    terms, rest = _damage_terms(m.group("hit"))
    effect, residue = _rider(rest)
    if effect and "additional_damage" in effect:
        terms = terms + effect.pop("additional_damage")
    if effect and effect.get("conditional_damage", {}).get("mode") == "instead":
        effect["conditional_damage"]["replaces_hit_damage_index"] = 0
    reasons = []
    if m.group("adv"):
        reasons.append(f"Advantage predicate needs validated state: {m.group('adv')!r}")
    if not rm:
        reasons.append(f"reach/range not typed: {reach!r}")
    if not terms:
        reasons.append("hit prints no leading damage term")
    if residue:
        reasons.append(f"hit rider not typed: {residue!r}")
    if m.group("miss"):
        reasons.append(f"miss effect not typed: {m.group('miss')!r}")
    if effect and effect.get("duration") or effect and effect.get("rider_save"):
        reasons.append("timed/linked effect needs explicit actor-turn authority")
    if effect and effect.pop("needs_position", False):
        reasons.append("missing state: position/movement for the rider")
    untyped = [{"part": p, "text": x} for p, x in (("reach_or_range", None if rm else reach),
               ("hit", residue), ("miss", m.group("miss"))) if x]
    return {"kind": slug(m.group("kind")), "untyped_clauses": untyped,
            "attack_bonus": int(m.group("bonus").replace("−", "-")),
            "advantage_when": m.group("adv"),
            "reach_ft": int(rm.group(1)) if rm and rm.group(1) else None,
            "normal_range_ft": int(rm.group(2)) if rm and rm.group(2) else None,
            "long_range_ft": int(rm.group(3)) if rm and rm.group(3) else None,
            "hit_damage": terms, "hit_effect": effect, "untyped": reasons}


def _framed_save(frame: str, text: str) -> dict[str, Any] | None:
    """A save with a framing preamble, or with outcome branches the plain
    save shape does not read. Target reasons come from the plain shape."""
    sv = _save(text)
    if sv is None:
        hm = re.match(r"^_(?P<ab>\w+) Saving Throw:_ DC (?P<dc>\d+)(?:, (?P<t>.+?))?\. "
                      r"(?P<out>_.*)$", text)
        if not hm:
            return None
        probe = _save(f"_{hm['ab']} Saving Throw:_ DC {hm['dc']}, "
                      f"{hm['t'] or 'the target'}. _Failure:_ x")
        assert probe is not None, text
        sv = {**probe, "failure_damage": [], "failure_effect": None, "success": None,
              "untyped": [r for r in probe["untyped"]
                          if not r.startswith("failure rider not typed")
                          and (hm["t"] or not r.startswith("target predicate"))],
              "untyped_clauses": [c for c in probe["untyped_clauses"]
                                  if c["part"] == "targets" and hm["t"]]
              + [{"part": "outcomes", "text": hm["out"]}]}
        if not hm["t"]:
            # "Each creature whose space ... is targeted once by the following
            # effect": the participants are stated by the frame.
            sv["targets"] = {"stated_by": "frame"}
    if frame.strip():
        sv["untyped_clauses"].insert(0, {"part": "frame", "text": frame.strip()})
        sv["untyped"].append("frame not typed")
    return sv


def _save(text: str) -> dict[str, Any] | None:
    m = re.match(r"^_(?P<ability>\w+) Saving Throw:_ (?:DC (?P<dc>\d+)|DC equals your spell "
                 r"save DC|Your spell save DC), (?P<targets>.+?)\. "
                 r"_Failure:_ (?P<fail>.*?)(?: _Success:_ (?P<succ>.*?))?"
                 r"(?: _Failure or Success:_ (?P<both>.*))?$", text)
    if not m:
        return None
    tgt, tgt_residue = _predicates(m.group("targets"))
    terms, rest = _damage_terms(m.group("fail"))
    effect, residue = _rider(rest if not terms else rest)
    reasons = []
    if "area" in tgt or "in_source_space" in tgt:
        reasons.append("area membership needs explicit position authority")
    if "within_ft" in tgt:
        reasons.append("range needs explicit position authority")
    if "source_environment" in tgt:
        reasons.append("missing state: the source's recorded environment")
    if "trigger" in tgt:
        reasons.append("turn-start trigger needs explicit actor-turn authority")
    if tgt_residue:
        reasons.append(f"target predicate not typed: {tgt_residue!r}")
    if tgt.get("requires_target_sees_source"):
        reasons.append("visibility prerequisite: the target must see the source")
    if tgt.get("requires_source_sees_point"):
        reasons.append("visibility prerequisite: the source must see the area's origin point")
    if tgt.get("requires_source_sees_target"):
        reasons.append("visibility prerequisite: the source must see the target; refuses "
                       "unless validated visibility state exists")
    if residue:
        reasons.append(f"failure rider not typed: {residue!r}")
    if effect and effect.get("duration"):
        reasons.append("timed effect needs explicit actor-turn authority")
    if effect and effect.pop("needs_position", False):
        reasons.append("missing state: position/movement for the rider")
    succ = (m.group("succ") or "").strip()
    if succ and succ not in ("Half damage.", "Half damage only."):
        reasons.append(f"success effect not typed: {succ!r}")
    both, reuse_limit = m.group("both"), None
    if both and re.fullmatch(r"The [\w' -]+? can't take this action again until the start "
                             r"of its next turn\.", both.strip()):
        reuse_limit = {"kind": "once_until_start_of_own_turn"}
        reasons.append("missing state: actor-turn authority for the reuse limit")
        both = None
    if both:
        reasons.append(f"failure-or-success effect not typed: {both!r}")
    untyped = [{"part": p, "text": x} for p, x in (
        ("targets", tgt_residue), ("failure", residue),
        ("success", succ if succ not in ("", "Half damage.", "Half damage only.") else None),
        ("failure_or_success", both)) if x]
    if m.group("dc") is None:
        reasons.append("missing runtime input: the caster (identity, spellcasting class, "
                       "level and ability scores) for the spell save DC formula")
    return {"save": m.group("ability").lower(), "untyped_clauses": untyped,
            **({"reuse_limit": reuse_limit} if reuse_limit else {}),
            "dc": int(m.group("dc")) if m.group("dc") else {"formula_ref": "spells.saving_throws/spell_save_dc", "of": "caster"},
            "targets": tgt,
            "failure_damage": terms, "failure_effect": effect,
            "success": ("half_damage_only" if succ == "Half damage only." else
                        "half_damage" if succ == "Half damage." else None),
            "untyped": reasons}


# -- Multiattack: alternatives + replacements, certified per selection -------

_PART = re.compile(r"(?P<n>one|two|three|four|five|six) (?P<name>.+?) attacks?")


def _parts(alt: str) -> tuple[list[dict[str, Any]], list[str]]:
    parts: list[dict[str, Any]] = []
    residue: list[str] = []
    for clause in re.split(r",? and (?=(?:one|two|three|uses|can use|it can use|it uses|makes) )"
                           r"|, (?=(?:one|two|three|four|five|six|uses) )", alt.strip()):
        clause = re.sub(r"^(?:it |makes )", "", clause.strip().rstrip("."))
        if m := re.fullmatch(r"uses (.+?) (twice|three times)", clause):
            parts.append({"count": 2 if m.group(2) == "twice" else 3,
                          "uses_one_of": [m.group(1)], "if_available": False,
                          "optional": False})
            continue
        if m := re.fullmatch(r"a number of (?:(.+?) )?attacks equal to (.+)", clause):
            # Parameterized count (summons): the formula is in the record's
            # quote-verified parameters; the count is a missing input here.
            parts.append({"count": {"parameterized": m.group(2)},
                          **({"attack": m.group(1)} if m.group(1) else {"any_of": []})})
            continue
        if m := re.fullmatch(r"(one|two|three|four|five|six) (?:other )?attacks?, using (.+?) "
                             r"in any combination", clause):
            parts.append({"count": NUM[m.group(1)],
                          "any_of": [o.strip() for o in re.split(r",? or | and |, ", m.group(2))]})
        elif m := re.fullmatch(r"(one|two|three|four|five|six) (.+?) or (.+?) attacks?", clause):
            parts.append({"count": NUM[m.group(1)], "any_of": [m.group(2), m.group(3)]})
        elif m := _PART.fullmatch(clause):
            parts.append({"count": NUM[m.group("n")], "attack": m.group("name")})
        elif m := re.fullmatch(r"(?:uses|can use|it can use) (?:either )?(.+?)(?P<avail> if available)?",
                               clause):
            options = [o.strip() for o in re.split(r",? or |, ", m.group(1)) if o.strip()]
            parts.append({"count": 1, "uses_one_of": options,
                          "if_available": bool(m.group("avail")),
                          "optional": clause.startswith(("can use", "it can use"))})
        else:
            residue.append(clause)
    return parts, residue


def _multiattack(text: str) -> dict[str, Any]:
    first, _, tail = text.partition(". ")
    body = re.sub(r"^The [\w' -]+? makes ", "", first.strip().rstrip("."))
    alternatives: list[dict[str, Any]] = []
    residue: list[str] = []
    for alt in re.split(r", or it makes | or (?=uses )", body):
        cond = None
        if m := re.fullmatch(r"(.+?) if (it used .+?)", alt):
            alt, cond = m.group(1), m.group(2)
        if m := re.fullmatch(r"as many (.+?) attacks as it has heads", alt):
            alternatives.append({"parts": [{"count": {"per": "head"}, "attack": m.group(1)}],
                                 "condition": None})
            continue
        parts, res = _parts(alt)
        residue += res
        alternatives.append({"parts": parts, "condition": cond})
    replacements = []
    for m in re.finditer(r"It can replace (one|two|any|the (?P<the>[\w' -]+?)) attacks? with "
                         r"(?:a use of |an? )?(?P<with>.+?)(?P<avail> if available)?\.(?: |$)",
                         tail):
        quant = m.group(1)
        with_ = re.sub(r" attack$", "", m.group("with"))
        options = [o for o in re.split(r" or (?=\(B\))", with_)]
        options = [re.sub(r"^\([AB]\) ", "", o) for o in options]
        replacements.append({"replaces": ("any" if quant == "any" else
                                          {"attack": m.group("the")} if m.group("the") else
                                          NUM[quant]),
                             "with_one_of": options,
                             "if_available": bool(m.group("avail"))})
    leftover = re.sub(r"It can replace .+?\.(?: |$)", "", tail).strip()
    if leftover:
        residue.append(leftover)
    return {"alternatives": alternatives, "replacements": replacements, "residue": residue}


# -- Contributors ------------------------------------------------------------

#: Recurring contributors with exact typed meaning; each still needs state.
TYPED_CONTRIBUTORS: dict[str, tuple[dict[str, Any], str, list[str]]] = {
    # Each accepted-family payload is unchanged ("effects"); the predicate the
    # source states is carried beside it ("applies_when"), never inside it.
    "Magic Resistance": (
        {"effects": [{"family": "advantage", "state": "advantage",
                      "roll": {"actor": "subject", "context": "saving_throw",
                               "ability": None}}],
         "applies_when": "the effect forcing the save is a spell or other magical effect"},
        "the forcing effect's magical/non-magical classification", ["target_save"]),
    "Legendary Resistance": (
        {"save_override": {"on": "failed_saving_throw", "may_choose": "success",
                           "chooser": "gamemaster", "usage": "per_entry_limit"}},
        "the usage counter and a recorded GameMaster choice", ["target_save"]),
    "Pack Tactics": (
        {"effects": [{"family": "advantage", "state": "advantage",
                      "roll": {"actor": "subject", "context": "attack_roll",
                               "ability": None}}],
         "applies_when": {"ally_within_ft_of_target": 5, "ally_not": "incapacitated"}},
        "explicit position of allies and target", ["own_attack"]),
    "Sunlight Sensitivity": (
        {"effects": [{"family": "advantage", "state": "disadvantage",
                      "roll": {"actor": "subject", "context": ctx, "ability": None}}
                     for ctx in ("ability_check", "attack_roll")],
         "applies_when": "the subject is in sunlight"},
        "a recorded in-sunlight environment state", ["own_attack", "own_check"]),
}

def _adv(state: str, context: str, actor: str = "subject") -> dict[str, Any]:
    return {"family": "advantage", "state": state,
            "roll": {"actor": actor, "context": context, "ability": None}}


#: Applicability of every standing trait that bears on play, read per name:
#: who it applies to, which roll/damage contexts of that subject it touches,
#: and what it needs. ``effects`` hold accepted payloads where the meaning is
#: typed; ``needs`` is None when its predicate rests only on recorded state the
#: roster already has (hit points, conditions, the forcing save). Contexts:
#: own_attack, own_check, target_save (its own saves), rolls_against,
#: damage_taken, melee_hits_against, zero_hp_outcome. An empty context list
#: means it changes no admitted operation of that subject.
_REVIVAL = ("self", [], None, "revival after death; resurrection is a non-goal and the death "
            "determination itself is unchanged")
CONTRIBUTOR_REVIEW: dict[str, tuple[str, list[str], str | None, str]] = {
    **{n: _REVIVAL for n in (
        "Eldritch Restoration", "Diabolical Restoration", "Exalted Restoration",
        "Elemental Restoration", "Demonic Restoration", "Celestial Restoration",
        "Fiendish Restoration", "Hellish Restoration", "Undead Restoration", "Spirit Jar")},
    "Evasion": ("self", ["target_save"], None,
                "Dexterity save for half damage: success takes none, failure half; not while "
                "Incapacitated (recorded condition)"),
    "Fire Aura": ("self", [], "unsupported: end-of-turn aura damage to creatures in an "
                  "Emanation (needs actor-turn and position)",
                  "end-of-turn damage only; no instance triggers on a hit"),
    "Heat Aura": ("self", [], "unsupported: periodic aura damage",
                  "end-of-turn damage to nearby creatures; touches no admitted roll"),
    "Barbed Hide": ("self", [], "unsupported: periodic grapple damage",
                    "start-of-turn damage to grappling/grappled creatures"),
    "Bloodied Frenzy": ("self", ["own_attack", "target_save"], None,
                        "Advantage on attack rolls and saves while Bloodied (recorded HP)"),
    "Corrosive Form": ("self", ["melee_hits_against"], "unsupported: on-hit damage and weapon "
                       "degradation", "affects creatures that hit it"),
    "Acid Absorption": ("self", ["damage_taken"], "unsupported: absorption heals (healing is "
                        "a non-goal)", "acid damage"),
    "Fire Absorption": ("self", ["damage_taken"], "unsupported: absorption heals",
                        "fire damage"),
    "Lightning Absorption": ("self", ["damage_taken"], "unsupported: absorption heals",
                             "lightning damage"),
    "Light Sensitivity": ("self", ["own_attack"], "missing state: lighting",
                          "Disadvantage on its attack rolls in Bright Light"),
    "Training": ("self", ["own_check"], "missing runtime input: the GameMaster's skill choice",
                 "proficiency and Advantage in one chosen skill"),
    "Swarm": ("self", ["zero_hp_outcome"], None,
              "the source prohibition is unconditional. It is relevant to admitted "
              "operations only where character-style zero-HP treatment applies to the "
              "subject: then the natural-20 Death Saving Throw and the Stable 1d4-hour 1 "
              "Hit Point regains do not happen, because 'When an exception and a general "
              "rule disagree, the exception wins' (playing-the-game.md 109); the rest of "
              "the death-save rule is unchanged. The default monster death determination "
              "is unaffected"),
    "Sunlight Weakness": ("self", ["own_attack", "own_check", "target_save"],
                          "missing state: sunlight", "Disadvantage on D20 Tests in sunlight"),
    "Sunlight": ("self", ["own_attack", "own_check"], "missing state: sunlight",
                 "Disadvantage in sunlight; start-of-turn radiant damage (unsupported)"),
    "Siege Monster": ("self", [], None, "double damage to objects and structures"),
    "Magic Rope": ("self", [], None, "gates the Entangling Rope action only"),
    "Fire Form": ("self", [], "unsupported: space-entry damage", "movement-triggered damage"),
    "Water Susceptibility": ("self", [], "unsupported: environment damage", "water damage"),
    "Aversion to Fire": ("self", ["own_attack", "own_check"], "missing state: actor-turn timing "
                         "after fire damage", "Disadvantage until the end of its next turn"),
    "Ooze Cube": ("self", [], "unsupported: engulf space", "creatures entering its space"),
    "Incorporeal Movement": ("self", [], "unsupported: object-ending damage", "movement"),
    "Draconic Origin": ("self", ["damage_taken", "own_attack"], "missing runtime input: the "
                        "recorded Draconic Origin choice", "sets resistance and damage type"),
    "Aura of Authority": ("self_and_allies", ["own_attack", "target_save"],
                          "missing state: position", "Advantage within its emanation"),
    "Multiple Heads": ("self", ["damage_taken", "zero_hp_outcome"], "unsupported: head "
                       "loss and regrowth", "damage threshold per turn"),
    "Blurred Form": ("self", ["rolls_against"], None,
                     "attack rolls against it have Disadvantage unless it is Incapacitated "
                     "(recorded condition)"),
    "Adhesive": ("self", ["melee_hits_against"], "unsupported: grapple on touch",
                 "creatures touching it"),
    "Confer Fire Resistance": ("rider", [], None, "applies to its rider, not to itself"),
    "Regeneration": ("self", ["zero_hp_outcome"], "unsupported: per-turn healing changes when "
                     "it dies", "healing is a non-goal"),
    "Greater Magic Resistance": ("self", ["target_save"], "missing state: the forcing "
                                 "effect's magical classification", "automatic success vs "
                                 "magic"),
    "Blood Frenzy": ("self", ["own_attack"], None,
                     "Advantage on attack rolls against a creature missing Hit Points "
                     "(recorded HP)"),
    "Inscrutable": ("others", ["others_check_about_subject"], "missing state: whether a "
                    "Wisdom (Insight) check is made to ascertain the subject's intentions or "
                    "sincerity", "Disadvantage on those Insight checks; remote observation and "
                    "thought detection are spell effects, not typed"),
    "Reflective Carapace": ("self", [], None, "spells only"),
    "Loathsome Limbs": ("self", ["damage_taken"], "unsupported: limb severing", "slashing "
                        "damage threshold"),
    "Running Water": ("self", [], "unsupported: environment damage", "running water"),
    "Stake to the Heart": ("self", [], "unsupported: destruction/paralysis by stake",
                           "a specific narrative act"),
    "Freeze": ("self", [], None, "Speed change after cold damage; touches no admitted roll"),
    "Undead Fortitude": ("self", ["zero_hp_outcome"],
                         "missing state: the triggering damage event (amount taken, damage "
                         "type and whether it was a Critical Hit), resolved synchronously "
                         "with that damage",
                         "applies to these monsters whatever their zero-HP treatment; not "
                         "healing"),
    "Bloodied Fury": ("self", ["own_attack"], None,
                      "Advantage on melee attack rolls while Bloodied (recorded HP)"),
    "Life Bond": ("self", [], None, "healing shared with the caster; healing is a non-goal"),
    "Shared Resistances": ("caster", [], None, "the caster gains one of the spirit's "
                           "resistances; the spirit's own operations are unaffected"),
    "Bound": ("amulet_wearer", ["related_creature_damage_taken"], "unsupported: damage "
              "transfer (half, rounded up) from the amulet's wearer to the guardian; missing "
              "relation: the amulet's wearer; missing state: position within 60 feet",
              "applies to damage the wearer takes, not to the guardian's own rolls"),
}
#: Typed effects for reviewed contributors whose predicate rests on recorded
#: state; accepted payloads beside their predicate.
CONTRIBUTOR_EFFECTS: dict[str, dict[str, Any]] = {
    "Bloodied Frenzy": {"effects": [_adv("advantage", "attack_roll"),
                                    _adv("advantage", "saving_throw")],
                        "applies_when": {"subject_bloodied": True}},
    "Bloodied Fury": {"effects": [_adv("advantage", "attack_roll")],
                      "applies_when": {"subject_bloodied": True, "attack": "melee"}},
    "Blood Frenzy": {"effects": [_adv("advantage", "attack_roll")],
                     "applies_when": {"target_missing_hit_points": True}},
    "Blurred Form": {"effects": [_adv("disadvantage", "attack_roll", "against_subject")],
                     "applies_when": {"subject_not": "incapacitated"}},
    "Swarm": {"effects": [{"family": "hit_point_regain_prohibition", "hit_points": True,
                           "temporary_hit_points": True}],
              },
    "Undead Fortitude": {
        "family": "zero_hit_point_save",
        "trigger": "damage reduces the subject to 0 Hit Points",
        "save": "constitution", "dc": {"base": 5, "plus": "damage_taken"},
        "unless": {"damage_type": "radiant", "critical_hit": True},
        "on_success": {"set_hit_points": 1, "instead_of": "0 Hit Points"}},
    "Inscrutable": {"effects": [{"family": "advantage", "state": "disadvantage",
                                 "roll": {"actor": "against_subject", "context": "ability_check",
                                          "ability": "wisdom"}}],
                    "skill": "insight",
                    "purpose": "to ascertain the subject's intentions or sincerity"},
    "Evasion": {"save_damage_override": {"save": "dexterity", "on": "half_damage_effects",
                                         "success": "no_damage", "failure": "half_damage"},
                "applies_when": {"subject_not": "incapacitated"}},
}
#: Traits that remove an ability-check requirement the roster admits.
CHECK_REMOVALS: dict[str, dict[str, Any]] = {
    "Spider Climb": {"family": "check_requirement_removal",
                     "check": "glossary.climbing/difficult_climb",
                     "surfaces": "difficult surfaces, including along ceilings"},
    "Ice Walk": {"family": "check_requirement_removal",
                 "check": "glossary.climbing/difficult_climb", "surfaces": "icy surfaces",
                 "also": {"difficult_terrain_of": ["ice", "snow"], "extra_movement": False}},
}

#: Reviewed by name (``review-allowlist`` in the README): effects on movement,
#: senses, breathing, communication, light, planes or carrying, which change no
#: roster roll, DC, damage or defense. Anything not listed and not typed blocks.
NO_ROSTER_EFFECT: dict[str, str] = {n: why for why, names in {
    "movement or position only": [
        "Abduct", "Aberrant Ground", "Agile", "Air Form", "Amorphous", "Aquatic Charge",
        "Bubble Dash", "Charge", "Compression", "Earth Glide", "Flyby",
        "Jumper", "Leap", "Prowl", "Reel", "Running Leap", "Standing Leap",
        "Teleport", "Tree Stride", "Tunneler", "Water Form", "Web Walker",
        "Ethereal Jaunt", "Ethereal Stride", "Fey Step"],
    "a list header; each listed weakness is its own entry, classified individually": [
        "Vampire Weakness"],
    "standard actions outside the roster (their results are recorded state)": [
        "Cunning Action", "Deathless Agility", "Hasten", "Nimble Escape", "Shadow Stealth"],
    "senses, communication or knowledge only": [
        "Divine Awareness", "Ethereal Sight", "Iron Scent", "Probing Telepathy",
        "Sense Magic", "Shark Telepathy", "Shielded Mind", "Speak with Beasts and Plants",
        "Telepathic Bond", "Treasure Sense", "Vampiric Connection"],
    "breathing, carrying, light or bookkeeping only": [
        "Amphibious", "Beast of Burden", "Ephemeral", "Forbiddance", "Hold Breath",
        "Ignited Illumination", "Illumination", "Immutable Form", "Limited Amphibiousness",
        "Water Breathing"],
}.items() for n in names}

def _observer_check(text: str) -> dict[str, Any] | None:
    """A source-fixed check another creature makes about this one (Mimicry,
    Transparent): an admitted skill check with its source predicate."""
    m = re.search(r"(?P<who>A hearer|A creature that hears the sounds|a creature) (?:can "
                  r"discern the sounds are imitations|can tell they are imitations|must succeed "
                  r"on a DC (?P<dc0>\d+) (?P<ab0>\w+) \((?P<sk0>\w+)\) check to notice the "
                  r"[\w' -]+? if the creature hasn't witnessed the [\w' -]+? move or otherwise "
                  r"act)(?: only)? with a successful DC (?P<dc>\d+) (?P<ab>\w+) \((?P<sk>\w+)\) "
                  r"check|(?P<who2>a creature) must succeed on a DC (?P<dc2>\d+) (?P<ab2>\w+) "
                  r"\((?P<sk2>\w+)\) check to notice the [\w' -]+? if the creature hasn't "
                  r"witnessed the [\w' -]+? move or otherwise act", text)
    if not m:
        return None
    if m["dc2"]:
        return {"made_by": "another creature", "purpose": "to notice the subject",
                "check": {"ability": m["ab2"].lower(), "skill": m["sk2"].lower(),
                          "dc": int(m["dc2"])},
                "only_if": {"checker_has_not_witnessed_subject_move_or_act": True},
                "needs": "whether the checking creature has witnessed the subject move or act"}
    return {"made_by": m["who"][0].lower() + m["who"][1:],
            "purpose": "to discern the sounds are imitations",
            "check": {"ability": m["ab"].lower(), "skill": m["sk"].lower(), "dc": int(m["dc"])},
            "needs": "whether the checking creature heard the imitated sounds"}


#: Named mechanics outside the roster's bounded shapes (deferred, individually).
NAMED_DEFERRED: dict[str, str] = {
    "Shape-Shift": "changes form; form-dependent entries need a recorded current form",
    "Incubus Form": "replaces the whole stat block",
    "Succubus Form": "replaces the whole stat block",
    "Berserk": "a per-turn random-target behaviour mechanic",
    "Coven Magic": "shared spellcasting (general spell execution is a non-goal)",
    "Spell Storing": "stores and casts a spell (non-goal)",
    "Animate Trees": "creates creatures",
    "Create Specter": "creates a creature",
    "Create Whirlwind": "creates an area effect with its own lifecycle",
    "Troll Spawn": "creates a creature",
    "Roar": "a rotating sequence of effects with its own lifecycle",
    "Destroy Metal": "object destruction",
    "Soul Bag": "item-gated action",
    "Reactive": "extra Reactions (reactions are deferred)",
    "Reactive Heads": "extra Reactions (reactions are deferred)",
    "Swoop": "drops a grappled creature from the air (falling outside the roster)",
}

_KEYWORDS = re.compile(r"Advantage|Disadvantage|saving throw|attack roll|damage|Armor Class|"
                       r"\bAC\b|Hit Points|condition|succeed instead|Darkness|Speed", re.I)


def _granted_conditions(text: str) -> list[str]:
    """Only an unconditional standing grant ("The stalker has the Invisible
    condition.") maps through the condition's typed facts; a mention inside a
    conditional sentence is an ordinary contributor and blocks conservatively."""
    m = re.fullmatch(r"The [\w'-]+(?: [\w'-]+){0,2} has the (\w+) condition\.", text.strip())
    return [m.group(1).lower()] if m and m.group(1).lower() in CONDITIONS else []


def _condition_semantics(index: dict[str, Any], condition: str) -> dict[str, Any]:
    """What a granted condition does, from G1's typed condition facts."""
    own, against, contextual = [], [], []
    for comp in index.get(f"glossary.{condition}", []):
        for f in comp["facts"]:
            if f["family"] not in ("advantage", "automatic_outcome", "critical_hit_rule"):
                continue
            actor = f.get("roll", {}).get("actor")
            ctx = f.get("roll", {}).get("context")
            where = f"glossary.{condition}/{comp['semantic_key']}"
            if comp["handling"] != "structured" or comp["applies_when"] is not None:
                contextual.append(where)
            (own if actor == "subject" else against).append(f"{where}:{ctx}")
    return {"own_rolls": own, "rolls_against": against, "contextual": contextual}


# -- Sub-clause dispositions (C5; Codex C4 review finding 1) ------------------
#
# Every clause the entry parsers leave untyped is split into exact pieces
# (sentences, conjuncts, leading predicates and branch labels) that rebuild it
# byte for byte. Each piece gets exactly one disposition:
#
# * ``typed``: a source fact in ``typed`` (it stays in the source part);
# * ``unsupported``: a genuinely different engine, named by its cluster;
# * ``no_mechanical_consequence``: narrative information only;
# * ``untyped``: an ordinary shape not yet typed (missing source authority).
#
# Typing a piece states what the source says; what the runtime still needs
# (position, actor-turn, elapsed time, a recorded choice) is capability.

_CONJUNCT = re.compile(
    r"(?<=[.])\s+(?=[A-Z_*])"                     # sentence boundary
    r"|(?<=:_)\s+(?!DC )"                         # after a branch label
    r"|\s+(?=_[A-Z][\w ]*?:_)"                    # before a branch label
    r"|;\s+(?![^()]*\))(?:and\s+)?"               # semicolon conjuncts
    r"|,\s+(?=and (?:the target|it|its|the [a-z][\w' -]*? (?:can|has|pulls|moves))\b)"
    r"|\s+(?=and (?:repeats|takes|subtracts|can't|has|doesn't|is transported|"
    r"loses|it takes|it has)\b)"
    r"|\s+(?=but has)"
    r"|,\s+(?=which )"
    r"|,\s+(?=at which point the)"
    r"|,\s+(?=(?:is suffocating|has the|and takes|takes|can't cast)\b)"
    r"|,\s+(?=(?:its|it) (?:Speed|Hit Point maximum|gains no)\b)")
_PREDICATE = re.compile(
    r"^(?P<p>(?:If|While|Until|Otherwise|At the end of each of its turns)\b[^,]*?),\s+"
    r"(?P<rest>.+)$", re.S)
_COND_WORDS = "|".join(sorted((c.capitalize() for c in CONDITIONS), key=len, reverse=True))
_CONDS = rf"(?P<conds>(?:{_COND_WORDS})(?:(?:,| and|, and) (?:{_COND_WORDS}))*)"
_SUBJ = r"(?:(?:[Tt]he target|[Ii]t|which) )?(?:also )?"
_WHOSE_TURN = r"(?P<whose>its|the target's|this|the [\w' -]+?'s)"
_DMG_TERM = r"(?P<avg>\d+) \((?P<n>\d+)d(?P<d>\d+)(?: (?P<sg>[+−-]) (?P<mod>\d+))?\)"


def _conds(text: str) -> list[str]:
    return [c.lower() for c in re.findall(_COND_WORDS, text)]


def _turn(whose: str) -> str:
    return ("target" if whose in ("its", "the target's") else
            "this_turn" if whose == "this" else "source")


def _until(m: re.Match[str]) -> dict[str, Any]:
    return {"until": f"{m['edge']}_of_turn", "turn": "this" if m["whose"] == "this"
            else "next", "turn_of": _turn(m["whose"])}


_TIMED = rf" until the (?P<edge>start|end) of {_WHOSE_TURN} (?:next turn|turn)"
_ENDS = (r"(?P<ends>(?:,? (?:or )?until it takes damage|,? (?:or )?until it ends its turn "
         r"with the [\w' -]+? out of line of sight|,? (?:or )?until a creature within 5 feet of "
         r"it takes an action to wake it)+)?")


def _end_events(text: str | None) -> list[Any]:
    out: list[Any] = []
    if text and re.search(r"takes (?:any )?damage", text):
        out.append("target_takes_damage")
    if text and (m := re.search(r"a creature within (\d+) feet of it takes an action to wake "
                                r"it", text)):
        out.append({"event": "woken_by_an_action", "by_creature_within_ft": int(m[1])})
    if text and re.search(r"out of line of sight", text):
        out.append("ends_turn_out_of_line_of_sight")
    return out


def _cond_payloads(conds: list[str]) -> list[dict[str, Any]]:
    return [{"family": "condition_effect", "condition": c, "effect": "applies"} for c in conds]


#: (family, pattern on the normalized piece, builder, needs). ``needs`` names
#: what an execution must validate; it is capability, never source.
_READERS: list[tuple[str, str, Any, list[str]]] = [
    ("grapple",
     r"^(?:(?:it|the target|The target) has|the [\w' -]+? can give it) the Grappled condition "
     r"\(escape DC (?P<dc>\d+)\)(?: from (?P<app>one of (?P<of>two|four|six|ten) \w+|both "
     r"(?:of the [\w' -]+?'s )?[\w ]+?|all (?P<all>\w+) \w+))?(?P<instead> instead of dealing "
     r"damage)?$",
     lambda m: {"family": "grapple", "condition": "grappled", "escape_dc": int(m["dc"]),
                **({"appendages": m["app"]} if m["app"] else {}),
                **({"instead_of_damage": True} if m["instead"] else {})},
     ["missing state: the source's occupied appendages (grapples held)"]),
    ("grapple",
     r"^(?:the target |it )?(?:can give it|has) the Grappled condition \(escape DC (?P<dc>\d+)\)$",
     lambda m: {"family": "grapple", "condition": "grappled", "escape_dc": int(m["dc"])},
     []),
    ("timed_condition",
     rf"^{_SUBJ}has the {_CONDS} conditions?{_TIMED}$",
     lambda m: {"effects": _cond_payloads(_conds(m["conds"])), "duration": _until(m)},
     ["missing state: actor-turn authority for the duration"]),
    ("timed_condition",
     rf"^{_SUBJ}has the {_CONDS} conditions?,?(?: instead of the "
     rf"(?P<inst>\w+) condition,?)? for (?P<n>\d+) (?P<unit>minute|hour)s?{_ENDS}$",
     lambda m: {"effects": _cond_payloads(_conds(m["conds"])),
                "duration": {"amount": int(m["n"]), "unit": m["unit"]},
                **({"replaces_condition": m["inst"].lower()} if m["inst"] else {}),
                **({"ends_early_when": _end_events(m["ends"])} if m["ends"] else {})},
     ["missing state: elapsed-time authority for the duration"]),
    ("linked_condition",
     rf"^{_SUBJ}has the {_CONDS} conditions? until the "
     r"(?P<link>grapple|curse|song) ends$",
     lambda m: {"effects": _cond_payloads(_conds(m["conds"])), "while": m["link"]}, []),
    ("condition",
     rf"^{_SUBJ}has the {_CONDS} conditions?(?: instead "
     r"of the (?P<inst>\w+) condition)?(?P<rep> and repeats the save at the end of "
     r"(?P<when>each of its turns|its next turn if it is still Restrained), ending the effect on "
     r"itself on a success)?$",
     lambda m: {"effects": _cond_payloads(_conds(m["conds"])),
                **({"replaces_condition": m["inst"].lower()} if m["inst"] else {}),
                **({"repeat_save": {"at": "end_of_each_of_its_turns" if "each" in m["when"]
                                    else "end_of_its_next_turn_if_still_restrained",
                                    "ends_on": "success"}} if m["rep"] else {})},
     []),
    ("condition_until_repeat",
     rf"^The target has the {_CONDS} condition until the end of its next turn,? (?:at which "
     r"point|when) it repeats the save$",
     lambda m: {"effects": _cond_payloads(_conds(m["conds"])),
                "duration": {"until": "end_of_turn", "turn": "next", "turn_of": "target"},
                "repeat_save": {"at": "end_of_its_next_turn", "turn_of": "target",
                                "once": True}},
     ["missing state: actor-turn authority for the duration and repeat save"]),
    ("condition_ends_early",
     r"^which ends early if the target takes (?:any )?damage(?: or a creature within 5 feet "
     r"of it takes an action to wake it)?$",
     lambda m: {"ends_early_when": _end_events(m.string)}, []),
    ("effect_ends",
     r"^This effect ends for the target if it takes damage or a creature within 5 feet of it "
     r"takes an action to wake it$",
     lambda m: {"ends_early_when": _end_events(m.string)}, []),
    ("effect_lasts",
     r"^This effect lasts until the (?P<edge>end|start) of (?P<whose>its) next turn$",
     lambda m: {"duration": _until(m), "scope": "sentence_effects_above"},
     ["missing state: actor-turn authority for the duration"]),
    ("speed_change",
     rf"^(?:the target's|its) Speed (?P<chg>decreases by (?P<ft>\d+) feet|is halved|is 0)"
     rf"(?:{_TIMED})?$",
     lambda m: {"family": "timed_speed_change",
                "change": ("decrease" if m["ft"] else "halve" if "halved" in m["chg"]
                           else "set_to"),
                **({"feet": int(m["ft"])} if m["ft"] else
                   {"feet": 0} if m["chg"] == "is 0" else {}),
                **({"duration": _until(m)} if m["edge"] else {})},
     ["missing state: actor-turn authority for the duration"]),
    ("ac_penalty",
     rf"^the target takes a [−-](?P<n>\d+) penalty to AC{_TIMED}$",
     lambda m: {"family": "timed_ac_modifier", "modifier": -int(m["n"]), "duration": _until(m)},
     ["missing state: actor-turn authority for the duration"]),
    ("next_roll",
     r"^the (?P<who>target|[\w' -]+?) has (?P<state>Advantage|Disadvantage) on the next attack "
     r"roll it makes before the (?P<edge>end|start) of (?P<whose>its|this) (?:next )?turn$",
     lambda m: {"family": "next_roll_modifier",
                "roll": {"actor": "target" if m["who"] == "target" else "source",
                         "context": "attack_roll"},
                "state": m["state"].lower(), "uses": 1,
                "expires": {"until": f"{m['edge']}_of_turn",
                            "turn": "this" if m["whose"] == "this" else "next",
                            "turn_of": "target" if m["who"] == "target" else "source"}},
     ["missing state: actor-turn authority for the expiry"]),
    ("next_roll",
     r"^the next attack roll made against the target before the (?P<edge>start|end) of "
     r"(?P<whose>the [\w' -]+?'s) next turn has (?P<state>Advantage|Disadvantage)$",
     lambda m: {"family": "next_roll_modifier",
                "roll": {"actor": "any", "against": "target", "context": "attack_roll"},
                "state": m["state"].lower(), "uses": 1,
                "expires": {"until": f"{m['edge']}_of_turn", "turn": "next",
                            "turn_of": "source"}},
     ["missing state: actor-turn authority for the expiry"]),
    ("penalty_die",
     r"^the target rolls 1d(?P<d>\d+) whenever it makes an ability check or attack roll$",
     lambda m: {"family": "d20_test_penalty_die", "count": 1, "die": f"d{m['d']}",
                "contexts": ["ability_check", "attack_roll"]},
     []),
    ("penalty_die_application",
     r"^(?:and )?subtracts the number rolled from the D20 Test$",
     lambda m: {"family": "penalty_die_application", "subtracts_from": "d20_test"}, []),
    ("ability_disadvantage",
     r"^The target has Disadvantage on (?P<ab>Strength)-based D20 Tests$",
     lambda m: {"subject": "target",
                "effects": [{"family": "advantage", "state": "disadvantage",
                             "roll": {"actor": "subject", "context": "d20_test",
                                      "ability": m["ab"].lower()}}]},
     []),
    ("roll_disadvantage",
     r"^the target also has Disadvantage on ability checks and attack rolls$",
     lambda m: {"subject": "target",
                "effects": [_adv("disadvantage", c) for c in ("ability_check", "attack_roll")]},
     []),
    ("damage_roll_penalty",
     r"^and subtracts (?P<avg>\d+) \((?P<n>\d+)d(?P<d>\d+)\) from its damage rolls$",
     lambda m: {"family": "damage_roll_penalty", "average": int(m["avg"]),
                "dice": {"count": int(m["n"]), "die": f"d{m['d']}"}}, []),
    ("repeat_save",
     r"^(?:and )?(?:it |It |the target |The target )?repeats the save,? at the end of each of "
     r"its turns, ending the effect on itself on a success$",
     lambda m: {"family": "repeat_save", "at": "end_of_each_of_its_turns",
                "turn_of": "target", "ends_on": "success"},
     ["missing state: actor-turn authority for the repeat save"]),
    ("repeat_save",
     r"^the target repeats the save, ending the effect on itself on a success$",
     lambda m: {"family": "repeat_save", "ends_on": "success"}, []),
    ("repeat_save",
     r"^(?:and )?(?:[Tt]he target |it )?repeats the save at the end of its next turn if it is "
     r"still Restrained, "
     r"ending the effect on itself on a success$",
     lambda m: {"family": "repeat_save", "at": "end_of_its_next_turn", "turn_of": "target",
                "only_if": {"has_condition": "restrained"}, "ends_on": "success"},
     ["missing state: actor-turn authority for the repeat save"]),
    ("repeat_save",
     r"^and repeats the save at the end of each of its turns$",
     lambda m: {"family": "repeat_save", "at": "end_of_each_of_its_turns",
                "turn_of": "target"},
     ["missing state: actor-turn authority for the repeat save"]),
    ("repeat_save_limit",
     r"^After (?P<n>\d+) minutes?, it succeeds automatically$",
     lambda m: {"family": "repeat_save_limit", "automatic_success_after_minutes": int(m["n"])},
     ["missing state: elapsed-time authority for the automatic success"]),
    ("temporary_immunity",
     r"^[Tt]he target is immune to this (?P<src>[\w' -]+?)'s (?P<what>[\w' -]+?) for (?:the next )?"
     r"(?P<n>\d+) hours$",
     lambda m: {"family": "temporary_immunity", "to": "this_source_entry",
                "entry": m["what"], "hours": int(m["n"])},
     ["missing state: elapsed-time authority for the immunity"]),
    ("branch_label",
     r"^_(?P<b>Failure|Success|First Failure|Second Failure|Subsequent Failures|Failure by 5 or "
     r"More|Failure or Success|Hit or Miss):_$",
     lambda m: {"family": "branch", "branch": slug(m["b"])}, []),
    ("nested_save",
     r"^_(?P<ab>\w+) Saving Throw:_ DC (?P<dc>\d+)$",
     lambda m: {"family": "nested_save", "ability": m["ab"].lower(), "dc": int(m["dc"])}, []),
    ("nested_save",
     r"^(?:it|the target) (?:is subjected to the following effect|must make the following "
     r"saving throw)$",
     lambda m: {"family": "nested_save_trigger"}, []),
    ("hit_points_set",
     r"^it drops to 0 Hit Points$",
     lambda m: {"family": "hit_points_set", "to": 0}, []),
    ("otherwise_damage",
     rf"^(?:the target takes |It otherwise takes )?{_DMG_TERM} (?P<type>[A-Z][a-z]+) damage"
     r"(?: plus (?P<avg2>\d+) \((?P<n2>\d+)d(?P<d2>\d+)\) (?P<type2>[A-Z][a-z]+) damage)?$",
     lambda m: {"family": "damage_branch", "terms": [_dice_term(m, m["type"])] + (
         [{"average": int(m["avg2"]), "dice": {"count": int(m["n2"]), "die": f"d{m['d2']}",
                                               "modifier": 0},
           "damage_type": m["type2"].lower()}] if m["avg2"] else [])}, []),
    ("stable",
     r"^the target becomes Stable$",
     lambda m: {"family": "zero_hit_point_outcome", "becomes": "stable"}, []),
    ("death_on_zero",
     r"^(?:The target|A creature) dies(?: and turns to dust)? if (?:it is )?reduced to 0 Hit "
     r"Points by this attack$",
     lambda m: {"family": "zero_hit_point_outcome", "becomes": "dead",
                "when": "reduced_to_0_by_this_attack"}, []),
    ("choice_damage",
     r"^(?P<avg>\d+) \((?P<n>\d+)d(?P<d>\d+)\) damage of the type chosen for the "
     r"(?P<trait>[\w' ]+) trait$",
     lambda m: {"family": "choice_typed_damage", "average": int(m["avg"]),
                "dice": {"count": int(m["n"]), "die": f"d{m['d']}", "modifier": 0},
                "damage_type": {"chosen_for": m["trait"]}},
     ["missing runtime input: the recorded Draconic Origin choice"]),
    ("underwater_fire",
     r"^Being underwater doesn't grant Resistance to this Fire damage$",
     lambda m: {"family": "damage_qualification",
                "underwater_fire_resistance_applies": False}, []),
    ("returning_weapon",
     r"^The (?P<w>\w+) magically returns to the [\w' -]+?'s hand(?: or hovers within "
     r"(?P<ft>\d+) feet of the [\w' -]+?)? immediately after a ranged attack$",
     lambda m: {"family": "returning_weapon", "weapon": m["w"],
                **({"or_hovers_within_ft": int(m["ft"])} if m["ft"] else {})}, []),
    ("periodic_damage",
     rf"^(?:and )?(?:the target |it )?takes {_DMG_TERM} (?P<type>[A-Z][a-z]+) damage at the "
     r"start of each of (?P<whose>its|the [\w' -]+?'s) turns$",
     lambda m: {"family": "periodic_damage", "term": _dice_term(m, m["type"]),
                "at": "start_of_each_turn", "turn_of": _turn(m["whose"])},
     ["missing state: actor-turn authority for the periodic damage"]),
    ("periodic_hp_loss",
     r"^the target loses (?P<avg>\d+) \((?P<n>\d+)d(?P<d>\d+)\) Hit Points at the start of "
     r"each of its turns$",
     lambda m: {"family": "periodic_hit_point_loss", "average": int(m["avg"]),
                "dice": {"count": int(m["n"]), "die": f"d{m['d']}"},
                "at": "start_of_each_turn", "turn_of": "target"},
     ["missing state: actor-turn authority for the periodic loss"]),
    ("forced_movement",
     r"^the [\w' -]+? (?P<verb>pulls|pushes|moves) the target (?P<up>up to )?(?P<ft>\d+) feet "
     r"straight (?P<dir>toward|away from) itself$",
     lambda m: {"family": "forced_movement",
                "distance_ft" + ("_up_to" if m["up"] else ""): int(m["ft"]),
                "direction": "straight_toward_source" if m["dir"] == "toward"
                else "straight_away"},
     ["missing state: position"]),
    ("forced_movement",
     r"^the target is pushed (?P<ft>\d+) feet straight away from the [\w' -]+?$",
     lambda m: {"family": "forced_movement", "distance_ft": int(m["ft"]),
                "direction": "straight_away"},
     ["missing state: position"]),
    ("follow_up_attack",
     r"^the [\w' -]+? can make one (?P<a>[\w' ]+?) attack against it$",
     lambda m: {"family": "follow_up_attack", "attack": m["a"], "count": 1,
                "optional": True}, []),
    ("source_movement",
     r"^The [\w' -]+? then moves up to its Speed$",
     lambda m: {"family": "source_movement", "up_to": "speed"}, ["missing state: position"]),
    ("hit_point_regain_prohibition",
     r"^the target can't regain Hit Points$",
     lambda m: {"family": "hit_point_regain_prohibition", "hit_points": True}, []),
    ("escape_disadvantage",
     r"^Ability checks made to escape this grapple have Disadvantage$",
     lambda m: {"subject": "target", "purpose": "escape_this_grapple",
                "effects": [_adv("disadvantage", "ability_check")]}, []),
    ("targeting_restriction",
     r"^(?:and )?can't be targeted by the [\w' -]+?'s (?P<a>\w+)$",
     lambda m: {"family": "targeting_restriction", "source_attack": m["a"],
                "excludes": "the creature grappled by this attack"}, []),
    ("named_effect",
     r"^the target is cursed for (?P<n>\d+) (?P<unit>hour)s?(?P<or> or until the [\w' -]+? "
     r"dies)?$",
     lambda m: {"family": "named_effect", "name": "cursed",
                "duration": {"amount": int(m["n"]), "unit": m["unit"],
                             **({"or_until": "source_dies"} if m["or"] else {})}},
     ["missing state: elapsed-time authority for the duration"]),
    ("conditional_damage",
     rf"^or {_DMG_TERM} (?P<type>[A-Z][a-z]+) damage if the [\w' -]+? had Advantage on the "
     r"attack roll$",
     lambda m: {"family": "conditional_damage", "mode": "instead", "replaces_hit_damage_index": 0,
                "term": _dice_term(m, m["type"]), "when": {"attack_roll_had_advantage": True}},
     []),
    ("conditional_damage",
     rf"^—or {_DMG_TERM} (?P<type>[A-Z][a-z]+) damage if the target is Grappled by the "
     r"[\w' -]+?—plus (?P<avg2>\d+) \((?P<n2>\d+)d(?P<d2>\d+)\) (?P<type2>[A-Z][a-z]+) damage$",
     lambda m: {"family": "conditional_damage", "mode": "instead", "replaces_hit_damage_index": 0,
                "term": _dice_term(m, m["type"]),
                "when": {"target_grappled_by_source": True},
                # ``when`` governs only ``term``; this applies in both branches.
                "unconditional_damage": [{"average": int(m["avg2"]),
                                       "dice": {"count": int(m["n2"]), "die": f"d{m['d2']}",
                                                "modifier": 0},
                                       "damage_type": m["type2"].lower()}]}, []),
    ("named_effect",
     r"^(?:it|[Tt]he target) is cursed$",
     lambda m: {"family": "named_effect", "name": "cursed"}, []),
    ("condition_ends",
     r"^The (?P<c>\w+) condition ends$",
     lambda m: {"family": "condition_ends", "condition": m["c"].lower()}, []),
    ("rescue_check",
     r"^As an action, a creature within (?P<ft>\d+) feet of the [\w' -]+? can pull a creature "
     r"out of it by succeeding on a DC (?P<dc>\d+) (?P<ab>\w+) \((?P<sk>[\w ]+)\) check$",
     lambda m: {"family": "rescue_check", "actor_within_ft": int(m["ft"]), "uses": "action",
                "check": {"ability": m["ab"].lower(), "skill": slug(m["sk"]),
                          "dc": int(m["dc"])}, "ends": "grapple"},
     ["missing state: position"]),
    ("choice_damage",
     r"^(?P<n>\d+)d(?P<d>\d+) damage of a type this spirit has Resistance to \(your choice when "
     r"you cast the spell\)$",
     lambda m: {"family": "choice_typed_damage", "dice": {"count": int(m["n"]), "die": f"d{m['d']}"},
                "damage_type": {"chosen_from": "this creature's Resistances",
                                "chosen_by": "caster", "when": "casting"}},
     ["missing runtime input: the caster's damage-type choice"]),
    ("save_success",
     r"^Half damage(?P<only> only)?$",
     lambda m: {"family": "save_success", "half_damage": True,
                **({"only": True} if m["only"] else {})}, []),
    ("self_save_predicate",
     r"^If the [\w' -]+? sees its reflection in the (?P<area>\w+), the [\w' -]+? must make "
     r"this save$",
     lambda m: {"family": "self_save_predicate", "when": {"source_sees_own_reflection_in":
                                                           m["area"].lower()}},
     ["missing state: visibility (the source seeing its reflection)"]),
    ("area_origin_point",
     r"^The [\w' -]+? hurls a boulder at a point it can see within (?P<ft>\d+) feet$",
     lambda m: {"family": "area_origin_point", "within_ft": int(m["ft"]),
                "requires_source_sees_point": True},
     ["missing state: position and visibility of the point"]),
    ("area_origin_point",
     r"^centered on that point$",
     lambda m: {"family": "area_origin_point", "centered_on": "the_frame_point"}, []),
    ("aura",
     r"^The [\w' -]+? emanates an aura in a (?P<ft>\d+)-foot Emanation while it doesn't have "
     r"the (?P<c>\w+) condition$",
     lambda m: {"family": "aura", "emanation_ft": int(m["ft"]),
                "suspended_while_source_has": m["c"].lower()},
     ["missing state: position"]),
    ("aura",
     r"^(?:in )?the aura$",
     lambda m: {"family": "aura", "targets_within": "the_aura"},
     ["missing state: position and actor-turn authority for the turn-start trigger"]),
    ("save_timing",
     r"^at the end of the [\w' -]+?'s turn$",
     lambda m: {"family": "save_timing", "at": "end_of_turn", "turn": "this",
                "turn_of": "source"},
     ["missing state: actor-turn authority for the save timing"]),
    ("trigger",
     r"^The [\w' -]+? explodes when it dies$",
     lambda m: {"family": "trigger", "on": "source_dies"},
     ["missing state: the trigger event (the source's death)"]),
]
#: Leading predicates; each scopes the rest of its sentence.
_PREDICATES: list[tuple[str, Any, list[str]]] = [
    (r"^If (?:the )?target is (?:a |an )?(?P<size>\w+) or smaller(?: creature)?(?: and the "
     r"[\w' -]+? (?:moved (?P<ft>\d+)\+ feet straight toward it immediately before the hit|"
     r"(?P<adv>had Advantage on the attack roll)))?$",
     lambda m: {"target_maximum_size": m["size"].lower(),
                **({"source_moved_straight_toward_target_ft_min": int(m["ft"])}
                   if m["ft"] else {}),
                **({"attack_roll_had_advantage": True} if m["adv"] else {})},
     []),
    (r"^If the target is a creature$", lambda m: {"target_is_creature": True}, []),
    (r"^If the target is a (?P<t>Humanoid)$", lambda m: {"target_type": m["t"].lower()}, []),
    (r"^If (?:this damage reduces the target|the target is reduced) to 0 Hit Points(?: by this "
     r"attack)?$", lambda m: {"target_reduced_to_0_hit_points_by_this": True}, []),
    (r"^If the (?:target|creature) has (?P<n>\d+) Hit Points or fewer$",
     lambda m: {"target_hit_points_at_most": int(m["n"])}, []),
    (r"^Otherwise$", lambda m: {"otherwise": True}, []),
    (r"^While (?P<c>Grappled|Poisoned|Charmed|Deafened)$",
     lambda m: {"while_condition": m["c"].lower()}, []),
    (r"^While it has the (?P<c>\w+) condition$", lambda m: {"while_condition": m["c"].lower()},
     []),
    (r"^Until the (?P<x>grapple|curse) ends$", lambda m: {"while": m["x"]}, []),
    (r"^Until this poison ends$", lambda m: {"while_condition": "poisoned",
                                             "refers_to": "this poison"}, []),
    (r"^While wounded$", lambda m: {"while": "infernal_wound"}, []),
    (r"^While cursed$", lambda m: {"while": "curse"}, []),
    (r"^Until the end of its next turn$",
     lambda m: {"duration": {"until": "end_of_turn", "turn": "next", "turn_of": "target"}},
     ["missing state: actor-turn authority for the duration"]),
    (r"^At the end of each of its turns$", lambda m: {"at": "end_of_each_of_its_turns"},
     ["missing state: actor-turn authority for the repeat save"]),
]
#: Genuinely different engines, named; matched against one piece only.
SUBCLAUSE_CLUSTERS: list[tuple[str, str]] = [
    ("object targeting", r"^each object|metal object|creature with the object"),
    ("aquatic mucus curse", r"surrounded by mucus|outside a body of water|moisture|"
                            r"breathe air and water"),
    ("possession and body control", r"possess|controls the body|game statistics are the same|"
                                    r"the ghost disappears|loses control of its body|"
                                    r"can't be targeted by any attack, spell"),
    ("swallowing", r"swallow|regurgitate|from the corpse"),
    ("engulfing", r"engulf|pulled into the [\w' -]+?'s space|moves with it"),
    ("attachment", r"attach|detach|covers the target|moves with the target|"
                   r"can attack only the target"),
    ("suffocation", r"suffocating|smother"),
    ("Hit Point maximum changes", r"Hit Point maximum"),
    ("lycanthropy and creature transformation", r"becomes a \*\*|rises|\*\*Shadow\*\*"),
    ("rest benefits", r"benefit from finishing|finishes a Long Rest"),
    ("teleport, banishment or planar travel", r"teleport|reappears|transported|demiplane|"
                                              r"plane of existence|Abyss"),
    ("object burning and armor or object degradation", r"burning|penalty to the AC it offers|"
                                                       r"destroyed|can be damaged|Mending|"
                                                       r"flammable object"),
    ("Reactions and action economy", r"Reactions?|Bonus Action|takes no action|"
                                     r"move or take one action|either an action"),
    ("spellcasting", r"cast spells|spell restores|Concentration"),
    ("Exhaustion and aging", r"Exhaustion|years older"),
    ("death caused directly by an effect", r"\bdies\b|is slain|\bslain\b"),
    ("the source regaining Hit Points", r"regains? (?:10 \(3d6\) )?Hit Points|regains Hit"),
    ("ability score reduction", r"Strength score decreases"),
    ("infernal wound", r"infernal wound|wound closes|stanch"),
    ("item interaction", r"Holy Water"),
    ("charm control and telepathy", r"acts as an ally|under its control|communicate "
                                    r"telepathically|repeats the save whenever it takes damage"),
    ("random behaviour table", r"rolls 1d8 to determine|\*\*\d"),
    ("compelling song or babbling", r"(?i:song)|babbl|moves on its turn toward|"
                                    r"avoid Opportunity Attacks|damaging terrain"),
    ("encounter movement and placement", r"moves up to its Speed without provoking|"
                                         r"move through the spaces|feet of movement to jump|"
                                         r"throws a [\w ]+? creature|unoccupied space|"
                                         r"escapes and enters|space the [\w' -]+? enters|"
                                         r"destination space|targeted once by the following"),
    ("halved damage sharing", r"halves the damage it takes|the same amount of damage"),
    ("multi-target grapple capacity", r"only one creature at a time|up to two Medium|"
                                      r"one creature Grappled by this action at a time|"
                                      r"can smother only"),
    ("stat-block self-restriction while acting", r"can't (?:make|take) (?:this action|Attach|"
                                                  r"Proboscis)"),
]
#: Narrative information only: no roll, DC, damage, condition or state.
NO_MECHANICAL_CONSEQUENCE = (
    r"^The sprite knows the target's emotions and alignment$",
    r"^The aboleth gains the target's memories if the target is a Humanoid and is reduced to 0 "
    r"Hit Points by this action$",
    r"^Its body is then absorbed into the mouther, leaving only equipment behind$",
    r"^the target's skin becomes slimy$",
    r"^The [\w' -]+? conjures a fiery chain to bind a creature$",
    r"^at which point the chain disappears$",
    r"^The chain disappears$",
)


def _norm_piece(p: str) -> str:
    t = re.sub(r"[;,]\s*and$", "", p.strip()).strip(" ,;")
    t = re.sub(r"^(?:and|but)\s+(?=(?:the|it|its|has|repeats|takes|can't|is)\b)", "", t)
    return t.rstrip(".").strip()


def split_pieces(text: str) -> list[str]:
    """Exact pieces of a clause; ``"".join(pieces) == text`` is asserted."""
    pieces, last = [], 0
    for m in _CONJUNCT.finditer(text):
        pieces.append(text[last:m.end()])
        last = m.end()
    pieces.append(text[last:])
    out = []
    for p in pieces:
        n = _norm_piece(p)
        if (pm := _PREDICATE.match(n)) and any(re.match(rx, pm["p"]) for rx, _, _ in
                                               _PREDICATES):
            cut = p.index(pm["rest"])
            out += [p[:cut], p[cut:]]
        else:
            out.append(p)
    out = [p for p in out if p]
    assert "".join(out) == text, (text, out)
    return out


def dispose_clause(text: str) -> list[dict[str, Any]]:
    """Per-piece disposition of one untyped clause (see the section comment)."""
    out = []
    active: list[int] = []
    pieces = split_pieces(text)
    sentence_of, cur = [], 0
    for p in pieces:
        sentence_of.append(cur)
        if p.rstrip().endswith("."):
            cur += 1
    for i, piece in enumerate(pieces):
        n = _norm_piece(piece)
        row: dict[str, Any] = {"text": piece}
        if not n:
            row["disposition"] = "punctuation"
            out.append(row)
            continue
        for rx, build, needs in _PREDICATES:
            if pm := re.match(rx, n):
                row.update(disposition="typed", typed={"family": "predicate", **build(pm)},
                           needs=needs, scope="rest_of_sentence")
                active.append(i)
                break
        else:
            for family, rx, build, needs in _READERS:
                if rm := re.match(rx, n):
                    typed = build(rm)
                    typed.setdefault("family", family)
                    row.update(disposition="typed", typed=typed, needs=needs)
                    if active:
                        row["typed"]["under_predicates"] = list(active)
                    break
            else:
                cluster = next((name for name, crx in SUBCLAUSE_CLUSTERS
                                if re.search(crx, n)), None)
                sentence = "".join(p for j, p in enumerate(pieces)
                                   if sentence_of[j] == sentence_of[i])
                context = next((name for name, crx in SUBCLAUSE_CLUSTERS
                                if re.search(crx, sentence)), None)
                if cluster:
                    row.update(disposition="unsupported", cluster=cluster)
                elif any(re.match(rx, n) for rx in NO_MECHANICAL_CONSEQUENCE):
                    row["disposition"] = "no_mechanical_consequence"
                elif context:
                    row.update(disposition="unsupported", cluster=context,
                               by_sentence_context=True)
                else:
                    row["disposition"] = "untyped"
        if piece.rstrip().endswith(".") or row.get("typed", {}).get("family") == "branch":
            active = []
        out.append(row)
    return out


#: Families whose typed piece creates a mechanical effect on its subject.
_EFFECT_FAMILIES = frozenset({
    "grapple", "condition", "timed_condition", "linked_condition", "condition_until_repeat",
    "named_effect", "timed_speed_change", "timed_ac_modifier", "next_roll_modifier",
    "d20_test_penalty_die", "hit_point_regain_prohibition", "periodic_damage",
    "periodic_hit_point_loss", "targeting_restriction", "temporary_immunity",
    "ability_disadvantage", "roll_disadvantage", "damage_roll_penalty", "escape_disadvantage"})


def _applied(t: dict[str, Any]) -> set[str]:
    out = {x["condition"] for x in t.get("effects", []) if x.get("family") == "condition_effect"}
    if t["family"] == "grapple":
        out.add("grappled")
    if t["family"] == "named_effect":
        out.add(t["name"])
    return out


def link_effects(clauses: list[dict[str, Any]]) -> None:
    """Source-local effect identity, branch ownership and termination.

    Each effect-creating piece gets an entry-local ``effect_id`` (E1, E2, …);
    these name effects within this entry's source text only and are never
    runtime identifiers. Every typed piece states its ``branch`` (the clause
    part, or the branch label it follows). Links are explicit fields:

    * ``bound_effect``: a "While X" / "Until X ends" predicate or a linked
      condition refers to the nearest preceding effect of this entry that
      applies X ("this poison", the grapple, the curse), never to an unrelated
      effect the subject may also have;
    * ``ends_effects``: a termination (ends early, ends on a repeat-save
      success) ends exactly these effects, and no others;
    * ``duration_of_effects``: a sentence-level duration governs exactly
      these effects.
    """
    effects: list[tuple[str, str, set[str]]] = []  # (id, branch, applied)
    n = 0
    for c in clauses:
        branch = c["part"]
        for p in c["pieces"]:
            t = p.get("typed")
            if t is None:
                continue
            fam = t["family"]
            if fam == "branch":
                branch = t["branch"]
                continue
            t["branch"] = branch
            if fam in _EFFECT_FAMILIES:
                n += 1
                t["effect_id"] = f"E{n}"
                effects.append((t["effect_id"], branch, _applied(t)))
            in_branch = [i for i, b, _ in effects if b == branch and i != t.get("effect_id")]
            link = t.get("while_condition") or ({"grapple": "grappled", "curse": "cursed"}
                                                .get(t.get("while", "")))
            if link and (fam == "predicate" or fam == "linked_condition"):
                bound = next((i for i, _, ap in reversed(effects)
                              if link in ap and i != t.get("effect_id")), None)
                t["bound_effect"] = bound
            if fam in ("condition_ends_early",):
                t["ends_effects"] = [effects[-1][0]]
            elif fam in ("effect_ends", "repeat_save", "repeat_save_limit"):
                t["ends_effects"] = in_branch
            elif fam == "effect_lasts":
                t["duration_of_effects"] = in_branch
            elif fam == "condition" and "repeat_save" in t:
                t["repeat_save"]["ends_effects"] = [t["effect_id"]]
        # An effect stated under a bound "While X" predicate lasts exactly
        # while that effect lasts.
        for p in c["pieces"]:
            t = p.get("typed") or {}
            for j in t.get("under_predicates", []):
                bound = (c["pieces"][j].get("typed") or {}).get("bound_effect")
                if bound and "effect_id" in t:
                    t["lasts_while_effect"] = bound


_OLD_UNTYPED = ("hit rider not typed", "failure rider not typed", "success effect not typed",
                "failure-or-success effect not typed", "miss effect not typed",
                "target predicate not typed", "reach/range not typed", "frame not typed")


def dispose_entry(e: dict[str, Any]) -> None:
    """Replace whole-clause residue with per-piece dispositions. Typed pieces
    stay in the source entry (``clauses``); dispositions are capability."""
    body = e.get("attack") or e.get("save")
    if not body or "untyped_clauses" not in body:
        return
    reasons = [r for r in e["reasons"] if not r.startswith(_OLD_UNTYPED)]
    clauses, dispositions = [], []
    for u in body.pop("untyped_clauses"):
        rows = dispose_clause(u["text"])
        clauses.append({"part": u["part"], "text": u["text"],
                        "pieces": [{"text": r["text"], **({"typed": r["typed"]}
                                                          if "typed" in r else {})}
                                   for r in rows]})
        for r in rows:
            d = {"part": u["part"], "piece": r["text"], "disposition": r["disposition"]}
            if "cluster" in r:
                d["cluster"] = r["cluster"]
                if r.get("by_sentence_context"):
                    d["by_sentence_context"] = True
            dispositions.append(d)
            if r["disposition"] == "unsupported":
                reasons.append(f"unsupported mechanic ({r['cluster']}): {r['text'].strip()!r}")
            elif r["disposition"] == "untyped":
                reasons.append(f"untyped source clause: {r['text'].strip()!r}")
            for need in r.get("needs", []):
                if need not in reasons:
                    reasons.append(need)
    # One representation for unconditional damage printed beside a
    # conditional replacement (Mimic, as Venomous Snakes): it joins
    # ``hit_damage``; the piece points at it, and ``when`` governs only the
    # replacement of ``hit_damage[replaces_hit_damage_index]``.
    for c in clauses:
        for p in c["pieces"]:
            t = p.get("typed") or {}
            if t.get("family") == "conditional_damage" and "unconditional_damage" in t:
                start = len(body["hit_damage"])
                body["hit_damage"] += t.pop("unconditional_damage")
                t["unconditional_hit_damage_indices"] = list(
                    range(start, len(body["hit_damage"])))
    link_effects(clauses)
    body["clauses"] = clauses
    e["clause_dispositions"] = dispositions
    e["reasons"] = reasons
    if e["classification"] != "deferred":
        e["classification"] = "supported" if not reasons else "conditional"


def logical_entries(block_lines: list[str]) -> list[dict[str, Any]]:
    """Complete logical entries: a head line plus every following continuation
    line (a wrapped line or an ``&emsp;`` paragraph) up to the next entry head,
    heading, blank line or ``<hr>``. Each keeps its 0-based physical span; the
    joined text is what every later parser reads (C4 review finding 2)."""
    section, out = "trait", []
    for i, line in enumerate(block_lines):
        h = re.match(r"^#{3,6} (.+)$", line)
        if h and h.group(1).lower() in _SECTIONS:
            section = _SECTIONS[h.group(1).lower()]
            continue
        e = _ENTRY.match(line)
        if e and not line.startswith(("**AC**", "**HP**")):
            name = e.group("a") or e.group("b") or e.group("c")
            text = e.group("text")
            if e.group("c"):  # "_Name. Melee Attack Roll:_" → restore the italic head
                text = "_" + text
            out.append({"section": section, "name": name, "text": text, "span": [i, i]})
        elif out and line.strip() and not line.startswith(("#", "<")) \
                and out[-1]["span"][1] == i - 1:
            out[-1]["text"] += " " + line.removeprefix("&emsp;").strip()
            out[-1]["span"][1] = i
    for le in out:  # formatting only: an HTML line break is not source content
        le["text"] = re.sub(r"\s*<br>\s*", " ", le["text"]).strip()
    return out


def entries(block_lines: list[str], cond_index: dict[str, Any], file: str,
            first_line: int) -> list[dict[str, Any]]:
    assert file and first_line > 0, (file, first_line)
    raw = []
    for le in logical_entries(block_lines):
        name, usage = le["name"], None
        if u := _USAGE.match(name):
            name, usage = u.group("base"), u.group("usage")
        raw.append((le["section"], name, usage, le["text"],
                    {"file": file, "first_line": first_line + le["span"][0],
                     "last_line": first_line + le["span"][1]}))
    names = {n for _, n, _, _, _ in raw}
    out = []
    for section, name, usage, text, span in raw:
        entry: dict[str, Any] = {"section": section, "name": name, "_text": text,
                                 "source_span": span}
        reasons: list[str] = []
        if hm := re.match(r"Legendary Action Uses: (\d)(?: \((\d) in Lair\))?", name):
            # The section's usage header, not an entry.
            entry.update(kind="usage_header", classification="conditional",
                         usage={"kind": "legendary_action_uses", "uses": int(hm.group(1)),
                                "in_lair": int(hm.group(2)) if hm.group(2) else None},
                         reasons=["legendary timing needs explicit actor-turn authority"]
                         + (["the lair variant needs a recorded in-lair state"]
                            if hm.group(2) else []))
            out.append(entry)
            continue
        if usage:
            u = _usage(usage)
            entry["usage"] = u or {"text": usage}
            if u is None:
                reasons.append(f"usage not typed: {usage!r}")
            elif u["kind"] == "recharge":
                reasons.append("Recharge needs explicit start-of-turn authority")
            if u and u.get("in_lair"):
                reasons.append("the lair variant needs a recorded in-lair state")
            if u and u["kind"] == "form_only":
                reasons.append("needs the creature's recorded current form")
        if section == "legendary_action":
            reasons.append("legendary timing needs explicit actor-turn authority")
        caster = re.search(r"your spell (?:attack modifier|save DC)|DC equals your spell save "
                           r"DC|Your spell save DC|the spell's level|your spellcasting ability",
                           text)
        attack = _attack(text)
        save = None if attack else _save(text)
        if attack:
            entry.update(kind="attack", attack=attack)
            reasons += attack.pop("untyped")
        elif save:
            entry.update(kind="save_effect", save=save)
            reasons += save.pop("untyped")
        elif name == "Multiattack":
            ma = _multiattack(text)
            entry.update(kind="multiattack", multiattack=ma)
            if ma["residue"]:
                reasons.append(f"composition residue: {ma['residue']!r}")
            for alt in ma["alternatives"]:
                for p in alt["parts"]:
                    if isinstance(p["count"], dict):
                        reasons.append(
                            "missing state: the recorded head count" if "per" in p["count"]
                            else "missing runtime input: the spell level or summoner's "
                                 f"Proficiency Bonus for the attack count {p['count']}")
                    if p.get("any_of") == []:
                        # "a number of attacks" names none: the source set is
                        # every attack-roll action of the block, each keeping
                        # its own form qualification (Giant Insect).
                        p["any_of"] = [n for s_, n, _, t, _ in raw if s_ == "action"
                                       and re.match(r"_?(?:Melee|Ranged) Attack Roll:", t)]
                        assert p["any_of"], name
        elif "Spellcasting" in name or re.search(
                r"\bcasts? (?:the )?_|\bcasts [A-Z]|uses Spellcasting|_Wish_ spell", text):
            entry.update(kind="spellcasting", classification="deferred",
                         reasons=["general spell execution is a non-goal"])
            out.append(entry)
            continue
        elif section == "reaction":
            tm = re.search(r"_?Trigger:_? (.*?) _?Response", text)
            trigger = tm.group(1) if tm else ""
            assert trigger, (name, text)
            wearer = "wearer" in trigger
            rx = [("rolls_against", r"attack roll (?:hits|targets)|hits? (?:it|the [\w' -]+?) "
                   r"with|targeted by|is hit by|makes an attack roll against"),
                  ("damage_taken", r"takes? damage|would take|subjected to [\w ]+ damage|"
                   r"becomes Bloodied"),
                  ("target_save", r"saving throw"),
                  ("own_check", r"makes an ability check")]
            affects = sorted({("related_creature_" + k) if wearer else k
                              for k, p in rx if re.search(p, trigger)})
            entry.update(kind="reaction", text=text, classification="deferred",
                         affects=affects, trigger=trigger,
                         reasons=["reaction trigger/response is a new mechanic; named"])
            out.append(entry)
            continue
        elif oc := _observer_check(text):
            entry.update(kind="observer_check", text=text, observer_check=oc)
            reasons.append("missing state: " + oc.pop("needs"))
        elif name in NAMED_DEFERRED:
            entry.update(kind="named_mechanic", text=text, classification="deferred",
                         reasons=[NAMED_DEFERRED[name]])
            out.append(entry)
            continue
        elif ref := next((n for n in sorted(names) if n != name and re.search(
                rf"\bmakes? (?:one|two|three) (?:[\w' ]+ or )?{re.escape(n)}(?: or [\w' ]+)? "
                rf"attacks?\b|\buses {re.escape(n)}\b", text)), None):
            entry.update(kind="entry_reference", text=text, references=ref)
            reasons.append(f"missing state: position and actor-turn for {ref!r} (an "
                           "already typed entry) used under this entry's movement terms")
        elif (sm := re.search(r"_\w+ Saving Throw:_", text)) and (
                save := _framed_save(text[:sm.start()], text[sm.start():])):
            # A save inside a framing sentence (a death trigger, a leap, a
            # gaze) or with First/Second Failure branches: the frame and the
            # outcomes go through the per-piece dispositions (C5).
            entry.update(kind="save_effect", save=save)
            reasons += save.pop("untyped")
        elif "Saving Throw:_" in text or "Attack Roll:" in text:
            entry.update(kind="special_effect", text=text)
            reasons.append("special effect outside the bounded attack/save shapes; named")
        elif section != "trait" and name not in CHECK_REMOVALS and (
                name in CONTRIBUTOR_REVIEW or _KEYWORDS.search(text)):
            # A separately selected action never stands as a contributor to the
            # creature's other entries; it is its own (named) operation.
            entry.update(kind="separate_action", text=text, affects=[])
            reasons.append("separately selected action outside the bounded attack/save "
                           "shapes; named")
        elif name in TYPED_CONTRIBUTORS:
            typed, needs, contexts = TYPED_CONTRIBUTORS[name]
            entry.update(kind="contributor", text=text, contributor=typed,
                         subject="self", affects=contexts)
            reasons.append(f"missing state: {needs}")
        elif name in CHECK_REMOVALS:
            removal = dict(CHECK_REMOVALS[name])
            if text.startswith("If the swarm has a Climb Speed"):
                removal["applies_when"] = {"subject_has_speed": "climb"}
            entry.update(kind="contributor", text=text, contributor=removal,
                         subject="self", affects=["own_check"])
        elif granted := _granted_conditions(text):
            sem = {c: _condition_semantics(cond_index, c) for c in granted}
            affects = sorted({ctx for c in sem.values() for ctx, key in
                              (("own_attack", "own_rolls"), ("rolls_against", "rolls_against"))
                              if c[key]} or {"own_attack", "rolls_against", "target_save"})
            entry.update(kind="contributor", text=text, grants_conditions=sem,
                         subject="self", affects=affects)
            reasons.append(f"grants {granted}: their typed facts apply to {affects}; "
                           "contextual components need validated state")
        elif name in CONTRIBUTOR_REVIEW:
            subject, contexts, needs, note = CONTRIBUTOR_REVIEW[name]
            entry.update(kind="contributor", text=text, subject=subject, affects=contexts,
                         applicability=note)
            if name in CONTRIBUTOR_EFFECTS:
                entry["contributor"] = CONTRIBUTOR_EFFECTS[name]
            if needs:
                # Recorded even when no admitted context of this creature is
                # touched; ``affects`` alone decides what it blocks.
                reasons.append(needs)
        elif name in NO_ROSTER_EFFECT:
            entry.update(kind="no_roster_effect", text=text, reviewed=NO_ROSTER_EFFECT[name])
        elif _KEYWORDS.search(text):
            entry.update(kind="unreviewed", text=text,
                         affects=["own_attack", "own_check", "rolls_against", "target_save",
                                  "damage_taken", "melee_hits_against", "zero_hp_outcome"])
            reasons.append("trait not individually reviewed; blocks every context")
        else:
            entry.update(kind="unreviewed", text=text,
                         affects=["own_attack", "own_save_effect", "rolls_against",
                                  "target_save"])
            reasons.append("not on the reviewed no-effect allowlist; blocks conservatively")
        if caster:
            reasons.append("missing runtime input: the caster and the spell's level as recorded "
                           "state (formulas are typed; no spell is cast)")
        entry["classification"] = ("no_roster_effect" if entry["kind"] == "no_roster_effect"
                                   else "supported" if not reasons else "conditional")
        entry["reasons"] = reasons
        out.append(entry)
    return out


def _usage(usage: str) -> dict[str, Any] | None:
    if m := re.fullmatch(r"Recharge (\d)(?:–(\d))?", usage):
        return {"kind": "recharge", "minimum_d6": int(m.group(1))}
    if m := re.fullmatch(r"(\d)/Day(?: Each)?", usage):
        return {"kind": "per_day", "uses": int(m.group(1))}
    if usage == "Recharges after a Short or Long Rest":
        return {"kind": "recharge_after_rest"}
    if m := re.fullmatch(r"(\d)/Day, or (\d)/Day in Lair", usage):
        return {"kind": "per_day", "uses": int(m.group(1)), "in_lair": int(m.group(2))}
    if m := re.fullmatch(r"(.+?) (?:Form )?Only(?:; Recharges after a Long Rest)?", usage):
        forms = [slug(f) for f in re.split(r" or ", m.group(1).removesuffix(" Form"))]
        return {"kind": "form_only", "forms": forms,
                "recharge_after_long_rest": "Recharges" in usage}
    if usage == "Requires Magic Rope":
        return {"kind": "requires_entry", "entry": "Magic Rope"}
    return None


#: Every ``affects`` value; each is rolled up below (asserted).
CONTEXTS = frozenset({
    "own_attack", "own_save_effect", "own_check", "rolls_against", "target_save",
    "damage_taken", "melee_hits_against", "zero_hp_outcome", "others_check_about_subject",
    "related_creature_damage_taken", "related_creature_rolls_against"})
_TARGET_SIDE = ("rolls_against", "target_save", "damage_taken", "melee_hits_against",
                "zero_hp_outcome", "own_check", "others_check_about_subject",
                "related_creature_damage_taken", "related_creature_rolls_against")
assert set(_TARGET_SIDE) | {"own_attack", "own_save_effect"} == CONTEXTS


def _rollup(block: list[dict[str, Any]], profile_conditional: list[str]) -> dict[str, Any]:
    """Block-level certification.

    Own-entry blockers are every conditional/unreviewed contributor whose
    ``affects`` reaches that kind of roll; target-side blockers are what a
    roll *against* this creature or *its* save would also have to resolve.
    A Multiattack is certified per selectable composition.
    """
    def blockers(kind: str) -> list[str]:
        return sorted({e["name"] for e in block
                       if e["kind"] in ("contributor", "unreviewed", "reaction")
                       and e["classification"] != "supported"
                       and kind in e.get("affects", [])})

    for e in block:
        assert set(e.get("affects", [])) <= CONTEXTS, (e["name"], e.get("affects"))
    own_attack, own_save = blockers("own_attack"), blockers("own_save_effect")

    def applies(kind: str) -> list[str]:
        return sorted({e["name"] for e in block if e["kind"] == "contributor"
                       and e["classification"] == "supported"
                       and kind in e.get("affects", [])})
    standing = {e["name"] for e in block if e["kind"] in ("contributor", "unreviewed")}
    by_name = {e["name"]: e for e in block}
    for e in block:
        if e["kind"] == "attack":
            e["blocked_by"] = own_attack
            e["applies"] = applies("own_attack")
            e["executable_once_accepted"] = e["classification"] == "supported" and not own_attack
        elif e["kind"] == "save_effect":
            e["blocked_by"] = own_save
            e["executable_once_accepted"] = e["classification"] == "supported" and not own_save

    def ok(ref: str) -> bool:
        return bool(by_name.get(ref, {}).get("executable_once_accepted"))

    for e in block:
        if e["kind"] != "multiattack":
            continue
        ma = e["multiattack"]
        selections = []
        for i, alt in enumerate(ma["alternatives"]):
            # Every selectable composition is enumerated and certified by its
            # own parts: fixed attacks; each "any combination" choice by its
            # certified options; one selection per option of a mandatory use;
            # an optional or if-available use as the base without it plus one
            # selection per option. An unavailable part refuses only the
            # selections containing it.
            fixed = [p["attack"] for p in alt["parts"] if "attack" in p]
            choices = [p["any_of"] for p in alt["parts"] if "any_of" in p]
            certified = [[o for o in c if ok(o)] for c in choices]
            use_parts = [p for p in alt["parts"] if "uses_one_of" in p]
            mandatory = [p for p in use_parts if not p.get("optional")
                         and not p.get("if_available")]
            optional = [p for p in use_parts if p not in mandatory]
            base_parts_ok = bool(e["classification"] == "supported"
                                 and (fixed or choices) and not ma["residue"]
                                 and alt["condition"] is None
                                 and all(ok(r) for r in fixed) and all(certified))
            mandatory_combos: list[list[str]] = [[]]
            for p in mandatory:
                mandatory_combos = [c + [o] for c in mandatory_combos for o in p["uses_one_of"]]
            for combo in mandatory_combos:
                label = f"alternative {i + 1}" + (f" using {', '.join(combo)}" if combo else "")
                base_ok = base_parts_ok and all(ok(u) for u in combo)
                selections.append({"selection": label, "attacks": fixed,
                                   "any_of": choices, "certified_options": certified,
                                   "uses": combo, "executable_once_accepted": base_ok,
                                   "unresolved": [r for r in fixed + combo
                                                  if r not in by_name]})
                for p in optional:
                    for opt in p["uses_one_of"]:
                        selections.append({
                            "selection": f"{label} plus optional {opt}",
                            "uses": combo + [opt],
                            "executable_once_accepted": base_ok and ok(opt)
                            and not p.get("if_available"),
                            "unresolved": [opt] if opt not in by_name else [],
                            "spellcasting": "Spellcasting" in opt})
                for j, rep in enumerate(ma["replacements"]):
                    for opt in rep["with_one_of"]:
                        selections.append({
                            "selection": f"{label} with replacement {j + 1}: {opt}",
                            "executable_once_accepted": base_ok and ok(opt)
                            and not rep["if_available"],
                            "unresolved": [opt] if opt not in by_name else [],
                            "spellcasting": "Spellcasting" in opt})
        e["selections"] = selections
        e["executable_once_accepted"] = any(
            s["executable_once_accepted"] for s in selections
            if "replacement" not in s["selection"] and "optional" not in s["selection"])
        for s_ in selections:
            assert not (s_["executable_once_accepted"] and (s_["unresolved"]
                        or s_.get("spellcasting"))), (e["name"], s_)
    del standing
    # Each context an operation other than this creature's own attack/save
    # consults: rolls against it, its saves, damage it takes, its zero-HP
    # outcome, its own checks, others' checks about it, and a related
    # creature's (the amulet wearer's) rolls and damage.
    return {**{f"{k}_blocked_by": blockers(k) for k in _TARGET_SIDE},
            "applies_when_targeted": {k: applies(k) for k in _TARGET_SIDE if applies(k)},
            "conditional_profile_fields": profile_conditional}


# -- Profiles ----------------------------------------------------------------


def _terms(text: str) -> list[str]:
    return [t.strip().lower() for t in text.split(",") if t.strip()]


def _profile(b: dict[str, Any], conditional: dict[str, dict[str, str]]) -> dict[str, Any]:
    """Fixed fields of any stat block, tolerant of parameterized AC/HP.

    A qualified defensive term is never dropped: it becomes an explicit
    ``{"conditional": …}`` member, and unrecognized terms are kept verbatim.
    """
    m = re.match(r"_((?:\w+ or )?\w+)(?: or Smaller)? ", b["size_line"])
    sizes = [slug(w) for w in m.group(1).split(" or ")] if m else []
    if "or Smaller" in b["size_line"]:
        sizes = [s for s in SIZES if SIZES.index(s) <= SIZES.index(sizes[0])]
    body = "\n".join(b["body"])
    cells = [html.unescape(re.sub(r"<[^>]+>", "", c)).strip()
             for c in re.findall(r"<td>(.*?)</td>", body)]
    scores = {ABILITY[cells[n]]: {"score": int(cells[n + 1]),
                                  "save": int(cells[n + 3].replace("−", "-").replace("+", ""))}
              for n in range(0, len(cells) - 3, 4) if cells[n] in ABILITY}
    out: dict[str, Any] = {"family": "creature_defensive_profile", "sizes": sizes,
                           "abilities": scores, "resistance": [], "vulnerability": [],
                           "immunity": [], "condition_immunity": [], "verbatim": []}
    for label, key in (("Resistances", "resistance"), ("Vulnerabilities", "vulnerability"),
                       ("Immunities", "immunity")):
        mm = re.search(rf"^\*\*{label}\*\* (.*?)(?:<br>)?\s*$", body, re.M)
        if not mm:
            continue
        damage_part, _, cond_part = mm.group(1).partition(";")
        for t in _terms(damage_part):
            if t in DAMAGE:
                out[key].append(t)
            elif key == "immunity" and not cond_part and t in CONDITIONS:
                out["condition_immunity"].append(t)
            else:
                out["verbatim"].append({label: t})
        for t in _terms(cond_part):
            if t in CONDITIONS:
                out["condition_immunity"].append(t)
            else:
                out["verbatim"].append({label: t})
    for field, marker in conditional.items():
        out[field].append(marker)
        out["verbatim"] = [v for v in out["verbatim"]
                           if not any(w in json.dumps(v) for w in marker["source_terms"])]
    return out


def _defense(b: dict[str, Any], params: dict[str, Any] | None = None) -> dict[str, Any]:
    ac = re.match(r"\*\*AC\*\* (\d+)(?: \*\*Initiative\*\*.*)?(?: <br>)?$", b["ac_line"].strip())
    hp_line = next((l for l in b["body"] if l.startswith("**HP**")), "")
    hp = re.match(r"\*\*HP\*\* (\d+) \((\d+)d(\d+)(?: ([+−-]) (\d+))?\)", hp_line)
    if ac and hp:
        mod = int(hp.group(5) or 0) * (-1 if hp.group(4) in ("−", "-") else 1)
        return {"family": "creature_defense", "armor_class": int(ac.group(1)),
                "hit_points": int(hp.group(1)),
                "hit_point_dice": {"count": int(hp.group(2)), "die": f"d{hp.group(3)}",
                                   "modifier": mod}}
    # A parameterized profile keeps each fixed value as a number and each
    # formula as its quote-verified parameter; neither stands in for the other.
    params = params or {}
    return {"family": "creature_defense_parameterized",
            "armor_class": int(ac.group(1)) if ac else params.get("armor_class"),
            "hit_points": params.get("hit_points")}


# -- Individually assessed creatures ------------------------------------------

#: Qualified defensive terms (source_terms identify the printed residue).
CONDITIONAL_FIELDS: dict[str, dict[str, dict[str, Any]]] = {
    "monsters.half_dragon.half_dragon": {"resistance": {
        "conditional": "the one damage type chosen for Draconic Origin",
        "selection": {"vocabulary": ["acid", "cold", "fire", "lightning", "poison"],
                      "chosen_for": "Draconic Origin", "chosen_by": "GM"},
        "source_terms": ["damage type chosen"]}},
    "monsters.mages.archmage": {"condition_immunity": {
        "conditional": "charmed, while under Mind Blank",
        "predicate": {"active_effect_on_subject": "spells.mind_blank"},
        "source_terms": ["mind blank"]}},
    "monsters.rakshasa.rakshasa": {"vulnerability": {
        "conditional": "piercing, from a weapon wielded by a creature under Bless",
        "predicate": {"damage_type": "piercing", "attack": "weapon",
                      "attacker_active_effect": "spells.bless"},
        "source_terms": ["bless"]}},
    "monsters.vampires.vampire_familiar": {"condition_immunity": {
        "conditional": "charmed, except from its vampire master",
        "predicate": {"condition": "charmed",
                      "unless_source_is": {"relation": "master_of_the_subject",
                                           "qualification": "vampire"}},
        "source_terms": ["vampire master"]}},
}

#: Parameterized/fixed values that are not printed as plain numbers, per
#: creature, quote-verified on the stat block; everything else is read from
#: the block like any other.
PARAMETERS: dict[str, dict[str, Any]] = {
    "magic_items.figurine_of_wondrous_power.giant_fly": {"status": "fixed"},
    "magic_items.mysterious_deck.avatar_of_death": {
        "status": "parameterized",
        "hit_points": ("HP** Half the HP maximum of its summoner",
                       {"half_of": "summoner_hit_point_maximum"}),
        "proficiency_bonus": ("PB equals its summoner's", {"equals": "summoner_proficiency_bonus"}),
        "multiattack_count": ("equal to half the summoner's Proficiency Bonus (rounded up)",
                              {"half_round_up_of": "summoner_proficiency_bonus"}),
        "automatic_hit": ("_Melee Attack Roll:_ Automatic hit", {"entry": "Reaping Scythe"}),
        "targets_only": ("The avatar targets only you with its attacks",
                         {"only_target": "the summoner"}),
    },
    "spells.animate_objects.animated_object": {
        "status": "parameterized",
        "hit_points": ("**HP** 10 (Medium or smaller), 20 (Large), 40 (Huge)",
                       {"by_size": {"medium_or_smaller": 10, "large": 20, "huge": 40}}),
        "attack_bonus": ("Bonus equals your spell attack modifier",
                         {"equals": "caster_spell_attack_modifier"}),
        "slam_damage": ("Force damage equal to 1d4 + 3 (Medium or smaller)",
                        {"by_size": {"medium_or_smaller": "1d4 + 3",
                                     "large": "2d6 + 3 + caster_spellcasting_ability_modifier",
                                     "huge": "2d12 + 3 + caster_spellcasting_ability_modifier"},
                         "damage_type": "force"}),
    },
    "spells.find_steed.otherworldly_steed": {
        "status": "parameterized",
        "armor_class": ("**AC** 10 + 1 per spell level", {"base": 10, "per_spell_level": 1}),
        "hit_points": ("**HP** 5 + 10 per spell level", {"base": 5, "per_spell_level": 10}),
        "type_choice": ("Celestial, Fey, or Fiend (Your Choice)",
                        {"vocabulary": ["celestial", "fey", "fiend"]}),
        "slam": ("1d8 plus the spell's level of Radiant (Celestial), Psychic (Fey), or Necrotic",
                 {"damage": "1d8 + spell_level",
                  "type_by_choice": {"celestial": "radiant", "fey": "psychic",
                                     "fiend": "necrotic"}}),
    },
    "spells.giant_insect.giant_insect": {
        "status": "parameterized",
        "armor_class": ("**AC** 11 + the spell's level", {"base": 11, "per_spell_level": 1}),
        "hit_points": ("**HP** 30 + 10 for each spell level above 4",
                       {"base": 30, "per_spell_level_above": {"level": 4, "amount": 10}}),
        "form_choice": ("giant centipede, spider, or wasp",
                        {"vocabulary": ["centipede", "spider", "wasp"]}),
        "multiattack_count": ("equal to half this spell's level (round down)",
                              {"half_round_down_of": "spell_level"}),
    },
    "spells.summon_dragon.draconic_spirit": {
        "status": "parameterized",
        "armor_class": ("**AC** 14 + the spell's level", {"base": 14, "per_spell_level": 1}),
        "hit_points": ("**HP** 50 + 10 for each spell level above 5",
                       {"base": 50, "per_spell_level_above": {"level": 5, "amount": 10}}),
        "multiattack_count": ("equal to half the spell's level (round down)",
                              {"half_round_down_of": "spell_level"}),
        "breath_type_choice": ("a type this spirit has Resistance to (your choice when you cast",
                               {"vocabulary": "the spirit's printed resistances"}),
    },
}

#: Proposed, not implemented: the smallest source-required relation.
def _term(count: int, die: str, damage_type: str | None = None, constant: int = 0,
          addends: tuple[str, ...] = (), **extra: Any) -> dict[str, Any]:
    out: dict[str, Any] = {"dice": {"count": count, "die": die}, "constant": constant,
                           "addends": [{"input": a} for a in addends]}
    if damage_type:
        out["damage_type"] = damage_type
    out.update(extra)
    return out


#: Source formulas for summon entries whose hit or failure is printed as a
#: formula, quote-verified on the stat block. Inputs (``spell_level``,
#: ``caster_spellcasting_ability_modifier``) are runtime values; the formulas
#: themselves are source authority. Applied after ordinary parsing.
ENTRY_FORMULAS: dict[tuple[str, str], tuple[str, str, dict[str, Any]]] = {
    ("spells.animate_objects.animated_object", "Slam"): (
        "Force damage equal to 1d4 + 3 (Medium or smaller), 2d6 + 3 + your spellcasting "
        "ability modifier (Large), or 2d12 + 3 + your spellcasting ability modifier (Huge)",
        "attack", {"hit_damage": [], "hit_damage_by_size": {
            "medium_or_smaller": [_term(1, "d4", "force", 3)],
            "large": [_term(2, "d6", "force", 3, ("caster_spellcasting_ability_modifier",))],
            "huge": [_term(2, "d12", "force", 3, ("caster_spellcasting_ability_modifier",))]},
            "size_input": "the creature's recorded size"}),
    ("spells.find_steed.otherworldly_steed", "Otherworldly Slam"): (
        "1d8 plus the spell's level of Radiant (Celestial), Psychic (Fey), or Necrotic (Fiend) "
        "damage", "attack", {"hit_damage": [_term(
            1, "d8", None, 0, ("spell_level",),
            damage_type_by_choice={"celestial": "radiant", "fey": "psychic",
                                   "fiend": "necrotic"})]}),
    ("spells.giant_insect.giant_insect", "Poison Jab"): (
        "1d6 + 3 plus the spell's level Piercing damage plus 1d4 Poison damage",
        "attack", {"hit_damage": [_term(1, "d6", "piercing", 3, ("spell_level",)),
                                  _term(1, "d4", "poison")]}),
    ("spells.giant_insect.giant_insect", "Web Bolt"): (
        "1d10 + 3 plus the spell's level Bludgeoning damage, and the target's Speed is reduced "
        "to 0 until the start of the insect's next turn", "attack", {
            "hit_damage": [_term(1, "d10", "bludgeoning", 3, ("spell_level",))],
            "hit_effect": {"applies_to": "target",
                           "effect": {"family": "speed_modification", "change": "set_to",
                                      "feet": 0, "can_increase": True, "mode": None},
                           "duration": turn("start_of_turn", "source", "insect")}}),
    ("spells.summon_dragon.draconic_spirit", "Rend"): (
        "1d6 + 4 + the spell's level Piercing damage", "attack",
        {"hit_damage": [_term(1, "d6", "piercing", 4, ("spell_level",))]}),
    ("spells.summon_dragon.draconic_spirit", "Breath Weapon"): (
        "2d6 damage of a type this spirit has Resistance to (your choice when you cast the "
        "spell)", "save", {"failure_damage": [_term(
            2, "d6", None, 0, (),
            damage_type_by_choice={"from": "the spirit's printed resistances",
                                   "chosen_by": "caster", "when": "casting"})],
            "failure_effect": None, "success": "half_damage"}),
}


def _apply_formulas(key: str, block_lines: list[str], block: list[dict[str, Any]]) -> None:
    for (record, name), (quote, part, update) in ENTRY_FORMULAS.items():
        if record != key:
            continue
        assert any(quote in line for line in block_lines), (record, name, quote)
        entry = next(e for e in block if e["name"] == name)
        entry[part].update(update)
        entry["formula_source"] = {"quote": quote}
        entry["reasons"] = [r for r in entry["reasons"]
                            if not r.startswith(("formula hit pending", "failure rider not typed",
                                                 "hit rider not typed"))]
        if not entry["reasons"]:
            entry["classification"] = "supported"


VAMPIRE_MASTER_PROPOSAL = {
    "relation": "vampire_master",
    "owner": "the familiar's CreatureState (2b), additive optional field",
    "value": "one SubjectReference to a creature in the same story",
    "source_qualification": "vampire (the source says 'its vampire master')",
    "validation": ["the referenced creature exists in the same story",
                   "the referenced creature's vampire qualification is itself validated; "
                   "a same-story reference alone does not make a creature a vampire master",
                   "how that qualification is validated is a held determination; no exact "
                   "template or type restriction is proposed and none is invented",
                   "not inferred from summoner/controller"],
    "consumer": "only the Charmed-immunity determination on the familiar",
    "absent": "a missing relation, or a missing or unvalidated vampire qualification, "
              "refuses that one determination as missing state; nothing else changes",
    "status": "proposal for review; adding the field is dependent implementation (held)",
}


def stat_blocks(file: str) -> list[dict[str, Any]]:
    src = lines(file)
    blocks = []
    for i, line in enumerate(src):
        if not line.startswith("**AC** "):
            continue
        j = i - 1
        while not src[j].startswith("#"):
            j -= 1
        level = len(src[j]) - len(src[j].lstrip("#"))
        k = i + 1
        while k < len(src):
            h = re.match(r"^(#+) ", src[k])
            if h and len(h.group(1)) <= level:
                break
            k += 1
        blocks.append({"file": file, "line": i + 1, "first_line": j + 1,
                       "heading": src[j].lstrip("#").strip(),
                       "lines": src[j:k], "ac_line": line, "body": src[i:k],
                       "size_line": next(src[x] for x in range(j + 1, i)
                                         if src[x].startswith("_"))})
    return blocks


def creatures(rep: dict[str, Any]) -> tuple[list[Any], dict[str, Any]]:
    keys = sorted(r["semantic_key"] for r in rep["records"] if r["kind"] == "creature")
    comps = {(c["record_key"], c["semantic_key"]) for c in rep["components"]}
    cond_index: dict[str, Any] = collections.defaultdict(list)
    for c in rep["components"]:
        if c["record_key"].startswith("glossary."):
            cond_index[c["record_key"]].append(c)
    by_tail: dict[str, list[str]] = {}
    for key in keys:
        by_tail.setdefault(key.rsplit(".", 1)[1], []).append(key)
    prefix = {"monsters-A-Z.md": "monsters.", "animals.md": "animals.",
              "spells.md": "spells.", "magic-items.md": "magic_items."}
    out, unmatched, matched = [], [], set()
    for file in prefix:
        for b in stat_blocks(file):
            tail = slug(b["heading"])
            cand = [k for k in by_tail.get(tail, []) if k.startswith(prefix[file])]
            if len(cand) != 1:
                unmatched.append({"heading": b["heading"], "file": file, "line": b["line"]})
                continue
            (key,) = cand
            matched.add(key)
            assert (key, tail) in comps, key
            record: dict[str, Any] = {
                "record_key": key, "defense_component_key": tail,
                "source": {"file": file, "line": b["line"], "heading": b["heading"],
                           "block_first_line": b["first_line"],
                           "block_last_line": b["first_line"] + len(b["lines"]) - 1},
                "defense": None,
                "profile": _profile(b, CONDITIONAL_FIELDS.get(key, {})),
            }
            if key in PARAMETERS:
                params = {}
                for field, value in PARAMETERS[key].items():
                    if field == "status":
                        continue
                    quote, typed = value
                    at = next((n for n, l in enumerate(lines(file), 1) if quote in l
                               and n >= b["line"] - 30), None)
                    assert at is not None, (key, quote)
                    params[field] = {**typed, "source": {"file": file, "line": at,
                                                         "quote": quote}}
                record["parameters"] = params
                record["classification"] = PARAMETERS[key]["status"]
            record["defense"] = _defense(b, record.get("parameters"))
            assert record["defense"].get("armor_class") is not None, key
            assert record["defense"].get("hit_points") is not None, key
            if key in CONDITIONAL_FIELDS:
                record["classification"] = "conditional"
            if key == "monsters.vampires.vampire_familiar":
                record["proposed_relation"] = VAMPIRE_MASTER_PROPOSAL
            record["entries"] = entries(b["lines"], cond_index, b["file"], b["first_line"])
            _apply_formulas(key, b["lines"], record["entries"])
            for e in record["entries"]:
                dispose_entry(e)
            for e in record["entries"]:
                component = _ANCHOR[e["section"]]
                assert (key, component) in comps, (key, component, e["name"])
                e["component_key"] = component
                if key in PARAMETERS and PARAMETERS[key]["status"] == "parameterized" \
                        and e["kind"] == "attack" and e["attack"]["attack_bonus"] is None:
                    e["classification"] = "conditional"
            profile_cond = [f for f in CONDITIONAL_FIELDS.get(key, {})]
            _check_possessors(b["heading"], record["entries"])
            record["target_side"] = _rollup(record["entries"], profile_cond)
            cross = sorted(e["name"] for e in record["entries"]
                           if e["name"] in ("Pack Tactics", "Aura of Authority", "Bound",
                                            "Inscrutable"))
            if cross:
                record["target_side"]["encounter_state"] = {
                    "entries": cross,
                    "note": "depends on or changes other creatures' operations (allies' "
                            "positions, a related wearer, others' checks); a block-level "
                            "rollup cannot see them"}
            record.setdefault("classification", "typed")
            out.append(record)
    census = {"creature_records": len(keys),
              "unmatched_records": [k for k in keys if k not in matched],
              "unmatched_stat_blocks": unmatched}
    return out, census


# Parameterized attacks print "Bonus equals your spell attack modifier" or
# "Automatic hit" instead of a number: read them as attacks with that input.
_orig_attack = _attack


def _attack(text: str) -> dict[str, Any] | None:  # noqa: F811
    parsed = _orig_attack(text)
    if parsed is not None:
        return parsed
    text = text.replace("Melee or _Ranged Attack Roll:_", "_Melee or Ranged Attack Roll:_")
    m = re.match(r"^_(?P<kind>Melee|Ranged) Attack Roll:_ (?P<bonus>Bonus equals your spell "
                 r"attack modifier|Automatic hit), (?P<reach>.+?)\. _Hit:_ (?P<hit>.*)$", text)
    if not m:
        return None
    rm = re.fullmatch(r"(?:reach (\d+) (?:ft\.?|feet))?(?:range (\d+) ft)?", m.group("reach"))
    terms, rest = _damage_terms(m.group("hit"))
    rest = rest.strip(" .")
    reasons = []
    if not terms or rest:
        # Replaced by a quote-verified formula overlay (ENTRY_FORMULAS); an
        # entry without one is missing source authority (asserted in main).
        reasons.append(f"formula hit pending overlay: {m.group('hit')!r}")
    automatic = m.group("bonus") == "Automatic hit"
    return {"kind": slug(m.group("kind")),
            "attack_bonus": None if automatic else {"formula_ref": "spells.attack_rolls/spell_attack_modifier", "of": "caster"},
            "automatic_hit": m.group("bonus") == "Automatic hit",
            "reach_ft": int(rm.group(1)) if rm and rm.group(1) else None,
            "normal_range_ft": int(rm.group(2)) if rm and rm.group(2) else None,
            "long_range_ft": None, "advantage_when": None,
            "hit_damage": terms, "hit_effect": None, "untyped": reasons}


# ===========================================================================


#: Digest of every (name, normalized text) instance read and accepted as having
#: no roster effect. A new or changed instance of an allowlisted name changes
#: it and fails the build until that text is read (see no-effect-review.json).
REVIEWED_NO_EFFECT_SHA256 = "90751c05ee3ff481fb0bee94be8d46a3a20cf4f0672c8ad62f61527b8ddd1a2d"  # pragma: allowlist secret


def no_effect_review(records: list[Any]) -> tuple[list[Any], str]:
    rows = set()
    for r in records:
        words = sorted({w for w in re.findall(r"[a-z]+", r["source"]["heading"].lower())
                        if len(w) > 2}, key=len, reverse=True)
        for e in r["entries"]:
            if e["kind"] != "no_roster_effect":
                continue
            text = e["text"].lower()
            for w in words:
                text = re.sub(rf"\b{w}s?\b", "X", text)
            rows.add((e["name"], NO_ROSTER_EFFECT[e["name"]], text))
    listed = [{"name": n, "reviewed": why, "text": t} for n, why, t in sorted(rows)]
    return listed, sha(json.dumps(listed, sort_keys=True).encode())


def reuse_validation(a_facts: list[Any], b: list[Any], c_facts: list[Any]) -> dict[str, Any]:
    from afterworlds.ingestion.mechanical.representation import fact_from_payload

    results: list[dict[str, Any]] = []

    def visit(node: Any, where: str) -> None:
        if isinstance(node, dict):
            fam = node.get("family")
            if fam in REUSED:
                try:
                    fact_from_payload(node)
                    results.append({"where": where, "family": fam, "ok": True})
                except Exception as exc:  # noqa: BLE001
                    results.append({"where": where, "family": fam, "ok": False,
                                    "error": f"{type(exc).__name__}: {exc}"})
                return
            for k, v in node.items():
                visit(v, f"{where}.{k}")
        elif isinstance(node, list):
            for i, v in enumerate(node):
                visit(v, f"{where}[{i}]")

    visit(a_facts, "c3a.facts")
    visit([r.get("defense") for r in b], "c3b.defense")
    visit([e for r in b for e in r["entries"]], "c3b.entries")
    visit(c_facts, "c3c.facts")
    new = collections.Counter()
    for f in a_facts + c_facts:
        if f["fact"]["family"] not in REUSED:
            new[f["fact"]["family"]] += 1
    return {"reused_payloads": len(results),
            "failures": [r for r in results if not r["ok"]],
            "by_family": dict(collections.Counter(r["family"] for r in results)),
            "new_family_payloads": dict(new)}


def transition(parts: dict[str, list[str]], rep_raw: dict[str, Any]) -> dict[str, Any]:
    span_batch = {r["span_id"]: r["batch_id"] for r in rep_raw["acceptance"]["records"]}
    record_batches: dict[str, set[str]] = collections.defaultdict(set)
    for pb in rep_raw["representation"]["prose_bindings"]:
        if pb["span_id"] in span_batch:
            record_batches[pb["record_key"]].add(span_batch[pb["span_id"]])
    touched: dict[str, set[str]] = collections.defaultdict(set)
    for part, recs in parts.items():
        for rk in recs:
            for batch in record_batches.get(rk, {"<unbound>"}):
                touched[batch].add(part)
    return {"batches": {b: sorted(p) for b, p in sorted(touched.items())},
            "batch_count": len(touched),
            "records_touched": {p: len(set(r)) for p, r in parts.items()},
            "all_batches": len(rep_raw["acceptance"]["batches"])}


def main() -> None:
    own = Path(__file__).read_text("utf-8")
    assert not re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", own), "control character"
    for rel, digest in PRESERVED.items():
        assert sha((NOTES / rel).read_bytes()) == digest, f"preserved file changed: {rel}"
    raw = ORACLE.read_bytes()
    assert sha(raw) == ORACLE_SHA256, "accepted oracle changed"
    oracle = json.loads(raw)
    rep = oracle["representation"]
    comps = {(c["record_key"], c["semantic_key"]) for c in rep["components"]}
    records = {r["semantic_key"] for r in rep["records"]}

    tool_facts, tool_concord = tools(records, comps)
    a_facts = (c1a.weapons() + rule_facts(RULES, comps) + tool_facts
               + rule_facts(STAT_BLOCK_RULES, comps) + rule_facts(SPELLCASTING_RULES, comps)
               + grant_facts(comps))
    for f in a_facts:
        if f["fact"]["family"] == "damage":  # weapon rows: accepted family, unchanged
            assert "option_key" not in f["fact"]
    assert not {(f["record_key"], f["component_key"]) for f in a_facts} - comps
    # Expertise gain levels must resolve to accepted progression_entry facts.
    gains = {f["entitlement_key"] for c in rep["components"] for f in c.get("facts", [])
             if f.get("family") == "progression_entry"}
    assert all(f["fact"]["gain_levels"]["entitlement_key"] in gains for f in a_facts
               if "gain_levels" in f["fact"])

    c_facts = c1c.armor() + rule_facts(ARMOR_RULES, comps)

    creature_records, census = creatures(rep)

    meta = {"status": STATUS, "proposed_schema": PROPOSED_SCHEMA,
            "anchored_oracle_sha256": ORACLE_SHA256, "supersedes": "15c-C4 (unaccepted)"}
    regressions(creature_records, a_facts, c_facts)
    source_records, capability = split_capability(creature_records)
    invariant_report = invariants(source_records, creature_records, a_facts, c_facts)
    part_a = {"candidate_id": "15c-C5-A", **meta, "facts": a_facts}
    part_b = {"candidate_id": "15c-C5-B", **meta, "creatures": source_records,
              "census": census}
    part_c = {"candidate_id": "15c-C5-C", **meta, "facts": c_facts}
    write("source-key-review.json", source_key_review([part_a, part_b, part_c]))
    write("entitlement-examples.json", {
        "note": "source-rule assertions over the candidate's facts; not runtime entitlement "
                "validation, which stays held until native semantic acceptance",
        "source_rule_assertions": entitlement_examples(a_facts),
        "vocabulary_resolution": grant_vocabulary_resolution(
            a_facts, c_facts, [f for c in rep["components"] for f in c.get("facts", [])])})
    h_a = write("c5a.json", part_a)
    h_b = write("c5b.json", part_b)
    h_c = write("c5c.json", part_c)
    capability["scope"] = CAPABILITY_SCOPE
    h_cap = write("capability.json", {"candidate_id": "15c-C5-capability", "status": STATUS,
                                      "note": "execution evidence, not source authority",
                                      **capability})
    reuse = reuse_validation(a_facts, source_records, c_facts)
    write("reuse-validation.json", reuse)
    assert not reuse["failures"], reuse["failures"][:3]
    write("rules-disposition.json", rules_disposition())
    reviewed, reviewed_digest = no_effect_review(creature_records)
    write("no-effect-review.json", {"digest": reviewed_digest, "instances": reviewed})
    assert reviewed_digest == REVIEWED_NO_EFFECT_SHA256, (
        f"no-roster-effect instances changed ({reviewed_digest}); read no-effect-review.json "
        "and re-pin only after every instance is reviewed")
    trans = transition({
        "c5a.json": [f["record_key"] for f in a_facts],
        "c5b.json": [r["record_key"] for r in creature_records],
        "c5c.json": [f["record_key"] for f in c_facts]}, oracle)
    write("transition.json", trans)
    write("invariants.json", invariant_report)

    entries_all = [(r, e) for r in creature_records for e in r["entries"]]
    attack_lines = {f: sum("Attack Roll:" in l for l in lines(f))
                    for f in ("monsters-A-Z.md", "animals.md", "spells.md", "magic-items.md")}
    parsed_attacks = sum(1 for _, e in entries_all if e["kind"] == "attack")
    assert sum(attack_lines.values()) == 429 and parsed_attacks == 429, attack_lines
    ma = [e for _, e in entries_all if e["kind"] == "multiattack"]
    deps = collections.Counter(d["kind"] for c in capability["entries"].values()
                               for d in c["dependencies"])
    concordance = {
        "hashes": {"c5a.json": h_a, "c5b.json": h_b, "c5c.json": h_c, "capability.json": h_cap},
        "tools": tool_concord,
        "attack_roll_lines": {"by_file": attack_lines, "total": sum(attack_lines.values()),
                              "parsed_attacks": parsed_attacks,
                              "in_assessed_creatures": sum(
                                  1 for r, e in entries_all
                                  if e["kind"] == "attack" and r["record_key"] in PARAMETERS)},
        "creatures": {
            "records": census["creature_records"],
            "matched": census["creature_records"] - len(census["unmatched_records"]),
            "entry_kinds": dict(collections.Counter(e["kind"] for _, e in entries_all)),
            "entry_classification": dict(collections.Counter(
                e["classification"] for _, e in entries_all)),
            "dependency_kinds": dict(deps),
            "executable_once_accepted": dict(collections.Counter(
                e["kind"] for _, e in entries_all if e.get("executable_once_accepted"))),
            "multiattack_selections": {
                "total": sum(len(e["selections"]) for e in ma),
                "executable": sum(s["executable_once_accepted"] for e in ma
                                  for s in e["selections"]),
                "base_executable_beside_unavailable_option": sum(
                    1 for e in ma if e["executable_once_accepted"] and any(
                        not s["executable_once_accepted"] for s in e["selections"]
                        if "replacement" in s["selection"] or "optional" in s["selection"]))},
            "unreviewed_entries": sorted({e["name"] for _, e in entries_all
                                          if e["kind"] == "unreviewed"}),
        },
        "invariants": {k: (len(v) if isinstance(v, list) else v)
                       for k, v in invariant_report.items()},
        "reuse_validation": {k: reuse[k] for k in ("reused_payloads", "by_family")}
        | {"failures": len(reuse["failures"])},
        "transition": {k: trans[k] for k in ("batch_count", "batches")},
    }
    write("concordance.json", concordance)
    for rel, digest in PRESERVED.items():
        assert sha((NOTES / rel).read_bytes()) == digest, f"preserved file changed: {rel}"
    print(json.dumps(concordance["hashes"], indent=1))
    print(json.dumps({k: v for k, v in concordance.items() if k not in ("tools", "hashes")},
                     indent=1)[:5000])


# ===========================================================================
# Source / capability split, and the general invariants
# ===========================================================================

#: Capability (not source) facts about the A/C parts: execution exclusions and
#: adapter procedures that C3 had placed inside source payloads.
CAPABILITY_SCOPE = {
    "execution_exclusions": [
        {"identity": "equipment.weapons.ammunition/ammunition", "part": "recovery",
         "why": "post-fight ammunition recovery is outside the bounded roster; the source "
                "rule is kept intact in c5a"},
        {"identity": "equipment.armor/light_medium_or_heavy_armor", "part": "cannot_cast_spells",
         "why": "spellcasting is a non-goal; the source rule is kept intact in c5c"},
        {"identity": "classes.*.weapon_mastery/weapon_mastery", "part": "rest_swap",
         "why": "changing mastery choices after a Long Rest is a rest-resource transition; "
                "it refuses explicitly. The source qualifier is kept intact in c5a"},
    ],
    "observations": [
        {"identity": "G1 progression_entry 'weapon_mastery'",
         "note": "G1 records the Barbarian and Fighter Weapon Mastery column quantities under "
                 "one unqualified entitlement key, so it cannot say which class a count "
                 "belongs to. C5-A types each class's count from its own Features table; the "
                 "accepted G1 entry is preserved unchanged and is not relied on for counts"},
        {"identity": "clause links (effect_id, bound_effect, ends_effects, "
                     "duration_of_effects, lasts_while_effect, branch)",
         "note": "entry-local source associations, not runtime identifiers. Execution binds "
                 "the effect instances it creates to these ids; it never recovers an "
                 "association from prose"},
    ],
    "adapter_procedures": [
        {"identity": "play.damage_and_healing/hit_points",
         "procedure": "apply the minimum-0 bound after damage overflow is computed (massive "
                      "damage needs it); never a persistence floor (ADR-0003)"},
        {"identity": "monsters.parts_of_a_stat_block/multiattack",
         "procedure": "certify each selected composition by its own parts"},
    ],
}

#: How a capability reason maps to a dependency kind.
_DEPENDENCY = [
    ("missing_runtime_input", ("missing runtime input",)),
    ("missing_state", ("missing state", "visibility prerequisite", "area membership",
                       "range needs", "turn-start trigger", "Recharge needs", "legendary timing",
                       "timed effect", "timed/linked effect", "the lair variant",
                       "needs the creature's recorded current form",
                       "Advantage predicate needs", "grants [")),
    ("untyped_source_clause", ("hit rider not typed", "failure rider not typed",
                               "success effect not typed", "failure-or-success effect",
                               "miss effect not typed", "target predicate not typed",
                               "reach/range not typed")),
    ("missing_source_authority", ("formula hit pending", "turn owner",
                                  "missing source authority", "untyped source clause")),
    ("unsupported_mechanic", ("unsupported", "special effect", "separately selected",
                              "composition residue", "hit prints no", "usage not typed",
                              "general spell execution", "reaction trigger",
                              "trait not individually reviewed")),
]


#: Reviewed clusters of untyped clauses that are genuinely new mechanics
#: (named). Every other untyped clause is an ordinary source shape not yet
#: typed: missing source authority, never an exclusion.
NEW_MECHANIC_CLUSTERS: list[tuple[str, str]] = [
    ("swallowing", r"swallow"),
    ("Hit Point maximum reduction", r"Hit Point maximum decreases"),
    ("Exhaustion and aging", r"Exhaustion level|years older"),
    ("curses", r"\bcursed?\b"),
    ("restraint by a breakable object", r"until the (?:web|rope) is destroyed"),
    ("duration bound to the source's death or plane", r"until the [\w' -]+? dies or is on a "
                                                      r"different plane"),
    ("armor or object degradation", r"penalty to the AC it offers|armor is destroyed|"
                                    r"flammable object|starts burning"),
    ("teleport, banishment or planar travel", r"teleport|reappears|transported|demiplane"),
    ("Concentration interaction", r"Concentration"),
    ("action-economy restriction", r"can't take Reactions|Bonus Action|takes? no actions"),
    ("healing or HP regain", r"regains? .*Hit Points"),
    ("instant death or petrification", r"\bdies\b|Petrified|turns to stone"),
]


def _dependency(reason: str, deferred_named: bool) -> dict[str, str]:
    if m := re.match(r"unsupported mechanic \((?P<c>[^)]+)\): ", reason):
        return {"kind": "unsupported_mechanic", "cluster": m["c"], "detail": reason}
    for kind, prefixes in _DEPENDENCY:
        if reason.startswith(prefixes):
            if kind == "untyped_source_clause":
                for name, rx in NEW_MECHANIC_CLUSTERS:
                    if re.search(rx, reason):
                        return {"kind": "unsupported_mechanic", "cluster": name,
                                "detail": reason}
                return {"kind": "missing_source_authority",
                        "detail": reason + " (ordinary source shape not yet typed)"}
            return {"kind": kind, "detail": reason}
    if deferred_named:
        return {"kind": "unsupported_mechanic", "detail": reason}
    raise AssertionError(f"unclassified capability reason: {reason!r}")


_CAPABILITY_KEYS = ("classification", "reasons", "blocked_by", "executable_once_accepted",
                    "selections", "reviewed", "applies", "applicability", "affects",
                    "clause_dispositions")


SOURCE_KINDS = frozenset({"attack", "save_effect", "multiattack", "usage_header",
                          "entry_reference", "reaction", "observer_check"})


def split_capability(records: list[Any]) -> tuple[list[Any], dict[str, Any]]:
    source, entries_cap, records_cap = [], {}, {}
    for r in records:
        rec = {k: v for k, v in r.items()
               if k not in ("classification", "target_side", "proposed_relation", "entries")}
        rec["entries"] = []
        for i, e in enumerate(r["entries"]):
            src = {k: v for k, v in e.items() if k not in _CAPABILITY_KEYS and k != "_text"}
            # The complete logical source entry, verbatim, on every entry.
            src.pop("text", None)
            src["source_text"] = e["_text"]
            if "grants_conditions" in src:
                # Which roll contexts a granted condition touches is derived
                # applicability (capability); the source states the grant.
                src["grants_conditions"] = sorted(src["grants_conditions"])
            # Source kind is the printed shape only; roles such as contributor,
            # separate action, named mechanic or no effect are capability.
            if src["kind"] not in SOURCE_KINDS:
                src["kind"] = "prose"
            rec["entries"].append(src)
            entries_cap[f"{r['record_key']}#{i}:{e['name']}"] = {
                "entry_kind": e["kind"],
                "classification": e["classification"],
                "dependencies": [_dependency(x, e["classification"] == "deferred")
                                 for x in e.get("reasons", [])],
                **{k: e[k] for k in ("blocked_by", "applies", "executable_once_accepted",
                                     "selections", "reviewed", "applicability", "affects",
                                     "clause_dispositions", "grants_conditions")
                   if k in e},
            }
        records_cap[r["record_key"]] = {
            "classification": r["classification"], "target_side": r["target_side"],
            **({"proposed_relation": r["proposed_relation"]} if "proposed_relation" in r
               else {})}
        source.append(rec)
    return source, {"records": records_cap, "entries": entries_cap}


_SCOPE_WORDS = re.compile(r"roster|adapter|excluded|certif|adjudicat|executable|deferred|"
                          r"\bheld\b|outside the|non-goal", re.I)


def _values(node: Any, skip: tuple[str, ...]) -> list[str]:
    out: list[str] = []
    if isinstance(node, dict):
        for k, v in node.items():
            if k in skip:
                continue
            out += [k] if isinstance(k, str) else []
            out += _values(v, skip)
    elif isinstance(node, list):
        for v in node:
            out += _values(v, skip)
    elif isinstance(node, str):
        out.append(node)
    return out


#: The one normalization applied to raw source lines when joining a logical
#: entry: an ``&emsp;`` paragraph prefix and ``<br>`` are formatting only, and
#: physical lines join with one space.
def _normalize(raw_lines: list[str]) -> str:
    text = " ".join(x.removeprefix("&emsp;").strip() for x in raw_lines)
    return re.sub(r"\s*<br>\s*", " ", text).strip()


_RAW_HEAD = re.compile(r"^(?:\*\*_|_[A-Z])")
_PROFILE_LABELS = ("**AC**", "**HP**", "**Speed**", "**Initiative**", "**Skills**",
                   "**Senses**", "**Languages**", "**CR**", "**Resistances**",
                   "**Immunities**", "**Vulnerabilities**", "**Gear**", "**Saving Throws**")


def conservation(source_records: list[Any]) -> dict[str, Any]:
    """Logical-entry completeness, re-read from the raw files without the
    entry or clause parsers: after each block's CR line, every non-blank,
    non-heading, non-``<hr>`` line belongs to exactly one entry span; each
    span reproduces that entry's ``source_text``; raw head lines and entries
    correspond one to one."""
    problems, entries_checked, lines_checked = [], 0, 0
    profile_strays = []
    for r in source_records:
        src = r["source"]
        raw = lines(src["file"])
        first, last = src["block_first_line"], src["block_last_line"]
        block = list(range(first, last + 1))
        cr = next(n for n in block if raw[n - 1].startswith("**CR**"))
        size = next(n for n in block if raw[n - 1].startswith("_"))
        for n in range(size + 1, cr):
            t = raw[n - 1].strip()
            if t and not t.startswith(_PROFILE_LABELS + ("<", "|")):
                profile_strays.append({"record": r["record_key"], "line": n, "text": t})
        content = {n for n in block if n > cr and raw[n - 1].strip()
                   and not raw[n - 1].startswith("#") and raw[n - 1].strip() != "<hr>"}
        heads = {n for n in content if _RAW_HEAD.match(raw[n - 1])}
        claimed: list[int] = []
        for e in r["entries"]:
            sp = e["source_span"]
            assert sp["file"] == src["file"], (r["record_key"], e["name"])
            span = list(range(sp["first_line"], sp["last_line"] + 1))
            claimed += span
            joined = _normalize([raw[n - 1] for n in span])
            text = e["source_text"]
            if re.match(r"^_[^_.]+?\. [A-Z]", raw[span[0] - 1]):
                # The malformed spells.md head "_Name. Melee Attack Roll:_" is
                # read with its italic restored; the raw line lacks that "_".
                text = text.removeprefix("_")
            if not joined.endswith(text) or sp["first_line"] not in heads:
                problems.append({"record": r["record_key"], "entry": e["name"],
                                 "span": [span[0], span[-1]]})
        entries_checked += len(r["entries"])
        lines_checked += len(content)
        if sorted(claimed) != sorted(content) or len(claimed) != len(set(claimed)):
            problems.append({"record": r["record_key"],
                             "unclaimed": sorted(content - set(claimed)),
                             "outside_or_twice": sorted(n for n in claimed
                                                        if n not in content
                                                        or claimed.count(n) > 1)})
        if len(heads) != len(r["entries"]):
            problems.append({"record": r["record_key"], "heads": len(heads),
                             "entries": len(r["entries"])})
    assert not problems, problems[:5]
    assert not profile_strays, profile_strays[:5]
    return {"entries": entries_checked, "content_lines": lines_checked,
            "problems": problems, "profile_region_strays": profile_strays,
            "normalization": "an &emsp; prefix and <br> removed; physical lines joined "
                             "with one space"}


_SIZE_WORDS = ("tiny", "small", "medium", "large", "huge", "gargantuan")
_ARMOR_WORDS = ("light", "medium", "heavy", "shields")


def _tokens(text: str, vocab: set[str]) -> collections.Counter[str]:
    words = re.findall(r"[a-z]+|\d+", text.lower().replace("_", " "))
    return collections.Counter(w for w in words if w in vocab or w.isdigit())


def _stem_tokens(text: str, vocab: set[str]) -> collections.Counter[str]:
    words = re.findall(r"[a-z]+|\d+", text.lower().replace("_", " "))
    return collections.Counter(w.rstrip("s") for w in words
                               if w.rstrip("s") in vocab or w.isdigit())


def _turn_owner(raw: str) -> str | None:
    m = re.search(r"(?:start|end) of (its|the target's|this|the [\w' -]+?'s) (?:next )?turn",
                  raw)
    if not m:
        return None
    return {"its": "target", "the target's": "target", "this": "this_turn"}.get(m[1], "source")


def fidelity(source_records: list[Any], a_facts: list[Any]) -> dict[str, Any]:
    """Source-to-field fidelity without the readers: the closed-vocabulary
    tokens (sizes, conditions, damage types, abilities, numbers and dice) of
    each typed piece's raw text must all be present in its serialized fields,
    as a multiset. Grant facts are checked the same way against their quote
    (abilities, armor words, numbers)."""
    vocab = (set(_SIZE_WORDS) | set(CONDITIONS) | set(DAMAGE) | set(ABILITY)
             | {"minute", "minutes", "hour", "hours"})
    fails, pieces, turns = [], collections.Counter(), 0
    for r in source_records:
        for e in r["entries"]:
            body = e.get("attack") or e.get("save") or {}
            for c in body.get("clauses", []):
                for p in c["pieces"]:
                    if "typed" not in p:
                        continue
                    pieces[p["typed"]["family"]] += 1
                    raw = _tokens(p["text"].replace("minutes", "minute")
                                  .replace("hours", "hour"), vocab)
                    pointed = [body["hit_damage"][i] for i in
                               p["typed"].get("unconditional_hit_damage_indices", [])]
                    held = _tokens(json.dumps([p["typed"], pointed], ensure_ascii=False)
                                   .replace("minutes", "minute").replace("hours", "hour"), vocab)
                    if raw - held:
                        fails.append({"record": r["record_key"], "entry": e["name"],
                                      "piece": p["text"], "missing": sorted(raw - held)})
                    owner = _turn_owner(p["text"])
                    if owner:
                        turns += 1
                        found = {v["turn_of"] if v["turn_of"] != "target" or v.get("turn")
                                 != "this" else "this_turn"
                                 for v in _walk(p["typed"])
                                 if isinstance(v, dict) and "turn_of" in v}
                        found |= {"this_turn" for v in _walk(p["typed"]) if isinstance(v, dict)
                                  and v.get("turn") == "this"}
                        if owner not in found:
                            fails.append({"record": r["record_key"], "entry": e["name"],
                                          "piece": p["text"], "turn_owner": owner,
                                          "typed_turn_of": sorted(found)})
    gvocab = (set(ABILITY) | {w.rstrip("s") for w in _ARMOR_WORDS}
              | {"simple", "martial", "finesse", "melee", "tool", "supplie", "kit",
                 "musical", "instrument", "gaming", "set", "artisan", "thieve", "herbalism",
                 "calligrapher"})
    grants = 0
    for f in a_facts:
        if not f["fact"]["family"].endswith(("_grant", "_choice")) \
                or f["fact"]["family"].startswith(("skill", "multiclass_skill", "feat")):
            continue
        grants += 1
        raw = _stem_tokens(f["source"]["quote"], gvocab)
        held = _stem_tokens(json.dumps(f["fact"]), gvocab)
        if raw - held:
            fails.append({"record": f["record_key"], "quote": f["source"]["quote"],
                          "missing": sorted(raw - held)})
    assert not fails, fails[:5]
    return {"typed_pieces_by_family": dict(sorted(pieces.items())),
            "turn_owner_pieces_checked": turns,
            "grant_facts_checked": grants, "failures": fails}


#: Every key path in the source parts, reviewed once as source fact (not
#: storage, applicability, certification or execution policy). A new path
#: fails the derivation until it is reviewed here.
def key_paths(node: Any, prefix: str = "") -> set[str]:
    out: set[str] = set()
    if isinstance(node, dict):
        for k, v in node.items():
            p = f"{prefix}.{k}"
            # Option, choice and table keys inside a value are data, not schema.
            if k in ("count_by_level", "by_family", "patterns") or re.fullmatch(r"\d+", k):
                out.add(p)
                continue
            out.add(p)
            out |= key_paths(v, p)
    elif isinstance(node, list):
        for v in node:
            out |= key_paths(v, prefix + "[]")
    return out


#: Candidate packaging around the minted facts (identity, status, census);
#: never minted as source facts.
PACKAGING_KEYS = frozenset({"candidate_id", "status", "proposed_schema", "supersedes",
                            "anchored_oracle_sha256", "census", "creature_records",
                            "unmatched_records", "unmatched_stat_blocks"})
#: SHA-256 of the sorted key names of C5-A/B/C after the one-by-one review in
#: source-key-review.json (each is a source fact, a source location, or
#: packaging). A new key name fails the derivation until reviewed.
REVIEWED_SOURCE_KEYS_SHA256 = "dc0b1521029a9458694281699b2ba1bc8fad381219f3b786155a0f486d1bbfcd"  # pragma: allowlist secret


def source_key_review(parts: list[Any]) -> dict[str, Any]:
    names: set[str] = set()
    for part in parts:
        names |= {k.rsplit(".", 1)[-1].removesuffix("[]") for k in key_paths(part)}
    names = {n for n in names if not re.fullmatch(r"\d+", n)}
    digest = sha("\n".join(sorted(names)).encode())
    if digest != REVIEWED_SOURCE_KEYS_SHA256:
        prior = set(json.loads((HERE / "source-key-review.json").read_text("utf-8"))
                    .get("key_names", [])) if (HERE / "source-key-review.json").exists() else set()
        raise AssertionError(("unreviewed source keys", digest,
                              {"added": sorted(names - prior),
                               "removed": sorted(prior - names)}))
    return {"key_names": sorted(names), "packaging": sorted(PACKAGING_KEYS & names),
            "sha256": digest,
            "review": "each name read once as a source fact, a source location/quote, a "
                      "reader-local link (effect_id, bound_effect, ends_effects, branch: "
                      "entry-local, never runtime identity) or candidate packaging; "
                      "removed after review: grants_conditions roll-context mapping (to "
                      "capability), Half-Dragon recorded_as and Vampire Familiar requires "
                      "(to capability), Swarm applies_when/precedence (to capability), "
                      "legendary blocked_by renamed not_while_has_conditions"}


def invariants(source_records: list[Any], records: list[Any], a_facts: list[Any],
               c_facts: list[Any]) -> dict[str, Any]:
    """General completeness checks (not example assertions)."""
    report: dict[str, Any] = {"logical_entry_conservation": conservation(source_records),
                              "source_to_field_fidelity": fidelity(source_records, a_facts)}
    # 1. Source parts carry no scope/capability vocabulary (prose fields aside).
    prose = ("text", "quote", "source", "formula_source", "_text", "untyped_clauses",
             "trigger", "source_text")
    leaks = [v for v in _values([a_facts, c_facts, source_records], prose)
             if _SCOPE_WORDS.search(v)]
    assert not leaks, leaks[:10]
    report["scope_vocabulary_leaks"] = leaks
    # 2. Every number printed in a typed attack/save entry is in a field or in
    #    explicit residue.
    # Checked against the *source* entry (what would be minted), never the
    # capability reasons. Set comparison: a dropped number equal to another
    # printed number would pass (stated limitation).
    missing = []
    for r, sr in zip(records, source_records, strict=True):
        for e, se in zip(r["entries"], sr["entries"], strict=True):
            if e["kind"] not in ("attack", "save_effect", "multiattack"):
                continue
            body = re.sub(r"\(Recharge [^)]*\)|\(\d/Day[^)]*\)", "", e["_text"])
            printed = set(re.findall(r"\d+", body))
            held = set(re.findall(r"\d+", json.dumps(
                {k: v for k, v in se.items()
                 if k not in ("name", "source_text", "source_span")}, ensure_ascii=False)))
            if printed - held:
                missing.append({"record": r["record_key"], "entry": e["name"],
                                "numbers": sorted(printed - held)})
    assert not missing, missing[:10]
    report["unaccounted_numbers"] = missing
    # 3. Every formula reference resolves to a typed source fact.
    known = {f"{f['record_key']}/{f['component_key']}" for f in a_facts}
    refs = [v["formula_ref"] for v in _walk(records) if isinstance(v, dict)
            and "formula_ref" in v]
    unresolved = sorted({x for x in refs if x not in known})
    assert not unresolved, unresolved
    report["formula_references"] = sorted(set(refs))
    # 4. Target grammar: every save-target phrasing parsed, residue listed.
    residue = [{"record": r["record_key"], "entry": e["name"],
                "untyped_target_clause": c["text"]}
               for r in source_records for e in r["entries"] if e.get("save")
               for c in e["save"].get("clauses", []) if c["part"] == "targets"]
    report["target_residue"] = residue
    # 5. Every parameterized attack has its formula (no pending overlay).
    pending = [(r["record_key"], e["name"]) for r in records for e in r["entries"]
               if any(x.startswith("formula hit pending") for x in e.get("reasons", []))]
    assert not pending, pending
    report["parameterized_entries_without_formula"] = pending
    return report


def _walk(node: Any) -> list[Any]:
    out = [node]
    if isinstance(node, dict):
        for v in node.values():
            out += _walk(v)
    elif isinstance(node, list):
        for v in node:
            out += _walk(v)
    return out


def grant_vocabulary_resolution(a_facts: list[Any], c_facts: list[Any],
                                g1_facts: list[Any]) -> dict[str, Any]:
    """Every choice vocabulary or granted identity in a grant fact resolves to
    a typed fact (C5-A/C or accepted G1): skills, tool identities, tool
    variants, the Artisan's Tools category, weapon categories and properties,
    armor categories, and record/component references."""
    pair = lambda f: (f["record_key"], f["component_key"])  # noqa: E731
    tools = {pair(f) for f in a_facts if f["fact"]["family"] == "tool_entry"}
    tool_cats = {f["fact"]["category"] for f in a_facts if f["fact"]["family"] == "tool_entry"}
    variants = {pair(f) for f in a_facts if f["fact"]["family"] == "tool_variants"}
    props = {f["fact"]["property"] for f in a_facts if f["fact"]["family"] == "weapon_property"}
    ranges = {f["fact"]["range_class"] for f in a_facts
              if f["fact"]["family"] == "weapon_range_class"}
    cats = {f.get("category") for f in g1_facts if f.get("family") == "weapon_category"}
    armor = {str(v) for f in c_facts for v in f["fact"].values() if isinstance(v, str)}
    refs = {f"{f['record_key']}/{f['component_key']}" for f in a_facts}
    checked, bad = 0, []

    def ok(v: Any, field: str) -> bool:
        if isinstance(v, list):
            return all(ok(x, field) for x in v)
        if isinstance(v, dict):
            if "tool_variants_of" in v:
                sel = v["tool_variants_of"]
                return (sel["record_key"], sel["component_key"]) in variants
            if "record_key" in v and field == "tools":
                return (v["record_key"], v["component_key"]) in tools
            if "tool_category" in v:
                return v["tool_category"] in tool_cats
            if "any_tool_entry" in v:
                return bool(tools)
            return all(ok(x, k) for k, x in v.items() if k in _VOCAB_FIELDS)
        if field == "from":
            return v in _ALL_SKILLS or v in refs
        if field == "tools":
            return v in tools
        if field == "categories" or field == "category":
            return v in cats
        if field == "with_any_property":
            return v in props
        if field == "armor":
            return v in armor
        return True

    for f in a_facts:
        fam = f["fact"]["family"]
        if not fam.endswith(("_grant", "_choice")) or fam.startswith(("feat", "ability")):
            continue
        for k, v in f["fact"].items():
            if k in _VOCAB_FIELDS:
                checked += 1
                if not ok(v, k):
                    bad.append({"record": f["record_key"], "family": fam, "field": k,
                                "value": v})
        if f["fact"].get("melee_only"):
            checked += 1
            if "melee" not in ranges:
                bad.append({"record": f["record_key"], "field": "melee_only"})
    assert cats >= {"simple", "martial"}, cats
    assert not bad, bad[:5]
    return {"fields_checked": checked, "unresolved": bad}


_VOCAB_FIELDS = ("from", "tools", "categories", "with_any_property", "armor", "weapons",
                 "armor_training", "qualified", "or_tools", "category")


def entitlement_examples(a_facts: list[Any]) -> list[dict[str, Any]]:
    """Source-backed positive and invalid entitlement distinctions, each
    asserted against the candidate's own facts."""
    by = collections.defaultdict(list)
    for f in a_facts:
        by[(f["record_key"], f["fact"]["family"])].append(f["fact"])

    def one(record: str, family: str) -> dict[str, Any]:
        (fact,) = by[(record, family)]
        return fact

    rows = []

    def check(claim: str, ok: bool, _: bool) -> None:
        assert ok, claim
        rows.append({"source_rule_assertion": claim,
                     "asserted_against": "the candidate's own typed facts"})

    bmc = one("classes.barbarian.as_a_multiclass_character", "multiclass_proficiency_grant")
    check("Barbarian as a multiclass entry grants Martial weapons and Shields",
          bmc["weapons"]["categories"] == ["martial"] and bmc["armor_training"]["shields"],
          True)
    check("Barbarian as a multiclass entry grants no saving throws or Simple weapons",
          bmc["saving_throws"] == [] and "simple" not in bmc["weapons"]["categories"], False)
    monk = one("classes.monk", "weapon_proficiency_grant")
    check("Monk (level 1) is proficient with Martial weapons only if they have the Light "
          "property", monk["qualified"] == [{"category": "martial",
                                             "with_any_property": ["light"]}], True)
    check("Monk (level 1) Martial proficiency with a Heavy-only weapon is not granted",
          "martial" not in monk["categories"], False)
    check("Wizard has no Expertise grant (only Scholar's one listed skill)",
          [x["count_per_gain"] for x in by[("classes.wizard.scholar", "expertise_choice")]]
          == [1] and not by[("classes.wizard", "expertise_choice")], False)
    bwm = one("classes.barbarian.weapon_mastery", "weapon_mastery_choice")
    check("Barbarian Weapon Mastery counts only Melee weapons", bwm.get("melee_only") is True,
          False)
    check("Barbarian Weapon Mastery is 2 kinds at level 3 and 4 at level 10",
          bwm["count_by_level"]["3"] == 2 and bwm["count_by_level"]["10"] == 4, True)
    pwm = one("classes.paladin.weapon_mastery", "weapon_mastery_choice")
    check("Paladin Weapon Mastery requires proficiency with the weapon",
          pwm["requires_weapon_proficiency"] is True, True)
    sol = one("character_origins.soldier", "tool_proficiency_choice")
    check("Soldier chooses exactly one kind of Gaming Set", sol["count"] == 1
          and sol["from"] == {"tool_variants_of": _tool("gaming_set")}, True)
    mono = one("classes.monk.disciplined_survivor", "saving_throw_proficiency_grant")
    check("All six saving throws only through Disciplined Survivor (level 14)",
          len(mono["abilities"]) == 6 and mono["gain_levels"]["entitlement_key"]
          == "classes.monk.disciplined_survivor", True)
    lore = one("classes.bard.college_of_lore.bonus_proficiencies", "skill_proficiency_choice")
    check("College of Lore's three skills need the College of Lore subclass at Bard level 3",
          lore["eligibility"]["minimum_class_level"] == 3, True)
    asi = one("feats.grappler", "feat_prerequisite")
    check("Grappler's +1 needs level 4 and Strength or Dexterity 13",
          asi["minimum_character_level"] == 4
          and asi["minimum_ability_score"]["score"] == 13, False)
    return rows


def regressions(creature_records: list[Any], a_facts: list[Any], c_facts: list[Any]) -> None:
    """Cited examples from the C2 and C3 reviews (illustrations; the general
    invariants are the completeness evidence)."""
    by = {r["record_key"]: r for r in creature_records}

    def entry(rk: str, name: str) -> dict[str, Any]:
        return next(e for e in by[rk]["entries"] if e["name"] == name)

    # F1: timing ownership
    for rk, name in (("monsters.cloud_giant.cloud_giant", "Thundercloud"),
                     ("monsters.hill_giant.hill_giant", "Trash Lob"),
                     ("animals.giant_vulture", "Gouge")):
        d = entry(rk, name)["attack"]["hit_effect"]["duration"]
        assert d == {"until": "end_of_turn", "turn_of": "target", "turn": "next"}, (name, d)
    spittle = entry("monsters.guardian_naga.guardian_naga", "Poisonous Spittle")["save"]
    assert spittle["failure_effect"]["duration"]["turn_of"] == "source", spittle
    # F2: visibility predicates
    for rk, name in (("monsters.guardian_naga.guardian_naga", "Poisonous Spittle"),
                     ("monsters.satyr.satyr", "Mockery"),
                     ("animals.constrictor_snake", "Constrict")):
        e = entry(rk, name)
        assert e["save"]["targets"]["requires_source_sees_target"], name
        assert not e["executable_once_accepted"], name
    # F3: complete Multiattack alternatives and replacements
    naga = entry("monsters.guardian_naga.guardian_naga", "Multiattack")["multiattack"]
    assert naga["replacements"][0]["replaces"] == "any", naga
    turtle = entry("monsters.dragon_turtle.dragon_turtle", "Multiattack")["multiattack"]
    assert turtle["replacements"][0]["with_one_of"] == ["Tail"], turtle
    barbed = entry("monsters.barbed_devil.barbed_devil", "Multiattack")["multiattack"]
    assert len(barbed["alternatives"]) == 2 and not barbed["residue"], barbed
    brass = entry("monsters.brass_dragons.young_brass_dragon", "Multiattack")
    assert not any(s["executable_once_accepted"] for s in brass["selections"]
                   if "Sleep Breath" in s["selection"]), brass
    black = entry("monsters.black_dragons.adult_black_dragon", "Multiattack")
    base = [s for s in black["selections"] if "replacement" not in s["selection"]]
    assert base and not black["multiattack"]["residue"], black
    # F4: indirect contributors
    stalker = entry("monsters.invisible_stalker.invisible_stalker", "Wind Swipe")
    assert stalker["blocked_by"] and not stalker["executable_once_accepted"], stalker
    assert by["monsters.invisible_stalker.invisible_stalker"]["target_side"][
        "rolls_against_blocked_by"]
    # F5: fixed facts alongside parameters; assessed entries anchored
    assert "poison" in by["magic_items.mysterious_deck.avatar_of_death"]["profile"]["immunity"]
    assert "charmed" in by["spells.animate_objects.animated_object"]["profile"][
        "condition_immunity"]
    for rk in ("spells.animate_objects.animated_object", "spells.giant_insect.giant_insect",
               "spells.summon_dragon.draconic_spirit"):
        assert by[rk]["entries"] and all(e["component_key"] for e in by[rk]["entries"]), rk
        assert len(by[rk]["profile"]["abilities"]) == 6, rk
    # F6: approved bounded shapes not excluded by the parser
    for rk in ("monsters.ghouls.ghast", "monsters.ghouls.ghoul"):
        if rk in by:
            assert entry(rk, "Claw")["attack"]["hit_effect"]["rider_save"], rk
    glare = entry("spells.find_steed.otherworldly_steed", "Fell Glare")
    assert glare["kind"] == "save_effect" and any("missing runtime input" in r
                                                   for r in glare["reasons"])
    # C3 review 1: fixed values and formulas
    avatar = by["magic_items.mysterious_deck.avatar_of_death"]
    assert avatar["defense"]["armor_class"] == 20 and avatar["defense"]["hit_points"]
    assert by["spells.animate_objects.animated_object"]["defense"]["armor_class"] == 15
    scythe = entry("magic_items.mysterious_deck.avatar_of_death", "Reaping Scythe")
    assert scythe["classification"] == "supported" or not any(
        "formula" in x for x in scythe["reasons"]), scythe
    jab = entry("spells.giant_insect.giant_insect", "Poison Jab")["attack"]
    assert jab["hit_damage"][0]["addends"] == [{"input": "spell_level"}], jab
    web = entry("spells.giant_insect.giant_insect", "Web Bolt")["attack"]["hit_effect"]
    assert web["effect"]["family"] == "speed_modification", web
    assert glare["save"]["failure_effect"]["duration"]["turn_of"] == "caster", glare
    assert glare["save"]["dc"]["formula_ref"] == "spells.saving_throws/spell_save_dc"
    # C3 review 2: dimensions and target syntax
    storm = entry("monsters.storm_giant.storm_giant", "Lightning Storm")["save"]["targets"]
    assert storm["area"]["height_ft"] == 40, storm
    bash = entry("monsters.gladiator.gladiator", "Shield Bash")["save"]["targets"]
    assert bash["requires_source_sees_target"] and bash["within_ft"] == 5, bash
    # C3 review 3: exact selections
    dryad = entry("monsters.dryad.dryad", "Multiattack")["selections"]
    assert all(not (s["executable_once_accepted"] and s.get("spellcasting")) for s in dryad)
    assert [s for s in dryad if "optional" in s["selection"]], dryad
    glab = entry("monsters.glabrezu.glabrezu", "Multiattack")["selections"]
    assert {"Pummel"} in [set(s["uses"]) for s in glab], glab
    kraken = entry("monsters.kraken.kraken", "Multiattack")["selections"]
    assert len([s for s in kraken if "replacement" not in s["selection"]]) == 3, kraken
    # C3 review 4: applicability by subject/trigger/context
    spirit = by["spells.summon_dragon.draconic_spirit"]
    shared = entry("spells.summon_dragon.draconic_spirit", "Shared Resistances")
    assert shared["subject"] == "caster" and not shared["affects"], shared
    assert all("Shared Resistances" not in e.get("blocked_by", []) for e in spirit["entries"])
    steed = by["spells.find_steed.otherworldly_steed"]
    assert all("Healing Touch" not in e.get("blocked_by", []) for e in steed["entries"])
    for rk, name in (("monsters.black_pudding.black_pudding", "Spider Climb"),
                     ("monsters.white_dragons.adult_white_dragon", "Ice Walk")):
        if rk in by:
            e = entry(rk, name)
            assert e["kind"] == "contributor" and e["contributor"]["family"] == \
                "check_requirement_removal", e
    # C3 review 5: source vs capability
    ammo = next(f["fact"] for f in a_facts if f["fact"]["family"] == "ammunition_expenditure")
    assert ammo["loading_requires_free_hand"] and ammo["recovery"]["minutes"] == 1, ammo
    vamp = by["monsters.vampires.vampire_familiar"]["proposed_relation"]
    assert not any("monsters.vampires.vampire)" in v for v in vamp["validation"]), vamp
    # F7/F8: tool option fidelity and native option identity
    opts = [f["option"]["text"] for f in a_facts if f.get("option")]
    assert "Assemble a Tiny item composed of scrap, which falls apart in 1 minute" in opts
    assert all("option_key" not in f["fact"] for f in a_facts)
    # Conditional profiles are explicit, never empty
    for rk, fields in CONDITIONAL_FIELDS.items():
        for field in fields:
            assert any(isinstance(x, dict) for x in by[rk]["profile"][field]), (rk, field)


if __name__ == "__main__":
    main()
