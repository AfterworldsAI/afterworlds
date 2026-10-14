"""Pre-checks that could force a native design change (Advisor list).

1. Entry identity: (entry base name, section) is unique within each component.
2. Redundancy: every dropped duration ``possessor`` and every "Grappled by
   the X" collapsed into ``target_grappled_by_source`` names the record's own
   creature (or a form of it).
3. Absent versus null: no C5 object field is both absent somewhere and an
   explicit null elsewhere *with a different reading*; reported per field so
   each folding is visible.
Writes ../reports/prechecks.json. Read-only.
"""

from __future__ import annotations

import collections
import json
import re

import common as c


def main() -> None:
    b = json.loads(c.pinned(c.C5 / "c5b.json", c.C5_SHA256["c5b.json"]))
    report: dict[str, object] = {}

    # 1. Entry identity
    dupes = []
    for r in b["creatures"]:
        seen = collections.Counter((e["component_key"], e["name"], e["section"])
                                   for e in r["entries"])
        dupes += [{"record": r["record_key"], "key": list(k), "count": n}
                  for k, n in seen.items() if n > 1]
    report["entry_identity_duplicates"] = dupes

    # 2. Redundancy of dropped/collapsed creature nouns
    bad = []
    for r in b["creatures"]:
        words = set(re.findall(r"[a-z]+", (r["source"]["heading"] + " " + r["record_key"])
                               .lower()))
        text = " ".join(e["source_text"] for e in r["entries"]).lower()
        for e in r["entries"]:
            for body in (e.get("attack"), e.get("save")):
                if not body:
                    continue
                for eff in (body.get("hit_effect"), body.get("failure_effect")):
                    if eff and eff.get("duration") and "possessor" in eff["duration"]:
                        p = eff["duration"]["possessor"]
                        if p not in words and f"the {p}" not in text:
                            bad.append({"record": r["record_key"], "entry": e["name"],
                                        "possessor": p})
                adv = (body.get("advantage_when") or "") if isinstance(body, dict) else ""
                if m := re.search(r"Grappled by the (\w+)", adv):
                    if m[1].lower() not in words:
                        bad.append({"record": r["record_key"], "entry": e["name"],
                                    "grappled_by": m[1]})
    report["redundancy_violations"] = bad

    # 3. Absent versus null, per (object kind, key)
    present: collections.Counter[tuple[str, str]] = collections.Counter()
    nulls: collections.Counter[tuple[str, str]] = collections.Counter()
    objects: collections.Counter[str] = collections.Counter()

    def walk(o: object, kind: str) -> None:
        if isinstance(o, dict):
            k = o.get("family", kind)
            objects[k] += 1
            for key, v in o.items():
                present[(k, key)] += 1
                if v is None:
                    nulls[(k, key)] += 1
                walk(v, f"{k}.{key}" if not (isinstance(v, dict) and "family" in v) else k)
        elif isinstance(o, list):
            for v in o:
                walk(v, kind)

    for r in b["creatures"]:
        for e in r["entries"]:
            walk({x: y for x, y in e.items() if x not in ("source_text", "source_span")},
                 "entry")
    both = sorted(f"{k}.{key}: present {present[(k, key)]} of {objects[k]}, null "
                  f"{nulls[(k, key)]}" for (k, key) in present
                  if nulls[(k, key)] and present[(k, key)] < objects[k])
    report["absent_and_null_both_occur"] = both
    out = c.NATIVE / "reports" / "prechecks.json"
    out.write_text(json.dumps(report, indent=1) + "\n", "utf-8")
    print(json.dumps(report, indent=1)[:4000])


if __name__ == "__main__":
    main()
