"""Derive raw candidate C7 (CRD Issue 15c): C6-r2's four Origin feat category
facts, unchanged, consolidated with the ammunition identity and compatibility
facts the Owner directed into this issue (owner-ammunition-inclusion-
2026-10-12.md). REVIEW MATERIAL ONLY: nothing is accepted, minted, recorded
or published. C6, C6-r2, C5, the recorded successor and every pinned source
are digest-checked and only read. Run from the repository root."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

REPO = Path.cwd()
NOTES = REPO / ".claude/review-notes/issue-15c-implementation"
SRC = REPO / "docs/sources/community/dnd-5e-srd-markdown"
PINS = {
    NOTES / "candidate-c6/c6.json": "eb014b30e685543c435930913d00fe8762963c95b0fdcc9ce470c019bbfb554a",  # noqa: E501
    NOTES / "candidate-c6-r2/c6r2.json": "699718ff9bac8298c08fc6da706309819b864b604685c88f462669d68e8923f4",  # noqa: E501
    REPO / "src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-8781d4e0-a3b-15c.json": "23e5d8e0fac60e3f5417b3a41e40e6f475366dd385856f38c42104f4dd264f69",  # noqa: E501
    SRC / "equipment.md": "ba4d96bf7c08a44103b11be1ae5385e6e09f3f5478d56c3a2f38f97bd77d645b",  # noqa: E501
    SRC / "character-creation.md": "1c8f477398cc7ca5721542698d67147f303e4dd5a5dacdad7cb7cec1119f7c42",  # noqa: E501
}

#: The weapon rows that name each kind (equipment.md), as evidence that a
#: supply row's kind is the kind those rows print.
WEAPON_ROWS = {
    "arrow": [("equipment.weapons.shortbow", 231, 233), ("equipment.weapons.longbow", 421, 423)],  # noqa: E501
    "bolt": [
        ("equipment.weapons.light_crossbow", 223, 225),
        ("equipment.weapons.hand_crossbow", 405, 407),
        ("equipment.weapons.heavy_crossbow", 413, 415),
    ],
    "bullet": [
        ("equipment.weapons.sling", 239, 241),
        ("equipment.weapons.musket", 429, 431),
        ("equipment.weapons.pistol", 437, 439),
    ],
    "needle": [("equipment.weapons.blowgun", 397, 399)],
}

#: One supply fact per Ammunition table row (equipment.md:1204-1251).
SUPPLY = [
    # (record, component, table line, quote, kind, for_weapons, interpretations)
    ("equipment.adventuring_gear.arrows", "arrows", 1218, "<td>Arrows</td>", "arrow", None, ["I3"]),  # noqa: E501
    ("equipment.adventuring_gear.bolts", "bolts", 1225, "<td>Bolts</td>", "bolt", None, ["I3"]),  # noqa: E501
    ("equipment.adventuring_gear.needles", "needles", 1246, "<td>Needles</td>", "needle", None, ["I3"]),  # noqa: E501
    (
        "equipment.adventuring_gear.bullets_sling",
        "bullets_sling",
        1239,
        "<td>Bullets, Sling</td>",
        "bullet",
        [("equipment.weapons.sling", "sling")],
        ["I1"],
    ),
    (
        "equipment.adventuring_gear.bullets_firearm",
        "bullets_firearm",
        1232,
        "<td>Bullets, Firearm</td>",
        "bullet",
        [("equipment.weapons.musket", "musket"), ("equipment.weapons.pistol", "pistol")],  # noqa: E501
        ["I2"],
    ),
]

INTERPRETATIONS = {
    "I1": {
        "claim": "Sling bullets are the bullets for the Sling.",
        "evidence": [
            {"file": "equipment.md", "line": 1239, "quote": "Bullets, Sling"},
            {"file": "equipment.md", "line": 241, "quote": "Ammunition (Range 30/120; Bullet)"},  # noqa: E501
        ],
        "basis": "the table row names the Sling; the source states no other link",
    },
    "I2": {
        "claim": "Firearm bullets are the bullets for the Musket and the Pistol.",
        "evidence": [
            {"file": "equipment.md", "line": 1232, "quote": "Bullets, Firearm"},
            {
                "file": "character-creation.md",
                "line": 849,
                "quote": 'the firearms described in "Equipment"',
            },
        ],
        "basis": (
            "the source never labels the Musket or Pistol a firearm; the only "
            "support is character-creation.md's reference to firearms described "
            "in Equipment, whose only gunpowder weapons are those two"
        ),
        "alternative_if_rejected": (
            "the firearm row carries kind bullet with no weapon link; the Musket "
            "and Pistol then have no compatible ammunition item and stay "
            "missing_authority; the Sling is unaffected"
        ),
    },
    "I3": {
        "claim": (
            "An unqualified table row is the ammunition its singular weapon-side "
            "kind names (Arrows - Arrow, Bolts - Bolt, Needles - Needle)."
        ),
        "evidence": [
            {
                "file": "equipment.md",
                "line": 778,
                "quote": "A weapon's description specifies the type of ammunition used by the weapon",  # noqa: E501
            }
        ],
        "basis": "the Ammunition section names the table rows as the types",
    },
}


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> None:
    for path, digest in PINS.items():
        assert sha(path) == digest, path
    lines = {
        name: (SRC / name).read_text("utf-8").splitlines()
        for name in ("equipment.md", "character-creation.md")
    }
    for kind, rows in WEAPON_ROWS.items():
        for _record, name_line, props_line in rows:
            assert f"; {kind.capitalize()})" in lines["equipment.md"][props_line - 1]
            assert "<td>" in lines["equipment.md"][name_line - 1]
    for interp in INTERPRETATIONS.values():
        for ev in interp["evidence"]:  # type: ignore[union-attr]
            assert ev["quote"] in lines[ev["file"]][ev["line"] - 1], ev
    c6r2 = json.loads((NOTES / "candidate-c6-r2/c6r2.json").read_text("utf-8"))
    facts = list(c6r2["facts"])  # byte-identical in content
    for record, component, line, quote, kind, weapons, interps in SUPPLY:
        assert quote in lines["equipment.md"][line - 1], (record, line)
        facts.append(
            {
                "part": "C7-ammunition",
                "record_key": record,
                "component_key": component,
                "fact": {
                    "family": "ammunition_supply",
                    "kind": kind,
                    "for_weapons": (
                        None
                        if weapons is None
                        else [{"record_key": r, "component_key": c} for r, c in weapons]
                    ),
                },
                "source": {"file": "equipment.md", "line": line, "quote": quote},
                "weapon_evidence": [
                    {"record_key": r, "line": p}
                    for r, _n, p in WEAPON_ROWS[kind]
                    if weapons is None or r in {w for w, _ in weapons}
                ],
                "interpretations": interps,
            }
        )
    out = {
        "candidate_id": "15c-C7-consolidated",
        "status": "RAW CANDIDATE ONLY - not accepted, minted, recorded or published",
        "consolidates": {
            "C6-r2": {
                "candidate": c6r2["candidate_id"],
                "sha256": PINS[NOTES / "candidate-c6-r2/c6r2.json"],
            }
        },
        "anchored_successor_sha256": c6r2["anchored_successor_sha256"],
        "schema": {
            "C6-r2 facts": "5d-representation-schema-19 (unchanged)",
            "ammunition facts": "proposed schema 20: one new family, below",
        },
        "proposed_family": {
            "family": "ammunition_supply",
            "value_object": "AmmunitionSupplyFact",
            "fields": {
                "kind": "AmmunitionKind (existing schema-19 vocabulary)",
                "for_weapons": (
                    "tuple[ComponentReference, ...] | None: the weapons the row "
                    "narrows to, when it narrows a shared weapon-side kind; None "
                    "means every weapon whose row names kind"
                ),
            },
            "admitted_on": "the five Ammunition table rows' gear components only",
            "not_represented": [
                "amount per purchase, storage, weight and cost (not needed)",
                "ammunition recovery after a fight (stays the represented "
                "AmmunitionExpenditureFact.recovery; not executed)",
            ],
        },
        "interpretations": INTERPRETATIONS,
        "facts": facts,
    }
    target = NOTES / "candidate-c7/c7.json"
    target.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", "utf-8", newline="\n")
    for path, digest in PINS.items():
        assert sha(path) == digest, path
    print(len(facts), "facts;", target.name, sha(target))


if __name__ == "__main__":
    main()
