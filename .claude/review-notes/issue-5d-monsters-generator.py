# ruff: noqa: E501  -- patterns are verbatim source text, kept whole to be greppable
"""Author the **Monsters** proposal: the general rules and the whole A-Z
catalogue the SRD prints.

REVIEW MATERIAL for CRD Issue 5d (#137) over the Monsters-corrected private
release ``67c81736-15fd-5e82-8523-e84922f0a7c6`` / ``5.2.1-corpus.3fe24ff6-4e3``,
composed over the unaccepted twenty-batch replacement chain
``issue-5d-monsters-corrections-REPLACEMENT.py`` builds on it. It emits one *unaccepted* ``5d-proposal-2`` artifact and one file of unrecorded
resolution drafts. It accepts nothing, publishes nothing, writes nothing under
``oracles/`` and records no resolution.

Scope, 3139 leaves (pp254-344 of the official PDF): every leaf of the
*Monsters* part below its ``# Monsters`` heading and of the *Monsters A-Z* part
below its ``# Monsters A–Z`` heading; both part headings stay with the other
part headings (shared coverage is deferred). *Animals* is the next part and is
not authored here. None was accepted before. The qualified leaf texts are
``issue-5d-monsters-source.py``; this file reads them from there.

Record grain:

* *Stat Block Overview* is one ``general_rule`` record,
  ``monsters.stat_block_overview``, one component. *Parts of a Stat Block* is
  one ``general_rule`` record, ``monsters.parts_of_a_stat_block``, one
  component per printed container in printed order; the *Running a Monster*
  sidebar the release prints inside *Resistances and Vulnerabilities* is its
  own component there, in its release position;
* each of the 177 ``##`` groups *Monsters A-Z* prints is a ``general_rule``
  record ``monsters.<group>`` reading only its heading (the accepted *Spell
  Descriptions* precedent), and each of the 235 ``###`` stat blocks is a
  ``creature`` record ``monsters.<group>.<block>`` (the accepted *Equipment*
  nesting) and a ``CATALOGUE_MEMBER`` of its group, in printed order. A
  creature has one prose component per printed container: its own leaves
  (heading, type line, combat highlights, ability table, details) keyed by its
  own slug, then *Traits*, *Actions*, *Bonus Actions*, *Reactions* and
  *Legendary Actions* where printed, each with its ``####`` heading, so every
  repeated heading stays with its own stat block.

Every component is prose-bound: the ``Creature*`` fact families of the
representation have no consumer, so no typed use is invented (ADR-005d
Decision 4). A component whose text explicitly leaves an open ruling or
outcome to whoever runs the game is ``gamemaster_latitude`` (``LATITUDE``); one
that names the GM choosing among printed options, or a rule that leaves only a
printed either/or, states reducible meaning (``NOT_LATITUDE``), as does every
other component: ``no_identified_structured_use``.

References, once per component: each accepted Rules Glossary term the prose
depends on; every spell named in italics, and each one a stat block depends on
by its plain name (``PLAIN_SPELLS``), to its accepted record; every creature
named in bold, to its stat block here (a creature naming itself is no
reference); every item of a *Gear* entry, to its accepted *Equipment* record
where one exists and unresolved otherwise; every quoted chapter pointer
unresolved unless its own sentence names exactly one accepted record
(``QUALIFIED``).

Governing context: a creature's component also reads, ``CONTEXTUAL`` and in
source order, the exact *Parts of a Stat Block* spans that govern it -- the
Alignment, Initiative, Hit Points and Ability Scores rules and the *Running a
Monster* sidebar for every stat block, and the size-option, class-tag
Attunement, Gear, Languages and Telepathy rules where its entry prints them;
the section rule of each container; the ammunition rule where it attacks with
an ammunition weapon; the notation rules its own text uses (attack, saving
throw, damage, Multiattack, X/Day, Recharge); and the spellcasting rules where
it casts a spell.
Each span stays owned (``PRIMARY``) by its rules component, so an override or
disable of that owner suppresses it on the creature, and a catalogue reading
does not repeat it.

Run: ``python issue-5d-monsters-generator.py <published afterworlds.db>``
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
from afterworlds.ingestion.mechanical.oracle import AcceptedInputs
from afterworlds.ingestion.mechanical.reference_resolution import (
    reference_resolution_payload,
)
from afterworlds.ingestion.mechanical.representation import RecordKind

ORIGIN = "issue-5d-monsters-generator.py"
PROPOSAL_FILE = "issue-5d-monsters-PROPOSAL.json"
DRAFTS_FILE = "issue-5d-monsters-resolutions-DRAFTS.json"
#: Every record here is placed; the unplaced-entry default is never read.
PARENT = ("Rules Glossary", "Rules Definitions")
RULES = "Monsters"
A_Z = "Monsters A–Z"
MONSTERS = "srd-5.2.1/monsters"
SPELLS = "srd-5.2.1/spells"
EQUIPMENT = "srd-5.2.1/equipment"
PLAY = "srd-5.2.1/playing-the-game"
GLOSSARY = "srd-5.2.1/rules-glossary"
CHARACTER_CREATION = "srd-5.2.1/character-creation"
TOOLBOX = "srd-5.2.1/gameplay-toolbox"
#: The target of a printed pointer whose destination has no record yet.
UNRESOLVED_TARGET = ""

GM = "gamemaster_latitude"
NO_USE = "no_identified_structured_use"
P = ComponentHandling.PROSE_BOUND


def _load(name: str) -> object:
    spec = importlib.util.spec_from_file_location(
        name.replace("-", "_"), Path(__file__).with_name(f"{name}.py")
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclasses resolve their own module
    spec.loader.exec_module(module)
    return module


#: (full label path, exact text) of every scoped leaf, in printed order.
LEAVES: tuple[tuple[tuple[str, ...], str], ...] = _load("issue-5d-monsters-source").LEAVES  # type: ignore[attr-defined]
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


assert tuple(children((RULES,))) == ("Stat Block Overview", "Parts of a Stat Block")
PARTS = (RULES, "Parts of a Stat Block")
#: The groups *Monsters A-Z* prints, and each group's stat blocks.
GROUPS = tuple(children((A_Z,)))
BLOCKS = tuple((g, b) for g in GROUPS for b in children((A_Z, g)))
assert len(GROUPS) == 177 and len(BLOCKS) == 235
#: The printed containers of a stat block below its own leaves.
BLOCK_PARTS = ("Traits", "Actions", "Bonus Actions", "Reactions", "Legendary Actions")
TYPE_LINE = re.compile(r"_[^_\n]+_")
for _g, _b in BLOCKS:
    _path = (A_Z, _g, _b)
    _h, _type, *_ = texts_at(_path)
    assert _h == f"### {_b}" and TYPE_LINE.fullmatch(_type), _path
    assert texts_at((A_Z, _g)) == [f"## {_g}"], _g
    assert [c for c in BLOCK_PARTS if c in children(_path)] == children(_path), _path
    for _c in children(_path):
        assert not children((*_path, _c)) and texts_at((*_path, _c))[0] == f"#### {_c}"
    # Every text is located whole within its own creature: none repeats there.
    _own = [t for p, t in LEAVES if p[:3] == _path]
    assert len(_own) == len(set(_own)), _path


def group_key(group: str) -> str:
    return f"monsters.{slug(group)}"


def creature_key(group: str, block: str) -> str:
    return f"monsters.{slug(group)}.{slug(block)}"


def creature_entry(group: str, block: str) -> str:
    return f"{slug(group)}.{slug(block)}"


#: Each stat block by its printed name: every name is printed once.
BLOCK_KEY = {b: creature_key(g, b) for g, b in BLOCKS}
assert len(BLOCK_KEY) == len(BLOCKS)
RULE_ENTRIES = ("stat_block_overview", "parts_of_a_stat_block")
assert not {slug(g) for g in GROUPS} & set(RULE_ENTRIES)
assert len({slug(g) for g in GROUPS}) == len(GROUPS)
assert len({creature_key(g, b) for g, b in BLOCKS}) == len(BLOCKS)


# ---------------------------------------------------------------------------
# Governing context
# ---------------------------------------------------------------------------
def _rule(path: tuple[str, ...], start: str) -> str:
    (text,) = [t for t in texts_at((*PARTS, *path)) if t.startswith(start)]
    return text


RULES_ENTRY = "parts_of_a_stat_block"
SIZE_OPTIONS = _rule(("Size",), "A monster is Tiny")
#: The alignment a stat block prints is a default roleplaying suggestion; the
#: leaf also prints the rule's own latitude, which its owner component states.
ALIGNMENT = _rule(("Alignment",), "The alignment specified")
INITIATIVE = (
    _rule(("Initiative",), "The Initiative entry"),
    _rule(("Initiative",), "If you don't want to roll"),
)
HIT_POINTS = _rule(("Hit Points",), "A monster's Hit Points are presented")
ABILITY_SCORES = _rule(("Ability Scores",), "Every monster has six")
GEAR = tuple(t for t in texts_at((*PARTS, "Gear")) if not t.startswith("#"))
assert len(GEAR) == 3
#: A class tag after the creature type makes the monster a member of that
#: class for Attunement purposes; the *Equipping* leaf that says so.
CLASS_TAG_RULE = _rule(
    ("Gear", "Equipping a Monster with Other Items"), "Beware of giving"
)
CLASS_TAG = re.compile(
    r"\((?:Barbarian|Bard|Cleric|Druid|Fighter|Monk|Paladin|Ranger|Rogue|Sorcerer|Warlock|Wizard)\)"
)
AMMUNITION = _rule(("Gear", "Ammunition and Ranged Attacks"), "A monster that requires")
#: An attack with a weapon that fires ammunition, by its printed label.
AMMUNITION_WEAPON = re.compile(
    r"\*\*_(?:Longbow|Shortbow|Light Crossbow|Heavy Crossbow|Hand Crossbow|Pistol)[ .]"
)
#: The sidebar's combat usage instructions govern how every monster is run to
#: act in accordance with the Challenge Rating its stat block prints.
RUNNING = _rule(("Resistances and Vulnerabilities",), "> **Running a Monster**")
LANGUAGES = _rule(("Languages",), "This entry lists languages")
TELEPATHY = _rule(("Languages", "Telepathy"), "Telepathy is a magical ability")
#: The section rule each printed container of a stat block reads.
CONTAINER_RULES = {
    "Traits": (_rule(("Traits",), "A monster's traits"),),
    "Actions": (_rule(("Actions",), "A monster can take the actions"),),
    "Bonus Actions": (_rule(("Bonus Action",), "If a monster has Bonus Action"),),
    "Reactions": (_rule(("Reactions",), "If the monster has Reaction"),),
    "Legendary Actions": (
        _rule(("Legendary Actions",), "If the monster has Legendary Action"),
        _rule(("Legendary Actions",), "The monster has a limited number"),
    ),
}
_NOTE = ("Actions",)
#: The notation rules a container's own text uses, by the printed notation.
#: Not read: the *Hit Dice by Size* table and the Constitution rule (a stat
#: block prints its own Hit Point Dice) and the Experience Points rules
#: (awarding XP is not the creature's).
NOTATIONS: tuple[tuple[re.Pattern[str], tuple[str, ...]], ...] = (
    (
        re.compile(r"Attack Roll:_"),
        (
            _rule((*_NOTE, "Attack Notation"), "The entry for a monster's attack"),
            _rule((*_NOTE, "Attack Notation"), "**_Hit._**"),
        ),
    ),
    (re.compile(r"_Miss:_"), (_rule((*_NOTE, "Attack Notation"), "**_Miss._**"),)),
    (
        re.compile(r"_Hit or Miss:_"),
        (_rule((*_NOTE, "Attack Notation"), "**_Hit or Miss._**"),),
    ),
    (
        re.compile(r"Saving Throw:_"),
        (_rule((*_NOTE, "Saving Throw Effect Notation"), "If an effect forces"),),
    ),
    (
        re.compile(r"Half damage only"),
        (_rule((*_NOTE, "Saving Throw Effect Notation"), '"Half damage only"'),),
    ),
    (
        re.compile(r"\b\d+ \(\d+d\d+[^)]*\) (?:[A-Z][a-z]+ )?damage"),
        (_rule((*_NOTE, "Damage Notation"), "A stat block usually provides"),),
    ),
    (
        re.compile(r"Multiattack"),
        (_rule((*_NOTE, "Multiattack"), "Some creatures can make"),),
    ),
    (re.compile(r"\d/Day"), (_rule(("Limited Usage",), "**X/Day.**"),)),
    (re.compile(r"Recharge \d"), (_rule(("Limited Usage",), "**Recharge X–Y.**"),)),
    (
        re.compile(r"Recharge after a Short or Long Rest"),
        (_rule(("Limited Usage",), "**Recharge after a Short or Long Rest.**"),),
    ),
)
#: The spellcasting rules, read by every component in which the creature casts
#: a spell, whether or not the spell's name is italic: its lowest level, "self
#: only" restrictions, components and casting times of 1 minute or more.
SPELLCASTING = tuple(
    t for t in texts_at((*PARTS, "Actions", "Spellcasting")) if not t.startswith("#")
)
assert len(SPELLCASTING) == 4


def _context(chosen: set[str]) -> tuple[tuple[str, str], ...]:
    """(text, printing entry) of *chosen*, in source order."""
    return tuple((t, RULES_ENTRY) for p, t in LEAVES if p[:2] == PARTS and t in chosen)


def header_context(texts: tuple[str, ...]) -> tuple[tuple[str, str], ...]:
    """The rules a stat block's own leaves invoke."""
    joined = "\n".join(texts)
    chosen = {ALIGNMENT, *INITIATIVE, HIT_POINTS, ABILITY_SCORES, RUNNING}
    if re.match(r"_\w+ or \w+ ", texts[1]):
        chosen.add(SIZE_OPTIONS)
    if CLASS_TAG.search(texts[1]):
        chosen.add(CLASS_TAG_RULE)
    if "**Gear**" in joined:
        chosen |= set(GEAR)
    if re.search(r"\*\*Languages\*\* None|understands", joined, re.IGNORECASE):
        chosen.add(LANGUAGES)
    if "telepathy" in joined:
        chosen.add(TELEPATHY)
    return _context(chosen)


