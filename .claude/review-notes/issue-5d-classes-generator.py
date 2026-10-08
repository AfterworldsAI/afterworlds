# ruff: noqa: E501  -- patterns are verbatim source text, kept whole to be greppable
"""Author the **classes** proposals: the whole *Classes* part, in two chunks.

REVIEW MATERIAL for CRD Issue 5d (#137) over the qualified 5c release
``ebdd9333-eeed-5df1-b3e1-8b97c2f65f80`` / ``5.2.1-corpus.574662e9-0ef``. It
emits two *unaccepted* ``5d-proposal-2`` artifacts and one file of unrecorded
resolution drafts. It accepts nothing, publishes nothing, writes nothing under
``oracles/`` and records no resolution.

Scope, 1174 leaves (pp28-82 of the official PDF): every leaf of *Classes*
except the part title ``# Classes``, which states no rule and belongs to no
class, as ``# Equipment`` belongs to no section. The qualified leaf texts are
``issue-5d-classes-source.py``; this file reads them from there.

Chunks. A catalogue of options (*Metamagic Options*, *Eldritch Invocation
Options*) prints identical whole leaves for several options ("_Cost: 1 Sorcery
Point_" eight times, "_Prerequisite: Level 2+ Warlock_" six, "_Repeatable._"
three), and a span is located exactly once per entry, so each option must be
its own entry. Membership is checked against printed containment: an option
entry in the same batch as its class would have to be a member of the class,
not of its catalogue. So the two catalogues and their options are a second
chunk, ``class-option-catalogues``, where each option is a member of its
catalogue; the class reaches its catalogue through the printed pointer
("Metamagic Options", "Eldritch Invocation Options"), not a member edge.

Record grain (chunk ``classes``):

* each class is one ``class`` record reading its core traits table, *Becoming
  a ... / As a Level 1 Character*, its *Class Features* intro and progression
  table, and its *Spell List* intro and per-level spell tables;
* each class feature (``#### Level N: Name``) is a ``class_feature`` record,
  a ``CATALOGUE_MEMBER`` of its class, reading its heading (level and name)
  and its prose; a labelled option ("_Rage Damage._", "**Spell Slots.**",
  "**_Patient Defense._**") or a boxed sidebar starts a component of its own;
* *As a Multiclass Character* is its own entry, a ``character_advancement``
  record and a member of its class: its level-1 bullet prints inside the
  multiclass leaf, and a span is located once per entry;
* each included subclass is a ``class_feature`` record (there is no subclass
  kind) and a member of its class; its features are its own records;
* each feature record is located inside its own printed container, so
  *Level 7: Defensive Tactics*, which prints the same leaf as *Hunter's Prey*
  ("You gain one of the following feature options ..."), is a feature of the
  Hunter like any other, found once where each is printed.

Every record reads its own printed heading -- class, subclass, catalogue,
option, multiclass, as each feature reads ``Level N: Name`` -- in its first
component: the name, level or category a direct read and its section's read
are read under. Only a subclass's italic motto is excluded, as flavor.

Every component is prose-bound but one per class: the progression table is
``mixed``, its governing prose kept whole and its level-indexed entitlements
typed under the existing Decision 4 families (Canary 5): each feature the
Class Features column grants, as a ``ProgressionEntryFact`` naming its record;
each count column (Rages, Cantrips, Prepared Spells ...) as a
``ProgressionEntryFact`` with its ``quantity``; each spell-slot cell as a
``SpellSlotProgressionFact``. Proficiency Bonus is already the accepted
``play.proficiency`` bands, and a die, a damage bonus or a distance is no
``quantity``, so those columns stay in the table's prose.
``gamemaster_latitude`` is kept where the rule leaves the outcome to the GM
(Wild Shape's sources and worn equipment, a Paladin breaking their oath);
everything else is ``no_identified_structured_use``.

References, once per component (a glossary entry at its first name, any other
pointer once per printed text and target):

* each accepted Rules Glossary term the prose depends on (``GLOSSARY_TERMS``),
  never from a table, a heading, or an italic spell name;
* every spell a rule or table names, to the *Spells* catalogue, unresolved:
  the italic names in prose and the spell column of every spell table;
* each item, category or property a core traits table names, to the exact
  record that prices or defines it; a named item with no record of its own
  and a pointer to a whole part ("see Equipment", "see Playing the Game")
  stay unresolved, never widened to the section that lists them;
* each feat named by name or category, the *Character Creation* rules named,
  the class spell lists and class sections named, the subclass each class
  says is "detailed after", the two option catalogues, and the invocations an
  invocation requires;
* each creature a rule names, to *Animals* or *Monsters* as printed,
  unresolved. "any class's spell list" and "Spells" stay unresolved too.

Run: ``python issue-5d-classes-generator.py <published afterworlds.db>``
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from collections.abc import Iterable
from pathlib import Path

from sqlalchemy.orm import Session

from afterworlds.ingestion.mechanical.authoring import (
    Built,
    EntryBatch,
    EntryComponent,
    Placement,
    Target,
    build_entry_batch,
    emit,
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
from afterworlds.ingestion.mechanical.reference_resolution import (
    reference_resolution_payload,
)
from afterworlds.ingestion.mechanical.representation import (
    MechanicalFact,
    ProgressionEntryFact,
    RecordKind,
    SpellSlotProgressionFact,
)

ORIGIN = "issue-5d-classes-generator.py"
PROPOSAL_FILE = "issue-5d-classes-REGEN-574662e9-PROPOSAL.json"
OPTIONS_PROPOSAL_FILE = "issue-5d-class-option-catalogues-REGEN-574662e9-PROPOSAL.json"
DRAFTS_FILE = "issue-5d-classes-resolutions-REGEN-574662e9-DRAFTS.json"
#: Every record here is placed; the unplaced-entry default is never read.
PARENT = ("Rules Glossary", "Rules Definitions")
PART = "Classes"
CLASSES = "srd-5.2.1/classes"
SPELLS = "srd-5.2.1/spells"
EQUIPMENT = "srd-5.2.1/equipment"
FEATS = "srd-5.2.1/feats"
CHARACTER_CREATION = "srd-5.2.1/character-creation"
PLAY = "srd-5.2.1/playing-the-game"
ANIMALS = "srd-5.2.1/animals"
MONSTERS = "srd-5.2.1/monsters"
#: The target of a printed pointer whose destination has no record yet.
UNRESOLVED_TARGET = ""

GM = "gamemaster_latitude"
NO_USE = "no_identified_structured_use"
P = ComponentHandling.PROSE_BOUND
#: Passages that leave the outcome to the Game Master.
GM_PASSAGES = ("if the Game Master permits", "the GM decides", "talk to your GM")


def _source() -> tuple[tuple[tuple[str, ...], str], ...]:
    spec = importlib.util.spec_from_file_location(
        "issue_5d_classes_source",
        Path(__file__).with_name("issue-5d-classes-source.py"),
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return tuple(((PART, *p), t) for p, t in module.LEAVES)


#: (full label path, exact text) of every scoped leaf, in printed order.
LEAVES = _source()

CLASS_NAMES = (
    "Barbarian",
    "Bard",
    "Cleric",
    "Druid",
    "Fighter",
    "Monk",
    "Paladin",
    "Ranger",
    "Rogue",
    "Sorcerer",
    "Warlock",
    "Wizard",
)
#: (class, catalogue label, catalogue slug): the two option catalogues.
CATALOGUES = (
    ("Sorcerer", "Metamagic Options", "metamagic_options"),
    ("Warlock", "Eldritch Invocation Options", "eldritch_invocation_options"),
)
#: The Hunter feature that prints another Hunter feature's leaf again.
DEFENSIVE_TACTICS = (
    PART,
    "Ranger",
    "Ranger Subclass: Hunter",
    "Level 7: Defensive Tactics",
)
#: The release appends the last sentence of *Channel Divinity* (p55) to the
#: *Breaking Your Oath* sidebar (p54) inside the one blockquote leaf. The PDF
#: prints it as Channel Divinity body text, so it is its own span there.
OATH_DC = (
    "If a Channel Divinity effect requires a saving throw, the DC equals the "
    "spell save DC from this class's Spellcasting feature."
)


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", re.sub(r"['’]", "", text.lower())).strip("_")


def cls_key(cls: str) -> str:
    return f"classes.{slug(cls)}"


def catalogue_key(cls: str) -> str:
    (label,) = [s for c, _, s in CATALOGUES if c == cls]
    return f"{cls_key(cls)}.{label}"


def texts_at(path: tuple[str, ...]) -> list[str]:
    """The leaves printed directly in *path*, not in a container below it."""
    return [t for p, t in LEAVES if p == path]


def children(path: tuple[str, ...]) -> list[str]:
    """The labels of *path*'s sub-containers, in printed order."""
    return list(
        dict.fromkeys(
            p[len(path)]
            for p, _ in LEAVES
            if p[: len(path)] == path and len(p) > len(path)
        )
    )


