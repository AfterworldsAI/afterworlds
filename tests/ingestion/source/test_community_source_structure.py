"""What the window pass cannot see: cell association, signs, and ownership.

``community_compare`` compares characters after compaction, so it cannot say
whether ``13`` is Chain Shirt's AC or its cost, and it folds a minus sign away
before comparing. Those are the two blind spots its own record names as pending.
This module reads the structures directly instead, which is what closes them:

* a table's rows all fill the same number of columns, so no row is one cell wide
  of the table it belongs to;
* a creature ability row is twelve cells in ``LABEL SCORE MOD SAVE`` order, and
  every modifier follows arithmetically from its score — a check that is blind
  to the glyph by construction, so a swapped pair of cells fails it even when
  both sides hold the same characters;
* the Owner-named regions hold the values the official pages print, in the
  columns those pages put them in;
* the snapshot carries the attribution the licence requires.

These read the pinned Markdown, not the PDF, except the one test that has to
compare against official page 1.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from afterworlds.ingestion.corpus.pdf_source import (
    ExtractedPage,
    PageLine,
)
from afterworlds.ingestion.source import community_compare as cc
from afterworlds.ingestion.source import community_tokens as ct

REPO_ROOT = Path(__file__).resolve().parents[3]
PIN_DIR = REPO_ROOT / cc.PIN_DIR
MANIFEST = json.loads((PIN_DIR / "source_pin.json").read_text(encoding="utf-8"))
# The committed evidence record, so the figures it reports are the figures
# these tests read off the source rather than a number typed once by hand.
RECORD = json.loads(
    (
        REPO_ROOT / "docs/architecture/issue-5c-5d-community-source-coverage.json"
    ).read_text(encoding="utf-8")
)["qualification"]["structure"]

RAW = {name: (PIN_DIR / name).read_text(encoding="utf-8") for name in cc.CONTENT_FILES}

_TABLE = re.compile(r"<table>(.*?)</table>", re.S)
_ROW = re.compile(r"<tr>(.*?)</tr>", re.S)
_CELL = re.compile(r"<t[dh]\b([^>]*)>(.*?)</t[dh]>", re.S)
_COLSPAN = re.compile(r'colspan="(\d+)"')
_TAG = re.compile(r"<[^>]+>")

ABILITIES = ("STR", "DEX", "CON", "INT", "WIS", "CHA")
MINUS = "−"
_SIGNED = re.compile(f"[+{MINUS}-]?" + r"\d+")


def _cells(row_body: str) -> list[str]:
    return [_TAG.sub("", body).strip() for _attrs, body in _CELL.findall(row_body)]


def _line_of(text: str, position: int) -> int:
    return text.count("\n", 0, position) + 1


def _ability_rows() -> list[tuple[str, int, list[str]]]:
    """Every twelve-cell row whose first cell is an ability label."""
    found = []
    for name, text in RAW.items():
        for row in _ROW.finditer(text):
            cells = _cells(row.group(1))
            if len(cells) == 12 and cells[0].upper() in ABILITIES:
                found.append((name, _line_of(text, row.start()), cells))
    return found


# ---------------------------------------------------------------------------
# Table shape and cell association
# ---------------------------------------------------------------------------


def test_every_row_of_every_table_fills_the_same_number_of_columns() -> None:
    """A row one cell wide of its header has lost the column its values sit in.

    This is how the defect showed up: the Bard and Druid feature tables carried
    a sixteenth cell on each of their twenty level rows against a fifteen-column
    header. That cell was empty and it was the last one, so the printed values
    were not displaced — the table's shape was wrong, not the association of any
    value. The check cannot tell those two apart, which is why it is a shape
    check and not an association check, and why the ability-grid tests below
    read cell order and arithmetic separately. Counting ``colspan`` rather than
    tags is the point: a legend spanning four columns fills four, and a row that
    pads with filler instead fails here.
    """
    ragged = []
    tables = 0
    for name, text in RAW.items():
        for table in _TABLE.finditer(text):
            tables += 1
            widths = {
                sum(
                    int(span.group(1)) if (span := _COLSPAN.search(attrs)) else 1
                    for attrs, _body in _CELL.findall(row)
                )
                for row in _ROW.findall(table.group(1))
            }
            if len(widths) > 1:
                ragged.append((name, _line_of(text, table.start()), sorted(widths)))
    assert tables > 500, f"only {tables} tables found; the parse is wrong"
    assert ragged == []
    assert (tables, len(ragged)) == (RECORD["tables"], RECORD["ragged_tables"])


def test_every_ability_row_is_label_score_modifier_save_three_times() -> None:
    """The stat-block grid's shape, with no departure from it.

    A merged or shifted cell in one of these rows moves a number under the wrong
    ability or the wrong quantity while leaving the same characters on the page,
    which is exactly what a character comparison cannot see. The one row the
    official PDF prints unsigned, the Young White Dragon's INT save on p.340,
    carries the official-source-backed ``−2`` (correction family N), so no row is an
    expected exception.
    """
    assert MANIFEST["preserved_official_defects"] == []
    malformed = []
    for name, line, cells in _ability_rows():
        ok = all(
            cells[i].upper() in ABILITIES
            and re.fullmatch(r"\d+", cells[i + 1])
            and _SIGNED.fullmatch(cells[i + 2])
            and _SIGNED.fullmatch(cells[i + 3])
            and cells[i + 2][0] in f"+{MINUS}-"
            and cells[i + 3][0] in f"+{MINUS}-"
            for i in (0, 4, 8)
        )
        if not ok:
            malformed.append((name, line, cells))
    assert malformed == []
    assert RECORD["ability_rows_not_in_label_score_mod_save_shape"] == []


def test_every_modifier_follows_arithmetically_from_its_score() -> None:
    """The check that is blind to the glyph, so it sees a moved cell.

    ``compact`` folds the minus sign and removes it, so ``+2`` and ``-2`` and
    ``2`` all compare equal there. Here the modifier is recomputed from the
    score: a cell moved between columns, a sign inverted, or a digit changed all
    break the arithmetic even though the page still holds the same characters.
    """
    checked = 0
    wrong = []
    for name, line, cells in _ability_rows():
        for i in (0, 4, 8):
            label, score, modifier = cells[i], cells[i + 1], cells[i + 2]
            if not (re.fullmatch(r"\d+", score) and _SIGNED.fullmatch(modifier)):
                continue
            checked += 1
            if int(modifier.replace(MINUS, "-")) != (int(score) - 10) // 2:
                wrong.append((name, line, label, score, modifier))
    assert checked > 2000, f"only {checked} score/modifier pairs read"
    assert wrong == []
    assert checked == RECORD["score_to_modifier_triples"]
    assert RECORD["score_to_modifier_mismatches"] == []


# ---------------------------------------------------------------------------
# Owner-named regression cases, read as values rather than as characters
# ---------------------------------------------------------------------------


def test_the_chain_shirt_row_keeps_each_value_in_its_own_column() -> None:
    """Official p.91: AC 13, +2 Dex cap, 20 lb., 50 GP — four distinct columns.

    The compacted window ``chainshirt1350gp`` matches whether or not the
    snapshot associates 13 with the armour class, which is why this reads cells.
    """
    row = next(
        _cells(r.group(1))
        for r in _ROW.finditer(RAW["equipment.md"])
        if "Chain Shirt" in r.group(1)
    )
    assert row[0].replace("*", "") == "Chain Shirt"
    assert row[1] == "13 + Dex modifier (max 2)"
    assert row[2] == row[3] == "—"  # Strength requirement, Stealth penalty
    assert row[4] == "20 lb."
    assert row[5] == "50 GP"


def test_hold_person_is_a_level_two_spell() -> None:
    """Official p.141. A spell's level is the one number that regrades it."""
    text = RAW["spells.md"]
    start = text.index("\n#### Hold Person\n")
    assert "_Level 2 Enchantment (" in text[start : start + 400]


