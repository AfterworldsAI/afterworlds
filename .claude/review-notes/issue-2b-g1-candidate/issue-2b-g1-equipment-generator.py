# ruff: noqa: E501  -- clause literals are verbatim source text, kept whole to be greppable
"""Author the **equipment** proposal: the whole *Equipment* part, one
dependency group.

**CRD Issue 2b G1 candidate.** A copy of the recorded
``issue-5d-equipment-cited-targets-generator.py`` with exactly two changes,
both unaccepted review material. The build applies the accepted
class-eligibility removal (``scripts/common.py``) exactly as the identity
control that reproduces the recorded proposal does.

1. The twelve SRD equipment items no citation named are named records too:
   Dart, Glaive, Halberd, Lance, Maul, Trident, War Pick, Whip and Blowgun
   (Weapons table), Scale Mail and Ring Mail (Armor table) and Needles
   (Ammunition table), each owning its own row, read and cited as every
   accepted row of its table is.
2. Every one of the 38 Weapons-table rows states two schema-18 facts: the
   category its group row prints and the mastery property its Mastery column
   prints (``WEAPON_FACTS``). Each row component becomes ``mixed``: those two
   facts are structured, the rest of the row stays governing prose under the
   same retention reason. A ``weapon_rows`` clause holds the rows so the
   review inventory expects both families of each row's owner and of nothing
   else.

The batch declares schema 18. Everything else is the recorded generator.

---

REVIEW MATERIAL for CRD Issue 5d (#137) over the qualified 5c release
``ebdd9333-eeed-5df1-b3e1-8b97c2f65f80`` / ``5.2.1-corpus.574662e9-0ef``. It
emits an *unaccepted* ``5d-proposal-2`` artifact. It accepts nothing, publishes
nothing, writes nothing under ``oracles/``, records no reference resolution,
and imports no earlier batch's content, identity or authority: every leaf is
read afresh from the release.

Scope, 375 leaves, 14 section records, one review unit each: the fourteen ``##``
sections of *Equipment* (pp89-103 of the official PDF), each whole, in printed
order -- *Coins*, *Weapons*, *Armor*, *Tools*, *Adventuring Gear*, *Mounts and
Vehicles*, *Lifestyle Expenses*, *Food, Drink, and Lodging*, *Hirelings*,
*Spellcasting*, *Magic Items*, *Crafting Nonmagical Items*, *Brewing Potions
of Healing* and *Scribing Spell Scrolls*. The part title ``# Equipment``
states no rule and belongs to no section, as ``# Character Origins`` belongs to
none. The separate *Magic Items*, *Spells*, *Classes* and *Monsters* parts are
not authored; the *Magic Items* section here is the part's general rules for
using magic items, not the catalogue.

Record grain: one record per section, each reading its whole section in
printed order. Every *Adventuring Gear* entry and every *Lifestyle Expenses*
option prints its price in its own heading ("#### Acid (25 GP)", "### Modest
(1 GP per Day)"), so each is a component whose clause holds its priced heading
and its body.

Named records (ADR-005d Decisions 3 and 7; Owner Decision 2026-09-24): each
item or rule a citation names -- an accepted citation, a resolution draft's
target, or a pointer inside Equipment (Club, Shield, Bullet ...) -- is its own
record (``NAMED``), with the in-Equipment rules needed to interpret it: a gear
item, a tool, a weapon or armor table row, a weapon property or mastery, a
weapon or armor category, armor class and stealth, *Artisan's Tools*. The
record is the one authority for what it names: it owns its exact spans
(PRIMARY) and reads the table head and group row it sits under (CONTEXTUAL); a
cited table row is its own span, so the table is cut into contiguous pieces
at its rows and still rejoins whole. Each named record is a
``CATALOGUE_MEMBER`` of its section, which no longer reads the member's own
prose: the section reaches the member where it is printed, so its GameMaster
reading interleaves its own passages with its members' in source order.
Uncited entries stay the section's own components.

Kinds: the ten sections that price goods or services -- *Coins* to
*Spellcasting* -- are ``equipment``; the rules for using magic items and for
crafting, brewing and scribing are ``general_rule``.

This file is literal review data only; the assembly is the committed shared
:mod:`afterworlds.ingestion.mechanical.authoring`. ``CLAUSES`` is the source
review; ``COMPONENTS`` is the representation proposed for it; expected rules
come from ``CLAUSES`` alone.

Authoring conventions (as the twelve accepted batches):

* Every component is prose-bound. ``EquipmentDescriptorFact`` (cost, weight)
  and ``WeaponPropertyFact`` exist, but no consumer reads either, and the
  latter cannot state an Ammunition property's range and ammunition type or
  "Two-Handed (unless mounted)". Typing one table column would detach the
  rows, group rows and prose that qualify it. They are the lift path, not
  this batch.
* A table keeps every header row, group row and data row, in printed order,
  with the prose that introduces it (``table`` below writes the release's
  own rows, and fails loudly if the release renders them otherwise). The
  *Food, Drink, and Lodging* and *Tack, Harness, and Drawn Vehicles* group
  rows and the *Airborne and Waterborne Vehicles* caption are read from the
  corrected source (correction families I and J).
* Each item, tool, property and option is one component with its conditions
  (and, when named, also its named record's component, which carries its
  references while the section's reads the same prose as context):
  a gear item's heading, body and own table (*Ammunition*, the three focus
  kinds); an artisan's tool's name line and its ability, weight, utilize and
  craft lines; a property's label and definition.
* ``gamemaster_latitude`` is kept where the rule leaves the outcome to the GM
  (lifestyle period and consequences, crafting tools, materials and
  assistants, extra worn items); ``contextual_applicability`` where applying
  it turns on fiction the projection cannot enumerate (an accurate Book or
  Map, a Crowbar's leverage, a Costume's disguise, a Magnifying Glass's
  detail, the events Fine Clothes or a Robe admit to); everything else is
  ``no_identified_structured_use``.
* References:

  - every explicit pointer. "Improvised Weapons" in "Rules Glossary" names
    that entry, which no accepted record defines yet (an unknown target);
    "Magic Items", "Monsters" and "Gameplay Toolbox" name unauthored parts
    and stay unresolved. "Later in "Equipment"" and "in "Equipment"" locate a
    section of this part and name that section's record.
  - each named item, tool, weapon or armor a rule here requires or crafts,
    to the record that prices it, once per record per component at its first
    printed name. A pack's contents are items of its own record and not
    references; the classes that may use a focus name the *Classes* part,
    unresolved; the *Identify* spell names *Spells*, unresolved.
  - each accepted Rules Glossary term a rule here depends on, by its printed
    name (``GLOSSARY_TERMS``), once per component, read from prose and never
    from a table. Unaccepted glossary terms (Advantage, Disadvantage, Bonus
    Action, Reaction, D20 Test, Bright and Dim Light, Cone) and skills stay
    unreferenced, as before. Examples ("such as Weapon Mastery", "a Ring of
    Swimming", "Plate Armor, which sells for 1,500 GP") illustrate and are not
    references.

Forty-five accepted citations name "Equipment" or a thing it prices and stay
unresolved. This batch makes forty-three resolvable; their drafts are given
below for the same Owner packet. Nothing here records or applies them, and the
six recorded resolutions are untouched. Two stay unresolved: each points at
the whole part, which no single section truthfully stands for.

Run: ``python issue-5d-equipment-generator.py <published afterworlds.db>``
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from sqlalchemy.orm import Session

from afterworlds.ingestion.mechanical.authoring import (
    Built,
    EntryBatch,
    EntryComponent,
    Placement,
    RecordReference,
    Target,
    build_entry_batch,
    emit,
    scoped,
    unknown_target_findings,
)
from afterworlds.ingestion.mechanical.authoring import batch_findings as batch_findings
from afterworlds.ingestion.mechanical.authoring import render as render
from afterworlds.ingestion.mechanical.bound_corpus import published_release_binding
from afterworlds.ingestion.mechanical.models import (
    ComponentHandling,
    ReferenceResolution,
    ReleaseBinding,
)
from afterworlds.ingestion.mechanical.reference_resolution import (
    reference_resolution_payload,
)
from afterworlds.ingestion.mechanical.representation import (
    FactFamily,
    RecordKind,
    WeaponCategory,
    WeaponCategoryFact,
    WeaponMastery,
    WeaponMasteryFact,
)
from afterworlds.ingestion.mechanical.schema_lift import (
    SCHEMA_18_HASH,
    SCHEMA_18_VERSION,
)

ORIGIN = "issue-2b-g1-equipment-generator.py"
PROPOSAL_FILE = "issue-2b-g1-equipment-PROPOSAL.json"
DRAFTS_FILE = "issue-2b-g1-equipment-resolutions-DRAFTS.json"
#: Every record here is placed; the unplaced-entry default is never read.
PARENT = ("Rules Glossary", "Rules Definitions")
#: The parts this batch's records and pointers name, formed from the release's
#: own part names under the ``<release-family>/<section-slug>`` convention.
EQUIPMENT = "srd-5.2.1/equipment"
MAGIC_ITEMS = "srd-5.2.1/magic-items"
MONSTERS = "srd-5.2.1/monsters"
SPELLS = "srd-5.2.1/spells"
CLASSES = "srd-5.2.1/classes"
GAMEPLAY_TOOLBOX = "srd-5.2.1/gameplay-toolbox"
#: The target of a printed pointer whose destination has no record yet. It is
#: reported as ``unresolved reference`` until a reviewed resolution names one;
#: naming a key here would guess at a record nobody has authored.
UNRESOLVED_TARGET = ""

PART = "Equipment"

#: (record slug, printed section label, record kind), in printed order.
ENTRIES: tuple[tuple[str, str, RecordKind], ...] = (
    ("coins", "Coins", RecordKind.EQUIPMENT),
    ("weapons", "Weapons", RecordKind.EQUIPMENT),
    ("armor", "Armor", RecordKind.EQUIPMENT),
    ("tools", "Tools", RecordKind.EQUIPMENT),
    ("adventuring_gear", "Adventuring Gear", RecordKind.EQUIPMENT),
    ("mounts_and_vehicles", "Mounts and Vehicles", RecordKind.EQUIPMENT),
    ("lifestyle_expenses", "Lifestyle Expenses", RecordKind.EQUIPMENT),
    ("food_drink_and_lodging", "Food, Drink, and Lodging", RecordKind.EQUIPMENT),
    ("hirelings", "Hirelings", RecordKind.EQUIPMENT),
    ("spellcasting", "Spellcasting", RecordKind.EQUIPMENT),
    ("magic_items", "Magic Items", RecordKind.GENERAL_RULE),
    ("crafting_nonmagical_items", "Crafting Nonmagical Items", RecordKind.GENERAL_RULE),
    (
        "brewing_potions_of_healing",
        "Brewing Potions of Healing",
        RecordKind.GENERAL_RULE,
    ),
    ("scribing_spell_scrolls", "Scribing Spell Scrolls", RecordKind.GENERAL_RULE),
)

#: Every record's key, container and heading. The container is qualified by
#: the part: the release prints a *Tools* section in *Crafting Nonmagical
#: Items* and a *Magic Items* part as well.
PLACEMENTS: dict[str, Placement] = {
    s: Placement(f"equipment.{s}", (PART, label), f"## {label}")
    for s, label, _ in ENTRIES
}

# ---------------------------------------------------------------------------
# Reason codes and handling
# ---------------------------------------------------------------------------
CTX = "contextual_applicability"
GM = "gamemaster_latitude"
NO_USE = "no_identified_structured_use"
P = ComponentHandling.PROSE_BOUND
M = ComponentHandling.MIXED
PROSE = None

# ---------------------------------------------------------------------------
# Table leaves, written as their rows
# ---------------------------------------------------------------------------
Row = tuple[str, ...] | str


def table(caption: str | None, heads: list[tuple[str, ...]], rows: list[Row]) -> str:
    """A 5c table leaf's exact text, written as its rows rather than as markup.

    As :func:`~afterworlds.ingestion.mechanical.authoring.html_table`, with
    what these tables also print: an uncaptioned table, more than one header
    row, and group rows (a string) spanning every column. Only a way to *name*
    source text; a table the release renders differently fails to locate.
    """
    width = len(heads[0])

    def tr(tag: str, cells: tuple[str, ...]) -> str:
        inner = "".join(f"\n      <{tag}>{c}</{tag}>" for c in cells)
        return f"    <tr>{inner}\n    </tr>\n"

    def body(row: Row) -> str:
        if isinstance(row, str):
            return f'    <tr>\n      <th colspan="{width}"><em>{row}</em></th>\n    </tr>\n'
        return tr("td", row)

    caption_text = f"**{caption}**\n\n" if caption else ""
    return (
        f"{caption_text}<table>\n  <thead>\n{''.join(tr('th', h) for h in heads)}  </thead>\n"
        f"  <tbody>\n{''.join(body(r) for r in rows)}  </tbody>\n</table>"
    )


def head_of(tbl: str) -> str:
    """A table's caption, header rows and the opening of its body."""
    return tbl[: tbl.index("  <tbody>\n") + len("  <tbody>\n")]


def row_of(tbl: str, needle: str) -> str:
    """The one whole row of *tbl* that prints *needle*."""
    if tbl.count(needle) != 1:
        raise ValueError(f"{needle!r} is printed {tbl.count(needle)} times")
    at = tbl.index(needle)
    start = tbl.rindex("    <tr>\n", 0, at)
    return tbl[start : tbl.index("    </tr>\n", at) + len("    </tr>\n")]


def cut(tbl: str, *pieces: str) -> tuple[str, ...]:
    """*tbl* as contiguous texts: each of *pieces*, in printed order, and the
    runs between them. Joined, they are the table byte for byte."""
    out: list[str] = []
    at = 0
    for piece in pieces:
        i = tbl.index(piece, at)
        out += [tbl[at:i], piece]
        at = i + len(piece)
    out.append(tbl[at:])
    texts = tuple(t for t in out if t)
    if "".join(texts) != tbl or any(not t.strip() for t in texts):
        raise ValueError("a table cut must rejoin whole, with no blank piece")
    return texts


COIN_VALUES_TABLE = table(
    "Coin Values",
    [
        ("Coin", "Value in GP"),
    ],
    [
        ("Copper Piece (CP)", "1/100"),
        ("Silver Piece (SP)", "1/10"),
        ("Electrum Piece (EP)", "1/2"),
        ("Gold Piece (GP)", "1"),
        ("Platinum Piece (PP)", "10"),
    ],
)

WEAPONS_TABLE = table(
    "Weapons",
    [
        ("Name", "Damage", "Properties", "Mastery", "Weight", "Cost"),
    ],
    [
        "Simple Melee Weapons",
        ("Club", "1d4 Bludgeoning", "Light", "Slow", "2 lb.", "1 SP"),
        (
            "Dagger",
            "1d4 Piercing",
            "Finesse, Light, Thrown (Range 20/60)",
            "Nick",
            "1 lb.",
            "2 GP",
        ),
        ("Greatclub", "1d8 Bludgeoning", "Two-Handed", "Push", "10 lb.", "2 SP"),
        (
            "Handaxe",
            "1d6 Slashing",
            "Light, Thrown (Range 20/60)",
            "Vex",
            "2 lb.",
            "5 GP",
        ),
        ("Javelin", "1d6 Piercing", "Thrown (Range 30/120)", "Slow", "2 lb.", "5 SP"),
        (
            "Light Hammer",
            "1d4 Bludgeoning",
            "Light, Thrown (Range 20/60)",
            "Nick",
            "2 lb.",
            "2 GP",
        ),
        ("Mace", "1d6 Bludgeoning", "—", "Sap", "4 lb.", "5 GP"),
        (
            "Quarterstaff",
            "1d6 Bludgeoning",
            "Versatile (1d8)",
            "Topple",
            "4 lb.",
            "2 SP",
        ),
        ("Sickle", "1d4 Slashing", "Light", "Nick", "2 lb.", "1 GP"),
        (
            "Spear",
            "1d6 Piercing",
            "Thrown (Range 20/60), Versatile (1d8)",
            "Sap",
            "3 lb.",
            "1 GP",
        ),
        "Simple Ranged Weapons",
        (
            "Dart",
            "1d4 Piercing",
            "Finesse, Thrown (Range 20/60)",
            "Vex",
            "1/4 lb.",
            "5 CP",
        ),
        (
            "Light Crossbow",
            "1d8 Piercing",
            "Ammunition (Range 80/320; Bolt), Loading, Two-Handed",
            "Slow",
            "5 lb.",
            "25 GP",
        ),
        (
            "Shortbow",
            "1d6 Piercing",
            "Ammunition (Range 80/320; Arrow), Two-Handed",
            "Vex",
            "2 lb.",
            "25 GP",
        ),
        (
            "Sling",
            "1d4 Bludgeoning",
            "Ammunition (Range 30/120; Bullet)",
            "Slow",
            "—",
            "1 SP",
        ),
        "Martial Melee Weapons",
        ("Battleaxe", "1d8 Slashing", "Versatile (1d10)", "Topple", "4 lb.", "10 GP"),
        ("Flail", "1d8 Bludgeoning", "—", "Sap", "2 lb.", "10 GP"),
        (
            "Glaive",
            "1d10 Slashing",
            "Heavy, Reach, Two-Handed",
            "Graze",
            "6 lb.",
            "20 GP",
        ),
        ("Greataxe", "1d12 Slashing", "Heavy, Two-Handed", "Cleave", "7 lb.", "30 GP"),
        ("Greatsword", "2d6 Slashing", "Heavy, Two-Handed", "Graze", "6 lb.", "50 GP"),
        (
            "Halberd",
            "1d10 Slashing",
            "Heavy, Reach, Two-Handed",
            "Cleave",
            "6 lb.",
            "20 GP",
        ),
        (
            "Lance",
            "1d10 Piercing",
            "Heavy, Reach, Two-Handed (unless mounted)",
            "Topple",
            "6 lb.",
            "10 GP",
        ),
        ("Longsword", "1d8 Slashing", "Versatile (1d10)", "Sap", "3 lb.", "15 GP"),
        ("Maul", "2d6 Bludgeoning", "Heavy, Two-Handed", "Topple", "10 lb.", "10 GP"),
        ("Morningstar", "1d8 Piercing", "—", "Sap", "4 lb.", "15 GP"),
        ("Pike", "1d10 Piercing", "Heavy, Reach, Two-Handed", "Push", "18 lb.", "5 GP"),
        ("Rapier", "1d8 Piercing", "Finesse", "Vex", "2 lb.", "25 GP"),
        ("Scimitar", "1d6 Slashing", "Finesse, Light", "Nick", "3 lb.", "25 GP"),
        ("Shortsword", "1d6 Piercing", "Finesse, Light", "Vex", "2 lb.", "10 GP"),
        (
            "Trident",
            "1d8 Piercing",
            "Thrown (Range 20/60), Versatile (1d10)",
            "Topple",
            "4 lb.",
            "5 GP",
        ),
        ("Warhammer", "1d8 Bludgeoning", "Versatile (1d10)", "Push", "5 lb.", "15 GP"),
        ("War Pick", "1d8 Piercing", "Versatile (1d10)", "Sap", "2 lb.", "5 GP"),
        ("Whip", "1d4 Slashing", "Finesse, Reach", "Slow", "3 lb.", "2 GP"),
        "Martial Ranged Weapons",
        (
            "Blowgun",
            "1 Piercing",
            "Ammunition (Range 25/100; Needle), Loading",
            "Vex",
            "1 lb.",
            "10 GP",
        ),
        (
            "Hand Crossbow",
            "1d6 Piercing",
            "Ammunition (Range 30/120; Bolt), Light, Loading",
            "Vex",
            "3 lb.",
            "75 GP",
        ),
        (
            "Heavy Crossbow",
            "1d10 Piercing",
            "Ammunition (Range 100/400; Bolt), Heavy, Loading, Two-Handed",
            "Push",
            "18 lb.",
            "50 GP",
        ),
        (
            "Longbow",
            "1d8 Piercing",
            "Ammunition (Range 150/600; Arrow), Heavy, Two-Handed",
            "Slow",
            "2 lb.",
            "50 GP",
        ),
        (
            "Musket",
            "1d12 Piercing",
            "Ammunition (Range 40/120; Bullet), Loading, Two-Handed",
            "Slow",
            "10 lb.",
            "500 GP",
        ),
        (
            "Pistol",
            "1d10 Piercing",
            "Ammunition (Range 30/90; Bullet), Loading",
            "Vex",
            "3 lb.",
            "250 GP",
        ),
    ],
)

ARMOR_TABLE = table(
    "Armor",
    [
        ("Armor", "Armor Class (AC)", "Strength", "Stealth", "Weight", "Cost"),
    ],
    [
        "Light Armor (1 Minute to Don or Doff)",
        ("Padded Armor", "11 + Dex modifier", "—", "Disadvantage", "8 lb.", "5 GP"),
        ("Leather Armor", "11 + Dex modifier", "—", "—", "10 lb.", "10 GP"),
        ("Studded Leather Armor", "12 + Dex modifier", "—", "—", "13 lb.", "45 GP"),
        "Medium Armor (5 Minutes to Don and 1 Minute to Doff)",
        ("Hide Armor", "12 + Dex modifier (max 2)", "—", "—", "12 lb.", "10 GP"),
        ("Chain Shirt", "13 + Dex modifier (max 2)", "—", "—", "20 lb.", "50 GP"),
        (
            "Scale Mail",
            "14 + Dex modifier (max 2)",
            "—",
            "Disadvantage",
            "45 lb.",
            "50 GP",
        ),
        ("Breastplate", "14 + Dex modifier (max 2)", "—", "—", "20 lb.", "400 GP"),
        (
            "Half Plate Armor",
            "15 + Dex modifier (max 2)",
            "—",
            "Disadvantage",
            "40 lb.",
            "750 GP",
        ),
        "Heavy Armor (10 Minutes to Don and 5 Minutes to Doff)",
        ("Ring Mail", "14", "—", "Disadvantage", "40 lb.", "30 GP"),
        ("Chain Mail", "16", "Str 13", "Disadvantage", "55 lb.", "75 GP"),
        ("Splint Armor", "17", "Str 15", "Disadvantage", "60 lb.", "200 GP"),
        ("Plate Armor", "18", "Str 15", "Disadvantage", "65 lb.", "1,500 GP"),
        "Shield (Utilize Action to Don or Doff)",
        ("Shield", "+2", "—", "—", "6 lb.", "10 GP"),
    ],
)

ADVENTURING_GEAR_TABLE = table(
    "Adventuring Gear",
    [
        ("Item", "Weight", "Cost"),
    ],
    [
        ("Acid", "1 lb.", "25 GP"),
        ("Alchemist's Fire", "1 lb.", "50 GP"),
        ("Ammunition", "Varies", "Varies"),
        ("Antitoxin", "—", "50 GP"),
        ("Arcane Focus", "Varies", "Varies"),
        ("Backpack", "5 lb.", "2 GP"),
        ("Ball Bearings", "2 lb.", "1 GP"),
        ("Barrel", "70 lb.", "2 GP"),
        ("Basket", "2 lb.", "4 SP"),
        ("Bedroll", "7 lb.", "1 GP"),
        ("Bell", "—", "1 GP"),
        ("Blanket", "3 lb.", "5 SP"),
        ("Block and Tackle", "5 lb.", "1 GP"),
        ("Book", "5 lb.", "25 GP"),
        ("Bottle, Glass", "2 lb.", "2 GP"),
        ("Bucket", "2 lb.", "5 CP"),
        ("Burglar's Pack", "42 lb.", "16 GP"),
        ("Caltrops", "2 lb.", "1 GP"),
        ("Candle", "—", "1 CP"),
        ("Case, Crossbow Bolt", "1 lb.", "1 GP"),
        ("Case, Map or Scroll", "1 lb.", "1 GP"),
        ("Chain", "10 lb.", "5 GP"),
        ("Chest", "25 lb.", "5 GP"),
        ("Climber's Kit", "12 lb.", "25 GP"),
        ("Clothes, Fine", "6 lb.", "15 GP"),
        ("Clothes, Traveler's", "4 lb.", "2 GP"),
        ("Component Pouch", "2 lb.", "25 GP"),
        ("Costume", "4 lb.", "5 GP"),
        ("Crowbar", "5 lb.", "2 GP"),
        ("Diplomat's Pack", "39 lb.", "39 GP"),
        ("Druidic Focus", "Varies", "Varies"),
        ("Dungeoneer's Pack", "55 lb.", "12 GP"),
        ("Entertainer's Pack", "58½ lb.", "40 GP"),
        ("Explorer's Pack", "55 lb.", "10 GP"),
        ("Flask", "1 lb.", "2 CP"),
        ("Grappling Hook", "4 lb.", "2 GP"),
        ("Healer's Kit", "3 lb.", "5 GP"),
        ("Holy Symbol", "Varies", "Varies"),
        ("Holy Water", "1 lb.", "25 GP"),
        ("Hunting Trap", "25 lb.", "5 GP"),
        ("Ink", "—", "10 GP"),
        ("Ink Pen", "—", "2 CP"),
        ("Jug", "4 lb.", "2 CP"),
        ("Ladder", "25 lb.", "1 SP"),
        ("Lamp", "1 lb.", "5 SP"),
        ("Lantern, Bullseye", "2 lb.", "10 GP"),
        ("Lantern, Hooded", "2 lb.", "5 GP"),
        ("Lock", "1 lb.", "10 GP"),
        ("Magnifying Glass", "—", "100 GP"),
        ("Manacles", "6 lb.", "2 GP"),
        ("Map", "—", "1 GP"),
        ("Mirror", "1/2 lb.", "5 GP"),
        ("Net", "3 lb.", "1 GP"),
        ("Oil", "1 lb.", "1 SP"),
        ("Paper", "—", "2 SP"),
        ("Parchment", "—", "1 SP"),
        ("Perfume", "—", "5 GP"),
        ("Poison, Basic", "—", "100 GP"),
        ("Pole", "7 lb.", "5 CP"),
        ("Pot, Iron", "10 lb.", "2 GP"),
        ("Potion of Healing", "1/2 lb.", "50 GP"),
        ("Pouch", "1 lb.", "5 SP"),
        ("Priest's Pack", "29 lb.", "33 GP"),
        ("Quiver", "1 lb.", "1 GP"),
        ("Ram, Portable", "35 lb.", "4 GP"),
        ("Rations", "2 lb.", "5 SP"),
        ("Robe", "4 lb.", "1 GP"),
        ("Rope", "5 lb.", "1 GP"),
        ("Sack", "1/2 lb.", "1 CP"),
        ("Scholar's Pack", "22 lb.", "40 GP"),
        ("Shovel", "5 lb.", "2 GP"),
        ("Signal Whistle", "—", "5 CP"),
        ("Spell Scroll (Cantrip)", "—", "30 GP"),
        ("Spell Scroll (Level 1)", "—", "50 GP"),
        ("Spikes, Iron", "5 lb.", "1 GP"),
        ("Spyglass", "1 lb.", "1,000 GP"),
        ("String", "—", "1 SP"),
        ("Tent", "20 lb.", "2 GP"),
        ("Tinderbox", "1 lb.", "5 SP"),
        ("Torch", "1 lb.", "1 CP"),
        ("Vial", "—", "1 GP"),
        ("Waterskin", "5 lb. (full)", "2 SP"),
    ],
)

