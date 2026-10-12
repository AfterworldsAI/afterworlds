"""CRD Issue 15c semantic candidate C1 — source-derived content (REVIEW MATERIAL).

Candidate only. Nothing here is accepted, recorded, published or activated, and
nothing is written outside this directory. The accepted G1 oracle is read only
(its SHA-256 is checked) to anchor every proposed fact to an existing accepted
record/component identity.

* Weapon rows (38) and record-backed tools (13) are derived mechanically from
  the pinned Markdown tables/entries; no artifact count is consulted.
* Rule facts are hand-authored. Each carries an exact ``quote`` that must occur
  on its cited Markdown line; the script refuses to emit if any quote is absent.

Usage (repository root, clone venv)::

    venv/Scripts/python.exe .claude/review-notes/issue-15c-implementation/candidate/derive_candidate.py

Writes ``candidate-c1.json`` beside this file and prints its content SHA-256.
"""

from __future__ import annotations

import hashlib
import html
import json
import re
from pathlib import Path
from typing import Any

REPO = Path.cwd()
SRC = REPO / "docs/sources/community/dnd-5e-srd-markdown"
HERE = Path(__file__).parent
ORACLE = (
    REPO
    / "src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-8781d4e0-a3b-g1.json"
)
ORACLE_SHA256 = "2ccbaeba6de75d9787fbdd407e42dc2425fa20d4d26bcc298b681b550bd11258"  # pragma: allowlist secret
CANDIDATE_ID = "15c-C1"
PROPOSED_SCHEMA = "5d-representation-schema-19 (proposed; not minted)"


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower().replace("'", "")).strip("_")


def lines(name: str) -> list[str]:
    return (SRC / name).read_text("utf-8").splitlines()


def locate(name: str, needle: str, start: int = 0) -> int:
    for i, line in enumerate(lines(name)[start:], start + 1):
        if needle in line:
            return i
    raise SystemExit(f"{name}: {needle!r} not found")


# ---------------------------------------------------------------------------
# Weapons table (equipment.md)
# ---------------------------------------------------------------------------

_DICE = re.compile(r"^(\d+)d(\d+) (\w+)$")
_FLAT = re.compile(r"^(\d+) (\w+)$")
_PROP = re.compile(r"^([A-Za-z\- ]+?)(?: \((.*)\))?$")


def _property(text: str) -> dict[str, Any]:
    m = _PROP.match(text.strip())
    assert m, text
    name, arg = slug(m.group(1)), m.group(2)
    fact: dict[str, Any] = {"family": "weapon_property", "property": name}
    if arg is None:
        return fact
    if name == "versatile":
        count, die = arg.split("d")
        fact["two_handed_dice"] = {"count": int(count), "die": f"d{die}"}
        return fact
    if name == "two_handed" and arg == "unless mounted":
        # Lance: the printed exception needs mount state 15c does not record,
        # so it is carried as a qualifier and executed as a refusal.
        fact["except_when"] = "mounted"
        return fact
    rng = re.match(r"Range (\d+)/(\d+)(?:; (.+))?$", arg)
    assert rng and name in ("ammunition", "thrown"), (name, arg)
    fact["normal_range_ft"] = int(rng.group(1))
    fact["long_range_ft"] = int(rng.group(2))
    if rng.group(3):
        fact["ammunition"] = slug(rng.group(3))
    return fact


def weapons() -> list[dict[str, Any]]:
    text = (SRC / "equipment.md").read_text("utf-8")
    start = text.index("**Weapons**")
    body = text[text.index("<table>", start) : text.index("</table>", start)]
    offset = text[: text.index("<table>", start)].count("\n") + 1
    out: list[dict[str, Any]] = []
    range_class = ""
    for m in re.finditer(r"<tr>(.*?)</tr>", body, re.S):
        tr = m.group(1)
        line = offset + body[: m.start()].count("\n") + 1
        if "<th colspan" in tr:
            group = html.unescape(re.sub(r"<[^>]+>", "", tr)).strip()
            range_class = "melee" if "Melee" in group else "ranged"
            continue
        cells = [html.unescape(c).strip() for c in re.findall(r"<td>(.*?)</td>", tr)]
        if not cells:
            continue
        name, damage, props = cells[0], cells[1], cells[2]
        key = slug(name)
        row_line = locate("equipment.md", f"<td>{name}</td>", line - 1)
        where = {"file": "equipment.md", "line": row_line, "quote": f"<td>{name}</td>"}
        dm = _DICE.match(damage)
        fm = _FLAT.match(damage)
        if dm:
            dmg = {
                "dice": {
                    "count": int(dm.group(1)),
                    "die": f"d{dm.group(2)}",
                    "modifier": 0,
                },
                "flat_amount": None,
                "damage_type": dm.group(3).lower(),
            }
        else:
            assert fm, damage
            dmg = {
                "dice": None,
                "flat_amount": int(fm.group(1)),
                "damage_type": fm.group(2).lower(),
            }
        facts = [
            {"family": "weapon_range_class", "range_class": range_class},
            # Reuses the accepted ``damage`` family (schema 18), unchanged.
            {"family": "damage", **dmg, "stated_average": None},
        ]
        if props != "—":
            facts += [_property(p) for p in _split_props(props)]
        for f in facts:
            out.append(
                {
                    "record_key": f"equipment.weapons.{key}",
                    "component_key": key,
                    "fact": f,
                    "source": where,
                }
            )
    return out