def _table_after(name: str, caption: str) -> list[list[str]]:
    text = RAW[name]
    table = _TABLE.search(text, text.index(f"\n**{caption}**\n"))
    assert table is not None
    return [_cells(row) for row in _ROW.findall(table.group(1))]


def test_food_drink_and_lodging_pairs_each_item_with_its_own_price() -> None:
    """Official pp.101–102: one ``Item | Cost`` list snaked across sub-columns.

    Read row-major, the conversion paired Ale with Comfortable's inn price and
    swapped the inn and meal prices of the top three lifestyles, keeping every
    character, so only the pairs themselves can show it (correction family I).
    """
    rows = _table_after("equipment.md", "Food, Drink, and Lodging")
    assert rows[0] == ["Item", "Cost"]
    groups, pairs, group = [], {}, ""
    for row in rows[1:]:
        if len(row) == 1:
            group = row[0]
            groups.append(group)
        else:
            pairs[(group, row[0])] = row[1]
    assert groups == ["Inn Stay per Day", "Meal", "Wine (bottle)"]
    assert pairs[("", "Ale (mug)")] == "4 CP"
    assert pairs[("Inn Stay per Day", "Comfortable")] == "8 SP"
    assert pairs[("Inn Stay per Day", "Aristocratic")] == "4 GP"
    assert pairs[("Meal", "Comfortable")] == "2 SP"
    assert pairs[("Meal", "Aristocratic")] == "6 SP"
    assert pairs[("Wine (bottle)", "Fine")] == "10 GP"
    assert len(pairs) == 17