AMMUNITION_TABLE = table(
    "Ammunition",
    [
        ("Type", "Amount", "Storage", "Weight", "Cost"),
    ],
    [
        ("Arrows", "20", "Quiver", "1 lb.", "1 GP"),
        ("Bolts", "20", "Case", "1½ lb.", "1 GP"),
        ("Bullets, Firearm", "10", "Pouch", "2 lb.", "3 GP"),
        ("Bullets, Sling", "20", "Pouch", "1½ lb.", "4 CP"),
        ("Needles", "50", "Pouch", "1 lb.", "1 GP"),
    ],
)

#: The rows a citation names by name -- an accepted citation, or a pointer of
#: this batch -- and the head and group rows they are read under. Each is its
#: own span, so the record naming it owns exactly its row, and its table is
#: cut into contiguous pieces at them.
WEAPONS_HEAD = head_of(WEAPONS_TABLE)
WEAPON_GROUPS = {
    g: row_of(WEAPONS_TABLE, f"<em>{g}</em>")
    for g in (
        "Simple Melee Weapons",
        "Simple Ranged Weapons",
        "Martial Melee Weapons",
        "Martial Ranged Weapons",
    )
}
WEAPON_ROWS = {
    n: row_of(WEAPONS_TABLE, f"<td>{n}</td>")
    for n in (
        "Club",
        "Dagger",
        "Greatclub",
        "Handaxe",
        "Javelin",
        "Light Hammer",
        "Mace",
        "Quarterstaff",
        "Sickle",
        "Spear",
        "Dart",
        "Light Crossbow",
        "Shortbow",
        "Sling",
        "Battleaxe",
        "Flail",
        "Glaive",
        "Greataxe",
        "Greatsword",
        "Halberd",
        "Lance",
        "Longsword",
        "Maul",
        "Morningstar",
        "Pike",
        "Rapier",
        "Scimitar",
        "Shortsword",
        "Trident",
        "Warhammer",
        "War Pick",
        "Whip",
        "Blowgun",
        "Hand Crossbow",
        "Heavy Crossbow",
        "Longbow",
        "Musket",
        "Pistol",
    )
}
ARMOR_HEAD = head_of(ARMOR_TABLE)
ARMOR_GROUPS = {
    g: row_of(ARMOR_TABLE, f"<em>{g} (")
    for g in ("Light Armor", "Medium Armor", "Heavy Armor", "Shield")
}
ARMOR_ROWS = {
    n: row_of(ARMOR_TABLE, f"<td>{n}</td>")
    for n in (
        "Padded Armor",
        "Leather Armor",
        "Studded Leather Armor",
        "Hide Armor",
        "Chain Shirt",
        "Scale Mail",
        "Breastplate",
        "Half Plate Armor",
        "Ring Mail",
        "Chain Mail",
        "Splint Armor",
        "Plate Armor",
        "Shield",
    )
}
GEAR_HEAD = head_of(ADVENTURING_GEAR_TABLE)
#: Each named gear item's rows of the Adventuring Gear table, by clause key.
GEAR_ROWS = {
    key: tuple(row_of(ADVENTURING_GEAR_TABLE, f"<td>{n}</td>") for n in names)
    for key, *names in (
        ("acid", "Acid"),
        ("alchemists_fire", "Alchemist's Fire"),
        ("antitoxin", "Antitoxin"),
        ("arcane_focus", "Arcane Focus"),
        ("backpack", "Backpack"),
        ("ball_bearings", "Ball Bearings"),
        ("barrel", "Barrel"),
        ("basket", "Basket"),
        ("bell", "Bell"),
        ("block_and_tackle", "Block and Tackle"),
        ("book", "Book"),
        ("bottle_glass", "Bottle, Glass"),
        ("burglars_pack", "Burglar's Pack"),
        ("caltrops", "Caltrops"),
        ("climbers_kit", "Climber's Kit"),
        ("clothes_travelers", "Clothes, Traveler's"),
        ("component_pouch", "Component Pouch"),
        ("costume", "Costume"),
        ("crowbar", "Crowbar"),
        ("druidic_focus", "Druidic Focus"),
        ("dungeoneers_pack", "Dungeoneer's Pack"),
        ("entertainers_pack", "Entertainer's Pack"),
        ("explorers_pack", "Explorer's Pack"),
        ("grappling_hook", "Grappling Hook"),
        ("healers_kit", "Healer's Kit"),
        ("holy_symbol", "Holy Symbol"),
        ("holy_water", "Holy Water"),
        ("ink", "Ink"),
        ("jug", "Jug"),
        ("lantern_bullseye", "Lantern, Bullseye"),
        ("map", "Map"),
        ("mirror", "Mirror"),
        ("net", "Net"),
        ("parchment", "Parchment"),
        ("poison_basic", "Poison, Basic"),
        ("pole", "Pole"),
        ("potion_of_healing", "Potion of Healing"),
        ("pouch", "Pouch"),
        ("priests_pack", "Priest's Pack"),
        ("quiver", "Quiver"),
        ("rations", "Rations"),
        ("robe", "Robe"),
        ("rope", "Rope"),
        ("sack", "Sack"),
        ("scholars_pack", "Scholar's Pack"),
        ("spell_scroll", "Spell Scroll (Cantrip)", "Spell Scroll (Level 1)"),
        ("spikes_iron", "Spikes, Iron"),
        ("torch", "Torch"),
    )
}
AMMUNITION_HEAD = head_of(AMMUNITION_TABLE)
AMMUNITION_ROWS = {
    n: row_of(AMMUNITION_TABLE, f"<td>{n}</td>")
    for n in ("Arrows", "Bolts", "Bullets, Firearm", "Bullets, Sling", "Needles")
}
#: G1: Needles is the Ammunition table's last row. Cut alone it would leave the
#: table's close as a piece of its own, the same text as the Arcane Focuses
#: close in this entry, and a span is keyed by (entry, text), so the two
#: printings could not be told apart (``ANCHORS`` holds one per key). The row
#: owns the close it is printed with instead.
AMMUNITION_ROWS["Needles"] = AMMUNITION_TABLE[
    AMMUNITION_TABLE.index(AMMUNITION_ROWS["Needles"]) :
]


def pieces(tbl: str, *cuts: str) -> tuple[str, ...]:
    """:func:`cut` at *cuts*, whatever order they are listed in."""
    return cut(tbl, *sorted(cuts, key=tbl.index))


WEAPONS_PIECES = pieces(
    WEAPONS_TABLE, WEAPONS_HEAD, *WEAPON_GROUPS.values(), *WEAPON_ROWS.values()
)
ARMOR_PIECES = pieces(
    ARMOR_TABLE, ARMOR_HEAD, *ARMOR_GROUPS.values(), *ARMOR_ROWS.values()
)
GEAR_PIECES = pieces(
    ADVENTURING_GEAR_TABLE,
    GEAR_HEAD,
    *(r for rows in GEAR_ROWS.values() for r in rows),
)
AMMUNITION_PIECES = pieces(AMMUNITION_TABLE, AMMUNITION_HEAD, *AMMUNITION_ROWS.values())

ARCANE_FOCUSES_TABLE = table(
    "Arcane Focuses",
    [
        ("Focus", "Weight", "Cost"),
    ],
    [
        ("Crystal", "1 lb.", "10 GP"),
        ("Orb", "3 lb.", "20 GP"),
        ("Rod", "2 lb.", "10 GP"),
        ("Staff (also a Quarterstaff)", "4 lb.", "5 GP"),
        ("Wand", "1 lb.", "10 GP"),
    ],
)
ARCANE_FOCUSES_HEAD = head_of(ARCANE_FOCUSES_TABLE)
WAND_ROW = row_of(ARCANE_FOCUSES_TABLE, "<td>Wand</td>")
ARCANE_FOCUSES_PIECES = pieces(ARCANE_FOCUSES_TABLE, ARCANE_FOCUSES_HEAD, WAND_ROW)
#: The table's close, cut from its last row, the Wand's, stays the table's.
#: Printed five times among the gear leaves, it is located inside the Wand row
#: and close, printed once.
ARCANE_FOCUSES_CLOSE = ARCANE_FOCUSES_PIECES[-1]
ANCHORS = {("adventuring_gear", ARCANE_FOCUSES_CLOSE): WAND_ROW + ARCANE_FOCUSES_CLOSE}

DRUIDIC_FOCUSES_TABLE = table(
    "Druidic Focuses",
    [
        ("Focus", "Weight", "Cost"),
    ],
    [
        ("Sprig of mistletoe", "—", "1 GP"),
        ("Wooden staff (also a Quarterstaff)", "4 lb.", "5 GP"),
        ("Yew wand", "1 lb.", "10 GP"),
    ],
)

HOLY_SYMBOLS_TABLE = table(
    "Holy Symbols",
    [
        ("Symbol", "Weight", "Cost"),
    ],
    [
        ("Amulet (worn or held)", "1 lb.", "5 GP"),
        ("Emblem (borne on fabric or a Shield)", "—", "5 GP"),
        ("Reliquary (held)", "2 lb.", "5 GP"),
    ],
)

MOUNTS_TABLE = table(
    "Mounts and Other Animals",
    [
        ("Item", "Carrying Capacity", "Cost"),
    ],
    [
        ("Camel", "450 lb.", "50 GP"),
        ("Elephant", "1,320 lb.", "200 GP"),
        ("Horse, Draft", "540 lb.", "50 GP"),
        ("Horse, Riding", "480 lb.", "75 GP"),
        ("Mastiff", "195 lb.", "25 GP"),
        ("Mule", "420 lb.", "8 GP"),
        ("Pony", "225 lb.", "30 GP"),
        ("Warhorse", "540 lb.", "400 GP"),
    ],
)

TACK_TABLE = table(
    "Tack, Harness, and Drawn Vehicles",
    [
        ("Item", "Weight", "Cost"),
    ],
    [
        ("Carriage", "600 lb.", "100 GP"),
        ("Cart", "200 lb.", "15 GP"),
        ("Chariot", "100 lb.", "250 GP"),
        ("Feed per day", "10 lb.", "5 CP"),
        "Saddle",
        ("Exotic", "40 lb.", "60 GP"),
        ("Military", "30 lb.", "20 GP"),
        ("Riding", "25 lb.", "10 GP"),
        ("Sled", "300 lb.", "20 GP"),
        ("Stabling per day", "—", "5 SP"),
        ("Wagon", "400 lb.", "35 GP"),
    ],
)

VEHICLES_TABLE = table(
    "Airborne and Waterborne Vehicles",
    [
        (
            "Ship",
            "Speed",
            "Crew",
            "Passengers",
            "Cargo (Tons)",
            "AC",
            "HP",
            "Damage Threshold",
            "Cost",
        ),
    ],
    [
        ("Airship", "8 mph", "10", "20", "1", "13", "300", "—", "40,000 GP"),
        ("Galley", "4 mph", "80", "—", "150", "15", "500", "20", "30,000 GP"),
        ("Keelboat", "1 mph", "1", "6", "1/2", "15", "100", "10", "3,000 GP"),
        ("Longship", "3 mph", "40", "150", "10", "15", "300", "15", "10,000 GP"),
        ("Rowboat", "1½ mph", "1", "3", "—", "11", "50", "—", "50 GP"),
        ("Sailing Ship", "2 mph", "20", "20", "100", "15", "300", "15", "10,000 GP"),
        ("Warship", "2½ mph", "60", "60", "200", "15", "500", "20", "25,000 GP"),
    ],
)
VEHICLES_HEAD = head_of(VEHICLES_TABLE)
VEHICLE_ROWS = {
    n: row_of(VEHICLES_TABLE, f"<td>{n}</td>") for n in ("Keelboat", "Rowboat")
}
VEHICLES_PIECES = pieces(VEHICLES_TABLE, VEHICLES_HEAD, *VEHICLE_ROWS.values())

FOOD_DRINK_AND_LODGING_TABLE = table(
    "Food, Drink, and Lodging",
    [
        ("Item", "Cost"),
    ],
    [
        ("Ale (mug)", "4 CP"),
        ("Bread (loaf)", "2 CP"),
        ("Cheese (wedge)", "1 SP"),
        "Inn Stay per Day",
        ("Squalid", "7 CP"),
        ("Poor", "1 SP"),
        ("Modest", "5 SP"),
        ("Comfortable", "8 SP"),
        ("Wealthy", "2 GP"),
        ("Aristocratic", "4 GP"),
        "Meal",
        ("Squalid", "1 CP"),
        ("Poor", "2 CP"),
        ("Modest", "1 SP"),
        ("Comfortable", "2 SP"),
        ("Wealthy", "3 SP"),
        ("Aristocratic", "6 SP"),
        "Wine (bottle)",
        ("Common", "2 SP"),
        ("Fine", "10 GP"),
    ],
)

HIRELINGS_TABLE = table(
    "Hirelings",
    [
        ("Service", "Cost"),
    ],
    [
        ("Skilled hireling", "2 GP per day"),
        ("Untrained hireling", "2 SP per day"),
        ("Messenger", "2 CP per mile"),
    ],
)

SPELLCASTING_SERVICES_TABLE = table(
    "Spellcasting Services",
    [
        ("Spell Level", "Availability", "Cost"),
    ],
    [
        ("Cantrip", "Village, town, or city", "30 GP"),
        ("1", "Village, town, or city", "50 GP"),
        ("2", "Village, town, or city", "200 GP"),
        ("3", "Town or city only", "300 GP"),
        ("4–5", "Town or city only", "2,000 GP"),
        ("6–8", "City only", "20,000 GP"),
        ("9", "City only", "100,000 GP"),
    ],
)

SPELL_SCROLL_COSTS_TABLE = table(
    "Spell Scroll Costs",
    [
        ("Spell Level", "Time", "Cost"),
    ],
    [
        ("Cantrip", "1 day", "15 GP"),
        ("1", "1 day", "25 GP"),
        ("2", "3 days", "100 GP"),
        ("3", "5 days", "150 GP"),
        ("4", "10 days", "1,000 GP"),
        ("5", "25 days", "1,500 GP"),
        ("6", "40 days", "10,000 GP"),
        ("7", "50 days", "12,500 GP"),
        ("8", "60 days", "15,000 GP"),
        ("9", "120 days", "50,000 GP"),
    ],
)


Clause = tuple[str, str, tuple[str | None, ...], tuple[str, ...]]


def cl(entry: str, key: str, *texts: str) -> Clause:
    """One clause row whose meaning is carried by governing prose."""
    return (entry, key, (PROSE,), texts)