def part_context(
    part: str, texts: tuple[str, ...], casts: bool
) -> tuple[tuple[str, str], ...]:
    """The rules a stat block's printed container *part* invokes."""
    joined = "\n".join(texts)
    chosen = set(CONTAINER_RULES[part])
    for pattern, rules in NOTATIONS:
        if pattern.search(joined):
            chosen |= set(rules)
    if AMMUNITION_WEAPON.search(joined):
        chosen.add(AMMUNITION)
    if casts:
        chosen |= set(SPELLCASTING)
    return _context(chosen)


# ---------------------------------------------------------------------------
# Latitude
# ---------------------------------------------------------------------------
#: (entry, component key) -> the printed words by which the source explicitly
#: leaves an open ruling or outcome to whoever runs the game. The *Commoner*'s
#: skill is an open choice: no list of options is printed.
LATITUDE: dict[tuple[str, str], str] = {
    (
        RULES_ENTRY,
        "alignment",
    ): "Change a monster's alignment to suit your storytelling needs.",
    (
        RULES_ENTRY,
        "equipping_a_monster_with_other_items",
    ): "You decide how much of a monster's equipment is recoverable",
    (
        creature_entry("Aboleth", "Aboleth"),
        "traits",
    ): "another location chosen by the GM.",
    (creature_entry("Commoner", "Commoner"), "traits"): "one skill of the GM's choice",
}
#: (entry, component key) -> the printed words naming the GM or "you" that only
#: choose among printed options, or say who controls a printed outcome, and so
#: are reducible.
NOT_LATITUDE: dict[tuple[str, str], str] = {
    (RULES_ENTRY, "size"): "you choose the creature's size from those options.",
    (
        RULES_ENTRY,
        "damage_notation",
    ): "You decide whether to use the number or the die expression in parentheses; don't use both.",
    (
        creature_entry("Half-Dragon", "Half-Dragon"),
        "traits",
    ): "(GM's choice): Acid, Cold, Fire, Lightning, or Poison",
    **{
        (
            creature_entry(w, w),
            "actions",
        ): f"it instead becomes a **{w}** under the GM's control"
        for w in ("Werebear", "Wereboar", "Wererat", "Weretiger", "Werewolf")
    },
}
#: The words that name whoever runs the game or leave a ruling to them: every
#: component printing one is classified in exactly one of the two tables above.
DELEGATING = re.compile(
    r"\bGM\b|discretion|you can decide|you can allow|if you allow|you decide"
    r"|however you like|suit your|you choose",
    re.IGNORECASE,
)
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
#: The accepted magic items generator's Rules Glossary alternation.
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