def _split_props(props: str) -> list[str]:
    parts, depth, cur = [], 0, ""
    for ch in props:
        depth += ch == "("
        depth -= ch == ")"
        if ch == "," and depth == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    return [p.strip() for p in [*parts, cur] if p.strip()]


# ---------------------------------------------------------------------------
# Record-backed tools (equipment.md "Tools")
# ---------------------------------------------------------------------------


def tools(record_keys: set[str]) -> list[dict[str, Any]]:
    src = lines("equipment.md")
    out: list[dict[str, Any]] = []
    for i, line in enumerate(src):
        m = re.match(r"^\*\*(.+?) \((?:[\d,]+ [GS]P|Varies)\)\*\*$", line)
        if not m:
            continue
        key = f"equipment.tools.{slug(m.group(1))}"
        if key not in record_keys:
            continue  # component-only identities are not tool-grant identities
        j = i + 1 + (src[i + 1] == "")
        ab = re.match(r"^\*\*Ability:\*\* (\w+)", src[j])
        assert ab, src[j]
        where = {"file": "equipment.md", "line": j + 1, "row": m.group(1)}
        out.append(
            {
                "record_key": key,
                "component_key": slug(m.group(1)),
                "fact": {"family": "tool_ability", "ability": ab.group(1).lower()},
                "source": where,
            }
        )
        util = src[j + 1]
        assert util.startswith("**Utilize:**"), util
        for opt, dc in re.findall(
            r"([^,]+?) \(DC (\d+)\)", util.removeprefix("**Utilize:** ")
        ):
            opt = re.sub(r"^(or )", "", opt.strip())
            out.append(
                {
                    "record_key": key,
                    "component_key": slug(m.group(1)),
                    "option_key": slug(opt),
                    # Reuses the accepted ``ability_check`` family, one per
                    # Utilize option (a component option to be minted).
                    "fact": {
                        "family": "ability_check",
                        "ability": ab.group(1).lower(),
                        "context": "ability_check",
                        "dc_kind": "fixed",
                        "dc_value": int(dc),
                    },
                    "source": {
                        "file": "equipment.md",
                        "line": j + 2,
                        "row": m.group(1),
                    },
                }
            )
    return out


# ---------------------------------------------------------------------------
# Hand-authored rule facts: (record, component, file, quote, fact)
# ---------------------------------------------------------------------------

PTG, EQ, GL = "playing-the-game.md", "equipment.md", "rules-glossary.md"
_TURN_START = {"until": "start_of_turn", "whose": "attacker", "turn": "next"}