#: Every covered leaf, in printed order, one row per item, property or rule.
CLAUSES: tuple[Clause, ...] = (
    cl(
        "coins",
        "coin_values",
        "Characters often find coins on their adventures and can spend those coins in shops, inns, and other businesses. Coins come in different denominations based on the relative worth of their material. The Coin Values table lists coins and how much they're worth relative to the Gold Piece, which is the game's main coin. For example, 100 Copper Pieces are worth 1 Gold Piece.",
        COIN_VALUES_TABLE,
    ),
    cl(
        "coins",
        "coin_weight",
        "A coin weighs about a third of an ounce, so fifty coins weigh a pound.",
    ),
    cl(
        "weapons",
        "weapons_table",
        "The Weapons table in this section shows the game's main weapons. The table lists the cost and weight of each weapon, as well as the following details:",
        *(t for t in WEAPONS_PIECES if t not in WEAPON_ROWS.values()),
    ),
    # CRD Issue 2b G1: every Weapons-table row, each owned by its weapon's
    # record, which states the category and mastery the row prints.
    (
        "weapons",
        "weapon_rows",
        (PROSE, FactFamily.WEAPON_CATEGORY.value, FactFamily.WEAPON_MASTERY.value),
        tuple(t for t in WEAPONS_PIECES if t in WEAPON_ROWS.values()),
    ),
    cl(
        "weapons",
        "category",
        "**Category.** Every weapon falls into a category: Simple or Martial. Weapon proficiencies are usually tied to one of these categories. For example, you might have proficiency with Simple weapons.",
    ),
    cl(
        "weapons",
        "melee_or_ranged",
        "**Melee or Ranged.** A weapon is classified as either Melee or Ranged. A Melee weapon is used to attack a target within 5 feet, whereas a Ranged weapon is used to attack at a greater distance.",
    ),
    cl(
        "weapons",
        "damage",
        "**Damage.** The table lists the amount of damage a weapon deals when an attacker hits with it as well as the type of that damage.",
    ),
    cl(
        "weapons",
        "properties",
        '**Properties.** Any properties a weapon has are listed in the Properties column. Each property is defined in the "Properties" section.',
    ),
    cl(
        "weapons",
        "mastery",
        '**Mastery.** Each weapon has a mastery property, which is defined in the "Mastery Properties" section. To use that property, you must have a feature that lets you use it.',
    ),
    cl(
        "weapons",
        "selling_equipment",
        '> **Selling Equipment**\n>\n> Equipment fetches half its cost when sold. In contrast, trade goods and valuables—like gems and art objects—retain their full value in the marketplace. "Magic Items" has prices for magic items.',
    ),
    cl(
        "weapons",
        "weapon_proficiency",
        "Anyone can wield a weapon, but you must have proficiency with it to add your Proficiency Bonus to an attack roll you make with it. A player character's features can provide weapon proficiencies. A monster is proficient with any weapon in its stat block.",
    ),
    cl(
        "weapons",
        "ammunition",
        "**Ammunition.**",
        "You can use a weapon that has the Ammunition property to make a ranged attack only if you have ammunition to fire from it. The type of ammunition required is specified with the weapon's range. Each attack expends one piece of ammunition. Drawing the ammunition is part of the attack (you need a free hand to load a one-handed weapon). After a fight, you can spend 1 minute to recover half the ammunition (round down) you used in the fight; the rest is lost.",
    ),
    cl(
        "weapons",
        "finesse",
        "**Finesse.** When making an attack with a Finesse weapon, use your choice of your Strength or Dexterity modifier for the attack and damage rolls. You must use the same modifier for both rolls.",
    ),
    cl(
        "weapons",
        "heavy",
        "**Heavy.** You have Disadvantage on attack rolls with a Heavy weapon if it's a Melee weapon and your Strength score isn't at least 13 or if it's a Ranged weapon and your Dexterity score isn't at least 13.",
    ),
    cl(
        "weapons",
        "light",
        "**Light.** When you take the Attack action on your turn and attack with a Light weapon, you can make one extra attack as a Bonus Action later on the same turn. That extra attack must be made with a different Light weapon, and you don't add your ability modifier to the extra attack's damage unless that modifier is negative. For example, you can attack with a Shortsword in one hand and a Dagger in the other using the Attack action and a Bonus Action, but you don't add your Strength or Dexterity modifier to the damage roll of the Bonus Action unless that modifier is negative.",
    ),
    cl(
        "weapons",
        "loading",
        "**Loading.** You can fire only one piece of ammunition from a Loading weapon when you use an action, a Bonus Action, or a Reaction to fire it, regardless of the number of attacks you can normally make.",
    ),
    cl(
        "weapons",
        "range",
        "**Range.** A Range weapon has a range in parentheses after the Ammunition or Thrown property. The range lists two numbers. The first is the weapon's normal range in feet, and the second is the weapon's long range. When attacking a target beyond normal range, you have Disadvantage on the attack roll. You can't attack a target beyond the long range.",
    ),
    cl(
        "weapons",
        "reach",
        "**Reach.** A Reach weapon adds 5 feet to your reach when you attack with it, as well as when determining your reach for Opportunity Attacks with it.",
    ),
    cl(
        "weapons",
        "thrown",
        "**Thrown.** If a weapon has the Thrown property, you can throw the weapon to make a ranged attack, and you can draw that weapon as part of the attack. If the weapon is a Melee weapon, use the same ability modifier for the attack and damage rolls that you use for a melee attack with that weapon.",
    ),
    cl(
        "weapons",
        "two_handed",
        "**Two-Handed.** A Two-Handed weapon requires two hands when you attack with it.",
    ),
    cl(
        "weapons",
        "versatile",
        "**Versatile.** A Versatile weapon can be used with one or two hands. A damage value in parentheses appears with the property. The weapon deals that damage when used with two hands to make a melee attack.",
    ),
    cl(
        "weapons",
        "mastery_properties",
        "Each weapon has a mastery property, which is usable only by a character who has a feature, such as Weapon Mastery, that unlocks the property for the character. The properties are defined below.",
    ),
    cl(
        "weapons",
        "improvised_weapons",
        '> **Improvised Weapons**\n>\n> If you use an object—such as a table leg, frying pan, or bottle—as a makeshift weapon, see "Improvised Weapons" in "Rules Glossary." Also see those rules if you wield a weapon in an unusual way, such as using a Ranged weapon to make a melee attack.',
    ),
    cl(
        "weapons",
        "cleave",
        "**Cleave.** If you hit a creature with a melee attack roll using this weapon, you can make a melee attack roll with the weapon against a second creature within 5 feet of the first that is also within your reach. On a hit, the second creature takes the weapon's damage, but don't add your ability modifier to that damage unless that modifier is negative. You can make this extra attack only once per turn.",
    ),
    cl(
        "weapons",
        "graze",
        "**Graze.** If your attack roll with this weapon misses a creature, you can deal damage to that creature equal to the ability modifier you used to make the attack roll. This damage is the same type dealt by the weapon, and the damage can be increased only by increasing the ability modifier.",
    ),
    cl(
        "weapons",
        "nick",
        "**Nick.** When you make the extra attack of the Light property, you can make it as part of the Attack action instead of as a Bonus Action. You can make this extra attack only once per turn.",
    ),
    cl(
        "weapons",
        "push",
        "**Push.** If you hit a creature with this weapon, you can push the creature up to 10 feet straight away from yourself if it is Large or smaller.",
    ),
    cl(
        "weapons",
        "sap",
        "**Sap.** If you hit a creature with this weapon, that creature has Disadvantage on its next attack roll before the start of your next turn.",
    ),
    cl(
        "weapons",
        "slow",
        "**Slow.** If you hit a creature with this weapon and deal damage to it, you can reduce its Speed by 10 feet until the start of your next turn. If the creature is hit more than once by weapons that have this property, the Speed reduction doesn't exceed 10 feet.",
    ),
    cl(
        "weapons",
        "topple",
        "**Topple.** If you hit a creature with this weapon, you can force the creature to make a Constitution saving throw (DC 8 plus the ability modifier used to make the attack roll and your Proficiency Bonus). On a failed save, the creature has the Prone condition.",
    ),
    cl(
        "weapons",
        "vex",
        "**Vex.** If you hit a creature with this weapon and deal damage to the creature, you have Advantage on your next attack roll against that creature before the end of your next turn.",
    ),
    cl(
        "armor",
        "armor_table",
        "The Armor table lists the game's main armor. The table includes the cost and weight of armor, as well as the following details:",
        *ARMOR_PIECES,
    ),
    cl(
        "armor",
        "category",
        "**Category.** Every type of armor falls into a category: Light, Medium, or Heavy. The category determines how long it takes to don or doff the armor (as shown in the table).",
    ),
    cl(
        "armor",
        "armor_class",
        "**Armor Class (AC).** The table's Armor Class column tells you what your base AC is when you wear a type of armor. For example, if you wear Leather Armor, your base AC is 11 plus your Dexterity modifier, whereas your AC is 16 in Chain Mail.",
    ),
    cl(
        "armor",
        "strength",
        "**Strength.** If the table shows a Strength score in the Strength column for an armor type, that armor reduces the wearer's speed by 10 feet unless the wearer has a Strength score equal to or higher than the listed score.",
    ),
    cl(
        "armor",
        "stealth",
        '**Stealth.** If the table shows "Disadvantage" in the Stealth column for an armor type, the wearer has Disadvantage on Dexterity (Stealth) checks.',
    ),
    cl(
        "armor",
        "armor_training",
        "Anyone can don armor or hold a Shield, but only those with training can use them effectively, as explained below. A character's class and other features determine the character's armor training. A monster has training with any armor in its stat block.",
    ),
    cl(
        "armor",
        "light_medium_or_heavy_armor",
        "**Light, Medium, or Heavy Armor.** If you wear Light, Medium, or Heavy armor and lack training with it, you have Disadvantage on any D20 Test that involves Strength or Dexterity, and you can't cast spells.",
    ),
    cl(
        "armor",
        "shield",
        "**Shield.** You gain the Armor Class benefit of a Shield only if you have training with it.",
    ),
    cl(
        "armor",
        "one_at_a_time",
        "A creature can wear only one suit of armor at a time and wield only one Shield at a time.",
    ),
    cl(
        "tools",
        "tools",
        "A tool helps you make specialized ability checks, craft certain items, or both. A tool's description includes the tool's cost and weight, as well as the following entries:",
    ),
    cl(
        "tools",
        "ability",
        "**Ability.** This entry lists the ability to use when making an ability check with the tool.",
    ),
    cl(
        "tools",
        "utilize",
        "**Utilize.** This entry lists things you can do with the tool when you take the Utilize action. You can do one of those things each time you take the action. This entry also provides the DC for the action.",
    ),
    cl(
        "tools",
        "craft",
        '**Craft.** This entry lists what, if anything, you can craft with the tool. For crafting rules, see "Crafting Nonmagical Items," "Brewing Potions of Healing," and "Scribing Spell Scrolls" later in "Equipment."',
    ),
    cl(
        "tools",
        "variants",
        "**Variants.** This entry appears if the tool has variants, which are listed. Each requires a separate proficiency.",
    ),
    cl(
        "tools",
        "tool_proficiency",
        "If you have proficiency with a tool, add your Proficiency Bonus to any ability check you make that uses the tool. If you have proficiency in a skill that's used with that check, you have Advantage on the check too.",
        "Your features might give you proficiency with a tool. A monster has proficiency with any tool in its stat block.",
    ),
    cl(
        "tools",
        "artisans_tools",
        "Artisan's Tools are each focused on crafting items and pursuing a trade. Each of these tools requires a separate proficiency.",
    ),
    cl(
        "tools",
        "alchemists_supplies",
        "**Alchemist's Supplies (50 GP)**",
        "**Ability:** Intelligence **Weight:** 8 lb.\n**Utilize:** Identify a substance (DC 15), or start a fire (DC 15)\n**Craft:** Acid, Alchemist's Fire, Component Pouch, Oil, Paper, Perfume",
    ),
    cl(
        "tools",
        "brewers_supplies",
        "**Brewer's Supplies (20 GP)**",
        "**Ability:** Intelligence **Weight:** 9 lb.\n**Utilize:** Detect poisoned drink (DC 15), or identify alcohol (DC 10)\n**Craft:** Antitoxin",
    ),
    cl(
        "tools",
        "calligraphers_supplies",
        "**Calligrapher's Supplies (10 GP)**",
        "**Ability:** Dexterity **Weight:** 5 lb.\n**Utilize:** Write text with impressive flourishes that guard against forgery (DC 15)\n**Craft:** Ink, _Spell Scroll_",
    ),
    cl(
        "tools",
        "carpenters_tools",
        "**Carpenter's Tools (8 GP)**",
        "**Ability:** Strength **Weight:** 6 lb.\n**Utilize:** Seal or pry open a door or container (DC 20)\n**Craft:** Club, Greatclub, Quarterstaff, Barrel, Chest, Ladder, Pole, Portable Ram, Torch",
    ),
    cl(
        "tools",
        "cartographers_tools",
        "**Cartographer's Tools (15 GP)**",
        "**Ability:** Wisdom **Weight:** 6 lb.\n**Utilize:** Draft a map of a small area (DC 15)\n**Craft:** Map",
    ),
    cl(
        "tools",
        "cobblers_tools",
        "**Cobbler's Tools (5 GP)**",
        "**Ability:** Dexterity **Weight:** 5 lb.\n**Utilize:** Modify footwear to give Advantage on the wearer's next Dexterity (Acrobatics) check (DC 10)\n**Craft:** Climber's Kit",
    ),
    cl(
        "tools",
        "cooks_utensils",
        "**Cook's Utensils (1 GP)**",
        "**Ability:** Wisdom **Weight:** 8 lb.\n**Utilize:** Improve food's flavor (DC 10), or detect spoiled or poisoned food (DC 15)\n**Craft:** Rations",
    ),
    cl(
        "tools",
        "glassblowers_tools",
        "**Glassblower's Tools (30 GP)**",
        "**Ability:** Intelligence **Weight:** 5 lb.\n**Utilize:** Discern what a glass object held in the past 24 hours (DC 15)\n**Craft:** Glass Bottle, Magnifying Glass, Spyglass, Vial",
    ),
    cl(
        "tools",
        "jewelers_tools",
        "**Jeweler's Tools (25 GP)**",
        "**Ability:** Intelligence **Weight:** 2 lb.\n**Utilize:** Discern a gem's value (DC 15)\n**Craft:** Arcane Focus, Holy Symbol",
    ),
    cl(
        "tools",
        "leatherworkers_tools",
        "**Leatherworker's Tools (5 GP)**",
        "**Ability:** Dexterity **Weight:** 5 lb.\n**Utilize:** Add a design to a leather item (DC 10)\n**Craft:** Sling, Whip, Hide Armor, Leather Armor, Studded Leather Armor, Backpack, Crossbow Bolt Case, Map or Scroll Case, Parchment, Pouch, Quiver, Waterskin",
    ),
    cl(
        "tools",
        "masons_tools",
        "**Mason's Tools (10 GP)**",
        "**Ability:** Strength **Weight:** 8 lb.\n**Utilize:** Chisel a symbol or hole in stone (DC 10)\n**Craft:** Block and Tackle",
    ),
    cl(
        "tools",
        "painters_supplies",
        "**Painter's Supplies (10 GP)**",
        "**Ability:** Wisdom **Weight:** 5 lb.\n**Utilize:** Paint a recognizable image of something you've seen (DC 10)\n**Craft:** Druidic Focus, Holy Symbol",
    ),
    cl(
        "tools",
        "potters_tools",
        "**Potter's Tools (10 GP)**",
        "**Ability:** Intelligence **Weight:** 3 lb.\n**Utilize:** Discern what a ceramic object held in the past 24 hours (DC 15)\n**Craft:** Jug, Lamp",
    ),
    cl(
        "tools",
        "smiths_tools",
        "**Smith's Tools (20 GP)**",
        "**Ability:** Strength **Weight:** 8 lb.\n**Utilize:** Pry open a door or container (DC 20)\n**Craft:** Any Melee weapon (except Club, Greatclub, Quarterstaff, and Whip), Medium armor (except Hide), Heavy armor, Ball Bearings, Bucket, Caltrops, Chain, Crowbar, Firearm Bullets, Grappling Hook, Iron Pot, Iron Spikes, Sling Bullets",
    ),
    cl(
        "tools",
        "tinkers_tools",
        "**Tinker's Tools (50 GP)**\n**Ability:** Dexterity **Weight:** 10 lb.\n**Utilize:** Assemble a Tiny item composed of scrap, which falls apart in 1 minute (DC 20)\n**Craft:** Musket, Pistol, Bell, Bullseye Lantern, Flask, Hooded Lantern, Hunting Trap, Lock, Manacles, Mirror, Shovel, Signal Whistle, Tinderbox",
    ),
    cl(
        "tools",
        "weavers_tools",
        "**Weaver's Tools (1 GP)**\n**Ability:** Dexterity **Weight:** 5 lb.\n**Utilize:** Mend a tear in clothing (DC 10), or sew a Tiny design (DC 10)\n**Craft:** Padded Armor, Basket, Bedroll, Blanket, Fine Clothes, Net, Robe, Rope, Sack, String, Tent, Traveler's Clothes",
    ),
    cl(
        "tools",
        "woodcarvers_tools",
        "**Woodcarver's Tools (1 GP)**\n**Ability:** Dexterity **Weight:** 5 lb.\n**Utilize:** Carve a pattern in wood (DC 10)\n**Craft:** Club, Greatclub, Quarterstaff, Ranged weapons (except Pistol, Musket, and Sling), Arcane Focus, Arrows, Bolts, Druidic Focus, Ink Pen, Needles",
    ),
    cl(
        "tools",
        "disguise_kit",
        "**Disguise Kit (25 GP)**\n**Ability:** Charisma **Weight:** 3 lb.\n**Utilize:** Apply makeup (DC 10)\n**Craft:** Costume",
    ),
    cl(
        "tools",
        "forgery_kit",
        "**Forgery Kit (15 GP)**\n**Ability:** Dexterity **Weight:** 5 lb.\n**Utilize:** Mimic 10 or fewer words of someone else's handwriting (DC 15), or duplicate a wax seal (DC 20)",
    ),
    cl(
        "tools",
        "gaming_set",
        "**Gaming Set (Varies)**\n**Ability:** Wisdom **Weight:** —\n**Utilize:** Discern whether someone is cheating (DC 10), or win the game (DC 20)\n**Variants:** Dice (1 SP), dragonchess (1 GP), playing cards (5 SP), three-dragon ante (1 GP)",
    ),
    cl(
        "tools",
        "herbalism_kit",
        "**Herbalism Kit (5 GP)**\n**Ability:** Intelligence **Weight:** 3 lb.\n**Utilize:** Identify a plant (DC 10)\n**Craft:** Antitoxin, Candle, Healer's Kit, _Potion of Healing_",
    ),
    cl(
        "tools",
        "musical_instrument",
        "**Musical Instrument (Varies)**\n**Ability:** Charisma **Weight:** Varies\n**Utilize:** Play a known tune (DC 10), or improvise a song (DC 15)\n**Variants:** Bagpipes (30 GP, 6 lb.), drum (6 GP, 3 lb.), dulcimer (25 GP, 10 lb.), flute (2 GP, 1 lb.), horn (3 GP, 2 lb.), lute (35 GP, 2 lb.), lyre (30 GP, 2 lb.), pan flute (12 GP, 2 lb.), shawm (2 GP, 1 lb.), viol (30 GP, 1 lb.)",
    ),
    cl(
        "tools",
        "navigators_tools",
        "**Navigator's Tools (25 GP)**\n**Ability:** Wisdom **Weight:** 2 lb.\n**Utilize:** Plot a course (DC 10), or determine position by stargazing (DC 15)",
    ),
    cl(
        "tools",
        "poisoners_kit",
        "**Poisoner's Kit (50 GP)**\n**Ability:** Intelligence **Weight:** 2 lb.\n**Utilize:** Detect a poisoned object (DC 10)\n**Craft:** Basic Poison",
    ),
    cl(
        "tools",
        "thieves_tools",
        "**Thieves' Tools (25 GP)**\n**Ability:** Dexterity **Weight:** 1 lb.\n**Utilize:** Pick a lock (DC 15), or disarm a trap (DC 15)",
    ),
    cl(
        "adventuring_gear",
        "adventuring_gear_table",
        "The Adventuring Gear table in this section includes gear that adventurers often find useful. These items are described here in alphabetical order, with an item's price appearing after its name.",
        *GEAR_PIECES,
    ),
    cl(
        "adventuring_gear",
        "acid",
        "#### Acid (25 GP)",
        "When you take the Attack action, you can replace one of your attacks with throwing a vial of Acid. Target one creature or object you can see within 20 feet of yourself. The target must succeed on a Dexterity saving throw (DC 8 plus your Dexterity modifier and Proficiency Bonus) or take 2d6 Acid damage.",
    ),
    cl(
        "adventuring_gear",
        "alchemists_fire",
        "#### Alchemist's Fire (50 GP)",
        'When you take the Attack action, you can replace one of your attacks with throwing a flask of Alchemist\'s Fire. Target one creature or object you can see within 20 feet of yourself. The target must succeed on a Dexterity saving throw (DC 8 plus your Dexterity modifier and Proficiency Bonus) or take 1d4 Fire damage and start burning (see "Rules Glossary").',
    ),
    cl(
        "adventuring_gear",
        "ammunition",
        "#### Ammunition (Varies)",
        "Ammunition is required by a weapon that has the Ammunition property. A weapon's description specifies the type of ammunition used by the weapon. The Ammunition table lists the different types and the amount you get when you buy them. The table also lists the item that is typically used to store each type; storage must be bought separately.",
        *AMMUNITION_PIECES,
    ),
    cl(
        "adventuring_gear",
        "antitoxin",
        "#### Antitoxin (50 GP)",
        "As a Bonus Action, you can drink a vial of Antitoxin to gain Advantage on saving throws to avoid or end the Poisoned condition for 1 hour.",
    ),
    cl(
        "adventuring_gear",
        "arcane_focus",
        "#### Arcane Focus (Varies)",
        "An Arcane Focus takes one of the forms in the Arcane Focuses table and is bejeweled or carved to channel arcane magic. A Sorcerer, Warlock, or Wizard can use such an item as a Spellcasting Focus.",
        *ARCANE_FOCUSES_PIECES,
    ),
    cl(
        "adventuring_gear",
        "backpack",
        "#### Backpack (2 GP)",
        "A Backpack holds up to 30 pounds within 1 cubic foot. It can also serve as a saddlebag.",
    ),
    cl(
        "adventuring_gear",
        "ball_bearings",
        "#### Ball Bearings (1 GP)",
        "As a Utilize action, you can spill Ball Bearings from their pouch. They spread to cover a level, 10-foot-square area within 10 feet of yourself. A creature that enters this area for the first time on a turn must succeed on a DC 10 Dexterity saving throw or have the Prone condition. It takes 10 minutes to recover the Ball Bearings.",
    ),
    cl(
        "adventuring_gear",
        "barrel",
        "#### Barrel (2 GP)",
        "A Barrel holds up to 40 gallons of liquid or up to 4 cubic feet of dry goods.",
    ),
    cl(
        "adventuring_gear",
        "basket",
        "#### Basket (4 SP)",
        "A Basket holds up to 40 pounds within 2 cubic feet.",
    ),
    cl(
        "adventuring_gear",
        "bedroll",
        "#### Bedroll (1 GP)",
        'A Bedroll sleeps one Small or Medium creature. While in a Bedroll, you automatically succeed on saving throws against extreme cold (see "Gameplay Toolbox").',
    ),
    cl(
        "adventuring_gear",
        "bell",
        "#### Bell (1 GP)",
        "When rung as a Utilize action, a Bell produces a sound that can be heard up to 60 feet away.",
    ),
    cl(
        "adventuring_gear",
        "blanket",
        "#### Blanket (5 SP)",
        'While wrapped in a blanket, you have Advantage on saving throws against extreme cold (see "Gameplay Toolbox").',
    ),
    cl(
        "adventuring_gear",
        "block_and_tackle",
        "#### Block and Tackle (1 GP)",
        "A Block and Tackle allows you to hoist up to four times the weight you can normally lift.",
    ),
    cl(
        "adventuring_gear",
        "book",
        "#### Book (25 GP)",
        "A Book contains fiction or nonfiction. If you consult an accurate nonfiction Book about its topic, you gain a +5 bonus to Intelligence (Arcana, History, Nature, or Religion) checks you make about that topic.",
    ),
    cl(
        "adventuring_gear",
        "bottle_glass",
        "#### Bottle, Glass (2 GP)",
        "A Glass Bottle holds up to 1½ pints.",
    ),
    cl(
        "adventuring_gear",
        "bucket",
        "#### Bucket (5 CP)",
        "A Bucket holds up to half a cubic foot of contents.",
    ),
    cl(
        "adventuring_gear",
        "burglars_pack",
        "#### Burglar's Pack (16 GP)",
        "A Burglar's Pack contains the following items: Backpack, Ball Bearings, Bell, 10 Candles, Crowbar, Hooded Lantern, 7 flasks of Oil, 5 days of Rations, Rope, Tinderbox, and Waterskin.",
    ),
    cl(
        "adventuring_gear",
        "caltrops",
        "#### Caltrops (1 GP)",
        "As a Utilize action, you can spread Caltrops from their bag to cover a 5-foot-square area within 5 feet of yourself. A creature that enters this area for the first time on a turn must succeed on a DC 15 Dexterity saving throw or take 1 Piercing damage and have its Speed reduced to 0 until the start of its next turn. It takes 10 minutes to recover the Caltrops.",
    ),
    cl(
        "adventuring_gear",
        "candle",
        "#### Candle (1 CP)",
        "For 1 hour, a lit Candle sheds Bright Light in a 5-foot radius and Dim Light for an additional 5 feet.",
    ),
    cl(
        "adventuring_gear",
        "case_crossbow_bolt",
        "#### Case, Crossbow Bolt (1 GP)",
        "A Crossbow Bolt Case holds up to 20 Bolts.",
    ),
    cl(
        "adventuring_gear",
        "case_map_or_scroll",
        "#### Case, Map or Scroll (1 GP)",
        "A Map or Scroll Case holds up to 10 sheets of paper or 5 sheets of parchment.",
    ),
    cl(
        "adventuring_gear",
        "chain",
        "#### Chain (5 GP)",
        "As a Utilize action, you can wrap a Chain around an unwilling creature within 5 feet of yourself that has the Grappled, Incapacitated, or Restrained condition if you succeed on a DC 13 Strength (Athletics) check. If the creature's legs are bound, the creature has the Restrained condition until it escapes. Escaping the Chain requires the creature to make a successful DC 18 Dexterity (Acrobatics) check as an action. Bursting the Chain requires a successful DC 20 Strength (Athletics) check as an action.",
    ),
    cl(
        "adventuring_gear",
        "chest",
        "#### Chest (5 GP)",
        "A Chest holds up to 12 cubic feet of contents.",
    ),
    cl(
        "adventuring_gear",
        "climbers_kit",
        "#### Climber's Kit (25 GP)",
        "A Climber's Kit includes boot tips, gloves, pitons, and a harness. As a Utilize action, you can use the Climber's Kit to anchor yourself; when you do, you can't fall more than 25 feet from the anchor point, and you can't move more than 25 feet from there without undoing the anchor as a Bonus Action.",
    ),
    cl(
        "adventuring_gear",
        "clothes_fine",
        "#### Clothes, Fine (15 GP)",
        "Fine Clothes are made of expensive fabrics and adorned with expertly crafted details. Some events and locations admit only people wearing these clothes.",
    ),
    cl(
        "adventuring_gear",
        "clothes_travelers",
        "#### Clothes, Traveler's (2 GP)",
        "Traveler's Clothes are resilient garments designed for travel in various environments.",
    ),
    cl(
        "adventuring_gear",
        "component_pouch",
        "#### Component Pouch (25 GP)",
        "A Component Pouch is watertight and filled with compartments that hold all the free Material components of your spells.",
    ),
    cl(
        "adventuring_gear",
        "costume",
        "#### Costume (5 GP)",
        "While wearing a Costume, you have Advantage on any ability check you make to impersonate the person or type of person it represents.",
    ),
    cl(
        "adventuring_gear",
        "crowbar",
        "#### Crowbar (2 GP)",
        "Using a Crowbar gives you Advantage on Strength checks where the Crowbar's leverage can be applied.",
    ),
    cl(
        "adventuring_gear",
        "diplomats_pack",
        "#### Diplomat's Pack (39 GP)",
        "A Diplomat's Pack contains the following items: Chest, Fine Clothes, Ink, 5 Ink Pens, Lamp, 2 Map or Scroll Cases, 4 flasks of Oil, 5 sheets of Paper, 5 sheets of Parchment, Perfume, and Tinderbox.",
    ),
    cl(
        "adventuring_gear",
        "druidic_focus",
        "#### Druidic Focus (Varies)",
        "A Druidic Focus takes one of the forms in the Druidic Focuses table and is carved, tied with ribbon, or painted to channel primal magic. A Druid or Ranger can use such an object as a Spellcasting Focus.",
        DRUIDIC_FOCUSES_TABLE,
    ),
    cl(
        "adventuring_gear",
        "dungeoneers_pack",
        "#### Dungeoneer's Pack (12 GP)",
        "A Dungeoneer's Pack contains the following items: Backpack, Caltrops, Crowbar, 2 flasks of Oil, 10 days of Rations, Rope, Tinderbox, 10 Torches, and Waterskin.",
    ),
    cl(
        "adventuring_gear",
        "entertainers_pack",
        "#### Entertainer's Pack (40 GP)",
        "An Entertainer's Pack contains the following items: Backpack, Bedroll, Bell, Bullseye Lantern, 3 Costumes, Mirror, 8 flasks of Oil, 9 days of Rations, Tinderbox, and Waterskin.",
    ),
    cl(
        "adventuring_gear",
        "explorers_pack",
        "#### Explorer's Pack (10 GP)",
        "An Explorer's Pack contains the following items: Backpack, Bedroll, 2 flasks of Oil, 10 days of Rations, Rope, Tinderbox, 10 Torches, and Waterskin.",
    ),
    cl(
        "adventuring_gear",
        "flask",
        "#### Flask (2 CP)",
        "A Flask holds up to 1 pint.",
    ),
    cl(
        "adventuring_gear",
        "grappling_hook",
        "#### Grappling Hook (2 GP)",
        "As a Utilize action, you can throw the Grappling Hook at a railing, a ledge, or another catch within 50 feet of yourself, and the hook catches on if you succeed on a DC 13 Dexterity (Acrobatics) check. If you tied a Rope to the hook, you can then climb it.",
    ),
    cl(
        "adventuring_gear",
        "healers_kit",
        "#### Healer's Kit (5 GP)",
        "A Healer's Kit has ten uses. As a Utilize action, you can expend one of its uses to stabilize an Unconscious creature that has 0 Hit Points without needing to make a Wisdom (Medicine) check.",
    ),
    cl(
        "adventuring_gear",
        "holy_symbol",
        "#### Holy Symbol (Varies)",
        "A Holy Symbol takes one of the forms in the Holy Symbol table and is bejeweled or painted to channel divine magic. A Cleric or Paladin can use a Holy Symbol as a Spellcasting Focus.",
        "The table indicates whether a Holy Symbol needs to be held, worn, or borne on fabric (such as a tabard or banner) or a Shield.",
        HOLY_SYMBOLS_TABLE,
    ),
    cl(
        "adventuring_gear",
        "holy_water",
        "#### Holy Water (25 GP)",
        "When you take the Attack action, you can replace one of your attacks with throwing a flask of Holy Water. Target one creature you can see within 20 feet of yourself. The target must succeed on a Dexterity saving throw (DC 8 plus your Dexterity modifier and Proficiency Bonus) or take 2d8 Radiant damage if it is a Fiend or an Undead.",
    ),
    cl(
        "adventuring_gear",
        "hunting_trap",
        "#### Hunting Trap (5 GP)",
        "As a Utilize action, you can set a Hunting Trap, which is a sawtooth steel ring that snaps shut when a creature steps on a pressure plate in the center.",
        "The trap is affixed by a heavy chain to an immobile object, such as a tree or a spike driven into the ground. A creature that steps on the plate must succeed on a DC 13 Dexterity saving throw or take 1d4 Piercing damage and have its Speed reduced to 0 until the start of its next turn. Thereafter, until the creature breaks free of the trap, its movement is limited by the length of the chain (typically 3 feet). A creature can use its action to make a DC 13 Strength (Athletics) check, freeing itself or another creature within its reach on a success. Each failed check deals 1 Piercing damage to the trapped creature.",
    ),
    cl(
        "adventuring_gear",
        "ink",
        "#### Ink (10 GP)",
        "Ink comes in a 1-ounce bottle, which provides enough ink to write about 500 pages.",
    ),
    cl(
        "adventuring_gear",
        "ink_pen",
        "#### Ink Pen (2 CP)",
        "Using Ink, an Ink Pen is used to write or draw.",
    ),
    cl(
        "adventuring_gear",
        "jug",
        "#### Jug (2 CP)",
        "A Jug holds up to 1 gallon.",
    ),
    cl(
        "adventuring_gear",
        "ladder",
        "#### Ladder (1 SP)",
        "A Ladder is 10 feet tall. You must climb to move up or down it.",
    ),
    cl(
        "adventuring_gear",
        "lamp",
        "#### Lamp (5 SP)",
        "A Lamp burns Oil as fuel to cast Bright Light in a 15-foot radius and Dim Light for an additional 30 feet.",
    ),
    cl(
        "adventuring_gear",
        "lantern_bullseye",
        "#### Lantern, Bullseye (10 GP)",
        "A Bullseye Lantern burns Oil as fuel to cast Bright Light in a 60-foot Cone and Dim Light for an additional 60 feet.",
    ),
    cl(
        "adventuring_gear",
        "lantern_hooded",
        "#### Lantern, Hooded (5 GP)",
        "A Hooded Lantern burns Oil as fuel to cast Bright Light in a 30-foot radius and Dim Light for an additional 30 feet. As a Bonus Action, you can lower the hood, reducing the light to Dim Light in a 5-foot radius, or raise it again.",
    ),
    cl(
        "adventuring_gear",
        "lock",
        "#### Lock (10 GP)",
        "A Lock comes with a key. Without the key, a creature can use Thieves' Tools to pick this Lock with a successful DC 15 Dexterity (Sleight of Hand) check.",
    ),
    cl(
        "adventuring_gear",
        "magnifying_glass",
        "#### Magnifying Glass (100 GP)",
        "A Magnifying Glass grants Advantage on any ability check made to appraise or inspect a highly detailed item. Lighting a fire with a Magnifying Glass requires light as bright as sunlight to focus, tinder to ignite, and about 5 minutes for the fire to ignite.",
    ),
    cl(
        "adventuring_gear",
        "manacles",
        "#### Manacles (2 GP)",
        "As a Utilize action, you can use Manacles to bind an unwilling Small or Medium creature within 5 feet of yourself that has the Grappled, Incapacitated, or Restrained condition if you succeed on a DC 13 Dexterity (Sleight of Hand) check. While bound, a creature has Disadvantage on attack rolls, and the creature is Restrained if the Manacles are attached to a chain or hook that is fixed in place. Escaping the Manacles requires a successful DC 20 Dexterity (Sleight of Hand) check as an action. Bursting them requires a successful DC 25 Strength (Athletics) check as an action.",
        "Each set of Manacles comes with a key. Without the key, a creature can use Thieves' Tools to pick the Manacles' lock with a successful DC 15 Dexterity (Sleight of Hand) check.",
    ),
    cl(
        "adventuring_gear",
        "map",
        "#### Map (1 GP)",
        "If you consult an accurate Map, you gain a +5 bonus to Wisdom (Survival) checks you make to find your way in the place represented on it.",
    ),
    cl(
        "adventuring_gear",
        "mirror",
        "#### Mirror (5 GP)",
        "A handheld steel Mirror is useful for personal cosmetics but also for peeking around corners and reflecting light as a signal.",
    ),
    cl(
        "adventuring_gear",
        "net",
        "#### Net (1 GP)",
        "When you take the Attack action, you can replace one of your attacks with throwing a Net. Target a creature you can see within 15 feet of yourself. The target must succeed on a Dexterity saving throw (DC 8 plus your Dexterity modifier and Proficiency Bonus) or have the Restrained condition until it escapes. The target succeeds automatically if it is Huge or larger.",
        "To escape, the target or a creature within 5 feet of it must take an action to make a DC 10 Strength (Athletics) check, freeing the Restrained creature on a success. Destroying the Net (AC 10; 5 HP; Immunity to Bludgeoning, Poison, and Psychic damage) also frees the target, ending the effect.",
    ),
    cl(
        "adventuring_gear",
        "oil",
        "#### Oil (1 SP)",
        "You can douse a creature, object, or space with Oil or use it as fuel, as detailed below.",
        "_Dousing a Creature or an Object._ When you take the Attack action, you can replace one of your attacks with throwing an Oil flask. Target one creature or object within 20 feet of yourself. The target must succeed on a Dexterity saving throw (DC 8 plus your Dexterity modifier and Proficiency Bonus) or be covered in oil. If the target takes Fire damage before the oil dries (after 1 minute), the target takes an extra 5 Fire damage from burning oil.",
        "_Dousing a Space._ You can take the Utilize action to pour an Oil flask on level ground to cover a 5-foot-square area within 5 feet of yourself. If lit, the oil burns until the end of the turn 2 rounds from when the oil was lit (or 12 seconds) and deals 5 Fire damage to any creature that enters the area or ends its turn there. A creature can take this damage only once per turn.",
        "_Fuel._ Oil serves as fuel for Lamps and Lanterns. Once lit, a flask of Oil burns for 6 hours in a Lamp or Lantern. That duration doesn't need to be consecutive; you can extinguish the burning Oil (as a Utilize action) and rekindle it again until it has burned for a total of 6 hours.",
    ),
    cl(
        "adventuring_gear",
        "paper",
        "#### Paper (2 SP)",
        "One sheet of Paper can hold about 250 handwritten words.",
    ),
    cl(
        "adventuring_gear",
        "parchment",
        "#### Parchment (1 SP)",
        "One sheet of Parchment can hold about 250 handwritten words.",
    ),
    cl(
        "adventuring_gear",
        "perfume",
        "#### Perfume (5 GP)",
        "Perfume comes in a 4-ounce vial. For 1 hour after applying Perfume to yourself, you have Advantage on Charisma (Persuasion) checks made to influence an Indifferent Humanoid within 5 feet of yourself.",
    ),
    cl(
        "adventuring_gear",
        "poison_basic",
        "#### Poison, Basic (100 GP)",
        "As a Bonus Action, you can use a vial of Basic Poison to coat one weapon or up to three pieces of ammunition. A creature that takes Piercing or Slashing damage from the poisoned weapon or ammunition takes an extra 1d4 Poison damage. Once applied, the poison retains potency for 1 minute or until its damage is dealt, whichever comes first.",
    ),
    cl(
        "adventuring_gear",
        "pole",
        "#### Pole (5 CP)",
        "A Pole is 10 feet long. You can use it to touch something up to 10 feet away. If you must make a Strength (Athletics) check as part of a High or Long Jump, you can use the Pole to vault, giving yourself Advantage on the check.",
    ),
    cl(
        "adventuring_gear",
        "pot_iron",
        "#### Pot, Iron (2 GP)",
        "An Iron Pot holds up to 1 gallon.",
    ),
    cl(
        "adventuring_gear",
        "potion_of_healing",
        "#### Potion of Healing (50 GP)",
        "This potion is a magic item. As a Bonus Action, you can drink it or administer it to another creature within 5 feet of yourself. The creature that drinks the magical red fluid in this vial regains 2d4 + 2 Hit Points.",
    ),
    cl(
        "adventuring_gear",
        "pouch",
        "#### Pouch (5 SP)",
        "A Pouch holds up to 6 pounds within one-fifth of a cubic foot.",
    ),
    cl(
        "adventuring_gear",
        "priests_pack",
        "#### Priest's Pack (33 GP)",
        "A Priest's Pack contains the following items: Backpack, Blanket, Holy Water, Lamp, 7 days of Rations, Robe, and Tinderbox.",
    ),
    cl(
        "adventuring_gear",
        "quiver",
        "#### Quiver (1 GP)",
        "A Quiver holds up to 20 Arrows.",
    ),
    cl(
        "adventuring_gear",
        "ram_portable",
        "#### Ram, Portable (4 GP)",
        "You can use a Portable Ram to break down doors. When doing so, you gain a +4 bonus to the Strength check. One other character can help you use the ram, giving you Advantage on this check.",
    ),
    cl(
        "adventuring_gear",
        "rations",
        "#### Rations (5 SP)",
        'Rations consist of travel-ready food, including jerky, dried fruit, hardtack, and nuts. See "Malnutrition" in "Rules Glossary" for the risks of not eating.',
    ),
    cl(
        "adventuring_gear",
        "robe",
        "#### Robe (1 GP)",
        "A Robe has vocational or ceremonial significance. Some events and locations admit only people wearing a Robe bearing certain colors or symbols.",
    ),
    cl(
        "adventuring_gear",
        "rope",
        "#### Rope (1 GP)",
        "As a Utilize action, you can tie a knot with Rope if you succeed on a DC 10 Dexterity (Sleight of Hand) check. The Rope can be burst with a successful DC 20 Strength (Athletics) check.",
        "You can bind an unwilling creature with the Rope only if the creature has the Grappled, Incapacitated, or Restrained condition. If the creature's legs are bound, the creature has the Restrained condition until it escapes. Escaping the Rope requires the creature to make a successful DC 15 Dexterity (Acrobatics) check as an action.",
    ),
    cl(
        "adventuring_gear",
        "sack",
        "#### Sack (1 CP)",
        "A Sack holds up to 30 pounds within 1 cubic foot.",
    ),
    cl(
        "adventuring_gear",
        "scholars_pack",
        "#### Scholar's Pack (40 GP)",
        "A Scholar's Pack contains the following items: Backpack, Book, Ink, Ink Pen, Lamp, 10 flasks of Oil, 10 sheets of Parchment, and Tinderbox.",
    ),
    cl(
        "adventuring_gear",
        "shovel",
        "#### Shovel (2 GP)",
        "Working for 1 hour, you can use a Shovel to dig a hole that is 5 feet on each side in soil or similar material.",
    ),
    cl(
        "adventuring_gear",
        "signal_whistle",
        "#### Signal Whistle (5 CP)",
        "When blown as a Utilize action, a Signal Whistle produces a sound that can be heard up to 600 feet away.",
    ),
    cl(
        "adventuring_gear",
        "spell_scroll",
        "#### Spell Scroll (Cantrip, 30 GP; Level 1, 50 GP)",
        "A _Spell Scroll_ (Cantrip) or _Spell Scroll_ (Level 1) is a magic item that bears the words of a cantrip or level 1 spell, respectively, determined by the scroll's creator. If the spell is on your class's spell list, you can read the scroll and cast the spell using its normal casting time and without providing any Material components.",
        "If the spell requires a saving throw or an attack roll, the spell save DC is 13, and the attack bonus is +5. The scroll disintegrates when the casting is completed.",
    ),
    cl(
        "adventuring_gear",
        "spikes_iron",
        "#### Spikes, Iron (1 GP)",
        "Iron Spikes come in bundles of ten. As a Utilize action, you can use a blunt object, such as a Light Hammer, to hammer a spike into wood, earth, or a similar material. You can do so to jam a door shut or to then tie a Rope or Chain to the Spike.",
    ),
    cl(
        "adventuring_gear",
        "spyglass",
        "#### Spyglass (1,000 GP)",
        "Objects viewed through a Spyglass are magnified to twice their size.",
    ),
    cl(
        "adventuring_gear",
        "string",
        "#### String (1 SP)",
        "String is 10 feet long. You can tie a knot in it as a Utilize action.",
    ),
    cl(
        "adventuring_gear",
        "tent",
        "#### Tent (2 GP)",
        "A Tent sleeps up to two Small or Medium creatures.",
    ),
    cl(
        "adventuring_gear",
        "tinderbox",
        "#### Tinderbox (5 SP)",
        "A Tinderbox is a small container holding flint, fire steel, and tinder (usually dry cloth soaked in light oil) used to kindle a fire. Using it to light a Candle, Lamp, Lantern, or Torch—or anything else with exposed fuel—takes a Bonus Action. Lighting any other fire takes 1 minute.",
    ),
    cl(
        "adventuring_gear",
        "torch",
        "#### Torch (1 CP)",
        "A Torch burns for 1 hour, casting Bright Light in a 20-foot radius and Dim Light for an additional 20 feet. When you take the Attack action, you can attack with the Torch, using it as a Simple Melee weapon. On a hit, the target takes 1 Fire damage.",
    ),
    cl(
        "adventuring_gear",
        "vial",
        "#### Vial (1 GP)",
        "A Vial holds up to 4 ounces.",
    ),
    cl(
        "adventuring_gear",
        "waterskin",
        "#### Waterskin (2 SP)",
        'A Waterskin holds up to 4 pints. If you don\'t drink sufficient water, you risk dehydration (see "Rules Glossary").',
    ),
    cl(
        "mounts_and_vehicles",
        "mounts",
        "A mount can help you move more quickly through the wilderness, but its primary purpose is to carry gear that would otherwise slow you down. The Mounts and Other Animals table shows each animal's carrying capacity. See \"Monsters\" for the animals' stat blocks.",
        MOUNTS_TABLE,
    ),
    cl(
        "mounts_and_vehicles",
        "mounts_and_cargo",
        "An animal pulling a carriage, cart, chariot, sled, or wagon can move weight up to five times its base carrying capacity, including the weight of the vehicle. If multiple animals pull the same vehicle, add their carrying capacities together.",
    ),
    cl(
        "mounts_and_vehicles",
        "barding",
        'Barding is armor designed for a mount. Any type of armor on the Armor table in "Equipment" can be purchased as barding. The cost is four times the normal cost, and it weighs twice as much.',
    ),
    cl(
        "mounts_and_vehicles",
        "saddles",
        "A saddle comes with a bit, a bridle, reins, and any other equipment needed to use the saddle. A Military Saddle gives Advantage on any ability check you make to remain mounted. An Exotic Saddle is required for riding an aquatic or a flying mount.",
    ),
    cl(
        "mounts_and_vehicles",
        "tack_harness_and_drawn_vehicles",
        TACK_TABLE,
    ),
    cl(
        "mounts_and_vehicles",
        "large_vehicles",
        "The Airborne and Waterborne Vehicles table provides statistics for various types of large vehicles. The following notes apply.",
        *VEHICLES_PIECES,
    ),
    cl(
        "mounts_and_vehicles",
        "speed",
        "A ship sailing against a strong wind moves at half speed. In a dead calm (no wind), waterborne ships can't move under sail and must be rowed. Keelboats and Rowboats are used on lakes and rivers. If going downstream, add the speed of the current (typically 3 miles per hour) to the speed of the vehicle. These vehicles can't be rowed against any significant current, but they can be pulled upstream by draft animals on the shores. A Rowboat can be carried and weighs 100 pounds.",
    ),
    cl(
        "mounts_and_vehicles",
        "crew",
        'A ship larger than a Keelboat or Rowboat needs a crew of skilled hirelings (see "Hirelings" later in "Equipment") to function. The minimum number of skilled hirelings needed to crew a ship depends on the type of ship, as shown in the table.',
    ),
    cl(
        "mounts_and_vehicles",
        "passengers",
        "The table lists the number of Small and Medium passengers the ship can accommodate using hammocks. A ship outfitted with private accommodations can carry one-fifth as many passengers. A passenger usually pays 5 SP per day for a hammock, but prices can vary from ship to ship. A small private cabin usually costs 2 GP per day.",
    ),
    cl(
        "mounts_and_vehicles",
        "damage_threshold",
        'If a vehicle has a damage threshold (see "Rules Glossary"), it\'s noted in the table.',
    ),
    cl(
        "mounts_and_vehicles",
        "ship_repair",
        "Repairs to a damaged ship can be made while the vessel is berthed. Repairing 1 Hit Point of damage requires 1 day and costs 20 GP for materials and labor. If the repairs are made in a location where supplies and skilled labor are abundant, such as a city shipyard, the repair time and cost are halved.",
    ),
    cl(
        "lifestyle_expenses",
        "lifestyle_expenses",
        "Lifestyle expenses summarize the cost of living in a fantasy world. They cover lodging, food, equipment maintenance, and other necessities.",
        "At the start of each week or month (GM's choice), choose a lifestyle below—Wretched, Squalid, Poor, Modest, Comfortable, Wealthy, or Aristocratic—and pay the price to sustain that lifestyle.",
    ),
    cl(
        "lifestyle_expenses",
        "lifestyle_perception",
        "Lifestyles have no inherent consequences, but the GM might take them into account when determining risks or how others perceive your character.",
    ),
    cl(
        "lifestyle_expenses",
        "wretched",
        "### Wretched (Free)",
        "You survive via chance and charity. You're often exposed to natural dangers as a result of sleeping outside.",
    ),
    cl(
        "lifestyle_expenses",
        "squalid",
        "### Squalid (1 SP per Day)",
        "You spend the bare minimum for your necessities. You might be exposed to unhealthy conditions and opportunistic criminals.",
    ),
    cl(
        "lifestyle_expenses",
        "poor",
        "### Poor (2 SP per Day)",
        "You spend frugally for your necessities.",
    ),
    cl(
        "lifestyle_expenses",
        "modest",
        "### Modest (1 GP per Day)",
        "You support yourself at an average level.",
    ),
    cl(
        "lifestyle_expenses",
        "comfortable",
        "### Comfortable (2 GP per Day)",
        "You spend modestly for your necessities and enjoy a few luxuries.",
    ),
    cl(
        "lifestyle_expenses",
        "wealthy",
        "### Wealthy (4 GP per Day)",
        "You're accustomed to the finer things in life and might have servants.",
    ),
    cl(
        "lifestyle_expenses",
        "aristocratic",
        "### Aristocratic (10 GP per Day)",
        "You pay for the best and might have a staff that supports your lifestyle. Others notice your wealth and might encourage you to share it, either legally or otherwise.",
    ),
    cl(
        "food_drink_and_lodging",
        "food_drink_and_lodging",
        "The Food, Drink, and Lodging table gives prices for food and a single night's lodging. Prices for daily lodging and meals are included in your lifestyle's expenses.",
        FOOD_DRINK_AND_LODGING_TABLE,
    ),
    cl(
        "hirelings",
        "hirelings",
        "Skilled hirelings include anyone hired to perform a service that involves a proficiency (including weapon, tool, or skill): a mercenary, an artisan, a scribe, or the like. The pay shown on the Hirelings table is a minimum; some expert hirelings require more pay. Untrained hirelings are hired for work that requires no particular proficiencies; they include laborers and porters.",
        HIRELINGS_TABLE,
    ),
    cl(
        "spellcasting",
        "spellcasting_services",
        "Most settlements contain individuals who are willing to cast spells in exchange for payment. If a spell has expensive components, add the cost of those components to the cost listed in the Spellcasting Services table. The higher the level of a desired spell, the harder it is to find someone to cast it.",
        SPELLCASTING_SERVICES_TABLE,
    ),
    cl(
        "magic_items",
        "magic_items",
        'Adventures hold the promise—but not a guarantee—of finding magic items. Hundreds of magic items are detailed in "Magic Items" later in this document. Here\'s what you need to know about using magic items.',
    ),
    cl(
        "magic_items",
        "identifying_a_magic_item",
        "Some magic items are indistinguishable from their nonmagical counterparts, while others are conspicuously magical. Handling a magic item is enough to give you a sense that it is extraordinary, but learning a magic item's properties isn't automatic.",
        "The _Identify_ spell is the fastest way to reveal an item's properties. Alternatively, you can focus on one magic item during a Short Rest while being in physical contact with the item. At the end of the rest, you learn its properties and how to use them (but not any curse the item might bear).",
        "Sometimes a magic item carries a clue to its properties. The command word to activate a ring might be etched inside the band, or a feathered design might hint that it's a _Ring of Feather Falling_.",
        'Wearing or experimenting with an item can also offer hints about its properties. In the specific case of Potions, a little taste is enough to tell the taster what a potion does. Other items might require more experimentation. For example, if your character puts on a _Ring of Swimming_, the GM might say, "Your movement feels strangely fluid." Perhaps you then dive into a river to see what happens. The GM would then say you swim unexpectedly well.',
    ),
    cl(
        "magic_items",
        "attunement",
        "Some magic items require a creature to form a bond—called Attunement—with them before the creature can use an item's magical properties. Without becoming attuned to an item that requires Attunement, you gain only its nonmagical benefits unless its description states otherwise. For example, a magic Shield that requires Attunement provides the benefits of a normal Shield if you aren't attuned to it, but none of its magical properties.",
    ),
    cl(
        "magic_items",
        "attune_during_a_short_rest",
        "Attuning to an item requires you to spend a Short Rest focused on only that item while being in physical contact with it (this can't be the same Short Rest used to learn the item's properties). This focus can take the form of weapon practice (for a Weapon), meditation (for a Wand), or some other appropriate activity. If the Short Rest is interrupted, the Attunement attempt fails. Otherwise, at the end of the Short Rest, you're attuned to the magic item and can access its full magical capabilities.",
    ),
    cl(
        "magic_items",
        "no_more_than_three_items",
        "You can be attuned to no more than three magic items at a time. Any attempt to attune to a fourth item fails; you must end your Attunement to an item first. Additionally, you can't attune to more than one copy of an item. For example, you can't attune to more than one _Ring of Protection_ at a time.",
    ),
    cl(
        "magic_items",
        "ending_attunement",
        "Your Attunement to an item ends if you no longer satisfy the prerequisites for Attunement, if the item has been more than 100 feet away for at least 24 hours, if you die, or if another creature attunes to\nthe item. You can also voluntarily end Attunement by spending another Short Rest focused on the item unless the item is cursed.",
    ),
    cl(
        "magic_items",
        "wearing_and_wielding_items",
        "Using a magic item's properties might mean wearing or wielding it. A magic item meant to be worn must be donned in the intended fashion: boots go on feet, gloves on hands, hats and helmets on a head, and rings on a finger. Magic armor must be donned, a Shield strapped to the arm, a cloak fastened about the shoulders. A weapon must be held.",
        "In most cases, a magic item that's meant to be worn can fit a creature regardless of size or build. Magic garments are made to be easily adjustable, or they magically adjust themselves to the wearer.",
    ),
    cl(
        "magic_items",
        "multiple_items_of_the_same_kind",
        "You can't wear more than one of certain magic items. You can't normally wear more than one pair of footwear, one pair of gloves or gauntlets, one pair of bracers, one suit of armor, one item of headwear, or one cloak. The GM might make exceptions.",
    ),
    cl(
        "magic_items",
        "paired_items",
        "Items that come in pairs—such as boots, bracers, gauntlets, and gloves—impart their benefits only if both items of the pair are worn. For example, a character wearing a _Boot of Striding and Springing_ on one foot and a _Boot of Elvenkind_ on the other foot gains no benefit from either.",
    ),
    cl(
        "crafting_nonmagical_items",
        "crafting_nonmagical_items",
        "To craft a nonmagical item, you need tools, raw materials, and time, each of which is detailed below. If you meet the requirements, you make the item, and you can use it or sell it at its normal price.",
    ),
    cl(
        "crafting_nonmagical_items",
        "tools",
        'The "Tools" section of "Equipment" lists which tools are required to make certain items. The GM assigns required tools for items not listed there.',
        "You must use the required tool to make an item and have proficiency with that tool. Anyone who helps you must also have proficiency with it.",
    ),
    cl(
        "crafting_nonmagical_items",
        "raw_materials",
        "To make an item, you need raw materials worth half its purchase cost (round down). For example, you need 750 GP of raw materials to make Plate Armor, which sells for 1,500 GP. The GM determines whether appropriate raw materials are available.",
    ),
    cl(
        "crafting_nonmagical_items",
        "time",
        "To determine how many days (working 8 hours a day) it takes to make an item, divide its purchase cost in GP by 10 (round a fraction up to a day). For example, you need 5 days to make a Heavy Crossbow, which sells for 50 GP.",
        "If an item requires multiple days, the days needn't be consecutive.",
        "Characters can combine their efforts to shorten the crafting time. Divide the time needed to create an item by the number of characters working on it. Normally, only one other character can assist you, but the GM might allow more assistants.",
    ),
    cl(
        "brewing_potions_of_healing",
        "brewing_potions_of_healing",
        "A character who has proficiency with the Herbalism Kit can create a _Potion of Healing_. Doing so requires using that kit and 25 GP of raw material over the course of 1 day (8 hours of work).",
    ),
    cl(
        "scribing_spell_scrolls",
        "scribing_spell_scrolls",
        "A spellcaster can transfer a spell to a scroll and create a _Spell Scroll_, using the rules below.",
    ),
    cl(
        "scribing_spell_scrolls",
        "time_and_cost",
        "Scribing a scroll takes an amount of time and money based on the level of the spell, as shown in the Spell Scroll Costs table. For each day of inscription, you must work for 8 hours. If a scroll requires multiple days, those days needn't be consecutive.",
        SPELL_SCROLL_COSTS_TABLE,
    ),
    cl(
        "scribing_spell_scrolls",
        "prerequisites_for_the_scribe",
        "To scribe a scroll, you must have proficiency in the Arcana skill or with Calligrapher's Supplies and have the spell prepared on each day of the inscription. You must also have at hand any Material components required by the spell; if the spell consumes its Material components, they are consumed only when you complete the scroll. The scroll's spell uses your spell save DC and spell attack bonus.",
    ),
    cl(
        "scribing_spell_scrolls",
        "cantrips",
        "If the scribed spell is a cantrip, the version on the scroll works as if the caster were your level.",
    ),
)


