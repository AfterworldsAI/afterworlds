"""Normalized semantic comparison of the live oracle and the candidate.

Usage: compare_oracles.py CANDIDATE_JSON OUT_JSON

Normalization maps only release-scoped identities back to the old release: the
six binding coordinates and every prose chunk_id (via the leaf-keyed chunk
maps). Every remaining difference is listed by path pattern (list indices
replaced by '*') with counts and samples, so each can be accounted for.
Lists are compared positionally, so any reordering of records, routes or
destinations would show up as a difference.
"""

import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path.cwd()
SP = REPO / ".claude/_sp/release-order-candidate"
LIVE = REPO / "src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-3fe24ff6-4e3.json"
CAND, OUT = Path(sys.argv[1]), Path(sys.argv[2])
assert not OUT.exists()


def ident(rel: str) -> dict:
    return json.loads((SP / rel / "identity.json").read_text("utf-8"))


def chunks(rel: str) -> dict[str, str]:
    leaves = json.loads((SP / rel / "leaves.json").read_text("utf-8"))
    return {x["leaf_id"]: x["chunk"]["chunk_id"] for x in leaves}


oi, ni = ident("rel-old"), ident("rel-new")
BIND = ["package_uuid", "release_version", "authoritative_source_hash",
        "transform_config_hash", "bundle_root_hash", "persisted_corpus_digest"]
MAP = {ni[k]: oi[k] for k in BIND if ni[k] != oi[k]}
oc, nc = chunks("rel-old"), chunks("rel-new")
MAP.update({nc[k]: oc[k] for k in oc})
mapped: Counter[str] = Counter()


def norm(x):
    if isinstance(x, dict):
        return {norm(k): norm(v) for k, v in x.items()}
    if isinstance(x, list):
        return [norm(v) for v in x]
    if isinstance(x, str) and x in MAP:
        mapped["chunk" if x in nc.values() else "binding"] += 1
        return MAP[x]
    return x


diffs: dict[str, list] = defaultdict(list)
order_only: dict[str, int] = {}
#: Acceptance evidence the candidate replaces with simulated values, and the
#: proposal identities that hash the (rebound) binding and chunk ids.
EVIDENCE = {"reviewer", "accepted_at", "rule", "authorized_by",
            "authorization_reference", "resolved_at", "proposal_identity"}
evidence: dict[str, dict] = defaultdict(lambda: {"count": 0, "old_distinct": set(), "new_distinct": set()})


def canon(x) -> str:
    return json.dumps(x, sort_keys=True, ensure_ascii=False)


def blank(x, path):
    if isinstance(x, dict):
        return {k: ("<evidence>" if k in EVIDENCE else blank(v, f"{path}.{k}")) for k, v in x.items()}
    if isinstance(x, list):
        return [blank(v, f"{path}[*]") for v in x]
    return x


def gather(a, b, path):
    """Accounted evidence differences, joined by each record's stable key."""
    if isinstance(a, dict) and isinstance(b, dict):
        for k in set(a) & set(b):
            if k in EVIDENCE and a[k] != b[k]:
                e = evidence[f"{path}.{k}"]
                e["count"] += 1
                e["old_distinct"].add(a[k])
                e["new_distinct"].add(b[k])
            else:
                gather(a[k], b[k], f"{path}.{k}")
    elif isinstance(a, list) and isinstance(b, list):
        key = next((k for k in ("span_id", "resolution_id", "unit_id", "batch_id")
                    if a and isinstance(a[0], dict) and k in a[0]), None)
        if key and len({x[key] for x in a}) == len(a):
            bi = {x[key]: x for x in b}
            for x in a:
                gather(x, bi.get(x[key]), f"{path}[*]")
        elif len(a) == len(b):
            for x, y in zip(a, b):
                gather(x, y, f"{path}[*]")


def walk(a, b, path):
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            walk(a.get(k, "<absent>"), b.get(k, "<absent>"), f"{path}.{k}")
    elif isinstance(a, list) and isinstance(b, list):
        if a == b:
            return
        ca, cb = sorted(map(canon, a)), sorted(map(canon, b))
        if ca == cb:
            order_only[path] = len(a)
            return
        sa, sb = sorted(a, key=canon), sorted(b, key=canon)
        if len(sa) == len(sb):
            for i, (x, y) in enumerate(zip(sa, sb)):
                walk(x, y, f"{path}[{i}]")
        else:
            diffs[path].append((path, len(a), len(b)))
    elif a != b:
        diffs[re.sub(r"\[\d+\]", "[*]", path)].append((path, a, b))


old = json.loads(LIVE.read_text("utf-8"))
new_raw = json.loads(CAND.read_text("utf-8"))
new = norm(new_raw)
gather(old, new, "$")
walk(blank(old, "$"), blank(new, "$"), "$")
def at(d, path):
    for k in path.removeprefix("$.").split("."):
        d = d[k]
    return d


#: Each order-only collection is held in canonical-payload order in both
#: artifacts, so its order is a function of its (accounted) contents.
canonical_order = {
    path: all([canon(x) for x in at(d, path)] == sorted(canon(x) for x in at(d, path))
              for d in (old, new_raw))
    for path in order_only
}
for path, held in canonical_order.items():
    print(f"  canonical-payload order in both artifacts {held}  {path}")
report = {
    "live": {"path": str(LIVE.relative_to(REPO)), "sha256": hashlib.sha256(LIVE.read_bytes()).hexdigest()},
    "candidate": {"path": str(CAND), "sha256": hashlib.sha256(CAND.read_bytes()).hexdigest()},
    "normalized_identities": dict(mapped),
    "accounted_evidence": {p: {"count": v["count"], "old_distinct": len(v["old_distinct"]),
                               "new_values": sorted(v["new_distinct"])[:3]}
                           for p, v in sorted(evidence.items())},
    "order_only_collections": order_only,
    "order_only_canonically_sorted_in_both": canonical_order,
    "unaccounted_difference_patterns": {
        p: {"count": len(v), "samples": [[s[0], str(s[1])[:160], str(s[2])[:160]] for s in v[:3]]}
        for p, v in sorted(diffs.items())
    },
}
OUT.write_text(json.dumps(report, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print("normalized", dict(mapped))
for p, v in sorted(evidence.items()):
    print(f"  accounted {v['count']:6d}  {p}  old distinct {len(v['old_distinct'])} -> new distinct {len(v['new_distinct'])}")
for p, n in sorted(order_only.items()):
    print(f"  order-only {n:6d}  {p}")
print("unaccounted difference patterns", len(diffs))
for p, v in sorted(diffs.items()):
    print(f"  {len(v):6d}  {p}")
    print(f"          e.g. {str(v[0][1])[:90]!r} -> {str(v[0][2])[:90]!r}")
assert not diffs and all(canonical_order.values())
print("report", OUT, hashlib.sha256(OUT.read_bytes()).hexdigest())