#: Every item a *Gear* entry prints, by its printed name without its count:
#: each the accepted *Equipment* holds a record for, to it; each other one
#: unresolved, rather than widened to the section that lists it.
GEAR_ITEMS: dict[str, Target] = {
    "Club": eq("weapons.club"),
    "Daggers": eq("weapons.dagger"),
    "Light Hammers": eq("weapons.light_hammer"),
    "Spear": eq("weapons.spear"),
    "Spears": eq("weapons.spear"),
    "Shortbow": eq("weapons.shortbow"),
    "Shield": eq("armor.shield"),
    "Hide Armor": eq("armor.hide_armor"),
    "Holy Symbol": eq("adventuring_gear.holy_symbol"),
    "Thieves' Tools": eq("tools.thieves_tools"),
    **{
        n: (EQUIPMENT, UNRESOLVED_TARGET)
        for n in (
            "Battleaxe",
            "Breastplate",
            "Chain Mail",
            "Chain Shirt",
            "Component Pouch",
            "Greataxe",
            "Greatclub",
            "Greatsword",
            "Half Plate Armor",
            "Hand Crossbow",
            "Handaxes",
            "Heavy Crossbow",
            "Javelins",
            "Leather Armor",
            "Light Crossbow",
            "Longbow",
            "Longsword",
            "Mace",
            "Morningstar",
            "Pike",
            "Pistol",
            "Plate Armor",
            "Rapier",
            "Scimitar",
            "Shortsword",
            "Sickle",
            "Splint Armor",
            "Studded Leather Armor",
            "Wand",
            "Warhammer",
        )
    },
}
_GEAR = re.compile(r"\*\*Gear\*\* (?P<g>[^<\n]*)")
#: The stat-block labels a stat block prints in bold.
STAT_LABELS = frozenset(
    {
        "AC",
        "Initiative",
        "HP",
        "Speed",
        "Skills",
        "Resistances",
        "Vulnerabilities",
        "Immunities",
        "Gear",
        "Senses",
        "Languages",
        "CR",
    }
)
#: A bold creature named in the plural, to its stat block's name.
PLURALS = {"Black Puddings": "Black Pudding", "Ochre Jellies": "Ochre Jelly"}
#: Italic spell names the release prints otherwise than the spell's name: a
#: line-break hyphen the PDF prints inside *Longstrider* (the *Druid*).
SPELL_FORMS = {"Long-strider": "Longstrider"}
#: (entry, component key) -> spells a component depends on by a name the
#: release prints plain, not in italics. Every other plain spell name a stat
#: block prints is a speed (Fly), illumination (Bright Light, magical
#: Darkness), a glossary term (Darkvision), gear (Shield, Holy Symbol, Light
#: Crossbow), a feature label (Divine Aid, Dread Command, Sleep Breath, Web
#: Strand, Deathly Teleport), a creature's own action (the *Nalfeshnee*'s
#: Teleport) or a creature (Blink Dog).
PLAIN_SPELLS: dict[tuple[str, str], tuple[str, ...]] = {
    (creature_entry("Storm Giant", "Storm Giant"), "actions"): (
        "Detect Magic",
        "Light",
        "Control Weather",
    ),
    (creature_entry("Succubus", "Succubus"), "actions"): ("Dominate Person",),
    (creature_entry("Tarrasque", "Tarrasque"), "traits"): ("Magic Missile",),
}
#: Every quoted pointer the rules part prints, by its printed name.
POINTERS: dict[str, Target] = {
    "Playing the Game": (PLAY, UNRESOLVED_TARGET),
    "Rules Glossary": (GLOSSARY, UNRESOLVED_TARGET),
    "Character Creation": (CHARACTER_CREATION, UNRESOLVED_TARGET),
    "Equipment": (EQUIPMENT, UNRESOLVED_TARGET),
    "Gameplay Toolbox": (TOOLBOX, UNRESOLVED_TARGET),
    "Spells": (SPELLS, UNRESOLVED_TARGET),
}
#: A pointer its own sentence qualifies to exactly one accepted record, by
#: (the leaf's start, name). A sentence naming two destinations (ability
#: scores and saving throws; Speed and the special speeds; Passive Perception
#: and special senses; the Magic action and Concentration; kinds of attacks in
#: two chapters) stays unresolved, as does a pointer to a whole chapter.
QUALIFIED: dict[tuple[str, str], Target] = {
    ("**Actions.** The monster can take", "Playing the Game"): (PLAY, "play.actions"),
    ("A monster is Tiny", "Playing the Game"): (PLAY, "play.combat"),
    ('"Character Creation" describes the nine alignments', "Character Creation"): (
        CHARACTER_CREATION,
        "character_creation.create_your_character",
    ),
    ("A monster's Armor Class (AC)", "Playing the Game"): (PLAY, "play.d20_tests"),
    ("If you don't want to roll a monster's Initiative", "Playing the Game"): (
        PLAY,
        "play.combat",
    ),
    ("For more on Hit Points", "Playing the Game"): (PLAY, "play.damage_and_healing"),
    ("These entries list a monster's Resistances", "Playing the Game"): (
        PLAY,
        "play.damage_and_healing",
    ),
    ("This entry lists the monster's Immunities", "Playing the Game"): (
        PLAY,
        "play.damage_and_healing",
    ),
    # The Attunement "as noted in" *Equipment* is the *Magic Items* rule; the
    # leaf is its own component, apart from the whole-chapter pointer.
    ("Beware of giving a monster", "Equipment"): (EQUIPMENT, "equipment.magic_items"),
    ("Telepathy is a magical ability", "Rules Glossary"): "telepathy",
    ("Challenge Rating is defined", "Rules Glossary"): "challenge_rating",
    ("Challenge Rating is defined", "Gameplay Toolbox"): (
        TOOLBOX,
        "gameplay_toolbox.combat_encounters",
    ),
    ("A monster can take the actions", "Playing the Game"): (PLAY, "play.actions"),
    ("If a monster has Bonus Action options", "Playing the Game"): (
        PLAY,
        "play.actions",
    ),
    ("If the monster has Reaction options", "Playing the Game"): (PLAY, "play.actions"),
}
#: Quoted words that point nowhere: notations, a section name, an example.
NOT_POINTERS = frozenset(
    {
        "Hit:",
        "Miss:",
        "Hit or Miss:",
        "Half damage only",
        "Actions",
        "self only",
        "1/Day",
        "Recharge 5–6",
        "None",
    }
)
_QUOTED = re.compile(r'"(?P<n>[^"\n]+?)[.,]?"')
_NUMBER = re.compile(r"[\d–.]+")
_ITALIC = re.compile(r"(?<![\w*])_(?P<n>[A-Z+][^_\n]*?)_(?!\w)")
_BOLD = re.compile(r"\*\*(?P<n>[^*]+?)\*\*")

