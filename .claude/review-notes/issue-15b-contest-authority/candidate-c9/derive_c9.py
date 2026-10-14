"""Derive raw candidate C9 (CRD Issue 15b): every accepted creature profile's
printed Skills entry, complete, for generic contests. REVIEW MATERIAL ONLY:
nothing is accepted, minted, recorded or published, and no schema or source
code is changed. The accepted C8 successor and every pinned source are
digest-checked and only read. Run from the repository root:

    PYTHONIOENCODING=utf-8 venv/Scripts/python.exe \
        .claude/review-notes/issue-15b-contest-authority/candidate-c9/derive_c9.py

Writes ``c9.json`` (the candidate), ``correspondence.json`` (one row per
fact: the profile, its stat-block extent, the printed Skills line or its
absence, the claimed spans, the batch) and ``inventory.json``. Byte-identical
across runs.
"""

from __future__ import annotations

import collections
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from afterworlds.ingestion.mechanical.representation import SKILL_ABILITY, Skill

REPO = Path.cwd()
HERE = REPO / ".claude/review-notes/issue-15b-contest-authority/candidate-c9"
SRC = REPO / "docs/sources/community/dnd-5e-srd-markdown"
ORACLE = (
    REPO
    / "src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-8781d4e0-a3b-15c-c8.json"
)
C8_CORRESPONDENCE = (
    REPO / ".claude/review-notes/issue-15c-implementation/candidate-c8/correspondence.json"
)
PINS: dict[Path, str | None] = {
    ORACLE: "ead7fa9d4fde484098f71221ca5ef82dfb2c82229d8fca80ab5feeb4e4d62d0d",  # pragma: allowlist secret
    C8_CORRESPONDENCE: "43589153ee7befe4e46052f0e7fe7db053b5a9a22c3ff8a6b4468e41c9e0ce24",  # pragma: allowlist secret
    SRC / "monsters-A-Z.md": None,
    SRC / "animals.md": None,
    SRC / "spells.md": None,
    SRC / "magic-items.md": None,
    SRC / "monsters.md": None,
    SRC / "rules-glossary.md": None,
}
TEMPLATE_FILES = ("monsters-A-Z.md", "animals.md", "spells.md", "magic-items.md")
SKILLS_LINE = re.compile(r"^\*\*Skills\*\* (?P<list>.+?) ?<br>$")
ENTRY = re.compile(r"^(?P<name>[A-Z][a-z]+(?: of [A-Z][a-z]+)?) (?P<sign>[+−-])(?P<n>\d+)$")

#: Forms, carried from C8's per-template classification. A Shape-Shift that
#: keeps "game statistics ... the same in each form" keeps the Skills entry,
#: a game statistic of the stat block (I2 as accepted in C8, here S2); a form
#: "using that stat block instead" reads its own template; the Vampire's mist
#: form stays held as form state.
FORM_SOURCE = "C8 correspondence `form`, accepted in the C8 successor"

INTERPRETATIONS = {
    "S1": {
        "claim": "A creature profile whose stat block prints no Skills entry is "
        "proficient in no skill: its complete Skills list is empty. An empty "
        "list is a positive source statement, distinct from a missing fact.",
        "evidence": [
            {
                "file": "monsters.md",
                "line": 13,
                "quote": "If a monster lacks those details, entries for them "
                "don't appear.",
            },
            {
                "file": "monsters.md",
                "line": 149,
                "quote": "The Skills entry specifies a monster's skill "
                "proficiencies, if any.",
            },
            {
                "file": "rules-glossary.md",
                "line": 1353,
                "quote": "_Skills._ This entry lists the monster's skill "
                "proficiencies, if any.",
            },
        ],
        "claim_span": "the native stage claims the span holding the stat "
        "block's details lines (Senses/Languages/CR), where the entry would "
        "appear; the raw stage lists the component's existing claim spans, as "
        "C8 did",
    },
    "S2": {
        "claim": "A Shape-Shift keeping game statistics the same in each form "
        "keeps the Skills entry; the bat form likewise. The mist form is held.",
        "evidence": [{"file": "monsters.md", "line": 7, "quote": "skill proficiencies"}],
        "basis": "the same classification C8 accepted for the creature type (I2)",
    },
    "S3": {
        "claim": "A printed skill bonus is the complete check bonus for that "
        "skill. It is recorded as printed and never decomposed into ability "
        "modifier, Proficiency Bonus or Expertise, and nothing is re-added.",
        "evidence": [
            {
                "file": "monsters.md",
                "line": 149,
                "quote": "A skill bonus is the sum of a monster's relevant "
                "ability modifier and its Proficiency Bonus. Other modifiers "
                "might apply.",
            }
        ],
        "basis": "the diagnostic below shows printed totals that exceed "
        "modifier + PB (for example doubled PB); decomposing them would invent "
        "a cause the stat block does not state",
    },
}

