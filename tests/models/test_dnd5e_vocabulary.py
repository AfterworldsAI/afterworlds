"""Each 2b state vocabulary is exactly what the pinned SRD source prints."""

from __future__ import annotations

import re
from pathlib import Path

from afterworlds.models.dnd5e_vocabulary import (
    ORIGIN_CHOICE_SOURCES,
    Alignment,
    ArmorCategory,
    CreatureType,
    DraconicAncestor,
    ElvenLineage,
    FiendishLegacy,
    GiantAncestry,
    GnomishLineage,
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


def _origins() -> str:
    return (SRD / "character-origins.md").read_text("utf-8")


def _section(text: str, start: str) -> str:
    begin = text.index(start)
    return text[begin : text.index("####", begin)]


def test_draconic_ancestors_are_the_table_dragons() -> None:
    cells = _cells_after(_origins(), "**Draconic Ancestors**")
    assert {_slug(c) for c in cells[0::2]} == {m.value for m in DraconicAncestor}


def test_elven_lineages_and_fiendish_legacies_are_their_table_rows() -> None:
    text = _origins()
    elven = _cells_after(text, "**Elven Lineages**")[0::4]
    fiendish = _cells_after(text, "**Fiendish Legacies**")[0::4]
    assert {_slug(c) for c in elven} == {m.value for m in ElvenLineage}
    assert {_slug(c) for c in fiendish} == {m.value for m in FiendishLegacy}


def test_gnomish_lineages_and_giant_ancestries_are_their_printed_options() -> None:
    text = _origins()
    gnome = re.findall(
        r"\*\*([A-Z]\w+ Gnome)\.\*\*", _section(text, "_Gnomish Lineage._")
    )
    giant = re.findall(
        r"\(([A-Z]\w+ Giant)\)\.\*\*", _section(text, "_Giant Ancestry._")
    )
    assert {_slug(g) for g in gnome} == {m.value for m in GnomishLineage}
    assert {_slug(g) for g in giant} == {m.value for m in GiantAncestry}


def test_each_origin_vocabulary_names_an_accepted_component() -> None:
    from tests.services.dnd5e_state.builders import real_index

    index = real_index()
    for record, component in ORIGIN_CHOICE_SOURCES.values():
        assert index.component(record, component) is not None, (record, component)