#: (entry, leaf prefix): whole leaves that introduce the rules after them and
#: state none of their own.
FRAMING: tuple[tuple[str, str], ...] = (
    ("weapons", "Here are definitions of the properties"),
)

SUBSECTION_HEADING = "subsection heading: names a subsection and states no rule"

#: (entry, exact leaf contents, reason): whole leaves that only name a
#: subsection. The priced headings of gear, tools and lifestyles are not here:
#: each states a price and is its own item's clause.
EXCLUDED: tuple[tuple[str, tuple[str, ...], str], ...] = (
    (
        "weapons",
        ("### Weapon Proficiency", "### Properties", "### Mastery Properties"),
        SUBSECTION_HEADING,
    ),
    ("armor", ("### Armor Training", "### One at a Time"), SUBSECTION_HEADING),
    (
        "tools",
        ("### Tool Proficiency", "#### Artisan's Tools", "#### Other Tools"),
        SUBSECTION_HEADING,
    ),
    (
        "mounts_and_vehicles",
        (
            "### Mounts and Cargo",
            "### Barding",
            "### Saddles",
            "### Large Vehicles",
            "#### Speed",
            "#### Crew",
            "#### Passengers",
            "#### Damage Threshold",
            "#### Ship Repair",
        ),
        SUBSECTION_HEADING,
    ),
    (
        "magic_items",
        (
            "### Identifying a Magic Item",
            "### Attunement",
            "#### Attune during a Short Rest",
            "#### No More Than Three Items",
            "#### Ending Attunement",
            "### Wearing and Wielding Items",
            "#### Multiple Items of the Same Kind",
            "#### Paired Items",
        ),
        SUBSECTION_HEADING,
    ),
    (
        "crafting_nonmagical_items",
        ("### Tools", "### Raw Materials", "### Time"),
        SUBSECTION_HEADING,
    ),
    (
        "scribing_spell_scrolls",
        ("### Time and Cost", "### Prerequisites for the Scribe", "### Cantrips"),
        SUBSECTION_HEADING,
    ),
)