HELD = [
    {
        "case": "a Vampire in mist form",
        "why": "carried from C8: the mist paragraph states specific changes and "
        "CreatureState records no current form; the base and bat profiles are "
        "not held",
        "evidence": [{"file": "monsters-A-Z.md", "line": 17726}],
    },
    {
        "case": "a trait or condition that changes a creature's check (Keen "
        "Senses, Sunlight Sensitivity, Disadvantage from a condition)",
        "why": "not part of the Skills entry. Typed traits are existing "
        "creature_roll_modifier facts and conditions existing condition facts; "
        "contest execution must apply or refuse them as it does any "
        "contributor. This candidate types the printed entry only.",
    },
    {
        "case": "a creature under Polymorph, Shapechange or another form-changing "
        "effect, or a summoned form not in the roster",
        "why": "general spell execution is excluded; refuses as an unexecuted "
        "active effect (as in C8)",
    },
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def lines(file: str) -> list[str]:
    return (SRC / file).read_text("utf-8").split("\n")


def block_extent(src: list[str], header_line: int) -> tuple[int, int, int]:
    """(AC line, end line exclusive), 1-based, for the stat block whose italic
    header is at ``header_line``: from its ``**AC**`` line to the next heading
    (its Traits/Actions section or the next entry)."""
    i = header_line  # 0-based index of the line after the header
    while not src[i].startswith("**AC** "):
        assert not src[i].startswith("#"), (header_line, src[i])
        i += 1
    ac = i
    j = ac + 1
    while j < len(src) and not src[j].startswith("#") and not src[j].startswith("**AC** "):
        j += 1
    return ac + 1, j + 1, header_line


def parse_skills(text: str) -> list[dict[str, Any]]:
    out = []
    for raw in text.split(", "):
        m = ENTRY.match(raw.strip())
        assert m, raw
        skill = Skill(m.group("name").lower().replace(" ", "_"))
        sign = 1 if m.group("sign") == "+" else -1
        out.append({"skill": skill.value, "bonus": sign * int(m.group("n"))})
    names = [e["skill"] for e in out]
    assert len(names) == len(set(names)), text
    return sorted(out, key=lambda e: e["skill"])


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
    kinds = {r["semantic_key"]: r["kind"] for r in rep["records"]}
    sized = sorted(
        key
        for key, c in components.items()
        if any(f["family"] == "creature_size" for f in c["facts"])
    )
    assert all(kinds[k[0]] == "creature" for k in sized)
    assert not any(
        f["family"] == "creature_skills" for c in components.values() for f in c["facts"]
    )
    c8_rows = {
        (r["record_key"], r["component_key"]): r
        for r in json.loads(C8_CORRESPONDENCE.read_bytes())
        if r["file"] in TEMPLATE_FILES and r["component_key"] != "effect"
    }
    assert sorted(c8_rows) == sized, sorted(set(c8_rows) ^ set(sized))

    claimed_lines: dict[tuple[str, int], tuple[str, str]] = {}
    facts: list[dict[str, Any]] = []
    corr: list[dict[str, Any]] = []
    diagnostic: collections.Counter[str] = collections.Counter()
    for key in sized:
        row = c8_rows[key]
        src = lines(row["file"])
        assert src[row["line"] - 1] == row["quote"], key
        ac, end, header = block_extent(src, row["line"])
        assert sum(1 for x in src[ac - 1 : end - 1] if x.startswith("**AC** ")) == 1
        found = [
            (n + 1, src[n])
            for n in range(ac - 1, end - 1)
            if src[n].startswith("**Skills**")
        ]
        assert len(found) <= 1, (key, found)
        senses = [
            (n + 1, src[n]) for n in range(ac - 1, end - 1) if src[n].startswith("**Senses**")
        ]
        assert len(senses) == 1, key
        if found:
            line_no, quote = found[0]
            m = SKILLS_LINE.match(quote)
            assert m, quote
            skills = parse_skills(m.group("list"))
            claimed_lines[(row["file"], line_no)] = key
            assert line_no < senses[0][0], key  # the entry precedes Senses
            basis = "direct"
            source = {"file": row["file"], "line": line_no, "quote": quote}
        else:
            skills = []
            basis = "S1"
            source = {
                "file": row["file"],
                "absent_between_lines": [ac, end - 1],
                "details_line": senses[0][0],
                "details_quote": senses[0][1],
            }
        # Diagnostic only (S3): how the printed total relates to the printed
        # ability modifier and the CR line's PB. Never written into a fact.
        pb_line = next((x for x in src[ac - 1 : end - 1] if x.startswith("**CR**")), "")
        pb = re.search(r"PB \+(\d+)", pb_line)
        # The printed modifier where the accepted fact records one, else the
        # score's modifier by the accepted ability-modifier rule.
        mods = {
            f["ability"]: (
                f["modifier"] if f.get("modifier") is not None else (f["score"] - 10) // 2
            )
            for f in components[key]["facts"]
            if f["family"] == "creature_ability_score"
        }
        for entry in skills:
            mod = mods.get(SKILL_ABILITY[Skill(entry["skill"])].value)
            if pb is None or mod is None:
                diagnostic["no printed PB or modifier"] += 1
                continue
            extra = entry["bonus"] - mod
            p = int(pb.group(1))
            diagnostic[
                "modifier + PB"
                if extra == p
                else "modifier + 2 x PB"
                if extra == 2 * p
                else f"other (bonus - modifier - PB = {extra - p:+d})"
            ] += 1
        claim_spans = sorted(
            {
                p["span_id"]
                for p in rep["provenance"]
                if p.get("target_kind") == "fact"
                and (p.get("target_key") or [None])[0] == key[0]
                and (p.get("target_key") or [None, None])[1] == key[1]
            }
        )
        batches = sorted({batch_of[s] for s in claim_spans if s in batch_of})
        assert len(batches) == 1 and batches[0] == row["batch"], (key, batches)
        fact = {"family": "creature_skills", "skills": skills}
        facts.append(
            {
                "record_key": key[0],
                "component_key": key[1],
                "fact": fact,
                "basis": basis,
                "source": source,
            }
        )
        corr.append(
            {
                "record_key": key[0],
                "component_key": key[1],
                "file": row["file"],
                "header_line": header,
                "stat_block_lines": [ac, end - 1],
                "skills_line": found[0][0] if found else None,
                "quote": found[0][1] if found else None,
                "details_line": senses[0][0],
                "claim_spans": claim_spans,
                "batch": batches[0],
                "form": row["form"],
                "skill_count": len(skills),
            }
        )

    # Bijection: every printed Skills line in the template files belongs to
    # exactly one profile's stat block, and no profile holds two.
    every = {
        (file, n + 1)
        for file in TEMPLATE_FILES
        for n, x in enumerate(lines(file))
        if x.startswith("**Skills**")
    }
    assert set(claimed_lines) == every, sorted(every ^ set(claimed_lines))
    assert len(set(claimed_lines.values())) == len(claimed_lines)
    # Every Skills line has the plain "Name +N, ..." shape: no parenthetical,
    # condition or parameter exists to preserve.
    qualifiers = sorted(
        f"{f}:{n}"
        for f, n in every
        if not SKILLS_LINE.match(lines(f)[n - 1])
        or re.search(r"[(;]|\bor\b|\bplus\b|\bPB\b", lines(f)[n - 1])
    )
    assert not qualifiers, qualifiers

    by_batch: dict[str, collections.Counter[str]] = collections.defaultdict(
        collections.Counter
    )
    for row in corr:
        by_batch[row["batch"]]["components"] += 1
        by_batch[row["batch"]]["facts"] += 1
        by_batch[row["batch"]]["with_skills" if row["skill_count"] else "empty"] += 1
    all_batches = sorted({r["batch_id"] for r in oracle["acceptance"]["records"]})
    inventory = {
        "candidate_id": "15b-C9-creature-skills",
        "total_facts": len(facts),
        "with_printed_skills": sum(1 for r in corr if r["skill_count"]),
        "empty_skill_lists": sum(1 for r in corr if not r["skill_count"]),
        "printed_skills_lines": len(every),
        "skill_entries": sum(r["skill_count"] for r in corr),
        "touched_batches": {b: dict(sorted(c.items())) for b, c in sorted(by_batch.items())},
        "untouched_batch_count": len(set(all_batches) - set(by_batch)),
        "diagnostic_printed_total_vs_modifier_and_pb": dict(sorted(diagnostic.items())),
        "why": "a generic contest participant may be any creature of the story "
        "making any ability check; each profile needs its complete printed "
        "Skills entry so a listed skill uses its printed total and an "
        "unlisted skill is known to be unlisted",
    }
    candidate = {
        "candidate_id": "15b-C9-creature-skills",
        "status": "RAW CANDIDATE: not accepted, minted, recorded or published",
        "anchored_successor_sha256": PINS[ORACLE],
        "schema": {
            "proposed_version": "5d-representation-schema-22",
            "family": "creature_skills",
            "plan": "schema-22-delta.md",
        },
        "pins": {str(p.relative_to(REPO)).replace("\\", "/"): h for p, h in PINS.items()},
        "interpretations": INTERPRETATIONS,
        "held": HELD,
        "form_source": FORM_SOURCE,
        "facts": facts,
    }
    for name, data in (
        ("c9.json", candidate),
        ("correspondence.json", corr),
        ("inventory.json", inventory),
    ):
        text = json.dumps(data, indent=1, ensure_ascii=False, sort_keys=True) + "\n"
        (HERE / name).write_bytes(text.encode("utf-8"))
        print(name, hashlib.sha256(text.encode("utf-8")).hexdigest())


if __name__ == "__main__":
    main()
