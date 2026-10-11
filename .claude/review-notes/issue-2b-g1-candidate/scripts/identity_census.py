"""Identity census of every priced Equipment row (informational, CRD Issue 2b).

For each row of the priced Equipment tables and each tool entry, reports
whether the artifact gives it a record identity, only a component identity on
its section record, or none (a bare cell of a table component, the position
G1's twelve were in). Sources only; no artifact count is consulted.

Usage: ``identity_census.py ARTIFACT``; writes
``reports/identity-census.json``.
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, ".claude/review-notes/issue-2b-g1-candidate/scripts")
from source_catalogue_check import HERE, MD, md_table, slug  # noqa: E402

#: (table caption, section record) for every priced item table.
TABLES = (
    ("Weapons", "equipment.weapons"),
    ("Armor", "equipment.armor"),
    ("Adventuring Gear", "equipment.adventuring_gear"),
    ("Ammunition", "equipment.adventuring_gear"),
    ("Arcane Focuses", "equipment.adventuring_gear"),
    ("Druidic Focuses", "equipment.adventuring_gear"),
    ("Holy Symbols", "equipment.adventuring_gear"),
    ("Mounts and Other Animals", "equipment.mounts_and_vehicles"),
    ("Tack, Harness, and Drawn Vehicles", "equipment.mounts_and_vehicles"),
    ("Airborne and Waterborne Vehicles", "equipment.mounts_and_vehicles"),
)


def main(artifact: Path) -> None:
    text = MD.read_text("utf-8")
    doc = json.loads(artifact.read_text("utf-8"))
    rep = doc["representation"]
    records = {r["semantic_key"] for r in rep["records"]}
    components = {(c["record_key"], c["semantic_key"]) for c in rep["components"]}
    rows: list[tuple[str, str, str]] = []
    for caption, section in TABLES:
        for r in md_table(text, caption):
            if not isinstance(r, str):
                rows.append((caption, section, r[0]))
    tools = text[text.index("#### Artisan's Tools") : text.index("## Adventuring Gear")]
    for name in re.findall(r"^\*\*(.+?) \((?:[\d,]+ [CSG]P|Varies)\)\*\*$", tools, re.M):
        rows.append(("Tools", "equipment.tools", name))
    out: dict[str, list[dict[str, str]]] = {"record": [], "component": [], "none": []}
    for caption, section, name in rows:
        s = slug(name)
        if f"{section}.{s}" in records:
            kind = "record"
        elif (section, s) in components:
            kind = "component"
        else:
            kind = "none"
        out[kind].append({"table": caption, "name": name, "key": f"{section}.{s}"})
    summary = {k: len(v) for k, v in out.items()}
    by_table: dict[str, list[str]] = {}
    for r in out["none"]:
        by_table.setdefault(r["table"], []).append(r["name"])
    result = {
        "artifact": artifact.as_posix(),
        "summary": summary,
        "none_by_table": by_table,
        "rows": out,
    }
    (HERE / "reports").mkdir(exist_ok=True)
    (HERE / "reports/identity-census.json").write_text(
        json.dumps(result, indent=1) + "\n", encoding="utf-8"
    )
    print(json.dumps({"summary": summary, "none_by_table": by_table}, indent=1))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
