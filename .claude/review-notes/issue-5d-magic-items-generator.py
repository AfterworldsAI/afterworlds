# ruff: noqa: E501  -- patterns are verbatim source text, kept whole to be greppable
"""Author the **Magic Items** proposal: the whole part the SRD prints.

REVIEW MATERIAL for CRD Issue 5d (#137) over the corrected 5c release
``ebdd9333-eeed-5df1-b3e1-8b97c2f65f80`` / ``5.2.1-corpus.574662e9-0ef``. It
emits one *unaccepted* ``5d-proposal-2`` artifact and one file of unrecorded
resolution drafts. It accepts nothing, publishes nothing, writes nothing under
``oracles/`` and records no resolution.

Scope, 1332 leaves (pp204-253 of the official PDF): every leaf of the *Magic
Items* part below its ``# Magic Items`` heading and the paragraph printed
directly under that heading, which both stay with the other part headings
(shared coverage is deferred). None was accepted before. The qualified leaf
texts are ``issue-5d-magic-items-source.py``; this file reads them from there.

Record grain:

* each top-level section the release prints is one ``general_rule`` record,
  ``magic_items.<section>``, its first component its heading and the prose
  before its first subheading, then one component per printed subheading in
  printed order. The four floated *Sentient Item's* tables the release prints
  inside *Special Purpose* are each their own component there, in printed
  position: the trait subsections cite each by name;
* the PDF sets *Time and Cost* inside *Crafting Magic Items*, and *Sentient
  Magic Item Traits* and *Special Purpose* inside *Sentient Magic Items*
  (pp208-209), though the release prints each at ``##``. Each stays its own
  review unit over its own container and is read into that section's record,
  its components after the section's own, in printed order. No record, edge or
  membership is added for them, and the release is read as it is;
* each of the 258 items *Magic Items A-Z* prints -- a ``####`` heading whose
  next line is its italic category, rarity and attunement -- is its own
  ``magic_item`` record ``magic_items.<item>`` and a ``CATALOGUE_MEMBER`` of
  ``magic_items.magic_items_a_z``, in printed order. Each is one prose-bound
  component keyed by its own slug, heading and type line included, so a direct
  read of an item carries its rarity and attunement; its tables and variants
  stay in it. The section's components never bind an item's leaves;
* the two stat blocks an item prints (the *Figurine of Wondrous Power*'s Giant
  Fly, the *Mysterious Deck*'s Avatar of Death) are ``creature`` records
  ``SCOPED_WITHIN`` their item, one prose component per printed container.

Every component is prose-bound: no typed contract exists for rarity,
attunement, charges or an item's effects, so none is invented (ADR-005d
Decision 4). A component whose text explicitly leaves an open ruling or outcome
to whoever runs the game is ``gamemaster_latitude`` (``LATITUDE``, by the
delegating words); one that only names the GM choosing among printed options
or rolling a printed table states reducible meaning (``NOT_LATITUDE``), as does
every other component: ``no_identified_structured_use``.

References, once per component: each accepted Rules Glossary term the prose
depends on; every spell named in italics, to its accepted record; every item
of this part named in italics, to its record here, by the exact heading or a
listed printed variant (``VARIANTS``); an unqualified Potion of Healing to the
accepted *Equipment* potion (the 2d4 + 2 potion the family table's first row
names) and an unqualified Spell Scroll to the family here (``SHARED``); the
plain-text equipment the accepted *Equipment* holds a record for, to it, and
every other one unresolved; each creature named in bold to "Monsters",
unresolved, by its whole printed name where the bolding covers only part of it
(``BOLD_PREFIXES``: the Giant Goat), or to the stat block its item prints; the
"Equipment" and "Monsters" pointers unresolved, "Scribing Spell Scrolls" to its
accepted section and "see Poison in Gameplay Toolbox" to the accepted toolbox
Poison. Names an effect depends on that the source prints plain -- a
cast-spell or rolled-creature table cell, a named spell or creature an effect
produces -- are read the same way (``PLAIN``), by the operative meaning, not
the typography; an example or a category label is not. A pointer inside its
own record ("Conflict") and an item naming itself are not references.

Governing context: an item's component also reads, ``CONTEXTUAL`` and in source
order, the exact *Magic Item Rules* and *Activating a Magic Item* spans that
govern it -- the attunement prerequisite rule for an item that requires a
class or a spellcaster, the command word rule for an item using one, *Spells
Cast from Items* for an item that casts a spell, and the item's own
spellcasting ability rule where the item says it uses its own. Each span stays
owned (``PRIMARY``) by its section's component, so an override or disable of
that owner suppresses it on the item, and a catalogue reading does not repeat
it.

Run: ``python issue-5d-magic-items-generator.py <published afterworlds.db>``
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from collections.abc import Iterable
from functools import cache
from pathlib import Path

from sqlalchemy.orm import Session

from afterworlds.ingestion.mechanical.authoring import (
    Built,
    EntryBatch,
    EntryComponent,
    Placement,
    Target,
    accepted_read_findings,
    build_entry_batch,
    emit,
    read_accepted,
    scoped,
)
from afterworlds.ingestion.mechanical.authoring import batch_findings as batch_findings
from afterworlds.ingestion.mechanical.authoring import render as render
from afterworlds.ingestion.mechanical.bound_corpus import published_release_binding
from afterworlds.ingestion.mechanical.models import (
    ComponentHandling,
    ReferenceResolution,
    ReleaseBinding,
    ReviewUnitKind,
)
from afterworlds.ingestion.mechanical.oracle import (
    COMMITTED_ORACLE_DIR,
    AcceptedInputs,
)
from afterworlds.ingestion.mechanical.reference_resolution import (
    reference_resolution_payload,
)
from afterworlds.ingestion.mechanical.representation import RecordKind

ORIGIN = "issue-5d-magic-items-generator.py"
PROPOSAL_FILE = "issue-5d-magic-items-PROPOSAL.json"
DRAFTS_FILE = "issue-5d-magic-items-resolutions-DRAFTS.json"
#: Every record here is placed; the unplaced-entry default is never read.
PARENT = ("Rules Glossary", "Rules Definitions")
PART = "Magic Items"
A_Z = "Magic Items A–Z"
MAGIC_ITEMS = "srd-5.2.1/magic-items"
SPELLS = "srd-5.2.1/spells"
EQUIPMENT = "srd-5.2.1/equipment"
MONSTERS = "srd-5.2.1/monsters"
#: The target of a printed pointer whose destination has no record yet.
UNRESOLVED_TARGET = ""
#: The accepted authority this packet composes over, as the task pins it.
ORACLE_FILE = COMMITTED_ORACLE_DIR / "srd-5-2-1-corpus-574662e9-0ef.json"
ORACLE_SHA256 = "671f47d706f5eb484c70d8bacaa9d169801c014689d7fd400e018e3d999eae95"

GM = "gamemaster_latitude"
NO_USE = "no_identified_structured_use"
P = ComponentHandling.PROSE_BOUND
#: A section and the section the source sets it in, read into its record.
READ_INTO = {
    "Time and Cost": "Crafting Magic Items",
    "Sentient Magic Item Traits": "Sentient Magic Items",
    "Special Purpose": "Sentient Magic Items",
}


def _load(name: str) -> object:
    spec = importlib.util.spec_from_file_location(
        name.replace("-", "_"), Path(__file__).with_name(f"{name}.py")
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclasses resolve their own module
    spec.loader.exec_module(module)
    return module


def _source() -> tuple[tuple[tuple[str, ...], str], ...]:
    module = _load("issue-5d-magic-items-source")
    return tuple(((PART, *p), t) for p, t in module.LEAVES)  # type: ignore[attr-defined]


#: (full label path, exact text) of every scoped leaf, in printed order.
LEAVES = _source()
#: The accepted spell descriptions: their names, keys and glossary terms.
SD = _load("issue-5d-spell-descriptions-generator")
slug = SD.slug  # type: ignore[attr-defined]
spell_key = SD.spell_key  # type: ignore[attr-defined]


def texts_at(path: tuple[str, ...]) -> list[str]:
    """The leaves printed directly in *path*, not in a container below it."""
    return [t for p, t in LEAVES if p == path]


def containers(path: tuple[str, ...]) -> list[tuple[str, ...]]:
    """*path* and every container below it, in printed order."""
    return list(dict.fromkeys(p for p, _ in LEAVES if p[: len(path)] == path))


def children(path: tuple[str, ...]) -> list[str]:
    """The labels of *path*'s sub-containers, in printed order."""
    return list(
        dict.fromkeys(
            p[len(path)]
            for p, _ in LEAVES
            if p[: len(path)] == path and len(p) > len(path)
        )
    )


