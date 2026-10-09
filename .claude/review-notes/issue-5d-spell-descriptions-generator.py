# ruff: noqa: E501  -- patterns are verbatim source text, kept whole to be greppable
"""Author the **spell descriptions** proposal: every spell the SRD prints.

REVIEW MATERIAL for CRD Issue 5d (#137) over the corrected 5c release
``ebdd9333-eeed-5df1-b3e1-8b97c2f65f80`` / ``5.2.1-corpus.574662e9-0ef``, whose
Level 2 class spell tables carry the Owner's correction. It
emits one *unaccepted* ``5d-proposal-2`` artifact and one file of unrecorded
resolution drafts. It accepts nothing, publishes nothing, writes nothing under
``oracles/`` and records no resolution.

Scope, 2036 leaves (pp107-175 of the official PDF): the *Spell Descriptions*
section of *Spells*, its ``## Spell Descriptions`` heading first. The general
spellcasting rules before it are accepted (``spells.casting_spells`` ...) and
are not reauthored. The qualified leaf texts are
``issue-5d-spell-descriptions-source.py``; this file reads them from there.

Record grain:

* ``spells.spell_descriptions`` is the section, a ``general_rule`` reading its
  heading, as ``feats.feat_descriptions`` is *Feat Descriptions*; each of the
  339 spells is a ``spell`` record and a ``CATALOGUE_MEMBER`` of it, in
  printed order;
* each spell's ``descriptor`` component reads its heading, its level line and
  its Casting Time / Range / Components / Duration lines and is ``mixed``: one
  ``SpellDescriptorFact`` (ADR-005d Decision 4) beside the governing prose,
  which keeps the material description, cost and consumption, the reaction or
  bonus-action trigger and any arm the contract cannot state (see
  ``UNTYPED``); a descriptor the release prints fused with the first body
  paragraph in one leaf is cut there, at the line break the PDF prints;
* the body is prose-bound: ``effect`` from the first paragraph, then
  ``using_a_higher_level_spell_slot`` and ``cantrip_upgrade`` where printed.
  Option labels, tables and their rows stay inside the component that prints
  them, in printed order. *Wish* is the Canary 1 shape: each printed effect is
  its own component, *Instant Health* ``mixed`` with
  ``HealingFact(restores_all_hit_points=True)``, the stress its own, and
  *Reshape Reality* keeps ``gamemaster_latitude``;
* each of the four stat blocks a spell prints (*Animated Object*,
  *Otherworldly Steed*, *Giant Insect*, *Draconic Spirit*) is a ``creature``
  record ``SCOPED_WITHIN`` its spell (Canary 4), prose-bound by printed
  container, and the spell's "uses the ... stat block" names it;
* each class a level line names is a ``SPELL_LIST_MEMBER`` edge from the
  accepted ``classes.<class>`` to the spell, cited on that line. The accepted
  class records are not changed; this packet only adds edges to them.

``gamemaster_latitude`` is kept where the text leaves the outcome to the GM;
everything else is ``no_identified_structured_use``. Saves, attacks, damage and
slot scaling stay prose: no code-owned use is identified for them here, and the
slot-level basis of scaling is a Known Unknown.

References, once per component: each accepted Rules Glossary term the prose
depends on; every spell named in italics, to its record in this packet; each
stat block a spell uses, to its scoped record; each creature named in bold, and
the "Monsters" and "Animals" part pointers, unresolved; the four items the
accepted *Equipment* prices by the printed name.

Run: ``python issue-5d-spell-descriptions-generator.py <published afterworlds.db>``
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
from afterworlds.ingestion.mechanical.representation import (
    ActionCost,
    DurationKind,
    HealingFact,
    MechanicalFact,
    RangeKind,
    RecordKind,
    RelationshipKind,
    SpellCastingTime,
    SpellComponents,
    SpellDescriptorFact,
    SpellDuration,
    SpellRange,
    SpellSchool,
    TimeUnit,
)

ORIGIN = "issue-5d-spell-descriptions-generator.py"
PROPOSAL_FILE = "issue-5d-spell-descriptions-PROPOSAL.json"
DRAFTS_FILE = "issue-5d-spell-descriptions-resolutions-DRAFTS.json"
#: Every record here is placed; the unplaced-entry default is never read.
PARENT = ("Rules Glossary", "Rules Definitions")
PART = "Spells"
SECTION = (PART, "Spell Descriptions")
SPELLS = "srd-5.2.1/spells"
EQUIPMENT = "srd-5.2.1/equipment"
ANIMALS = "srd-5.2.1/animals"
MONSTERS = "srd-5.2.1/monsters"
#: The target of a printed pointer whose destination has no record yet.
UNRESOLVED_TARGET = ""

GM = "gamemaster_latitude"
NO_USE = "no_identified_structured_use"
P = ComponentHandling.PROSE_BOUND
#: A passage naming the Game Master leaves that part of the outcome to them.
_GM = re.compile(r"\bGM\b")

#: The ``spells.*`` records the accepted *Spellcasting* section holds. No
#: spell's key may collide with one.
ACCEPTED_SPELLS_KEYS = frozenset(
    {
        "spells.attack_rolls",
        "spells.casting_spells",
        "spells.casting_time",
        "spells.combining_spell_effects",
        "spells.components",
        "spells.duration",
        "spells.effects",
        "spells.gaining_spells",
        "spells.range",
        "spells.saving_throws",
        "spells.targets",
    }
)
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


def _load(name: str) -> object:
    spec = importlib.util.spec_from_file_location(
        name.replace("-", "_"), Path(__file__).with_name(f"{name}.py")
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _source() -> tuple[tuple[tuple[str, ...], str], ...]:
    module = _load("issue-5d-spell-descriptions-source")
    return tuple(((PART, *p), t) for p, t in module.LEAVES)  # type: ignore[attr-defined]


#: (full label path, exact text) of every scoped leaf, in printed order.
LEAVES = _source()


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", re.sub(r"['’]", "", text.lower())).strip("_")


def spell_key(name: str) -> str:
    return f"spells.{slug(name)}"


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


SPELL_NAMES = tuple(children(SECTION))
assert len(SPELL_NAMES) == len(set(map(slug, SPELL_NAMES))) == 339
assert not {spell_key(n) for n in SPELL_NAMES} & ACCEPTED_SPELLS_KEYS

#: The stat block each spell prints, by spell: (creature label, the texts of
#: the spell that name it as the stat block the creature uses).
STAT_BLOCKS = {
    "Animate Objects": ("Animated Object", "Animated Object"),
    "Find Steed": ("Otherworldly Steed", "Otherworldly Steed"),
    "Giant Insect": ("Giant Insect", "Giant Insect"),
    "Summon Dragon": ("Draconic Spirit", "Draconic Spirit"),
}


def creature_key(spell: str) -> str:
    return f"{spell_key(spell)}.{slug(STAT_BLOCKS[spell][0])}"


# ---------------------------------------------------------------------------
# The descriptor
# ---------------------------------------------------------------------------
LEVEL = re.compile(
    r"_(?:Level (?P<level>\d) (?P<school>[A-Z][a-z]+)|(?P<cschool>[A-Z][a-z]+) Cantrip) \((?P<classes>[A-Za-z, ]+)\)_"
)
DESCRIPTOR = re.compile(
    r"\*\*Casting Time:\*\* (?P<ct>[^\n]+)\n\*\*Range:\*\* (?P<rg>[^\n]+)\n"
    r"\*\*Components?:\*\* (?P<co>[^\n]+)\n\*\*Duration:\*\* (?P<du>[^\n]+)"
)
UNITS = {
    "round": TimeUnit.ROUND,
    "minute": TimeUnit.MINUTE,
    "hour": TimeUnit.HOUR,
    "day": TimeUnit.DAY,
}
COSTS = {
    "Action": ActionCost.ACTION,
    "Bonus Action": ActionCost.BONUS_ACTION,
    "Reaction": ActionCost.REACTION,
}
#: Printed descriptor arms the existing contract cannot state without a value
#: the source does not print: the arm is left ``None`` and the printed line
#: governs. Each is a contract question for the Owner, not a guess.
UNTYPED = {
    # Two casting times, one per mode; SpellCastingTime states exactly one.
    ("casting_time", "Action (Overgrowth) or 8 hours (Enrichment)"),
    # RANGED states feet; a mile would be a conversion the line never prints.
    ("range", "1 mile"),
    ("range", "500 miles"),
    # UNTIL_DISPELLED would drop the trigger that also ends it.
    ("duration", "Until dispelled or triggered"),
    # A ceiling without Concentration: TIMED states a fixed length.
    ("duration", "Up to 8 hours"),
    ("duration", "Up to 1 hour"),
    ("duration", "Up to 1 minute"),
}


def _time(text: str) -> tuple[int, TimeUnit]:
    m = re.fullmatch(r"(\d+) (round|minute|hour|day)s?", text)
    assert m, text
    return int(m[1]), UNITS[m[2]]


def casting_time(text: str) -> tuple[SpellCastingTime | None, bool]:
    """The typed casting time and whether it may be cast as a Ritual."""
    if ("casting_time", text) in UNTYPED:
        return None, False
    ritual = text.endswith(" or Ritual")
    text = text.removesuffix(" or Ritual")
    # A trigger ("Reaction, which you take when ...") stays in the prose.
    head = text.split(", which you take ")[0]
    if head in COSTS:
        return SpellCastingTime(cost=COSTS[head]), ritual
    amount, unit = _time(head)
    return SpellCastingTime(amount=amount, unit=unit), ritual


def spell_range(text: str) -> SpellRange | None:
    if ("range", text) in UNTYPED:
        return None
    if m := re.fullmatch(r"(\d+) feet", text):
        return SpellRange(RangeKind.RANGED, int(m[1]))
    return SpellRange(RangeKind(text.lower()))


def components(text: str) -> SpellComponents:
    m = re.fullmatch(r"(?P<vsm>[VSM](?:, [VSM])*)(?: \((?P<material>.+)\))?", text)
    assert m, text
    letters = m["vsm"].split(", ")
    assert ("M" in letters) == (m["material"] is not None), text
    return SpellComponents(
        verbal="V" in letters,
        somatic="S" in letters,
        material="M" in letters,
        material_consumed="consumes" in (m["material"] or ""),
    )


def duration(text: str) -> SpellDuration | None:
    if ("duration", text) in UNTYPED:
        return None
    if text == "Instantaneous":
        return SpellDuration(DurationKind.INSTANTANEOUS)
    if text == "Until dispelled":
        return SpellDuration(DurationKind.UNTIL_DISPELLED)
    if text == "Special":
        return SpellDuration(DurationKind.SPECIAL)
    concentration = text.startswith("Concentration, up to ")
    amount, unit = _time(text.removeprefix("Concentration, up to "))
    return SpellDuration(DurationKind.TIMED, amount, unit, concentration)


def descriptor_fact(level_line: str, block: str) -> SpellDescriptorFact:
    lv = LEVEL.fullmatch(level_line)
    d = DESCRIPTOR.fullmatch(block)
    assert lv and d, (level_line, block)
    ct, ritual = casting_time(d["ct"])
    du = duration(d["du"])
    return SpellDescriptorFact(
        level=int(lv["level"] or 0),
        school=SpellSchool((lv["school"] or lv["cschool"]).lower()),
        ritual=ritual,
        concentration=d["du"].startswith("Concentration"),
        casting_time=ct,
        spell_range=spell_range(d["rg"]),
        components=components(d["co"]),
        duration=du,
    )


def spell_classes(level_line: str) -> tuple[str, ...]:
    m = LEVEL.fullmatch(level_line)
    assert m, level_line
    names = tuple(m["classes"].split(", "))
    assert set(names) <= set(CLASS_NAMES), names
    return names


def descriptor_texts(texts: list[str]) -> tuple[list[str], list[str]]:
    """(descriptor pieces, body texts) of one spell's direct leaves.

    The descriptor lines end at the Duration line. The release prints them as
    one leaf, as two (Casting Time and Range, then Components and Duration),
    or fused with the first body paragraph after a line break; the fused leaf
    is cut at that break, so each piece is exact source text.
    """
    pieces: list[str] = []
    rest = list(texts)
    while rest:
        t = rest.pop(0)
        if "**Duration:** " not in t:
            pieces.append(t)
            continue
        end = (
            t.index("\n", t.index("**Duration:** "))
            if "\n" in t[t.index("**Duration:** ") :]
            else len(t)
        )
        pieces.append(t[:end])
        if end < len(t):
            rest.insert(0, t[end + 1 :])
        break
    assert DESCRIPTOR.fullmatch("\n".join(pieces)), pieces
    return pieces, rest


# ---------------------------------------------------------------------------
# Components
# ---------------------------------------------------------------------------
#: The labels that end a spell's effect: slot scaling and cantrip scaling.
TRAILING = re.compile(r"^_(Using a Higher-Level Spell Slot|Cantrip Upgrade)\._ ")
FUSED_TRAILING = re.compile(
    r"\n(?=_(?:Using a Higher-Level Spell Slot|Cantrip Upgrade)\._ )"
)
#: *Wish*'s effects, each its own printed label.
WISH_LABEL = re.compile(r"^\*\*(?P<n>[A-Z][A-Za-z ]+)\.\*\* ")
WISH_STRESS = "The stress of casting _Wish_"


def body_groups(spell: str, texts: list[str]) -> list[tuple[str, tuple[str, ...]]]:
    """(component key, texts): the effect, then each trailing scaling label."""
    groups: list[tuple[str, list[str]]] = [("effect", [])]
    # A label printed after a line break inside one leaf (Giant Insect, Ice
    # Storm, Wall of Ice) opens its component there: the leaf is cut at that
    # break, as a fused descriptor leaf is, so each piece is exact source text.
    for t in (p for leaf in texts for p in FUSED_TRAILING.split(leaf)):
        if m := TRAILING.match(t):
            groups.append((slug(m[1]), [t]))
        elif spell == "Wish" and (m := WISH_LABEL.match(t)):
            groups.append((slug(m["n"]), [t]))
        elif spell == "Wish" and t.startswith(WISH_STRESS):
            groups.append(("stress", [t]))
        else:
            assert len(groups) == 1 or spell == "Wish", (spell, t[:60])
            groups[-1][1].append(t)
    keys = [k for k, _ in groups]
    assert len(keys) == len(set(keys)) and groups[0][1], (spell, keys)
    return [(k, tuple(ts)) for k, ts in groups]


def reason(texts: Iterable[str]) -> str:
    return GM if any(_GM.search(t) for t in texts) else NO_USE


# ---------------------------------------------------------------------------
# References
# ---------------------------------------------------------------------------
#: Rules Glossary terms, as one alternation in this order; ``None`` consumes a
#: name no entry defines ("Proficiency Bonus" is not "Proficiency"). The
#: Classes list, less nothing, plus the accepted entries spells print that
#: classes do not: Spell Attack, Cone, Line and Passive Perception.
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
    ("Passive Perception", "passive_perception"),
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
    ("Cone", "cone"),
    ("Line", "line"),
    ("Cover", "cover"),
    ("Expertise", "expertise"),
    ("Rituals?", "ritual"),
    ("[Cc]antrips?", "cantrip"),
    ("spell attacks?", "spell_attack"),
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


def eq(key: str) -> Target:
    return (EQUIPMENT, f"equipment.{key}")


#: Items the accepted *Equipment* prices, by the exact printed name. *Holy
#: Water* is priced in the release but holds no record of its own, so it
#: stays unresolved rather than widened to the section that lists it.
ITEMS: tuple[tuple[str, Target], ...] = (
    ("Holy Symbol", eq("adventuring_gear.holy_symbol")),
    ("Holy Water", (EQUIPMENT, UNRESOLVED_TARGET)),
    ("Artisan's Tools", eq("tools.artisans_tools")),
    ("Club", eq("weapons.club")),
    ("Quarterstaff", eq("weapons.quarterstaff")),
)
_ITEMS = re.compile(
    "|".join(rf"\b(?P<i{i}>{re.escape(n)})\b" for i, (n, _) in enumerate(ITEMS))
)
#: The creatures prose names in bold, all pointing at "Monsters", as qualified
#: against the PDF, and the one it names in plain text.
CREATURE_NAMES = frozenset(
    {
        "Awakened Shrub",
        "Awakened Tree",
        "Bat",
        "Cat",
        "Frog",
        "Hawk",
        "Lizard",
        "Octopus",
        "Owl",
        "Rat",
        "Raven",
        "Spider",
        "Weasel",
        "Ghasts",
        "Ghoul",
        "Ghouls",
        "Mummies",
        "Skeleton",
        "Wights",
        "Zombie",
    }
)
PLAIN_CREATURES = re.compile(r"(?<=uses the )Riding Horse(?= stat block)")
SPELL: Target = (SPELLS, UNRESOLVED_TARGET)
_POINTERS = re.compile(r'(?<=")(?P<n>Monsters|Animals)(?=[".])')
_ITALIC = re.compile(r"(?<![\w*])_(?P<n>[A-Z][^_\n]*?)_(?!\w)")
#: Asterisk italics, used only inside the two Prismatic tables' cells.
_STAR = re.compile(r"(?<![\w*])\*(?P<n>[A-Z][^*\n]*?)\*(?![\w*])")
_BOLD = re.compile(r"\*\*(?P<n>[^*]+?)\*\*")

#: Every italic spell name and bold creature name read, for the qualification check.
SEEN_SPELLS: set[str] = set()
SEEN_CREATURES: set[str] = set()


def refs_of(
    spell: str, own: str, texts: tuple[str, ...], *, stat_block: bool = False
) -> tuple[tuple[str, Target], ...]:
    """The references of one component of record *own*, printed in *spell*."""
    out: dict[tuple[str, Target], None] = {}
    terms: dict[str, str] = {}

    def add(text: str, target: Target) -> None:
        if scoped(target)[1] != own:
            out.setdefault((text, target))

    for t in texts:
        if t.startswith("#") or LEVEL.fullmatch(t):
            continue
        if not stat_block:
            for m in (*_ITALIC.finditer(t), *_STAR.finditer(t)):
                name = m["n"]
                # A label ("_Using a Higher-Level Spell Slot._", "*Failed Save:*").
                if name.endswith((".", ":")):
                    continue
                for n in name.split(", "):
                    assert n in SPELL_NAMES, (spell, n)
                    SEEN_SPELLS.add(n)
                    add(n, (SPELLS, spell_key(n)))
            for m in _BOLD.finditer(t):
                name = m["n"]
                if m.start() == 0 or name.endswith((".", ":")):
                    continue
                if spell in STAT_BLOCKS and name == STAT_BLOCKS[spell][1]:
                    add(name, (SPELLS, creature_key(spell)))
                    continue
                for n in name.split(", "):
                    SEEN_CREATURES.add(n)
                    add(n, (MONSTERS, UNRESOLVED_TARGET))
            if (
                spell in STAT_BLOCKS
                and f"uses the {STAT_BLOCKS[spell][1]} stat block" in t
            ):
                add(STAT_BLOCKS[spell][1], (SPELLS, creature_key(spell)))
            for m in PLAIN_CREATURES.finditer(t):
                SEEN_CREATURES.add(m.group())
                add(m.group(), (MONSTERS, UNRESOLVED_TARGET))
            for m in _POINTERS.finditer(t):
                add(
                    m["n"],
                    (ANIMALS if m["n"] == "Animals" else MONSTERS, UNRESOLVED_TARGET),
                )
            for m in _ITEMS.finditer(t):
                assert m.lastgroup is not None
                add(m.group(), ITEMS[int(m.lastgroup[1:])][1])
        # A label's markup is not a term: "_Cantrip Upgrade._" is no Cantrip.
        plain = TRAILING.sub("", t)
        for m in _TERMS.finditer(plain):
            if (s := _term_slug(m.group())) is not None:
                terms.setdefault(s, m.group())
    for s, printed in terms.items():
        add(printed, s)
    return tuple(out)


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
        self.edges: list[tuple[str, str, RelationshipKind, str, str]] = []
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
        spell: str,
        facts: tuple[MechanicalFact, ...] = (),
    ) -> None:
        """A component of the entry's own record; MIXED when it carries *facts*."""
        ts = tuple(texts)
        self.clauses.append((entry, key, (None,), ts))
        own = self.placements[entry].record_key
        self.components.append(
            EntryComponent(
                entry,
                key,
                ComponentHandling.MIXED if facts else P,
                reason(ts),
                facts=facts,
                refs=refs_of(spell, own, ts),
            )
        )

    def stat_block(self, entry: str, spell: str, path: tuple[str, ...]) -> None:
        """The spell's stat block: a creature record SCOPED_WITHIN the spell,
        one prose component per printed container."""
        record = creature_key(spell)
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
                    reason(ts),
                    refs=refs_of(spell, record, ts, stat_block=True),
                    record=record,
                    texts=ts,
                )
            )

    def batch(self) -> EntryBatch:
        return EntryBatch(
            origin=ORIGIN,
            proposal_origin=f"{ORIGIN} (CRD Issue 5d spell descriptions; unaccepted)",
            unit_prefix="spell-descriptions",
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
            scoped_records=tuple(k for k, _, _ in self.records),
            edges=tuple(self.edges),
        )

    def record_keys(self) -> set[str]:
        return {p.record_key for p in self.placements.values()} | {
            k for k, _, _ in self.records
        }