def test_saddle_is_a_group_label_over_its_three_kinds() -> None:
    """Official p.100 sets *Saddle* in italic over Exotic, Military and Riding."""
    rows = _table_after("equipment.md", "Tack, Harness, and Drawn Vehicles")
    at = rows.index(["Saddle"])
    assert [row[0] for row in rows[at + 1 : at + 4]] == [
        "Exotic",
        "Military",
        "Riding",
    ]


def test_the_vehicle_table_carries_the_caption_the_page_prints() -> None:
    """Official p.101 (correction family J)."""
    rows = _table_after("equipment.md", "Airborne and Waterborne Vehicles")
    assert rows[0][0] == "Ship"


def test_the_travel_pace_header_is_the_two_rows_the_page_prints() -> None:
    """Official p.12 (correction family K): no pace row named ``""``."""
    rows = _table_after("playing-the-game.md", "Travel Pace")
    assert rows[0] == ["", "Distance Traveled Per …"]
    assert rows[1] == ["Pace", "Minute", "Hour", "Day"]
    assert [row[0] for row in rows[2:]] == ["Fast", "Normal", "Slow"]


def test_archelon_and_baboon_are_separate_creature_headings() -> None:
    """Official pp.344–345. Two stat blocks merged into one loses a record.

    Adjacent stat blocks read as one continuous stream after compaction, so the
    heading is the only thing that says where one creature's traits stop.
    """
    text = RAW["animals.md"]
    assert "\n## Archelon\n" in text
    assert "\n## Baboon\n" in text
    assert text.index("\n## Archelon\n") < text.index("\n## Baboon\n")


def test_every_skill_names_the_ability_it_uses() -> None:
    """Official p.13: eighteen skills, each bound to one ability.

    A skill under the wrong ability is a rules error that leaves the page's
    characters untouched.
    """
    text = RAW["playing-the-game.md"]
    table = _TABLE.search(text, text.index("<td>Acrobatics</td>") - 2000)
    assert table is not None
    rows = [_cells(r) for r in _ROW.findall(table.group(1))]
    assert rows[0] == ["Skill", "Ability", "Example Uses"]
    body = rows[1:]
    assert len(body) == 18, [r[0] for r in body]
    skills = {r[0]: r[1] for r in body}
    assert skills["Perception"] == "Wisdom"
    assert skills["Acrobatics"] == "Dexterity"
    assert skills["Deception"] == "Charisma"


# ---------------------------------------------------------------------------
# Record ownership: which entry a heading and its prose belong to
# ---------------------------------------------------------------------------


_MD_HEADING = re.compile(r"^(#{1,6})[ \t]+(.*)$", re.M)

#: The en dash the source spells "Magic Items A-Z" with, written as an escape so
#: that the expectation reads the same in any editor as it does on disk.
DASH = "–"
MAGIC_ITEMS_AZ = ["Magic Items", f"Magic Items A{DASH}Z"]


def _headings(text: str) -> list[tuple[int, int, str]]:
    """``(line, depth, title)`` for every Markdown heading, in file order."""
    return [
        (_line_of(text, m.start()), len(m.group(1)), m.group(2).strip())
        for m in _MD_HEADING.finditer(text)
    ]


def _owners(text: str, line: int) -> list[str]:
    """The heading stack that owns *line*, outermost first.

    A heading at depth N closes every open section at depth N or deeper, so this
    is the whole of what Markdown says about which record a line belongs to. A
    heading line is owned by the stack above it rather than by itself.
    """
    stack: list[tuple[int, str]] = []
    for at, depth, title in _headings(text):
        if at > line:
            break
        while stack and stack[-1][0] >= depth:
            stack.pop()
        if at == line:
            return [t for _depth, t in stack]
        stack.append((depth, title))
    return [t for _depth, t in stack]