#: Every name read, for the qualification check.
SEEN: set[str] = set()
#: Every bold creature a stat block names itself by (no reference).
SELF_NAMED: set[tuple[str, str]] = set()


class Refs:
    """The references of one component of record *own*."""

    def __init__(self, own: str) -> None:
        self.own = own
        self.out: dict[tuple[str, Target], None] = {}
        self.terms: dict[str, str] = {}

    def add(self, text: str, target: Target) -> None:
        SEEN.add(text)
        if scoped(target)[1] != self.own:
            self.out.setdefault((text, target))

    def spells(self, t: str) -> bool:
        """Every italic spell name of *t*; whether it printed one."""
        found = False
        for m in _ITALIC.finditer(t):
            name = m["n"]
            # A label: "_Hit:_", "_Spell Components._", the Legendary uses.
            if name.endswith((".", ":")) or TYPE_LINE.fullmatch(t):
                continue
            for n in name.split(", "):
                n = n.rstrip(",")
                spell = SPELL_FORMS.get(n, n)
                assert spell in SD.SPELL_NAMES, (self.own, n)  # type: ignore[attr-defined]
                self.add(n, (SPELLS, spell_key(spell)))
                found = True
        return found

    def glossary(self, t: str) -> None:
        for m in _TERMS.finditer(t):
            if (s := _term_slug(m.group())) is not None:
                self.terms.setdefault(s, m.group())

    def done(self) -> tuple[tuple[str, Target], ...]:
        for s, printed in self.terms.items():
            self.add(printed, s)
        return tuple(self.out)