RULES: list[tuple[str, str, str, str, dict[str, Any]]] = [
    # -- D20 tests -----------------------------------------------------------
    *[
        (
            "play.d20_tests",
            "typical_dcs",
            PTG,
            f"<td>{label}</td>",
            {"family": "difficulty_band", "difficulty": slug(label), "dc": dc},
        )
        for label, dc in (
            ("Very easy", 5),
            ("Easy", 10),
            ("Medium", 15),
            ("Hard", 20),
            ("Very hard", 25),
            ("Nearly impossible", 30),
        )
    ],
    (
        "play.d20_tests",
        "attack_ability_modifier",
        PTG,
        "Melee attack with a weapon or an Unarmed Strike",
        {
            "family": "attack_roll_ability",
            "range_class": "melee",
            "ability": "strength",
        },
    ),
    (
        "play.d20_tests",
        "attack_ability_modifier",
        PTG,
        "Ranged attack with a weapon",
        {
            "family": "attack_roll_ability",
            "range_class": "ranged",
            "ability": "dexterity",
        },
    ),
    (
        "play.d20_tests",
        "natural_20",
        PTG,
        "the attack hits regardless of any modifiers",
        {
            "family": "natural_roll_outcome",
            "context": "attack_roll",
            "face": 20,
            "outcome": "hit",
            "critical_hit": True,
        },
    ),
    (
        "play.d20_tests",
        "natural_1",
        PTG,
        "the attack misses regardless of any modifiers",
        {
            "family": "natural_roll_outcome",
            "context": "attack_roll",
            "face": 1,
            "outcome": "miss",
            "critical_hit": False,
        },
    ),
    (
        "play.combat",
        "initiative_roll",
        PTG,
        "they make a Dexterity check",
        {
            "family": "initiative_roll",
            "ability": "dexterity",
            "context": "ability_check",
        },
    ),
    # -- Damage --------------------------------------------------------------
    (
        "play.damage_and_healing",
        "damage_rolls",
        PTG,
        "you add your ability modifier—the same modifier used for the attack roll",
        {
            "family": "damage_roll_rule",
            "adds_attack_ability_modifier": True,
            "fixed_amount_adds_modifier": False,
            "minimum_damage": 0,
        },
    ),
    (
        "play.damage_and_healing",
        "critical_hits",
        PTG,
        "Roll the attack's damage dice twice",
        {"family": "critical_damage", "damage_dice_multiplier": 2},
    ),
    (
        "play.damage_and_healing",
        "temporary_hit_points",
        PTG,
        "those points are lost first, and any leftover damage carries over",
        {"family": "temporary_hit_point_absorption", "absorbed_first": True},
    ),
    # -- Zero HP lifecycle ---------------------------------------------------
    (
        "play.damage_and_healing",
        "hit_points",
        PTG,
        "which is the lowest Hit Points can go",
        # Gameplay bound applied by adjudication AFTER damage overflow is
        # computed (massive damage needs it); never a persistence floor (ADR-0003).
        {
            "family": "hit_point_bound",
            "minimum_current": 0,
            "applied": "adjudication_after_overflow",
        },
    ),
    (
        "play.damage_and_healing",
        "monster_death",
        PTG,
        "A monster dies the instant it drops to 0 Hit Points",
        {
            "family": "zero_hit_point_outcome",
            "subject": "monster",
            "outcome": "dies",
            "gamemaster_exception": "treat_as_character",
        },
    ),
    (
        "play.damage_and_healing",
        "hit_point_maximum_of_0",
        PTG,
        "A creature dies if its Hit Point maximum reaches 0",
        {
            "family": "zero_hit_point_outcome",
            "subject": "any",
            "trigger": "hit_point_maximum_zero",
            "outcome": "dies",
        },
    ),
    (
        "play.damage_and_healing",
        "massive_damage",
        PTG,
        "the character dies if the remainder equals or exceeds their Hit Point maximum",
        {
            "family": "massive_damage",
            "subject": "character",
            "dies_when_remainder_at_least": "hit_point_maximum",
        },
    ),
    (
        "play.damage_and_healing",
        "falling_unconscious",
        PTG,
        "you now face making Death Saving Throws",
        {
            "family": "zero_hit_point_outcome",
            "subject": "character",
            "outcome": "unconscious_and_dying",
        },
    ),
    (
        "play.damage_and_healing",
        "death_saving_throws",
        PTG,
        "Roll 1d20. If the roll is 10 or higher, you succeed.",
        {
            "family": "death_saving_throw",
            "die": "d20",
            "success_minimum": 10,
            "successes_to_stable": 3,
            "failures_to_die": 3,
            "timing": {"when": "start_of_turn", "whose": "subject", "at_hit_points": 0},
            "ability": None,
            "reset_on": ["regains_hit_points", "becomes_stable"],
        },
    ),
    (
        "play.damage_and_healing",
        "death_saving_throws",
        PTG,
        "When you roll a 1 on the d20 for a Death Saving Throw, you suffer two failures",
        {"family": "death_save_natural_roll", "face": 1, "failures": 2},
    ),
    (
        "play.damage_and_healing",
        "death_saving_throws",
        PTG,
        "If you roll a 20 on the d20, you regain 1 Hit Point",
        {"family": "death_save_natural_roll", "face": 20, "regain_hit_points": 1},
    ),
    (
        "play.damage_and_healing",
        "damage_at_0_hit_points",
        PTG,
        "If the damage is from a Critical Hit, you suffer two failures instead",
        {
            "family": "damage_at_zero_hit_points",
            "failures": 1,
            "critical_hit_failures": 2,
            "dies_when_damage_at_least": "hit_point_maximum",
        },
    ),
    (
        "play.damage_and_healing",
        "stabilizing",
        PTG,
        "You can take the Help action to try to stabilize a creature with 0 Hit Points",
        {"family": "stabilization", "action": "help", "on_success": "stable"},
    ),
    (
        "play.damage_and_healing",
        "stable",
        PTG,
        "A Stable creature that isn't healed regains 1 Hit Point after 1d4 hours",
        {
            "family": "stable_state",
            "makes_death_saves": False,
            "remains_unconscious": True,
            "damage_ends_stable": True,
            "recovery": {
                "dice": {"count": 1, "die": "d4"},
                "unit": "hour",
                "regain_hit_points": 1,
                "unless": "healed",
            },
        },
    ),
    (
        "play.damage_and_healing",
        "knocking_out",
        PTG,
        "you can instead reduce the creature to 1 Hit Point",
        {
            "family": "knockout_alternative",
            "attack": "melee",
            "set_hit_points": 1,
            "condition": "unconscious",
            "ends_after": "short_rest",
            "ends_early_on": ["regains_hit_points", "first_aid_success"],
        },
    ),
    (
        "glossary.short_rest",
        "short_rest",
        GL,
        "A Short Rest is a 1-hour period",
        {"family": "rest_duration", "rest": "short_rest", "hours": 1},
    ),
    # -- Weapon properties ---------------------------------------------------
    (
        "equipment.weapons.finesse",
        "finesse",
        EQ,
        "use your choice of your Strength or Dexterity",
        {
            "family": "attack_ability_option",
            "abilities": ["strength", "dexterity"],
            "same_for_damage": True,
        },
    ),
    (
        "equipment.weapons.heavy",
        "heavy",
        EQ,
        "your Strength score isn't at least 13",
        {
            "family": "ability_score_requirement",
            "range_class": "melee",
            "ability": "strength",
            "minimum": 13,
            "unmet": "attack_disadvantage",
        },
    ),
    (
        "equipment.weapons.heavy",
        "heavy",
        EQ,
        "your Dexterity score isn't at least 13",
        {
            "family": "ability_score_requirement",
            "range_class": "ranged",
            "ability": "dexterity",
            "minimum": 13,
            "unmet": "attack_disadvantage",
        },
    ),
    (
        "equipment.weapons.light",
        "light",
        EQ,
        "you can make one extra attack as a Bonus Action",
        {
            "family": "light_extra_attack",
            "cost": "bonus_action",
            "requires": "different_light_weapon",
            "limit": "once_per_turn",
            "ability_modifier_damage": "only_if_negative",
        },
    ),
    (
        "equipment.weapons.loading",
        "loading",
        EQ,
        "You can fire only one piece of ammunition",
        {"family": "ammunition_per_activation", "maximum": 1},
    ),
    (
        "equipment.weapons.range",
        "range",
        EQ,
        "you have Disadvantage on the attack roll",
        {
            "family": "range_band_rule",
            "beyond_normal": "attack_disadvantage",
            "beyond_long": "cannot_attack",
        },
    ),
    (
        "equipment.weapons.reach",
        "reach",
        EQ,
        "adds 5 feet to your reach",
        {"family": "reach_extension", "feet": 5},
    ),
    (
        "equipment.weapons.thrown",
        "thrown",
        EQ,
        "you can throw the weapon to make a ranged attack",
        {
            "family": "thrown_attack",
            "attack": "ranged",
            "melee_weapon_ability": "as_melee_attack",
        },
    ),
    (
        "equipment.weapons.two_handed",
        "two_handed",
        EQ,
        "requires two hands",
        {"family": "hands_required", "hands": 2},
    ),
    (
        "equipment.weapons.versatile",
        "versatile",
        EQ,
        "when used with two hands to make a melee attack",
        {"family": "versatile_damage", "hands": 2, "attack": "melee"},
    ),
    (
        "equipment.weapons.ammunition",
        "ammunition",
        EQ,
        "Each attack expends one piece of ammunition",
        {"family": "ammunition_expenditure", "per_attack": 1},
    ),
    # -- Masteries -----------------------------------------------------------
    (
        "equipment.weapons.cleave",
        "cleave",
        EQ,
        "against a second creature within 5 feet of the first",
        {
            "family": "mastery_effect",
            "mastery": "cleave",
            "trigger": "hit_melee_attack",
            "second_target_within_ft": 5,
            "second_target_within_reach": True,
            "ability_modifier_damage": "only_if_negative",
            "limit": "once_per_turn",
        },
    ),
    (
        "equipment.weapons.graze",
        "graze",
        EQ,
        "equal to the ability modifier you used to make the attack roll",
        {
            "family": "mastery_effect",
            "mastery": "graze",
            "trigger": "miss",
            "damage": "attack_ability_modifier",
            "damage_type": "weapon",
        },
    ),
    (
        "equipment.weapons.nick",
        "nick",
        EQ,
        "as part of the Attack action instead of as a Bonus Action",
        {
            "family": "mastery_effect",
            "mastery": "nick",
            "trigger": "light_extra_attack",
            "cost": "attack_action",
            "limit": "once_per_turn",
        },
    ),
    (
        "equipment.weapons.push",
        "push",
        EQ,
        "push the creature up to 10 feet straight away",
        {
            "family": "mastery_effect",
            "mastery": "push",
            "trigger": "hit",
            "distance_ft": 10,
            "direction": "away",
            "maximum_size": "large",
        },
    ),
    (
        "equipment.weapons.sap",
        "sap",
        EQ,
        "Disadvantage on its next attack roll before the start of your next turn",
        {
            "family": "mastery_effect",
            "mastery": "sap",
            "trigger": "hit",
            "effects": [
                {
                    "family": "advantage",
                    "state": "disadvantage",
                    "roll": {
                        "actor": "target",
                        "context": "attack_roll",
                        "ability": None,
                    },
                    "uses": "next_one",
                },
                {"family": "effect_duration", **_TURN_START},
            ],
        },
    ),
    (
        "equipment.weapons.slow",
        "slow",
        EQ,
        "reduce its Speed by 10 feet until the start of your next turn",
        {
            "family": "mastery_effect",
            "mastery": "slow",
            "trigger": "hit_and_damage",
            "speed_reduction_ft": 10,
            "maximum_reduction_ft": 10,
            "duration": _TURN_START,
        },
    ),
    (
        "equipment.weapons.topple",
        "topple",
        EQ,
        "DC 8 plus the ability modifier used to make the attack roll",
        {
            "family": "mastery_effect",
            "mastery": "topple",
            "trigger": "hit",
            "save": "constitution",
            "dc": {"base": 8, "plus": ["attack_ability_modifier", "proficiency_bonus"]},
            "on_failure": [
                {
                    "family": "condition_effect",
                    "condition": "prone",
                    "effect": "applies",
                }
            ],
        },
    ),
    (
        "equipment.weapons.vex",
        "vex",
        EQ,
        "Advantage on your next attack roll against that creature",
        {
            "family": "mastery_effect",
            "mastery": "vex",
            "trigger": "hit_and_damage",
            "effects": [
                {
                    "family": "advantage",
                    "state": "advantage",
                    "roll": {
                        "actor": "attacker",
                        "context": "attack_roll",
                        "ability": None,
                        "against": "target",
                    },
                    "uses": "next_one",
                },
                {
                    "family": "effect_duration",
                    "until": "end_of_turn",
                    "whose": "attacker",
                    "turn": "next",
                },
            ],
        },
    ),
]