def leaves_below(path: tuple[str, ...]) -> list[str]:
    return [t for p, t in LEAVES if p[: len(path)] == path]


# ---------------------------------------------------------------------------
# Components: a feature's heading and prose, a label or a sidebar starts a new one
# ---------------------------------------------------------------------------
LABEL = re.compile(
    r"^(?:\*\*_(?P<a>[^_*]+?)\._\*\*|\*\*(?P<b>[^*]+?)\.\*\*|_(?P<c>[^_]+?)\._)\s"
)
SIDEBAR = re.compile(r"^> (?:#+ |\*\*)(?P<t>[^*\n]+)")


def split(first: str, texts: Iterable[str]) -> list[tuple[str, tuple[str, ...]]]:
    """(component key, texts) groups: *first* until the first label or sidebar."""
    groups: list[tuple[str, list[str]]] = [(first, [])]
    for t in texts:
        m = LABEL.match(t) or SIDEBAR.match(t)
        if m:
            groups.append((slug(next(g for g in m.groups() if g)), [t]))
        else:
            groups[-1][1].append(t)
    seen: dict[str, int] = {}
    out = []
    for key, ts in groups:
        if not ts:
            continue
        seen[key] = seen.get(key, 0) + 1
        out.append((key if seen[key] == 1 else f"{key}_{seen[key]}", tuple(ts)))
    return out


def reason(texts: Iterable[str]) -> str:
    return GM if any(g in t for t in texts for g in GM_PASSAGES) else NO_USE


