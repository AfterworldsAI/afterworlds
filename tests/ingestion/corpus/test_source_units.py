"""The Markdown front end's units and citations — CRD Issue 5c/5d step 3.

The real source is 1.9 MB across fourteen files and the official PDF takes half
a minute to extract, so the whole-source facts are established once in a
session-scoped fixture and asserted from there; the shape tests use small
hand-written sources, where a wrong answer is visible rather than inferred.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import pytest

from afterworlds.ingestion.corpus.models import LeafType
from afterworlds.ingestion.corpus.pdf_source import PDF_REPO_PATH, extract_pages
from afterworlds.ingestion.corpus.source_citations import (
    ANCHORED,
    INHERITED,
    LOCATED,
    PLACED,
    UNRESOLVED,
    build_report,
    cite_units,
    page_locator,
)
from afterworlds.ingestion.corpus.source_ledger import load_pinned_sources
from afterworlds.ingestion.corpus.source_units import (
    CORPUS_FILES,
    SourceTilingError,
    build_leaves,
    build_structure,
    resolve_container_pages,
)
from afterworlds.ingestion.source.community_compare import (
    CONTENT_FILES,
    PIN_DIR,
    WINDOW,
    markdown_text,
)
from afterworlds.ingestion.source.community_tokens import normalized

ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture(scope="session")
def sources() -> dict[str, str]:
    """The pinned files, decoded exactly as the source qualification read them."""
    return {
        name: (ROOT / PIN_DIR / name).read_text(encoding="utf-8")
        for name in CORPUS_FILES
    }


@pytest.fixture(scope="session")
def structure(sources: dict[str, str]):
    return build_structure(sources)


@pytest.fixture(scope="session")
def pages():
    return extract_pages(ROOT / PDF_REPO_PATH)


@pytest.fixture(scope="session")
def citations(structure, sources: dict[str, str], pages):
    return cite_units(structure, sources, pages)


# ---------------------------------------------------------------------------
# Shape: what a unit is
# ---------------------------------------------------------------------------


def test_a_table_is_one_unit_with_its_caption() -> None:
    """A row without its header means nothing, and a caption names the table."""
    text = (
        "# Spells\n\n"
        "Prose above the table.\n\n"
        "**Spell Preparation by Class**\n\n"
        "<table>\n  <thead>\n    <tr><th>Class</th></tr>\n  </thead>\n"
        "  <tbody>\n    <tr><td>Bard</td></tr>\n  </tbody>\n</table>\n\n"
        "Prose below.\n"
    )
    units = build_structure({"f.md": text}).units
    tables = [u for u in units if u.leaf_type is LeafType.TABLE]
    assert len(tables) == 1
    assert "Spell Preparation by Class" in tables[0].content
    assert "<thead>" in tables[0].content and "</table>" in tables[0].content
    assert [u.leaf_type for u in units] == [
        LeafType.HEADING,
        LeafType.PARAGRAPH,
        LeafType.TABLE,
        LeafType.PARAGRAPH,
    ]


def test_a_table_keeps_the_footnote_that_defines_its_marker() -> None:
    """A starred value means nothing without the rule defining the star."""
    text = (
        "# Magic Items\n\n"
        "**Magic Item Rarities and Values**\n\n"
        "<table>\n  <tbody>\n    <tr><td>Common</td><td>100 GP\\*</td></tr>\n"
        "  </tbody>\n</table>\n\n"
        "\\*Halve the value for a consumable item.\n\n"
        "## Activating a Magic Item\n"
    )
    units = build_structure({"f.md": text}).units
    tables = [u for u in units if u.leaf_type is LeafType.TABLE]
    assert len(tables) == 1
    assert "Magic Item Rarities and Values" in tables[0].content
    assert "Halve the value for a consumable item" in tables[0].content
    assert [u.leaf_type for u in units] == [
        LeafType.HEADING,
        LeafType.TABLE,
        LeafType.HEADING,
    ]


def test_a_list_is_one_unit_and_a_stat_field_group_is_one_unit() -> None:
    text = (
        "# Rules\n\n"
        "- First item\n- Second item\n- Third item\n\n"
        "**AC** 17 **Initiative** +7 (17) <br>\n"
        "**HP** 150 (20d10 + 40) <br>\n"
        "**Speed** 10 ft.\n"
    )
    units = build_structure({"f.md": text}).units
    assert [u.leaf_type for u in units] == [
        LeafType.HEADING,
        LeafType.LIST,
        LeafType.STAT_FIELD,
    ]
    assert units[1].content.count("\n") == 2
    assert "**Speed**" in units[2].content


def test_a_heading_closes_every_section_at_its_own_depth_or_above() -> None:
    """Record ownership is heading depth, which is what the corrections fixed."""
    text = (
        "# Magic Items\n\n"
        "#### Figurine of Wondrous Power\n\n"
        "Item prose.\n\n"
        "##### Giant Fly\n\n"
        "**AC** 12 <br>\n\n"
        "#### Necklace of Adaptation\n\n"
        "Next item prose.\n"
    )
    structure = build_structure({"f.md": text})
    by_line = {u.line: u for u in structure.units}
    assert by_line[7].heading_path == (
        "Magic Items",
        "Figurine of Wondrous Power",
        "Giant Fly",
    )
    # The next `####` closes the `#####` beneath it, so the following item does
    # not inherit the Giant Fly's block.
    assert by_line[13].heading_path == ("Magic Items", "Necklace of Adaptation")


def test_a_separator_carries_no_text_and_becomes_no_unit() -> None:
    units = build_structure({"f.md": "# T\n\n<hr>\n\nReal prose.\n"}).units
    assert [u.leaf_type for u in units] == [LeafType.HEADING, LeafType.PARAGRAPH]


def test_the_attribution_file_produces_attribution_leaves() -> None:
    text = "# Legal Information\n\nThis work includes material from the SRD.\n"
    units = build_structure({"legal-information.md": text}).units
    assert units[1].leaf_type is LeafType.ATTRIBUTION


# ---------------------------------------------------------------------------
# Tiling: the completeness guarantee
# ---------------------------------------------------------------------------


def test_units_tile_every_pinned_file(structure, sources: dict[str, str]) -> None:
    """Concatenated unit text must equal the file's own compacted text.

    This is the whole completeness guarantee: nothing can be dropped, doubled,
    reordered or truncated without breaking the equality. It is asserted here
    over the real 1.9 MB source, not over a fixture.
    """
    for name, text in sources.items():
        units = structure.units_for(name)
        whole = normalized(markdown_text(text)).compact
        rebuilt = "".join(whole[u.compact_start : u.compact_end] for u in units)
        # Separator units carry no characters, so the units' spans are the whole
        # file minus exactly those empty stretches.
        assert rebuilt == whole, name
        assert [u.compact_start for u in units] == sorted(
            u.compact_start for u in units
        ), name


def test_a_build_that_cannot_tile_its_source_refuses(monkeypatch) -> None:
    """A partial corpus is never reported as a complete one.

    The stand-in reduction drops a character from whatever it is handed, so it
    takes one character off the whole file and one off each block: the shape of
    a conversion that is not additive over spans, which is the only way units
    can silently lose or double text.
    """
    import afterworlds.ingestion.corpus.source_units as su

    monkeypatch.setattr(su, "markdown_text", lambda raw: raw[1:])
    with pytest.raises(SourceTilingError, match="do not tile"):
        su.build_structure({"f.md": "# T\n\nalpha\n\nbeta\n"})


def test_the_whole_source_parses_into_coherent_units(structure) -> None:
    kinds = {u.leaf_type for u in structure.units}
    assert LeafType.TABLE in kinds and LeafType.LIST in kinds
    assert LeafType.TABLE_CELL not in kinds and LeafType.LIST_ITEM not in kinds
    assert len(structure.units_for("legal-information.md")) >= 4
    assert all(u.content.strip() for u in structure.units)


def test_every_table_footnote_is_served_with_its_table(structure) -> None:
    """Five corpus tables define a marker in a block below themselves.

    Each is part of its table's unit, not a sibling that merely shares a
    section label, so retrieving the table carries the rule for the star.
    """
    carried: list[tuple[str, str]] = []
    for unit in structure.units:
        body = unit.content.split("\n")
        closes = [i for i, ln in enumerate(body) if ln.strip() == "</table>"]
        if not closes:
            continue
        tail = [ln for ln in body[closes[-1] + 1 :] if ln.strip()]
        if tail:
            carried.append((unit.file, tail[0].strip()))

    assert len(carried) == 5
    assert all(note.lstrip("\\").startswith("*") for _, note in carried)
    assert sorted({file for file, _ in carried}) == [
        "character-creation.md",
        "gameplay-toolbox.md",
        "magic-items.md",
    ]
    notes = " ".join(note for _, note in carried)
    assert "Halve the value for a consumable item" in notes
    assert "Primordial includes the Aquan" in notes


# ---------------------------------------------------------------------------
# Citation
# ---------------------------------------------------------------------------


def test_page_locator_formats_single_ranged_and_scattered_pages() -> None:
    assert page_locator((131,)) == "p. 131"
    assert page_locator((131, 132)) == "pp. 131-132"
    assert page_locator((131, 134)) == "pp. 131, 134"
    assert page_locator(()) == ""


def test_every_unit_is_cited_and_no_body_page_goes_uncited(
    structure, citations, pages
) -> None:
    report = build_report(citations, tuple(p.printed_page for p in pages))
    assert len(citations) == len(structure.units)
    assert report.unresolved == ()
    assert report.uncited_body_pages == ()
    assert report.resolved
    # Page 1 is the licence notice, which the attribution file reproduces; the
    # three-page table of contents is front matter and cites nothing.
    assert 1 in report.cited_pages
    assert set(report.cited_pages).isdisjoint({2, 3, 4})


def test_repeated_headings_are_scoped_by_record_not_by_first_occurrence(
    structure, citations
) -> None:
    """An `Actions` heading appears under hundreds of creatures, on many pages.

    Scoping is what is tested here, and the observable form of it is order: the
    nth creature's Actions heading is cited no earlier than the (n-1)th one's.
    A mapper that attached repeated wording to its first occurrence would
    collapse these onto one page, and a mapper that attached it to whichever
    page happened to match would scatter them out of document order. Neither
    survives a non-decreasing run over the file's own units.
    """
    actions = [
        (structure.units[c.unit_index], c)
        for c in citations
        if structure.units[c.unit_index].content.strip().lstrip("#").strip()
        == "Actions"
    ]
    assert len(actions) > 50
    assert len({c.pages[0] for _u, c in actions}) > 20
    assert all(u.heading_path[-1] == "Actions" for u, _c in actions)
    by_file: dict[str, list[int]] = {}
    for unit, citation in actions:
        by_file.setdefault(unit.file, []).append(citation.pages[0])
    assert len(by_file) > 1
    for file, pages in by_file.items():
        assert pages == sorted(pages), file


def test_multi_page_units_cite_every_page_they_cross(structure, citations) -> None:
    crossing = [c for c in citations if len(c.pages) > 1]
    assert crossing, "the document breaks units across pages"
    for citation in crossing:
        assert citation.locator_value.startswith("pp. ")
        assert list(citation.pages) == sorted(citation.pages)


def test_the_report_counts_every_citation_by_the_mechanism_that_made_it(
    structure, citations, pages
) -> None:
    report = build_report(citations, tuple(p.printed_page for p in pages))
    counts = Counter(c.anchor for c in citations)
    assert set(counts) <= {LOCATED, PLACED, ANCHORED, INHERITED, UNRESOLVED}
    assert (
        report.located,
        report.placed,
        report.anchored,
        report.inherited,
        len(report.unresolved),
    ) == tuple(
        counts[status] for status in (LOCATED, PLACED, ANCHORED, INHERITED, UNRESOLVED)
    )
    assert sum(counts.values()) == report.units
    # Most units are located by their own wording; the rest are inferred, and
    # the report says which rather than reporting one number.
    assert report.located / report.units > 0.8
    assert report.inherited > 0
    payload = report.payload()
    assert {"located", "placed", "anchored", "inherited"} <= set(payload)
    assert "not a proof it is right" in str(payload["statuses_are"])


def test_inherited_citations_are_wording_that_could_not_have_anchored(
    structure, citations
) -> None:
    """*Why* they inherited, measured on the units rather than asserted.

    An anchor is a window of WINDOW characters unique to one official page. A
    unit shorter than the window has none to offer, and a unit the snapshot
    prints verbatim more than once has none that is unique. Those two account
    for the overwhelming majority; the small remainder is wording the official
    pages do not carry character-for-character, which is a snapshot difference
    rather than a mapping failure. Nothing here claims the inherited pages are
    independently established -- the point is that document order is the only
    instrument available for them, which is what the report says.
    """

    key = lambda unit: normalized(markdown_text(unit.content)).compact  # noqa: E731
    occurrences = Counter(key(u) for u in structure.units)
    inherited = [
        structure.units[c.unit_index] for c in citations if c.anchor == INHERITED
    ]
    assert inherited
    unanchorable = sum(
        1 for u in inherited if len(key(u)) < WINDOW or occurrences[key(u)] > 1
    )
    assert unanchorable / len(inherited) > 0.9


def test_citation_is_reproducible(structure, sources, pages) -> None:
    first = cite_units(structure, sources, pages)
    second = cite_units(structure, sources, pages)
    assert first == second


#: The official document's chapter order (Owner decision on the release-order
#: review): the attribution page, then the thirteen chapters as printed.
OFFICIAL_CHAPTER_ORDER = (
    "legal-information.md",
    "playing-the-game.md",
    "character-creation.md",
    "classes.md",
    "character-origins.md",
    "feats.md",
    "equipment.md",
    "spells.md",
    "rules-glossary.md",
    "gameplay-toolbox.md",
    "magic-items.md",
    "monsters.md",
    "monsters-A-Z.md",
    "animals.md",
)


def test_the_release_reads_the_files_in_the_official_chapter_order(
    structure,
) -> None:
    """The reading order is the official chapter order, every file once.

    The pinned loader hands the files to the parser in this order, and each
    file's units form one contiguous run at its position, so the global
    ``occurrence_index`` the readers sort on follows the printed document:
    Monsters' governing rules before Monsters A-Z, both before Animals.
    """
    assert CORPUS_FILES == OFFICIAL_CHAPTER_ORDER
    assert len(set(CORPUS_FILES)) == len(CORPUS_FILES)
    assert set(CORPUS_FILES) == {"legal-information.md", *CONTENT_FILES}
    assert tuple(load_pinned_sources(ROOT)) == CORPUS_FILES
    files = [u.file for u in structure.units]
    runs = [f for i, f in enumerate(files) if i == 0 or files[i - 1] != f]
    assert runs == list(CORPUS_FILES)
    assert all(u.file_index == CORPUS_FILES.index(u.file) for u in structure.units)


def test_leaf_occurrence_index_is_the_global_emission_order(
    structure, citations
) -> None:
    """Reconstruction restores canonical chunk order by sorting on this field.

    ``persistence._load_members`` sorts the rebuilt chunks by their first leaf's
    ``occurrence_index``, so anything short of a total order over the leaves
    silently reorders the rebuilt corpus and moves ``bundle_root_hash`` away from
    the one the release was published under. A per-file or per-duplicate counter
    reads plausibly and fails exactly there.
    """
    cited = {c.unit_index: c.pages for c in citations}
    leaves = build_leaves(structure, cited)
    assert [leaf.occurrence_index for leaf in leaves] == list(range(len(leaves)))


def test_leaves_and_containers_carry_the_resolved_citation(
    structure, citations
) -> None:
    cited = {c.unit_index: c.pages for c in citations}
    leaves = build_leaves(structure, cited)
    containers = resolve_container_pages(structure, cited)
    assert len(leaves) == len(structure.units)
    assert len({leaf.leaf_id for leaf in leaves}) == len(leaves)
    assert all(leaf.printed_page > 0 for leaf in leaves)
    assert all(c.printed_page > 0 for c in containers)
    # A leaf's span is its position in its own file's compacted text, and the
    # container path is the heading stack that owns it.
    for leaf in leaves[:200]:
        assert leaf.char_end > leaf.char_start
        assert len(leaf.container_path) == len(set(leaf.container_path))


# ---------------------------------------------------------------------------
# Citation by the unit's own wording: the real relocated, straddled and repeated cases
# ---------------------------------------------------------------------------


def _units(structure, file: str, wording: str) -> list[int]:
    """Indexes of the units in ``file`` whose compact text starts with ``wording``."""
    key = lambda unit: normalized(markdown_text(unit.content)).compact  # noqa: E731
    return [
        i
        for i, u in enumerate(structure.units)
        if u.file == file and key(u).startswith(wording)
    ]


def _cited(structure, citations, file: str, wording: str):
    (index,) = _units(structure, file, wording)
    return citations[index]


@pytest.mark.parametrize(
    ("file", "wording", "page"),
    [
        # Interacting with Objects continues at the top of p.14; Unseen Attackers
        # is the p.14 sidebar. Both were cited to a neighbour's page.
        ("playing-the-game.md", "thegmmightrequireyoutouseanactionforanyofthes", 14),
        ("playing-the-game.md", "unseenattackersandtargetswhenyoumakeanattackr", 14),
        # Rogue Expertise is printed on p.61, before the features table's page.
        ("classes.md", "yougainexpertiseintwoofyourskillproficiencies", 61),
    ],
)
def test_a_unit_printed_on_a_facing_page_is_cited_where_it_is_printed(
    structure, citations, file: str, wording: str, page: int
) -> None:
    citation = _cited(structure, citations, file, wording)
    assert citation.pages == (page,)
    assert citation.anchor == LOCATED


@pytest.mark.parametrize(
    ("wording", "page"),
    [
        ("travelersinwagons,carriages,orotherlandvehicl", 12),
        ("playingonagridifyouplayusingasquaregridandmin", 13),
        ("duringyourmove,youcanmountacreaturethatiswith", 15),
    ],
)
def test_a_window_straddling_into_the_next_unit_adds_no_page(
    structure, citations, wording: str, page: int
) -> None:
    """The legacy partition cites these one page further, from a window whose
    in-unit part is the last one or two characters (``e.``, ``.``)."""
    citation = _cited(structure, citations, "playing-the-game.md", wording)
    assert citation.pages == (page,)


def test_a_unit_shorter_than_a_window_is_never_certified_by_one(
    structure, citations
) -> None:
    key = lambda unit: normalized(markdown_text(unit.content)).compact  # noqa: E731
    short = [c for c in citations if len(key(structure.units[c.unit_index])) < WINDOW]
    assert short
    assert all(c.anchor != ANCHORED for c in short)


@pytest.mark.parametrize(
    ("file", "wording", "expected"),
    [
        (
            "character-creation.md",
            "abilityscoresandbackgroundsabilitybackgrounds",
            (19, 20),
        ),
        ("classes.md", "spellslots.thesorcererfeaturestableshowshowma", (64, 65)),
    ],
)
def test_a_unit_that_crosses_a_page_still_cites_both(
    structure, citations, file: str, wording: str, expected: tuple[int, ...]
) -> None:
    assert _cited(structure, citations, file, wording).pages == expected


@pytest.mark.parametrize(
    ("file", "wording", "expected"),
    [
        ("animals.md", "amphibious.thefrogcanbreatheairandwater.", [(349,), (351,)]),
        (
            "spells.md",
            "thecreatureisanallytoyouandyourallies.incomba",
            [(135, 136), (166,)],
        ),
        (
            "spells.md",
            "thetargetislimitedintheactionsitcanperformbyt",
            [(153, 154), (170,)],
        ),
    ],
)
def test_repeated_wording_takes_its_own_printing(
    structure, citations, file: str, wording: str, expected: list[tuple[int, ...]]
) -> None:
    found = [citations[i] for i in _units(structure, file, wording)]
    assert [c.pages for c in found] == expected
    assert all(c.anchor == LOCATED for c in found)


def test_repeated_wording_the_bounds_cannot_separate_is_not_guessed(
    structure, citations
) -> None:
    # Undead Fortitude is printed on both p.343 and p.344; the armor-training
    # rule is reprinted in the glossary far from p.92. Neither may adopt a page
    # from one printing, so both stay order-placed and say so.
    zombie = citations[
        _units(
            structure,
            "monsters-A-Z.md",
            "undeadfortitude.ifdamagereducesthezombieto0hi",
        )[0]
    ]
    armor = _cited(
        structure,
        citations,
        "equipment.md",
        "light,medium,orheavyarmor.ifyouwearlight,medi",
    )
    assert zombie.anchor == INHERITED
    assert armor == type(armor)(armor.unit_index, (92,), INHERITED)


def test_a_table_the_extraction_reorders_is_placed_by_its_tokens(
    structure, citations
) -> None:
    # The Ability Modifiers table is printed on p.6 only; its numbers are
    # extracted column by column, so no window of it matches any page.
    citation = _cited(
        structure,
        citations,
        "playing-the-game.md",
        "abilitymodifiersscoremodifierscoremodifier151",
    )
    assert citation.pages == (6,)
    assert citation.anchor == PLACED
