"""Source-derived SRD equipment catalogue check (CRD Issue 2b G1).

Derives the expected catalogue from the sources alone, never from an accepted
artifact or the generator: every Weapons-table row with the category its group
row prints and the mastery its Mastery column prints, every Armor-table row,
and every Ammunition-table row. It reads the qualified pinned Markdown, and the
official SRD 5.2.1 PDF as the cross-check. The mastery vocabulary is read from
the Markdown's own *Mastery Properties* definitions.

It then judges any accepted-inputs artifact against that catalogue: a missing
identity, a weapon without exactly one category fact and one mastery fact, or
a fact that disagrees with the source is reported by name. Counts in the
artifact are never consulted.

Usage: ``source_catalogue_check.py ARTIFACT [ARTIFACT ...]``; writes
``reports/source-catalogue-check.json``. Exit 1 if the sources disagree or any
artifact named with ``--expect-clean`` has a finding.
"""

from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

REPO = Path.cwd()
MD = REPO / "docs/sources/community/dnd-5e-srd-markdown/equipment.md"
PDF = REPO / "docs/sources/DnD5_5e_SRD_CC_v5_2_1.pdf"
HERE = REPO / ".claude/review-notes/issue-2b-g1-candidate"


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower().replace("'", "")).strip("_")


def md_table(text: str, caption: str) -> list[list[str] | str]:
    """Rows of the HTML table printed after ``**caption**``: a group row as its
    text, a data row as its cells."""
    start = text.index(f"**{caption}**")
    body = text[text.index("<table>", start) : text.index("</table>", start)]
    rows: list[list[str] | str] = []
    for tr in re.findall(r"<tr>(.*?)</tr>", body, re.S):
        if "<th colspan" in tr:
            rows.append(html.unescape(re.sub(r"<[^>]+>", "", tr)).strip())
        elif "<td>" in tr:
            rows.append(
                [html.unescape(c).strip() for c in re.findall(r"<td>(.*?)</td>", tr, re.S)]
            )
    return rows


def markdown_catalogue() -> dict[str, object]:
    text = MD.read_text("utf-8")
    section = text[text.index("### Mastery Properties") :]
    section = section[: section.index("\n## ")]
    masteries = re.findall(r"^\*\*(\w+)\.\*\*", section, re.M)
    weapons: dict[str, dict[str, str]] = {}
    group = ""
    for row in md_table(text, "Weapons"):
        if isinstance(row, str):
            group = row
            continue
        name, mastery = row[0], row[3]
        assert mastery in masteries, (name, mastery)
        category = group.split()[0].lower()
        assert category in ("simple", "martial"), group
        weapons[slug(name)] = {"name": name, "category": category, "mastery": mastery.lower()}
    armor = {
        slug(r[0]): r[0] for r in md_table(text, "Armor") if not isinstance(r, str)
    }
    ammunition = {
        slug(r[0]): r[0]
        for r in md_table(text, "Ammunition")
        if not isinstance(r, str)
    }
    gear = {
        slug(r[0]): r[0]
        for r in md_table(text, "Adventuring Gear")
        if not isinstance(r, str)
    }
    return {
        "masteries": [m.lower() for m in masteries],
        "weapons": weapons,
        "armor": armor,
        "ammunition": ammunition,
        "adventuring_gear_rows": gear,
    }


def pdf_catalogue(masteries: list[str]) -> dict[str, object]:
    import pdfplumber

    weapon_text = armor_text = ammo_text = ""
    with pdfplumber.open(PDF) as pdf:
        for page in pdf.pages:
            t = page.extract_text() or ""
            if "Martial Ranged Weapons" in t and "Simple Melee Weapons" in t:
                weapon_text = t
            if "Light Armor (1 Minute to Don or Doff)" in t:
                armor_text = t
            if "Needles" in t and "Bullets, Sling" in t:
                ammo_text = t
    m_alt = "|".join(m.capitalize() for m in masteries)
    line = re.compile(
        rf"^(?P<name>[A-Z][A-Za-z ]+?) \d+(?:d\d+)? \w+ .*?\b(?P<m>{m_alt}) "
        r"(?:\S+ lb\.|\S) [\d,]+ [A-Z]{2}$"
    )
    weapons: dict[str, dict[str, str]] = {}
    group = ""
    for raw in weapon_text.splitlines():
        s = raw.strip()
        if s.endswith(" Weapons") and s.split()[0] in ("Simple", "Martial"):
            group = s.split()[0].lower()
            continue
        if (m := line.match(s)) and group:
            weapons[slug(m["name"])] = {
                "name": m["name"],
                "category": group,
                "mastery": m["m"].lower(),
            }
    armor_names = re.findall(
        r"^([A-Z][A-Za-z ]+?) (?:\d+|\+2)\b", armor_text, re.M
    )
    return {
        "page_found": {
            "weapons": bool(weapon_text),
            "armor": bool(armor_text),
            "ammunition": bool(ammo_text),
        },
        "weapons": weapons,
        "armor": sorted({slug(n) for n in armor_names}),
        "ammunition_text_has": {
            n: n in ammo_text
            for n in ("Arrows", "Bolts", "Bullets, Firearm", "Bullets, Sling", "Needles")
        },
    }