# ---------------------------------------------------------------------------
# Representation proposed for the clauses above
# ---------------------------------------------------------------------------

C = EntryComponent


def eq(slug: str) -> Target:
    """A section record of this batch."""
    return (EQUIPMENT, PLACEMENTS[slug].record_key)


WEAPONS = eq("weapons")
ARMOR = eq("armor")
TOOLS = eq("tools")
GEAR = eq("adventuring_gear")


def named(entry: str, key: str) -> str:
    """The record key of an item or rule section *entry* prints."""
    return f"{PLACEMENTS[entry].record_key}.{key}"


def nm(entry: str, key: str) -> Target:
    """A named record of this batch, as a reference target."""
    return (EQUIPMENT, named(entry, key))


E = RecordKind.EQUIPMENT
G = RecordKind.GENERAL_RULE

#: Items and rules a citation names -- an accepted citation, or a pointer of
#: this batch -- each read from its whole clause: (entry, clause key, kind).
#: With them, the properties, masteries and categories the cited weapon and
#: armor rows print, and the armor columns they fill, which interpret them.
NAMED_CLAUSES: tuple[tuple[str, str, RecordKind], ...] = (
    *(
        ("weapons", k, G)
        for k in (
            "category",
            "melee_or_ranged",
            "ammunition",
            "finesse",
            "heavy",
            "light",
            "loading",
            "range",
            "reach",
            "thrown",
            "two_handed",
            "versatile",
            "cleave",
            "graze",
            "nick",
            "push",
            "sap",
            "slow",
            "topple",
            "vex",
        )
    ),
    *(("armor", k, G) for k in ("category", "armor_class", "strength", "stealth")),
    ("armor", "shield", E),
    ("tools", "artisans_tools", G),
    *(
        ("tools", k, E)
        for k in (
            "alchemists_supplies",
            "calligraphers_supplies",
            "jewelers_tools",
            "leatherworkers_tools",
            "smiths_tools",
            "tinkers_tools",
            "weavers_tools",
            "woodcarvers_tools",
            "gaming_set",
            "herbalism_kit",
            "musical_instrument",
            "poisoners_kit",
            "thieves_tools",
        )
    ),
    *(("adventuring_gear", k, E) for k in GEAR_ROWS),
)


def _row_refs(
    *pairs: tuple[str, str], entry: str = "weapons"
) -> tuple[tuple[str, Target], ...]:
    return tuple((text, nm(entry, key)) for text, key in pairs)


def clause(entry: str, key: str) -> tuple[str, ...]:
    """The reviewed texts of one clause."""
    (texts,) = [t for e, k, _, t in CLAUSES if (e, k) == (entry, key)]
    return texts


#: The section rules that govern a named record read on its own, printed
#: before its table: a weapon row's Mastery column needs a feature to use, and
#: its proficiency decides the attack's Proficiency Bonus (printed 89).
WEAPON_RULES = (*clause("weapons", "mastery"), *clause("weapons", "weapon_proficiency"))
SIMPLE_MELEE = (*WEAPON_RULES, WEAPONS_HEAD, WEAPON_GROUPS["Simple Melee Weapons"])
SIMPLE_RANGED = (*WEAPON_RULES, WEAPONS_HEAD, WEAPON_GROUPS["Simple Ranged Weapons"])
MARTIAL_MELEE = (*WEAPON_RULES, WEAPONS_HEAD, WEAPON_GROUPS["Martial Melee Weapons"])
MARTIAL_RANGED = (*WEAPON_RULES, WEAPONS_HEAD, WEAPON_GROUPS["Martial Ranged Weapons"])
#: Printed after the Armor table (printed 92): training and one at a time.
ARMOR_TRAINING = clause("armor", "armor_training")
ONE_AT_A_TIME = clause("armor", "one_at_a_time")
ARMOR_RULES = (
    *ARMOR_TRAINING,
    *clause("armor", "light_medium_or_heavy_armor"),
    *ONE_AT_A_TIME,
)
#: A tool's Utilize entry is one action, one listed thing, and proficiency
#: adds the bonus (printed 93); a listed variant is a separate proficiency.
TOOL_RULES = (*clause("tools", "utilize"), *clause("tools", "tool_proficiency"))
#: A vehicle row is read under the table's own introduction and head, and with
#: the notes that introduction says apply to it, printed after the table.
VEHICLE_CONTEXT = (*clause("mounts_and_vehicles", "large_vehicles")[:1], VEHICLES_HEAD)
VEHICLE_NOTES = tuple(
    t
    for k in ("speed", "crew", "passengers", "damage_threshold", "ship_repair")
    for t in clause("mounts_and_vehicles", k)
)
#: The Wand row is read under the Arcane Focus entry that governs it -- its
#: heading and rule -- and the Arcane Focuses table head.
WAND_CONTEXT = (*clause("adventuring_gear", "arcane_focus")[:2], ARCANE_FOCUSES_HEAD)
AMMUNITION_ENTRY = (
    "#### Ammunition (Varies)",
    "Ammunition is required by a weapon that has the Ammunition property. A weapon's description specifies the type of ammunition used by the weapon. The Ammunition table lists the different types and the amount you get when you buy them. The table also lists the item that is typically used to store each type; storage must be bought separately.",
    AMMUNITION_HEAD,
)


#: Table rows a citation names: (entry, key, kind, the texts read as context,
#: the row, references). A weapon or armor row is read under the table head
#: and its group row; each property, mastery and category a weapon row prints
#: references the rule defining it ("Each property is defined in the
#: "Properties" section"), and its ammunition the row pricing it; an armor row
#: references its category and the column rules its cells fill. An ammunition
#: row is read under the Ammunition entry and its table head.
NAMED_ROWS: tuple[
    tuple[str, str, RecordKind, tuple[str, ...], str, tuple[tuple[str, Target], ...]],
    ...,
] = (
    (
        "weapons",
        "dagger",
        E,
        SIMPLE_MELEE,
        WEAPON_ROWS["Dagger"],
        _row_refs(
            ("Simple", "category"),
            ("Melee", "melee_or_ranged"),
            ("Finesse", "finesse"),
            ("Light", "light"),
            ("Thrown", "thrown"),
            ("Range 20/60", "range"),
            ("Nick", "nick"),
        ),
    ),
    (
        "weapons",
        "quarterstaff",
        E,
        SIMPLE_MELEE,
        WEAPON_ROWS["Quarterstaff"],
        _row_refs(
            ("Simple", "category"),
            ("Melee", "melee_or_ranged"),
            ("Versatile (1d8)", "versatile"),
            ("Topple", "topple"),
        ),
    ),
    (
        "weapons",
        "spear",
        E,
        SIMPLE_MELEE,
        WEAPON_ROWS["Spear"],
        _row_refs(
            ("Simple", "category"),
            ("Melee", "melee_or_ranged"),
            ("Thrown", "thrown"),
            ("Range 20/60", "range"),
            ("Versatile (1d8)", "versatile"),
            ("Sap", "sap"),
        ),
    ),
    (
        "weapons",
        "shortbow",
        E,
        SIMPLE_RANGED,
        WEAPON_ROWS["Shortbow"],
        (
            *_row_refs(
                ("Simple", "category"),
                ("Ranged", "melee_or_ranged"),
                ("Ammunition", "ammunition"),
                ("Range 80/320", "range"),
            ),
            ("Arrow", nm("adventuring_gear", "arrows")),
            *_row_refs(("Two-Handed", "two_handed"), ("Vex", "vex")),
        ),
    ),
    (
        "weapons",
        "club",
        E,
        SIMPLE_MELEE,
        WEAPON_ROWS["Club"],
        _row_refs(
            ("Simple", "category"),
            ("Melee", "melee_or_ranged"),
            ("Light", "light"),
            ("Slow", "slow"),
        ),
    ),
    (
        "weapons",
        "light_hammer",
        E,
        SIMPLE_MELEE,
        WEAPON_ROWS["Light Hammer"],
        _row_refs(
            ("Simple", "category"),
            ("Melee", "melee_or_ranged"),
            ("Light, Thrown", "light"),
            ("Thrown", "thrown"),
            ("Range 20/60", "range"),
            ("Nick", "nick"),
        ),
    ),
    (
        "weapons",
        "sling",
        E,
        SIMPLE_RANGED,
        WEAPON_ROWS["Sling"],
        (
            *_row_refs(
                ("Simple", "category"),
                ("Ranged", "melee_or_ranged"),
                ("Ammunition", "ammunition"),
                ("Range 30/120", "range"),
            ),
            ("Bullet", nm("adventuring_gear", "bullets_sling")),
            *_row_refs(("Slow", "slow")),
        ),
    ),
    (
        "weapons",
        "musket",
        E,
        MARTIAL_RANGED,
        WEAPON_ROWS["Musket"],
        (
            *_row_refs(
                ("Martial", "category"),
                ("Ranged", "melee_or_ranged"),
                ("Ammunition", "ammunition"),
                ("Range 40/120", "range"),
            ),
            ("Bullet", nm("adventuring_gear", "bullets_firearm")),
            *_row_refs(
                ("Loading", "loading"),
                ("Two-Handed", "two_handed"),
                ("Slow", "slow"),
            ),
        ),
    ),
    (
        "armor",
        "padded_armor",
        E,
        (ARMOR_HEAD, ARMOR_GROUPS["Light Armor"]),
        ARMOR_ROWS["Padded Armor"],
        _row_refs(
            ("Light Armor", "category"),
            ("11 + Dex modifier", "armor_class"),
            ("Disadvantage", "stealth"),
            entry="armor",
        ),
    ),
    (
        "armor",
        "hide_armor",
        E,
        (ARMOR_HEAD, ARMOR_GROUPS["Medium Armor"]),
        ARMOR_ROWS["Hide Armor"],
        _row_refs(
            ("Medium Armor", "category"),
            ("12 + Dex modifier (max 2)", "armor_class"),
            entry="armor",
        ),
    ),
    ("adventuring_gear", "arrows", E, AMMUNITION_ENTRY, AMMUNITION_ROWS["Arrows"], ()),
    (
        "adventuring_gear",
        "bullets_firearm",
        E,
        AMMUNITION_ENTRY,
        AMMUNITION_ROWS["Bullets, Firearm"],
        (),
    ),
    (
        "adventuring_gear",
        "bullets_sling",
        E,
        AMMUNITION_ENTRY,
        AMMUNITION_ROWS["Bullets, Sling"],
        (),
    ),
    (
        "weapons",
        "greatclub",
        E,
        SIMPLE_MELEE,
        WEAPON_ROWS["Greatclub"],
        _row_refs(
            ("Simple", "category"),
            ("Melee", "melee_or_ranged"),
            ("Two-Handed", "two_handed"),
            ("Push", "push"),
        ),
    ),
    (
        "weapons",
        "handaxe",
        E,
        SIMPLE_MELEE,
        WEAPON_ROWS["Handaxe"],
        _row_refs(
            ("Simple", "category"),
            ("Melee", "melee_or_ranged"),
            ("Light", "light"),
            ("Thrown", "thrown"),
            ("Range 20/60", "range"),
            ("Vex", "vex"),
        ),
    ),
    (
        "weapons",
        "javelin",
        E,
        SIMPLE_MELEE,
        WEAPON_ROWS["Javelin"],
        _row_refs(
            ("Simple", "category"),
            ("Melee", "melee_or_ranged"),
            ("Thrown", "thrown"),
            ("Range 30/120", "range"),
            ("Slow", "slow"),
        ),
    ),
    (
        "weapons",
        "mace",
        E,
        SIMPLE_MELEE,
        WEAPON_ROWS["Mace"],
        _row_refs(
            ("Simple", "category"),
            ("Melee", "melee_or_ranged"),
            ("Sap", "sap"),
        ),
    ),
    (
        "weapons",
        "sickle",
        E,
        SIMPLE_MELEE,
        WEAPON_ROWS["Sickle"],
        _row_refs(
            ("Simple", "category"),
            ("Melee", "melee_or_ranged"),
            ("Light", "light"),
            ("Nick", "nick"),
        ),
    ),
    (
        "weapons",
        "light_crossbow",
        E,
        SIMPLE_RANGED,
        WEAPON_ROWS["Light Crossbow"],
        (
            *_row_refs(
                ("Simple", "category"),
                ("Ranged", "melee_or_ranged"),
                ("Ammunition", "ammunition"),
                ("Range 80/320", "range"),
            ),
            ("Bolt", nm("adventuring_gear", "bolts")),
            *_row_refs(
                ("Loading", "loading"),
                ("Two-Handed", "two_handed"),
                ("Slow", "slow"),
            ),
        ),
    ),
    (
        "weapons",
        "battleaxe",
        E,
        MARTIAL_MELEE,
        WEAPON_ROWS["Battleaxe"],
        _row_refs(
            ("Martial", "category"),
            ("Melee", "melee_or_ranged"),
            ("Versatile (1d10)", "versatile"),
            ("Topple", "topple"),
        ),
    ),
    (
        "weapons",
        "flail",
        E,
        MARTIAL_MELEE,
        WEAPON_ROWS["Flail"],
        _row_refs(
            ("Martial", "category"),
            ("Melee", "melee_or_ranged"),
            ("Sap", "sap"),
        ),
    ),
    (
        "weapons",
        "greataxe",
        E,
        MARTIAL_MELEE,
        WEAPON_ROWS["Greataxe"],
        _row_refs(
            ("Martial", "category"),
            ("Melee", "melee_or_ranged"),
            ("Heavy", "heavy"),
            ("Two-Handed", "two_handed"),
            ("Cleave", "cleave"),
        ),
    ),
    (
        "weapons",
        "greatsword",
        E,
        MARTIAL_MELEE,
        WEAPON_ROWS["Greatsword"],
        _row_refs(
            ("Martial", "category"),
            ("Melee", "melee_or_ranged"),
            ("Heavy", "heavy"),
            ("Two-Handed", "two_handed"),
            ("Graze", "graze"),
        ),
    ),
    (
        "weapons",
        "longsword",
        E,
        MARTIAL_MELEE,
        WEAPON_ROWS["Longsword"],
        _row_refs(
            ("Martial", "category"),
            ("Melee", "melee_or_ranged"),
            ("Versatile (1d10)", "versatile"),
            ("Sap", "sap"),
        ),
    ),
    (
        "weapons",
        "morningstar",
        E,
        MARTIAL_MELEE,
        WEAPON_ROWS["Morningstar"],
        _row_refs(
            ("Martial", "category"),
            ("Melee", "melee_or_ranged"),
            ("Sap", "sap"),
        ),
    ),
    (
        "weapons",
        "pike",
        E,
        MARTIAL_MELEE,
        WEAPON_ROWS["Pike"],
        _row_refs(
            ("Martial", "category"),
            ("Melee", "melee_or_ranged"),
            ("Heavy", "heavy"),
            ("Reach", "reach"),
            ("Two-Handed", "two_handed"),
            ("Push", "push"),
        ),
    ),
    (
        "weapons",
        "rapier",
        E,
        MARTIAL_MELEE,
        WEAPON_ROWS["Rapier"],
        _row_refs(
            ("Martial", "category"),
            ("Melee", "melee_or_ranged"),
            ("Finesse", "finesse"),
            ("Vex", "vex"),
        ),
    ),
    (
        "weapons",
        "scimitar",
        E,
        MARTIAL_MELEE,
        WEAPON_ROWS["Scimitar"],
        _row_refs(
            ("Martial", "category"),
            ("Melee", "melee_or_ranged"),
            ("Finesse", "finesse"),
            ("Light", "light"),
            ("Nick", "nick"),
        ),
    ),
    (
        "weapons",
        "shortsword",
        E,
        MARTIAL_MELEE,
        WEAPON_ROWS["Shortsword"],
        _row_refs(
            ("Martial", "category"),
            ("Melee", "melee_or_ranged"),
            ("Finesse", "finesse"),
            ("Light", "light"),
            ("Vex", "vex"),
        ),
    ),
    (
        "weapons",
        "warhammer",
        E,
        MARTIAL_MELEE,
        WEAPON_ROWS["Warhammer"],
        _row_refs(
            ("Martial", "category"),
            ("Melee", "melee_or_ranged"),
            ("Versatile (1d10)", "versatile"),
            ("Push", "push"),
        ),
    ),
    (
        "weapons",
        "hand_crossbow",
        E,
        MARTIAL_RANGED,
        WEAPON_ROWS["Hand Crossbow"],
        (
            *_row_refs(
                ("Martial", "category"),
                ("Ranged", "melee_or_ranged"),
                ("Ammunition", "ammunition"),
                ("Range 30/120", "range"),
            ),
            ("Bolt", nm("adventuring_gear", "bolts")),
            *_row_refs(
                ("Light", "light"),
                ("Loading", "loading"),
                ("Vex", "vex"),
            ),
        ),
    ),
    (
        "weapons",
        "heavy_crossbow",
        E,
        MARTIAL_RANGED,
        WEAPON_ROWS["Heavy Crossbow"],
        (
            *_row_refs(
                ("Martial", "category"),
                ("Ranged", "melee_or_ranged"),
                ("Ammunition", "ammunition"),
                ("Range 100/400", "range"),
            ),
            ("Bolt", nm("adventuring_gear", "bolts")),
            *_row_refs(
                ("Heavy, Loading", "heavy"),
                ("Loading", "loading"),
                ("Two-Handed", "two_handed"),
                ("Push", "push"),
            ),
        ),
    ),
    (
        "weapons",
        "longbow",
        E,
        MARTIAL_RANGED,
        WEAPON_ROWS["Longbow"],
        (
            *_row_refs(
                ("Martial", "category"),
                ("Ranged", "melee_or_ranged"),
                ("Ammunition", "ammunition"),
                ("Range 150/600", "range"),
            ),
            ("Arrow", nm("adventuring_gear", "arrows")),
            *_row_refs(
                ("Heavy", "heavy"),
                ("Two-Handed", "two_handed"),
                ("Slow", "slow"),
            ),
        ),
    ),
    (
        "weapons",
        "pistol",
        E,
        MARTIAL_RANGED,
        WEAPON_ROWS["Pistol"],
        (
            *_row_refs(
                ("Martial", "category"),
                ("Ranged", "melee_or_ranged"),
                ("Ammunition", "ammunition"),
                ("Range 30/90", "range"),
            ),
            ("Bullet", nm("adventuring_gear", "bullets_firearm")),
            *_row_refs(
                ("Loading", "loading"),
                ("Vex", "vex"),
            ),
        ),
    ),
    (
        "armor",
        "leather_armor",
        E,
        (ARMOR_HEAD, ARMOR_GROUPS["Light Armor"]),
        ARMOR_ROWS["Leather Armor"],
        _row_refs(
            ("Light Armor", "category"),
            ("11 + Dex modifier", "armor_class"),
            entry="armor",
        ),
    ),
    (
        "armor",
        "studded_leather_armor",
        E,
        (ARMOR_HEAD, ARMOR_GROUPS["Light Armor"]),
        ARMOR_ROWS["Studded Leather Armor"],
        _row_refs(
            ("Light Armor", "category"),
            ("12 + Dex modifier", "armor_class"),
            entry="armor",
        ),
    ),
    (
        "armor",
        "chain_shirt",
        E,
        (ARMOR_HEAD, ARMOR_GROUPS["Medium Armor"]),
        ARMOR_ROWS["Chain Shirt"],
        _row_refs(
            ("Medium Armor", "category"),
            ("13 + Dex modifier (max 2)", "armor_class"),
            entry="armor",
        ),
    ),
    (
        "armor",
        "breastplate",
        E,
        (ARMOR_HEAD, ARMOR_GROUPS["Medium Armor"]),
        ARMOR_ROWS["Breastplate"],
        _row_refs(
            ("Medium Armor", "category"),
            ("14 + Dex modifier (max 2)", "armor_class"),
            entry="armor",
        ),
    ),
    (
        "armor",
        "half_plate_armor",
        E,
        (ARMOR_HEAD, ARMOR_GROUPS["Medium Armor"]),
        ARMOR_ROWS["Half Plate Armor"],
        _row_refs(
            ("Medium Armor", "category"),
            ("15 + Dex modifier (max 2)", "armor_class"),
            ("Disadvantage", "stealth"),
            entry="armor",
        ),
    ),
    (
        "armor",
        "chain_mail",
        E,
        (ARMOR_HEAD, ARMOR_GROUPS["Heavy Armor"]),
        ARMOR_ROWS["Chain Mail"],
        _row_refs(
            ("Heavy Armor (10 Minutes to Don and 5 Minutes to Doff)", "category"),
            ("16", "armor_class"),
            ("Str 13", "strength"),
            ("Disadvantage", "stealth"),
            entry="armor",
        ),
    ),
    (
        "armor",
        "splint_armor",
        E,
        (ARMOR_HEAD, ARMOR_GROUPS["Heavy Armor"]),
        ARMOR_ROWS["Splint Armor"],
        _row_refs(
            ("Heavy Armor (10 Minutes to Don and 5 Minutes to Doff)", "category"),
            ("17", "armor_class"),
            ("Str 15", "strength"),
            ("Disadvantage", "stealth"),
            entry="armor",
        ),
    ),
    (
        "armor",
        "plate_armor",
        E,
        (ARMOR_HEAD, ARMOR_GROUPS["Heavy Armor"]),
        ARMOR_ROWS["Plate Armor"],
        _row_refs(
            ("Heavy Armor (10 Minutes to Don and 5 Minutes to Doff)", "category"),
            ("18", "armor_class"),
            ("Str 15", "strength"),
            ("Disadvantage", "stealth"),
            entry="armor",
        ),
    ),
    ("adventuring_gear", "bolts", E, AMMUNITION_ENTRY, AMMUNITION_ROWS["Bolts"], ()),
    # -- CRD Issue 2b G1: the twelve rows no citation named, each read and
    # cited as the accepted row it mirrors (named in each comment).
    (  # as Dagger and Shortbow
        "weapons",
        "dart",
        E,
        SIMPLE_RANGED,
        WEAPON_ROWS["Dart"],
        _row_refs(
            ("Simple", "category"),
            ("Ranged", "melee_or_ranged"),
            ("Finesse", "finesse"),
            ("Thrown", "thrown"),
            ("Range 20/60", "range"),
            ("Vex", "vex"),
        ),
    ),
    (  # as Pike
        "weapons",
        "glaive",
        E,
        MARTIAL_MELEE,
        WEAPON_ROWS["Glaive"],
        _row_refs(
            ("Martial", "category"),
            ("Melee", "melee_or_ranged"),
            ("Heavy", "heavy"),
            ("Reach", "reach"),
            ("Two-Handed", "two_handed"),
            ("Graze", "graze"),
        ),
    ),
    (  # as Pike
        "weapons",
        "halberd",
        E,
        MARTIAL_MELEE,
        WEAPON_ROWS["Halberd"],
        _row_refs(
            ("Martial", "category"),
            ("Melee", "melee_or_ranged"),
            ("Heavy", "heavy"),
            ("Reach", "reach"),
            ("Two-Handed", "two_handed"),
            ("Cleave", "cleave"),
        ),
    ),
    (  # as Pike; "(unless mounted)" stays the row's governing prose
        "weapons",
        "lance",
        E,
        MARTIAL_MELEE,
        WEAPON_ROWS["Lance"],
        _row_refs(
            ("Martial", "category"),
            ("Melee", "melee_or_ranged"),
            ("Heavy", "heavy"),
            ("Reach", "reach"),
            ("Two-Handed", "two_handed"),
            ("Topple", "topple"),
        ),
    ),
    (  # as Greatsword
        "weapons",
        "maul",
        E,
        MARTIAL_MELEE,
        WEAPON_ROWS["Maul"],
        _row_refs(
            ("Martial", "category"),
            ("Melee", "melee_or_ranged"),
            ("Heavy", "heavy"),
            ("Two-Handed", "two_handed"),
            ("Topple", "topple"),
        ),
    ),
    (  # as Spear
        "weapons",
        "trident",
        E,
        MARTIAL_MELEE,
        WEAPON_ROWS["Trident"],
        _row_refs(
            ("Martial", "category"),
            ("Melee", "melee_or_ranged"),
            ("Thrown", "thrown"),
            ("Range 20/60", "range"),
            ("Versatile (1d10)", "versatile"),
            ("Topple", "topple"),
        ),
    ),
    (  # as Longsword
        "weapons",
        "war_pick",
        E,
        MARTIAL_MELEE,
        WEAPON_ROWS["War Pick"],
        _row_refs(
            ("Martial", "category"),
            ("Melee", "melee_or_ranged"),
            ("Versatile (1d10)", "versatile"),
            ("Sap", "sap"),
        ),
    ),
    (  # as Rapier and Pike
        "weapons",
        "whip",
        E,
        MARTIAL_MELEE,
        WEAPON_ROWS["Whip"],
        _row_refs(
            ("Martial", "category"),
            ("Melee", "melee_or_ranged"),
            ("Finesse", "finesse"),
            ("Reach", "reach"),
            ("Slow", "slow"),
        ),
    ),
    (  # as Hand Crossbow
        "weapons",
        "blowgun",
        E,
        MARTIAL_RANGED,
        WEAPON_ROWS["Blowgun"],
        (
            *_row_refs(
                ("Martial", "category"),
                ("Ranged", "melee_or_ranged"),
                ("Ammunition", "ammunition"),
                ("Range 25/100", "range"),
            ),
            ("Needle", nm("adventuring_gear", "needles")),
            *_row_refs(("Loading", "loading"), ("Vex", "vex")),
        ),
    ),
    (  # as Half Plate Armor
        "armor",
        "scale_mail",
        E,
        (ARMOR_HEAD, ARMOR_GROUPS["Medium Armor"]),
        ARMOR_ROWS["Scale Mail"],
        _row_refs(
            ("Medium Armor", "category"),
            ("14 + Dex modifier (max 2)", "armor_class"),
            ("Disadvantage", "stealth"),
            entry="armor",
        ),
    ),
    (  # as Chain Mail; its Strength cell is "—", cited by nothing
        "armor",
        "ring_mail",
        E,
        (ARMOR_HEAD, ARMOR_GROUPS["Heavy Armor"]),
        ARMOR_ROWS["Ring Mail"],
        _row_refs(
            ("Heavy Armor (10 Minutes to Don and 5 Minutes to Doff)", "category"),
            ("14", "armor_class"),
            ("Disadvantage", "stealth"),
            entry="armor",
        ),
    ),
    ("adventuring_gear", "needles", E, AMMUNITION_ENTRY, AMMUNITION_ROWS["Needles"], ()),
    ("adventuring_gear", "wand", E, WAND_CONTEXT, WAND_ROW, ()),
    (
        "mounts_and_vehicles",
        "keelboat",
        E,
        VEHICLE_CONTEXT,
        VEHICLE_ROWS["Keelboat"],
        (),
    ),
    (
        "mounts_and_vehicles",
        "rowboat",
        E,
        VEHICLE_CONTEXT,
        VEHICLE_ROWS["Rowboat"],
        (),
    ),
)

