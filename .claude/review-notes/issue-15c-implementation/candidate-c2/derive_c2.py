"""CRD Issue 15c semantic candidate C2 — source-derived content (REVIEW MATERIAL).

Candidate only. Nothing here is accepted, recorded, minted, published or
activated, and nothing is written outside this directory. C2 supersedes the
unaccepted C1 (``../candidate/``), which is preserved byte for byte as review
evidence; C2 reuses C1's weapon-row, rule and armor derivations unchanged by
importing them, and revises what #191's updated scope (body SHA-256
``8225e1b6…57a2``) requires:

* **C2-A** rules, weapons and *every* tool the source prints, addressed by
  their accepted identity grain (13 standalone records, 12 components of the
  ``equipment.tools`` section record), with each tool's category (artisan's or
  other) and printed variants.
* **C2-B** every accepted ``creature`` record wherever its stat block is
  printed (``monsters-A-Z.md``, ``animals.md``, ``spells.md``,
  ``magic-items.md``): defenses, the creature's attacks, saving-throw effects,
  Multiattack composition, usage limits and traits, each classified
  ``supported`` / ``conditional`` / ``deferred`` with its exact reason.
  Conditional and parameterized profiles are represented individually, never
  dropped.
* **C2-C** armor and character AC (C1-C content, unchanged).

Usage (repository root, clone venv)::

    venv/Scripts/python.exe .claude/review-notes/issue-15c-implementation/candidate-c2/derive_c2.py

Writes ``c2a.json``, ``c2b.json``, ``c2c.json`` and ``concordance.json``.
"""

from __future__ import annotations

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
SRC = REPO / "docs/sources/community/dnd-5e-srd-markdown"
HERE = Path(__file__).parent
C1 = HERE.parent / "candidate"
ORACLE = (
    REPO
    / "src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-8781d4e0-a3b-g1.json"
)
ORACLE_SHA256 = "2ccbaeba6de75d9787fbdd407e42dc2425fa20d4d26bcc298b681b550bd11258"  # pragma: allowlist secret
PROPOSED_SCHEMA = "5d-representation-schema-19 (proposed; not minted)"
STATUS = "CANDIDATE ONLY - not accepted, recorded, minted, published or activated"


def load(name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, C1 / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


c1a = load("derive_candidate")
c1b = load("derive_creatures")
c1c = load("derive_armor")
slug = c1a.slug


def lines(file: str) -> list[str]:
    return (SRC / file).read_text("utf-8").splitlines()


def write(name: str, body: dict[str, Any]) -> str:
    data = (json.dumps(body, indent=1, sort_keys=True, ensure_ascii=False) + "\n").encode()
    (HERE / name).write_bytes(data)
    return hashlib.sha256(data).hexdigest()


# ===========================================================================
# C2-A: every printed tool at its accepted identity grain
# ===========================================================================


def tools(records: set[str], comps: set[tuple[str, str]]) -> tuple[list[Any], list[Any]]:
    src = lines("equipment.md")
    start = next(i for i, l in enumerate(src) if l == "#### Artisan's Tools")
    other = next(i for i, l in enumerate(src) if l == "#### Other Tools")
    end = next(i for i, l in enumerate(src) if l == "## Adventuring Gear")
    facts: list[Any] = []
    concord: list[Any] = []
    for i in range(start, end):
        m = re.match(r"^\*\*(.+?) \((?:[\d,]+ [GS]P|Varies)\)\*\*$", src[i])
        if not m:
            continue
        name, key = m.group(1), slug(m.group(1))
        if f"equipment.tools.{key}" in records:
            identity = (f"equipment.tools.{key}", key)
        else:
            identity = ("equipment.tools", key)
        assert identity in comps, identity
        j = i + 1 + (src[i + 1] == "")
        ability = re.match(r"^\*\*Ability:\*\* (\w+)", src[j])
        assert ability, src[j]
        where = {"file": "equipment.md", "line": i + 1, "quote": src[i]}
        entry = {
            "family": "tool_entry",
            "ability": ability.group(1).lower(),
            "category": "artisans_tools" if i < other else "other_tools",
        }
        tool_facts: list[dict[str, Any]] = [entry]
        k = j + 1
        while k < len(src) and src[k].startswith("**") and not src[k].endswith(")**"):
            if src[k].startswith("**Utilize:**"):
                text = src[k].removeprefix("**Utilize:** ")
                for opt, dc in re.findall(r"([^,]+?) \(DC (\d+)\)", text):
                    opt = re.sub(r"^or ", "", opt.strip())
                    tool_facts.append(
                        {"family": "ability_check", "option_key": slug(opt),
                         "ability": entry["ability"], "context": "ability_check",
                         "dc_kind": "fixed", "dc_value": int(dc)}
                    )
            if src[k].startswith("**Variants:**"):
                variants = [
                    slug(re.sub(r" \(.*", "", v))
                    for v in re.split(r", (?![^()]*\))", src[k].removeprefix("**Variants:** "))
                ]
                tool_facts.append(
                    {"family": "tool_variants", "variants": variants,
                     "separate_proficiency": True}
                )
            k += 1
        for f in tool_facts:
            facts.append({"record_key": identity[0], "component_key": identity[1],
                          "fact": f, "source": where})
        concord.append({"tool": name, "identity": "/".join(identity),
                        "grain": "record" if identity[0] != "equipment.tools" else "component",
                        "facts": [f["family"] for f in tool_facts]})
    variants_rule = src.index(next(l for l in src if "Each requires a separate proficiency" in l)) + 1
    for f in facts:
        if f["fact"]["family"] == "tool_variants":
            f["source"]["variants_rule_line"] = variants_rule
    return facts, concord


# ===========================================================================
# C2-B: creature stat blocks wherever printed
# ===========================================================================

SIZES = c1b.SIZES
DAMAGE = c1b.DAMAGE
CONDITIONS = c1b.CONDITIONS
NUM = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6}
_DMG = re.compile(
    r"(?P<avg>\d+) \((?P<n>\d+)d(?P<d>\d+)(?: (?P<sign>[+−-]) (?P<mod>\d+))?\) "
    r"(?P<type>[A-Z][a-z]+) damage"
)
_FLAT = re.compile(r"(?P<avg>\d+) (?P<type>[A-Z][a-z]+) damage")
_ENTRY = re.compile(r"^\*\*_(?P<name>.+?)\._\*\* (?P<text>.*)$")
_USAGE = re.compile(r"^(?P<base>.+?) \((?P<usage>[^)]*)\)$")
_SECTIONS = {"actions": "action", "bonus actions": "bonus_action",
             "reactions": "reaction", "legendary actions": "legendary_action",
             "traits": "trait"}