#: *Wish*'s one fixed consequence a typed family states (Canary 1): Instant
#: Health restores all Hit Points, an effect with no amount.
WISH_FACTS: dict[str, tuple[MechanicalFact, ...]] = {
    "instant_health": (HealingFact(restores_all_hit_points=True),)
}


def spell_chunk(names: Iterable[str] = SPELL_NAMES) -> Chunk:
    """The section and *names* (every spell, unless a review narrows it)."""
    chunk = Chunk()
    heading = texts_at(SECTION)
    assert heading == ["## Spell Descriptions"], heading
    chunk.entry(
        "spell_descriptions",
        "spells.spell_descriptions",
        RecordKind.GENERAL_RULE,
        SECTION,
        "## Spell Descriptions",
        omit=tuple(SECTION + (n,) for n in SPELL_NAMES),
    )
    chunk.section("spell_descriptions", "spell_descriptions", heading, "")
    for name in names:
        path = SECTION + (name,)
        e = slug(name)
        chunk.entry(
            e,
            spell_key(name),
            RecordKind.SPELL,
            path,
            f"#### {name}",
            unit=ReviewUnitKind.ENTRY,
        )
        chunk.members.append((e, "spell_descriptions"))
        head, level_line, *rest = texts_at(path)
        assert head == f"#### {name}", head
        pieces, body = descriptor_texts(rest)
        fact = descriptor_fact(level_line, "\n".join(pieces))
        chunk.section(e, "descriptor", (head, level_line, *pieces), name, (fact,))
        for cls in spell_classes(level_line):
            chunk.edges.append(
                (
                    f"classes.{slug(cls)}",
                    spell_key(name),
                    RelationshipKind.SPELL_LIST_MEMBER,
                    e,
                    level_line,
                )
            )
        for key, ts in body_groups(name, body):
            facts = WISH_FACTS.get(key, ()) if name == "Wish" else ()
            chunk.section(e, key, ts, name, facts)
        for c in children(path):
            assert name in STAT_BLOCKS and c == STAT_BLOCKS[name][0], (name, c)
            chunk.stat_block(e, name, path + (c,))
    return chunk


