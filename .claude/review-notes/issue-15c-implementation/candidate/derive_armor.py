"""CRD Issue 15c candidate C1-C — armor and character AC (REVIEW MATERIAL).

Candidate only; writes nothing outside this directory. Derives the Armor
table's 13 rows and Shield from the pinned Markdown (category from the group
row, AC formula, Strength requirement, Stealth Disadvantage), plus the base-AC
and armor-training rules a character AC and its D20-Test penalties need.
Writes ``candidate-c1c.json``.
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


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower().replace("'", "")).strip("_")


def locate(file: str, needle: str) -> int:
    for i, line in enumerate((SRC / file).read_text("utf-8").splitlines(), 1):
        if needle in line:
            return i
    raise SystemExit(f"{file}: {needle!r} not found")


def armor() -> list[dict[str, Any]]:
    text = (SRC / "equipment.md").read_text("utf-8")
    start = text.index("**Armor**\n")
    body = text[text.index("<table>", start) : text.index("</table>", start)]
    out, category = [], ""
    for tr in re.findall(r"<tr>(.*?)</tr>", body, re.S):
        if "<th colspan" in tr:
            category = slug(html.unescape(re.sub(r"<[^>]+>", "", tr)).split(" (")[0])
            continue
        cells = [html.unescape(c).strip() for c in re.findall(r"<td>(.*?)</td>", tr)]
        if not cells:
            continue
        name, ac, strength, stealth = cells[:4]
        key = slug(name)
        where = {
            "file": "equipment.md",
            "line": locate("equipment.md", f"<td>{name}</td>"),
            "quote": f"<td>{name}</td>",
        }
        if category == "shield":
            fact: dict[str, Any] = {
                "family": "shield_bonus",
                "bonus": int(ac.lstrip("+")),
            }
        else:
            m = re.fullmatch(r"(\d+)(?: \+ Dex modifier(?: \(max (\d+)\))?)?", ac)
            assert m, ac
            fact = {
                "family": "armor_class_formula",
                "category": category.removesuffix("_armor"),
                "base": int(m.group(1)),
                "adds_dexterity_modifier": "Dex" in ac,
                "dexterity_maximum": int(m.group(2)) if m.group(2) else None,
                "strength_minimum": (
                    int(strength.split()[1]) if strength != "—" else None
                ),
                "stealth_disadvantage": stealth == "Disadvantage",
            }
        out.append(
            {
                "record_key": f"equipment.armor.{key}",
                "component_key": key,
                "fact": fact,
                "source": where,
            }
        )
    return out


RULES = [
    (
        "play.d20_tests",
        "base_ac",
        "playing-the-game.md",
        "**Base AC** = 10 + the creature's Dexterity modifier",
        {"family": "base_armor_class", "base": 10, "adds_dexterity_modifier": True},
    ),
    (
        "play.d20_tests",
        "only_one_base_ac",
        "playing-the-game.md",
        "only one base calculation can be in effect",
        {"family": "base_armor_class_exclusivity", "maximum": 1},
    ),
    (
        "equipment.armor",
        "light_medium_or_heavy_armor",
        "equipment.md",
        "you have Disadvantage on any D20 Test that involves Strength or Dexterity",
        {
            "family": "armor_training_penalty",
            "abilities": ["strength", "dexterity"],
            "d20_tests": "disadvantage",
            "applies_to": ["light", "medium", "heavy"],
        },
    ),
    (
        "equipment.armor",
        "armor_training",
        "equipment.md",
        "You gain the Armor Class benefit of a Shield only if you have training with it",
        {
            "family": "shield_training_requirement",
            "untrained": "no_armor_class_benefit",
        },
    ),
]


def main() -> None:
    raw = ORACLE.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == ORACLE_SHA256, "accepted oracle changed"
    rep = json.loads(raw)["representation"]
    comps = {(c["record_key"], c["semantic_key"]) for c in rep["components"]}
    facts = armor() + [
        {
            "record_key": r,
            "component_key": c,
            "fact": f,
            "source": {"file": file, "line": locate(file, q), "quote": q},
        }
        for r, c, file, q, f in RULES
    ]
    missing = sorted({(f["record_key"], f["component_key"]) for f in facts} - comps)
    body = {
        "candidate_id": "15c-C1-C",
        "status": "CANDIDATE ONLY - not accepted, recorded, published or activated",
        "proposed_schema": "5d-representation-schema-19 (proposed; not minted)",
        "anchored_oracle_sha256": ORACLE_SHA256,
        "facts": facts,
        # Facts whose carrying component does not exist yet: minting must add
        # (or the reviewer must re-home) the component, never invent content.
        "components_to_mint": [list(m) for m in missing],
    }
    data = (
        json.dumps(body, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode()
    (HERE / "candidate-c1c.json").write_bytes(data)
    print(
        "facts",
        len(facts),
        "components to mint",
        missing,
        "sha256",
        hashlib.sha256(data).hexdigest(),
    )


if __name__ == "__main__":
    main()
