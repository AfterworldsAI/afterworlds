"""Old/new release comparison keyed by stable source extent. Read-only.

Every leaf is keyed by leaf_id (= content_id(file, compact_start, compact_end)),
every container by container_id. Any field difference other than the allowed
reading/identity coordinates fails. Exit 0 iff every difference is accounted.
"""

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, "src")
from afterworlds.ingestion.corpus.source_units import CORPUS_FILES  # noqa: E402
from afterworlds.ingestion.corpus.hashing import content_id  # noqa: E402

H = Path(".claude/_sp/release-order-candidate")
OLD_FILES = (
    "legal-information.md", "animals.md", "character-creation.md",
    "character-origins.md", "classes.md", "equipment.md", "feats.md",
    "gameplay-toolbox.md", "magic-items.md", "monsters.md", "monsters-A-Z.md",
    "playing-the-game.md", "rules-glossary.md", "spells.md",
)  # fmt: skip


def load(name: str, rel: str) -> object:
    return json.loads((H / rel / name).read_text(encoding="utf-8"))


io, inw = load("identity.json", "rel-old"), load("identity.json", "rel-new")
assert io["corpus_files"] == list(OLD_FILES) and inw["corpus_files"] == list(CORPUS_FILES)
assert sorted(OLD_FILES) == sorted(CORPUS_FILES) and len(set(CORPUS_FILES)) == 14
lo = {x["leaf_id"]: x for x in load("leaves.json", "rel-old")}
ln = {x["leaf_id"]: x for x in load("leaves.json", "rel-new")}
co = {x["container_id"]: x for x in load("containers.json", "rel-old")}
cn = {x["container_id"]: x for x in load("containers.json", "rel-new")}
ok = True


def check(label: str, cond: bool) -> None:
    global ok
    ok &= bool(cond)
    print(("OK  " if cond else "FAIL"), label)


check("leaf id sets equal (10464)", set(lo) == set(ln) and len(lo) == 10464)
check("container id sets/records identical (2877)", co == cn and len(co) == 2877)
ALLOWED = {"occurrence_index", "page_index"}
changed = Counter()
bad = []
for k, a in lo.items():
    b = ln[k]
    for f in set(a) | set(b):
        if f == "chunk":
            continue
        if a.get(f) != b.get(f):
            changed[f] += 1
            if f not in ALLOWED:
                bad.append((k, f))
    ca, cb = a["chunk"], b["chunk"]
    check_c = (ca is None) == (cb is None)
    if ca is not None and cb is not None:
        for f in ca:
            if ca[f] != cb[f]:
                changed["chunk." + f] += 1
                if f != "chunk_id":
                    bad.append((k, "chunk." + f))
        check_c &= ca["chunk_id"] == content_id("chunk", io["package_uuid"], k)
        check_c &= cb["chunk_id"] == content_id("chunk", inw["package_uuid"], k)
    if not check_c:
        bad.append((k, "chunk-derivation"))
check("only occurrence_index, page_index and chunk_id differ", not bad)
print("changed field counts:", dict(sorted(changed.items())))
# page_index is the file's position in CORPUS_FILES; occurrence is a total order.
check(
    "page_index == file position in each order",
    all(OLD_FILES[a["page_index"]] == CORPUS_FILES[ln[k]["page_index"]] for k, a in lo.items()),
)
for rel, d in (("old", lo), ("new", ln)):
    check(f"{rel} occurrence is 0..n-1", sorted(x["occurrence_index"] for x in d.values()) == list(range(len(d))))
fname = {k: OLD_FILES[a["page_index"]] for k, a in lo.items()}
for f in CORPUS_FILES:
    ks = [k for k in lo if fname[k] == f]
    so = sorted(ks, key=lambda k: lo[k]["occurrence_index"])
    sn = sorted(ks, key=lambda k: ln[k]["occurrence_index"])
    check(f"within-file order preserved {f} ({len(ks)})", so == sn)
seq = [fname[k] for k in sorted(ln, key=lambda k: ln[k]["occurrence_index"])]
runs = [f for i, f in enumerate(seq) if i == 0 or seq[i - 1] != f]
check("new global order runs == official sequence", runs == list(CORPUS_FILES))
moved = sum(lo[k]["occurrence_index"] != ln[k]["occurrence_index"] for k in lo)
fidx = sum(lo[k]["page_index"] != ln[k]["page_index"] for k in lo)
print("units moving globally", moved, "file_index changed", fidx)
chunked = sum(x["chunk"] is not None for x in lo.values())
print("chunks", chunked, "all chunk_ids changed", changed["chunk.chunk_id"] == chunked)
print("locators compared per leaf: identical for", chunked)
print("identity old", {k: v for k, v in io.items() if k not in ("citation_report", "corpus_files")})
print("identity new", {k: v for k, v in inw.items() if k not in ("citation_report", "corpus_files")})
check("citation report identical", io["citation_report"] == inw["citation_report"])
check("authoritative_source_hash unchanged", io["authoritative_source_hash"] == inw["authoritative_source_hash"])
print("ALL OK", ok)
raise SystemExit(0 if ok else 1)