SPELL_CHUNK = spell_chunk()
assert SPELL_CHUNK.leaves == len(LEAVES) == 2036
assert SEEN_CREATURES - {"Riding Horse"} == CREATURE_NAMES, sorted(
    SEEN_CREATURES ^ CREATURE_NAMES
)
assert {c.reason for c in SPELL_CHUNK.components} <= {GM, NO_USE}


#: Where a spell's level line and the class spell-list tables differ. None do:
#: the seven the official PDF printed (Flaming Sphere's school on pp44, 68, 80;
#: Mind Spike and Phantasmal Force missing from the Bard, Sorcerer and Wizard
#: tables) are Owner corrections in the controlled source, which follows the
#: spell descriptions (source_pin.json, "OWNER CORRECTION, not publisher text").
CLASS_LIST_DISAGREEMENTS: tuple[tuple[str, str, str, str, str], ...] = ()


#: A material the tables flag M: one priced in GP, or one the spell consumes.
COSTLY = re.compile(r"\d[\d,]*\+? GP|consumes")


def class_list_disagreements() -> tuple[tuple[str, str, str, str, str], ...]:
    """Each (class, spell, aspect, level line, class table) that differs.

    Reads the class tables from the qualified Classes source: each "<Class>
    Spell List" table row is (spell, school, special), where special flags C
    (Concentration), R (Ritual) and M (a costly or consumed material).
    """
    source = _load("issue-5d-classes-source").LEAVES  # type: ignore[attr-defined]
    rows: dict[tuple[str, str], tuple[int, str, set[str]]] = {}
    for path, text in source:
        if len(path) != 3 or not path[1].endswith(" Spell List"):
            continue
        m = re.fullmatch(r"(?:Cantrips \()?Level (\d) (\w+) Spells\)?", path[2])
        assert m and m[2] == path[0], path
        for row in re.findall(r"<tr>(.*?)</tr>", text, re.S):
            if cells := [c.strip() for c in re.findall(r"<td>(.*?)</td>", row, re.S)]:
                flags = set(re.findall(r"[CRM]", cells[2]))
                rows[(path[0], cells[0])] = (int(m[1]), cells[1], flags)
    out = []
    listed = set()
    for name in SPELL_NAMES:
        head, level_line, *rest = texts_at(SECTION + (name,))
        pieces, _ = descriptor_texts(rest)
        fact = descriptor_fact(level_line, "\n".join(pieces))
        for cls in spell_classes(level_line):
            listed.add((cls, name))
            if (cls, name) not in rows:
                out.append((cls, name, "listed", "yes", "no"))
                continue
            level, school, flags = rows[(cls, name)]
            assert level == fact.level, (cls, name)
            if school.lower() != fact.school.value:
                out.append((cls, name, "school", fact.school.value, school))
            assert ("C" in flags) == fact.concentration, (cls, name)
            assert ("R" in flags) == fact.ritual, (cls, name)
            material = DESCRIPTOR.fullmatch("\n".join(pieces))["co"]  # type: ignore[index]
            assert ("M" in flags) == bool(COSTLY.search(material)), (cls, name)
    assert set(rows) <= listed, sorted(set(rows) - listed)
    return tuple(sorted(out))