SECTIONS = tuple(children((PART,)))
assert SECTIONS == (
    "Magic Item Categories",
    "Magic Item Rules",
    "Magic Item Rarity",
    "Activating a Magic Item",
    '"The Next Dawn"',
    "Cursed Items",
    "Magic Item Resilience",
    "Crafting Magic Items",
    "Time and Cost",
    "Sentient Magic Items",
    "Sentient Magic Item Traits",
    "Special Purpose",
    A_Z,
), SECTIONS


def section_key(section: str) -> str:
    return f"magic_items.{slug(section)}"


def section_record(section: str) -> str:
    """The record a printed section is read into."""
    return section_key(READ_INTO.get(section, section))


#: A catalogue item's second line: its italic category, rarity and attunement.
TYPE_LINE = re.compile(r"_[^_\n]+_")
#: The items, in printed order: every container below *Magic Items A-Z*.
ITEM_NAMES = tuple(children((PART, A_Z)))
assert len(ITEM_NAMES) == len({slug(n) for n in ITEM_NAMES}) == 258
for _n in ITEM_NAMES:
    _h, _type, *_ = texts_at((PART, A_Z, _n))
    assert _h == f"#### {_n}" and TYPE_LINE.fullmatch(_type), _n


def item_key(name: str) -> str:
    return f"magic_items.{slug(name)}"


assert not {item_key(n) for n in ITEM_NAMES} & {section_key(s) for s in SECTIONS}

#: The stat block each item prints, by item: (creature label, the bold name
#: its item's prose gives it).
STAT_BLOCKS = {
    "Figurine of Wondrous Power": ("Giant Fly", "Giant Fly"),
    "Mysterious Deck": ("Avatar of Death", "Avatar of Death"),
}
assert {n for n in ITEM_NAMES if children((PART, A_Z, n))} == set(STAT_BLOCKS)


def creature_key(item: str) -> str:
    return f"{item_key(item)}.{slug(STAT_BLOCKS[item][0])}"


def item_entry(name: str) -> str:
    return f"{slug(A_Z)}.{slug(name)}"


#: The four tables the release floats into *Special Purpose*, which the
#: *Sentient Magic Item Traits* subsections cite by name.
FLOATED = re.compile(r"\*\*(?P<n>Sentient Item's [A-Z][a-z]+(?: [A-Z][a-z]+)?)\*\*\n")


# ---------------------------------------------------------------------------
# Governing context
# ---------------------------------------------------------------------------
def _rule(path: tuple[str, ...], start: str) -> str:
    (text,) = [t for t in texts_at((PART, *path)) if t.startswith(start)]
    return text


#: The general rules an item's own words invoke, each printed once in its
#: section, which owns it; a direct read of the item carries it as CONTEXTUAL,
#: bound to that exact leaf. An item requiring attunement by a class or a
#: spellcaster reads *Attunement Prerequisites* (only a spell from traits or
#: features qualifies, not one from a magic item); one naming a command word
#: reads *Command Word* (a spoken one fails where sound is suppressed); one
#: letting its user cast a spell reads *Spells Cast from Items* (no slot, no
#: components, normal casting time, range, duration and Concentration unless
#: it says otherwise), and one casting with its user's own spellcasting
#: ability also its second paragraph. Declared by item, never searched for.
PREREQUISITES = _rule(("Magic Item Rules",), "_Attunement Prerequisites_.")
COMMAND_WORD = _rule(("Activating a Magic Item", "Command Word"), "A command word is")
_CAST = ("Activating a Magic Item", "Consumable Items", "Spells Cast from Items")
CAST_FROM_ITEMS = _rule(_CAST, "Some magic items allow the user to cast a spell")
OWN_ABILITY = _rule(_CAST, "A magic item may require the user to use their own")
#: The entry printing each context rule.
RULE_ENTRY = {
    PREREQUISITES: slug("Magic Item Rules"),
    COMMAND_WORD: slug("Activating a Magic Item"),
    CAST_FROM_ITEMS: slug("Activating a Magic Item"),
    OWN_ABILITY: slug("Activating a Magic Item"),
}
_CLASSES = {"Bard", "Cleric", "Druid", "Paladin", "Sorcerer", "Warlock", "Wizard"}
_BY = re.compile(r"Requires Attunement by an? (?P<by>[^)]+)\)")


def _prerequisite(name: str) -> bool:
    """Whether the item's type line names a class or spellcaster prerequisite
    (not the "Dwarf or a Creature Attuned to a Belt of Dwarvenkind")."""
    m = _BY.search(texts_at((PART, A_Z, name))[1])
    by = set(re.split(r", or |, | or ", m["by"])) if m else set()
    return bool(by) and by <= _CLASSES | {"Spellcaster"}


COMMAND_WORD_ITEMS = frozenset(
    {
        "Broom of Flying",
        "Carpet of Flying",
        "Decanter of Endless Water",
        "Flame Tongue",
        "Folding Boat",
        "Gem of Brightness",
        "Instant Fortress",
        "Mirror of Life Trapping",
        "Oathbow",
        "Plate Armor of Etherealness",
    }
)
#: The items whose bearer casts a spell from them, read by operative meaning:
#: the *Ioun Stone*'s Reserve ("you can cast any spell stored in it", like the
#: *Ring of Spell Storing*) and, of the *Figurine*'s variants, only the Silver
#: Raven's *Animal Messenger*. Not one whose creature casts for you (*Efreeti
#: Bottle*), that absorbs spells cast at it (*Rod of Absorption*), that confers
#: a spell's effect without a casting (*Potion of Invisibility*, the
#: *Talismans*), or the *Mysterious Deck*: its Moon grants you future *Wish*
#: casts and vanishes, so nothing is cast from the deck. Where only a variant
#: casts, the rule governs that variant's own component (``CASTING_VARIANTS``).
CASTING_ITEMS = frozenset(
    {
        "Amulet of the Planes",
        "Boots of Levitation",
        "Candle of Invocation",
        "Cape of the Mountebank",
        "Chime of Opening",
        "Circlet of Blasting",
        "Cloak of Arachnida",
        "Cloak of the Bat",
        "Crystal Ball",
        "Crystal Ball of Mind Reading",
        "Crystal Ball of Telepathy",
        "Crystal Ball of True Seeing",
        "Cube of Force",
        "Cubic Gate",
        "Dragon Orb",
        "Eyes of Charming",
        "Figurine of Wondrous Power",
        "Hat of Disguise",
        "Hat of Many Spells",
        "Helm of Brilliance",
        "Helm of Comprehending Languages",
        "Helm of Telepathy",
        "Helm of Teleportation",
        "Ioun Stone",
        "Luck Blade",
        "Medallion of Thoughts",
        "Necklace of Prayer Beads",
        "Potion of Animal Friendship",
        "Ring of Animal Influence",
        "Ring of Elemental Command",
        "Ring of Jumping",
        "Ring of Shooting Stars",
        "Ring of Spell Storing",
        "Ring of Telekinesis",
        "Ring of Three Wishes",
        "Ring of Water Walking",
        "Robe of Stars",
        "Rod of Alertness",
        "Rod of Resurrection",
        "Sending Stones",
        "Spell Scroll",
        "Staff of Charming",
        "Staff of Fire",
        "Staff of Frost",
        "Staff of Healing",
        "Staff of Power",
        "Staff of Swarming Insects",
        "Staff of the Magi",
        "Staff of the Woodlands",
        "Trident of Fish Command",
        "Wand of Binding",
        "Wand of Fear",
        "Wand of Fireballs",
        "Wand of Lightning Bolts",
        "Wand of Magic Detection",
        "Wand of Magic Missiles",
        "Wand of Polymorph",
        "Wand of Web",
        "Wand of Wonder",
        "Wind Fan",
    }
)
#: Of those, the items that cast with their user's own spellcasting ability.
OWN_ABILITY_ITEMS = frozenset(
    {
        "Hat of Many Spells",
        "Necklace of Prayer Beads",
        "Spell Scroll",
        "Staff of Charming",
        "Staff of Fire",
        "Staff of Frost",
        "Staff of Healing",
        "Staff of Power",
        "Staff of Swarming Insects",
        "Staff of the Magi",
        "Staff of the Woodlands",
    }
)
assert set(ITEM_NAMES) >= COMMAND_WORD_ITEMS | CASTING_ITEMS
assert OWN_ABILITY_ITEMS <= CASTING_ITEMS
assert len([n for n in ITEM_NAMES if _prerequisite(n)]) == 20
# Every item printing a command word reads the rule, and no other.
assert {
    n for n in ITEM_NAMES if any("command word" in t for t in texts_at((PART, A_Z, n)))
} == COMMAND_WORD_ITEMS


