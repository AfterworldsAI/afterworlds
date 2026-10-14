"""CRD Issue 15c candidate C1-B — creature defensive profiles (REVIEW MATERIAL).

Candidate only; writes nothing outside this directory. Derives, from the pinned
Markdown stat blocks alone, the fields the 15c roster consumes when a creature
is an attack/mastery target: AC, size, the six ability scores and printed SAVE
modifiers, damage resistances/vulnerabilities/immunities and condition
immunities. Actions, skills, senses, HP and CR are not typed (monster
stat-block actions are outside the roster).

Two-sided census: every accepted ``creature`` record must map to exactly one
source stat block and vice versa; mismatches and any qualified/conditional
value are reported in ``refused`` (the creature is then "not typed → refuse")
rather than guessed. Writes ``candidate-c1b.json``.
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
SIZES = ("tiny", "small", "medium", "large", "huge", "gargantuan")
DAMAGE = {
    "acid",
    "bludgeoning",
    "cold",
    "fire",
    "force",
    "lightning",
    "necrotic",
    "piercing",
    "poison",
    "psychic",
    "radiant",
    "slashing",
    "thunder",
}
CONDITIONS = {
    "blinded",
    "charmed",
    "deafened",
    "exhaustion",
    "frightened",
    "grappled",
    "incapacitated",
    "invisible",
    "paralyzed",
    "petrified",
    "poisoned",
    "prone",
    "restrained",
    "stunned",
    "unconscious",
}
ABILITY = {
    "STR": "strength",
    "DEX": "dexterity",
    "CON": "constitution",
    "INT": "intelligence",
    "WIS": "wisdom",
    "CHA": "charisma",
}


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower().replace("'", "")).strip("_")


def _num(text: str) -> int:
    return int(text.replace("−", "-").replace("+", ""))


def _terms(text: str) -> list[str]:
    return [t.strip().lower() for t in text.split(",") if t.strip()]


def blocks(file: str) -> list[dict[str, Any]]:
    src = (SRC / file).read_text("utf-8").splitlines()
    out = []
    for i, line in enumerate(src):
        if not line.startswith("**AC** "):
            continue
        j = i - 1
        while not src[j].startswith("#"):
            j -= 1
        heading = src[j].lstrip("#").strip()
        size_line = next(src[k] for k in range(j + 1, i) if src[k].startswith("_"))
        k = i
        while k < len(src) and not src[k].startswith("#### "):
            k += 1
        out.append(
            {
                "file": file,
                "line": i + 1,
                "heading": heading,
                "size_line": size_line,
                "ac_line": line,
                "body": src[i:k],
            }
        )
    return out


def profile(b: dict[str, Any]) -> tuple[list[dict[str, Any]] | None, list[str]]:
    why: list[str] = []
    ac = re.fullmatch(r"\*\*AC\*\* (\d+) \*\*Initiative\*\*.*", b["ac_line"])
    if not ac:
        why.append(f"AC not a plain number: {b['ac_line']!r}")
    # "Medium or Small Humanoid" prints a size choice; "Medium Swarm of Tiny
    # Beasts" prints the swarm's own size first. Both are typed as printed.
    m = re.match(r"_((?:\w+ or )?\w+) ", b["size_line"])
    sizes = [slug(w) for w in m.group(1).split(" or ")] if m else []
    if not sizes or any(s not in SIZES for s in sizes):
        why.append(f"size not printed sizes: {b['size_line']!r}")
    body = "\n".join(b["body"])
    cells = [
        html.unescape(re.sub(r"<[^>]+>", "", c)).strip()
        for c in re.findall(r"<td>(.*?)</td>", body)
    ]
    scores: dict[str, Any] = {}
    for n in range(0, len(cells) - 3, 4):
        if cells[n] in ABILITY:
            scores[ABILITY[cells[n]]] = {
                "score": int(cells[n + 1]),
                "save": _num(cells[n + 3]),
            }
    if len(scores) != 6:
        why.append(f"{len(scores)} ability rows")
    defenses: dict[str, list[str]] = {
        "resistance": [],
        "vulnerability": [],
        "immunity": [],
        "condition_immunity": [],
    }
    for label, key in (
        ("Resistances", "resistance"),
        ("Vulnerabilities", "vulnerability"),
        ("Immunities", "immunity"),
    ):
        m = re.search(rf"^\*\*{label}\*\* (.*?)(?:<br>)?\s*$", body, re.M)
        if not m:
            continue
        damage_part, _, cond_part = m.group(1).partition(";")
        for t in _terms(damage_part):
            if t in DAMAGE:
                defenses[key].append(t)
            elif key == "immunity" and not cond_part and t in CONDITIONS:
                defenses["condition_immunity"].append(t)
            else:
                why.append(f"{label} term not a plain damage type: {t!r}")
        for t in _terms(cond_part):
            if key == "immunity" and t in CONDITIONS:
                defenses["condition_immunity"].append(t)
            else:
                why.append(f"{label} condition term not plain: {t!r}")
    hp = re.search(r"^\*\*HP\*\* (\d+) \((\d+)d(\d+)(?: ([+−-]) (\d+))?\)", body, re.M)
    if not hp:
        why.append("HP line not 'N (XdY [± Z])'")
    if why:
        return None, why
    assert ac is not None and hp is not None
    modifier = int(hp.group(5) or 0) * (-1 if hp.group(4) in ("−", "-") else 1)
    return [
        # Reuses the accepted ``creature_defense`` family (schema 18), unchanged.
        {
            "family": "creature_defense",
            "armor_class": int(ac.group(1)),
            "hit_points": int(hp.group(1)),
            "hit_point_dice": {
                "count": int(hp.group(2)),
                "die": f"d{hp.group(3)}",
                "modifier": modifier,
            },
        },
        {
            "family": "creature_defensive_profile",
            "sizes": sizes,
            "abilities": scores,
            **{k: sorted(v) for k, v in defenses.items()},
        },
    ], []


def main() -> None:
    raw = ORACLE.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == ORACLE_SHA256, "accepted oracle changed"
    rep = json.loads(raw)["representation"]
    creatures = sorted(
        r["semantic_key"] for r in rep["records"] if r["kind"] == "creature"
    )
    comps = {(c["record_key"], c["semantic_key"]) for c in rep["components"]}
    by_tail: dict[str, list[str]] = {}
    for key in creatures:
        by_tail.setdefault(key.rsplit(".", 1)[1], []).append(key)
    facts, refused, unmatched_blocks = [], [], []
    matched: set[str] = set()
    for b in blocks("monsters-A-Z.md") + blocks("animals.md"):
        tail = slug(b["heading"])
        keys = [
            k
            for k in by_tail.get(tail, [])
            if k.startswith("animals." if b["file"] == "animals.md" else "monsters.")
        ]
        if len(keys) != 1:
            unmatched_blocks.append(
                {
                    "heading": b["heading"],
                    "file": b["file"],
                    "line": b["line"],
                    "candidates": keys,
                }
            )
            continue
        (key,) = keys
        matched.add(key)
        where = {"file": b["file"], "line": b["line"], "heading": b["heading"]}
        typed, why = profile(b)
        if typed is None:
            refused.append({"record_key": key, "source": where, "reasons": why})
            continue
        if (key, tail) not in comps:
            refused.append(
                {
                    "record_key": key,
                    "source": where,
                    "reasons": [f"no accepted component {tail!r} to carry it"],
                }
            )
            continue
        facts += [
            {"record_key": key, "component_key": tail, "fact": fact, "source": where}
            for fact in typed
        ]
    unmatched_records = [k for k in creatures if k not in matched]
    body = {
        "candidate_id": "15c-C1-B",
        "status": "CANDIDATE ONLY - not accepted, recorded, published or activated",
        "proposed_schema": "5d-representation-schema-19 (proposed; not minted)",
        "anchored_oracle_sha256": ORACLE_SHA256,
        "facts": facts,
        "refused": refused,
        "census": {
            "creature_records": len(creatures),
            "unmatched_records": unmatched_records,
            "unmatched_stat_blocks": unmatched_blocks,
        },
    }
    data = (
        json.dumps(body, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode()
    (HERE / "candidate-c1b.json").write_bytes(data)
    print(
        "typed creatures",
        len({f["record_key"] for f in facts}),
        "facts",
        len(facts),
        "refused",
        len(refused),
        "unmatched records",
        len(unmatched_records),
        "unmatched blocks",
        len(unmatched_blocks),
        "sha256",
        hashlib.sha256(data).hexdigest(),
    )


if __name__ == "__main__":
    main()