# ---------------------------------------------------------------------------
# References
# ---------------------------------------------------------------------------
def eq(key: str) -> Target:
    return (EQUIPMENT, f"equipment.{key}")


def feat(key: str) -> Target:
    return (FEATS, f"feats.{key}")


def cc(key: str) -> Target:
    return (CHARACTER_CREATION, f"character_creation.{key}")


def cl(key: str) -> Target:
    return (CLASSES, key)


#: Rules Glossary terms, as one alternation in this order; ``None`` consumes a
#: name no entry defines ("Proficiency Bonus" is not "Proficiency").
GLOSSARY_TERMS: tuple[tuple[str, str | None], ...] = (
    ("Hit Point maximum", "hit_points"),
    ("Hit Point Dice", "hit_point_dice"),
    ("Temporary Hit Points", "temporary_hit_points"),
    ("Hit Points?", "hit_points"),
    ("Death Saving Throws?", "death_saving_throw"),
    ("Proficiency Bonus", None),
    ("Opportunity Attacks?", "opportunity_attacks"),
    ("Bonus Actions?", "bonus_action"),
    ("Reactions?", "reaction"),
    ("D20 Tests?", "d20_test"),
    ("Heroic Inspiration", "heroic_inspiration"),
    ("Armor Class", "armor_class"),
    ("Critical Hits?", "critical_hit"),
    ("Unarmed Strikes?", "unarmed_strike"),
    ("Spellcasting Focus", "spellcasting_focus"),
    ("Challenge Rating", "challenge_rating"),
    ("Advantage", "advantage"),
    ("Disadvantage", "disadvantage"),
    ("Bright Light", "bright_light"),
    ("Dim Light", "dim_light"),
    ("Darkness", "darkness"),
    ("Heavily Obscured", "heavily_obscured"),
    ("Lightly Obscured", "lightly_obscured"),
    ("Difficult Terrain", "difficult_terrain"),
    ("Long Rests?", "long_rest"),
    ("Short Rests?", "short_rest"),
    ("Concentration", "concentration"),
    ("Initiative", "initiative"),
    ("Immunity", "immunity"),
    ("Resistances?", "resistance"),
    ("Vulnerability", "vulnerability"),
    ("Exhaustion", "exhaustion"),
    ("Bloodied", "bloodied"),
    ("Blinded", "blinded"),
    ("Charmed", "charmed"),
    ("Deafened", "deafened"),
    ("Frightened", "frightened"),
    ("Grappled", "grappled"),
    ("Incapacitated", "incapacitated"),
    ("Invisible", "invisible"),
    ("Paralyzed", "paralyzed"),
    ("Petrified", "petrified"),
    ("Poisoned", "poisoned"),
    ("Prone", "prone"),
    ("Restrained", "restrained"),
    ("Stunned", "stunned"),
    ("Unconscious", "unconscious"),
    ("Blindsight", "blindsight"),
    ("Darkvision", "darkvision"),
    ("Tremorsense", "tremorsense"),
    ("Truesight", "truesight"),
    ("Telepathy", "telepathy"),
    ("Fly Speed", "fly_speed"),
    ("Swim Speed", "swim_speed"),
    ("Climb Speed", "climb_speed"),
    ("Burrow Speed", "burrow_speed"),
    ("Speed", "speed"),
    ("Emanation", "emanation"),
    ("Cube", "cube"),
    ("Sphere", "sphere"),
    ("Cylinder", "cylinder"),
    ("Cover", "cover"),
    ("Expertise", "expertise"),
    ("Rituals?", "ritual"),
    ("[Cc]antrips?", "cantrip"),
    ("ability checks?", "ability_check"),
    ("attack rolls?", "attack_roll"),
    ("saving throws?", "saving_throw"),
    ("damage rolls?", "damage_roll"),
    ("stat blocks?", "stat_block"),
    ("creature type", "creature_type"),
    ("unoccupied space", "unoccupied_space"),
    ("round down", "round_down"),
    *(
        (f"{a} action", slug(a))
        for a in (
            "Attack",
            "Dash",
            "Disengage",
            "Dodge",
            "Help",
            "Hide",
            "Influence",
            "Magic",
            "Ready",
            "Search",
            "Study",
            "Utilize",
        )
    ),
)
_TERMS = re.compile("|".join(rf"(?<![_\w*])(?:{p})\b" for p, _ in GLOSSARY_TERMS))


def _term_slug(printed: str) -> str | None:
    return next(s for p, s in GLOSSARY_TERMS if re.fullmatch(p, printed))