def _damage_terms(text: str) -> tuple[list[dict[str, Any]], str]:
    """Leading damage terms joined by 'plus'; returns (terms, remainder)."""
    terms: list[dict[str, Any]] = []
    rest = text.strip()
    while True:
        m = _DMG.match(rest) or _FLAT.match(rest)
        if not m or m.group("type").lower() not in DAMAGE:
            break
        g = m.groupdict()
        mod = int(g.get("mod") or 0) * (-1 if g.get("sign") in ("−", "-") else 1)
        terms.append({
            "average": int(g["avg"]),
            "dice": ({"count": int(g["n"]), "die": f"d{g['d']}", "modifier": mod}
                     if g.get("n") else None),
            "damage_type": g["type"].lower(),
        })
        rest = rest[m.end():]
        nxt = re.match(r"^ plus ", rest)
        if not nxt:
            break
        rest = rest[nxt.end():]
    return terms, rest.strip()


_RIDERS: list[tuple[re.Pattern[str], Any]] = [
    (re.compile(r"^,? and the target has the (\w+) condition until the (start|end) of "
                r"(?:the [\w' -]+?'s|its) next turn\.$"),
     lambda m: {"condition": m.group(1).lower(),
                "duration": {"until": f"{m.group(2)}_of_turn", "whose": "attacker",
                             "turn": "next"}}),
    (re.compile(r"^(?:\. )?If the target is a (\w+) or smaller creature, it has the (\w+) "
                r"condition(?: \(escape DC (\d+)\))?\.$"),
     lambda m: {"condition": m.group(2).lower(), "maximum_size": m.group(1).lower(),
                "escape_dc": int(m.group(3)) if m.group(3) else None}),
    (re.compile(r"^,? and the target has the (\w+) condition(?: \(escape DC (\d+)\))?\.$"),
     lambda m: {"condition": m.group(1).lower(),
                "escape_dc": int(m.group(2)) if m.group(2) else None}),
]


def _rider(rest: str) -> tuple[dict[str, Any] | None, str | None]:
    rest = rest.strip()
    if rest in ("", "."):
        return None, None
    for pattern, build in _RIDERS:
        m = pattern.match(rest)
        if m:
            effect = build(m)
            if effect["condition"] not in CONDITIONS:
                return None, rest
            return effect, None
    return None, rest