#: The rule each category's section prints for every item of it, unless the
#: item's description notes otherwise -- the item's own words stay its
#: authority: six staffs print themselves a *magic* Quarterstaff. Not read:
#: what a category merely describes (a rod's weight), *Mixing Potions* and the
#: scroll's readability (the *Spell Scroll* states its own), and the armor and
#: weapon type choice and *Ammunition* (they turn on a type the item may leave
#: open).
_CATEGORY = ("Magic Item Categories",)
CATEGORY_RULES = {
    "Armor": _rule((*_CATEGORY, "Armor"), "An item in the Armor category"),
    "Potion": _rule((*_CATEGORY, "Potions"), "_Using a Potion._"),
    "Ring": _rule((*_CATEGORY, "Rings"), "For its magic to function"),
    "Rod": _rule((*_CATEGORY, "Rods"), "Unless its description notes otherwise"),
    "Scroll": _rule((*_CATEGORY, "Scrolls"), "_Using a Scroll_."),
    "Staff": _rule((*_CATEGORY, "Staffs"), "Unless its description notes otherwise"),
    "Wand": _rule((*_CATEGORY, "Wands"), "Unless its description notes otherwise"),
}
_CATEGORY_OF = re.compile(
    r"_(?P<c>Armor|Potion|Ring|Rod|Scroll|Staff|Wand|Weapon|Wondrous Item)\b"
)


def category(name: str) -> str:
    m = _CATEGORY_OF.match(texts_at((PART, A_Z, name))[1])
    assert m, name
    return m["c"]


#: *Consumable Items*: an item used up when activated loses its magic. Read by
#: the items the source says are consumed: potions and scrolls (their category
#: says so) and those whose own words say it. An item stating its own end (a
#: *Feather Token* disappears) is read by its own words.
CONSUMED = _rule(
    ("Activating a Magic Item", "Consumable Items"), "Some items are consumed"
)
CONSUMED_BY_TEXT = {
    "Dust of Disappearance": "the dust is consumed",
    "Manual of Golems": "the book is consumed",
}
#: *Charges*: Identify reveals an item's remaining charges, and its attuned
#: creature knows them. Read by every item printing a number of charges.
CHARGES = _rule((*_CAST[:2], "Charges"), "Some magic items have charges")
_CHARGES = re.compile(r"\b\d+(?:d\d+)? charges\b")
RULE_ENTRY |= {t: slug("Magic Item Categories") for t in CATEGORY_RULES.values()}
RULE_ENTRY |= {
    CONSUMED: slug("Activating a Magic Item"),
    CHARGES: slug("Activating a Magic Item"),
}


def _charged(name: str) -> bool:
    return any(_CHARGES.search(t) for t in texts_at((PART, A_Z, name))[2:])


assert all(category(n) for n in ITEM_NAMES)
assert len([n for n in ITEM_NAMES if _charged(n)]) == 51
assert all(w in " ".join(texts_at((PART, A_Z, n))) for n, w in CONSUMED_BY_TEXT.items())


def item_context(name: str) -> tuple[tuple[str, str], ...]:
    """(text, entry printing it) of the rules a direct read of *name*
    carries, in source order."""
    kind = category(name)
    rules = {
        PREREQUISITES: _prerequisite(name),
        COMMAND_WORD: name in COMMAND_WORD_ITEMS,
        CAST_FROM_ITEMS: name in CASTING_ITEMS,
        OWN_ABILITY: name in OWN_ABILITY_ITEMS,
        CONSUMED: kind in {"Potion", "Scroll"} or name in CONSUMED_BY_TEXT,
        CHARGES: _charged(name),
    }
    if kind in CATEGORY_RULES:
        rules[CATEGORY_RULES[kind]] = True
    return tuple((t, RULE_ENTRY[t]) for _, t in LEAVES if rules.get(t))


#: The variant whose own leaves cast a spell from an item whose other variants
#: do not, by item: (the variant's printed name, its leaf count). The Silver
#: Raven grants *Animal Messenger* in raven form; the Reserve's three leaves
#: store spells and let you cast them. Each is its own component of the one
#: item record, in printed order between the item's leaves before and after
#: it; *Spells Cast from Items* governs that component alone.
CASTING_VARIANTS = {
    "Figurine of Wondrous Power": ("Silver Raven", 1),
    "Ioun Stone": ("Reserve", 3),
}
assert set(CASTING_VARIANTS) <= CASTING_ITEMS


def head_of(tbl: str) -> str:
    """A table's header rows and the opening of its body."""
    return tbl[: tbl.index("  <tbody>\n") + len("  <tbody>\n")]


def row_of(tbl: str, needle: str) -> str:
    """The one whole row of *tbl* that prints *needle*."""
    if tbl.count(needle) != 1:
        raise ValueError(f"{needle!r} is printed {tbl.count(needle)} times")
    at = tbl.index(needle)
    start = tbl.rindex("    <tr>\n", 0, at)
    return tbl[start : tbl.index("    </tr>\n", at) + len("    </tr>\n")]


def closer_of(tbl: str) -> str:
    """The close of a table's body and of the table, its last text."""
    closer = "  </tbody>\n</table>"
    if not tbl.endswith(closer):
        raise ValueError("a table ends at its body's close")
    return closer


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


#: The accepted *Equipment* record each family's table prints as some of its
#: rows, by the rows' first cells (Owner Decision 2026-09-27: one authoritative
#: item in both catalogues). *Equipment* sells the basic Potion of Healing
#: (2d4 + 2) and the cantrip and level 1 Spell Scrolls; the family prints them
#: as its first rows beside its wider variants. Each row is the *Equipment*
#: record's own ``SHARED_COMPONENT``, read with the table's head, and a
#: ``CATALOGUE_MEMBER`` of the family, which reads it in place as context. The
#: family keeps its other rows and its rules; the record keeps one identity.
SHARED_ROWS: dict[str, tuple[str, tuple[str, ...]]] = {
    "Potions of Healing": (
        "equipment.adventuring_gear.potion_of_healing",
        ("Potion of Healing",),
    ),
    "Spell Scroll": ("equipment.adventuring_gear.spell_scroll", ("Cantrip", "1")),
}
SHARED_COMPONENT = "magic_items_table"
#: The family's own passages its shared rows are read with, by opening words:
#: its type line and every paragraph stating a rule the rows are subject to --
#: the Spell Scroll's casting (an interrupted casting keeps the scroll), its
#: higher-level check, the level's DC and bonus, and copying a Wizard spell;
#: the potion's Hit Points by rarity. Not read: the potion's glimmer, which
#: describes and rules nothing. Each is the family's, read as context.
SHARED_FAMILY_TEXTS = {
    "Potions of Healing": ("_Potion, Rarity Varies_", "You regain Hit Points"),
    "Spell Scroll": (
        "_Scroll, Rarity Varies_",
        "A _Spell Scroll_ bears",
        "If the spell is on your spell list but",
        "The level of the spell on the scroll",
        "_Copying a Scroll into a Spellbook._",
    ),
}


