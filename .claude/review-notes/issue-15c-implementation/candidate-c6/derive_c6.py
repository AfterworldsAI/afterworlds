"""Derive raw candidate C6: the feat-category/prerequisite authority admitted
contributing paths consume (CRD Issue 15c). REVIEW MATERIAL ONLY — not
accepted, minted, recorded or published. Run from the repository root.

Every fact's quote is asserted present on its pinned source line; the native
C5 successor and the C1–C5 raw artifacts are read-only and digest-checked.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

REPO = Path.cwd()
SRC = REPO / "docs/sources/community/dnd-5e-srd-markdown"
HERE = REPO / ".claude/review-notes/issue-15c-implementation/candidate-c6"
SUCCESSOR = REPO / "src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-8781d4e0-a3b-15c.json"
SUCCESSOR_SHA256 = "23e5d8e0fac60e3f5417b3a41e40e6f475366dd385856f38c42104f4dd264f69"
C5 = REPO / ".claude/review-notes/issue-15c-implementation/candidate-c5"
C5_SHA256 = {
    "c5a.json": "866f2c132b974ec2c895c269c09fc5de554b881be5a94699faa8c1188b9687c9",
    "c5b.json": "187c041b8de8edcffe16e2c606b11c071b90b438dc3be2c68cb8a1a3a97df3f6",
    "c5c.json": "bb3761b955f06d94665e86eb817f38da16198069fea9c5919fb98d87db476ad4",
}


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def fact(record: str, component: str, payload: dict, file: str, line: int, quote: str,
         part: str) -> dict:
    text = (SRC / file).read_text("utf-8").splitlines()[line - 1]
    assert quote in text, (file, line, quote, text)
    return {"part": part, "record_key": record, "component_key": component,
            "fact": payload, "source": {"file": file, "line": line, "quote": quote}}


def prerequisite(category: str, feature: str | None = None) -> dict:
    return {"family": "feat_prerequisite", "category": category,
            "minimum_character_level": None, "minimum_ability_score": None,
            "requires_feature": feature}


def main() -> None:
    assert sha(SUCCESSOR) == SUCCESSOR_SHA256
    before = {n: sha(C5 / n) for n in C5_SHA256}
    assert before == C5_SHA256
    origin = [("alert", 23), ("magic_initiate", 33), ("savage_attacker", 47), ("skilled", 53)]
    style = [("archery", 87), ("defense", 93), ("great_weapon_fighting", 99),
             ("two_weapon_fighting", 105)]
    facts = [
        fact(f"feats.{k}", "category", prerequisite("origin"), "feats.md", n,
             "_Origin Feat_", "C6-A (schema 19, no vocabulary change)")
        for k, n in origin
    ] + [
        fact(f"feats.{k}", "category", prerequisite("fighting_style", "fighting_style"),
             "feats.md", n, "_Fighting Style Feat (Prerequisite: Fighting Style Feature)_",
             "C6-B (needs schema 20: FeatCategory.fighting_style, "
             "RequiredFeature.fighting_style)")
        for k, n in style
    ]
    choice = {"family": "feat_choice", "count": 1, "count_per_gain": None,
              "category": "fighting_style", "named_feat": None,
              "or_any_feat_whose_prerequisites_are_met": None, "gain_levels": None}
    for record, component, line, quote in (
        ("classes.fighter.fighting_style", "fighting_style", 4715,
         "gain a Fighting Style feat of your choice"),
        ("classes.fighter.champion.additional_fighting_style",
         "additional_fighting_style", 4803, "You gain another Fighting Style feat of your choice."),
        ("classes.paladin.fighting_style", "fighting_style", 5578,
         "You gain a Fighting Style feat of your choice"),
        ("classes.ranger.fighting_style", "fighting_style", 6362,
         "You gain a Fighting Style feat of your choice"),
    ):
        facts.append(fact(record, component, choice, "classes.md", line, quote,
                          "C6-B (needs schema 20: FeatCategory.fighting_style)"))
    out = {"candidate_id": "15c-C6-feat-category",
           "status": "RAW CANDIDATE ONLY - not accepted, minted, recorded or published",
           "anchored_successor_sha256": SUCCESSOR_SHA256, "facts": facts}
    (HERE / "c6.json").write_text(json.dumps(out, indent=1, sort_keys=True) + "\n",
                                  "utf-8", newline="\n")
    assert {n: sha(C5 / n) for n in C5_SHA256} == C5_SHA256
    assert sha(SUCCESSOR) == SUCCESSOR_SHA256
    print(len(facts), "facts; c6.json", sha(HERE / "c6.json"))


if __name__ == "__main__":
    main()