def _attack(text: str) -> dict[str, Any] | None:
    # Two printed variants of the same notation: a malformed italic span
    # ("Melee or _Ranged Attack Roll:_") and "+17 to hit".
    text = text.replace("Melee or _Ranged Attack Roll:_", "_Melee or Ranged Attack Roll:_")
    m = re.match(
        r"^_(?P<kind>Melee|Ranged|Melee or Ranged) Attack Roll:_ (?P<bonus>[+−-]\d+)"
        r"(?: to hit)?(?: \((?P<adv>with Advantage [^)]*)\))?, "
        r"(?P<reach>.+?)\. _Hit:_ (?P<hit>.*?)(?: _Miss:_ (?P<miss>.*))?$",
        text,
    )
    if not m:
        return None
    reach = m.group("reach")
    rm = re.fullmatch(r"(?:reach (\d+) ft\.?)?(?: or )?(?:range (\d+)(?:/(\d+))? ft)?", reach)
    terms, rest = _damage_terms(m.group("hit"))
    effect, residue = _rider(rest)
    payload: dict[str, Any] = {
        "kind": slug(m.group("kind")),
        "attack_bonus": int(m.group("bonus").replace("−", "-")),
        "reach_ft": int(rm.group(1)) if rm and rm.group(1) else None,
        "normal_range_ft": int(rm.group(2)) if rm and rm.group(2) else None,
        "long_range_ft": int(rm.group(3)) if rm and rm.group(3) else None,
        "hit_damage": terms,
        "hit_effect": effect,
        "advantage_when": m.group("adv"),
    }
    reasons = []
    if m.group("adv"):
        reasons.append(f"attack Advantage predicate needs validated state: {m.group('adv')!r}")
    if not rm:
        reasons.append(f"reach/range not typed: {reach!r}")
    if not terms:
        reasons.append("hit prints no leading damage term")
    if residue:
        reasons.append(f"hit rider not typed: {residue!r}")
    if m.group("miss"):
        reasons.append(f"miss effect not typed: {m.group('miss')!r}")
    payload["untyped"] = reasons
    return payload


def _save(text: str) -> dict[str, Any] | None:
    m = re.match(
        r"^_(?P<ability>\w+) Saving Throw:_ DC (?P<dc>\d+), (?P<targets>.+?)\. "
        r"_Failure:_ (?P<fail>.*?)(?: _Success:_ (?P<succ>.*?))?"
        r"(?: _Failure or Success:_ (?P<both>.*))?$",
        text,
    )
    if not m:
        return None
    targets = m.group("targets")
    single = re.fullmatch(r"one (?:(\w+) or smaller )?creature (?:the [\w' -]+ can see )?within "
                          r"(\d+) feet(?: of (?:itself|it))?", targets)
    area = re.fullmatch(r"each creature in (?:a|an) (\d+)-foot(?:-long, (\d+)-foot-wide)? "
                        r"(\w+)(?: .*)?", targets)
    terms, rest = _damage_terms(m.group("fail"))
    effect, residue = _rider(", and " + rest[0].lower() + rest[1:] if rest[:4] == "The " and
                             False else rest)
    reasons = []
    if single:
        tgt: dict[str, Any] = {"count": 1, "within_ft": int(single.group(2)),
                               "maximum_size": single.group(1).lower() if single.group(1) else None}
    elif area:
        tgt = {"area": area.group(3).lower(), "size_ft": int(area.group(1)),
               "width_ft": int(area.group(2)) if area.group(2) else None}
        reasons.append("area membership needs explicit position authority")
    else:
        tgt = {"text": targets}
        reasons.append(f"targets not typed: {targets!r}")
    if residue:
        reasons.append(f"failure rider not typed: {residue!r}")
    succ = (m.group("succ") or "").strip()
    if succ and succ not in ("Half damage.", "Half damage only."):
        reasons.append(f"success effect not typed: {succ!r}")
    if m.group("both"):
        reasons.append(f"failure-or-success effect not typed: {m.group('both')!r}")
    return {
        "save": m.group("ability").lower(), "dc": int(m.group("dc")), "targets": tgt,
        "failure_damage": terms, "failure_effect": effect,
        "success": "half_damage" if succ.startswith("Half damage") else None,
        "untyped": reasons,
    }


def _multiattack(text: str, names: set[str]) -> dict[str, Any]:
    parts: list[dict[str, Any]] = []
    reasons: list[str] = []
    body = re.sub(r"^The [\w' -]+? makes ", "", text.strip())
    for clause in re.split(r",? and (?=(?:one|two|three|four|five|six|uses) )", body):
        clause = clause.strip().rstrip(".")
        m = re.fullmatch(r"(one|two|three|four|five|six) (.+?) attacks?(?:\..*)?", clause)
        any_m = re.fullmatch(r"(one|two|three|four|five|six) attacks?, using (.+?) in any "
                             r"combination(?:\..*)?", clause)
        use_m = re.fullmatch(r"uses (.+?)(?:\..*)?", clause)
        if any_m:
            options = [o.strip() for o in re.split(r",? or |, ", any_m.group(2))]
            parts.append({"count": NUM[any_m.group(1)], "any_of": options})
        elif m:
            parts.append({"count": NUM[m.group(1)], "attack": m.group(2)})
        elif use_m:
            parts.append({"count": 1, "uses": use_m.group(1)})
        else:
            reasons.append(f"composition clause not typed: {clause!r}")
    replace = re.search(r"(?:It|they) can replace (one|two) attacks? with a use of (.+?)\.", text)
    if replace:
        parts.append({"may_replace": NUM[replace.group(1)], "with": replace.group(2)})
        if replace.group(2) not in names:
            reasons.append(f"replacement {replace.group(2)!r} names no entry of this block")
    for p in parts:
        for key in ("any_of", "attack", "uses", "with"):
            refs = p.get(key)
            refs = refs if isinstance(refs, list) else [refs] if refs else []
            resolved = []
            for ref in refs:
                for opt in _options(ref):
                    if "Spellcasting" in opt:
                        reasons.append(f"spellcasting option deferred: {opt!r}")
                        resolved.append({"spellcasting": opt})
                    elif opt in names:
                        resolved.append(opt)
                    else:
                        reasons.append(f"{opt!r} names no entry of this block")
                        resolved.append({"unresolved": opt})
            if refs:
                p[key + "_resolved"] = resolved
    return {"composition": parts, "untyped": reasons}


