"""Placement audit: which affected batch owns each C5 target component.

A component can take new facts only if exactly one affected batch states it
and every accepted provenance claim on it is one that batch's proposal states;
otherwise claim-based excision (excise.py) keeps it and re-acceptance would
conflict.
Writes ../reports/placement.json. Read-only over all inputs.
"""

from __future__ import annotations

import collections
import json

import common as c


def targets() -> dict[tuple[str, str], int]:
    out: collections.Counter[tuple[str, str]] = collections.Counter()
    for part in ("c5a.json", "c5c.json"):
        for f in json.loads(c.pinned(c.C5 / part, c.C5_SHA256[part]))["facts"]:
            out[(f["record_key"], f["component_key"])] += 1
    b = json.loads(c.pinned(c.C5 / "c5b.json", c.C5_SHA256["c5b.json"]))
    for r in b["creatures"]:
        out[(r["record_key"], r["defense_component_key"])] += 1
        for e in r["entries"]:
            out[(r["record_key"], e["component_key"])] += 1
    return dict(out)


def main() -> None:
    g = c.g1()
    stated: dict[tuple[str, str], list[str]] = collections.defaultdict(list)
    claims_by: dict[str, set[tuple[str, ...]]] = {}
    for batch in c.AFFECTED:
        rep = c.replayed(batch).proposed_representation
        for comp in rep.components:
            stated[(comp.record_key, comp.semantic_key)].append(batch)
        claims_by[batch] = {(p.target_kind.value, *p.target_key, p.span_id, p.role.value)
                            for p in rep.provenance}
    accepted: dict[tuple[str, str], set[tuple[str, ...]]] = collections.defaultdict(set)
    for p in g["representation"]["provenance"]:
        if p["target_kind"] in ("component", "fact", "prose_binding", "reference"):
            accepted[(p["target_key"][0], p["target_key"][1])].add(
                (p["target_kind"], *p["target_key"], p["span_id"], p["role"]))
    rows, problems = [], []
    for key, n in sorted(targets().items()):
        owners = stated.get(key, [])
        unowned = (sorted(accepted[key] - claims_by[owners[0]]) if len(owners) == 1
                   else sorted(accepted[key]))
        row = {"record_key": key[0], "component_key": key[1], "c5_items": n,
               "stated_by": owners, "claims": len(accepted[key]),
               "claims_not_stated_by_owner": len(unowned)}
        rows.append(row)
        if len(owners) != 1 or unowned:
            problems.append({**row, "examples": [list(u) for u in unowned[:3]]})
    by_batch = collections.Counter(r["stated_by"][0] for r in rows if len(r["stated_by"]) == 1)
    report = {"rule": "a target component takes new facts only if exactly one affected "
                      "proposal states it and every accepted provenance claim on it (and on "
                      "its prose bindings, facts and references) is one that proposal states",
              "targets": len(rows), "by_owning_batch": dict(sorted(by_batch.items())),
              "problems": problems}
    out = c.NATIVE / "reports" / "placement.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(report, indent=1, sort_keys=True) + "\n", "utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "problems"}, indent=1))
    print("problems", len(problems))
    for p in problems[:15]:
        print(p)


if __name__ == "__main__":
    main()