def creature_refs(
    own: str, texts: tuple[str, ...], plain: tuple[str, ...] = ()
) -> tuple[tuple[tuple[str, Target], ...], bool]:
    """(references, whether it names a spell) of one stat-block component of
    creature *own*, which also depends on the *plain* spell names."""
    refs = Refs(own)
    casts = bool(plain)
    for n in plain:
        assert n in SD.SPELL_NAMES, n  # type: ignore[attr-defined]
        assert any(re.search(rf"\b{n}\b(?! Crossbow)", t) for t in texts), n
        refs.add(n, (SPELLS, spell_key(n)))
    for t in texts:
        if t.startswith("#"):
            continue
        assert '"' not in t, (own, t)
        casts |= refs.spells(t)
        for m in _GEAR.finditer(t):
            for item in m["g"].split(", "):
                name = re.sub(r" \(\d+\)$", "", item.strip())
                refs.add(name, GEAR_ITEMS[name])
        for m in _BOLD.finditer(t):
            name = m["n"]
            if (
                name.startswith("_")
                or name in STAT_LABELS
                or name.endswith(":")
                or _NUMBER.fullmatch(name)
            ):
                continue
            target = (MONSTERS, BLOCK_KEY[PLURALS.get(name, name)])
            if target[1] == own:
                SELF_NAMED.add((own, name))
            refs.add(name, target)
        refs.glossary(t)
    return refs.done(), casts