def _options(ref: str) -> list[str]:
    """Option names a Multiattack reference offers: "(A) X or (B) Y",
    "either X or Y if available", "X and Y"."""
    ref = re.sub(r"\((?:A|B)\) ", "", ref).removeprefix("either ")
    available = ref.endswith(" if available")
    ref = ref.removesuffix(" if available")
    opts = [o.strip() for o in re.split(r",? or |, | and (?!Spellcasting)", ref)
            if o.strip()]
    return [o + (" [if available]" if available and False else "") for o in opts]


#: Recurring contributors typed exactly (name -> (typed meaning, state it needs)).
#: Their wording is uniform across blocks; the subject is the creature itself.
TYPED_CONTRIBUTORS: dict[str, tuple[dict[str, Any], str]] = {
    "Magic Resistance": (
        {"family": "advantage", "state": "advantage",
         "roll": {"actor": "subject", "context": "saving_throw", "ability": None},
         "applies_when": "the effect forcing the save is a spell or other magical effect"},
        "the forcing effect's magical/non-magical classification",
    ),
    "Legendary Resistance": (
        {"family": "save_override", "on": "failed_saving_throw", "may_choose": "success",
         "chooser": "gamemaster", "usage": "per_entry_limit"},
        "the usage counter (X/Day, lair variant) and a recorded GameMaster choice",
    ),
    "Pack Tactics": (
        {"family": "advantage", "state": "advantage",
         "roll": {"actor": "subject", "context": "attack_roll", "ability": None},
         "applies_when": {"ally_within_ft_of_target": 5, "ally_not": "incapacitated"}},
        "explicit position of allies and target",
    ),
    "Sunlight Sensitivity": (
        {"family": "advantage", "state": "disadvantage",
         "roll": {"actor": "subject", "context": ["ability_check", "attack_roll"],
                  "ability": None},
         "applies_when": "the subject is in sunlight"},
        "a recorded in-sunlight environment state",
    ),
}

#: Entries a keyword scan would file as having no roster effect but which are
#: their own mechanics; each is named rather than silently admitted.
NAMED_DEFERRED = {
    "Shape-Shift": "changes the creature's form; form-dependent entries need a "
                   "recorded current form, and the change itself is not a roster operation",
    "Berserk": "a per-turn random-target behaviour mechanic outside the roster",
    "Coven Magic": "shared spellcasting; general spell execution is a non-goal",
}
_CONTRIBUTOR = re.compile(r"Advantage|Disadvantage|saving throw|attack roll|damage|"
                          r"Armor Class|\bAC\b|Hit Points|condition|succeed instead", re.I)
_SPELL = re.compile(r"Spellcasting|\bcasts?\b|_[A-Z][\w' ]+_", re.S)