def _stat_blocks(text: str) -> list[tuple[int, int, str]]:
    """Headings whose own body, up to the next heading, states AC and HP.

    Two marks every stat block carries and no prose paragraph does, which makes
    the set of embedded records findable without a list of their names.
    """
    found = []
    heads = _headings(text)
    lines = text.split("\n")
    for index, (at, depth, title) in enumerate(heads):
        end = heads[index + 1][0] - 1 if index + 1 < len(heads) else len(lines)
        body = "\n".join(lines[at:end])
        if "**AC**" in body and "**HP**" in body:
            found.append((at, depth, title))
    return found


#: Every stat block the source embeds inside an entry that is not itself a
#: creature record, with the entry that summons it and the official page that
#: prints the two together. Written out rather than discovered, so that a block
#: which moves, appears or loses its owner fails here instead of being
#: re-derived into whatever the source happens to say.
EMBEDDED_BLOCKS = (
    ("spells.md", "Animated Object", "Animate Objects", 109),
    ("spells.md", "Otherworldly Steed", "Find Steed", 131),
    ("spells.md", "Giant Insect", "Giant Insect", 136),
    ("spells.md", "Draconic Spirit", "Summon Dragon", 166),
    ("magic-items.md", "Giant Fly", "Figurine of Wondrous Power", 222),
    ("magic-items.md", "Avatar of Death", "Mysterious Deck", 232),
)

#: The files whose records are stat blocks, with the depth each record sits at.
CREATURE_FILES = {"animals.md": 2, "monsters-A-Z.md": 3}

#: Labels a stat block subdivides itself with. They are not document sections.
BLOCK_LABELS = frozenset({"Traits", "Actions", "Bonus Actions", "Reactions"})


def test_the_source_embeds_exactly_the_stat_blocks_this_module_names() -> None:
    """The family is bounded, so a seventh embedded block is a new question.

    Blocks in the creature files are the records themselves and are checked
    separately; every other block is one held inside some other kind of entry.
    """
    found = {
        (name, title)
        for name, text in RAW.items()
        if name not in CREATURE_FILES
        for _at, _depth, title in _stat_blocks(text)
    }
    assert found == {(name, title) for name, title, _owner, _page in EMBEDDED_BLOCKS}


@pytest.mark.parametrize(
    "name,title,owner,_page", EMBEDDED_BLOCKS, ids=lambda value: str(value)
)
def test_an_embedded_stat_block_is_owned_by_the_entry_that_summons_it(
    name: str, title: str, owner: str, _page: int
) -> None:
    """The defect this closes: a block emitted at its owner's depth or above.

    Markdown offers no other ownership mechanism, so a block at the entry's own
    depth does not merely read oddly. It ends the entry, and it takes every
    following entry with it until something at that depth or above appears.
    """
    text = RAW[name]
    at, depth, _title = next(row for row in _stat_blocks(text) if row[2] == title)
    stack = _owners(text, at)
    assert stack[-1] == owner, f"{name}:{at} {title} sits under {stack}"
    _owner_at, owner_depth, _owner_title = next(
        row for row in _headings(text) if row[2] == owner and row[0] < at
    )
    assert depth > owner_depth, f"{title} at depth {depth}, {owner} at {owner_depth}"


@pytest.mark.parametrize("name,depth", sorted(CREATURE_FILES.items()))
def test_a_creature_file_stat_block_is_the_record_itself(name: str, depth: int) -> None:
    """The representative controls, stated as the thing that makes them safe.

    Nothing is embedded in these files: every block is a creature entry at the
    file's own record depth. That is why they never carried the ownership
    defect, and why a block at some other depth here would be news.
    """
    depths = {d for _at, d, _title in _stat_blocks(RAW[name])}
    assert depths == {depth}