#: The spells prose names in italics, as qualified against the PDF.
SPELL_NAMES = frozenset(
    {
        "Alter Self",
        "Animal Friendship",
        "Arcane Eye",
        "Bless",
        "Burning Hands",
        "Charm Person",
        "Color Spray",
        "Contact Other Plane",
        "Cure Wounds",
        "Dancing Lights",
        "Detect Magic",
        "Disguise Self",
        "Dissonant Whispers",
        "Divine Smite",
        "Druidcraft",
        "Eldritch Blast",
        "Ensnaring Strike",
        "Faerie Fire",
        "False Life",
        "Feather Fall",
        "Find Familiar",
        "Find Steed",
        "Guidance",
        "Guiding Bolt",
        "Hallow",
        "Healing Word",
        "Heroism",
        "Hex",
        "Hunter's Mark",
        "Identify",
        "Invisibility",
        "Jump",
        "Levitate",
        "Light",
        "Mage Armor",
        "Mage Hand",
        "Magic Missile",
        "Power Word Heal",
        "Power Word Kill",
        "Prestidigitation",
        "Produce Flame",
        "Ray of Frost",
        "Sacred Flame",
        "Searing Smite",
        "Shield of Faith",
        "Shocking Grasp",
        "Silent Image",
        "Sleep",
        "Sorcerous Burst",
        "Speak with Animals",
        "Speak with Dead",
        "Starry Wisp",
        "Summon Dragon",
        "Thaumaturgy",
        "Thunderwave",
        "Vicious Mockery",
        "Water Breathing",
        "Wish",
    }
)
#: Italic names that are not spells: an item priced in *Equipment*, and the
#: Pact of the Tome's own book.
ITALIC_ITEMS: dict[str, Target | None] = {
    "Spell Scroll": eq("adventuring_gear.spell_scroll"),
    "Book of Shadows": None,
}
#: The creatures rules name in bold, as qualified against the PDF.
CREATURE_NAMES = frozenset(
    {
        "Rat",
        "Riding Horse",
        "Spider",
        "Wolf",
        "Imp",
        "Pseudodragon",
        "Quasit",
        "Skeleton",
        "Sphinx of Wonder",
        "Sprite",
        "Venomous Snake",
    }
)
SPELL: Target = (SPELLS, UNRESOLVED_TARGET)
_CLS = "|".join(sorted(CLASS_NAMES, key=len, reverse=True))

#: Core traits tables: each item, category or property to the exact record
#: that prices or defines it, once per target at its first printed name. A
#: named item the accepted *Equipment* holds no record for, and a pointer to a
#: whole part, stays unresolved -- never widened to the section that lists it,
#: as the accepted *Component Pouch* and "Playing the Game" pointers are --
#: once per printed name. "Starting Equipment" is a row label, not a pointer.
CORE_TRAITS: tuple[tuple[str, Target], ...] = (
    ("(?:Light|Medium|Heavy)[^<]*?armor", eq("armor.category")),
    ("Shields?", eq("armor.shield")),
    ("Daggers", eq("weapons.dagger")),
    ("Spear", eq("weapons.spear")),
    ("Shortbow", eq("weapons.shortbow")),
    ("Quarterstaff", eq("weapons.quarterstaff")),
    ("Arrows", eq("adventuring_gear.arrows")),
    ("Quiver", eq("adventuring_gear.quiver")),
    ("Holy Symbol", eq("adventuring_gear.holy_symbol")),
    ("Druidic Focus", eq("adventuring_gear.druidic_focus")),
    ("Arcane Focus", eq("adventuring_gear.arcane_focus")),
    ("Book", eq("adventuring_gear.book")),
    ("Robe", eq("adventuring_gear.robe")),
    ("Herbalism Kit", eq("tools.herbalism_kit")),
    ("Thieves' Tools", eq("tools.thieves_tools")),
    ("Artisan's Tools", eq("tools.artisans_tools")),
    ("GP", eq("coins")),
    ("Simple|Martial", eq("weapons.category")),
    ("Light property", eq("weapons.light")),
    ("Finesse", eq("weapons.finesse")),
    (
        "Studded Leather Armor|Leather Armor|Chain Shirt|Chain Mail"
        "|Greataxe|Handaxes|Mace|Sickle|Greatsword|Flail|Javelins|Scimitar"
        "|Shortsword|Longbow|Longsword"
        "|(?:Explorer|Entertainer|Priest|Dungeoneer|Burglar|Scholar)'s Pack"
        "|Spellbook|Musical Instruments?|(?<=see )Equipment",
        (EQUIPMENT, UNRESOLVED_TARGET),
    ),
    ("(?<=see )Playing the Game", (PLAY, UNRESOLVED_TARGET)),
)
_CORE = re.compile(
    "|".join(rf"\b(?P<c{i}>{p})\b" for i, (p, _) in enumerate(CORE_TRAITS))
)


def _core_target(m: re.Match[str]) -> Target:
    assert m.lastgroup is not None
    return CORE_TRAITS[int(m.lastgroup[1:])][1]


def _invocation(name: str) -> Target:
    return cl(f"{catalogue_key('Warlock')}.{slug(name)}")


def _subclass_target(cls: str, name: str) -> Target:
    return cl(f"{cls_key(cls)}.{slug(name)}")