def entries(block_lines: list[str]) -> list[dict[str, Any]]:
    section = "trait"
    out = []
    names: set[str] = set()
    raw = []
    for line in block_lines:
        h = re.match(r"^#{3,6} (.+)$", line)
        if h and h.group(1).lower() in _SECTIONS:
            section = _SECTIONS[h.group(1).lower()]
            continue
        e = _ENTRY.match(line)
        if e:
            name = e.group("name")
            u = _USAGE.match(name)
            usage = None
            if u:
                name, usage = u.group("base"), u.group("usage")
            raw.append((section, name, usage, e.group("text")))
            names.add(name)
    for section, name, usage, text in raw:
        entry: dict[str, Any] = {"section": section, "name": name}
        usage_typed = None
        if usage:
            um = re.fullmatch(r"Recharge (\d)(?:–(\d))?", usage)
            dm = re.fullmatch(r"(\d)/Day(?: Each)?", usage)
            if um:
                usage_typed = {"kind": "recharge", "minimum_d6": int(um.group(1))}
            elif dm:
                usage_typed = {"kind": "per_day", "uses": int(dm.group(1))}
            elif usage == "Recharges after a Short or Long Rest":
                usage_typed = {"kind": "recharge_after_rest"}
            elif lm := re.fullmatch(r"(\d)/Day, or (\d)/Day in Lair", usage):
                usage_typed = {"kind": "per_day", "uses": int(lm.group(1)),
                               "in_lair": int(lm.group(2))}
            elif fm := re.fullmatch(r"(.+?) (?:Form )?Only(?:; Recharges after a Long Rest)?",
                                    usage):
                forms = [slug(f) for f in re.split(r" or ", fm.group(1).removesuffix(" Form"))]
                usage_typed = {"kind": "form_only", "forms": forms,
                               "recharge_after_long_rest": "Recharges" in usage}
            elif usage == "Requires Magic Rope":
                usage_typed = {"kind": "requires_entry", "entry": "Magic Rope"}
            entry["usage"] = usage_typed or {"text": usage}
        attack = _attack(text)
        save = None if attack else _save(text)
        reasons: list[str] = []
        if usage and usage_typed is None:
            reasons.append(f"usage not typed: {usage!r}")
        if usage_typed and usage_typed["kind"] == "recharge":
            reasons.append("Recharge needs explicit start-of-turn authority")
        if usage_typed and usage_typed.get("in_lair"):
            reasons.append("the lair variant needs a recorded in-lair state")
        if usage_typed and usage_typed["kind"] == "form_only":
            reasons.append("needs the creature's recorded current form")
        if section == "legendary_action":
            reasons.append("legendary timing needs explicit actor-turn authority")
        if attack:
            entry.update(kind="attack", attack=attack)
            reasons += attack.pop("untyped")
        elif save:
            entry.update(kind="save_effect", save=save)
            reasons += save.pop("untyped")
        elif name == "Multiattack":
            ma = _multiattack(text, names)
            entry.update(kind="multiattack", multiattack=ma)
            reasons += ma.pop("untyped")
        elif _SPELL.search(text) and ("Spellcasting" in name or " casts " in text or
                                      "uses Spellcasting" in text):
            entry.update(kind="spellcasting")
            entry["classification"] = "deferred"
            entry["reasons"] = ["general spell execution is a non-goal"]
            out.append(entry)
            continue
        elif section == "reaction":
            entry.update(kind="reaction", text=text)
            entry["classification"] = "deferred"
            entry["reasons"] = ["reaction trigger/response is a new mechanic; named "
                                "individually"]
            out.append(entry)
            continue
        elif ref := next((n for n in sorted(names) if n != name and
                          re.search(rf"\bmakes? (?:one|two|three) {re.escape(n)} attacks?\b|"
                                    rf"\buses {re.escape(n)}\b", text)), None):
            entry.update(kind="entry_reference", text=text, references=ref)
            reasons.append(f"uses {ref!r} under its own movement/timing terms; named "
                           "individually")
        elif "Saving Throw:_" in text or "Attack Roll:_" in text:
            entry.update(kind="special_effect", text=text)
            reasons.append("special effect outside the bounded attack/save shapes "
                           "(preamble movement, staged failures, death or aura "
                           "triggers); named individually")
        elif name in TYPED_CONTRIBUTORS:
            typed, needs = TYPED_CONTRIBUTORS[name]
            entry.update(kind="contributor", text=text, contributor=typed)
            reasons.append(f"predicate typed; needs {needs}")
        elif _CONTRIBUTOR.search(text):
            entry.update(kind="contributor", text=text)
            reasons.append("contributing trait/action named individually; operations it "
                           "can affect refuse until its predicate is typed and accepted")
        elif name in NAMED_DEFERRED:
            entry.update(kind="named_mechanic", text=text)
            entry["classification"] = "deferred"
            entry["reasons"] = [NAMED_DEFERRED[name]]
            out.append(entry)
            continue
        else:
            entry.update(kind="no_roster_effect", text=text)
        entry["classification"] = ("supported" if not reasons else
                                   "deferred" if entry.get("kind") == "contributor" and False
                                   else "conditional")
        if entry["kind"] == "no_roster_effect":
            entry["classification"] = "no_roster_effect"
        entry["reasons"] = reasons
        out.append(entry)
    return out


def stat_blocks(file: str, heading_level: str) -> list[dict[str, Any]]:
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
        blocks.append({"file": file, "line": i + 1, "heading_line": j + 1,
                       "heading": src[j].lstrip("#").strip(), "lines": src[j:k],
                       "size_line": next(src[x] for x in range(j + 1, i) if src[x].startswith("_")),
                       "ac_line": line, "body": src[i:k]})
    return blocks