def rules_refs(own: str, texts: tuple[str, ...]) -> tuple[tuple[str, Target], ...]:
    """The references of one rules component of record *own*."""
    refs = Refs(own)
    for t in texts:
        if t.startswith("#"):
            continue
        refs.spells(t)
        for m in _BOLD.finditer(t):
            name = m["n"]
            # A caption, a sidebar title or a label opening its line.
            line_start = m.start() == 0 or t[: m.start()].endswith(("\n", "> "))
            assert line_start or name.endswith((".", ":")), (own, name)
        for m in _QUOTED.finditer(t):
            if m["n"] in NOT_POINTERS:
                SEEN.add(m["n"])
                continue
            target = next(
                (
                    v
                    for (lead, n), v in QUALIFIED.items()
                    if n == m["n"] and t.startswith(lead)
                ),
                POINTERS[m["n"]],
            )
            refs.add(m["n"], target)
        refs.glossary(t)
    return refs.done()


def _casts_spells(texts: tuple[str, ...]) -> bool:
    return bool(re.search(r"\b(?:casts|to cast|can cast)\b", " ".join(texts)))


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
        self.members: list[tuple[str, str]] = []
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
        refs: tuple[tuple[str, Target], ...],
        context: tuple[tuple[str, str], ...] = (),
    ) -> None:
        """A prose-bound component of the entry's own record, read after the
        *context* (text, printing entry) governing it; its reason and
        references are its own texts'."""
        ts = tuple(texts)
        assert ts, (entry, key)
        self.clauses.append((entry, key, (None,), ts))
        ctx = tuple(t for t, _ in context)
        self.components.append(
            EntryComponent(
                entry,
                key,
                P,
                reason(entry, key, ts),
                refs=refs,
                texts=(*ctx, *ts) if ctx else (),
                context=ctx,
                context_from=context,
            )
        )

    def batch(self) -> EntryBatch:
        return EntryBatch(
            origin=ORIGIN,
            proposal_origin=f"{ORIGIN} (CRD Issue 5d monsters; unaccepted)",
            unit_prefix="monsters",
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
            edges=(),
        )

    def record_keys(self) -> set[str]:
        return {p.record_key for p in self.placements.values()}


#: The sidebar the release prints as the last leaf of *Resistances and
#: Vulnerabilities*: its own component, in its release position.
SIDEBAR = "> **Running a Monster**"


def rules_components() -> list[tuple[str, tuple[str, ...]]]:
    """(key, texts) of *Parts of a Stat Block*: each printed container in
    printed order, the sidebar its own, and the *Equipping* leaf on magic
    items and class tags its own, apart from the generic equipping leaf (the
    two cite "Equipment" differently)."""
    out: list[tuple[str, tuple[str, ...]]] = []
    for path in containers(PARTS):
        texts = tuple(texts_at(path))
        if texts[-1].startswith(SIDEBAR):
            assert path[-1] == "Resistances and Vulnerabilities"
            out += [(slug(path[-1]), texts[:-1]), ("running_a_monster", texts[-1:])]
            continue
        if CLASS_TAG_RULE in texts:
            assert len(texts) == 3 and texts[-1] == CLASS_TAG_RULE, path
            out += [
                (slug(path[-1]), texts[:-1]),
                ("magic_items_and_class_tags", texts[-1:]),
            ]
            continue
        out.append((slug(path[-1]), texts))
    assert len({k for k, _ in out}) == len(out)
    return out


