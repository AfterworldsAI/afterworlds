"""Each 2b state vocabulary is exactly what the pinned SRD source prints."""

from __future__ import annotations

import re
from pathlib import Path

from afterworlds.models.dnd5e_vocabulary import (
    Alignment,
    ArmorCategory,
    CreatureType,
    Language,
)

SRD = Path(__file__).resolve().parents[2] / "docs/sources/community/dnd-5e-srd-markdown"


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower().replace("'", "")).strip("_")


def _cells_after(text: str, marker: str) -> list[str]:
    start = text.index(marker)
    body = text[text.index("<table>", start) : text.index("</table>", start)]
    return [c.strip() for c in re.findall(r"<td>([^<]*)</td>", body)]


def test_languages_are_the_standard_and_rare_language_tables() -> None:
    text = (SRD / "character-creation.md").read_text("utf-8")
    standard = [
        c for c in _cells_after(text, "**Standard Languages**") if c[:1].isalpha()
    ]
    rare = [
        c.rstrip("*") for c in _cells_after(text, "**Rare Languages**") if c.strip()
    ]
    printed = {_slug(c) for c in standard + rare}
    assert printed == {m.value for m in Language}


def test_alignments_are_the_nine_printed_plus_unaligned() -> None:
    text = (SRD / "character-creation.md").read_text("utf-8")
    nine = re.findall(r"^_([A-Z][a-z]+(?: [A-Z][a-z]+)?) \([A-Z]{1,2}\)\._", text, re.M)
    assert len(nine) == 9
    assert "Unaligned Creatures" in text
    assert {_slug(n) for n in nine} | {"unaligned"} == {m.value for m in Alignment}


def test_creature_types_are_the_glossary_list() -> None:
    text = (SRD / "rules-glossary.md").read_text("utf-8")
    printed = {_slug(c) for c in _cells_after(text, "#### Creature Type") if c}
    assert printed == {m.value for m in CreatureType}


def test_armor_categories_are_the_armor_table_groups() -> None:
    text = (SRD / "equipment.md").read_text("utf-8")
    start = text.index("**Armor**")
    body = text[start : text.index("</table>", start)]
    groups = re.findall(r'<th colspan="6"><em>(\w+)', body)
    assert {_slug(g) for g in groups} == {m.value for m in ArmorCategory}