#: Entries that directly follow one of the embedded blocks. Each was swallowed
#: by the block before it, and each is a peer of the entry that owns that block.
FIRST_ENTRY_AFTER_A_BLOCK = (
    ("spells.md", "Find the Path", ["Spell Descriptions"]),
    ("spells.md", "Glibness", ["Spell Descriptions"]),
    ("spells.md", "Sunbeam", ["Spell Descriptions"]),
    ("spells.md", "Zone of Truth", ["Spell Descriptions"]),
    ("spells.md", "Antilife Shell", ["Spell Descriptions"]),
    ("magic-items.md", "Flame Tongue", MAGIC_ITEMS_AZ),
    ("magic-items.md", "Necklace of Adaptation", MAGIC_ITEMS_AZ),
    ("magic-items.md", "Necklace of Fireballs", MAGIC_ITEMS_AZ),
    ("magic-items.md", "Wand of Wonder", MAGIC_ITEMS_AZ),
)


@pytest.mark.parametrize(
    "name,title,owners", FIRST_ENTRY_AFTER_A_BLOCK, ids=lambda value: str(value)
)
def test_an_entry_after_a_stat_block_still_belongs_to_its_own_section(
    name: str, title: str, owners: list[str]
) -> None:
    """Zone of Truth is a spell, not part of the Draconic Spirit's Actions."""
    text = RAW[name]
    at = next(row[0] for row in _headings(text) if row[2] == title)
    assert _owners(text, at) == owners


#: Prose the Figurine of Wondrous Power entry prints alongside its embedded
#: block on official p.222. These lines are figurine variants, and no heading
#: may take them from the entry that describes them.
FIGURINE_VARIANTS = (
    "**Golden Lions (Rare).**",
    "**Ivory Goats (Rare).**",
    "**Marble Elephant (Rare).**",
    "**Obsidian Steed (Very Rare).**",
    "**Onyx Dog (Rare).**",
    "**Serpentine Owl (Rare).**",
    "**Silver Raven (Uncommon).**",
)


@pytest.mark.parametrize("opening", FIGURINE_VARIANTS)
def test_a_figurine_variant_belongs_to_the_figurine(opening: str) -> None:
    """Prose ownership, not only heading ownership.

    Official p.222 sets the Giant Fly beside the entry rather than after it, and
    the variants below it are the entry's own text. Markdown has no such inset,
    so the block is carried to the end of the entry and the prose keeps its
    owner. A reader following heading depth reaches the figurine either way.
    """
    text = RAW["magic-items.md"]
    at = _line_of(text, text.index("\n" + opening) + 1)
    assert _owners(text, at) == [*MAGIC_ITEMS_AZ, "Figurine of Wondrous Power"]


@pytest.mark.parametrize(
    "name,title,_owner,_page", EMBEDDED_BLOCKS, ids=lambda value: str(value)
)
def test_a_stat_block_subsection_stays_inside_its_block(
    name: str, title: str, _owner: str, _page: int
) -> None:
    """``Traits`` and ``Actions`` belong to the block, not to the document.

    These labels caused the worst instance of the defect: an ``### Actions``
    under a ``####`` magic item took every remaining item in the file into the
    Avatar of Death's action list.
    """
    text = RAW[name]
    heads = _headings(text)
    # The Giant Insect spell and the Giant Insect it summons share a name, so
    # the block is located as a block rather than by the first matching title.
    block_at, depth, _title = next(row for row in _stat_blocks(text) if row[2] == title)
    start = next(index for index, row in enumerate(heads) if row[0] == block_at)
    for at, sub_depth, sub_title in heads[start + 1 :]:
        if sub_depth <= depth:
            break
        assert sub_title in BLOCK_LABELS
        assert _owners(text, at)[-1] == title


#: The glossary is one flat run of entries under one section heading, which is
#: what makes it the other shape of the same ownership defect: it embeds no stat
#: block, so the scan above cannot see it, and a single entry emitted at the
#: wrong rank there does not read oddly — it closes the run and takes every
#: entry after it. ``### Swim Speed`` did exactly that to the thirteen entries
#: from Target to Weapon Attack and their 47 units before the correction the pin
#: manifest records against official pp.189—191.
GLOSSARY = "rules-glossary.md"
GLOSSARY_ENTRY_OWNERS = ["Rules Glossary", "Rules Definitions"]