#: Section rules a named armor row is read with, after its row, as printed.
ROW_AFTER: dict[tuple[str, str], tuple[str, ...]] = {
    ("armor", "padded_armor"): ARMOR_RULES,
    ("armor", "hide_armor"): ARMOR_RULES,
    ("armor", "leather_armor"): ARMOR_RULES,
    ("armor", "studded_leather_armor"): ARMOR_RULES,
    ("armor", "chain_shirt"): ARMOR_RULES,
    ("armor", "breastplate"): ARMOR_RULES,
    ("armor", "half_plate_armor"): ARMOR_RULES,
    ("armor", "chain_mail"): ARMOR_RULES,
    ("armor", "scale_mail"): ARMOR_RULES,
    ("armor", "ring_mail"): ARMOR_RULES,
    ("armor", "splint_armor"): ARMOR_RULES,
    ("armor", "plate_armor"): ARMOR_RULES,
    ("mounts_and_vehicles", "keelboat"): VEHICLE_NOTES,
    ("mounts_and_vehicles", "rowboat"): VEHICLE_NOTES,
}

#: Section rules a named clause is read with, (before, after) its own texts,
#: as printed: a mastery is usable only through a feature that unlocks it
#: (printed 90), a Shield's clause sits inside Armor Training, and a tool
#: reads the shared Utilize and proficiency rules -- the Gaming Set's
#: variants each a separate proficiency, an artisan's tool its own.
AROUND: dict[tuple[str, str], tuple[tuple[str, ...], tuple[str, ...]]] = {
    **{
        ("weapons", k): (clause("weapons", "mastery_properties"), ())
        for k in ("cleave", "graze", "nick", "push", "sap", "slow", "topple", "vex")
    },
    ("armor", "shield"): (ARMOR_TRAINING, ONE_AT_A_TIME),
    ("tools", "calligraphers_supplies"): (
        (*TOOL_RULES, *clause("tools", "artisans_tools")),
        (),
    ),
    ("tools", "alchemists_supplies"): (
        (*TOOL_RULES, *clause("tools", "artisans_tools")),
        (),
    ),
    ("tools", "jewelers_tools"): (
        (*TOOL_RULES, *clause("tools", "artisans_tools")),
        (),
    ),
    ("tools", "leatherworkers_tools"): (
        (*TOOL_RULES, *clause("tools", "artisans_tools")),
        (),
    ),
    ("tools", "smiths_tools"): (
        (*TOOL_RULES, *clause("tools", "artisans_tools")),
        (),
    ),
    ("tools", "tinkers_tools"): (
        (*TOOL_RULES, *clause("tools", "artisans_tools")),
        (),
    ),
    ("tools", "weavers_tools"): (
        (*TOOL_RULES, *clause("tools", "artisans_tools")),
        (),
    ),
    ("tools", "woodcarvers_tools"): (
        (*TOOL_RULES, *clause("tools", "artisans_tools")),
        (),
    ),
    ("tools", "gaming_set"): (
        (
            *clause("tools", "utilize"),
            *clause("tools", "variants"),
            *clause("tools", "tool_proficiency"),
        ),
        (),
    ),
    ("tools", "herbalism_kit"): (TOOL_RULES, ()),
    ("tools", "musical_instrument"): (
        (
            *clause("tools", "utilize"),
            *clause("tools", "variants"),
            *clause("tools", "tool_proficiency"),
        ),
        (),
    ),
    ("tools", "poisoners_kit"): (TOOL_RULES, ()),
    ("tools", "thieves_tools"): (TOOL_RULES, ()),
}

#: A named clause's rows of a table, and the rows they are read under: a gear
#: item's rows of the Adventuring Gear table, and the Shield's row of the
#: Armor table, which its own rule interprets.
ROWS_OF: dict[tuple[str, str], tuple[tuple[str, ...], tuple[str, ...]]] = {
    **{("adventuring_gear", k): ((GEAR_HEAD,), rows) for k, rows in GEAR_ROWS.items()},
    ("armor", "shield"): (
        (ARMOR_HEAD, ARMOR_GROUPS["Shield"]),
        (ARMOR_ROWS["Shield"],),
    ),
}


def unauthored(scope: str, *names: str) -> tuple[tuple[str, Target], ...]:
    """Pointers into a part no batch authors yet: unresolved."""
    return tuple((n, (scope, UNRESOLVED_TARGET)) for n in names)


#: A gear item as a pointer prints it, and its clause key.
GEAR_NAMES = {
    "Acid": "acid",
    "Antitoxin": "antitoxin",
    "Arcane Focus": "arcane_focus",
    "Backpack": "backpack",
    "Ball Bearings": "ball_bearings",
    "Barrel": "barrel",
    "Basic Poison": "poison_basic",
    "Basket": "basket",
    "Bell": "bell",
    "Block and Tackle": "block_and_tackle",
    "Climber's Kit": "climbers_kit",
    "Costume": "costume",
    "Druidic Focus": "druidic_focus",
    "Glass Bottle": "bottle_glass",
    "Ink": "ink",
    "Jug": "jug",
    "Map": "map",
    "Potion of Healing": "potion_of_healing",
    "Rations": "rations",
    "Spell Scroll": "spell_scroll",
}


def gear(*names: str) -> tuple[tuple[str, Target], ...]:
    """Pointers to gear items, each naming the item's record."""
    return tuple((n, nm("adventuring_gear", GEAR_NAMES[n])) for n in names)


#: Accepted Rules Glossary entries a rule here depends on, by printed name,
#: longest first. A component references each entry once, at its first printed
#: name, and only from prose: a table's cells are data, not dependencies.
#: "High or Long Jump" names both jumps: it references the High Jump by the
#: whole phrase and leaves "Long Jump" inside it free.
GLOSSARY_TERMS: tuple[tuple[str, str], ...] = (
    ("High or Long Jump", "high_jump"),
    ("Long Jump", "long_jump"),
    ("Short Rest", "short_rest"),
    ("Hit Points?", "hit_points"),
    ("Armor Class", "armor_class"),
    ("Attack action", "attack"),
    ("Utilize action", "utilize"),
    ("attack rolls?", "attack_roll"),
    ("damage rolls?", "damage_roll"),
    ("Opportunity Attacks", "opportunity_attacks"),
    ("stat block", "stat_block"),
    ("carrying capacity", "carrying_capacity"),
    ("Speed", "speed"),
    ("Prone", "prone"),
    ("Poisoned", "poisoned"),
    ("Grappled", "grappled"),
    ("Incapacitated", "incapacitated"),
    ("Restrained", "restrained"),
    ("Unconscious", "unconscious"),
    ("Immunity", "immunity"),
    ("Indifferent", "indifferent"),
)
#: Phrases whose inner names stay readable as references of their own.
OPEN_PHRASES = frozenset({"high_jump"})


def glossary_refs(texts: tuple[str, ...]) -> tuple[tuple[str, Target], ...]:
    """Each accepted glossary entry *texts*' prose prints, once, at its first name."""
    found: list[tuple[int, int, str, str]] = []
    for n, text in enumerate(texts):
        if "<t" in text or "</t" in text:
            continue
        taken: list[tuple[int, int]] = []
        for pattern, slug in GLOSSARY_TERMS:
            for m in re.finditer(rf"\b{pattern}\b", text):
                if any(a <= m.start() and m.end() <= b for a, b in taken):
                    continue
                if slug not in OPEN_PHRASES:
                    taken.append(m.span())
                found.append((n, m.start(), m.group(), slug))
    refs: dict[str, str] = {}
    for _, _, printed, slug in sorted(found):
        refs.setdefault(slug, printed)
    return tuple((printed, slug) for slug, printed in refs.items())


#: Explicit pointers, by component; accepted glossary terms are added from
#: each component's prose by :func:`glossary_refs`. A tool's *Craft* line
#: names each record it crafts from once, at the first item printed from it.
EXPLICIT_REFS: dict[tuple[str, str], tuple[tuple[str, Target], ...]] = {
    # -- Weapons ----------------------------------------------------------------
    ("weapons", "selling_equipment"): unauthored(MAGIC_ITEMS, "Magic Items"),
    ("weapons", "reach"): (("reach", "reach"),),
    ("weapons", "improvised_weapons"): (("Improvised Weapons", "improvised_weapons"),),
    # -- Tools ------------------------------------------------------------------
    ("tools", "craft"): (
        ("Crafting Nonmagical Items", eq("crafting_nonmagical_items")),
        ("Brewing Potions of Healing", eq("brewing_potions_of_healing")),
        ("Scribing Spell Scrolls", eq("scribing_spell_scrolls")),
    ),
    ("tools", "alchemists_supplies"): gear("Acid"),
    ("tools", "brewers_supplies"): gear("Antitoxin"),
    ("tools", "calligraphers_supplies"): gear("Ink"),
    ("tools", "carpenters_tools"): (("Club", nm("weapons", "club")), *gear("Barrel")),
    ("tools", "cartographers_tools"): gear("Map"),
    ("tools", "cobblers_tools"): gear("Climber's Kit"),
    ("tools", "cooks_utensils"): gear("Rations"),
    ("tools", "glassblowers_tools"): gear("Glass Bottle"),
    ("tools", "jewelers_tools"): gear("Arcane Focus"),
    ("tools", "leatherworkers_tools"): (
        ("Sling", nm("weapons", "sling")),
        ("Hide Armor", nm("armor", "hide_armor")),
        *gear("Backpack"),
    ),
    ("tools", "masons_tools"): gear("Block and Tackle"),
    ("tools", "painters_supplies"): gear("Druidic Focus"),
    ("tools", "potters_tools"): gear("Jug"),
    ("tools", "smiths_tools"): (
        ("Melee weapon", nm("weapons", "melee_or_ranged")),
        ("Medium armor", nm("armor", "category")),
        *gear("Ball Bearings"),
    ),
    ("tools", "tinkers_tools"): (("Musket", nm("weapons", "musket")), *gear("Bell")),
    ("tools", "weavers_tools"): (
        ("Padded Armor", nm("armor", "padded_armor")),
        *gear("Basket"),
    ),
    ("tools", "woodcarvers_tools"): (
        ("Club", nm("weapons", "club")),
        *gear("Arcane Focus"),
    ),
    ("tools", "disguise_kit"): gear("Costume"),
    ("tools", "herbalism_kit"): gear("Antitoxin"),
    ("tools", "poisoners_kit"): gear("Basic Poison"),
    # -- Adventuring Gear -------------------------------------------------------
    ("adventuring_gear", "ammunition"): (
        ("Ammunition property", nm("weapons", "ammunition")),
    ),
    ("adventuring_gear", "alchemists_fire"): (("burning", "burning"),),
    ("adventuring_gear", "arcane_focus"): (
        *unauthored(CLASSES, "Sorcerer, Warlock, or Wizard"),
        ("Quarterstaff", nm("weapons", "quarterstaff")),
    ),
    ("adventuring_gear", "druidic_focus"): (
        *unauthored(CLASSES, "Druid or Ranger"),
        ("Quarterstaff", nm("weapons", "quarterstaff")),
    ),
    ("adventuring_gear", "holy_symbol"): (
        *unauthored(CLASSES, "Cleric or Paladin"),
        ("Shield", nm("armor", "shield")),
    ),
    ("adventuring_gear", "bedroll"): unauthored(GAMEPLAY_TOOLBOX, "Gameplay Toolbox"),
    ("adventuring_gear", "blanket"): unauthored(GAMEPLAY_TOOLBOX, "Gameplay Toolbox"),
    ("adventuring_gear", "lock"): (("Thieves' Tools", nm("tools", "thieves_tools")),),
    ("adventuring_gear", "manacles"): (
        ("Thieves' Tools", nm("tools", "thieves_tools")),
    ),
    ("adventuring_gear", "rations"): (("Malnutrition", "malnutrition"),),
    ("adventuring_gear", "spikes_iron"): (
        ("Light Hammer", nm("weapons", "light_hammer")),
    ),
    # "Simple Melee weapon": *Category* defines Simple and Martial, *Melee or
    # Ranged* defines Melee -- cited as a weapon row's group row cites them.
    ("adventuring_gear", "torch"): (
        ("Simple", nm("weapons", "category")),
        ("Melee", nm("weapons", "melee_or_ranged")),
    ),
    ("adventuring_gear", "waterskin"): (("dehydration", "dehydration"),),
    # -- Mounts and Vehicles ----------------------------------------------------
    ("mounts_and_vehicles", "mounts"): unauthored(MONSTERS, "Monsters"),
    ("mounts_and_vehicles", "barding"): (("Armor table", ARMOR),),
    ("mounts_and_vehicles", "crew"): (("Hirelings", eq("hirelings")),),
    ("mounts_and_vehicles", "damage_threshold"): (
        ("damage threshold", "damage_threshold"),
    ),
    # -- Services ---------------------------------------------------------------
    ("food_drink_and_lodging", "food_drink_and_lodging"): (
        ("lifestyle's expenses", eq("lifestyle_expenses")),
    ),
    # -- Magic Items ------------------------------------------------------------
    ("magic_items", "magic_items"): unauthored(MAGIC_ITEMS, "Magic Items"),
    ("magic_items", "identifying_a_magic_item"): unauthored(SPELLS, "Identify"),
    # -- Crafting, Brewing and Scribing -----------------------------------------
    ("crafting_nonmagical_items", "tools"): (("Tools", TOOLS),),
    ("brewing_potions_of_healing", "brewing_potions_of_healing"): (
        ("Herbalism Kit", nm("tools", "herbalism_kit")),
        *gear("Potion of Healing"),
    ),
    ("scribing_spell_scrolls", "scribing_spell_scrolls"): gear("Spell Scroll"),
    ("scribing_spell_scrolls", "prerequisites_for_the_scribe"): (
        ("Calligrapher's Supplies", nm("tools", "calligraphers_supplies")),
    ),
}

#: Components whose outcome the rule leaves to the GM.
GM_LATITUDE: frozenset[tuple[str, str]] = frozenset(
    {
        ("lifestyle_expenses", "lifestyle_expenses"),
        ("lifestyle_expenses", "lifestyle_perception"),
        ("magic_items", "multiple_items_of_the_same_kind"),
        ("crafting_nonmagical_items", "tools"),
        ("crafting_nonmagical_items", "raw_materials"),
        ("crafting_nonmagical_items", "time"),
    }
)
#: Items whose applicability turns on fiction the projection cannot enumerate.
CONTEXTUAL: frozenset[tuple[str, str]] = frozenset(
    ("adventuring_gear", k)
    for k in (
        "book",
        "clothes_fine",
        "costume",
        "crowbar",
        "magnifying_glass",
        "map",
        "robe",
    )
)


S, MA = WeaponCategory.SIMPLE, WeaponCategory.MARTIAL
#: CRD Issue 2b G1 review data: (category, mastery) as each Weapons-table row
#: prints them -- the category from the row's group row ("Simple Melee
#: Weapons" ...), the mastery from its Mastery column (equipment.md, official
#: SRD 5.2.1 pp. 90-91). Literal, never read from the table above, so the
#: source catalogue check compares two independent statements.
WEAPON_FACTS: dict[str, tuple[WeaponCategory, WeaponMastery]] = {
    "club": (S, WeaponMastery.SLOW),
    "dagger": (S, WeaponMastery.NICK),
    "greatclub": (S, WeaponMastery.PUSH),
    "handaxe": (S, WeaponMastery.VEX),
    "javelin": (S, WeaponMastery.SLOW),
    "light_hammer": (S, WeaponMastery.NICK),
    "mace": (S, WeaponMastery.SAP),
    "quarterstaff": (S, WeaponMastery.TOPPLE),
    "sickle": (S, WeaponMastery.NICK),
    "spear": (S, WeaponMastery.SAP),
    "dart": (S, WeaponMastery.VEX),
    "light_crossbow": (S, WeaponMastery.SLOW),
    "shortbow": (S, WeaponMastery.VEX),
    "sling": (S, WeaponMastery.SLOW),
    "battleaxe": (MA, WeaponMastery.TOPPLE),
    "flail": (MA, WeaponMastery.SAP),
    "glaive": (MA, WeaponMastery.GRAZE),
    "greataxe": (MA, WeaponMastery.CLEAVE),
    "greatsword": (MA, WeaponMastery.GRAZE),
    "halberd": (MA, WeaponMastery.CLEAVE),
    "lance": (MA, WeaponMastery.TOPPLE),
    "longsword": (MA, WeaponMastery.SAP),
    "maul": (MA, WeaponMastery.TOPPLE),
    "morningstar": (MA, WeaponMastery.SAP),
    "pike": (MA, WeaponMastery.PUSH),
    "rapier": (MA, WeaponMastery.VEX),
    "scimitar": (MA, WeaponMastery.NICK),
    "shortsword": (MA, WeaponMastery.VEX),
    "trident": (MA, WeaponMastery.TOPPLE),
    "warhammer": (MA, WeaponMastery.PUSH),
    "war_pick": (MA, WeaponMastery.SAP),
    "whip": (MA, WeaponMastery.SLOW),
    "blowgun": (MA, WeaponMastery.VEX),
    "hand_crossbow": (MA, WeaponMastery.VEX),
    "heavy_crossbow": (MA, WeaponMastery.PUSH),
    "longbow": (MA, WeaponMastery.SLOW),
    "musket": (MA, WeaponMastery.SLOW),
    "pistol": (MA, WeaponMastery.VEX),
}
assert len(WEAPON_FACTS) == len(WEAPON_ROWS) == 38


def _weapon_facts(key: str) -> tuple[WeaponCategoryFact, WeaponMasteryFact]:
    category, mastery = WEAPON_FACTS[key]
    return WeaponCategoryFact(category=category), WeaponMasteryFact(mastery=mastery)


def _components() -> tuple[EntryComponent, ...]:
    """Each clause's component -- its section's, or the named record's owning
    it -- then each named row's.

    A named record owns its clause, with any table rows of its own read under
    their head and group rows as context, and carries the clause's
    references; a row of it another record names it reads as context. Its
    section no longer reads that prose: it reaches the record where it is
    printed (Owner Decision 2026-09-24), and a section's table component
    reads every piece no named record owns, in printed order.
    """
    whole = {(e, k) for e, k, _ in NAMED_CLAUSES}
    rows_named = {row for *_, row, _ in NAMED_ROWS}
    owned = rows_named | {r for _, rows in ROWS_OF.values() for r in rows}
    out = []
    for entry, key, _, texts in CLAUSES:
        explicit = EXPLICIT_REFS.get((entry, key), ())
        stated = {scoped(t) for _, t in explicit}
        refs = explicit + tuple(
            (printed, slug)
            for printed, slug in glossary_refs(texts)
            if scoped(slug) not in stated
        )
        reason = (
            GM
            if (entry, key) in GM_LATITUDE
            else CTX if (entry, key) in CONTEXTUAL else NO_USE
        )
        if (entry, key) in whole:
            context, rows = ROWS_OF.get((entry, key), ((), ()))
            before, after = AROUND.get((entry, key), ((), ()))
            read = (*context, *rows, *before, *texts, *after)
            # A peer's named row it prints (the Arcane Focus entry's Wand
            # row) it still reads, as context: the row is the peer's.
            peers = tuple(t for t in texts if t in rows_named)
            out.append(
                C(
                    entry,
                    key,
                    P,
                    reason,
                    refs=refs,
                    record=named(entry, key),
                    texts=read if read != texts else (),
                    context=(*context, *before, *after, *peers),
                )
            )
        else:
            kept = tuple(t for t in texts if t not in owned)
            # A clause every text of which a named row owns has no section
            # component (G1's ``weapon_rows``); an empty ``texts`` would read
            # the whole clause.
            if kept:
                out.append(
                    C(
                        entry,
                        key,
                        P,
                        reason,
                        refs=refs,
                        texts=kept if kept != texts else (),
                    )
                )
        for e, k, _, before, row, row_refs in NAMED_ROWS:
            if e == entry and row in texts:
                context = (*before, *ROW_AFTER.get((e, k), ()))
                for text, _ in row_refs:
                    # Cited from the row when it prints the words, else from
                    # the one context text that does -- as authoring cites.
                    held = [row] if text in row else [t for t in context if text in t]
                    if len(held) != 1:
                        raise ValueError(
                            f"{k}: {text!r} is read from {len(held)} texts"
                        )
                weapon = e == "weapons" and k in WEAPON_FACTS
                out.append(
                    C(
                        e,
                        k,
                        M if weapon else P,
                        NO_USE,
                        facts=_weapon_facts(k) if weapon else (),
                        refs=row_refs,
                        record=named(e, k),
                        texts=(*before, row, *ROW_AFTER.get((e, k), ())),
                        context=context,
                    )
                )
    return tuple(out)


COMPONENTS: tuple[EntryComponent, ...] = _components()