#: Prose pointers: (pattern, target function of the match).
POINTERS: tuple[tuple[str, object], ...] = (
    ("Ability Score Improvement feat", lambda m: feat("ability_score_improvement")),
    ("(?:Epic Boon|Fighting Style|Origin) feat", lambda m: feat("feat_descriptions")),
    ("Boon of (?:the )?[A-Z][a-z]+(?: [A-Z][a-z]+)?", lambda m: feat(slug(m.group()))),
    ("Defense(?= is recommended)", lambda m: feat("defense")),
    ("multiclassing rules", lambda m: cc("multiclassing")),
    ("language tables", lambda m: cc("create_your_character")),
    ('(?<=")Spells(?=")', lambda m: SPELL),
    ('(?<=")Animals(?=")', lambda m: (ANIMALS, UNRESOLVED_TARGET)),
    ('(?<=")Monsters(?=")', lambda m: (MONSTERS, UNRESOLVED_TARGET)),
    ('(?<=")Metamagic Options(?=")', lambda m: cl(catalogue_key("Sorcerer"))),
    ('(?<=")Eldritch Invocation Options(?=")', lambda m: cl(catalogue_key("Warlock"))),
    (rf"(?:{_CLS}) class's section", lambda m: cl(cls_key(m.group().split()[0]))),
    ("any class's spell list", lambda m: (CLASSES, UNRESOLVED_TARGET)),
    (
        rf"(?:(?:{_CLS}), )*(?:(?:{_CLS}),? (?:and|or) )?(?:{_CLS}) spell lists?",
        # One reference takes one target, so a list of several classes stays
        # unresolved, as the accepted *Arcane Focus* and *Magic Initiate* do.
        lambda m: (
            (CLASSES, UNRESOLVED_TARGET)
            if len(re.findall(_CLS, m.group())) > 1
            else cl(cls_key(m.group().split()[0]))
        ),
    ),
    (
        "Pact of the (?:Blade|Chain|Tome)|Thirsting Blade",
        lambda m: _invocation(m.group()),
    ),
)
_POINTERS = re.compile(
    "|".join(rf"\b(?P<p{i}>{p})\b" for i, (p, _) in enumerate(POINTERS))
)
_SUBCLASS = re.compile(r"The (?P<n>.+?) subclass is detailed after")
_ITALIC = re.compile(r"(?<![\w*])_(?P<n>[A-Z][^_\n]*?)_(?!\w)")
_BOLD = re.compile(r"\*\*(?P<n>[^*]+?)\*\*")
_SPELL_COLUMN = re.compile(r"Spells?$")


def _pointer_targets(m: re.Match[str]) -> list[Target]:
    assert m.lastgroup is not None
    got = POINTERS[int(m.lastgroup[1:])][1](m)  # type: ignore[operator]
    return got if isinstance(got, list) else [got]


def _spell_cells(table: str) -> list[str]:
    heads = re.findall(r"<th>(.*?)</th>", table)
    cols = [i for i, h in enumerate(heads) if _SPELL_COLUMN.search(h)]
    names: list[str] = []
    for row in re.findall(r"<tr>(.*?)</tr>", table, re.S):
        cells = re.findall(r"<td>(.*?)</td>", row, re.S)
        for i in cols:
            if i < len(cells):
                names += [n for n in cells[i].split(", ") if n[:1].isalpha()]
    return names


#: Every italic spell name and bold creature name read, for the qualification check.
SEEN_SPELLS: set[str] = set()
SEEN_CREATURES: set[str] = set()


def refs_of(
    cls: str, own: str, texts: tuple[str, ...]
) -> tuple[tuple[str, Target], ...]:
    """The references of one component of record *own* in class *cls*."""
    out: dict[tuple[str, Target], None] = {}
    terms: dict[str, str] = {}
    core: dict[str, tuple[str, Target]] = {}

    def add(text: str, target: Target) -> None:
        if scoped(target)[1] != own:
            out.setdefault((text, target))

    for t in texts:
        if t.startswith("#"):
            continue
        if "<table>" in t:
            if t.startswith("**Core "):
                for m in _CORE.finditer(t):
                    target = _core_target(m)
                    # An unresolved target is keyed by name, so two items
                    # without records stay two references.
                    core.setdefault(target[1] or m.group(), (m.group(), target))
            else:
                for name in _spell_cells(t):
                    add(name, SPELL)
            continue
        for m in _POINTERS.finditer(t):
            for target in _pointer_targets(m):
                add(m.group(), target)
        if m := _SUBCLASS.search(t):
            add(m["n"], _subclass_target(cls, m["n"]))
        for m in _ITALIC.finditer(t):
            name = m["n"]
            # A label, a cost or prerequisite line, or the Special-column legend.
            if name.endswith(".") or ":" in name or len(name) == 1:
                continue
            if name in ITALIC_ITEMS:
                if (item := ITALIC_ITEMS[name]) is not None:
                    add(name, item)
                continue
            for n in (x.strip().rstrip(",") for x in name.split(", ")):
                if n:
                    SEEN_SPELLS.add(n)
                    add(n, SPELL)
        for m in _BOLD.finditer(t):
            if m.start() == 0 or t[: m.start()].endswith("> "):
                continue
            scope = ANIMALS if '"Animals"' in t else MONSTERS
            for n in (x.strip().rstrip(",") for x in m["n"].split(", ")):
                if n:
                    SEEN_CREATURES.add(n)
                    add(n, (scope, UNRESOLVED_TARGET))
        # A label's markup is not an italic name: "_Temporary Hit Points._"
        # cites Temporary Hit Points, not a bare "Hit Points".
        label = LABEL.match(t)
        plain = (
            f"{next(g for g in label.groups() if g)}. {t[label.end():]}" if label else t
        )
        for m in _TERMS.finditer(plain):
            if (s := _term_slug(m.group())) is not None:
                terms.setdefault(s, m.group())
    for printed, target in core.values():
        add(printed, target)
    for s, printed in terms.items():
        add(printed, s)
    return tuple(out)


