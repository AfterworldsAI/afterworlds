"""Independently validate raw candidate C9 against the pinned sources and the
accepted C8 successor. REVIEW MATERIAL ONLY; schema-free (the candidate's
family does not exist in schema 21, which this check also asserts). Run from
the repository root:

    PYTHONIOENCODING=utf-8 venv/Scripts/python.exe \
        .claude/review-notes/issue-15b-contest-authority/candidate-c9/validate_c9.py

Re-reads every cited line rather than trusting the derivation's parser.
Writes ``validation.json``; exits non-zero on any failure.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

from afterworlds.ingestion.mechanical.representation import (
    SKILL_ABILITY,
    FactFamily,
    Skill,
)

REPO = Path.cwd()
HERE = REPO / ".claude/review-notes/issue-15b-contest-authority/candidate-c9"
SRC = REPO / "docs/sources/community/dnd-5e-srd-markdown"
ORACLE = (
    REPO
    / "src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-8781d4e0-a3b-15c-c8.json"  # noqa: E501
)
C8 = "ead7fa9d4fde484098f71221ca5ef82dfb2c82229d8fca80ab5feeb4e4d62d0d"  # noqa: E501  # pragma: allowlist secret
FILES = ("monsters-A-Z.md", "animals.md", "spells.md", "magic-items.md")
#: Display names as the source prints them, for the independent re-parse.
NAMES = {
    s.value: s.value.replace("_", " ").title().replace(" Of ", " of ") for s in Skill
}


def src_line(file: str, line: int) -> str:
    return (SRC / file).read_text("utf-8").splitlines()[line - 1]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    checks: dict[str, dict[str, object]] = {}

    def check(name: str, ok: bool, detail: object = None) -> None:
        checks[name] = {
            "ok": bool(ok),
            **({"detail": detail} if detail is not None else {}),
        }

    raw = {
        n: (HERE / n).read_bytes()
        for n in ("c9.json", "correspondence.json", "inventory.json")
    }
    c9, corr, inv = (
        json.loads(raw[n]) for n in ("c9.json", "correspondence.json", "inventory.json")
    )
    oracle_bytes = ORACLE.read_bytes()
    check("c8_unchanged", sha(oracle_bytes) == C8 == c9["anchored_successor_sha256"])
    pins_ok = all(sha((REPO / p).read_bytes()) == h for p, h in c9["pins"].items())
    check("pins_hold", pins_ok)
    oracle = json.loads(oracle_bytes)
    comps = {
        (c["record_key"], c["semantic_key"]): c
        for c in oracle["representation"]["components"]
    }
    profiles = sorted(
        k
        for k, c in comps.items()
        if any(f["family"] == "creature_size" for f in c["facts"])
    )
    check(
        "schema_21_cannot_carry_family",
        "creature_skills" not in {f.value for f in FactFamily}
        and oracle["representation_schema"]["version"] == "5d-representation-schema-21",
    )
    keys = [(f["record_key"], f["component_key"]) for f in c9["facts"]]
    check(
        "one_fact_per_profile",
        sorted(keys) == profiles and len(keys) == len(set(keys)),
        len(keys),
    )
    kinds = {r["semantic_key"]: r["kind"] for r in oracle["representation"]["records"]}
    check(
        "profiles_are_creature_records",
        all(kinds[k[0]] == "creature" for k in profiles),
    )

    src = {f: (SRC / f).read_text("utf-8").split("\n") for f in FILES}
    bad_shape, bad_quote, bad_absence, reparse = [], [], [], []
    for fact in c9["facts"]:
        body = fact["fact"]
        skills = body["skills"]
        names = [e["skill"] for e in skills]
        if (
            set(body) != {"family", "skills"}
            or body["family"] != "creature_skills"
            or names != sorted(set(names))
            or any(n not in NAMES for n in names)
            or any(
                type(e["bonus"]) is not int or set(e) != {"skill", "ability", "bonus"}
                for e in skills
            )
        ):
            bad_shape.append(fact["record_key"])
        s = fact["source"]
        if skills:
            line = src[s["file"]][s["line"] - 1]
            if line != s["quote"]:
                bad_quote.append(fact["record_key"])
            printed = line.removeprefix("**Skills** ").removesuffix("<br>").strip()
            rendered = {
                f"{NAMES[e['skill']]} {'+' if e['bonus'] >= 0 else '−'}{abs(e['bonus'])}"  # noqa: E501
                for e in skills
            }
            if set(printed.split(", ")) != rendered or len(printed.split(", ")) != len(
                skills
            ):
                reparse.append(fact["record_key"])
        else:
            lo, hi = s["absent_between_lines"]
            block = src[s["file"]][lo - 1 : hi]
            if (
                any(x.startswith("**Skills**") for x in block)
                or not block[0].startswith("**AC** ")
                or src[s["file"]][s["details_line"] - 1] != s["details_quote"]
                or not lo <= s["details_line"] <= hi
                or fact["basis"] != "S1"
            ):
                bad_absence.append(fact["record_key"])
    check("fact_shape_closed_sorted_distinct", not bad_shape, bad_shape)
    check("quotes_match_source_lines", not bad_quote, bad_quote)
    check("independent_reparse_matches", not reparse, reparse)
    check("absence_is_positive_within_extent", not bad_absence, bad_absence)

    every = sorted(
        (f, n + 1)
        for f in FILES
        for n, x in enumerate(src[f])
        if x.startswith("**Skills**")
    )
    cited = sorted(
        (f["source"]["file"], f["source"]["line"])
        for f in c9["facts"]
        if f["fact"]["skills"]
    )
    check(
        "skills_lines_bijective",
        every == cited,
        {"printed": len(every), "cited": len(cited)},
    )
    # No row's stat-block extent contains another row's Skills line.
    leaks = [
        r["record_key"]
        for r in corr
        for f, n in every
        if f == r["file"]
        and r["stat_block_lines"][0] <= n <= r["stat_block_lines"][1]
        and n != r["skills_line"]
    ]
    check("extents_disjoint_on_skills_lines", not leaks, leaks)
    plain = re.compile(
        r"^\*\*Skills\*\* [A-Z][a-z]+( of [A-Z][a-z]+)? [+−]\d+(, [A-Z][a-z]+( of [A-Z][a-z]+)? [+−]\d+)* ?<br>$"  # noqa: E501
    )
    qualified = [f"{f}:{n}" for f, n in every if not plain.match(src[f][n - 1])]
    check("no_qualified_or_parameterized_entries", not qualified, qualified)

    by_key = {(r["record_key"], r["component_key"]): r for r in corr}
    mismatch = [
        f["record_key"]
        for f in c9["facts"]
        if (r := by_key.get((f["record_key"], f["component_key"]))) is None
        or r["skill_count"] != len(f["fact"]["skills"])
        or r["skills_line"]
        != (f["source"].get("line") if f["fact"]["skills"] else None)
        or not r["claim_spans"]
    ]
    check(
        "correspondence_aligned",
        not mismatch and len(corr) == len(c9["facts"]),
        mismatch,
    )
    batch_of = {r["span_id"]: r["batch_id"] for r in oracle["acceptance"]["records"]}
    wrong_batch = [
        r["record_key"]
        for r in corr
        if {batch_of.get(s) for s in r["claim_spans"]} != {r["batch"]}
    ]
    check("claim_spans_in_one_accepted_batch", not wrong_batch, wrong_batch)
    counts = {
        "total_facts": len(c9["facts"]),
        "with_printed_skills": len(cited),
        "empty_skill_lists": len(c9["facts"]) - len(cited),
        "skill_entries": sum(len(f["fact"]["skills"]) for f in c9["facts"]),
    }
    check("inventory_counts", all(inv[k] == v for k, v in counts.items()), counts)
    wrong_pairing = [
        f["record_key"]
        for f in c9["facts"]
        for e in f["fact"]["skills"]
        if e["ability"] != SKILL_ABILITY[Skill(e["skill"])].value
    ]
    check("every_bonus_carries_its_usual_ability", not wrong_pairing, wrong_pairing)
    assassin = next(
        f for f in c9["facts"] if f["record_key"] == "monsters.assassin.assassin"
    )
    check(
        "assassin_acrobatics_is_dexterity_only",
        {"skill": "acrobatics", "ability": "dexterity", "bonus": 7}
        in assassin["fact"]["skills"],
    )
    stale = []
    for name, interp in c9["interpretations"].items():
        for ev in interp.get("evidence", []):
            line = src_line(ev["file"], ev["line"])
            if ev["quote"] not in line:
                stale.append(f"{name}:{ev['file']}:{ev['line']}")
    check("interpretation_quotes_on_cited_lines", not stale, stale)
    held_forms = sorted(r["record_key"] for r in corr if "held" in r["form"])
    check(
        "held_forms_carried_from_c8",
        held_forms == ["monsters.vampires.vampire"],
        held_forms,
    )

    result = {
        "candidate": {n: sha(b) for n, b in raw.items()},
        "checks": checks,
        "all_ok": all(v["ok"] for v in checks.values()),
    }
    out = json.dumps(result, indent=1, ensure_ascii=False, sort_keys=True) + "\n"
    (HERE / "validation.json").write_bytes(out.encode("utf-8"))
    print(f"validation.json {sha(out.encode('utf-8'))} all_ok={result['all_ok']}")
    for name, value in checks.items():
        if not value["ok"]:
            print("FAILED", name, value)
    return 0 if result["all_ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