SUPPORTING: tuple[tuple[str, str, str | None], ...] = ()
RECORD_REFERENCES: tuple[RecordReference, ...] = ()

#: Targets outside this batch that no accepted record defines and this batch
#: does not author: the *Improvised Weapons* glossary entry.
NEW_TARGETS: tuple[Target, ...] = ("improvised_weapons",)


def accepted_context_targets() -> tuple[Target, ...]:
    """The accepted glossary entries this batch's components cite."""
    return tuple(
        sorted(
            {
                t
                for c in COMPONENTS
                for _, t in c.refs
                if isinstance(t, str) and t not in NEW_TARGETS
            },
        )
    )


def batch() -> EntryBatch:
    """The tables above, read at call time so tests can mutate them."""
    return EntryBatch(
        origin=ORIGIN,
        proposal_origin=f"{ORIGIN} (CRD Issue 5d equipment batch; unaccepted)",
        unit_prefix="equipment",
        parent=PARENT,
        entries=ENTRIES,
        expected_leaves=375,
        clauses=CLAUSES,
        framing=FRAMING,
        components=COMPONENTS,
        supporting=SUPPORTING,
        record_references=RECORD_REFERENCES,
        placements=PLACEMENTS,
        excluded=EXCLUDED,
        anchors=ANCHORS,
        schema=(SCHEMA_18_VERSION, SCHEMA_18_HASH),
        records=tuple(
            (named(e, k), kind, e)
            for e, k, kind in (
                *NAMED_CLAUSES,
                *((e, k, kind) for e, k, kind, *_ in NAMED_ROWS),
            )
        ),
    )


def build(session: Session) -> Built:
    """Derive the equipment proposal from the release *session* published."""
    return build_entry_batch(session, batch(), published_release_binding(session))


def unresolved() -> list[tuple[str, str]]:
    """Printed pointers whose destination has no record yet, as (scope, text)."""
    return sorted(
        (scope, text)
        for c in COMPONENTS
        for text, t in c.refs
        for scope, key in (scoped(t),)
        if key == UNRESOLVED_TARGET
    )


def expected_representation_findings() -> list[str]:
    """Every out-of-batch target: the accepted ones stay unknown to the batch alone."""
    return sorted(
        [
            *unknown_target_findings(
                RECORD_REFERENCES,
                COMPONENTS,
                (*NEW_TARGETS, *accepted_context_targets()),
            ),
            *(f"reference {s}:{t!r}: unresolved reference" for s, t in unresolved()),
        ]
    )


# ---------------------------------------------------------------------------
# Unrecorded resolution drafts for the same Owner packet
# ---------------------------------------------------------------------------
def sec(slug: str) -> str:
    """The record key of one section of this batch."""
    return PLACEMENTS[slug].record_key


#: Forty-five accepted citations print "Equipment", or a thing it prices, under
#: scope ``srd-5.2.1/equipment`` and stay unresolved. Forty-three are
#: resolvable. A citation naming an item or rule targets the record for that
#: item or rule (ADR-005d Decisions 3 and 7): a weapon names its row, a
#: weapon property its rule, "Melee weapon" and "Ranged weapons" the *Melee or
#: Ranged* rule, "Light, Medium, or Heavy armor" the armor *Category* rule
#: that defines the three, a tool or gear item its entry, "Arrows" its
#: Ammunition row. A citation printing only "Equipment" names the section its
#: citing passage is about: weapons and AC for *Weapons* and *Armor*, tool
#: proficiency for *Tools*, travel by vehicle for *Mounts and Vehicles*, and
#: the Starting at Higher Levels firearms example for *Weapons*. Each draft
#: cites the accepted citation's own provenance spans, sorted, and becomes
#: applicable only once its target is accepted, and then only by its own
#: authorized ``resolve_references`` action. Nothing here records or applies
#: any.
#:
#: (from record, component, printed text, target record, provenance spans).
DRAFTS: tuple[tuple[str, str, str, str, tuple[str, ...]], ...] = (
    (
        "play.d20_tests",
        "",
        "Equipment",
        sec("weapons"),
        ("7ec23570-655e-50bd-9630-a75cc24336a3",),
    ),
    (
        "play.damage_and_healing",
        "",
        "Equipment",
        sec("weapons"),
        ("518926b1-25c2-5b9f-8b6a-14238f59ea96",),
    ),
    (
        "feats.archery",
        "archery",
        "Ranged weapons",
        named("weapons", "melee_or_ranged"),
        ("20c0f2e2-3999-5d8d-9d71-b5023685c303",),
    ),
    (
        "character_creation.create_your_character",
        "armor_class",
        "Equipment",
        sec("armor"),
        ("c6554bc4-0829-5e3c-b125-825a993ee51d",),
    ),
    (
        "character_creation.create_your_character",
        "armor_training",
        "Equipment",
        sec("armor"),
        ("b458f525-2b14-521e-84c5-7a757246cf15",),
    ),
    (
        "character_creation.create_your_character",
        "attacks",
        "Equipment",
        sec("weapons"),
        ("babe5cb1-30db-5e4e-8d8f-46d99b00199c",),
    ),
    (
        "feats.defense",
        "defense",
        "Light, Medium, or Heavy armor",
        named("armor", "category"),
        ("2a059eb3-5786-5254-99b0-fe309002b2f7",),
    ),
    *(
        (
            "character_origins.acolyte",
            "equipment",
            text,
            target,
            ("2cf2e102-4319-5fa8-a30f-089dfd1d95e2",),
        )
        for text, target in (
            ("Calligrapher's Supplies", named("tools", "calligraphers_supplies")),
            ("Book", named("adventuring_gear", "book")),
            ("Holy Symbol", named("adventuring_gear", "holy_symbol")),
            ("Parchment", named("adventuring_gear", "parchment")),
            ("Robe", named("adventuring_gear", "robe")),
        )
    ),
    *(
        (
            "character_origins.criminal",
            "equipment",
            text,
            target,
            ("4a7b2bde-e342-5409-b109-dc972b5ef400",),
        )
        for text, target in (
            ("Daggers", named("weapons", "dagger")),
            ("Thieves' Tools", named("tools", "thieves_tools")),
            ("Crowbar", named("adventuring_gear", "crowbar")),
            ("Pouches", named("adventuring_gear", "pouch")),
            ("Traveler's Clothes", named("adventuring_gear", "clothes_travelers")),
        )
    ),
    *(
        (
            "character_origins.sage",
            "equipment",
            text,
            target,
            ("5616570e-7d30-5460-8e53-30be2c9d8d93",),
        )
        for text, target in (
            ("Quarterstaff", named("weapons", "quarterstaff")),
            ("Calligrapher's Supplies", named("tools", "calligraphers_supplies")),
            ("Book", named("adventuring_gear", "book")),
            ("Parchment", named("adventuring_gear", "parchment")),
            ("Robe", named("adventuring_gear", "robe")),
        )
    ),
    *(
        (
            "character_origins.soldier",
            "equipment",
            text,
            target,
            ("41e895f8-b1ee-5163-b8ad-da7d22e5ebe7",),
        )
        for text, target in (
            ("Spear", named("weapons", "spear")),
            ("Shortbow", named("weapons", "shortbow")),
            ("Arrows", named("adventuring_gear", "arrows")),
            ("Gaming Set", named("tools", "gaming_set")),
            ("Healer's Kit", named("adventuring_gear", "healers_kit")),
            ("Quiver", named("adventuring_gear", "quiver")),
            ("Traveler's Clothes", named("adventuring_gear", "clothes_travelers")),
        )
    ),
    *(
        (
            "feats.great_weapon_fighting",
            "great_weapon_fighting",
            text,
            named("weapons", key),
            ("6c86f7ed-ba3d-5c7e-a376-3b25ca814722",),
        )
        for text, key in (
            ("Melee weapon", "melee_or_ranged"),
            ("Two-Handed", "two_handed"),
            ("Versatile", "versatile"),
        )
    ),
    (
        "character_creation.starting_at_higher_levels",
        "starting_equipment",
        "Equipment",
        sec("weapons"),
        (
            "24133049-722d-5195-875c-bea55323fbac",
            "9df6a836-4362-5877-bb97-e9ca6e7b4a3d",
            "fe5ba0bf-203e-5ceb-85ad-7fb15a601f5a",
        ),
    ),
    (
        "character_origins.acolyte",
        "tool_proficiency",
        "Calligrapher's Supplies",
        named("tools", "calligraphers_supplies"),
        ("fe841f55-4938-5735-b4ae-fa1b5195cbef",),
    ),
    (
        "character_origins.backgrounds",
        "tool_proficiency",
        "Artisan's Tools",
        named("tools", "artisans_tools"),
        ("ab8cbbff-666f-5773-9f8e-7a71235ed107",),
    ),
    (
        "character_origins.backgrounds",
        "tool_proficiency",
        "Equipment",
        sec("tools"),
        ("ab8cbbff-666f-5773-9f8e-7a71235ed107",),
    ),
    (
        "character_origins.criminal",
        "tool_proficiency",
        "Thieves' Tools",
        named("tools", "thieves_tools"),
        ("ba9cffb1-f00b-5f0e-9602-c5da9b4c1fb0",),
    ),
    (
        "character_origins.sage",
        "tool_proficiency",
        "Calligrapher's Supplies",
        named("tools", "calligraphers_supplies"),
        ("32dc5fd8-1d44-570c-b3e6-059a266091e8",),
    ),
    (
        "character_origins.soldier",
        "tool_proficiency",
        "Gaming Set",
        named("tools", "gaming_set"),
        ("777e49ba-8abe-5381-8a46-620f6dc86ed2",),
    ),
    (
        "character_origins.soldier",
        "tool_proficiency",
        "Equipment",
        sec("tools"),
        ("777e49ba-8abe-5381-8a46-620f6dc86ed2",),
    ),
    (
        "play.exploration",
        "travel_pace",
        "Equipment",
        sec("mounts_and_vehicles"),
        ("41f2ce66-b485-5e4c-a428-5443942d831e",),
    ),
    (
        "feats.two_weapon_fighting",
        "two_weapon_fighting",
        "Light property",
        named("weapons", "light"),
        ("b62effb9-feab-5b33-ae20-0e00a60b2c8a",),
    ),
    (
        "play.exploration",
        "vehicles",
        "Equipment",
        sec("mounts_and_vehicles"),
        ("8a5e47ef-595f-55eb-b8f7-534dbb1f780e",),
    ),
)

#: The two accepted citations that stay unresolved: each points at the whole
#: part ("the equipment described in "Equipment""; "the gear detailed in
#: "Equipment""), which no single section truthfully stands for.
UNRESOLVED_CITATIONS: tuple[tuple[str, str, str], ...] = (
    ("character_creation.create_your_character", "starting_equipment", "Equipment"),
    ("play.exploration", "weapons_beyond_battle", "Equipment"),
)


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def draft_resolutions(binding: ReleaseBinding) -> tuple[ReferenceResolution, ...]:
    """The forty-three pending resolutions, drafted for review against *binding*."""
    return tuple(
        ReferenceResolution(
            resolution_id=(
                f"resolve-{_slug(record)}-{_slug(component) or 'record'}-{_slug(text)}-equipment-1"
            ),
            from_record_key=record,
            from_component_key=component,
            source_text=text,
            scope_key=EQUIPMENT,
            target_record_key=target,
            release_binding=binding,
            provenance_span_ids=spans,
        )
        for record, component, text, target, spans in DRAFTS
    )