def _table(name: str) -> str:
    (tbl,) = [t for t in texts_at((PART, A_Z, name)) if t.startswith("<table>")]
    return tbl


def shared_rows(name: str) -> tuple[str, tuple[str, ...]]:
    """(the table head, the rows its *Equipment* record owns) of family
    *name*'s one table."""
    tbl = _table(name)
    return head_of(tbl), tuple(
        row_of(tbl, f"<td>{c}</td>") for c in SHARED_ROWS[name][1]
    )


def shared_closer(name: str) -> str:
    """The close of family *name*'s table, read with its shared rows."""
    return closer_of(_table(name))


def shared_texts(name: str) -> tuple[str, ...]:
    """What family *name*'s shared rows are read with and as, in printed
    order: the rules a direct read of the family carries, then the family's
    passages of :data:`SHARED_FAMILY_TEXTS`, its table's head, the rows and
    the table's close where the table prints them."""
    head, rows = shared_rows(name)
    out = [t for t, _ in item_context(name)]
    found = 0
    for t in texts_at((PART, A_Z, name)):
        if t.startswith("<table>"):
            out += [head, *rows, shared_closer(name)]
        elif t.startswith(SHARED_FAMILY_TEXTS[name]):
            out.append(t)
            found += 1
    assert found == len(SHARED_FAMILY_TEXTS[name]), name
    return tuple(out)


def item_components(
    name: str,
) -> tuple[tuple[str, tuple[str, ...], tuple[tuple[str, str], ...]], ...]:
    """(component key, texts, context) of *name*'s components in printed
    order: the item's own key reads every context but a casting variant's. A
    family sharing rows with *Equipment* reads its table cut at those rows and
    its close, each read with those rows."""
    ts = tuple(texts_at((PART, A_Z, name)))
    if name in SHARED_ROWS:
        head, rows = shared_rows(name)
        closer = shared_closer(name)
        ts = tuple(
            p
            for t in ts
            for p in (cut(t, head, *rows, closer) if t.startswith("<table>") else (t,))
        )
    context = item_context(name)
    if name not in CASTING_VARIANTS:
        return ((slug(name), ts, context),)
    variant, n = CASTING_VARIANTS[name]
    starts = [i for i, t in enumerate(ts) if re.match(rf"(\*\*|_){variant}\b", t)]
    assert len(starts) == 1, name
    i = starts[0]
    cast = tuple(c for c in context if c[0] == CAST_FROM_ITEMS)
    assert cast and re.search(r"\bcast\b", " ".join(ts[i : i + n]))
    parts = [
        (slug(name), ts[:i], tuple(c for c in context if c[0] != CAST_FROM_ITEMS)),
        (slug(variant), ts[i : i + n], cast),
    ]
    if ts[i + n :]:
        # The next leaf opens the next variant, so the variant's leaves end.
        assert re.match(r"(\*\*|_)[A-Z]", ts[i + n]), name
        parts.append((f"{slug(name)}_after_{slug(variant)}", ts[i + n :], ()))
    return tuple(parts)


#: The accepted *Equipment* rules every item requiring attunement is read
#: with: what attunement is, attuning in a Short Rest, the three-item limit and
#: ending it. *Magic Item Rules* points at them ("Rules for identifying,
#: attuning to, and using magic items appear in 'Equipment'"). Read in place,
#: from the accepted batch owning them; identifying, wearing and wielding, and
#: multiple or paired items are reached through that pointer, not bound.
ATTUNEMENT_RULES = tuple(
    ("equipment.magic_items", k)
    for k in (
        "attunement",
        "attune_during_a_short_rest",
        "no_more_than_three_items",
        "ending_attunement",
    )
)
ATTUNED = tuple(
    n for n in ITEM_NAMES if "Requires Attunement" in texts_at((PART, A_Z, n))[1]
)
assert len(ATTUNED) == 140
CROSS_READS = {(item_key(n), slug(n)): ATTUNEMENT_RULES for n in ATTUNED}


# ---------------------------------------------------------------------------
# Latitude
# ---------------------------------------------------------------------------
#: (entry, component key) -> the printed words by which the source explicitly
#: leaves an open ruling or outcome to whoever runs the game (policy: "The
#: source explicitly delegates the decision to the GM"). Read by meaning, not by
#: "you" or "GM": in an item "you" is its bearer, and "The GM chooses ... or
#: determines it randomly by rolling on the following table" chooses among
#: printed options (``NOT_LATITUDE``). A design procedure with printed steps --
#: *Sentient Magic Item Traits*, whose persona is made "much as you would create
#: an NPC, with these exceptions", each trait chosen or rolled on its table, and
#: *Special Purpose* -- is reducible, as the accepted toolbox's *Creating a
#: Background* is.
LATITUDE: dict[tuple[str, str], str] = {
    (
        "magic_item_categories",
        "potions",
    ): "At your discretion, a Dispel Magic spell or similar magic might end this lasting effect.",
    (
        "magic_item_rules",
        "magic_item_rules",
    ): "Use your discretion to decide whether a creature can wear an item not made for its anatomy.",
    # Whether items are traded at all is the runner's choice.
    (
        "magic_item_rarity",
        "magic_item_values_by_rarity",
    ): "If you allow characters to buy and sell magic items in your campaign",
    (
        "the_next_dawn",
        "the_next_dawn",
    ): "the GM determines when the item recharges.",
    (
        "time_and_cost",
        "time_and_cost",
    ): "the GM might allow more assistants.",
    (
        "sentient_magic_items",
        "sentient_magic_items",
    ): "The GM controls sentient magic items and their activated properties.",
    **{
        (item_entry(n), slug(n)): words
        for n, words in {
            "Bag of Beans": "Its sarcophagus contains treasure of the GM's choice.",
            "Bag of Devouring": "The GM determines the time and plane.",
            "Cubic Gate": "The other sides are linked to planes determined by the GM.",
            "Dragon Orb": "or something else the GM decides.",
            "Hat of Many Spells": "The GM determines where it leads.",
            "Iron Flask": "might already contain a creature chosen by the GM.",
            "Mysterious Deck": "A magic item (chosen by the GM) appears on your person.",
            "Pipes of the Sewers": "(as determined by the GM)",
            "Ring of Spell Storing": "levels of stored spells chosen by the GM.",
            "Vorpal Sword": "if the GM decides that the creature is too big for its head to be cut off",
            "Wand of Wonder": "An object of the GM's choice disappears into the Ethereal Plane.",
            "Well of Many Worlds": "the GM decides where it leads.",
        }.items()
    },
    (
        item_entry("Ioun Stone"),
        "reserve",
    ): "it contains 1d4 levels of stored spells chosen by the GM.",
}
#: (entry, component key) -> the printed words naming the GM that only choose
#: among the printed options or roll the printed table, and so are reducible;
#: and the one "if you allow" whose "you" is the item's bearer.
NOT_LATITUDE: dict[tuple[str, str], str] = {
    (item_entry(n), slug(n)): words
    for n, words in {
        "Ring of Mind Shielding": "Creatures can telepathically communicate with you only if you allow it.",
        "Ammunition of Slaying": "which the GM chooses or determines randomly by rolling on the table below",
        "Armor of Resistance": "The GM chooses the type or determines it randomly by rolling on the following table.",
        "Armor of Vulnerability": "The GM chooses the type or determines it randomly.",
        "Candle of Invocation": "chosen by the GM or determined by rolling on the following table.",
        "Carpet of Flying": "The GM chooses the size of a given carpet or determines it randomly",
        "Efreeti Bottle": "the GM rolls on the following table to determine what happens.",
        "Feather Token": "The GM chooses the kind of token or determines it randomly",
        "Horn of Valhalla": "The GM chooses the horn's type or determines it randomly",
        "Manual of Golems": "The GM chooses the type or determines it randomly",
        "Necklace of Prayer Beads": "The GM decides the type of each bead on the necklace or determines it randomly",
        "Potion of Resistance": "The GM chooses the type or determines it randomly",
        "Ring of Elemental Command": "The GM chooses or randomly determines the linked plane.",
        "Ring of Resistance": "which the GM chooses or determines randomly by rolling on the following table.",
        "Robe of Useful Items": "The GM chooses the patches or determines them randomly",
        "Sphere of Annihilation": "the GM determines randomly what happens using the following table.",
    }.items()
}
#: The words that name whoever runs the game or leave a ruling to them: every
#: component printing one is classified in exactly one of the two tables above.
DELEGATING = re.compile(
    r"\bGM\b|discretion|you can decide|you can allow|if you allow", re.IGNORECASE
)

