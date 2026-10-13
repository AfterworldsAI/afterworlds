"""Deterministic focused validation of raw candidate C8 (CRD Issue 15c).
Read-only. Run from the repository root after derive_c8.py:

    PYTHONIOENCODING=utf-8 venv/Scripts/python.exe \
        .claude/review-notes/issue-15c-implementation/candidate-c8/validate_c8.py

Writes validation.json.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

REPO = Path.cwd()
HERE = REPO / ".claude/review-notes/issue-15c-implementation/candidate-c8"
SRC = REPO / "docs/sources/community/dnd-5e-srd-markdown"
TYPES = {
    "aberration", "beast", "celestial", "construct", "dragon", "elemental", "fey",
    "fiend", "giant", "humanoid", "monstrosity", "ooze", "plant", "undead",
}  # fmt: skip


def line(file: str, n: int) -> str:
    return (SRC / file).read_text("utf-8").split("\n")[n - 1]


def main() -> None:
    c8 = json.loads((HERE / "c8.json").read_text("utf-8"))
    corr = json.loads((HERE / "correspondence.json").read_text("utf-8"))
    for rel, digest in c8["pins"].items():
        assert hashlib.sha256((REPO / rel).read_bytes()).hexdigest() == digest, rel
    checks: dict[str, object] = {}
    facts = c8["facts"]
    checks["facts"] = len(facts)
    checks["one_fact_per_record"] = len({f["record_key"] for f in facts}) == len(facts)
    checks["quotes_match_cited_lines"] = all(
        line(f["source"]["file"], f["source"]["line"]) == f["source"]["quote"]
        for f in facts
    )
    checks["correspondence_matches_facts"] = [
        (r["record_key"], r["component_key"], r["file"], r["line"], r["quote"])
        for r in corr
    ] == [
        (
            f["record_key"],
            f["component_key"],
            f["source"]["file"],
            f["source"]["line"],
            f["source"]["quote"],
        )
        for f in facts
    ]
    checks["every_row_has_claim_spans_and_one_batch"] = all(
        r["claim_spans"] and r["batch"] for r in corr
    )
    checks["types_in_closed_vocabulary"] = all(
        (f["fact"]["type"] in TYPES and not f["fact"]["type_choice"])
        or (
            f["fact"]["type"] is None
            and len(f["fact"]["type_choice"]) >= 2
            and f["fact"]["type_choice"] == sorted(set(f["fact"]["type_choice"]))
            and set(f["fact"]["type_choice"]) <= TYPES
        )
        for f in facts
    )
    checks["type_word_in_quote"] = all(
        (f["fact"]["type"] or "") in f["source"]["quote"].lower()
        and all(t in f["source"]["quote"].lower() for t in f["fact"]["type_choice"])
        for f in facts
    )
    checks["swarms_I1"] = sorted(
        f["record_key"] for f in facts if f["basis"] == "I1"
    )
    checks["type_choices"] = [
        f["record_key"] for f in facts if f["fact"]["type_choice"]
    ]
    checks["species_humanoid"] = sorted(
        f["record_key"]
        for f in facts
        if f["record_key"].startswith("character_origins.")
        and f["fact"]["type"] == "humanoid"
    )
    evidence_ok = []
    for name, interp in c8["interpretations"].items():
        for ev in interp["evidence"]:
            evidence_ok.append(
                (name, ev["file"], ev["line"], ev["quote"] in line(ev["file"], ev["line"]))
            )
    checks["interpretation_evidence_quotes_on_cited_lines"] = all(e[3] for e in evidence_ok)
    checks["interpretation_evidence"] = evidence_ok
    held_lines = [
        (h["case"], ev["file"], ev["line"], line(ev["file"], ev["line"])[:80])
        for h in c8["held"]
        for ev in h.get("evidence", [])
    ]
    checks["held_evidence_lines"] = held_lines
    checks["forms_lines"] = {
        k: line("monsters-A-Z.md", v["line"])[:60] for k, v in c8["forms"].items()
    }
    (HERE / "validation.json").write_text(
        json.dumps(checks, indent=1, sort_keys=True) + "\n", "utf-8", newline="\n"
    )
    bad = [
        k
        for k, v in checks.items()
        if v is False
    ]
    print(json.dumps({k: v for k, v in checks.items() if not isinstance(v, (list, dict))}))
    assert not bad, bad


if __name__ == "__main__":
    main()