#: Components that name a spell the creature does not cast -- a spell another
#: creature casts on it or its gear, one a trait is compared to, or one that
#: targets it (the *Tarrasque*'s reflection) -- and so do not read the
#: spellcasting rules.
NOT_CAST = frozenset(
    {
        (creature_entry("Black Pudding", "Black Pudding"), "traits"),
        (creature_entry("Black Pudding", "Black Pudding"), "actions"),
        (creature_entry("Chuul", "Chuul"), "traits"),
        (creature_entry("Gray Ooze", "Gray Ooze"), "traits"),
        (creature_entry("Gray Ooze", "Gray Ooze"), "actions"),
        (creature_entry("Guardian Naga", "Guardian Naga"), "traits"),
        (creature_entry("Lemure", "Lemure"), "traits"),
        (creature_entry("Rust Monster", "Rust Monster"), "actions"),
        (creature_entry("Spirit Naga", "Spirit Naga"), "traits"),
        (creature_entry("Tarrasque", "Tarrasque"), "traits"),
    }
)
#: Every component that names a spell, and every one that reads the
#: spellcasting rules.
NAMING: set[tuple[str, str]] = set()
CASTING: set[tuple[str, str]] = set()


def monsters_chunk() -> Chunk:
    chunk = Chunk()
    overview = (RULES, "Stat Block Overview")
    chunk.entry(
        "stat_block_overview",
        "monsters.stat_block_overview",
        RecordKind.GENERAL_RULE,
        overview,
        "## Stat Block Overview",
    )
    ts = tuple(texts_at(overview))
    chunk.section(
        "stat_block_overview",
        "stat_block_overview",
        ts,
        rules_refs("monsters.stat_block_overview", ts),
    )
    chunk.entry(
        RULES_ENTRY,
        "monsters.parts_of_a_stat_block",
        RecordKind.GENERAL_RULE,
        PARTS,
        "## Parts of a Stat Block",
    )
    for key, ts in rules_components():
        chunk.section(
            RULES_ENTRY, key, ts, rules_refs("monsters.parts_of_a_stat_block", ts)
        )
    for g in GROUPS:
        ge = slug(g)
        blocks = [(A_Z, g, b) for b in children((A_Z, g))]
        chunk.entry(
            ge,
            group_key(g),
            RecordKind.GENERAL_RULE,
            (A_Z, g),
            f"## {g}",
            omit=tuple(blocks),
        )
        chunk.section(ge, slug(g), (f"## {g}",), ())
        for path in blocks:
            b = path[-1]
            ce, own = creature_entry(g, b), creature_key(g, b)
            chunk.entry(
                ce,
                own,
                RecordKind.CREATURE,
                path,
                f"### {b}",
                unit=ReviewUnitKind.ENTRY,
            )
            chunk.members.append((ce, ge))
            ts = tuple(texts_at(path))
            # A header names a spell only as a condition (the *Archmage*'s
            # _Mind Blank_, the *Rakshasa*'s _Bless_): it casts nothing there.
            refs, _ = creature_refs(own, ts)
            chunk.section(ce, slug(b), ts, refs, header_context(ts))
            for part in children(path):
                ts = tuple(texts_at((*path, part)))
                at = (ce, slug(part))
                refs, names_spell = creature_refs(own, ts, PLAIN_SPELLS.get(at, ()))
                # Casting is what the text does, whether or not it names the
                # spell; a named spell it does not cast is an explicit exception.
                if at in NOT_CAST:
                    assert names_spell and not _casts_spells(ts), at
                else:
                    assert _casts_spells(ts) or not names_spell, at
                casts = at not in NOT_CAST and _casts_spells(ts)
                if names_spell:
                    NAMING.add(at)
                if casts:
                    CASTING.add(at)
                chunk.section(ce, slug(part), ts, refs, part_context(part, ts, casts))
    return chunk


MONSTERS_CHUNK = monsters_chunk()
assert MONSTERS_CHUNK.leaves == len(LEAVES) == 3139
assert set(LATITUDE) == DELEGATED, set(LATITUDE) - DELEGATED
assert set(NOT_LATITUDE) == READ_AS_OPTIONS, set(NOT_LATITUDE) - READ_AS_OPTIONS
assert set(GEAR_ITEMS) <= SEEN, set(GEAR_ITEMS) - SEEN
assert set(PLURALS) <= SEEN and set(SPELL_FORMS) <= SEEN
assert set(NOT_POINTERS) <= SEEN and set(POINTERS) <= SEEN
assert NOT_CAST <= NAMING and set(PLAIN_SPELLS) <= NAMING and not NOT_CAST & CASTING
# 103 components that name a spell they cast, and three that cast one printed
# plain (the *Storm Giant*, the *Succubus*) or chosen later (*Spell Storing*).
assert len(CASTING) == 106 and len(CASTING - NAMING) == 1, sorted(CASTING - NAMING)
assert {n for (_, n) in QUALIFIED} <= SEEN