#: Every LATITUDE and NOT_LATITUDE row a component consumed.
DELEGATED: set[tuple[str, str]] = set()
READ_AS_OPTIONS: set[tuple[str, str]] = set()


def reason(entry: str, key: str, texts: tuple[str, ...]) -> str:
    if (words := NOT_LATITUDE.get((entry, key))) is not None:
        assert any(words in t for t in texts), (entry, key)
        READ_AS_OPTIONS.add((entry, key))
        return NO_USE
    if (words := LATITUDE.get((entry, key))) is None:
        assert not any(DELEGATING.search(t) for t in texts), (entry, key)
        return NO_USE
    assert any(words in t for t in texts), (entry, key)
    DELEGATED.add((entry, key))
    return GM


# ---------------------------------------------------------------------------
# References
# ---------------------------------------------------------------------------
#: The accepted spell generator's Rules Glossary alternation, with the two
#: accepted entries magic items print that spells do not.
GLOSSARY_TERMS: tuple[tuple[str, str | None], ...] = (
    ("Damage Threshold", "damage_threshold"),
    ("Attunement", "attunement"),
    *SD.GLOSSARY_TERMS,  # type: ignore[attr-defined]
)
_TERMS = re.compile("|".join(rf"(?<![_\w*])(?:{p})\b" for p, _ in GLOSSARY_TERMS))


def _term_slug(printed: str) -> str | None:
    return next(s for p, s in GLOSSARY_TERMS if re.fullmatch(p, printed))


def eq(key: str) -> Target:
    return (EQUIPMENT, f"equipment.{key}")


#: Printed forms of an item that are not its exact heading, to that item: the
#: ``+N`` and weapon-type forms of the variant entries (the *Weapons* category
#: prints that a magic weapon may specify its type), and plurals or singulars.
VARIANTS = {
    "+1 Armor": "Armor, +1, +2, or +3",
    "+3 Ammunition": "Ammunition, +1, +2, or +3",
    "+3 Weapon": "Weapon, +1, +2, or +3",
    # The *Dragon Orb* prints "+3 _Weapon_": the italics hold only the noun.
    "Weapon": "Weapon, +1, +2, or +3",
    "+1 Lance": "Weapon, +1, +2, or +3",
    "+2 Longsword": "Weapon, +1, +2, or +3",
    "Ioun Stones": "Ioun Stone",
    "Rings of Djinni Summoning": "Ring of Djinni Summoning",
    "Beads of Force": "Bead of Force",
    "Glove of Missile Snaring": "Gloves of Missile Snaring",
}
assert set(VARIANTS.values()) <= set(ITEM_NAMES)
#: The two names this part shares with an accepted *Equipment* record, to one
#: destination each. *Equipment* sells the basic Potion of Healing (2d4 + 2),
#: which the *Potions of Healing* table prints as its first row by exactly that
#: name: an unqualified "Potion(s) of Healing" is that potion, whose row is its
#: own (``SHARED_ROWS``) and a member of the family. Magic Items never names the *Equipment*'s
#: cantrip/level 1 scroll subset: an unqualified "Spell Scroll(s)" is this
#: part's whole family, and the family naming itself is no reference.
SHARED: dict[str, Target] = {
    "Potion of Healing": eq("adventuring_gear.potion_of_healing"),
    "Potions of Healing": eq("adventuring_gear.potion_of_healing"),
    "Spell Scroll": (MAGIC_ITEMS, item_key("Spell Scroll")),
    "Spell Scrolls": (MAGIC_ITEMS, item_key("Spell Scroll")),
}
#: Plain-text equipment by the exact printed name (a regex where the bare word
#: would also match something else): each the accepted *Equipment* holds a
#: record for, to it; each it prices without a record of its own, unresolved,
#: rather than widened to the section that lists it.
ITEMS: tuple[tuple[str, str, Target], ...] = (
    ("Acid", r"(?<=vial of )Acid", eq("adventuring_gear.acid")),
    ("Ammunition", r"Ammunition(?= property)", eq("weapons.ammunition")),
    ("Finesse", r"Finesse(?= property)", eq("weapons.finesse")),
    ("Thrown", r"Thrown(?= property)", eq("weapons.thrown")),
    ("Arcane Focus", r"Arcane Focus", eq("adventuring_gear.arcane_focus")),
    ("Arrows", r"Arrows", eq("adventuring_gear.arrows")),
    ("Crowbar", r"Crowbar", eq("adventuring_gear.crowbar")),
    ("Dagger", r"Dagger", eq("weapons.dagger")),
    ("Holy Symbol", r"Holy Symbol", eq("adventuring_gear.holy_symbol")),
    ("Quarterstaff", r"Quarterstaff", eq("weapons.quarterstaff")),
    ("Rations", r"Rations", eq("adventuring_gear.rations")),
    # The *Cube of Force* table's "Shield" is the spell.
    ("Shield", r"(?<!<td>)Shield", eq("armor.shield")),
    ("Shortbow", r"Shortbow", eq("weapons.shortbow")),
    ("Spear", r"Spear", eq("weapons.spear")),
    ("Herbalism Kit", r"Herbalism Kit", eq("tools.herbalism_kit")),
    (
        "Calligrapher's Supplies",
        r"Calligrapher's Supplies",
        eq("tools.calligraphers_supplies"),
    ),
    *(
        (n, re.escape(n), (EQUIPMENT, UNRESOLVED_TARGET))
        for n in (
            "Alchemist's Fire",
            "Alchemist's Supplies",
            "Battleaxe",
            "Bolts",
            "Bullseye Lantern",
            "Caltrops",
            "Chain Mail",
            "Grappling Hook",
            "Jeweler's Tools",
            "Keelboat",
            "Leatherworker's Tools",
            "Longbow",
            "Longsword",
            "Mace",
            "Mirror",
            "Plate Armor",
            "Pole",
            "Rope",
            "Rowboat",
            "Sack",
            "Shortsword",
            "Smith's Tools",
            "Tinker's Tools",
            "Torch",
            "Weaver's Tools",
            "Woodcarver's Tools",
        )
    ),
    # Not a named variant ("Potion of Healing (greater)"), not the quoted
    # "Scribing Spell Scrolls" section.
    ("Potion of Healing", r"Potion of Healing(?! \()", SHARED["Potion of Healing"]),
    ("Potions of Healing", r"Potions of Healing", SHARED["Potions of Healing"]),
    ("Spell Scroll", r"Spell Scroll", SHARED["Spell Scroll"]),
    ("Spell Scrolls", r"(?<!Scribing )Spell Scrolls", SHARED["Spell Scrolls"]),
)
#: A plain name followed by "of" is an item's name ("Rope of Climbing").
_ITEMS = re.compile(
    "|".join(rf"\b(?P<i{i}>{p})\b(?! of\b)" for i, (_, p, _) in enumerate(ITEMS))
)
#: The *Magic Item Categories* table names example items plainly; plain item
#: names are no references (italics mark them), and none of its cells is one.
CATEGORIES_TABLE = "**Magic Item Categories**\n"
#: Every quoted pointer the part prints, by its printed name.
POINTERS: dict[str, Target] = {
    "Equipment": (EQUIPMENT, UNRESOLVED_TARGET),
    "Monsters": (MONSTERS, UNRESOLVED_TARGET),
    "Scribing Spell Scrolls": eq("scribing_spell_scrolls"),
    # Printed inside the record it points into.
    "Conflict": (MAGIC_ITEMS, section_key("Sentient Magic Items")),
}
#: A pointer its own sentence qualifies, by (the leaf's start, name): the
#: rules "for identifying, attuning to, and using magic items" are the accepted
#: *Equipment* section holding exactly those, not the whole chapter.
QUALIFIED = {
    (
        "Rules for identifying, attuning to, and using magic items appear in",
        "Equipment",
    ): eq("magic_items"),
}
#: Quoted words that point nowhere: speech, a command word, an option.
NOT_POINTERS = frozenset(
    {
        "you",
        "2",
        "pull",
        "reduce",
        "enlarge",
        "Swift defeat to my enemies",
        "Swift death to you who have wronged me",
    }
)
_QUOTED = re.compile(r'"(?P<n>[^"\n]+?)\.?"')
#: The creatures prose names in bold, all pointing at "Monsters" (the part's
#: "Unless the text states otherwise, the stat block is in 'Monsters'"), as
#: qualified against the PDF.
CREATURE_NAMES = frozenset(
    {
        "Berserker",
        "Camel",
        "Constrictor Snake",
        "Djinni",
        "Earth Elemental",
        "Efreeti",
        "Elephant",
        "Giant Constrictor Snake",
        "Giant Goat",
        "Giant Owl",
        "Griffon",
        "Knight",
        "Lion",
        "Mastiff",
        "Mule",
        "Nightmare",
        "Raven",
        "Riding Horse",
        "Roc",
        "Swarm of Bats",
        "Water Elemental",
    }
)
#: A bold run that covers only the end of the creature's printed name: the
#: *Figurine*'s "Giant **Goat**" is the Giant Goat, read by its whole name.
BOLD_PREFIXES = {"Goat": "Giant "}
#: Bold runs that are no creature: the part's own word for the type face.
BOLD_LABELS = frozenset({"bold"})
_NUMBER = re.compile(r"[\d–]+")
_ITALIC = re.compile(r"(?<![\w*])_(?P<n>[A-Z+][^_\n]*?)_(?!\w)")
#: Asterisk italics, used only inside table cells.
_STAR = re.compile(r"(?<![\w*\\])\*(?P<n>[A-Z][^*\n]*?)\*(?![\w*])")
_BOLD = re.compile(r"\*\*(?P<n>[^*]+?)\*\*")

