"""Derive raw candidate C8 (CRD Issue 15c): the source creature-type
assignments the admitted Ghast and Ghoul Claw target domain needs
(codex-creature-type-boundary-classification.md). REVIEW MATERIAL ONLY:
nothing is accepted, minted, recorded or published; no schema or source
code is changed. The accepted C7 successor and every pinned source are
digest-checked and only read. Run from the repository root:

    PYTHONIOENCODING=utf-8 venv/Scripts/python.exe \
        .claude/review-notes/issue-15c-implementation/candidate-c8/derive_c8.py

Writes ``c8.json`` (the candidate), ``correspondence.json`` (one row per
fact: quote, file:line, record, component, claimed span, batch) and
``inventory.json`` (affected batches and their replay cost). Byte-identical
across runs.
"""

from __future__ import annotations

import collections
import hashlib
import json
import re
from pathlib import Path
from typing import Any

REPO = Path.cwd()
HERE = REPO / ".claude/review-notes/issue-15c-implementation/candidate-c8"
SRC = REPO / "docs/sources/community/dnd-5e-srd-markdown"
ORACLE = (
    REPO
    / "src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-8781d4e0-a3b-15c-c7.json"
)
PINS = {
    ORACLE: "2853f30a832ca581c9d4169b82d0c360f3d6a2d78f0ad8980de9997eef51f373",
    SRC / "monsters-A-Z.md": None,
    SRC / "animals.md": None,
    SRC / "spells.md": None,
    SRC / "magic-items.md": None,
    SRC / "character-origins.md": None,
    SRC / "monsters.md": None,
    SRC / "rules-glossary.md": None,
    SRC / "classes.md": None,
}
TYPES = (
    "aberration beast celestial construct dragon elemental fey fiend giant "
    "humanoid monstrosity ooze plant undead"
).split()
SIZES = "Tiny Small Medium Large Huge Gargantuan".split()
TEMPLATE_FILES = {
    "monsters-A-Z.md": "monsters.",
    "animals.md": "animals.",
    "spells.md": "spells.",
    "magic-items.md": "magic_items.",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def lines(file: str) -> list[str]:
    return (SRC / file).read_text("utf-8").split("\n")


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def stat_blocks(file: str) -> list[dict[str, Any]]:
    """Every stat block (an ``**AC**`` line) with its heading and the
    italic size/type/alignment line under it (the C5 derivation's rule)."""
    src = lines(file)
    out = []
    for i, line in enumerate(src):
        if not line.startswith("**AC** "):
            continue
        j = i - 1
        while not src[j].startswith("#"):
            j -= 1
        header = next(x for x in range(j + 1, i) if src[x].startswith("_"))
        out.append(
            {
                "heading": src[j].lstrip("#").strip(),
                "line": header + 1,
                "quote": src[header],
            }
        )
    return out


HEADER = re.compile(
    rf"^_(?P<size>(?:{'|'.join(SIZES)})(?: or (?:{'|'.join(SIZES)}))?(?: or Smaller)?) "
    r"(?P<type>.+?), (?P<alignment>[A-Za-z ]+)_$"
)
TYPE_PHRASE = re.compile(
    rf"^(?P<type>{'|'.join(t.title() for t in TYPES)})(?: \((?P<tags>[A-Za-z, ]+)\))?$"
)
SWARM = re.compile(
    rf"^Swarm of (?P<of>{'|'.join(SIZES)}) (?P<plural>{'|'.join(t.title() for t in TYPES)})s?$"
)
CHOICE = re.compile(
    r"^(?P<list>[A-Za-z, ]+?),? or (?P<last>[A-Za-z]+) \(Your Choice\)$"
)


def classify(quote: str) -> dict[str, Any]:
    """The type the header prints: a single type (tags stay prose, and their
    absence proves nothing), a swarm's member type (interpretation I1), or a
    chosen type (Find Steed's ``(Your Choice)``)."""
    m = HEADER.match(quote)
    assert m, quote
    phrase = m.group("type")
    if t := TYPE_PHRASE.match(phrase):
        return {"type": t.group("type").lower(), "type_choice": [], "basis": "direct"}
    if s := SWARM.match(phrase):
        return {
            "type": s.group("plural").lower(),
            "type_choice": [],
            "basis": "I1",
        }
    if c := CHOICE.match(phrase):
        names = [n.strip().lower() for n in c.group("list").split(",") if n.strip()]
        names.append(c.group("last").lower())
        assert all(n in TYPES for n in names), names
        return {"type": None, "type_choice": sorted(names), "basis": "direct"}
    raise AssertionError(f"unclassified header {quote!r}")


#: Templates whose effective type a form can change, classified one by one
#: (monsters-A-Z.md Shape-Shift / Form traits).
FORMS = {
    # "game statistics ... are the same in each form" (other than size or
    # Speed): the type is a game statistic, kept in every form (I2).
    "monsters.doppelganger.doppelganger": ("kept", 5202, "I2"),
    "monsters.imp.imp": ("kept", 9940, "I2"),
    "monsters.mimic.mimic": ("kept", 11803, "I2"),
    "monsters.night_hag.night_hag": ("kept", 12252, "I2"),
    "monsters.oni.oni": ("kept", 12649, "I2"),
    "monsters.quasit.quasit": ("kept", 13725, "I2"),
    "monsters.succubus.succubus": ("kept", 16828, "I2"),
    "monsters.werebear.werebear": ("kept", 18142, "I2"),
    "monsters.wereboar.wereboar": ("kept", 18225, "I2"),
    "monsters.wererat.wererat": ("kept", 18308, "I2"),
    "monsters.weretiger.weretiger": ("kept", 18393, "I2"),
    "monsters.werewolf.werewolf": ("kept", 18482, "I2"),
    # "using that stat block instead of this one": the other template's own
    # type applies (its template key changes); nothing to add.
    "monsters.incubus.incubus": ("other_stat_block", 10011, None),
    "monsters.succubus.succubus#form": ("other_stat_block", 16810, None),
    # A bat or a cloud of mist, with no statement about its statistics: the
    # form's type is not stated. HELD: a vampire target refuses until its
    # form is represented.
    "monsters.vampires.vampire": ("held", 17724, None),
}

INTERPRETATIONS = {
    "I1": {
        "claim": "A swarm's creature type is the type of the creatures it is a "
        "swarm of (Swarm of Tiny Beasts: Beast; of Tiny Undead: Undead).",
        "evidence": [
            {"file": "monsters.md", "line": 7, "quote": "creature type"},
            {"file": "animals.md", "line": 6129, "quote": "Swarm of Tiny Beasts"},
        ],
        "basis": "the header line is the creature-type entry (monsters.md:7); no "
        "glossary rule names a swarm type, so the plural noun is read as the type",
    },
    "I2": {
        "claim": "A creature type is among the game statistics a Shape-Shift keeps "
        "'the same in each form'.",
        "evidence": [
            {"file": "monsters.md", "line": 7, "quote": "creature type"},
            {
                "file": "classes.md",
                "line": 3505,
                "quote": "you retain your creature type",
            },
        ],
        "basis": "the stat block states the type with the other game statistics; "
        "Wild Shape, which replaces game statistics, says so explicitly",
    },
}

HELD = [
    {
        "case": "Ghoul Claw against a creature that is not Undead",
        "why": "the rider save excludes Elves; a creature template's header lists "
        "its type and descriptive tags (monsters.md:7, :65-67), but no source "
        "statement makes those tags a statement of species, and a creature "
        "instance records no species. Absence of an Elf tag is not evidence "
        "of not being an Elf (governing instruction). Refuses before any die; "
        "open policy point surfaced with this evidence.",
        "evidence": [
            {"file": "monsters.md", "line": 7},
            {"file": "monsters.md", "line": 65},
            {"file": "monsters.md", "line": 67},
            {"file": "monsters-A-Z.md", "line": 6919},
        ],
    },
    {
        "case": "a vampire target (monsters.vampires.vampire)",
        "why": "its bat or mist form's type is not stated (monsters-A-Z.md:17724) "
        "and the form is not represented; refuses until it is",
    },
    {
        "case": "a creature whose stored creature_type departs from its template's "
        "fixed type (a familiar's chosen type)",
        "why": "the departure's source (a spell or feature) is not represented; "
        "an unvalidated stored type is not trusted: refuses",
    },
    {
        "case": "a creature under Shapechange, Polymorph or another form-changing "
        "spell; a character in Wild Shape",
        "why": "general spell execution is excluded; such effects refuse as "
        "unexecuted active effects. Wild Shape keeps the character's type "
        "(classes.md:3505), so a character's type stays its species type",
    },
]


def main() -> None:
    for path, want in PINS.items():
        got = sha(path)
        if want is not None:
            assert got == want, path
        PINS[path] = got
    oracle = json.loads(ORACLE.read_bytes())
    rep = oracle["representation"]
    batch_of = {r["span_id"]: r["batch_id"] for r in oracle["acceptance"]["records"]}
    components = {(c["record_key"], c["semantic_key"]): c for c in rep["components"]}
    claims: dict[tuple[str, str], list[str]] = collections.defaultdict(list)
    for p in rep["provenance"]:
        key = p.get("target_key") or []
        if p.get("target_kind") == "fact" and len(key) == 3:
            claims[(key[0], key[1])].append(p["span_id"])
    bindings: dict[tuple[str, str], list[str]] = collections.defaultdict(list)
    for b in rep["prose_bindings"]:
        bindings[(b["record_key"], b["component_key"])].append(b["span_id"])

    creatures = sorted(
        r["semantic_key"] for r in rep["records"] if r["kind"] == "creature"
    )
    sized = {
        rk: ck
        for (rk, ck), c in components.items()
        if any(f["family"] == "creature_size" for f in c["facts"])
    }
    by_tail: dict[str, list[str]] = collections.defaultdict(list)
    for key in sized:
        by_tail[key.rsplit(".", 1)[1]].append(key)

    facts: list[dict[str, Any]] = []
    corr: list[dict[str, Any]] = []
    for file, prefix in TEMPLATE_FILES.items():
        for block in stat_blocks(file):
            (key,) = [
                k for k in by_tail[slug(block["heading"])] if k.startswith(prefix)
            ]
            component = sized[key]
            assert lines(file)[block["line"] - 1] == block["quote"]
            typed = classify(block["quote"])
            size_spans = sorted(
                {
                    p["span_id"]
                    for p in rep["provenance"]
                    if p.get("target_kind") == "fact"
                    and (p.get("target_key") or [None])[0] == key
                    and (p.get("target_key") or [None, None])[1] == component
                }
            )
            batches = sorted({batch_of[s] for s in size_spans if s in batch_of})
            assert len(batches) == 1, (key, batches)
            fact = {
                "family": "creature_type",
                "type": typed["type"],
                "type_choice": typed["type_choice"],
            }
            facts.append(
                {
                    "record_key": key,
                    "component_key": component,
                    "fact": fact,
                    "basis": typed["basis"],
                    "source": {
                        "file": file,
                        "line": block["line"],
                        "quote": block["quote"],
                    },
                }
            )
            corr.append(
                {
                    "record_key": key,
                    "component_key": component,
                    "file": file,
                    "line": block["line"],
                    "quote": block["quote"],
                    "claim_spans": size_spans,
                    "batch": batches[0],
                    "form": FORMS.get(key, ("none", None, None))[0],
                }
            )
    # Each classified form trait lies in its own template's stat block.
    starts = sorted(
        (row["line"], row["record_key"])
        for row in corr
        if row["file"] == "monsters-A-Z.md"
    )
    for name, (_, at, _) in FORMS.items():
        owner = max((s for s in starts if s[0] <= at), default=(0, ""))[1]
        assert owner == name.split("#")[0], (name, at, owner)
    assert {f["record_key"] for f in facts} == set(sized), sorted(
        set(sized) ^ {f["record_key"] for f in facts}
    )
    assert set(sized) <= set(creatures)

    src = lines("character-origins.md")
    species = sorted(
        r["semantic_key"] for r in rep["records"] if r["kind"] == "species"
    )
    for n, line in enumerate(src):
        if line != "**Creature Type:** Humanoid":
            continue
        j = n
        while not src[j].startswith("#"):
            j -= 1
        key = f"character_origins.{slug(src[j].lstrip('#'))}"
        assert key in species, key
        assert (key, "creature_type") in components, key
        assert components[(key, "creature_type")]["handling"] == "prose_bound", key
        spans = sorted(bindings[(key, "creature_type")])
        batches = sorted({batch_of[s] for s in spans if s in batch_of})
        assert len(batches) == 1, (key, batches)
        facts.append(
            {
                "record_key": key,
                "component_key": "creature_type",
                "fact": {
                    "family": "creature_type",
                    "type": "humanoid",
                    "type_choice": [],
                },
                "basis": "direct",
                "source": {
                    "file": "character-origins.md",
                    "line": n + 1,
                    "quote": line,
                },
            }
        )
        corr.append(
            {
                "record_key": key,
                "component_key": "creature_type",
                "file": "character-origins.md",
                "line": n + 1,
                "quote": line,
                "claim_spans": spans,
                "batch": batches[0],
                "form": "none",
            }
        )
    assert {
        f["record_key"]
        for f in facts
        if f["record_key"].startswith("character_origins.")
    } == set(species)

    facts.sort(key=lambda f: (f["record_key"], f["component_key"]))
    corr.sort(key=lambda r: (r["record_key"], r["component_key"]))
    per_batch: dict[str, dict[str, Any]] = {}
    for row in corr:
        b = per_batch.setdefault(
            row["batch"], {"components": 0, "facts": 0, "records": []}
        )
        b["components"] += 1
        b["facts"] += 1
        b["records"].append(row["record_key"])
    candidate = {
        "candidate_id": "15c-C8-creature-type",
        "status": "RAW CANDIDATE - review only; not accepted, minted or recorded",
        "anchored_successor_sha256": PINS[ORACLE],
        "schema": {
            "proposed": "5d-representation-schema-21",
            "family": "creature_type",
            "fields": {
                "type": "CreatureType | None (the closed 14-value vocabulary)",
                "type_choice": "tuple[CreatureType, ...] (a chosen type; empty otherwise)",
            },
            "invariant": "exactly one of type / a non-empty sorted, distinct type_choice",
        },
        "facts": facts,
        "interpretations": INTERPRETATIONS,
        "forms": {
            k: {"disposition": v[0], "line": v[1], "interpretation": v[2]}
            for k, v in sorted(FORMS.items())
        },
        "held": HELD,
        "pins": {
            str(p.relative_to(REPO)).replace("\\", "/"): d for p, d in PINS.items()
        },
    }
    inventory = {
        "touched_batches": {
            b: {"components": v["components"], "facts": v["facts"]}
            for b, v in sorted(per_batch.items())
        },
        "untouched_batch_count": len(oracle["acceptance"]["batches"]) - len(per_batch),
        "total_facts": len(facts),
        "why": "Ghast and Ghoul Claw can target any creature or character; each "
        "admitted target needs its source type to decide the Undead exclusion",
    }
    for name, data in (
        ("c8.json", candidate),
        ("correspondence.json", corr),
        ("inventory.json", inventory),
    ):
        (HERE / name).write_text(
            json.dumps(data, indent=1, sort_keys=True) + "\n", "utf-8", newline="\n"
        )
    for path, digest in PINS.items():
        assert sha(path) == digest, path
    print(json.dumps(inventory, indent=1))
    print("c8.json", sha(HERE / "c8.json"))


if __name__ == "__main__":
    main()