def _readers(text: str) -> list[tuple[str, str]]:
    return [(c.entry, c.key) for c in MONSTERS_CHUNK.components if text in c.context]


assert len(_readers(CLASS_TAG_RULE)) == 7 and len(_readers(AMMUNITION)) == 19
assert len(_readers(ALIGNMENT)) == len(_readers(RUNNING)) == len(BLOCKS)
# Every intra-packet target is a record this packet emits.
assert all(
    scoped(t)[1] in MONSTERS_CHUNK.record_keys()
    for c in MONSTERS_CHUNK.components
    for _, t in c.refs
    if scoped(t)[0] == MONSTERS
)


def batch() -> EntryBatch:
    return MONSTERS_CHUNK.batch()


def build(session: Session) -> Built:
    """Derive the monsters proposal from the release *session* published."""
    return build_entry_batch(session, batch(), published_release_binding(session))


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
        ]
    )


# ---------------------------------------------------------------------------
# Unrecorded resolution drafts for the same Owner packet
# ---------------------------------------------------------------------------
def current() -> AcceptedInputs:
    """The twenty-batch replacement chain this packet composed over, as the
    Owner's acceptance recorded it, rebuilt from its recorded time."""
    return _load("issue-5d-monsters-corrections-ACCEPT").recorded()  # type: ignore[attr-defined,no-any-return]


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


_UNDEAD = ("spells.create_undead", "using_a_higher_level_spell_slot")
_BUDGET = ("gameplay_toolbox.combat_encounters", "step_3_spend_your_budget")
#: Accepted plural pointers, reviewed one by one, to the stat block their own
#: source names: *Create Undead*'s "See "Monsters" for these stat blocks", the
#: encounter examples' creatures at their stat blocks' XP (the *Druid* at 450
#: XP is the stat block, not the class), and *Bag of Beans*'s sprouting fungi.
#: A plural an *Animals* stat block prints (Giant Rats, Giant Wasps, Mastiffs)
#: stays unresolved.
PLURAL_DRAFTS: dict[tuple[str, str, str], str] = {
    (*_UNDEAD, "Ghasts"): "Ghast",
    (*_UNDEAD, "Ghouls"): "Ghoul",
    (*_UNDEAD, "Mummies"): "Mummy",
    (*_UNDEAD, "Wights"): "Wight",
    (*_BUDGET, "Skeletons"): "Skeleton",
    (*_BUDGET, "Druids"): "Druid",
    (*_BUDGET, "Adult Red Dragons"): "Adult Red Dragon",
    (*_BUDGET, "Fire Giants"): "Fire Giant",
    (*_BUDGET, "Stirges"): "Stirge",
    ("magic_items.bag_of_beans", "bag_of_beans", "Shrieker Fungi"): "Shrieker Fungus",
}


def draft_targets(
    prior: AcceptedInputs,
) -> tuple[
    list[tuple[str, str, str, str, tuple[str, ...]]], list[tuple[str, str, str]]
]:
    """(drafts, left): each accepted unresolved *Monsters* pointer whose
    printed text is exactly one stat block's name, or a reviewed plural of one
    (``PLURAL_DRAFTS``), to that creature, with the spans the oracle cites it
    from; and every other one, left unresolved as printed (a chapter pointer,
    a creature or plural *Animals* prints, a name the catalogue prints
    otherwise)."""
    from afterworlds.ingestion.mechanical.representation import (
        ProvenanceTargetKind,
        reference_target_key,
    )

    rep = prior.oracle.representation
    assert not {r.semantic_key for r in rep.records} & MONSTERS_CHUNK.record_keys()
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
        if ref.scope_key != MONSTERS or ref.target_record_key:
            continue
        where = (ref.from_record_key, ref.from_component_key, ref.source_text)
        assert where not in resolved, where
        name = PLURAL_DRAFTS.get(where, ref.source_text)
        if name in BLOCK_KEY:
            spans = tuple(cited[reference_target_key(ref)])
            assert spans, where
            drafts.append((*where, BLOCK_KEY[name], spans))
        else:
            left.append(where)
    assert set(PLURAL_DRAFTS) <= {d[:3] for d in drafts}
    return drafts, left


def draft_resolutions(
    binding: ReleaseBinding, prior: AcceptedInputs
) -> tuple[ReferenceResolution, ...]:
    drafts, _ = draft_targets(prior)
    out = tuple(
        ReferenceResolution(
            resolution_id=f"resolve-{_slug(record)}-{_slug(component) or 'record'}-{_slug(text)}-monsters-1",
            from_record_key=record,
            from_component_key=component,
            source_text=text,
            scope_key=MONSTERS,
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
    # Only the release the replacement chain is bound to.
    assert binding == prior.oracle.binding, binding
    emit(
        db,
        build,
        here / PROPOSAL_FILE,
        expected_representation_findings(MONSTERS_CHUNK),
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