#: Every name read, for the qualification check.
SEEN: set[str] = set()


def refs_of(
    item: str, own: str, texts: tuple[str, ...], *, stat_block: bool = False
) -> tuple[tuple[str, Target], ...]:
    """The references of one component of record *own*, printed in *item*
    (``""`` outside *Magic Items A-Z*)."""
    out: dict[tuple[str, Target], None] = {}
    terms: dict[str, str] = {}

    def add(text: str, target: Target) -> None:
        SEEN.add(text)
        if scoped(target)[1] != own:
            out.setdefault((text, target))

    def italic(name: str) -> None:
        if name in SHARED:
            add(name, SHARED[name])
        elif name in ITEM_NAMES or name in VARIANTS:
            add(name, (MAGIC_ITEMS, item_key(VARIANTS.get(name, name))))
        else:
            for n in name.split(", "):
                assert n in SD.SPELL_NAMES, (item, n)  # type: ignore[attr-defined]
                add(n, (SPELLS, spell_key(n)))

    for t in texts:
        if t.startswith("#"):
            continue
        if not stat_block and not TYPE_LINE.fullmatch(t):
            for m in (*_ITALIC.finditer(t), *_STAR.finditer(t)):
                name = m["n"]
                # A label: "_Using a Potion._", "_Absorption (Very Rare)_."
                if name.endswith((".", ":")) or (
                    m.start() == 0 and t[m.end() : m.end() + 1] == "."
                ):
                    continue
                italic(name)
            for m in _BOLD.finditer(t):
                name = m["n"]
                if (
                    m.start() == 0
                    or t[m.start() - 1] == "\n"
                    or name.endswith((".", ":"))
                    or _NUMBER.fullmatch(name)
                    or name in BOLD_LABELS
                ):
                    continue
                if (prefix := BOLD_PREFIXES.get(name)) is not None:
                    assert t[: m.start()].endswith(prefix), (item, name)
                    name = prefix + name
                if item in STAT_BLOCKS and name == STAT_BLOCKS[item][1]:
                    add(name, (MAGIC_ITEMS, creature_key(item)))
                    continue
                assert name in CREATURE_NAMES, (item, name)
                add(name, (MONSTERS, UNRESOLVED_TARGET))
            for m in _QUOTED.finditer(t):
                if m["n"] in NOT_POINTERS:
                    continue
                target = next(
                    (
                        v
                        for (lead, n), v in QUALIFIED.items()
                        if n == m["n"] and t.startswith(lead)
                    ),
                    POINTERS[m["n"]],
                )
                add(m["n"], target)
            if not t.startswith(CATEGORIES_TABLE):
                for m in _ITEMS.finditer(t):
                    assert m.lastgroup is not None
                    add(m.group(), ITEMS[int(m.lastgroup[1:])][2])
        for m in _TERMS.finditer(t):
            if (s := _term_slug(m.group())) is not None:
                terms.setdefault(s, m.group())
    for s, printed in terms.items():
        add(printed, s)
    return tuple(out)


def _spells(*printed: str) -> tuple[tuple[str, Target], ...]:
    # "Enlarge/ Reduce": the release breaks the name after its slash.
    return tuple((n, (SPELLS, spell_key(n.replace("/ ", "/")))) for n in printed)


def _creatures(*printed: str) -> tuple[tuple[str, Target], ...]:
    return tuple((n, (MONSTERS, UNRESOLVED_TARGET)) for n in printed)


def _cells(name: str, head: str = "") -> tuple[str, ...]:
    """The non-numeric cells of *name*'s tables (those after *head*)."""
    return tuple(
        c
        for t in texts_at((PART, A_Z, name))
        if "<table>" in t and t.startswith(head)
        for c in re.findall(r"<td>([^<]*)</td>", t)
        if not _NUMBER.fullmatch(c)
    )


#: The *Deck of Illusions* table's creatures ("Stat blocks for these creatures
#: (except the card drawer) appear in 'Monsters'").
_ILLUSIONS = tuple(c for c in _cells("Deck of Illusions") if c != "The card drawer")
assert len(_ILLUSIONS) == 32  # "32 depicting specific creatures"
#: The *Bag of Tricks* tables' creatures.
_TRICKS = _cells("Bag of Tricks")
assert len(_TRICKS) == 24


def _item(name: str) -> tuple[str, str]:
    return (item_entry(name), slug(name))


