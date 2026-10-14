"""CRD Issue 15c semantic candidate C4 — source-derived content (REVIEW MATERIAL).

Candidate only. Nothing here is accepted, recorded, minted, published or
activated, and nothing is written outside this directory. C4 supersedes the
unaccepted final C3 (``../candidate-c3/``) after Codex's independent review
(``../codex-c3-review.md``). C1, C2 and C3 are read, never written; their
digests are checked before and after every run. ``derive_c4.py`` is a fork of
``derive_c3.py``; ``derive_c4.diff`` shows every change.

C4 applies the settled source/capability contract:

* **Source parts** (``c4a.json``, ``c4b.json``, ``c4c.json``) carry only
  source facts, formulas and participant predicates, which are what a native
  mint would contain.
* **Capability** (``capability.json``) carries everything about execution:
  classification, dependency kind (missing source authority, missing runtime
  input, missing state, unsupported mechanic), blockers, selection
  certification, execution exclusions and adapter procedures.

Run from the repository root with the clone venv::

    venv/Scripts/python.exe .claude/review-notes/issue-15c-implementation/candidate-c4/derive_c4.py
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
      "blocked_by": ["incapacitated"]}),
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


def grant_facts(comps: set[tuple[str, str]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []

    def add(record: str, component: str, file: str, quote: str, fact: dict[str, Any],
            line: int | None = None) -> None:
        """``line`` (1-based) pins provenance when the same quote recurs."""
        assert (record, component) in comps, (record, component)
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
                    "from": _ALL_SKILLS}
        else:
            m = re.fullmatch(r"Choose (\d+): (.+)", text)
            assert m, text
            fact = {"family": "skill_proficiency_choice", "count": int(m.group(1)),
                    "from": _skill_list(m.group(2))}
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
         "or_tools": True, "repeatable": True})
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
         "from": "classes.barbarian/core_traits"})
    add("classes.bard.college_of_lore.bonus_proficiencies", "bonus_proficiencies", CLASSES,
        "You gain proficiency with three skills of your choice.",
        {"family": "skill_proficiency_choice", "count": 3, "from": _ALL_SKILLS})
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
            disposition = "new in C4"
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
    residue = " ".join(w for w in words if not _FILLER.match(w)).strip()
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
    rm = re.fullmatch(r"(?:reach (\d+) ft\.?)?(?: or )?(?:range (\d+)(?:/(\d+))? ft)?", reach)
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
              "can't regain Hit Points or gain Temporary Hit Points. Only where character-"
              "style zero-HP treatment applies to the subject: the natural-20 Death Saving "
              "Throw and the Stable 1d4-hour 1 Hit Point regains do not happen, because an "
              "exception supersedes the general rule; the rest of the death-save rule is "
              "unchanged. The default monster death determination is unaffected"),
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
    "Undead Fortitude": ("self", ["zero_hp_outcome"], "unsupported: save to stay at 1 HP",
                         "DC 5 plus the damage taken"),
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
              "applies_when": {"zero_hp_treatment": "character_style"},
              "precedence": located(PTG, "When an exception and a general rule disagree, the "
                                         "exception wins.")},
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
    "Mimicry": "a check by observers (DC 14 Insight) outside the roster",
    "Transparent": "a check by observers (DC 15 Perception) outside the roster",
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


def entries(block_lines: list[str], cond_index: dict[str, Any]) -> list[dict[str, Any]]:
    section = "trait"
    raw = []
    for line in block_lines:
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
            u = _USAGE.match(name)
            usage = None
            if u:
                name, usage = u.group("base"), u.group("usage")
            raw.append((section, name, usage, text))
    names = {n for _, n, _, _ in raw}
    out = []
    for section, name, usage, text in raw:
        entry: dict[str, Any] = {"section": section, "name": name, "_text": text}
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
                        p["any_of"] = [n for s_, n, _, t in raw if s_ == "action"
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
                      "recorded_as": "ChoiceRecord on the creature (existing 2b contract)"},
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
        "predicate": {"condition": "charmed", "unless_source_is": "vampire_master"},
        "requires": "a validated vampire-master relation (proposed below; not inferred "
                    "from summoner/controller)",
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
    "validation": ["the referenced creature exists in the same story",
                   "the source leaves the master's identity otherwise unconstrained; "
                   "no template or type restriction is proposed",
                   "not inferred from summoner/controller"],
    "consumer": "only the Charmed-immunity determination on the familiar",
    "absent": "that one determination refuses as missing state; nothing else changes",
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
        blocks.append({"file": file, "line": i + 1, "heading": src[j].lstrip("#").strip(),
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
                "source": {"file": file, "line": b["line"], "heading": b["heading"]},
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
            record["entries"] = entries(b["lines"], cond_index)
            _apply_formulas(key, b["lines"], record["entries"])
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
            "anchored_oracle_sha256": ORACLE_SHA256, "supersedes": "15c-C3 (unaccepted)"}
    regressions(creature_records, a_facts, c_facts)
    source_records, capability = split_capability(creature_records)
    invariant_report = invariants(source_records, creature_records, a_facts, c_facts)
    h_a = write("c4a.json", {"candidate_id": "15c-C4-A", **meta, "facts": a_facts})
    h_b = write("c4b.json", {"candidate_id": "15c-C4-B", **meta,
                             "creatures": source_records, "census": census})
    h_c = write("c4c.json", {"candidate_id": "15c-C4-C", **meta, "facts": c_facts})
    capability["scope"] = CAPABILITY_SCOPE
    h_cap = write("capability.json", {"candidate_id": "15c-C4-capability", "status": STATUS,
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
        "c4a.json": [f["record_key"] for f in a_facts],
        "c4b.json": [r["record_key"] for r in creature_records],
        "c4c.json": [f["record_key"] for f in c_facts]}, oracle)
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
        "hashes": {"c4a.json": h_a, "c4b.json": h_b, "c4c.json": h_c, "capability.json": h_cap},
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
                "rule is kept intact in c4a"},
        {"identity": "equipment.armor/light_medium_or_heavy_armor", "part": "cannot_cast_spells",
         "why": "spellcasting is a non-goal; the source rule is kept intact in c4c"},
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
                                  "missing source authority")),
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
                    "selections", "reviewed", "applies", "applicability", "affects")


def split_capability(records: list[Any]) -> tuple[list[Any], dict[str, Any]]:
    source, entries_cap, records_cap = [], {}, {}
    for r in records:
        rec = {k: v for k, v in r.items()
               if k not in ("classification", "target_side", "proposed_relation", "entries")}
        rec["entries"] = []
        for i, e in enumerate(r["entries"]):
            src = {k: v for k, v in e.items() if k not in _CAPABILITY_KEYS and k != "_text"}
            if src["kind"] in ("no_roster_effect", "unreviewed"):
                # Whether a trait touches admitted operations is a capability
                # judgment; as source it is a prose trait.
                src["kind"] = "prose_trait"
            rec["entries"].append(src)
            entries_cap[f"{r['record_key']}#{i}:{e['name']}"] = {
                "classification": e["classification"],
                "dependencies": [_dependency(x, e["classification"] == "deferred")
                                 for x in e.get("reasons", [])],
                **{k: e[k] for k in ("blocked_by", "applies", "executable_once_accepted",
                                     "selections", "reviewed", "applicability", "affects")
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


def invariants(source_records: list[Any], records: list[Any], a_facts: list[Any],
               c_facts: list[Any]) -> dict[str, Any]:
    """General completeness checks (not example assertions)."""
    report: dict[str, Any] = {}
    # 1. Source parts carry no scope/capability vocabulary (prose fields aside).
    prose = ("text", "quote", "source", "formula_source", "_text", "untyped_clauses",
             "trigger")
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
                {k: v for k, v in se.items() if k != "name"}, ensure_ascii=False)))
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
               for c in e["save"]["untyped_clauses"] if c["part"] == "targets"]
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