def test_every_glossary_entry_is_a_peer_of_every_other() -> None:
    """No entry in the run owns another, whatever rank a future edit gives it.

    Stated as a property of the whole run rather than as the names of the
    thirteen entries that were captured: a rank outlier anywhere in the 155
    fails here, which is the residue the stat-block scan could not have found.
    """
    text = RAW[GLOSSARY]
    run = [
        (at, depth, title)
        for at, depth, title in _headings(text)
        if _owners(text, at)[:2] == GLOSSARY_ENTRY_OWNERS
    ]
    assert run, "the glossary entry run is empty; the file or its sections moved"
    for at, _depth, title in run:
        assert _owners(text, at) == GLOSSARY_ENTRY_OWNERS, (
            f"{GLOSSARY}:{at} {title} is owned by {_owners(text, at)}, so an "
            "entry above it took ownership of the run"
        )
    assert len({depth for _at, depth, _title in run}) == 1, (
        "the entry run mixes heading ranks: " f"{sorted({d for _at, d, _title in run})}"
    )


# ---------------------------------------------------------------------------
# Ownership: what is in the source that the official document did not put there
# ---------------------------------------------------------------------------


#: Markup and wording that would mean community scaffolding rather than SRD
#: text. The vocabulary check deliberately omits "discord": the Symbol spell
#: names Discord as one of its effects, so the word is official content here.
_SCAFFOLDING = (
    re.compile(r"<!--"),
    re.compile(r"https?://"),
    re.compile(r"\]\(#"),
    re.compile(r"(?i)\b(github|reddit|homebrew|unofficial|contributor)\b"),
)


def test_no_content_file_carries_community_scaffolding() -> None:
    """The source used for ingestion holds SRD content and nothing else.

    Upstream's own ``README.md`` and ``CHANGELOG.md`` are kept, but with
    ``role: upstream-process`` and outside ``CONTENT_FILES``, so they are never
    ingested as rules.
    """
    found = [
        (name, _line_of(text, m.start()), m.group(0))
        for name, text in RAW.items()
        for pattern in _SCAFFOLDING
        for m in pattern.finditer(text)
    ]
    assert found == []


def test_the_process_files_are_named_but_not_ingested() -> None:
    """Licence history may stay, separately identified, out of the content set."""
    roles = {str(f["path"]): str(f["role"]) for f in MANIFEST["files"]}
    assert roles["README.md"] == roles["CHANGELOG.md"] == "upstream-process"
    assert roles["LICENSE"] == "license"
    assert "README.md" not in cc.CONTENT_FILES
    assert "CHANGELOG.md" not in cc.CONTENT_FILES
    content = {p for p, role in roles.items() if role == "content"}
    assert content == set(cc.CONTENT_FILES)


def test_the_legal_information_page_reproduces_official_page_one(
    official_pages: list[ExtractedPage],
) -> None:
    """CC-BY-4.0 requires the attribution to travel with the derived work.

    Official page 1 is the attribution page; the navigation-only table of
    contents on pp.2–4 is not it, and neither is upstream's repository README.
    The snapshot omitted page 1, so it is carried as a controlled addition —
    which is only worth anything if it really is that page.
    """
    page_one = next(p for p in official_pages if p.printed_page == 1)
    added = (PIN_DIR / "legal-information.md").read_text(encoding="utf-8")
    assert cc.compact(cc.markdown_text(added)) == cc.compact(cc.page_text(page_one))
    assert "creativecommons.org/licenses/by/4.0/legalcode" in added


# ---------------------------------------------------------------------------
# The token pass reports a changed number, which is why it is trusted
# ---------------------------------------------------------------------------


def _page(printed: int, text: str) -> ExtractedPage:
    line = PageLine(
        page_index=printed - 1,
        printed_page=printed,
        line_index=0,
        text=text,
        top=0.0,
        x0=0.0,
        x1=1.0,
        size=10.0,
        char_start=0,
        char_end=len(text),
    )
    return ExtractedPage(
        page_index=printed - 1,
        printed_page=printed,
        width=1.0,
        height=1.0,
        lines=(line,),
    )


#: Long enough that each page owns unique windows, which is what lets the
#: partition cut the snapshot at the right places.
_SYNTHETIC = {
    5: "The kraken hurls a barbed spear at the drowned lighthouse keeper "
    "and deals 19 Piercing damage on a hit, or 7 damage on a miss.",
    6: "A basilisk crossing the salt flats of Vashenmir has Speed 20 feet "
    "and a Petrifying Gaze that lasts for 3 rounds after it closes.",
    7: "Wandering minstrels of the Ember Coast sing of a copper dragon "
    "whose hoard weighs 400 pounds and answers to no crowned monarch.",
}