#: Individually assessed profiles: parameterized, conditional or (Giant Fly)
#: printed outside the creature chapters. Each keeps the printed parameters and
#: names exactly what an operation needs before it can rely on them.
ASSESSED: dict[str, dict[str, Any]] = {
    "magic_items.figurine_of_wondrous_power.giant_fly": {
        "status": "fixed",
        "defense": {"armor_class": 11, "hit_points": 19,
                    "hit_point_dice": {"count": 3, "die": "d10", "modifier": 3}},
        "note": "Fixed AC 11 and HP 19 (3d10 + 3); no action entries.",
    },
    "magic_items.mysterious_deck.avatar_of_death": {
        "status": "parameterized",
        "defense": {"armor_class": 20,
                    "hit_points": {"formula": "half_of", "of": "summoner_hit_point_maximum"}},
        "attacks": [{"name": "Reaping Scythe", "automatic_hit": True, "reach_ft": 5,
                     "hit_damage": [{"average": 7, "dice": {"count": 1, "die": "d8",
                                     "modifier": 3}, "damage_type": "slashing"},
                                    {"average": 4, "dice": {"count": 1, "die": "d8",
                                     "modifier": 0}, "damage_type": "necrotic"}]}],
        "multiattack": {"count": {"formula": "half_round_up", "of": "summoner_proficiency_bonus"}},
        "requires": ["the summoner's identity and current HP maximum and Proficiency Bonus "
                     "recorded (summon origin)", "'targets only' the summoner"],
    },
    "spells.animate_objects.animated_object": {
        "status": "parameterized",
        "defense": {"armor_class": 15,
                    "hit_points": {"by_size": {"medium_or_smaller": 10, "large": 20,
                                               "huge": 40}}},
        "attacks": [{"name": "Slam", "attack_bonus": {"formula": "caster_spell_attack_modifier"},
                     "reach_ft": 5,
                     "hit_damage_by_size": {
                         "medium_or_smaller": "1d4 + 3",
                         "large": "2d6 + 3 + caster_spellcasting_ability_modifier",
                         "huge": "2d12 + 3 + caster_spellcasting_ability_modifier"},
                     "damage_type": "force"}],
        "requires": ["the recorded size", "the caster's spell attack modifier and "
                     "spellcasting ability modifier as recorded state; casting is not "
                     "executed"],
    },
    "spells.find_steed.otherworldly_steed": {
        "status": "parameterized",
        "defense": {"armor_class": {"base": 10, "per_spell_level": 1},
                    "hit_points": {"base": 5, "per_spell_level": 10}},
        "attacks": [{"name": "Otherworldly Slam",
                     "attack_bonus": {"formula": "caster_spell_attack_modifier"},
                     "reach_ft": 5, "hit_damage": "1d8 + spell_level",
                     "damage_type_by_choice": {"celestial": "radiant", "fey": "psychic",
                                               "fiend": "necrotic"}}],
        "requires": ["the recorded cast level and type choice (summon state)",
                     "the caster's spell attack modifier / spell save DC as recorded state"],
        "deferred": ["Fell Glare, Fey Step, Healing Touch (bonus actions: spell-derived DC, "
                     "teleport, healing — individually named)"],
    },
    "spells.giant_insect.giant_insect": {
        "status": "parameterized",
        "defense": {"armor_class": {"base": 11, "per_spell_level": 1},
                    "hit_points": {"base": 30, "per_spell_level_above": {"level": 4,
                                                                         "amount": 10}}},
        "multiattack": {"count": {"formula": "half_round_down", "of": "spell_level"}},
        "attacks": [{"name": "Poison Jab",
                     "attack_bonus": {"formula": "caster_spell_attack_modifier"},
                     "reach_ft": 10, "hit_damage": "1d6 + 3 + spell_level piercing plus 1d4 "
                     "poison"},
                    {"name": "Web Bolt", "form": "spider",
                     "attack_bonus": {"formula": "caster_spell_attack_modifier"},
                     "range_ft": 60, "hit_damage": "1d10 + 3 + spell_level bludgeoning",
                     "hit_effect": "Speed 0 until the start of the insect's next turn"}],
        "requires": ["the recorded cast level and form choice"],
        "deferred": ["Venomous Spew (spell save DC)"],
    },
    "spells.summon_dragon.draconic_spirit": {
        "status": "parameterized",
        "defense": {"armor_class": {"base": 14, "per_spell_level": 1},
                    "hit_points": {"base": 50, "per_spell_level_above": {"level": 5,
                                                                         "amount": 10}},
                    "resistance": ["acid", "cold", "fire", "lightning", "poison"],
                    "condition_immunity": ["charmed", "frightened", "poisoned"]},
        "multiattack": {"count": {"formula": "half_round_down", "of": "spell_level"},
                        "and_uses": "Breath Weapon"},
        "attacks": [{"name": "Rend",
                     "attack_bonus": {"formula": "caster_spell_attack_modifier"},
                     "reach_ft": 10, "hit_damage": "1d6 + 4 + spell_level piercing"}],
        "requires": ["the recorded cast level; the breath damage type choice"],
        "deferred": ["Breath Weapon (spell save DC; area)"],
    },
    "monsters.half_dragon.half_dragon": {
        "status": "conditional",
        "exact_meaning": "Resistance to the one damage type chosen for Draconic Origin "
                         "(GM's choice among acid, cold, fire, lightning, poison); the same "
                         "choice sets the Claw's extra damage and Dragon's Breath type.",
        "selection": {"vocabulary": ["acid", "cold", "fire", "lightning", "poison"],
                      "recorded_as": "a ChoiceRecord on the creature (2b typed selection)"},
        "requires": ["the creature's recorded Draconic Origin choice; absent → operations "
                     "depending on it refuse as missing state"],
    },
    "monsters.mages.archmage": {
        "status": "conditional",
        "exact_meaning": "Immunity to Charmed only while under Mind Blank "
                         "(spells.mind_blank).",
        "predicate": {"active_effect_on_subject": "spells.mind_blank"},
        "requires": ["the creature's recorded active effects (2b ActiveEffect); Mind Blank "
                     "itself is not cast here"],
    },
    "monsters.rakshasa.rakshasa": {
        "status": "conditional",
        "exact_meaning": "Vulnerability to Piercing damage only from a weapon wielded by a "
                         "creature under Bless (spells.bless).",
        "predicate": {"damage_type": "piercing", "attack": "weapon",
                      "attacker_active_effect": "spells.bless"},
        "requires": ["the attacker's recorded active effects"],
    },
    "monsters.vampires.vampire_familiar": {
        "status": "conditional",
        "exact_meaning": "Immunity to Charmed except from its vampire master.",
        "predicate": {"condition": "charmed", "unless_source_is": "recorded_vampire_master"},
        "requires": ["a recorded master identity for the familiar; 2b records summoner/"
                     "controller only. Until a master relation is recorded, a Charmed "
                     "determination on it refuses as missing state (genuinely unprovable "
                     "prerequisite, surfaced)"],
    },
}