def judge(artifact: Path, cat: dict[str, object]) -> dict[str, object]:
    doc = json.loads(artifact.read_text("utf-8"))
    rep = doc["representation"]
    records = {r["semantic_key"] for r in rep["records"]}
    facts: dict[str, list[dict[str, object]]] = {}
    for c in rep["components"]:
        for f in c["facts"]:
            if f.get("family") in ("weapon_category", "weapon_mastery"):
                facts.setdefault(c["record_key"], []).append(f)
    missing: list[str] = []
    wrong: list[str] = []
    for kind, prefix in (
        ("weapons", "equipment.weapons."),
        ("armor", "equipment.armor."),
        ("ammunition", "equipment.adventuring_gear."),
    ):
        for s in cat[kind]:  # type: ignore[attr-defined]
            if prefix + s not in records:
                missing.append(prefix + s)
    for s, w in cat["weapons"].items():  # type: ignore[attr-defined]
        key = "equipment.weapons." + s
        got = facts.get(key, [])
        cats = [f["category"] for f in got if f["family"] == "weapon_category"]
        mas = [f["mastery"] for f in got if f["family"] == "weapon_mastery"]
        if cats != [w["category"]]:
            wrong.append(f"{key}: category {cats} != source {w['category']!r}")
        if mas != [w["mastery"]]:
            wrong.append(f"{key}: mastery {mas} != source {w['mastery']!r}")
    stray = sorted(
        k
        for k in facts
        if not k.startswith("equipment.weapons.")
        or k[len("equipment.weapons.") :] not in cat["weapons"]  # type: ignore[operator]
    )
    gear_without_record = sorted(
        s
        for s in cat["adventuring_gear_rows"]  # type: ignore[attr-defined]
        if "equipment.adventuring_gear." + s not in records
    )
    return {
        "artifact": artifact.as_posix(),
        "missing_identities": missing,
        "weapon_fact_findings": wrong,
        "facts_on_non_catalogue_records": stray,
        "clean": not (missing or wrong or stray),
        "informational_adventuring_gear_rows_without_record": gear_without_record,
    }


def main(argv: list[str]) -> int:
    clean_expected = {Path(a) for a in argv if not a.startswith("--")}
    expect = set()
    if "--expect-clean" in argv:
        i = argv.index("--expect-clean")
        expect = {Path(argv[i + 1])}
    md = markdown_catalogue()
    pdf = pdf_catalogue(md["masteries"])  # type: ignore[arg-type]
    agree = {
        "weapons_equal": pdf["weapons"] == md["weapons"],
        "armor_equal": pdf["armor"] == sorted(md["armor"]),  # type: ignore[arg-type]
        "ammunition_in_pdf": all(pdf["ammunition_text_has"].values()),  # type: ignore[attr-defined]
        "pages_found": all(pdf["page_found"].values()),  # type: ignore[attr-defined]
    }
    out = {
        "sources": {"markdown": MD.relative_to(REPO).as_posix(), "pdf": PDF.relative_to(REPO).as_posix()},
        "catalogue_counts": {
            "weapons": len(md["weapons"]),  # type: ignore[arg-type]
            "armor": len(md["armor"]),  # type: ignore[arg-type]
            "ammunition": len(md["ammunition"]),  # type: ignore[arg-type]
            "masteries": md["masteries"],
        },
        "weapons": md["weapons"],
        "markdown_pdf_agreement": agree,
        "pdf_weapons_differing": sorted(
            k
            for k in set(md["weapons"]) | set(pdf["weapons"])  # type: ignore[arg-type]
            if md["weapons"].get(k) != pdf["weapons"].get(k)  # type: ignore[attr-defined]
        ),
        "judgements": [judge(a, md) for a in sorted(clean_expected - expect) + sorted(expect)],
    }
    (HERE / "reports").mkdir(exist_ok=True)
    (HERE / "reports/source-catalogue-check.json").write_text(
        json.dumps(out, indent=1) + "\n", encoding="utf-8"
    )
    for j in out["judgements"]:  # type: ignore[union-attr]
        print(j["artifact"], "clean" if j["clean"] else "FINDINGS",
              len(j["missing_identities"]), len(j["weapon_fact_findings"]))
    print(json.dumps(agree))
    ok = all(agree.values()) and all(
        j["clean"] for j in out["judgements"] if Path(j["artifact"]) in expect  # type: ignore[union-attr]
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