#: (entry, component key) -> the names an effect depends on that the source
#: prints plainly, with no italics or bold to find them by: the spells a table
#: or effect casts, to their accepted records, and the creatures it conjures,
#: rolls or turns you into, to "Monsters", unresolved -- no Monster or Animal
#: record is accepted, and none is authored here. Read by meaning: a name in
#: an example list, a category ("some other Undead"), a class, or inside a
#: longer name (*Gauntlets of Ogre Power*, *Apparatus of the Crab*, the "Mage"
#: of *Mage Armor*, the "Animals" of *Speak with Animals*) is none. Each is
#: asserted printed in its component's own texts.
PLAIN: dict[tuple[str, str], tuple[tuple[str, Target], ...]] = {
    ("magic_item_categories", "potions"): (
        ("Potion of Invisibility", (MAGIC_ITEMS, item_key("Potion of Invisibility"))),
        *_spells("Dispel Magic"),
        # "(see Poison in Gameplay Toolbox)"
        ("Poison", ("srd-5.2.1/gameplay-toolbox", "gameplay_toolbox.poison")),
    ),
    _item("Wand of Wonder"): (
        *_spells(
            "Darkness",
            "Faerie Fire",
            "Fireball",
            "Slow",
            "Stinking Cloud",
            "Gust of Wind",
            "Lightning Bolt",
            "Enlarge/ Reduce",
            "Invisibility",
            "Polymorph",
            "Greater Restoration",
        ),
        *_creatures(
            "Rhinoceros", "Elephant", "Rat", "Black Bear", "Giant Wasp", "Frog"
        ),
    ),
    _item("Dragon Orb"): _spells(
        "Cure Wounds", "Daylight", "Death Ward", "Detect Magic", "Scrying"
    ),
    _item("Necklace of Prayer Beads"): _spells(
        "Bless",
        "Cure Wounds",
        "Greater Restoration",
        "Shining Smite",
        "Guardian of Faith",
        "Wind Walk",
    ),
    _item("Efreeti Bottle"): _spells("Wish"),
    _item("Cube of Force"): _spells(
        "Mage Armor",
        "Shield",
        "Tiny Hut",
        "Private Sanctum",
        "Resilient Sphere",
        "Wall of Force",
    ),
    _item("Bag of Tricks"): _creatures(*_TRICKS),
    _item("Deck of Illusions"): _creatures(*_ILLUSIONS),
    # "a Riding Horse with a Riding Saddle": the saddle is gear, not a creature.
    _item("Robe of Useful Items"): _creatures("Riding Horse", "Mastiffs"),
    _item("Bag of Beans"): _creatures(
        "Treant", "Shrieker Fungi", "Bulette", "Mummy", "Mummy Lord"
    ),
    _item("Bowl of Commanding Water Elementals"): _creatures("Water Elemental"),
    _item("Brazier of Commanding Fire Elementals"): _creatures("Fire Elemental"),
    _item("Censer of Controlling Air Elementals"): _creatures("Air Elemental"),
    _item("Elemental Gem"): _creatures(
        "Air Elemental", "Water Elemental", "Fire Elemental", "Earth Elemental"
    ),
    _item("Manual of Golems"): _creatures(
        "Clay Golem", "Flesh Golem", "Iron Golem", "Stone Golem"
    ),
    _item("Pipes of the Sewers"): _creatures("Swarm of Rats"),
    _item("Cloak of the Bat"): _creatures("Bat"),
}
#: (entry, component key) -> a reading the patterns make that the source's
#: meaning does not: the *Wand of Wonder*'s "Darkness" is the spell it casts
#: (above), not the glossary's Darkness.
NOT_READ: dict[tuple[str, str], tuple[tuple[str, Target], ...]] = {
    _item("Wand of Wonder"): (("Darkness", "darkness"),),
}
#: Every PLAIN and NOT_READ row a component consumed.
PLAIN_READ: set[tuple[str, str]] = set()


def plain_refs(
    entry: str,
    key: str,
    texts: tuple[str, ...],
    refs: tuple[tuple[str, Target], ...],
) -> tuple[tuple[str, Target], ...]:
    """*refs* without the component's NOT_READ readings, then its PLAIN names."""
    drop = NOT_READ.get((entry, key), ())
    assert set(drop) <= set(refs), (entry, key)
    plain = PLAIN.get((entry, key), ())
    for text, _ in plain:
        assert any(re.search(rf"\b{re.escape(text)}\b", t) for t in texts), text
    if drop or plain:
        PLAIN_READ.add((entry, key))
    return tuple(dict.fromkeys((*(r for r in refs if r not in drop), *plain)))


# ---------------------------------------------------------------------------
# The chunk
# ---------------------------------------------------------------------------
class Chunk:
    """The literal review data of the packet, gathered in printed order."""

    def __init__(self) -> None:
        self.entries: list[tuple[str, str, RecordKind]] = []
        self.placements: dict[str, Placement] = {}
        self.clauses: list[tuple[str, str, tuple[str | None, ...], tuple[str, ...]]] = (
            []
        )
        self.components: list[EntryComponent] = []
        self.records: list[tuple[str, RecordKind, str]] = []
        self.members: list[tuple[str, str]] = []
        self.containers: dict[str, tuple[str, ...]] = {}
        self.leaves = 0

    def entry(
        self,
        slug_: str,
        key: str,
        kind: RecordKind,
        container: tuple[str, ...],
        heading: str,
        *,
        unit: ReviewUnitKind = ReviewUnitKind.SECTION,
        omit: tuple[tuple[str, ...], ...] = (),
    ) -> None:
        self.entries.append((slug_, container[-1], kind))
        self.placements[slug_] = Placement(key, container, heading, unit, omit)
        self.leaves += sum(
            1
            for p, _ in LEAVES
            if p[: len(container)] == container
            and not any(p[: len(o)] == o for o in omit)
        )

    def section(
        self,
        entry: str,
        key: str,
        texts: Iterable[str],
        item: str,
        context: tuple[tuple[str, str], ...] = (),
        borrowed: tuple[str, ...] = (),
    ) -> None:
        """A prose-bound component of the entry's own record, read after the
        *context* (text, printing entry) governing it; its reason and
        references are its own texts'. Of *texts*, the *borrowed* are rows
        another record owns, read here in place as context."""
        ts = tuple(texts)
        assert ts and set(borrowed) <= set(ts), (entry, key)
        self.clauses.append((entry, key, (None,), ts))
        own = self.placements[entry].record_key
        ctx = tuple(t for t, _ in context)
        mine = tuple(t for t in ts if t not in borrowed)
        self.components.append(
            EntryComponent(
                entry,
                key,
                P,
                reason(entry, key, ts),
                refs=plain_refs(entry, key, ts, refs_of(item, own, mine)),
                texts=(*ctx, *ts) if ctx or borrowed else (),
                context=(*ctx, *borrowed),
                context_from=context,
            )
        )

    def shared(self, entry: str, name: str) -> None:
        """The accepted *Equipment* record whose rows family *name* prints:
        declared a member of the family, its ``SHARED_COMPONENT`` owning the
        rows, read with what governs them as context -- the rules a direct
        read of the family carries, the family's own passages of
        :data:`SHARED_FAMILY_TEXTS` and the table's head and close
        (:func:`shared_texts`) -- so the rows read alone are the family's
        rows, whole."""
        record = SHARED_ROWS[name][0]
        rows = shared_rows(name)[1]
        texts = shared_texts(name)
        self.records.append((record, RecordKind.EQUIPMENT, entry))
        self.components.append(
            EntryComponent(
                entry,
                SHARED_COMPONENT,
                P,
                reason(entry, SHARED_COMPONENT, rows),
                refs=refs_of(name, record, rows),
                record=record,
                texts=texts,
                context=tuple(t for t in texts if t not in rows),
                context_from=item_context(name),
            )
        )

    def stat_block(self, entry: str, item: str, path: tuple[str, ...]) -> None:
        """The item's stat block: a creature record SCOPED_WITHIN the item,
        one prose component per printed container."""
        record = creature_key(item)
        self.records.append((record, RecordKind.CREATURE, entry))
        self.containers[record] = path
        groups = [(slug(path[-1]), tuple(texts_at(path)))] + [
            (slug(c), tuple(texts_at(path + (c,)))) for c in children(path)
        ]
        assert all(children(path + (c,)) == [] for c in children(path)), path
        for key, ts in groups:
            self.components.append(
                EntryComponent(
                    entry,
                    key,
                    P,
                    reason(entry, key, ts),
                    refs=refs_of(item, record, ts, stat_block=True),
                    record=record,
                    texts=ts,
                )
            )

    def batch(self) -> EntryBatch:
        return EntryBatch(
            origin=ORIGIN,
            proposal_origin=f"{ORIGIN} (CRD Issue 5d magic items; unaccepted)",
            unit_prefix="magic-items",
            parent=PARENT,
            entries=tuple(self.entries),
            expected_leaves=self.leaves,
            clauses=tuple(self.clauses),
            framing=(),
            components=tuple(self.components),
            supporting=(),
            record_references=(),
            placements=self.placements,
            members=tuple(self.members),
            records=tuple(self.records),
            record_containers=self.containers,
            # A stat block is contained by its item; a shared row is a member.
            scoped_records=tuple(self.containers),
            edges=(),
        )

    def record_keys(self) -> set[str]:
        return {p.record_key for p in self.placements.values()} | {
            k for k, _, _ in self.records
        }


def section_components(section: str) -> list[tuple[str, tuple[str, ...]]]:
    """(key, texts) of a section: its own prose, then each printed subheading
    below it, in printed order; a floated table is its own."""
    out: list[tuple[str, tuple[str, ...]]] = []
    for path in containers((PART, section)):
        if path[:2] == (PART, A_Z) and len(path) > 2:
            continue
        texts = texts_at(path)
        tables = [i for i, t in enumerate(texts) if FLOATED.match(t)]
        if tables:
            assert path == (PART, "Special Purpose"), path
            assert tables == list(range(len(texts) - 4, len(texts))), tables
            out.append((slug(path[-1]), tuple(texts[: tables[0]])))
            for i in tables:
                m = FLOATED.match(texts[i])
                assert m is not None
                out.append((slug(m["n"]), (texts[i],)))
            continue
        out.append((slug(path[-1]), tuple(texts)))
    return out