def creatures(rep: dict[str, Any]) -> tuple[list[Any], dict[str, Any]]:
    keys = sorted(r["semantic_key"] for r in rep["records"] if r["kind"] == "creature")
    comps = {(c["record_key"], c["semantic_key"]) for c in rep["components"]}
    by_tail: dict[str, list[str]] = {}
    for key in keys:
        by_tail.setdefault(key.rsplit(".", 1)[1], []).append(key)
    prefix = {"monsters-A-Z.md": "monsters.", "animals.md": "animals.",
              "spells.md": "spells.", "magic-items.md": "magic_items."}
    out: list[Any] = []
    unmatched: list[Any] = []
    matched: set[str] = set()
    for file in prefix:
        for b in stat_blocks(file, ""):
            tail = slug(b["heading"])
            cand = [k for k in by_tail.get(tail, []) if k.startswith(prefix[file])]
            if len(cand) != 1:
                unmatched.append({"heading": b["heading"], "file": file, "line": b["line"]})
                continue
            (key,) = cand
            matched.add(key)
            where = {"file": file, "line": b["line"], "heading": b["heading"]}
            record: dict[str, Any] = {"record_key": key, "component_key": tail,
                                      "source": where}
            if key in ASSESSED:
                record["assessed"] = ASSESSED[key]
                record["classification"] = ASSESSED[key]["status"]
            if (key, tail) not in comps:
                record["classification"] = "unaddressable"
            typed, why = c1b.profile(b)
            if typed is not None:
                record["defense"], record["profile"] = typed
            else:
                record["profile_untyped"] = why
                if key not in ASSESSED:
                    record["classification"] = "conditional"
            # Re-type the conditional terms exactly rather than dropping them.
            if key in ASSESSED and typed is None:
                fixed, _ = _profile_without_conditionals(b)
                if fixed is not None:
                    record["defense"], record["profile"] = fixed
            record["entries"] = entries(b["lines"])
            record.setdefault("classification", "typed")
            out.append(record)
    census = {"creature_records": len(keys),
              "unmatched_records": [k for k in keys if k not in matched],
              "unmatched_stat_blocks": unmatched}
    return out, census


def _profile_without_conditionals(b: dict[str, Any]) -> tuple[Any, list[str]]:
    """The fixed fields of a block whose one defensive line is conditional:
    the conditional terms are removed here and carried exactly in ASSESSED."""
    body = [re.sub(r"^\*\*(Resistances|Vulnerabilities)\*\* (Damage type chosen|Piercing "
                   r"damage from).*$", "", l) for l in b["body"]]
    body = [l.replace("; Charmed (with _Mind Blank_)", "")
            .replace("**Immunities** Charmed (except from its vampire master) <br>", "")
            for l in body]
    return c1b.profile({**b, "body": body})


