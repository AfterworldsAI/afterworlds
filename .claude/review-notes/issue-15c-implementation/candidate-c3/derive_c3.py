"""CRD Issue 15c semantic candidate C3 — source-derived content (REVIEW MATERIAL).

Candidate only. Nothing here is accepted, recorded, minted, published or
activated, and nothing is written outside this directory. C3 supersedes the
unaccepted C2 (``../candidate-c2/``) after Codex's independent review
(``../codex-c2-review.md``); C1 and C2 are read, never written, and their
digests are checked. C3 owns its rule lists (``RULES``, ``STAT_BLOCK_RULES``)
and writes a per-rule disposition against C1/C2 (``rules-disposition.json``).
It imports only C1's weapon-row and armor-table *readers*, which the review
found correct.

Run from the repository root with the clone venv::

    venv/Scripts/python.exe .claude/review-notes/issue-15c-implementation/candidate-c3/derive_c3.py

Writes ``c3a.json``, ``c3b.json``, ``c3c.json``, ``concordance.json``,
``rules-disposition.json``, ``reuse-validation.json`` and ``transition.json``,
then asserts every defect the C2 review reported (and its cited siblings) is
corrected.
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
}
PROPOSED_SCHEMA = "5d-representation-schema-19 (proposed; not minted)"
STATUS = "CANDIDATE ONLY - not accepted, recorded, minted, published or activated"
#: Accepted families C3 claims to reuse unchanged; every such payload is run
#: through the accepted ``fact_from_payload`` (reuse-validation.json).
REUSED = {"damage", "ability_check", "condition_effect", "advantage", "effect_duration",
          "creature_defense"}


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
#:               Recharge).
TURN_OF = ("source", "target", "subject")


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
     {"family": "hit_point_bound", "minimum_current": 0,
      "applied": "adjudication_after_overflow"}),
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
      "requires": "ammunition_of_the_printed_type", "recovery": "excluded"}),
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
     {"family": "multiattack_rule", "action": "attack", "composition": "per_entry",
      "certification": "per_selected_composition"}),
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
            fact["also"] = "cannot cast spells (outside the roster)"
        out.append((record, component, file, quote, fact))
    return out


ARMOR_RULES = _armor_rules()


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
    for record, component, _, quote, fact in RULES + STAT_BLOCK_RULES + ARMOR_RULES:
        before = old.get((record, component, quote))
        if before is None:
            disposition = "new in C3"
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
    return "target" if phrase == "its" else "source"


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
_UNTIL = r"until the (start|end) of (its|the [\w' -]+?'s) next turn"


def _rider(rest: str) -> tuple[dict[str, Any] | None, str | None]:
    """Typed hit/failure riders; anything else is verbatim residue."""
    rest = rest.strip()
    if rest in ("", "."):
        return None, None
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


def _predicates(targets: str) -> tuple[dict[str, Any], str | None]:
    """Typed save-target predicates; unknown phrasing is kept verbatim."""
    t = targets
    out: dict[str, Any] = {}
    m = re.fullmatch(r"one (?:(\w+) or smaller )?creature(?: (?:the|that) [\w' -]+? can see)?"
                     r" within (\d+) feet(?: of (?:itself|it))?", t)
    if m:
        out = {"count": 1, "within_ft": int(m.group(2)),
               "maximum_size": m.group(1).lower() if m.group(1) else None,
               "requires_source_sees_target": " can see " in t}
        return out, None
    m = re.fullmatch(r"each creature in (?:a|an) (\d+)-foot(?P<radius>-radius)?"
                     r"(?:-long, (\d+)-foot-wide)?(?:, \d+-foot-high)? (\w+)(?P<rest>.*)", t)
    if m:
        out = {"area": m.group(4).lower(), "size_ft": int(m.group(1)),
               "radius": bool(m.group("radius")),
               "width_ft": int(m.group(3)) if m.group(3) else None}
        rest = m.group("rest").strip()
        if o := re.fullmatch(r"originating from (?:itself|the [\w' -]+)", rest):
            out["origin"] = "source"
            rest = ""
        elif o := re.fullmatch(r"centered on a point (?:the [\w' -]+? can see )?within (\d+) "
                               r"feet(?: of itself)?", rest):
            out["origin"] = {"point_within_ft": int(o.group(1))}
            out["requires_source_sees_point"] = " can see " in rest
            rest = ""
        return out, rest or None
    return {"text": t}, t


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
    return {"kind": slug(m.group("kind")),
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
    if "area" in tgt:
        reasons.append("area membership needs explicit position authority")
    if tgt_residue:
        reasons.append(f"target predicate not typed: {tgt_residue!r}")
    if tgt.get("requires_source_sees_target"):
        reasons.append("visibility prerequisite: the source must see the target; refuses "
                       "unless validated visibility state exists")
    if residue:
        reasons.append(f"failure rider not typed: {residue!r}")
    if effect and effect.get("duration"):
        reasons.append("timed effect needs explicit actor-turn authority")
    succ = (m.group("succ") or "").strip()
    if succ and succ not in ("Half damage.", "Half damage only."):
        reasons.append(f"success effect not typed: {succ!r}")
    if m.group("both"):
        reasons.append(f"failure-or-success effect not typed: {m.group('both')!r}")
    if m.group("dc") is None:
        reasons.append("missing input: the caster's spell save DC as recorded state")
    return {"save": m.group("ability").lower(),
            "dc": int(m.group("dc")) if m.group("dc") else {"equals": "caster_spell_save_dc"},
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

#: Reviewed by name (``review-allowlist`` in the README): effects on movement,
#: senses, breathing, communication, light, planes or carrying, which change no
#: roster roll, DC, damage or defense. Anything not listed and not typed blocks.
NO_ROSTER_EFFECT: dict[str, str] = {n: why for why, names in {
    "movement or position only": [
        "Abduct", "Aberrant Ground", "Agile", "Air Form", "Amorphous", "Aquatic Charge",
        "Bubble Dash", "Charge", "Compression", "Earth Glide", "Flyby", "Ice Walk",
        "Jumper", "Leap", "Prowl", "Reel", "Running Leap", "Spider Climb", "Standing Leap",
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
        entry: dict[str, Any] = {"section": section, "name": name}
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
                        reasons.append(f"missing input: attack count {p['count']} "
                                       "(summoner/spell level or recorded head count)")
                    if p.get("any_of") == []:
                        reasons.append("the counted attacks name no entry; the form "
                                       "choice decides them")
        elif "Spellcasting" in name or re.search(
                r"\bcasts? (?:the )?_|\bcasts [A-Z]|uses Spellcasting|_Wish_ spell", text):
            entry.update(kind="spellcasting", classification="deferred",
                         reasons=["general spell execution is a non-goal"])
            out.append(entry)
            continue
        elif section == "reaction":
            entry.update(kind="reaction", text=text, classification="deferred",
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
            reasons.append(f"uses {ref!r} under its own movement/timing terms")
        elif "Saving Throw:_" in text or "Attack Roll:" in text:
            entry.update(kind="special_effect", text=text)
            reasons.append("special effect outside the bounded attack/save shapes; named")
        elif name in TYPED_CONTRIBUTORS:
            typed, needs, contexts = TYPED_CONTRIBUTORS[name]
            entry.update(kind="contributor", text=text, contributor=typed,
                         affects=contexts)
            reasons.append(f"predicate typed; needs {needs}")
        elif granted := _granted_conditions(text):
            sem = {c: _condition_semantics(cond_index, c) for c in granted}
            affects = sorted({ctx for c in sem.values() for ctx, key in
                              (("own_attack", "own_rolls"), ("rolls_against", "rolls_against"))
                              if c[key]} or {"own_attack", "rolls_against", "target_save"})
            entry.update(kind="contributor", text=text, grants_conditions=sem,
                         affects=affects)
            reasons.append(f"grants {granted}: their typed facts apply to {affects}; "
                           "contextual components need validated state")
        elif name in NO_ROSTER_EFFECT:
            entry.update(kind="no_roster_effect", text=text, reviewed=NO_ROSTER_EFFECT[name])
        elif _KEYWORDS.search(text):
            entry.update(kind="contributor", text=text,
                         affects=["own_attack", "own_save_effect", "rolls_against",
                                  "target_save"])
            reasons.append("contributor named individually; blocks every roll it could "
                           "touch until its predicate is typed and accepted")
        else:
            entry.update(kind="unreviewed", text=text,
                         affects=["own_attack", "own_save_effect", "rolls_against",
                                  "target_save"])
            reasons.append("not on the reviewed no-effect allowlist; blocks conservatively")
        if caster:
            reasons.append("missing input: the caster's spell attack modifier / spell save DC "
                           "/ spell level as recorded state (no spell is cast)")
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


def _rollup(block: list[dict[str, Any]], profile_conditional: list[str]) -> dict[str, Any]:
    """Block-level certification.

    Own-entry blockers are every conditional/unreviewed contributor whose
    ``affects`` reaches that kind of roll; target-side blockers are what a
    roll *against* this creature or *its* save would also have to resolve.
    A Multiattack is certified per selectable composition.
    """
    def blockers(kind: str) -> list[str]:
        return sorted({e["name"] for e in block
                       if e["kind"] in ("contributor", "unreviewed")
                       and e["classification"] != "supported"
                       and kind in e.get("affects", [])})

    own_attack, own_save = blockers("own_attack"), blockers("own_save_effect")
    by_name = {e["name"]: e for e in block}
    for e in block:
        if e["kind"] == "attack":
            e["blocked_by"] = own_attack
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
            fixed = [p["attack"] for p in alt["parts"] if "attack" in p]
            choices = [p["any_of"] for p in alt["parts"] if "any_of" in p]
            refs = fixed + [r for c in choices for r in c]
            uses = [u for p in alt["parts"] for u in p.get("uses_one_of", [])]
            mandatory_uses = [u for p in alt["parts"] if not p.get("optional")
                              and not p.get("if_available") for u in p.get("uses_one_of", [])]
            # "N attacks using A or B in any combination" is certified per
            # selected option: the certified subset of each choice is
            # selectable even when a sibling option is conditional.
            certified = [[o for o in c if ok(o)] for c in choices]
            base_ok = bool(e["classification"] == "supported" and refs
                           and not ma["residue"] and alt["condition"] is None
                           and all(ok(r) for r in fixed) and all(certified)
                           and all(ok(u) for u in mandatory_uses))
            selections.append({"selection": f"alternative {i + 1}", "attacks": refs,
                               "uses": uses, "executable_once_accepted": base_ok,
                               "certified_options": certified,
                               "unresolved": [r for r in refs + uses if r not in by_name]})
            for j, rep in enumerate(ma["replacements"]):
                for opt in rep["with_one_of"]:
                    selections.append({
                        "selection": f"alternative {i + 1} with replacement {j + 1}: {opt}",
                        "executable_once_accepted": base_ok and ok(opt)
                        and not rep["if_available"],
                        "unresolved": [opt] if opt not in by_name else [],
                        "spellcasting": "Spellcasting" in opt})
        e["selections"] = selections
        e["executable_once_accepted"] = any(s["executable_once_accepted"] for s in selections
                                            if "replacement" not in s["selection"])
    return {"rolls_against_blocked_by": blockers("rolls_against"),
            "target_save_blocked_by": blockers("target_save"),
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


def _defense(b: dict[str, Any]) -> dict[str, Any]:
    ac = re.match(r"\*\*AC\*\* (\d+)(?: \*\*Initiative\*\*.*)?(?: <br>)?$", b["ac_line"].strip())
    hp_line = next((l for l in b["body"] if l.startswith("**HP**")), "")
    hp = re.match(r"\*\*HP\*\* (\d+) \((\d+)d(\d+)(?: ([+−-]) (\d+))?\)", hp_line)
    if ac and hp:
        mod = int(hp.group(5) or 0) * (-1 if hp.group(4) in ("−", "-") else 1)
        return {"family": "creature_defense", "armor_class": int(ac.group(1)),
                "hit_points": int(hp.group(1)),
                "hit_point_dice": {"count": int(hp.group(2)), "die": f"d{hp.group(3)}",
                                   "modifier": mod}}
    return {"parameterized": {"armor_class_printed": b["ac_line"],
                              "hit_points_printed": hp_line}}


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
VAMPIRE_MASTER_PROPOSAL = {
    "relation": "vampire_master",
    "owner": "the familiar's CreatureState (2b), additive optional field",
    "value": "one SubjectReference to a creature in the same story",
    "validation": ["the referenced creature exists in the same story",
                   "interpretation for Codex to confirm: its template is a vampire stat block (monsters.vampires.vampire)",
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
                "defense": _defense(b),
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
            if key in CONDITIONAL_FIELDS:
                record["classification"] = "conditional"
            if key == "monsters.vampires.vampire_familiar":
                record["proposed_relation"] = VAMPIRE_MASTER_PROPOSAL
            record["entries"] = entries(b["lines"], cond_index)
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
    reasons = ([] if m.group("bonus") == "Automatic hit"
               else ["missing input: caster spell attack modifier as recorded state"])
    if not terms or rest:
        reasons.append(f"parameterized hit: {m.group('hit')!r} (see record parameters)")
    return {"kind": slug(m.group("kind")),
            "attack_bonus": None,
            "automatic_hit": m.group("bonus") == "Automatic hit",
            "reach_ft": int(rm.group(1)) if rm and rm.group(1) else None,
            "normal_range_ft": int(rm.group(2)) if rm and rm.group(2) else None,
            "long_range_ft": None, "advantage_when": None,
            "hit_damage": terms, "hit_effect": None, "untyped": reasons}


# ===========================================================================


#: Digest of every (name, normalized text) instance read and accepted as having
#: no roster effect. A new or changed instance of an allowlisted name changes
#: it and fails the build until that text is read (see no-effect-review.json).
REVIEWED_NO_EFFECT_SHA256 = "d057cdbaf76a37efdd77b44c62580642f06370a8b39ef74023874dfd01691a00"  # pragma: allowlist secret


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
               + rule_facts(STAT_BLOCK_RULES, comps))
    for f in a_facts:
        if f["fact"]["family"] == "damage":  # weapon rows: accepted family, unchanged
            assert "option_key" not in f["fact"]
    assert not {(f["record_key"], f["component_key"]) for f in a_facts} - comps

    c_facts = c1c.armor() + rule_facts(ARMOR_RULES, comps)

    creature_records, census = creatures(rep)

    meta = {"status": STATUS, "proposed_schema": PROPOSED_SCHEMA,
            "anchored_oracle_sha256": ORACLE_SHA256, "supersedes": "15c-C2 (unaccepted)"}
    h_a = write("c3a.json", {"candidate_id": "15c-C3-A", **meta, "facts": a_facts})
    h_b = write("c3b.json", {"candidate_id": "15c-C3-B", **meta,
                             "creatures": creature_records, "census": census})
    h_c = write("c3c.json", {"candidate_id": "15c-C3-C", **meta, "facts": c_facts})
    reuse = reuse_validation(a_facts, creature_records, c_facts)
    write("reuse-validation.json", reuse)
    disposition = rules_disposition()
    write("rules-disposition.json", disposition)
    reviewed, reviewed_digest = no_effect_review(creature_records)
    write("no-effect-review.json", {"digest": reviewed_digest, "instances": reviewed})
    assert reviewed_digest == REVIEWED_NO_EFFECT_SHA256, (
        f"no-roster-effect instances changed ({reviewed_digest}); read no-effect-review.json "
        "and re-pin only after every instance is reviewed")
    trans = transition({
        "c3a.json": [f["record_key"] for f in a_facts],
        "c3b.json": [r["record_key"] for r in creature_records],
        "c3c.json": [f["record_key"] for f in c_facts]}, oracle)
    write("transition.json", trans)

    entries_all = [(r, e) for r in creature_records for e in r["entries"]]
    attack_lines = {f: sum("Attack Roll:" in l for l in lines(f))
                    for f in ("monsters-A-Z.md", "animals.md", "spells.md", "magic-items.md")}
    assessed_attacks = sum(1 for r, e in entries_all
                           if e["kind"] == "attack" and r["record_key"] in PARAMETERS)
    ma = [e for _, e in entries_all if e["kind"] == "multiattack"]
    concordance = {
        "hashes": {"c3a.json": h_a, "c3b.json": h_b, "c3c.json": h_c},
        "tools": tool_concord,
        "attack_roll_lines": {"by_file": attack_lines, "total": sum(attack_lines.values()),
                              "parsed_attacks": sum(1 for _, e in entries_all
                                                    if e["kind"] == "attack"),
                              "in_assessed_creatures": assessed_attacks},
        "creatures": {
            "records": census["creature_records"],
            "matched": census["creature_records"] - len(census["unmatched_records"]),
            "record_classification": dict(collections.Counter(
                r["classification"] for r in creature_records)),
            "entry_kinds": dict(collections.Counter(e["kind"] for _, e in entries_all)),
            "entry_classification": dict(collections.Counter(
                e["classification"] for _, e in entries_all)),
            "executable_once_accepted": dict(collections.Counter(
                e["kind"] for _, e in entries_all if e.get("executable_once_accepted"))),
            "multiattack_selections": {
                "total": sum(len(e["selections"]) for e in ma),
                "executable": sum(s["executable_once_accepted"] for e in ma
                                  for s in e["selections"]),
                "base_executable_with_unavailable_substitution": sum(
                    1 for e in ma if e["executable_once_accepted"] and any(
                        not s["executable_once_accepted"] for s in e["selections"]
                        if "replacement" in s["selection"]))},
            "creatures_with_target_side_blockers": sum(
                1 for r in creature_records if r["target_side"]["rolls_against_blocked_by"]),
            "unreviewed_entries": sorted({e["name"] for _, e in entries_all
                                          if e["kind"] == "unreviewed"}),
        },
        "reuse_validation": {k: reuse[k] for k in ("reused_payloads", "by_family")}
        | {"failures": len(reuse["failures"])},
        "transition": {k: trans[k] for k in ("batch_count", "batches")},
    }
    write("concordance.json", concordance)
    regressions(creature_records, a_facts, c_facts, reuse, attack_lines)
    for rel, digest in PRESERVED.items():
        assert sha((NOTES / rel).read_bytes()) == digest, f"preserved file changed: {rel}"
    print(json.dumps(concordance["hashes"], indent=1))
    print(json.dumps({k: v for k, v in concordance.items() if k not in ("tools", "hashes")},
                     indent=1)[:4000])


def regressions(creature_records: list[Any], a_facts: list[Any], c_facts: list[Any],
                reuse: dict[str, Any], attack_lines: dict[str, int]) -> None:
    """Fail if any defect Codex reported on C2 (or a cited sibling) returns."""
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
    assert glare["kind"] == "save_effect" and any("missing input" in r for r in glare["reasons"])
    # F7/F8: tool option fidelity and native option identity
    opts = [f["option"]["text"] for f in a_facts if f.get("option")]
    assert "Assemble a Tiny item composed of scrap, which falls apart in 1 minute" in opts
    assert all("option_key" not in f["fact"] for f in a_facts)
    assert not reuse["failures"], reuse["failures"][:3]
    # Concordance: all-source attack-roll lines
    total = sum(attack_lines.values())
    parsed = sum(1 for r in creature_records for e in r["entries"] if e["kind"] == "attack")
    assert total == 429 and parsed == total, (total, parsed)
    # Conditional profiles are explicit, never empty
    for rk, fields in CONDITIONAL_FIELDS.items():
        for field in fields:
            assert any(isinstance(x, dict) for x in by[rk]["profile"][field]), (rk, field)


if __name__ == "__main__":
    main()