def magic_items_chunk() -> Chunk:
    chunk = Chunk()
    keys: dict[str, list[str]] = {}
    for section in SECTIONS:
        path = (PART, section)
        e = slug(section)
        members = [path + (n,) for n in ITEM_NAMES] if section == A_Z else []
        chunk.entry(
            e,
            section_record(section),
            RecordKind.GENERAL_RULE,
            path,
            f"## {section}",
            omit=tuple(members),
        )
        for key, texts in section_components(section):
            keys.setdefault(section_record(section), []).append(key)
            chunk.section(e, key, texts, "")
        for m in members:
            name = m[-1]
            me = item_entry(name)
            chunk.entry(
                me,
                item_key(name),
                RecordKind.MAGIC_ITEM,
                m,
                f"#### {name}",
                unit=ReviewUnitKind.ENTRY,
            )
            chunk.members.append((me, e))
            borrowed = shared_rows(name)[1] if name in SHARED_ROWS else ()
            for key, texts, context in item_components(name):
                chunk.section(me, key, texts, name, context, borrowed)
            if name in SHARED_ROWS:
                chunk.shared(me, name)
            for c in children(m):
                assert c == STAT_BLOCKS[name][0], (name, c)
                chunk.stat_block(me, name, m + (c,))
    assert all(len(ks) == len(set(ks)) for ks in keys.values()), keys
    return chunk


MAGIC_ITEMS_CHUNK = magic_items_chunk()
assert MAGIC_ITEMS_CHUNK.leaves == len(LEAVES) == 1332
assert CREATURE_NAMES <= SEEN and set(VARIANTS) <= SEEN and set(SHARED) <= SEEN
assert set(POINTERS) <= SEEN and {n for n, _, _ in ITEMS} <= SEEN
assert set(LATITUDE) == DELEGATED, set(LATITUDE) - DELEGATED
assert set(NOT_LATITUDE) == READ_AS_OPTIONS, set(NOT_LATITUDE) - READ_AS_OPTIONS
assert set(PLAIN) | set(NOT_READ) == PLAIN_READ, set(PLAIN) - PLAIN_READ


def batch() -> EntryBatch:
    return MAGIC_ITEMS_CHUNK.batch()


def build(session: Session) -> Built:
    """Derive the magic items proposal from the release *session* published,
    its attuned items reading the accepted *Equipment* attunement rules."""
    built = build_entry_batch(session, batch(), published_release_binding(session))
    return read_accepted(built, current().oracle.representation, CROSS_READS)


def unresolved(chunk: Chunk) -> list[tuple[str, str]]:
    """Printed pointers whose destination has no record yet, as (scope, text)."""
    return sorted(
        (scoped(t)[0], text)
        for c in chunk.components
        for text, t in c.refs
        if scoped(t)[1] == UNRESOLVED_TARGET
    )


def outside(chunk: Chunk) -> set[Target]:
    """Every resolved target this chunk names and does not itself hold."""
    return {
        t
        for c in chunk.components
        for _, t in c.refs
        if scoped(t)[1] not in chunk.record_keys() and scoped(t)[1] != UNRESOLVED_TARGET
    }


def expected_representation_findings(chunk: Chunk) -> list[str]:
    """What the packet alone cannot see: accepted targets and open pointers.

    One finding per component reference to an accepted record and one per
    unresolved pointer -- each accepted target is valid once the packet is
    read over the accepted oracle, which the composition check shows.
    """
    targets = outside(chunk)
    return sorted(
        [
            *(
                f"reference {scoped(t)[0]}:{text!r}: unknown target record {scoped(t)[1]}"
                for c in chunk.components
                for text, t in c.refs
                if t in targets
            ),
            *(
                f"reference {s}:{t!r}: unresolved reference"
                for s, t in unresolved(chunk)
            ),
            # The accepted rules the attuned items read: seen once composed.
            *accepted_read_findings(
                current().oracle.representation,
                CROSS_READS,
                {
                    (item_key(n), slug(n)): reason(
                        item_entry(n), slug(n), item_components(n)[0][1]
                    )
                    for n in ATTUNED
                },
            ),
        ]
    )


# ---------------------------------------------------------------------------
# Unrecorded resolution drafts for the same Owner packet
# ---------------------------------------------------------------------------
@cache
def current() -> AcceptedInputs:
    """The nineteen-batch chain this packet is composed over on the
    Monsters-corrected release, as the Owner's acceptance recorded it.

    Over the superseded release it was ``ORACLE_FILE`` at ``ORACLE_SHA256``,
    which ``issue-5d-magic-items-ACCEPT.py`` recorded (historical).
    """
    recording = _load("issue-5d-monsters-corrections-ACCEPT")
    inputs: AcceptedInputs = recording.owner_chain(  # type: ignore[attr-defined]
        recording.ACCEPTED_AT,  # type: ignore[attr-defined]
        through="gameplay-toolbox",
    )
    return inputs


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def draft_targets(
    prior: AcceptedInputs,
) -> tuple[
    list[tuple[str, str, str, str, tuple[str, ...]]], list[tuple[str, str, str]]
]:
    """(drafts, left): each accepted unresolved *Magic Items* pointer whose
    printed text is exactly one item's name, to that item, with the spans the
    oracle cites it from; and every other one, left unresolved as printed.
    """
    from afterworlds.ingestion.mechanical.representation import (
        ProvenanceTargetKind,
        reference_target_key,
    )

    rep = prior.oracle.representation
    cited: dict[tuple[str, ...], list[str]] = {}
    for claim in rep.provenance:
        if claim.target_kind is ProvenanceTargetKind.REFERENCE:
            cited.setdefault(claim.target_key, []).append(claim.span_id)
    resolved = {
        (r.from_record_key, r.from_component_key, r.source_text)
        for r in prior.oracle.reference_resolutions
    }
    drafts, left = [], []
    for ref in rep.references:
        if ref.scope_key != MAGIC_ITEMS or ref.target_record_key:
            continue
        where = (ref.from_record_key, ref.from_component_key, ref.source_text)
        assert where not in resolved, where
        if ref.source_text in ITEM_NAMES:
            spans = tuple(cited[reference_target_key(ref)])
            assert spans, where
            drafts.append((*where, item_key(ref.source_text), spans))
        else:
            left.append(where)
    return drafts, left


def draft_resolutions(
    binding: ReleaseBinding, prior: AcceptedInputs
) -> tuple[ReferenceResolution, ...]:
    drafts, _ = draft_targets(prior)
    out = tuple(
        ReferenceResolution(
            resolution_id=f"resolve-{_slug(record)}-{_slug(component) or 'record'}-{_slug(text)}-magic-items-1",
            from_record_key=record,
            from_component_key=component,
            source_text=text,
            scope_key=MAGIC_ITEMS,
            target_record_key=target,
            release_binding=binding,
            provenance_span_ids=spans,
        )
        for record, component, text, target, spans in drafts
    )
    assert len({r.resolution_id for r in out}) == len(out)
    return out


def main(db: str) -> int:
    here = Path(__file__).resolve().parent
    from afterworlds.persistence.database import create_engine, create_session_factory

    engine = create_engine(f"sqlite:///{db}")
    with create_session_factory(engine)() as session:
        binding = published_release_binding(session)
    engine.dispose()
    prior = current()
    # Only the release the accepted authority is bound to.
    assert binding == prior.oracle.binding, binding
    emit(
        db,
        build,
        here / PROPOSAL_FILE,
        expected_representation_findings(MAGIC_ITEMS_CHUNK),
    )
    drafts = draft_resolutions(binding, prior=prior)
    payload = reference_resolution_payload(drafts)
    (here / DRAFTS_FILE).write_bytes(
        (json.dumps(payload, indent=2) + "\n").encode("utf-8")
    )
    print(f"drafts            {DRAFTS_FILE} ({len(drafts)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