# Stat-block conventions the creature entries rely on (hand-authored; each
# quote is checked on its line, as in C1).
MON = "monsters.md"
SB = "monsters.parts_of_a_stat_block"
STAT_BLOCK_RULES: list[tuple[str, str, str, str, dict[str, Any]]] = [
    (SB, "attack_notation", MON, "An attack is against one target unless its entry says",
     {"family": "creature_attack_notation", "targets": 1,
      "sections": ["hit", "miss", "hit_or_miss"]}),
    (SB, "saving_throw_effect_notation", MON,
     "\"Half damage only\" on a successful save means the target takes half as much damage",
     {"family": "creature_save_notation", "half_damage_rounding": "down",
      "half_damage_only_ignores_other_effects": True}),
    (SB, "damage_notation", MON, "You decide whether to use the number or the die expression",
     {"family": "damage_notation_option", "options": ["average", "dice"],
      "selected_by": "gamemaster", "exclusive": True}),
    (SB, "multiattack", MON, "Some creatures can make more than one attack when they take the "
     "Attack action", {"family": "multiattack_rule", "action": "attack",
                       "composition": "per_entry"}),
    (SB, "limited_usage", MON, "**X/Day.** This notation means",
     {"family": "usage_limit_rule", "kind": "per_day", "regain": "long_rest"}),
    (SB, "limited_usage", MON, "**Recharge X–Y.** This notation means",
     {"family": "usage_limit_rule", "kind": "recharge", "die": "d6",
      "roll_at": "start_of_turn", "also_regain": ["short_rest", "long_rest"]}),
    (SB, "limited_usage", MON, "**Recharge after a Short or Long Rest.**",
     {"family": "usage_limit_rule", "kind": "recharge_after_rest",
      "regain": ["short_rest", "long_rest"]}),
    (SB, "legendary_actions", MON, "it regains all expended uses at the start of each of its turns",
     {"family": "legendary_action_rule", "timing": "after_another_creatures_turn",
      "one_at_a_time": True, "regain": "start_of_own_turn",
      "blocked_by": ["incapacitated"]}),
]


def stat_block_rules(comps: set[tuple[str, str]]) -> list[dict[str, Any]]:
    out = []
    for record, component, file, quote, fact in STAT_BLOCK_RULES:
        assert (record, component) in comps, (record, component)
        out.append({"record_key": record, "component_key": component, "fact": fact,
                    "source": {"file": file, "line": c1a.locate(file, quote),
                               "quote": quote}})
    return out


# ===========================================================================


def main() -> None:
    raw = ORACLE.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == ORACLE_SHA256, "accepted oracle changed"
    rep = json.loads(raw)["representation"]
    comps = {(c["record_key"], c["semantic_key"]) for c in rep["components"]}
    records = {r["semantic_key"] for r in rep["records"]}

    weapon_and_rules = c1a.weapons() + c1a.rule_facts()
    tool_facts, tool_concord = tools(records, comps)
    a_facts = weapon_and_rules + tool_facts + stat_block_rules(comps)
    assert not {(f["record_key"], f["component_key"]) for f in a_facts} - comps
    h_a = write("c2a.json", {"candidate_id": "15c-C2-A", "status": STATUS,
                             "proposed_schema": PROPOSED_SCHEMA,
                             "anchored_oracle_sha256": ORACLE_SHA256, "facts": a_facts})

    creature_records, census = creatures(rep)
    h_b = write("c2b.json", {"candidate_id": "15c-C2-B", "status": STATUS,
                             "proposed_schema": PROPOSED_SCHEMA,
                             "anchored_oracle_sha256": ORACLE_SHA256,
                             "creatures": creature_records, "census": census})

    c_facts = c1c.armor() + [
        {"record_key": r, "component_key": c, "fact": f,
         "source": {"file": file, "line": c1c.locate(file, q), "quote": q}}
        for r, c, file, q, f in c1c.RULES
    ]
    h_c = write("c2c.json", {"candidate_id": "15c-C2-C", "status": STATUS,
                             "proposed_schema": PROPOSED_SCHEMA,
                             "anchored_oracle_sha256": ORACLE_SHA256, "facts": c_facts})

    from collections import Counter
    entry_classes: Counter[str] = Counter()
    kinds: Counter[str] = Counter()
    for r in creature_records:
        for e in r["entries"]:
            entry_classes[e["classification"]] += 1
            kinds[e["kind"]] += 1
    concordance = {
        "hashes": {"c2a.json": h_a, "c2b.json": h_b, "c2c.json": h_c},
        "tools": tool_concord,
        "creatures": {
            "records": census["creature_records"],
            "matched": census["creature_records"] - len(census["unmatched_records"]),
            "unmatched_records": census["unmatched_records"],
            "unmatched_stat_blocks": census["unmatched_stat_blocks"],
            "record_classification": dict(Counter(r["classification"]
                                                  for r in creature_records)),
            "entry_kinds": dict(kinds),
            "entry_classification": dict(entry_classes),
        },
        "a_families": dict(Counter(f["fact"]["family"] for f in a_facts)),
    }
    write("concordance.json", concordance)
    print(json.dumps(concordance["hashes"], indent=1))
    print(json.dumps({k: v for k, v in concordance["creatures"].items()
                      if k not in ("unmatched_records",)}, indent=1))
    print(len(tool_concord), "tools")


if __name__ == "__main__":
    main()