# ---------------------------------------------------------------------------
# Cited-target drafts (CRD Issue 5d Equipment cited-targets packet; unrecorded)
# ---------------------------------------------------------------------------
#: The 161 accepted citations under scope ``srd-5.2.1/equipment`` that name an
#: item or rule this candidate gives its own record: (from record, component,
#: printed text, target record, the citation's own provenance spans, sorted).
#: A qualified pointer names what it qualifies: Falling Net's "see "Adventuring
#: Gear" for the Net's statistics" names the Net, not the section. A plural
#: or inverted name names the one item the table prints ("Javelins" the
#: Javelin row, "Iron Spike" the "Spikes, Iron" row, "Bullseye Lantern" the
#: "Lantern, Bullseye" row), as the recorded "Daggers", "Pouches" and
#: "Traveler's Clothes" drafts do. Nothing here records or applies any.
CITED_DRAFTS: tuple[tuple[str, str, str, str, tuple[str, ...]], ...] = (
    (
        "magic_items.hat_of_many_spells",
        "hat_of_many_spells",
        "Alchemist's Fire",
        named("adventuring_gear", "alchemists_fire"),
        ("3ecc65a7-33a6-5565-9abc-1c5510d76012",),
    ),
    (
        "magic_items.efficient_quiver",
        "efficient_quiver",
        "Bolts",
        named("adventuring_gear", "bolts"),
        ("ac606bee-4547-59a1-9374-91ad891204a6",),
    ),
    (
        "classes.rogue",
        "core_traits",
        "Burglar's Pack",
        named("adventuring_gear", "burglars_pack"),
        ("e15857ee-0ac7-5b19-bf6d-ddd9069b70f0",),
    ),
    (
        "magic_items.hat_of_many_spells",
        "hat_of_many_spells",
        "Caltrops",
        named("adventuring_gear", "caltrops"),
        ("3ecc65a7-33a6-5565-9abc-1c5510d76012",),
    ),
    (
        "monsters.lich.lich",
        "lich",
        "Component Pouch",
        named("adventuring_gear", "component_pouch"),
        ("1205ce9a-488c-55fa-b2dc-1d290615b48e",),
    ),
    (
        "spells.components",
        "component_pouch_and_focus",
        "Component Pouch",
        named("adventuring_gear", "component_pouch"),
        ("32591758-96b7-53a5-8ef7-db655b3c2372",),
    ),
    (
        "classes.fighter",
        "core_traits",
        "Dungeoneer's Pack",
        named("adventuring_gear", "dungeoneers_pack"),
        ("5bae2240-b5c8-5e5e-8069-1c077312521f",),
    ),
    (
        "classes.sorcerer",
        "core_traits",
        "Dungeoneer's Pack",
        named("adventuring_gear", "dungeoneers_pack"),
        ("81821344-a26a-58b6-ab15-fd971182ab7b",),
    ),
    (
        "classes.bard",
        "core_traits",
        "Entertainer's Pack",
        named("adventuring_gear", "entertainers_pack"),
        ("73a15de1-87fe-504d-9fc1-8253175bfad7",),
    ),
    (
        "classes.barbarian",
        "core_traits",
        "Explorer's Pack",
        named("adventuring_gear", "explorers_pack"),
        ("1b44dce7-3c45-59ff-a269-a042e0826857",),
    ),
    (
        "classes.druid",
        "core_traits",
        "Explorer's Pack",
        named("adventuring_gear", "explorers_pack"),
        ("5e29d7a9-14b0-5b46-984f-32941631b224",),
    ),
    (
        "classes.monk",
        "core_traits",
        "Explorer's Pack",
        named("adventuring_gear", "explorers_pack"),
        ("ffecf855-ed96-5042-8654-49f86f398b6f",),
    ),
    (
        "classes.ranger",
        "core_traits",
        "Explorer's Pack",
        named("adventuring_gear", "explorers_pack"),
        ("e357b4c1-dc21-545f-9c2b-dd3dc20b10e3",),
    ),
    (
        "magic_items.hat_of_many_spells",
        "hat_of_many_spells",
        "Grappling Hook",
        named("adventuring_gear", "grappling_hook"),
        ("3ecc65a7-33a6-5565-9abc-1c5510d76012",),
    ),
    (
        "spells.protection_from_evil_and_good",
        "descriptor",
        "Holy Water",
        named("adventuring_gear", "holy_water"),
        ("76ddc7e2-ca1d-574f-b9d1-1f9fd887c87d",),
    ),
    (
        "magic_items.robe_of_useful_items",
        "robe_of_useful_items",
        "Bullseye Lantern",
        named("adventuring_gear", "lantern_bullseye"),
        ("d09d4237-efea-5a50-8351-089bb7ede57d",),
    ),
    (
        "magic_items.robe_of_useful_items",
        "robe_of_useful_items",
        "Mirror",
        named("adventuring_gear", "mirror"),
        ("d09d4237-efea-5a50-8351-089bb7ede57d",),
    ),
    (
        "gameplay_toolbox.traps.falling_net",
        "falling_net",
        "Adventuring Gear",
        named("adventuring_gear", "net"),
        ("443bf2ba-809d-57ac-a118-5a440b3c00c6",),
    ),
    (
        "gameplay_toolbox.traps.falling_net",
        "falling_net",
        "Net",
        named("adventuring_gear", "net"),
        (
            "1593a0a6-c16f-52b3-888a-b784bcb30f11",
            "37814220-d6d5-5645-8b49-d0f579b78cbe",
            "443bf2ba-809d-57ac-a118-5a440b3c00c6",
            "5a1eed7d-79d7-53ec-93f1-095aa3dc88ec",
            "8116a953-f7d5-5121-b6bd-c1338be78d24",
            "915e5147-085f-5272-bfa6-1c2823e0a724",
            "ca1ba9b4-a084-5d50-87d7-4e9176c7e2a5",
        ),
    ),
    (
        "magic_items.quarterstaff_of_the_acrobat",
        "quarterstaff_of_the_acrobat",
        "Pole",
        named("adventuring_gear", "pole"),
        ("c1bf0f11-f82f-5883-ac2b-a0f688585a08",),
    ),
    (
        "magic_items.robe_of_useful_items",
        "robe_of_useful_items",
        "Pole",
        named("adventuring_gear", "pole"),
        ("d09d4237-efea-5a50-8351-089bb7ede57d",),
    ),
    (
        "classes.cleric",
        "core_traits",
        "Priest's Pack",
        named("adventuring_gear", "priests_pack"),
        ("1b3e6f7f-bf6a-5b29-8bac-45808cafd3bc",),
    ),
    (
        "classes.paladin",
        "core_traits",
        "Priest's Pack",
        named("adventuring_gear", "priests_pack"),
        ("4186658b-3701-57d4-b064-028906ee7375",),
    ),
    (
        "magic_items.hat_of_many_spells",
        "hat_of_many_spells",
        "Rope",
        named("adventuring_gear", "rope"),
        ("3ecc65a7-33a6-5565-9abc-1c5510d76012",),
    ),
    (
        "magic_items.robe_of_useful_items",
        "robe_of_useful_items",
        "Rope",
        named("adventuring_gear", "rope"),
        ("d09d4237-efea-5a50-8351-089bb7ede57d",),
    ),
    (
        "magic_items.robe_of_useful_items",
        "robe_of_useful_items",
        "Sack",
        named("adventuring_gear", "sack"),
        ("d09d4237-efea-5a50-8351-089bb7ede57d",),
    ),
    (
        "classes.warlock",
        "core_traits",
        "Scholar's Pack",
        named("adventuring_gear", "scholars_pack"),
        ("347f4f5f-2de3-5072-b4a6-e6809f51e0bd",),
    ),
    (
        "classes.wizard",
        "core_traits",
        "Scholar's Pack",
        named("adventuring_gear", "scholars_pack"),
        ("6b37ee42-7341-50da-ba0c-cf9778c8edf0",),
    ),
    (
        "gameplay_toolbox.traps.fire_casting_statue",
        "fire_casting_statue",
        "Iron Spike",
        named("adventuring_gear", "spikes_iron"),
        ("33a3c764-acd7-59d5-aecd-656303c320a7",),
    ),
    (
        "gameplay_toolbox.traps.hidden_pit",
        "hidden_pit",
        "Iron Spike",
        named("adventuring_gear", "spikes_iron"),
        ("75e4ac68-9108-5cc9-bb68-59a8236ebb5b",),
    ),
    (
        "gameplay_toolbox.traps.poisoned_darts",
        "poisoned_darts",
        "Iron Spike",
        named("adventuring_gear", "spikes_iron"),
        ("b4d0bbe6-0c48-54d4-98c3-b0cb3678251c",),
    ),
    (
        "gameplay_toolbox.traps.rolling_stone",
        "rolling_stone",
        "Iron Spike",
        named("adventuring_gear", "spikes_iron"),
        ("8dae6ea8-a400-5c7f-9380-ce8e76f5f257",),
    ),
    (
        "gameplay_toolbox.traps.spiked_pit",
        "spiked_pit",
        "Iron Spike",
        named("adventuring_gear", "spikes_iron"),
        ("89d9c52b-0fd8-5f83-9432-d9fc53717e4f",),
    ),
    (
        "magic_items.hat_of_many_spells",
        "hat_of_many_spells",
        "Torch",
        named("adventuring_gear", "torch"),
        ("3ecc65a7-33a6-5565-9abc-1c5510d76012",),
    ),
    (
        "monsters.mages.archmage",
        "archmage",
        "Wand",
        named("adventuring_gear", "wand"),
        ("a0f20ad8-f0c5-54c9-8f17-a7e25b9a967a",),
    ),
    (
        "monsters.mages.mage",
        "mage",
        "Wand",
        named("adventuring_gear", "wand"),
        ("7742a046-56c2-52e7-bfb1-378a1264cec2",),
    ),
    (
        "monsters.centaur.centaur_trooper",
        "centaur_trooper",
        "Breastplate",
        named("armor", "breastplate"),
        ("af28874c-d5a1-5099-8ed0-98114984128c",),
    ),
    (
        "monsters.guards.guard_captain",
        "guard_captain",
        "Breastplate",
        named("armor", "breastplate"),
        ("79ed318a-64a4-5c05-b587-b904d3b4e1d4",),
    ),
    (
        "monsters.noble.noble",
        "noble",
        "Breastplate",
        named("armor", "breastplate"),
        ("797ebcbf-cc44-5b6b-a709-42f8905e788f",),
    ),
    (
        "classes.fighter",
        "core_traits",
        "Chain Mail",
        named("armor", "chain_mail"),
        ("5bae2240-b5c8-5e5e-8069-1c077312521f",),
    ),
    (
        "classes.paladin",
        "core_traits",
        "Chain Mail",
        named("armor", "chain_mail"),
        ("4186658b-3701-57d4-b064-028906ee7375",),
    ),
    (
        "magic_items.magic_item_categories",
        "armor",
        "Chain Mail",
        named("armor", "chain_mail"),
        ("f20e75f5-4053-5800-99fa-fbacf1d682bb",),
    ),
    (
        "monsters.toughs.tough_boss",
        "tough_boss",
        "Chain Mail",
        named("armor", "chain_mail"),
        ("4e46339c-dd19-5bb9-b817-94219bfb2d38",),
    ),
    (
        "classes.cleric",
        "core_traits",
        "Chain Shirt",
        named("armor", "chain_shirt"),
        ("1b3e6f7f-bf6a-5b29-8bac-45808cafd3bc",),
    ),
    (
        "monsters.bugbears.bugbear_stalker",
        "bugbear_stalker",
        "Chain Shirt",
        named("armor", "chain_shirt"),
        ("aa1dbba3-59ba-5516-866e-a2981e74bd0e",),
    ),
    (
        "monsters.goblins.goblin_boss",
        "goblin_boss",
        "Chain Shirt",
        named("armor", "chain_shirt"),
        ("21c2ea83-a7eb-585c-b42d-7f9fe7122dbe",),
    ),
    (
        "monsters.guards.guard",
        "guard",
        "Chain Shirt",
        named("armor", "chain_shirt"),
        ("18fb14ab-3a29-5197-b0c5-31fbd070466b",),
    ),
    (
        "monsters.priests.priest",
        "priest",
        "Chain Shirt",
        named("armor", "chain_shirt"),
        ("fcf09668-e3b9-5c75-b065-a154d3c0a3bf",),
    ),
    (
        "monsters.priests.priest_acolyte",
        "priest_acolyte",
        "Chain Shirt",
        named("armor", "chain_shirt"),
        ("f65f970f-5be6-5566-9ca7-b1a8c86e6dc8",),
    ),
    (
        "monsters.warriors.warrior_infantry",
        "warrior_infantry",
        "Chain Shirt",
        named("armor", "chain_shirt"),
        ("28ba840d-181d-5c7f-a81a-a860fdba8111",),
    ),
    (
        "monsters.hobgoblins.hobgoblin_captain",
        "hobgoblin_captain",
        "Half Plate Armor",
        named("armor", "half_plate_armor"),
        ("6b0a0520-29c5-5b36-bf0f-c9e63c6023fb",),
    ),
    (
        "monsters.hobgoblins.hobgoblin_warrior",
        "hobgoblin_warrior",
        "Half Plate Armor",
        named("armor", "half_plate_armor"),
        ("0333372b-6f2a-5c0e-a949-710a805a1096",),
    ),
    (
        "classes.bard",
        "core_traits",
        "Leather Armor",
        named("armor", "leather_armor"),
        ("73a15de1-87fe-504d-9fc1-8253175bfad7",),
    ),
    (
        "classes.druid",
        "core_traits",
        "Leather Armor",
        named("armor", "leather_armor"),
        ("5e29d7a9-14b0-5b46-984f-32941631b224",),
    ),
    (
        "classes.rogue",
        "core_traits",
        "Leather Armor",
        named("armor", "leather_armor"),
        ("e15857ee-0ac7-5b19-bf6d-ddd9069b70f0",),
    ),
    (
        "classes.warlock",
        "core_traits",
        "Leather Armor",
        named("armor", "leather_armor"),
        ("347f4f5f-2de3-5072-b4a6-e6809f51e0bd",),
    ),
    (
        "monsters.bandits.bandit",
        "bandit",
        "Leather Armor",
        named("armor", "leather_armor"),
        ("3c87ea31-d4b4-5947-b78a-0bdf913bb4f9",),
    ),
    (
        "monsters.cultists.cultist",
        "cultist",
        "Leather Armor",
        named("armor", "leather_armor"),
        ("46e0feeb-1fed-510c-a7df-6c929a951270",),
    ),
    (
        "monsters.cultists.cultist_fanatic",
        "cultist_fanatic",
        "Leather Armor",
        named("armor", "leather_armor"),
        ("43a84aa3-7ae9-5c44-b509-504fb48945d3",),
    ),
    (
        "monsters.goblins.goblin_warrior",
        "goblin_warrior",
        "Leather Armor",
        named("armor", "leather_armor"),
        ("21a32302-5062-5414-9e49-aece9aa8aab3",),
    ),
    (
        "monsters.pirates.pirate",
        "pirate",
        "Leather Armor",
        named("armor", "leather_armor"),
        ("ddf68069-60e4-5f9e-9d61-162782577876",),
    ),
    (
        "monsters.scout.scout",
        "scout",
        "Leather Armor",
        named("armor", "leather_armor"),
        ("e9a8fd1f-3533-5fc6-802c-9d7e6efb3a49",),
    ),
    (
        "monsters.toughs.tough",
        "tough",
        "Leather Armor",
        named("armor", "leather_armor"),
        ("250dd03d-4052-5255-ba2c-22a2556e0992",),
    ),
    (
        "magic_items.crafting_magic_items",
        "time_and_cost",
        "Plate Armor",
        named("armor", "plate_armor"),
        ("d5d97869-3ec0-5091-b447-22d91d2d78b5",),
    ),
    (
        "magic_items.magic_item_categories",
        "armor",
        "Plate Armor",
        named("armor", "plate_armor"),
        ("f20e75f5-4053-5800-99fa-fbacf1d682bb",),
    ),
    (
        "magic_items.magic_item_rarity",
        "magic_item_values_by_rarity",
        "Plate Armor",
        named("armor", "plate_armor"),
        ("2909e2fc-8085-5114-810c-8eb656af6b29",),
    ),
    (
        "monsters.knight.knight",
        "knight",
        "Plate Armor",
        named("armor", "plate_armor"),
        ("f041b588-a307-59be-9270-b4ae4bc44a0b",),
    ),
    (
        "monsters.warriors.veteran_warrior",
        "veteran_warrior",
        "Splint Armor",
        named("armor", "splint_armor"),
        ("4f8520c5-eeb9-588c-a355-6dd9af2780b7",),
    ),
    (
        "classes.fighter",
        "core_traits",
        "Studded Leather Armor",
        named("armor", "studded_leather_armor"),
        ("5bae2240-b5c8-5e5e-8069-1c077312521f",),
    ),
    (
        "classes.ranger",
        "core_traits",
        "Studded Leather Armor",
        named("armor", "studded_leather_armor"),
        ("e357b4c1-dc21-545f-9c2b-dd3dc20b10e3",),
    ),
    (
        "monsters.assassin.assassin",
        "assassin",
        "Studded Leather Armor",
        named("armor", "studded_leather_armor"),
        ("de503114-cdd5-5db0-9ffc-d062127b95e8",),
    ),
    (
        "monsters.bandits.bandit_captain",
        "bandit_captain",
        "Studded Leather Armor",
        named("armor", "studded_leather_armor"),
        ("44864065-c5db-5f38-b07b-8339b39d331c",),
    ),
    (
        "monsters.druid.druid",
        "druid",
        "Studded Leather Armor",
        named("armor", "studded_leather_armor"),
        ("5ba40a04-4619-5d9d-b670-0f316d84e4fe",),
    ),
    (
        "monsters.gladiator.gladiator",
        "gladiator",
        "Studded Leather Armor",
        named("armor", "studded_leather_armor"),
        ("72884613-a75b-521b-98c4-9c8f9ad51489",),
    ),
    (
        "monsters.wight.wight",
        "wight",
        "Studded Leather Armor",
        named("armor", "studded_leather_armor"),
        ("86436269-69eb-5e32-90e6-84bf87d93d9c",),
    ),
    (
        "magic_items.folding_boat",
        "folding_boat",
        "Keelboat",
        named("mounts_and_vehicles", "keelboat"),
        (
            "9fc720fe-58c3-52d7-8cdb-92cbe62d0c5b",
            "c5d40317-2aef-562c-b60f-56d1809a04aa",
        ),
    ),
    (
        "magic_items.folding_boat",
        "folding_boat",
        "Rowboat",
        named("mounts_and_vehicles", "rowboat"),
        (
            "62951c5f-3bb6-5fb8-874c-b9ebae61d676",
            "9fc720fe-58c3-52d7-8cdb-92cbe62d0c5b",
        ),
    ),
    (
        "magic_items.robe_of_useful_items",
        "robe_of_useful_items",
        "Rowboat",
        named("mounts_and_vehicles", "rowboat"),
        ("7a5606af-468b-54ba-93b5-012bb3e33cdd",),
    ),
    (
        "magic_items.crafting_magic_items",
        "tools",
        "Alchemist's Supplies",
        named("tools", "alchemists_supplies"),
        ("4e8cdbcb-4277-52dd-bd95-7b2d7d07138c",),
    ),
    (
        "magic_items.crafting_magic_items",
        "tools",
        "Jeweler's Tools",
        named("tools", "jewelers_tools"),
        ("4e8cdbcb-4277-52dd-bd95-7b2d7d07138c",),
    ),
    (
        "magic_items.crafting_magic_items",
        "tools",
        "Leatherworker's Tools",
        named("tools", "leatherworkers_tools"),
        ("4e8cdbcb-4277-52dd-bd95-7b2d7d07138c",),
    ),
    (
        "classes.bard",
        "core_traits",
        "Musical Instrument",
        named("tools", "musical_instrument"),
        ("73a15de1-87fe-504d-9fc1-8253175bfad7",),
    ),
    (
        "classes.bard",
        "core_traits",
        "Musical Instruments",
        named("tools", "musical_instrument"),
        ("73a15de1-87fe-504d-9fc1-8253175bfad7",),
    ),
    (
        "classes.monk",
        "core_traits",
        "Musical Instrument",
        named("tools", "musical_instrument"),
        ("ffecf855-ed96-5042-8654-49f86f398b6f",),
    ),
    (
        "gameplay_toolbox.poison",
        "harvesting_poison",
        "Poisoner's Kit",
        named("tools", "poisoners_kit"),
        ("d89f4179-ad5d-50f1-b7bd-99c6da61d937",),
    ),
    (
        "magic_items.crafting_magic_items",
        "tools",
        "Smith's Tools",
        named("tools", "smiths_tools"),
        ("4e8cdbcb-4277-52dd-bd95-7b2d7d07138c",),
    ),
    (
        "magic_items.crafting_magic_items",
        "tools",
        "Tinker's Tools",
        named("tools", "tinkers_tools"),
        ("4e8cdbcb-4277-52dd-bd95-7b2d7d07138c",),
    ),
    (
        "magic_items.crafting_magic_items",
        "tools",
        "Weaver's Tools",
        named("tools", "weavers_tools"),
        ("4e8cdbcb-4277-52dd-bd95-7b2d7d07138c",),
    ),
    (
        "magic_items.crafting_magic_items",
        "tools",
        "Woodcarver's Tools",
        named("tools", "woodcarvers_tools"),
        ("4e8cdbcb-4277-52dd-bd95-7b2d7d07138c",),
    ),
    (
        "magic_items.rod_of_lordly_might",
        "rod_of_lordly_might",
        "Battleaxe",
        named("weapons", "battleaxe"),
        ("b0686dc8-73d0-52ab-bcab-33405dcc2584",),
    ),
    (
        "monsters.ettin.ettin",
        "ettin",
        "Battleaxe",
        named("weapons", "battleaxe"),
        ("7b35e8d1-3c84-5953-82bd-a14813cc6975",),
    ),
    (
        "classes.fighter",
        "core_traits",
        "Flail",
        named("weapons", "flail"),
        ("5bae2240-b5c8-5e5e-8069-1c077312521f",),
    ),
    (
        "classes.barbarian",
        "core_traits",
        "Greataxe",
        named("weapons", "greataxe"),
        ("1b44dce7-3c45-59ff-a269-a042e0826857",),
    ),
    (
        "monsters.berserker.berserker",
        "berserker",
        "Greataxe",
        named("weapons", "greataxe"),
        ("5eb0d3e9-1192-56aa-abde-3f3a6ae5cd7b",),
    ),
    (
        "monsters.ogre.ogre",
        "ogre",
        "Greatclub",
        named("weapons", "greatclub"),
        ("edbf60d6-2891-56ce-a850-5c48d71e564f",),
    ),
    (
        "classes.fighter",
        "core_traits",
        "Greatsword",
        named("weapons", "greatsword"),
        ("5bae2240-b5c8-5e5e-8069-1c077312521f",),
    ),
    (
        "monsters.hobgoblins.hobgoblin_captain",
        "hobgoblin_captain",
        "Greatsword",
        named("weapons", "greatsword"),
        ("6b0a0520-29c5-5b36-bf0f-c9e63c6023fb",),
    ),
    (
        "monsters.knight.knight",
        "knight",
        "Greatsword",
        named("weapons", "greatsword"),
        ("f041b588-a307-59be-9270-b4ae4bc44a0b",),
    ),
    (
        "monsters.warriors.veteran_warrior",
        "veteran_warrior",
        "Greatsword",
        named("weapons", "greatsword"),
        ("4f8520c5-eeb9-588c-a355-6dd9af2780b7",),
    ),
    (
        "monsters.spy.spy",
        "spy",
        "Hand Crossbow",
        named("weapons", "hand_crossbow"),
        ("7ee254d1-ac70-5685-999d-9cff527e751a",),
    ),
    (
        "monsters.wererat.wererat",
        "wererat",
        "Hand Crossbow",
        named("weapons", "hand_crossbow"),
        ("0a9487bf-7af5-5288-afed-af0bc84cb099",),
    ),
    (
        "classes.barbarian",
        "core_traits",
        "Handaxes",
        named("weapons", "handaxe"),
        ("1b44dce7-3c45-59ff-a269-a042e0826857",),
    ),
    (
        "monsters.werebear.werebear",
        "werebear",
        "Handaxes",
        named("weapons", "handaxe"),
        ("89186f42-32dc-5eac-9003-5effad26266a",),
    ),
    (
        "monsters.knight.knight",
        "knight",
        "Heavy Crossbow",
        named("weapons", "heavy_crossbow"),
        ("f041b588-a307-59be-9270-b4ae4bc44a0b",),
    ),
    (
        "monsters.toughs.tough",
        "tough",
        "Heavy Crossbow",
        named("weapons", "heavy_crossbow"),
        ("250dd03d-4052-5255-ba2c-22a2556e0992",),
    ),
    (
        "monsters.toughs.tough_boss",
        "tough_boss",
        "Heavy Crossbow",
        named("weapons", "heavy_crossbow"),
        ("4e46339c-dd19-5bb9-b817-94219bfb2d38",),
    ),
    (
        "monsters.warriors.veteran_warrior",
        "veteran_warrior",
        "Heavy Crossbow",
        named("weapons", "heavy_crossbow"),
        ("4f8520c5-eeb9-588c-a355-6dd9af2780b7",),
    ),
    (
        "classes.fighter",
        "core_traits",
        "Javelins",
        named("weapons", "javelin"),
        ("5bae2240-b5c8-5e5e-8069-1c077312521f",),
    ),
    (
        "classes.paladin",
        "core_traits",
        "Javelins",
        named("weapons", "javelin"),
        ("4186658b-3701-57d4-b064-028906ee7375",),
    ),
    (
        "monsters.bugbears.bugbear_stalker",
        "bugbear_stalker",
        "Javelins",
        named("weapons", "javelin"),
        ("aa1dbba3-59ba-5516-866e-a2981e74bd0e",),
    ),
    (
        "monsters.guards.guard_captain",
        "guard_captain",
        "Javelins",
        named("weapons", "javelin"),
        ("79ed318a-64a4-5c05-b587-b904d3b4e1d4",),
    ),
    (
        "monsters.ogre.ogre",
        "ogre",
        "Javelins",
        named("weapons", "javelin"),
        ("edbf60d6-2891-56ce-a850-5c48d71e564f",),
    ),
    (
        "monsters.wereboar.wereboar",
        "wereboar",
        "Javelins",
        named("weapons", "javelin"),
        ("1a94afa4-10fc-5a3a-98ff-23d8a2d02aa7",),
    ),
    (
        "monsters.assassin.assassin",
        "assassin",
        "Light Crossbow",
        named("weapons", "light_crossbow"),
        ("de503114-cdd5-5db0-9ffc-d062127b95e8",),
    ),
    (
        "monsters.bandits.bandit",
        "bandit",
        "Light Crossbow",
        named("weapons", "light_crossbow"),
        ("3c87ea31-d4b4-5947-b78a-0bdf913bb4f9",),
    ),
    (
        "classes.fighter",
        "core_traits",
        "Longbow",
        named("weapons", "longbow"),
        ("5bae2240-b5c8-5e5e-8069-1c077312521f",),
    ),
    (
        "classes.ranger",
        "core_traits",
        "Longbow",
        named("weapons", "longbow"),
        ("e357b4c1-dc21-545f-9c2b-dd3dc20b10e3",),
    ),
    (
        "magic_items.bracers_of_archery",
        "bracers_of_archery",
        "Longbow",
        named("weapons", "longbow"),
        ("3c1a424d-2f81-5a43-8522-f4c8d46e23ad",),
    ),
    (
        "magic_items.magic_item_categories",
        "weapons",
        "Longbow",
        named("weapons", "longbow"),
        ("e43f5e79-08f4-52f1-bcb4-54de7dc4c2d7",),
    ),
    (
        "monsters.centaur.centaur_trooper",
        "centaur_trooper",
        "Longbow",
        named("weapons", "longbow"),
        ("af28874c-d5a1-5099-8ed0-98114984128c",),
    ),
    (
        "monsters.hobgoblins.hobgoblin_captain",
        "hobgoblin_captain",
        "Longbow",
        named("weapons", "longbow"),
        ("6b0a0520-29c5-5b36-bf0f-c9e63c6023fb",),
    ),
    (
        "monsters.hobgoblins.hobgoblin_warrior",
        "hobgoblin_warrior",
        "Longbow",
        named("weapons", "longbow"),
        ("0333372b-6f2a-5c0e-a949-710a805a1096",),
    ),
    (
        "monsters.scout.scout",
        "scout",
        "Longbow",
        named("weapons", "longbow"),
        ("e9a8fd1f-3533-5fc6-802c-9d7e6efb3a49",),
    ),
    (
        "monsters.weretiger.weretiger",
        "weretiger",
        "Longbow",
        named("weapons", "longbow"),
        ("d52de4c3-27d1-576f-839b-99f758c258d3",),
    ),
    (
        "monsters.werewolf.werewolf",
        "werewolf",
        "Longbow",
        named("weapons", "longbow"),
        ("809d4174-9f1d-5c3a-a278-859cc9639fcc",),
    ),
    (
        "classes.paladin",
        "core_traits",
        "Longsword",
        named("weapons", "longsword"),
        ("4186658b-3701-57d4-b064-028906ee7375",),
    ),
    (
        "magic_items.magic_item_categories",
        "weapons",
        "Longsword",
        named("weapons", "longsword"),
        ("e43f5e79-08f4-52f1-bcb4-54de7dc4c2d7",),
    ),
    (
        "magic_items.rod_of_lordly_might",
        "rod_of_lordly_might",
        "Longsword",
        named("weapons", "longsword"),
        ("ccf93865-2659-50c8-9b3d-c96393e37a81",),
    ),
    (
        "magic_items.sun_blade",
        "sun_blade",
        "Longsword",
        named("weapons", "longsword"),
        (
            "1e03eb29-bf39-5353-ba48-02f8f6ddd241",
            "338a0fd1-63f7-5789-894d-cd005cdbb67d",
        ),
    ),
    (
        "monsters.guards.guard_captain",
        "guard_captain",
        "Longsword",
        named("weapons", "longsword"),
        ("79ed318a-64a4-5c05-b587-b904d3b4e1d4",),
    ),
    (
        "monsters.hobgoblins.hobgoblin_warrior",
        "hobgoblin_warrior",
        "Longsword",
        named("weapons", "longsword"),
        ("0333372b-6f2a-5c0e-a949-710a805a1096",),
    ),
    (
        "classes.cleric",
        "core_traits",
        "Mace",
        named("weapons", "mace"),
        ("1b3e6f7f-bf6a-5b29-8bac-45808cafd3bc",),
    ),
    (
        "magic_items.rod_of_lordly_might",
        "rod_of_lordly_might",
        "Mace",
        named("weapons", "mace"),
        ("ac9fd61e-f1fb-5cb6-8bb2-aedfaccffee1",),
    ),
    (
        "monsters.priests.priest",
        "priest",
        "Mace",
        named("weapons", "mace"),
        ("fcf09668-e3b9-5c75-b065-a154d3c0a3bf",),
    ),
    (
        "monsters.priests.priest_acolyte",
        "priest_acolyte",
        "Mace",
        named("weapons", "mace"),
        ("f65f970f-5be6-5566-9ca7-b1a8c86e6dc8",),
    ),
    (
        "monsters.toughs.tough",
        "tough",
        "Mace",
        named("weapons", "mace"),
        ("250dd03d-4052-5255-ba2c-22a2556e0992",),
    ),
    (
        "monsters.bugbears.bugbear_stalker",
        "bugbear_stalker",
        "Morningstar",
        named("weapons", "morningstar"),
        ("aa1dbba3-59ba-5516-866e-a2981e74bd0e",),
    ),
    (
        "monsters.ettin.ettin",
        "ettin",
        "Morningstar",
        named("weapons", "morningstar"),
        ("7b35e8d1-3c84-5953-82bd-a14813cc6975",),
    ),
    (
        "monsters.centaur.centaur_trooper",
        "centaur_trooper",
        "Pike",
        named("weapons", "pike"),
        ("af28874c-d5a1-5099-8ed0-98114984128c",),
    ),
    (
        "monsters.bandits.bandit_captain",
        "bandit_captain",
        "Pistol",
        named("weapons", "pistol"),
        ("44864065-c5db-5f38-b07b-8339b39d331c",),
    ),
    (
        "monsters.pirates.pirate_captain",
        "pirate_captain",
        "Pistol",
        named("weapons", "pistol"),
        ("b3d3526f-5e21-589e-b3b8-27e85274fdda",),
    ),
    (
        "monsters.noble.noble",
        "noble",
        "Rapier",
        named("weapons", "rapier"),
        ("797ebcbf-cc44-5b6b-a709-42f8905e788f",),
    ),
    (
        "monsters.pirates.pirate_captain",
        "pirate_captain",
        "Rapier",
        named("weapons", "rapier"),
        ("b3d3526f-5e21-589e-b3b8-27e85274fdda",),
    ),
    (
        "classes.fighter",
        "core_traits",
        "Scimitar",
        named("weapons", "scimitar"),
        ("5bae2240-b5c8-5e5e-8069-1c077312521f",),
    ),
    (
        "classes.ranger",
        "core_traits",
        "Scimitar",
        named("weapons", "scimitar"),
        ("e357b4c1-dc21-545f-9c2b-dd3dc20b10e3",),
    ),
    (
        "monsters.bandits.bandit",
        "bandit",
        "Scimitar",
        named("weapons", "scimitar"),
        ("3c87ea31-d4b4-5947-b78a-0bdf913bb4f9",),
    ),
    (
        "monsters.bandits.bandit_captain",
        "bandit_captain",
        "Scimitar",
        named("weapons", "scimitar"),
        ("44864065-c5db-5f38-b07b-8339b39d331c",),
    ),
    (
        "monsters.goblins.goblin_boss",
        "goblin_boss",
        "Scimitar",
        named("weapons", "scimitar"),
        ("21c2ea83-a7eb-585c-b42d-7f9fe7122dbe",),
    ),
    (
        "monsters.goblins.goblin_warrior",
        "goblin_warrior",
        "Scimitar",
        named("weapons", "scimitar"),
        ("21a32302-5062-5414-9e49-aece9aa8aab3",),
    ),
    (
        "classes.fighter",
        "core_traits",
        "Shortsword",
        named("weapons", "shortsword"),
        ("5bae2240-b5c8-5e5e-8069-1c077312521f",),
    ),
    (
        "classes.ranger",
        "core_traits",
        "Shortsword",
        named("weapons", "shortsword"),
        ("e357b4c1-dc21-545f-9c2b-dd3dc20b10e3",),
    ),
    (
        "classes.rogue",
        "core_traits",
        "Shortsword",
        named("weapons", "shortsword"),
        ("e15857ee-0ac7-5b19-bf6d-ddd9069b70f0",),
    ),
    (
        "magic_items.rod_of_lordly_might",
        "rod_of_lordly_might",
        "Shortsword",
        named("weapons", "shortsword"),
        ("ccf93865-2659-50c8-9b3d-c96393e37a81",),
    ),
    (
        "monsters.assassin.assassin",
        "assassin",
        "Shortsword",
        named("weapons", "shortsword"),
        ("de503114-cdd5-5db0-9ffc-d062127b95e8",),
    ),
    (
        "monsters.scout.scout",
        "scout",
        "Shortsword",
        named("weapons", "shortsword"),
        ("e9a8fd1f-3533-5fc6-802c-9d7e6efb3a49",),
    ),
    (
        "monsters.skeletons.skeleton",
        "skeleton",
        "Shortsword",
        named("weapons", "shortsword"),
        ("1d210ff4-bf74-5706-8ec2-0c4f3c63f626",),
    ),
    (
        "monsters.spy.spy",
        "spy",
        "Shortsword",
        named("weapons", "shortsword"),
        ("7ee254d1-ac70-5685-999d-9cff527e751a",),
    ),
    (
        "classes.druid",
        "core_traits",
        "Sickle",
        named("weapons", "sickle"),
        ("5e29d7a9-14b0-5b46-984f-32941631b224",),
    ),
    (
        "classes.warlock",
        "core_traits",
        "Sickle",
        named("weapons", "sickle"),
        ("347f4f5f-2de3-5072-b4a6-e6809f51e0bd",),
    ),
    (
        "monsters.cultists.cultist",
        "cultist",
        "Sickle",
        named("weapons", "sickle"),
        ("46e0feeb-1fed-510c-a7df-6c929a951270",),
    ),
    (
        "monsters.toughs.tough_boss",
        "tough_boss",
        "Warhammer",
        named("weapons", "warhammer"),
        ("4e46339c-dd19-5bb9-b817-94219bfb2d38",),
    ),
)

#: Equipment-scoped citations this packet leaves unresolved: (text, why).
CITED_UNRESOLVED: tuple[tuple[str, str], ...] = (
    (
        "Spellbook",
        "Equipment prints no Spellbook item; the Wizard's Spellcasting feature "
        "does not make a generic Book one, nor move the citation's scope",
    ),
)


def draft_cited_resolutions(
    binding: ReleaseBinding,
) -> tuple[ReferenceResolution, ...]:
    """The 161 cited-target resolutions, drafted for review against *binding*."""
    drafts = tuple(
        ReferenceResolution(
            resolution_id=(
                f"resolve-{_slug(record)}-{_slug(component) or 'record'}"
                f"-{_slug(text)}-equipment-cited-1"
            ),
            from_record_key=record,
            from_component_key=component,
            source_text=text,
            scope_key=EQUIPMENT,
            target_record_key=target,
            release_binding=binding,
            provenance_span_ids=spans,
        )
        for record, component, text, target, spans in CITED_DRAFTS
    )
    assert len({d.resolution_id for d in drafts}) == len(drafts) == 161
    return drafts


def main(db: str) -> int:
    here = Path(__file__).resolve().parent
    code = emit(db, build, here / PROPOSAL_FILE, expected_representation_findings())
    if code == 0:
        from afterworlds.persistence.database import (
            create_engine,
            create_session_factory,
        )

        engine = create_engine(f"sqlite:///{db}")
        with create_session_factory(engine)() as session:
            binding = published_release_binding(session)
        engine.dispose()
        payload = reference_resolution_payload(draft_cited_resolutions(binding))
        (here / DRAFTS_FILE).write_bytes(
            (json.dumps(payload, indent=2) + "\n").encode("utf-8")
        )
    return code


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