def rule_facts() -> list[dict[str, Any]]:
    out = []
    for record, component, file, quote, fact in RULES:
        line = locate(file, quote)
        out.append(
            {
                "record_key": record,
                "component_key": component,
                "fact": fact,
                "source": {"file": file, "line": line, "quote": quote},
            }
        )
    return out


def main() -> None:
    raw = ORACLE.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == ORACLE_SHA256, "accepted oracle changed"
    oracle = json.loads(raw)
    comps = {
        (c["record_key"], c["semantic_key"])
        for c in oracle["representation"]["components"]
    }
    records = {r["semantic_key"] for r in oracle["representation"]["records"]}
    facts = weapons() + tools(records) + rule_facts()
    missing = sorted({(f["record_key"], f["component_key"]) for f in facts} - comps)
    assert not missing, f"facts name no accepted component: {missing}"
    weapon_rows = {
        f["record_key"]
        for f in facts
        if f["fact"]["family"] == "damage"
        and f["record_key"].startswith("equipment.weapons.")
    }
    assert len(weapon_rows) == 38, len(weapon_rows)
    body = {
        "candidate_id": CANDIDATE_ID,
        "status": "CANDIDATE ONLY - not accepted, recorded, published or activated",
        "proposed_schema": PROPOSED_SCHEMA,
        "anchored_oracle_sha256": ORACLE_SHA256,
        "facts": facts,
    }
    data = (
        json.dumps(body, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode()
    (HERE / "candidate-c1.json").write_bytes(data)
    print("facts", len(facts), "sha256", hashlib.sha256(data).hexdigest())
    print(
        json.dumps(
            {
                fam: sum(f["fact"]["family"] == fam for f in facts)
                for fam in sorted({f["fact"]["family"] for f in facts})
            },
            indent=1,
        )
    )


if __name__ == "__main__":
    main()