# ---------------------------------------------------------------------------
# The two chunks
# ---------------------------------------------------------------------------
class Chunk:
    """The literal review data of one chunk, gathered in printed order."""

    def __init__(self) -> None:
        self.entries: list[tuple[str, str, RecordKind]] = []
        self.placements: dict[str, Placement] = {}
        self.clauses: list[tuple[str, str, tuple[str | None, ...], tuple[str, ...]]] = (
            []
        )
        self.components: list[EntryComponent] = []
        self.records: list[tuple[str, RecordKind, str]] = []
        self.members: list[tuple[str, str]] = []
        self.excluded: list[tuple[str, tuple[str, ...], str]] = []
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
        owned = {id(x) for o in omit for x in LEAVES if x[0][: len(o)] == o}
        self.leaves += sum(
            1
            for x in LEAVES
            if x[0][: len(container)] == container and id(x) not in owned
        )

    def section(
        self,
        entry: str,
        key: str,
        texts: Iterable[str],
        cls: str,
        facts: tuple[MechanicalFact, ...] = (),
    ) -> None:
        """A component of the entry's own record; MIXED when it carries *facts*."""
        ts = tuple(texts)
        if not ts:
            return
        self.clauses.append((entry, key, (None,), ts))
        own = self.placements[entry].record_key
        self.components.append(
            EntryComponent(
                entry,
                key,
                ComponentHandling.MIXED if facts else P,
                reason(ts),
                facts=facts,
                refs=refs_of(cls, own, ts),
            )
        )

    def record(
        self,
        entry: str,
        record: str,
        kind: RecordKind,
        groups: list[tuple[str, tuple[str, ...]]],
        cls: str,
        container: tuple[str, ...],
    ) -> None:
        """A record printed in *container* of *entry*: a CATALOGUE_MEMBER of
        the entry's record, its texts located in that container."""
        self.records.append((record, kind, entry))
        self.containers[record] = container
        for key, ts in groups:
            self.components.append(
                EntryComponent(
                    entry,
                    key,
                    P,
                    reason(ts),
                    refs=refs_of(cls, record, ts),
                    record=record,
                    texts=ts,
                )
            )

    def batch(self, unit_prefix: str, label: str) -> EntryBatch:
        return EntryBatch(
            origin=ORIGIN,
            proposal_origin=f"{ORIGIN} (CRD Issue 5d {label}; unaccepted)",
            unit_prefix=unit_prefix,
            parent=PARENT,
            entries=tuple(self.entries),
            expected_leaves=self.leaves,
            clauses=tuple(self.clauses),
            framing=(),
            components=tuple(self.components),
            supporting=(),
            record_references=(),
            placements=self.placements,
            excluded=tuple(self.excluded),
            members=tuple(self.members),
            records=tuple(self.records),
            record_containers=self.containers,
        )

    def record_keys(self) -> set[str]:
        return {p.record_key for p in self.placements.values()} | {
            k for k, _, _ in self.records
        }


def _features(
    chunk: Chunk, entry: str, host: str, container: tuple[str, ...], cls: str
) -> None:
    """Each ``Level N: Name`` below *container* as a class-feature record of *host*."""
    labels = children(container)
    names = [re.sub(r"^Level \d+: ", "", c) for c in labels]
    for label, name in zip(labels, names, strict=True):
        key = slug(name)
        if names.count(name) > 1:
            key = f"{key}_{re.match(r'Level (\d+)', label)[1]}"  # type: ignore[index]
        path = container + (label,)
        assert children(path) == [], path
        groups = split(key, texts_at(path))
        for i, (k, ts) in enumerate(groups):
            if ts[-1].endswith(f"\n> {OATH_DC}") and k == "breaking_your_oath":
                groups[i] = (k, (*ts[:-1], ts[-1].removesuffix(f"\n> {OATH_DC}")))
                groups[0] = (groups[0][0], (*groups[0][1], OATH_DC))
                break
        chunk.record(
            entry, f"{host}.{key}", RecordKind.CLASS_FEATURE, groups, cls, path
        )


#: Progression-table columns whose cells are a level-indexed count of an
#: entitlement: ADR-005d Decision 4's ``ProgressionEntryFact(quantity=)``. The
#: others stay prose in the same component: Proficiency Bonus is already the
#: accepted ``play.proficiency`` band facts (one authority), and a die, a
#: damage bonus or a distance is not a count a ``quantity`` can hold.
COUNT_COLUMNS = frozenset(
    {
        "Rages",
        "Weapon Mastery",
        "Channel Divinity",
        "Wild Shape",
        "Cantrips",
        "Prepared Spells",
        "Second Wind",
        "Focus Points",
        "Favored Enemy",
        "Sorcery Points",
        "Eldritch Invocations",
    }
)
PROSE_COLUMNS = frozenset(
    {
        "Level",
        "Proficiency Bonus",
        "Class Features",
        "Rage Damage",
        "Bardic Die",
        "Martial Arts",
        "Unarmored Movement",
        "Sneak Attack",
    }
)
#: A Class Features cell naming no feature record: the subclass's features at
#: that level, which its own records carry under their own levels.
SUBCLASS_FEATURE = "Subclass feature"
USES = {"one": 1, "two": 2, "three": 3}


