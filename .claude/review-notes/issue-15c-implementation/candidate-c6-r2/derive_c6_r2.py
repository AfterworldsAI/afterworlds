"""Derive raw candidate C6-r2 (CRD Issue 15c): the four Origin feat category
facts of C6-A, unchanged, as the complete revised candidate. REVIEW MATERIAL
ONLY. C6 (eb014b30...) is preserved and read, not rewritten; C5, the recorded
successor and the pinned source are digest-checked. Run from the repository
root."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

REPO = Path.cwd()
NOTES = REPO / ".claude/review-notes/issue-15c-implementation"
C6 = NOTES / "candidate-c6/c6.json"
C6_SHA256 = "eb014b30e685543c435930913d00fe8762963c95b0fdcc9ce470c019bbfb554a"
SUCCESSOR = REPO / "src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-8781d4e0-a3b-15c.json"
SUCCESSOR_SHA256 = "23e5d8e0fac60e3f5417b3a41e40e6f475366dd385856f38c42104f4dd264f69"
FEATS = REPO / "docs/sources/community/dnd-5e-srd-markdown/feats.md"
FEATS_SHA256 = "3894f4a147df40adb8b090825b4c2e3e5ee2c67851aca42305b11f2477bcfbf7"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> None:
    for path, digest in ((C6, C6_SHA256), (SUCCESSOR, SUCCESSOR_SHA256), (FEATS, FEATS_SHA256)):
        assert sha(path) == digest, path
    c6 = json.loads(C6.read_text("utf-8"))
    facts = [f for f in c6["facts"] if f["part"].startswith("C6-A")]
    assert len(facts) == 4 and all(f["fact"]["category"] == "origin" for f in facts)
    lines = FEATS.read_text("utf-8").splitlines()
    for f in facts:
        assert f["source"]["quote"] in lines[f["source"]["line"] - 1]
    out = {
        "candidate_id": "15c-C6-r2-feat-category",
        "status": "RAW CANDIDATE ONLY - not accepted, minted, recorded or published",
        "supersedes_raw": {"candidate": "15c-C6-feat-category", "sha256": C6_SHA256},
        "anchored_successor_sha256": SUCCESSOR_SHA256,
        "schema": "5d-representation-schema-19 (unchanged; no vocabulary change)",
        "facts": [{**f, "part": "C6-r2"} for f in facts],
    }
    target = NOTES / "candidate-c6-r2/c6r2.json"
    target.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", "utf-8", newline="\n")
    assert sha(C6) == C6_SHA256
    print(len(facts), "facts;", target.name, sha(target))


if __name__ == "__main__":
    main()