def batch() -> EntryBatch:
    return SPELL_CHUNK.batch()


def build(session: Session) -> Built:
    """Derive the spell descriptions proposal from the release *session* published."""
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
    """What the packet alone cannot see: accepted targets and class endpoints.

    One finding per component reference to an accepted record, one per
    unresolved pointer, and one per ``SPELL_LIST_MEMBER`` edge whose source is
    an accepted class record -- each is valid once the packet is read over the
    accepted oracle, which the composition check shows.
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
            *(
                f"relationship {s}->{t}: unknown record {s}"
                for s, t, _, _, _ in chunk.edges
            ),
        ]
    )


# ---------------------------------------------------------------------------
# Unrecorded resolution drafts for the same Owner packet
# ---------------------------------------------------------------------------
#: The recording script; its seventeen-batch chain is what the drafts compose over.
ACCEPT = "issue-5d-class-spell-tables-REPLACEMENT-ACCEPT.py"


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def draft_targets(
    prior: AcceptedInputs,
) -> tuple[
    list[tuple[str, str, str, str, tuple[str, ...]]], list[tuple[str, str, str]]
]:
    """(drafts, left): each accepted unresolved *Spells* pointer whose printed
    text is exactly one spell's name, to that spell, with the spans the oracle
    cites it from; and every other one, left unresolved as printed.

    ``prior`` is the chain the packet composes over."""
    from afterworlds.ingestion.mechanical.representation import (
        ProvenanceTargetKind,
        reference_target_key,
    )

    rep = prior.oracle.representation
    cited: dict[tuple[str, ...], list[str]] = {}
    for claim in rep.provenance:
        if claim.target_kind is ProvenanceTargetKind.REFERENCE:
            cited.setdefault(claim.target_key, []).append(claim.span_id)
    names = {n: spell_key(n) for n in SPELL_NAMES}
    drafts, left = [], []
    for ref in rep.references:
        if ref.scope_key != SPELLS or ref.target_record_key:
            continue
        where = (ref.from_record_key, ref.from_component_key, ref.source_text)
        if ref.source_text in names:
            spans = tuple(cited[reference_target_key(ref)])
            assert spans, where
            drafts.append((*where, names[ref.source_text], spans))
        else:
            left.append(where)
    return drafts, left


def draft_resolutions(
    binding: ReleaseBinding, prior: AcceptedInputs
) -> tuple[ReferenceResolution, ...]:
    drafts, _ = draft_targets(prior)
    out = tuple(
        ReferenceResolution(
            resolution_id=f"resolve-{_slug(record)}-{_slug(component) or 'record'}-{_slug(text)}-spell-descriptions-1",
            from_record_key=record,
            from_component_key=component,
            source_text=text,
            scope_key=SPELLS,
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
    emit(db, build, here / PROPOSAL_FILE, expected_representation_findings(SPELL_CHUNK))
    from afterworlds.persistence.database import create_engine, create_session_factory

    engine = create_engine(f"sqlite:///{db}")
    with create_session_factory(engine)() as session:
        binding = published_release_binding(session)
    engine.dispose()
    # The Owner's recorded chain, rebuilt natively; the committed oracle now
    # also holds this packet, whose drafts are already resolved in it.
    import importlib.util

    spec = importlib.util.spec_from_file_location("replacement_accept", here / ACCEPT)
    assert spec is not None and spec.loader is not None
    replacement = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = replacement
    spec.loader.exec_module(replacement)
    drafts = draft_resolutions(binding, prior=replacement.recorded())
    payload = reference_resolution_payload(drafts)
    (here / DRAFTS_FILE).write_bytes(
        (json.dumps(payload, indent=2) + "\n").encode("utf-8")
    )
    print(f"drafts            {DRAFTS_FILE} ({len(drafts)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
