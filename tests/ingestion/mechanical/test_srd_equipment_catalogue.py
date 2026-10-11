"""Source-derived SRD equipment catalogue check — CRD Issue 2b G1.

The expected catalogue is read from the pinned SRD 5.2.1 Markdown alone: every
Weapons-table row with the category its group row prints and the mastery its
Mastery column prints, every Armor-table row and every Ammunition-table row.
It is never read from an accepted artifact or its counts. The committed
authority must name every row and state exactly the printed facts. The
byte-preserved predecessor is the control: the check must find exactly the
twelve missing identities and every missing weapon fact there, which shows it
detects omissions rather than agreeing with whatever it is given.
"""

from __future__ import annotations

import html
import json
import re
from pathlib import Path
from typing import Any

import pytest

from afterworlds.ingestion.mechanical.oracle import (
    COMMITTED_ORACLE_DIR,
    committed_inputs_for,
    oracle_payload,
)

REPO = Path(__file__).resolve().parents[3]
EQUIPMENT_MD = REPO / "docs/sources/community/dnd-5e-srd-markdown/equipment.md"
PREDECESSOR = COMMITTED_ORACLE_DIR / "srd-5-2-1-corpus-8781d4e0-a3b.json"
PACKAGE = "1299484e-c72d-509b-bd8d-d0169ee1f8d2"
RELEASE = "5.2.1-corpus.8781d4e0-a3b"

G1_IDENTITIES = {
    "equipment.weapons.dart",
    "equipment.weapons.glaive",
    "equipment.weapons.halberd",
    "equipment.weapons.lance",
    "equipment.weapons.maul",
    "equipment.weapons.trident",
    "equipment.weapons.war_pick",
    "equipment.weapons.whip",
    "equipment.weapons.blowgun",
    "equipment.armor.scale_mail",
    "equipment.armor.ring_mail",
    "equipment.adventuring_gear.needles",
}


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower().replace("'", "")).strip("_")


def _table(text: str, caption: str) -> list[list[str] | str]:
    start = text.index(f"**{caption}**")
    body = text[text.index("<table>", start) : text.index("</table>", start)]
    rows: list[list[str] | str] = []
    for tr in re.findall(r"<tr>(.*?)</tr>", body, re.S):
        if "<th colspan" in tr:
            rows.append(html.unescape(re.sub(r"<[^>]+>", "", tr)).strip())
        elif "<td>" in tr:
            rows.append(
                [html.unescape(c).strip() for c in re.findall(r"<td>(.*?)</td>", tr)]
            )
    return rows


def source_catalogue() -> dict[str, Any]:
    text = EQUIPMENT_MD.read_text("utf-8")
    section = text[text.index("### Mastery Properties") :]
    section = section[: section.index("\n## ")]
    masteries = [m.lower() for m in re.findall(r"^\*\*(\w+)\.\*\*", section, re.M)]
    weapons: dict[str, tuple[str, str]] = {}
    group = ""
    for row in _table(text, "Weapons"):
        if isinstance(row, str):
            group = row.split()[0].lower()
            continue
        assert row[3].lower() in masteries, row
        weapons["equipment.weapons." + _slug(row[0])] = (group, row[3].lower())
    armor = {
        "equipment.armor." + _slug(r[0])
        for r in _table(text, "Armor")
        if not isinstance(r, str)
    }
    ammunition = {
        "equipment.adventuring_gear." + _slug(r[0])
        for r in _table(text, "Ammunition")
        if not isinstance(r, str)
    }
    return {
        "masteries": masteries,
        "weapons": weapons,
        "identities": set(weapons) | armor | ammunition,
    }


def judge(representation: dict[str, Any]) -> tuple[set[str], list[str]]:
    """(missing identities, weapon fact findings) of one representation."""
    catalogue = source_catalogue()
    records = {r["semantic_key"] for r in representation["records"]}
    facts: dict[str, list[dict[str, Any]]] = {}
    for c in representation["components"]:
        for f in c["facts"]:
            if f["family"] in ("weapon_category", "weapon_mastery"):
                facts.setdefault(c["record_key"], []).append(f)
    findings: list[str] = []
    for key, (category, mastery) in catalogue["weapons"].items():
        got = facts.pop(key, [])
        cats = [f["category"] for f in got if f["family"] == "weapon_category"]
        mas = [f["mastery"] for f in got if f["family"] == "weapon_mastery"]
        if cats != [category]:
            findings.append(f"{key}: category {cats} != {category!r}")
        if mas != [mastery]:
            findings.append(f"{key}: mastery {mas} != {mastery!r}")
    findings.extend(f"{key}: weapon facts on a non-catalogue record" for key in facts)
    return catalogue["identities"] - records, findings


@pytest.fixture(scope="module")
def committed() -> dict[str, Any]:
    inputs = committed_inputs_for(PACKAGE, RELEASE)
    assert inputs is not None
    payload = oracle_payload(inputs.oracle)
    representation: dict[str, Any] = payload["representation"]  # type: ignore[assignment]
    return representation


def test_the_source_catalogue_is_the_printed_srd_catalogue() -> None:
    catalogue = source_catalogue()
    assert catalogue["masteries"] == [
        "cleave", "graze", "nick", "push", "sap", "slow", "topple", "vex"
    ]  # fmt: skip
    assert len(catalogue["weapons"]) == 38
    categories = {c for c, _ in catalogue["weapons"].values()}
    assert categories == {"simple", "martial"}
    assert catalogue["identities"] >= G1_IDENTITIES


def test_committed_authority_names_every_catalogue_item(
    committed: dict[str, Any],
) -> None:
    missing, _ = judge(committed)
    assert missing == set()


def test_committed_authority_states_every_weapons_printed_facts(
    committed: dict[str, Any],
) -> None:
    _, findings = judge(committed)
    assert findings == []


def test_the_check_detects_the_predecessors_gaps() -> None:
    representation = json.loads(PREDECESSOR.read_text("utf-8"))["representation"]
    missing, findings = judge(representation)
    assert missing == G1_IDENTITIES
    assert len(findings) == 76  # 38 weapons x (category, mastery), all absent


def test_a_wrong_fact_is_detected(committed: dict[str, Any]) -> None:
    mutated = json.loads(json.dumps(committed))
    for c in mutated["components"]:
        if c["record_key"] == "equipment.weapons.whip":
            for f in c["facts"]:
                if f["family"] == "weapon_mastery":
                    f["mastery"] = "vex"
    _, findings = judge(mutated)
    assert findings == ["equipment.weapons.whip: mastery ['vex'] != 'slow'"]