def progression_facts(
    host: str, table: str, features: tuple[str, ...]
) -> tuple[MechanicalFact, ...]:
    """The typed entitlements of one class progression table.

    Each Class Features name is the feature record printed under the latest
    ``Level N: Name`` heading at or below that level (Ability Score Improvement
    at 8 is the level 4 record's "again at levels 8, 12 and 16"); each count
    column one ``ProgressionEntryFact`` per level; each slot cell one
    ``SpellSlotProgressionFact``. A dash grants nothing and states no fact.
    """
    heads = re.findall(r"<th>(.*?)</th>", table)
    labels = children(features)
    records: dict[str, list[tuple[int, str]]] = {}
    for label in labels:
        m = re.fullmatch(r"Level (\d+): (.+)", label)
        assert m, label
        name = m[2]
        key = slug(name)
        if sum(re.sub(r"^Level \d+: ", "", x) == name for x in labels) > 1:
            key = f"{key}_{m[1]}"
        records.setdefault(slug(name), []).append((int(m[1]), f"{host}.{key}"))
    facts: list[MechanicalFact] = []
    for row in re.findall(r"<tr>(.*?)</tr>", table, re.S):
        cells = re.findall(r"<td>(.*?)</td>", row, re.S)
        if not cells:
            continue
        assert len(cells) == len(heads), (heads, cells)
        level = int(cells[0])
        for head, cell in zip(heads, cells, strict=True):
            if head == "Class Features":
                for name in cell.split(", "):
                    if not name[:1].isalpha():
                        continue
                    # "Action Surge (two uses)" is a count of the feature; a
                    # "Mystic Arcanum (level 6 spell)" spell level is a second
                    # dimension the prose keeps, never a quantity.
                    m = re.fullmatch(r"(.+?)(?: \((one|two|three) uses?\))?", name)
                    assert m
                    name = re.sub(r" \(level \d spell\)$", "", m[1])
                    uses = USES.get(m[2] or "")
                    if name == SUBCLASS_FEATURE:
                        key = slug(name)
                    else:
                        key = max(r for r in records[slug(name)] if r[0] <= level)[1]
                    facts.append(ProgressionEntryFact(level, key, uses))
            elif head in COUNT_COLUMNS:
                if cell.isdigit():
                    facts.append(ProgressionEntryFact(level, slug(head), int(cell)))
            elif head.isdigit() or head == "Spell Slots":
                slot_level = int(head) if head.isdigit() else int(cells[-1])
                if cell.isdigit():
                    facts.append(SpellSlotProgressionFact(level, slot_level, int(cell)))
            else:
                assert head in PROSE_COLUMNS or head == "Slot Level", head
    return tuple(facts)


def classes_chunk() -> Chunk:
    chunk = Chunk()
    for cls in CLASS_NAMES:
        root = (PART, cls)
        e = slug(cls)
        host = cls_key(cls)
        subs = [c for c in children(root) if c.startswith(f"{cls} Subclass: ")]
        (becoming,) = [c for c in children(root) if c.startswith("Becoming a")]
        b = root + (becoming,)
        assert children(b) == ["As a Level 1 Character", "As a Multiclass Character"], b
        multiclass = b + ("As a Multiclass Character",)
        chunk.entry(
            e,
            host,
            RecordKind.CLASS,
            root,
            f"## {cls}",
            omit=(multiclass,)
            + tuple(root + (s,) for s in subs)
            + tuple(root + (label,) for c, label, _ in CATALOGUES if c == cls),
        )
        core = texts_at(root)
        assert core[0] == f"## {cls}", core[0]
        chunk.section(e, "core_traits", core, cls)
        chunk.section(
            e,
            "as_a_level_1_character",
            texts_at(b) + texts_at(b + ("As a Level 1 Character",)),
            cls,
        )
        # Its bullets reprint the level 1 bullet, so it cannot share the class's entry.
        m = f"{e}_as_a_multiclass_character"
        chunk.entry(
            m,
            f"{host}.as_a_multiclass_character",
            RecordKind.CHARACTER_ADVANCEMENT,
            multiclass,
            "#### As a Multiclass Character",
            unit=ReviewUnitKind.ENTRY,
        )
        chunk.members.append((m, e))
        chunk.section(m, "as_a_multiclass_character", texts_at(multiclass), cls)
        features = root + (f"{cls} Class Features",)
        *intro, table = texts_at(features)
        assert table.startswith(f"**{cls} Features**\n\n<table>"), table[:40]
        chunk.section(e, "class_features", intro, cls)
        chunk.section(
            e, "progression", (table,), cls, progression_facts(host, table, features)
        )
        _features(chunk, e, host, features, cls)
        spell_list = root + (f"{cls} Spell List",)
        if any(p[:3] == spell_list for p, _ in LEAVES):
            chunk.section(e, "spell_list", texts_at(spell_list), cls)
            for level in children(spell_list):
                key = (
                    "cantrips"
                    if level.startswith("Cantrips")
                    else slug(level.replace(f" {cls}", ""))
                )
                chunk.section(e, key, texts_at(spell_list + (level,)), cls)
        for sub in subs:
            name = sub.removeprefix(f"{cls} Subclass: ")
            path = root + (sub,)
            s = slug(name)
            skey = f"{host}.{s}"
            chunk.entry(s, skey, RecordKind.CLASS_FEATURE, path, f"### {sub}")
            chunk.members.append((s, e))
            h, motto, *intro = texts_at(path)
            assert (
                h == f"### {sub}" and motto.startswith("_") and motto.endswith("_")
            ), path
            chunk.excluded.append(
                (
                    s,
                    (motto,),
                    "subclass motto: names the subclass's theme and states no rule",
                )
            )
            chunk.section(s, s, (h, *intro), cls)
            _features(chunk, s, skey, path, cls)
    return chunk