def test_the_token_pass_reports_a_changed_sign_the_window_pass_folds_away() -> None:
    """A planted defect has to fire, or a quiet report means nothing.

    ``compact`` removes the minus sign, so a modifier flipped from −2 to +2 is
    invisible to the window pass. Here the same flip is planted in a synthetic
    document and must surface on the page it was planted on, and only there.
    """
    pages = [_page(n, text) for n, text in _SYNTHETIC.items()]
    clean = " ".join(_SYNTHETIC[n] for n in sorted(_SYNTHETIC))
    rows = {r.printed_page: r for r in ct.inventory(pages, {"synthetic.md": clean})}
    assert all(not r.pdf_only and not r.snapshot_only for r in rows.values()), rows

    damaged = clean.replace("deals 19 Piercing", "deals 18 Piercing")
    assert damaged != clean
    rows = {r.printed_page: r for r in ct.inventory(pages, {"synthetic.md": damaged})}
    assert rows[5].pdf_only == {"19": 1}
    assert rows[5].snapshot_only == {"18": 1}
    assert all(not rows[n].pdf_only and not rows[n].snapshot_only for n in (6, 7)), rows


def test_reading_the_numbers_in_order_finds_a_row_dropped_under_a_page_header() -> None:
    """The check that found the one omission the multiset pass let through.

    A table running across a page break has its header reprinted at the top of
    the second page. Drop the first body row under that reprinted header and the
    multiset comparison still reports the header's words as surplus — the same
    shape every other repeated header produces — so the omission reads as
    ordinary noise. In sequence it does not: the numbers stop lining up.
    """
    # Enough surrounding prose that each page owns windows of its own; a table
    # fragment alone is shorter than the window and its repeated header makes
    # what little there is ambiguous between the two pages.
    first = (
        "While holding the crooked hazel staff of the drowned archivist, you "
        "can cast one of the spells on the following table from it, using your "
        "own spell save DC. Spell Charge Cost Arcane Lock 0 Detect Magic 0 "
        "Ice Storm 4 Knock 2 "
    )
    second = (
        "Spell Charge Cost Mage Hand 0 Passwall 5 Plane Shift 7 Web 2 "
        "Regaining Charges. The staff recovers its expended charges at dawn, "
        "and a staff broken over the knee of its bearer releases them all at "
        "once in a roar of coloured fire that no ward in the vault will stop."
    )
    pages = [_page(5, first), _page(6, second)]
    # One table, so the snapshot writes the header once; the document reprints
    # it at the top of the second page. That surplus is the noise this has to
    # be told apart from.
    kept = first + second.replace("Spell Charge Cost ", "", 1)
    dropped = kept.replace("Mage Hand 0 ", "")

    residue = {r.printed_page: r.pdf_only for r in ct.inventory(pages, {"t.md": kept})}
    assert residue[6] == {"spell": 1, "charge": 1, "cost": 1}
    lost = {r.printed_page: r.pdf_only for r in ct.inventory(pages, {"t.md": dropped})}
    # The repeated header dominates the residue either way: "mage", "hand" and
    # "0" are the only difference between a complete table and a broken one.
    assert set(lost[6]) - set(residue[6]) == {"mage", "hand", "0"}

    order = {r.printed_page: r for r in ct.number_order(pages, {"t.md": kept})}
    assert all(r.same_order for r in order.values())
    order = {r.printed_page: r for r in ct.number_order(pages, {"t.md": dropped})}
    assert order[5].same_order
    assert order[6].pdf == ("0", "5", "7", "2")
    assert order[6].snapshot == ("5", "7", "2")


def test_the_token_pass_keeps_a_minus_sign_that_compaction_folds_away() -> None:
    """The normalization difference that is the whole reason for the second pass."""
    assert cc.compact("modifier −2") == cc.compact("modifier 2")
    assert ct.tokens(ct.snorm("modifier −2")) != ct.tokens(ct.snorm("modifier 2"))
    assert ct.tokens(ct.snorm("−2"))["-2"] == 1


@pytest.mark.parametrize(
    "entry", MANIFEST["controlled_additions"], ids=lambda e: str(e["path"])
)
def test_a_controlled_addition_is_not_in_the_ingested_content_set(
    entry: dict[str, object],
) -> None:
    """It is pinned content, but it is not one of the thirteen compared files.

    The comparison covers the official document against upstream's content
    files; an added page has no upstream counterpart to compare. Ingestion picks
    it up separately, which is a later increment's job and is recorded as such.
    """
    assert str(entry["path"]) not in cc.CONTENT_FILES