def options_chunk() -> Chunk:
    chunk = Chunk()
    for cls, label, cslug in CATALOGUES:
        path = (PART, cls, label)
        host = catalogue_key(cls)
        options = children(path)
        chunk.entry(
            cslug,
            host,
            RecordKind.CLASS_FEATURE,
            path,
            f"### {label}",
            omit=tuple(path + (o,) for o in options),
        )
        chunk.section(cslug, cslug, texts_at(path), cls)
        for option in options:
            o = slug(option)
            chunk.entry(
                o,
                f"{host}.{o}",
                RecordKind.CLASS_FEATURE,
                path + (option,),
                f"#### {option}",
                unit=ReviewUnitKind.ENTRY,
            )
            chunk.members.append((o, cslug))
            body = texts_at(path + (option,))
            assert body[0] == f"#### {option}", body[0]
            for key, ts in split(o, body):
                chunk.section(o, key, ts, cls)
    return chunk


CLASSES_CHUNK = classes_chunk()
OPTIONS_CHUNK = options_chunk()
assert CLASSES_CHUNK.leaves + OPTIONS_CHUNK.leaves == len(LEAVES) == 1174
assert not CLASSES_CHUNK.record_keys() & OPTIONS_CHUNK.record_keys()
assert [(c.record, c.key) for c in CLASSES_CHUNK.components if OATH_DC in c.texts] == [
    ("classes.cleric.channel_divinity", "channel_divinity"),
    ("classes.paladin.channel_divinity", "channel_divinity"),
]
assert CLASSES_CHUNK.containers["classes.ranger.hunter.defensive_tactics"] == (
    DEFENSIVE_TACTICS
)
assert SEEN_SPELLS == SPELL_NAMES, sorted(SEEN_SPELLS ^ SPELL_NAMES)
assert SEEN_CREATURES == CREATURE_NAMES, sorted(SEEN_CREATURES ^ CREATURE_NAMES)
assert {c.reason for ch in (CLASSES_CHUNK, OPTIONS_CHUNK) for c in ch.components} <= {
    GM,
    NO_USE,
}


def batch() -> EntryBatch:
    return CLASSES_CHUNK.batch("classes", "classes chunk")


def options_batch() -> EntryBatch:
    return OPTIONS_CHUNK.batch(
        "class-option-catalogues", "class option catalogues chunk"
    )


def build(session: Session) -> Built:
    """Derive the classes proposal from the release *session* published."""
    return build_entry_batch(session, batch(), published_release_binding(session))


def build_options(session: Session) -> Built:
    """Derive the class option catalogues proposal."""
    return build_entry_batch(
        session, options_batch(), published_release_binding(session)
    )


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
    """Accepted and other-chunk targets stay unknown to one chunk alone.

    One finding per component reference. ``unknown_target_findings`` keys a
    component by (entry, key), which merges two records' same-named components
    printed in one entry (Cleric's *Blessed Strikes* and *Improved Blessed
    Strikes* both have *Potent Spellcasting*), so it is not used here.
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
        ]
    )


# ---------------------------------------------------------------------------
# Unrecorded resolution drafts for the same Owner packet
# ---------------------------------------------------------------------------
#: The one accepted Classes citation a single record answers: the Elf's
#: Elven Lineage names the Wizard spell list, which ``classes.wizard`` reads.
DRAFTS: tuple[tuple[str, str, str, str, tuple[str, ...]], ...] = (
    (
        "character_origins.elf",
        "elven_lineage",
        "Wizard spell list",
        cls_key("Wizard"),
        ("b1be94cc-654b-5a8a-916b-b4140e35bbd6",),
    ),
)


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def draft_resolutions(binding: ReleaseBinding) -> tuple[ReferenceResolution, ...]:
    return tuple(
        ReferenceResolution(
            resolution_id=f"resolve-{_slug(record)}-{_slug(component) or 'record'}-{_slug(text)}-classes-1",
            from_record_key=record,
            from_component_key=component,
            source_text=text,
            scope_key=CLASSES,
            target_record_key=target,
            release_binding=binding,
            provenance_span_ids=spans,
        )
        for record, component, text, target, spans in DRAFTS
    )


def main(db: str) -> int:
    here = Path(__file__).resolve().parent
    emit(
        db, build, here / PROPOSAL_FILE, expected_representation_findings(CLASSES_CHUNK)
    )
    emit(
        db,
        build_options,
        here / OPTIONS_PROPOSAL_FILE,
        expected_representation_findings(OPTIONS_CHUNK),
    )
    from afterworlds.persistence.database import create_engine, create_session_factory

    engine = create_engine(f"sqlite:///{db}")
    with create_session_factory(engine)() as session:
        binding = published_release_binding(session)
    engine.dispose()
    payload = reference_resolution_payload(draft_resolutions(binding))
    (here / DRAFTS_FILE).write_bytes(
        (json.dumps(payload, indent=2) + "\n").encode("utf-8")
    )
    print(f"drafts            {DRAFTS_FILE} ({len(DRAFTS)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
