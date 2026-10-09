# ruff: noqa: E501  -- clause literals are verbatim source text, kept whole to be greppable
"""Author the **character-origins-feats** proposal: the whole *Character
Origins* part and the whole *Feats* part, one dependency group.

REVIEW MATERIAL for CRD Issue 5d (#137) over the qualified 5c release
``9717e288-c099-5217-b2d2-f89aeabd7b73`` / ``5.2.1-corpus.883aabdf-462``. It
emits an *unaccepted* ``5d-proposal-2`` artifact. It accepts nothing, publishes
nothing, writes nothing under ``oracles/``, records no reference resolution,
and imports no earlier batch's content, identity or authority: every leaf is
read afresh from the release.

Scope, 208 leaves, 33 records, one review unit each:

* *Character Origins* (pp83-86). ``character_origins.backgrounds`` is the
  *Character Backgrounds* section less its four backgrounds (15 leaves: the
  definition and *Parts of a Background*); each background -- *Acolyte*,
  *Criminal*, *Sage*, *Soldier* -- is a ``background`` record of 2 leaves.
  ``character_origins.species`` is *Character Species* less its nine species
  (16 leaves: the introduction, life span and *Parts of a Species*); each
  species -- *Dragonborn* to *Tiefling* -- is a ``species`` record with its
  traits and its own table (Draconic Ancestors, Elven Lineages, Fiendish
  Legacies).
* *Feats* (pp87-88). ``feats.feat_descriptions`` is *Feat Descriptions* less
  its seventeen feats (12 leaves: the category organization, *Parts of a
  Feat* and the four category headings); each feat is a ``feat`` record.

The part titles ``# Character Origins`` and ``# Feats`` state no rule and
belong to no section, as ``# Character Creation`` belongs to none.

Kinds: the two origin sections say how a background and a species are built
into a level 1 character, so they are ``character_creation``. *Feat
Descriptions* is ``general_rule``: feats are taken at creation (Origin) and as
a character advances (General, Fighting Style, Epic Boon), so neither the
creation nor the advancement kind alone is what it is.

This file is literal review data only; the assembly is the committed shared
:mod:`afterworlds.ingestion.mechanical.authoring`. ``CLAUSES`` is the source
review; ``COMPONENTS`` is the representation proposed for it; expected rules
come from ``CLAUSES`` alone.

Authoring conventions (as the eleven accepted batches):

* Every component is prose-bound. No closed family faithfully states what
  these options carry. A use count "equal to your Proficiency Bonus" is not
  ``ResourceRecoveryFact.uses`` (an integer); Breath Weapon's steps at levels
  5, 11 and 17 are not one ``ScalingFact`` threshold; ``Sense`` declares no
  Darkvision, Tremorsense or Truesight member, and adding one is a schema
  change this batch does not make. A typed Darkvision range or Speed would in
  any case detach the lineage rows that change them (Drow 120 feet, Wood Elf
  35 feet) from the value they change.
* Each option keeps its conditions with it: a trait and its uses paragraph are
  one component (Breath Weapon, Stonecunning, Adrenaline Rush); a lineage or
  legacy trait is one component with its level 3 and 5 paragraph, its
  spellcasting-ability choice and its table (Elven Lineage, Fiendish Legacy),
  or with its options (Gnomish Lineage, Giant Ancestry). A background is one
  component per printed line; a species' creature type, size and speed are
  one component each. A feat's category line, which prints its prerequisite,
  is its ``category`` component; each named benefit and each *Repeatable* is
  its own component.
* ``contextual_applicability`` is kept where applying the trait turns on
  fiction the projection cannot enumerate (Stonecunning's stone surface, Large
  Form's "big enough space"); everything else is
  ``no_identified_structured_use``. No rule here delegates to the GM.
* Examples and advice are supporting spans of the component they illustrate:
  the Rock Gnome's device example, the Human's "Skilled is recommended." and
  the species introduction's paragraph on where species come from.
* Membership: each background, species and feat is a ``CATALOGUE_MEMBER`` of
  the section that prints it (4, 9 and 17 edges, ``MEMBERS``; representation
  schema 16), so a consumer that names a section reaches the entries it prints,
  in printed order, rather than its introduction alone. ``SCOPED_WITHIN`` is
  not used and keeps its meaning. The edges are declared, checked against the
  release's containment, and cite each member's first clause as contextual
  source, which is also the position the member is read in.
* References:

  - every explicit pointer. A background's ``(see "Feats")`` follows the feat
    it names, and names that feat's record; the Parts-of-a-Background *Feat*
    and the Human's *Versatile* ("an Origin feat ... (see "Feats")") name
    ``feats.feat_descriptions``, the part's only section, which defines the
    categories and, through its members, reaches every feat; the Origin
    restriction stays in the pointer's own clause. The *Creature Type* part's
    "Rules Glossary" names the accepted ``glossary.creature_type``, the entry
    its clause describes. "Equipment"
    is an unauthored part and stays unresolved. The two mentions of
    "Character Origins" inside *Character Species* name the part that section
    belongs to and point nowhere else, so they are not references.
  - each accepted Rules Glossary term a rule here depends on, by its printed
    name (``GLOSSARY_TERMS``), once per component. Unaccepted glossary terms
    (Advantage, Bonus Action, Reaction, Heroic Inspiration, Dim Light,
    Darkness, Cone, Line) and skills stay unreferenced, as before.
  - each named member of a catalogue this batch does not author that a rule
    here grants or requires -- a spell, a class spell list, a class feature
    prerequisite, a piece of equipment or a tool, a weapon property or armor
    category -- is a reference in that catalogue's part with no target,
    reported unresolved. None is stubbed or authored. Currency (GP) is a unit,
    not a catalogue member, and the giant kinds that title Giant Ancestry's
    options name an ancestry, not a rule dependency.

Three accepted citations print "Character Origins" or "Feats" and stay
unresolved. This batch makes each resolvable, so three unrecorded resolution
drafts are given below for the same Owner packet; nothing here records or
applies them, and the three recorded resolutions are untouched.

Run: ``python issue-5d-character-origins-feats-generator.py <published afterworlds.db>``
"""

from __future__ import annotations

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
    html_table,
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
    ReviewUnitKind,
)
from afterworlds.ingestion.mechanical.representation import RecordKind

ORIGIN = "issue-5d-character-origins-feats-generator.py"
PROPOSAL_FILE = "issue-5d-character-origins-feats-PROPOSAL.json"
#: Every record here is placed; the unplaced-entry default is never read.
PARENT = ("Rules Glossary", "Rules Definitions")
#: The parts this batch's records and pointers name, formed from the release's
#: own part names under the ``<release-family>/<section-slug>`` convention.
CHARACTER_ORIGINS = "srd-5.2.1/character-origins"
FEATS = "srd-5.2.1/feats"
CLASSES = "srd-5.2.1/classes"
EQUIPMENT = "srd-5.2.1/equipment"
SPELLS = "srd-5.2.1/spells"
#: The target of a printed pointer whose destination has no record yet. It is
#: reported as ``unresolved reference`` until a reviewed resolution names one;
#: naming a key here would guess at a record nobody has authored.
UNRESOLVED_TARGET = ""

ORIGINS_PART = "Character Origins"
FEATS_PART = "Feats"
BACKGROUNDS = (ORIGINS_PART, "Character Backgrounds")
BACKGROUND_DESCRIPTIONS = (*BACKGROUNDS, "Background Descriptions")
SPECIES = (ORIGINS_PART, "Character Species")
SPECIES_DESCRIPTIONS = (*SPECIES, "Species Descriptions")
FEAT_DESCRIPTIONS = (FEATS_PART, "Feat Descriptions")

#: (slug, printed label) of each background and species, in printed order.
BACKGROUND_ENTRIES = (
    ("acolyte", "Acolyte"),
    ("criminal", "Criminal"),
    ("sage", "Sage"),
    ("soldier", "Soldier"),
)
SPECIES_ENTRIES = (
    ("dragonborn", "Dragonborn"),
    ("dwarf", "Dwarf"),
    ("elf", "Elf"),
    ("gnome", "Gnome"),
    ("goliath", "Goliath"),
    ("halfling", "Halfling"),
    ("human", "Human"),
    ("orc", "Orc"),
    ("tiefling", "Tiefling"),
)
#: (slug, printed label, printed category heading) of each feat, in printed order.
FEAT_ENTRIES = (
    ("alert", "Alert", "Origin Feats"),
    ("magic_initiate", "Magic Initiate", "Origin Feats"),
    ("savage_attacker", "Savage Attacker", "Origin Feats"),
    ("skilled", "Skilled", "Origin Feats"),
    ("ability_score_improvement", "Ability Score Improvement", "General Feats"),
    ("grappler", "Grappler", "General Feats"),
    ("archery", "Archery", "Fighting Style Feats"),
    ("defense", "Defense", "Fighting Style Feats"),
    ("great_weapon_fighting", "Great Weapon Fighting", "Fighting Style Feats"),
    ("two_weapon_fighting", "Two-Weapon Fighting", "Fighting Style Feats"),
    ("boon_of_combat_prowess", "Boon of Combat Prowess", "Epic Boon Feats"),
    ("boon_of_dimensional_travel", "Boon of Dimensional Travel", "Epic Boon Feats"),
    ("boon_of_fate", "Boon of Fate", "Epic Boon Feats"),
    (
        "boon_of_irresistible_offense",
        "Boon of Irresistible Offense",
        "Epic Boon Feats",
    ),
    ("boon_of_spell_recall", "Boon of Spell Recall", "Epic Boon Feats"),
    ("boon_of_the_night_spirit", "Boon of the Night Spirit", "Epic Boon Feats"),
    ("boon_of_truesight", "Boon of Truesight", "Epic Boon Feats"),
)

#: (record slug, printed container label, record kind), in printed order.
ENTRIES: tuple[tuple[str, str, RecordKind], ...] = (
    ("backgrounds", "Character Backgrounds", RecordKind.CHARACTER_CREATION),
    *((s, label, RecordKind.BACKGROUND) for s, label in BACKGROUND_ENTRIES),
    ("species", "Character Species", RecordKind.CHARACTER_CREATION),
    *((s, label, RecordKind.SPECIES) for s, label in SPECIES_ENTRIES),
    ("feat_descriptions", "Feat Descriptions", RecordKind.GENERAL_RULE),
    *((s, label, RecordKind.FEAT) for s, label, _ in FEAT_ENTRIES),
)


def _entry(key: str, container: tuple[str, ...], label: str) -> Placement:
    return Placement(key, container, f"#### {label}", ReviewUnitKind.ENTRY)


#: Every record's key, container and heading. A section record omits the
#: entries placed as records of their own, keeping its subsection headings.
PLACEMENTS: dict[str, Placement] = {
    "backgrounds": Placement(
        "character_origins.backgrounds",
        BACKGROUNDS,
        "## Character Backgrounds",
        omit=tuple(
            (*BACKGROUND_DESCRIPTIONS, label) for _, label in BACKGROUND_ENTRIES
        ),
    ),
    **{
        s: _entry(f"character_origins.{s}", (*BACKGROUND_DESCRIPTIONS, label), label)
        for s, label in BACKGROUND_ENTRIES
    },
    "species": Placement(
        "character_origins.species",
        SPECIES,
        "## Character Species",
        omit=tuple((*SPECIES_DESCRIPTIONS, label) for _, label in SPECIES_ENTRIES),
    ),
    **{
        s: _entry(f"character_origins.{s}", (*SPECIES_DESCRIPTIONS, label), label)
        for s, label in SPECIES_ENTRIES
    },
    "feat_descriptions": Placement(
        "feats.feat_descriptions",
        FEAT_DESCRIPTIONS,
        "## Feat Descriptions",
        omit=tuple((*FEAT_DESCRIPTIONS, c, label) for _, label, c in FEAT_ENTRIES),
    ),
    **{
        s: _entry(f"feats.{s}", (*FEAT_DESCRIPTIONS, c, label), label)
        for s, label, c in FEAT_ENTRIES
    },
}

#: Each background, species and feat as a member of the section that prints
#: it, in printed order. The shared assembly emits one ``CATALOGUE_MEMBER``
#: edge per row, citing the member's first clause, and refuses the list unless it is
#: exactly the entries whose leaves lie in the section's container: 4, 9, 17.
MEMBERS: tuple[tuple[str, str], ...] = (
    *((s, "backgrounds") for s, _ in BACKGROUND_ENTRIES),
    *((s, "species") for s, _ in SPECIES_ENTRIES),
    *((s, "feat_descriptions") for s, _, _ in FEAT_ENTRIES),
)

# ---------------------------------------------------------------------------
# Reason codes and handling
# ---------------------------------------------------------------------------
CTX = "contextual_applicability"
NO_USE = "no_identified_structured_use"
P = ComponentHandling.PROSE_BOUND
PROSE = None

# ---------------------------------------------------------------------------
# Table leaves, written as their rows
# ---------------------------------------------------------------------------
DRACONIC_ANCESTORS_TABLE = html_table(
    "Draconic Ancestors",
    ("Dragon", "Damage Type", "Dragon", "Damage Type"),
    [
        ("Black", "Acid", "Gold", "Fire"),
        ("Blue", "Lightning", "Green", "Poison"),
        ("Brass", "Fire", "Red", "Fire"),
        ("Bronze", "Lightning", "Silver", "Cold"),
        ("Copper", "Acid", "White", "Cold"),
    ],
)

ELVEN_LINEAGES_TABLE = html_table(
    "Elven Lineages",
    ("Lineage", "Level 1", "Level 3", "Level 5"),
    [
        (
            "Drow",
            "The range of your Darkvision increases to 120 feet. You also know the Dancing Lights cantrip.",
            "Faerie Fire",
            "Darkness",
        ),
        (
            "High Elf",
            "You know the Prestidigitation cantrip. Whenever you finish a Long Rest, you can replace that cantrip with a different cantrip from the Wizard spell list.",
            "Detect Magic",
            "Misty Step",
        ),
        (
            "Wood Elf",
            "Your Speed increases to 35 feet. You also know the Druidcraft cantrip.",
            "Longstrider",
            "Pass without Trace",
        ),
    ],
)

FIENDISH_LEGACIES_TABLE = html_table(
    "Fiendish Legacies",
    ("Legacy", "Level 1", "Level 3", "Level 5"),
    [
        (
            "Abyssal",
            "You have Resistance to Poison damage. You also know the Poison Spray cantrip.",
            "Ray of Sickness",
            "Hold Person",
        ),
        (
            "Chthonic",
            "You have Resistance to Necrotic damage. You also know the Chill Touch cantrip.",
            "False Life",
            "Ray of Enfeeblement",
        ),
        (
            "Infernal",
            "You have Resistance to Fire damage. You also know the Fire Bolt cantrip.",
            "Hellish Rebuke",
            "Darkness",
        ),
    ],
)

#: The level 3 and 5 paragraph Elven Lineage and Fiendish Legacy both print.
HIGHER_LEVEL_SPELLS = "When you reach character levels 3 and 5, you learn a higher-level spell, as shown on the table. You always have that spell prepared. You can cast it once without a spell slot, and you regain the ability to cast it in that way when you finish a Long Rest. You can also cast the spell using any spell slots you have of the appropriate level."
EPIC_ASI = "_Ability Score Increase._ Increase one ability score of your choice by 1, to a maximum of 30."
FIGHTING_STYLE_CATEGORY = "_Fighting Style Feat (Prerequisite: Fighting Style Feature)_"
EPIC_BOON_CATEGORY = "_Epic Boon Feat (Prerequisite: Level 19+)_"
ROCK_GNOME_EXAMPLE = "For example, if you choose the spell's ignite-extinguish effect, you determine whether the device ignites or extinguishes fire; the device doesn't do both."
SKILLED_ADVICE = "Skilled is recommended."
SPECIES_GENESIS = "Some species can trace their origin to a single world, plane of existence, or god, while other species first appeared in multiple realms at once. Whatever a species' genesis, its members have spread across the multiverse and contribute to many different cultures."

Clause = tuple[str, str, tuple[str | None, ...], tuple[str, ...]]


def cl(entry: str, key: str, *texts: str) -> Clause:
    """One clause row whose meaning is carried by governing prose."""
    return (entry, key, (PROSE,), texts)


def _stats(entry: str, size: str, speed: str) -> tuple[Clause, ...]:
    """A species' three printed stat lines, one clause each."""
    return (
        cl(entry, "creature_type", "**Creature Type:** Humanoid"),
        cl(entry, "size", f"**Size:** {size}"),
        cl(entry, "speed", f"**Speed:** {speed}"),
    )


def _background(
    entry: str, scores: str, feat: str, skills: str, tool: str, equipment: str
) -> tuple[Clause, ...]:
    """A background's five printed lines, one clause each."""
    return (
        cl(entry, "ability_scores", f"**Ability Scores:** {scores}"),
        cl(entry, "feat", f"**Feat:** {feat}"),
        cl(entry, "skill_proficiencies", f"**Skill Proficiencies:** {skills}"),
        cl(entry, "tool_proficiency", f"**Tool Proficiency:** {tool}"),
        cl(entry, "equipment", f"**Equipment:** {equipment}"),
    )


CLAUSES: tuple[Clause, ...] = (
    # == Character Backgrounds (p83) ==========================================
    cl(
        "backgrounds",
        "background",
        "Your character's background is a collection of characteristics that represent the place and occupation that were most formative before your character embarked on a life of adventure.",
    ),
    cl(
        "backgrounds",
        "ability_scores",
        "A background lists three of your character's ability scores. Increase one by 2 and another one by 1, or increase all three by 1. None of these increases can raise a score above 20.",
    ),
    cl(
        "backgrounds",
        "feat",
        'A background gives your character a specified Origin feat (described in "Feats").',
    ),
    cl(
        "backgrounds",
        "skill_proficiencies",
        "A background gives your character proficiency in two specified skills.",
    ),
    cl(
        "backgrounds",
        "tool_proficiency",
        'Each background gives a character proficiency with one tool—either a specific tool or one chosen from the Artisan\'s Tools category. Tools are detailed in "Equipment."',
    ),
    cl(
        "backgrounds",
        "equipment",
        "Each background offers a choice between a package of equipment and 50 GP.",
    ),
    *_background(
        "acolyte",
        "Intelligence, Wisdom, Charisma",
        'Magic Initiate (Cleric) (see "Feats")',
        "Insight and Religion",
        "Calligrapher's Supplies",
        "_Choose A or B:_ (A) Calligrapher's Supplies, Book (prayers), Holy Symbol, Parchment (10 sheets), Robe, 8 GP; or (B) 50 GP",
    ),
    *_background(
        "criminal",
        "Dexterity, Constitution, Intelligence",
        'Alert (see "Feats")',
        "Sleight of Hand and Stealth",
        "Thieves' Tools",
        "_Choose A or B:_ (A) 2 Daggers, Thieves' Tools, Crowbar, 2 Pouches, Traveler's Clothes, 16 GP; or (B) 50 GP",
    ),
    *_background(
        "sage",
        "Constitution, Intelligence, Wisdom",
        'Magic Initiate (Wizard) (see "Feats")',
        "Arcana and History",
        "Calligrapher's Supplies",
        "_Choose A or B:_ (A) Quarterstaff, Calligrapher's Supplies, Book (history), Parchment (8 sheets), Robe, 8 GP; or (B) 50 GP",
    ),
    *_background(
        "soldier",
        "Strength, Dexterity, Constitution",
        'Savage Attacker (see "Feats")',
        "Athletics and Intimidation",
        '_Choose one kind of_ Gaming Set (see "Equipment")',
        "_Choose A or B:_ (A) Spear, Shortbow, 20 Arrows, Gaming Set (same as above), Healer's Kit, Quiver, Traveler's Clothes, 14 GP; or (B) 50 GP",
    ),
    # == Character Species (pp83-84) ==========================================
    cl(
        "species",
        "species",
        "When you choose your character's species, you determine whether your character is a human or a member of a fantastical species, such as dragonborn or gnome.",
        "The peoples of the multiverse hail from different worlds and include many kinds of sapient life forms. A player character's species is the set of game traits that an adventurer gains from being one of those life forms.",
    ),
    cl(
        "species",
        "life_span",
        "Members of most species live for about 80 years, with exceptions noted in the text about the species in \"Character Origins.\" Regardless of life span, members of all species reach physical maturity at about the same age. Your character can be any age that isn't beyond their species' normal life span.",
    ),
    cl(
        "species",
        "creature_type",
        'A character\'s species determines the character\'s creature type, which is described in "Rules Glossary." Every species in "Character Origins" is Humanoid; playable non-Humanoid species appear in other books.',
    ),
    cl(
        "species",
        "size",
        "Your character's species determines the character's size. Individuals within a species cover a wide range of heights, and some species include such diversity of size that you can choose whether your character is Small or Medium.",
    ),
    cl(
        "species", "speed", "Your character's species determines the character's Speed."
    ),
    cl(
        "species",
        "special_traits",
        "Each species gives a character special traits—unique characteristics based on the species' physiology or magical nature. When you choose a species, your character gets all the special traits listed for it. Some traits involve making a choice from a handful of options.",
    ),
    # -- Dragonborn (p84) -----------------------------------------------------
    *_stats("dragonborn", "Medium (about 5–7 feet tall)", "30 feet"),
    cl(
        "dragonborn",
        "draconic_ancestry",
        "_Draconic Ancestry._ Your lineage stems from a dragon progenitor. Choose the kind of dragon from the Draconic Ancestors table. Your choice affects your Breath Weapon and Damage Resistance traits as well as your appearance.",
        DRACONIC_ANCESTORS_TABLE,
    ),
    cl(
        "dragonborn",
        "breath_weapon",
        "_Breath Weapon._ When you take the Attack action on your turn, you can replace one of your attacks with an exhalation of magical energy in either a 15-foot Cone or a 30-foot Line that is 5 feet wide (choose the shape each time). Each creature in that area must make a Dexterity saving throw (DC 8 plus your Constitution modifier and Proficiency Bonus). On a failed save, a creature takes 1d10 damage of the type determined by your Draconic Ancestry trait. On a successful save, a creature takes half as much damage. This damage increases by 1d10 when you reach character levels 5 (2d10), 11 (3d10), and 17 (4d10).",
        "You can use this Breath Weapon a number of times equal to your Proficiency Bonus, and you regain all expended uses when you finish a Long Rest.",
    ),
    cl(
        "dragonborn",
        "damage_resistance",
        "_Damage Resistance._ You have Resistance to the damage type determined by your Draconic Ancestry trait.",
    ),
    cl(
        "dragonborn",
        "darkvision",
        "_Darkvision._ You have Darkvision with a range of 60 feet.",
    ),
    cl(
        "dragonborn",
        "draconic_flight",
        "_Draconic Flight._ When you reach character level 5, you can channel draconic magic to give yourself temporary flight. As a Bonus Action, you sprout spectral wings on your back that last for 10 minutes or until you retract the wings (no action required) or have the Incapacitated condition. During that time, you have a Fly Speed equal to your Speed. Your wings appear to be made of the same energy as your Breath Weapon. Once you use this trait, you can't use it again until you finish a Long Rest.",
    ),
    # -- Dwarf (p84) ----------------------------------------------------------
    *_stats("dwarf", "Medium (about 4–5 feet tall)", "30 feet"),
    cl(
        "dwarf",
        "darkvision",
        "_Darkvision._ You have Darkvision with a range of 120 feet.",
    ),
    cl(
        "dwarf",
        "dwarven_resilience",
        "_Dwarven Resilience._ You have Resistance to Poison damage. You also have Advantage on saving throws you make to avoid or end the Poisoned condition.",
    ),
    cl(
        "dwarf",
        "dwarven_toughness",
        "_Dwarven Toughness._ Your Hit Point maximum increases by 1, and it increases by 1 again whenever you gain a level.",
    ),
    cl(
        "dwarf",
        "stonecunning",
        "_Stonecunning._ As a Bonus Action, you gain Tremorsense with a range of 60 feet for 10 minutes. You must be on a stone surface or touching a stone surface to use this Tremorsense. The stone can be natural or worked.",
        "You can use this Bonus Action a number of times equal to your Proficiency Bonus, and you regain all expended uses when you finish a Long Rest.",
    ),
    # -- Elf (pp84-85) --------------------------------------------------------
    *_stats("elf", "Medium (about 5–6 feet tall)", "30 feet"),
    cl(
        "elf",
        "darkvision",
        "_Darkvision._ You have Darkvision with a range of 60 feet.",
    ),
    cl(
        "elf",
        "elven_lineage",
        "_Elven Lineage._ You are part of a lineage that grants you supernatural abilities. Choose a lineage from the Elven Lineages table. You gain the level 1 benefit of that lineage.",
        HIGHER_LEVEL_SPELLS,
        "Intelligence, Wisdom, or Charisma is your spellcasting ability for the spells you cast with this trait (choose the ability when you select the lineage).",
        ELVEN_LINEAGES_TABLE,
    ),
    cl(
        "elf",
        "fey_ancestry",
        "_Fey Ancestry._ You have Advantage on saving throws you make to avoid or end the Charmed condition.",
    ),
    cl(
        "elf",
        "keen_senses",
        "_Keen Senses._ You have proficiency in the Insight, Perception, or Survival skill.",
    ),
    cl(
        "elf",
        "trance",
        "_Trance._ You don't need to sleep, and magic can't put you to sleep. You can finish a Long Rest in 4 hours if you spend those hours in a trancelike meditation, during which you retain consciousness.",
    ),
    # -- Gnome (p85) ----------------------------------------------------------
    *_stats("gnome", "Small (about 3–4 feet tall)", "30 feet"),
    cl(
        "gnome",
        "darkvision",
        "_Darkvision._ You have Darkvision with a range of 60 feet.",
    ),
    cl(
        "gnome",
        "gnomish_cunning",
        "_Gnomish Cunning._ You have Advantage on Intelligence, Wisdom, and Charisma saving throws.",
    ),
    cl(
        "gnome",
        "gnomish_lineage",
        "_Gnomish Lineage._ You are part of a lineage that grants you supernatural abilities. Choose one of the following options; whichever one you choose, Intelligence, Wisdom, or Charisma is your spellcasting ability for the spells you cast with this trait (choose the ability when you select the lineage):",
        "**Forest Gnome.** You know the _Minor Illusion_ cantrip. You also always have the _Speak with Animals_ spell prepared. You can cast it without a spell slot a number of times equal to your Proficiency Bonus, and you regain all expended uses when you finish a Long Rest. You can also use any spell slots you have to cast the spell.",
        "**Rock Gnome.** You know the _Mending_ and _Prestidigitation_ cantrips. In addition, you can spend 10 minutes casting _Prestidigitation_ to create a Tiny clockwork device (AC 5, 1 HP), such as a toy, fire starter, or music box. When you create the device, you determine its function by choosing one effect from _Prestidigitation_; the device produces that effect whenever you or another creature takes a Bonus Action to activate it with a touch. If the chosen effect has options within it, you choose one of those options for the device when you create it.",
        "You can have three such devices in existence at a time, and each falls apart 8 hours after its creation or when you dismantle it with a touch as a Utilize action.",
    ),
    # -- Goliath (pp85-86) ----------------------------------------------------
    *_stats("goliath", "Medium (about 7–8 feet tall)", "35 feet"),
    cl(
        "goliath",
        "giant_ancestry",
        "_Giant Ancestry._ You are descended from Giants. Choose one of the following benefits—a supernatural boon from your ancestry; you can use the chosen benefit a number of times equal to your Proficiency Bonus, and you regain all expended uses when you finish a Long Rest:",
        "**Cloud's Jaunt (Cloud Giant).** As a Bonus Action, you magically teleport up to 30 feet to an unoccupied space you can see.",
        "**Fire's Burn (Fire Giant).** When you hit a target with an attack roll and deal damage to it, you can also deal 1d10 Fire damage to that target.",
        "**Frost's Chill (Frost Giant).** When you hit a target with an attack roll and deal damage to it, you can also deal 1d6 Cold damage to that target and reduce its Speed by 10 feet until the start of your next turn.",
        "**Hill's Tumble (Hill Giant).** When you hit a Large or smaller creature with an attack roll and deal damage to it, you can give that target the Prone condition.",
        "**Stone's Endurance (Stone Giant).** When you take damage, you can take a Reaction to roll 1d12. Add your Constitution modifier to the number rolled and reduce the damage by that total.",
        "**Storm's Thunder (Storm Giant).** When you take damage from a creature within 60 feet of you, you can take a Reaction to deal 1d8 Thunder damage to that creature.",
    ),
    cl(
        "goliath",
        "large_form",
        "_Large Form._ Starting at character level 5, you can change your size to Large as a Bonus Action if you're in a big enough space. This transformation lasts for 10 minutes or until you end it (no action required). For that duration, you have Advantage on Strength checks, and your Speed increases by 10 feet. Once you use this trait, you can't use it again until you finish a Long Rest.",
    ),
    cl(
        "goliath",
        "powerful_build",
        "_Powerful Build._ You have Advantage on any ability check you make to end the Grappled condition. You also count as one size larger when determining your carrying capacity.",
    ),
    # -- Halfling (p86) -------------------------------------------------------
    *_stats("halfling", "Small (about 2–3 feet tall)", "30 feet"),
    cl(
        "halfling",
        "brave",
        "_Brave._ You have Advantage on saving throws you make to avoid or end the Frightened condition.",
    ),
    cl(
        "halfling",
        "halfling_nimbleness",
        "_Halfling Nimbleness._ You can move through the space of any creature that is a size larger than you, but you can't stop in the same space.",
    ),
    cl(
        "halfling",
        "luck",
        "_Luck._ When you roll a 1 on the d20 of a D20 Test, you can reroll the die, and you must use the new roll.",
    ),
    cl(
        "halfling",
        "naturally_stealthy",
        "_Naturally Stealthy._ You can take the Hide action even when you are obscured only by a creature that is at least one size larger than you.",
    ),
    # -- Human (p86) ----------------------------------------------------------
    *_stats(
        "human",
        "Medium (about 4–7 feet tall) or Small (about 2–4 feet tall), chosen when you select this species",
        "30 feet",
    ),
    cl(
        "human",
        "resourceful",
        "_Resourceful._ You gain Heroic Inspiration whenever you finish a Long Rest.",
    ),
    cl(
        "human",
        "skillful",
        "_Skillful._ You gain proficiency in one skill of your choice.",
    ),
    cl(
        "human",
        "versatile",
        '_Versatile._ You gain an Origin feat of your choice (see "Feats").',
    ),
    # -- Orc (p86) ------------------------------------------------------------
    *_stats("orc", "Medium (about 6–7 feet tall)", "30 feet"),
    cl(
        "orc",
        "adrenaline_rush",
        "_Adrenaline Rush._ You can take the Dash action as a Bonus Action. When you do so, you gain a number of Temporary Hit Points equal to your Proficiency Bonus.",
        "You can use this trait a number of times equal to your Proficiency Bonus, and you regain all expended uses when you finish a Short or Long Rest.",
    ),
    cl(
        "orc",
        "darkvision",
        "_Darkvision._ You have Darkvision with a range of 120 feet.",
    ),
    cl(
        "orc",
        "relentless_endurance",
        "_Relentless Endurance._ When you are reduced to 0 Hit Points but not killed outright, you can drop to 1 Hit Point instead. Once you use this trait, you can't do so again until you finish a Long Rest.",
    ),
    # -- Tiefling (p86) -------------------------------------------------------
    *_stats(
        "tiefling",
        "Medium (about 4–7 feet tall) or Small (about 3–4 feet tall), chosen when you select this species",
        "30 feet",
    ),
    cl(
        "tiefling",
        "darkvision",
        "_Darkvision._ You have Darkvision with a range of 60 feet.",
    ),
    cl(
        "tiefling",
        "fiendish_legacy",
        "_Fiendish Legacy._ You are the recipient of a legacy that grants you supernatural abilities. Choose a legacy from the Fiendish Legacies table. You gain the level 1 benefit of the chosen legacy.",
        HIGHER_LEVEL_SPELLS,
        "Intelligence, Wisdom, or Charisma is your spellcasting ability for the spells you cast with this trait (choose the ability when you select the legacy).",
        FIENDISH_LEGACIES_TABLE,
    ),
    cl(
        "tiefling",
        "otherworldly_presence",
        "_Otherworldly Presence._ You know the _Thaumaturgy_ cantrip. When you cast it with this trait, the spell uses the same spellcasting ability you use for your Fiendish Legacy trait.",
    ),
    # == Feat Descriptions (p87) ===============================================
    cl(
        "feat_descriptions",
        "categories",
        "The feats that follow are organized by category—Origin, General, Fighting Style, or Epic Boon—and alphabetized in each category.",
    ),
    cl(
        "feat_descriptions",
        "category",
        "_Category._ A feat is a member of a category, which is noted in the feat. If you're instructed to choose a feat from a specific category, such as the Origin category, that category must appear under the feat's name. If you're instructed to choose a feat and no category is specified, you can choose from any category.",
    ),
    cl(
        "feat_descriptions",
        "prerequisite",
        "_Prerequisite._ To take a feat, you must meet any prerequisite in its description unless a feature allows you to take the feat without the prerequisite. If a prerequisite includes a class, you must have at least 1 level in that class to take the feat.",
    ),
    cl(
        "feat_descriptions",
        "benefit",
        "_Benefit._ The benefits of a feat are detailed after any prerequisites are listed. If you have a feat, you gain its benefits.",
    ),
    cl(
        "feat_descriptions",
        "repeatable",
        '_Repeatable._ A feat can be taken only once unless its description states otherwise in a "Repeatable" subsection.',
    ),
    # -- Origin Feats (p87) ---------------------------------------------------
    cl("alert", "category", "_Origin Feat_"),
    cl(
        "alert",
        "initiative_proficiency",
        "_Initiative Proficiency._ When you roll Initiative, you can add your Proficiency Bonus to the roll.",
    ),
    cl(
        "alert",
        "initiative_swap",
        "_Initiative Swap._ Immediately after you roll Initiative, you can swap your Initiative with the Initiative of one willing ally in the same combat. You can't make this swap if you or the ally has the Incapacitated condition.",
    ),
    cl("magic_initiate", "category", "_Origin Feat_"),
    cl(
        "magic_initiate",
        "two_cantrips",
        "_Two Cantrips._ You learn two cantrips of your choice from the Cleric, Druid, or Wizard spell list. Intelligence, Wisdom, or Charisma is your spellcasting ability for this feat's spells (choose when you select this feat).",
    ),
    cl(
        "magic_initiate",
        "level_1_spell",
        "_Level 1 Spell._ Choose a level 1 spell from the same list you selected for this feat's cantrips. You always have that spell prepared. You can cast it once without a spell slot, and you regain the ability to cast it in that way when you finish a Long Rest. You can also cast the spell using any spell slots you have.",
    ),
    cl(
        "magic_initiate",
        "spell_change",
        "_Spell Change._ Whenever you gain a new level, you can replace one of the spells you chose for this feat with a different spell of the same level from the chosen spell list.",
    ),
    cl(
        "magic_initiate",
        "repeatable",
        "_Repeatable._ You can take this feat more than once, but you must choose a different spell list each time.",
    ),
    cl("savage_attacker", "category", "_Origin Feat_"),
    cl(
        "savage_attacker",
        "savage_attacker",
        "You've trained to deal particularly damaging strikes. Once per turn when you hit a target with a weapon, you can roll the weapon's damage dice twice and use either roll against the target.",
    ),
    cl("skilled", "category", "_Origin Feat_"),
    cl(
        "skilled",
        "skilled",
        "You gain proficiency in any combination of three skills or tools of your choice.",
    ),
    cl("skilled", "repeatable", "_Repeatable._ You can take this feat more than once."),
    # -- General Feats (p87) --------------------------------------------------
    cl(
        "ability_score_improvement",
        "category",
        "_General Feat (Prerequisite: Level 4+)_",
    ),
    cl(
        "ability_score_improvement",
        "ability_score_improvement",
        "Increase one ability score of your choice by 2, or increase two ability scores of your choice by 1. This feat can't increase an ability score above 20.",
    ),
    cl(
        "ability_score_improvement",
        "repeatable",
        "_Repeatable._ You can take this feat more than once.",
    ),
    cl(
        "grappler",
        "category",
        "_General Feat (Prerequisite: Level 4+, Strength or Dexterity 13+)_",
    ),
    cl(
        "grappler",
        "ability_score_increase",
        "_Ability Score Increase._ Increase your Strength or Dexterity score by 1, to a maximum of 20.",
    ),
    cl(
        "grappler",
        "punch_and_grab",
        "_Punch and Grab._ When you hit a creature with an Unarmed Strike as part of the Attack action on your turn, you can use both the Damage and the Grapple option. You can use this benefit only once per turn.",
    ),
    cl(
        "grappler",
        "attack_advantage",
        "_Attack Advantage._ You have Advantage on attack rolls against a creature Grappled by you.",
    ),
    cl(
        "grappler",
        "fast_wrestler",
        "_Fast Wrestler._ You don't have to spend extra movement to move a creature Grappled by you if the creature is your size or smaller.",
    ),
    # -- Fighting Style Feats (pp87-88) ---------------------------------------
    cl("archery", "category", FIGHTING_STYLE_CATEGORY),
    cl(
        "archery",
        "archery",
        "You gain a +2 bonus to attack rolls you make with Ranged weapons.",
    ),
    cl("defense", "category", FIGHTING_STYLE_CATEGORY),
    cl(
        "defense",
        "defense",
        "While you're wearing Light, Medium, or Heavy armor, you gain a +1 bonus to Armor Class.",
    ),
    cl("great_weapon_fighting", "category", FIGHTING_STYLE_CATEGORY),
    cl(
        "great_weapon_fighting",
        "great_weapon_fighting",
        "When you roll damage for an attack you make with a Melee weapon that you are holding with two hands, you can treat any 1 or 2 on a damage die as a 3. The weapon must have the Two-Handed or Versatile property to gain this benefit.",
    ),
    cl("two_weapon_fighting", "category", FIGHTING_STYLE_CATEGORY),
    cl(
        "two_weapon_fighting",
        "two_weapon_fighting",
        "When you make an extra attack as a result of using a weapon that has the Light property, you can add your ability modifier to the damage of that attack if you aren't already adding it to the damage.",
    ),
    # -- Epic Boon Feats (p88) ------------------------------------------------
    cl("boon_of_combat_prowess", "category", EPIC_BOON_CATEGORY),
    cl("boon_of_combat_prowess", "ability_score_increase", EPIC_ASI),
    cl(
        "boon_of_combat_prowess",
        "peerless_aim",
        "_Peerless Aim._ When you miss with an attack roll, you can hit instead. Once you use this benefit, you can't use it again until the start of your next turn.",
    ),
    cl("boon_of_dimensional_travel", "category", EPIC_BOON_CATEGORY),
    cl("boon_of_dimensional_travel", "ability_score_increase", EPIC_ASI),
    cl(
        "boon_of_dimensional_travel",
        "blink_steps",
        "_Blink Steps._ Immediately after you take the Attack action or the Magic action, you can teleport up to 30 feet to an unoccupied space you can see.",
    ),
    cl("boon_of_fate", "category", EPIC_BOON_CATEGORY),
    cl("boon_of_fate", "ability_score_increase", EPIC_ASI),
    cl(
        "boon_of_fate",
        "improve_fate",
        "_Improve Fate._ When you or another creature within 60 feet of you succeeds on or fails a D20 Test, you can roll 2d4 and apply the total rolled as a bonus or penalty to the d20 roll. Once you use this benefit, you can't use it again until you roll Initiative or finish a Short or Long Rest.",
    ),
    cl("boon_of_irresistible_offense", "category", EPIC_BOON_CATEGORY),
    cl(
        "boon_of_irresistible_offense",
        "ability_score_increase",
        "_Ability Score Increase._ Increase your Strength or Dexterity score by 1, to a maximum of 30.",
    ),
    cl(
        "boon_of_irresistible_offense",
        "overcome_defenses",
        "_Overcome Defenses._ The Bludgeoning, Piercing, and Slashing damage you deal always ignores Resistance.",
    ),
    cl(
        "boon_of_irresistible_offense",
        "overwhelming_strike",
        "_Overwhelming Strike._ When you roll a 20 on the d20 for an attack roll, you can deal extra damage to the target equal to the ability score increased by this feat. The extra damage's type is the same as the attack's type.",
    ),
    cl(
        "boon_of_spell_recall",
        "category",
        "_Epic Boon Feat (Prerequisite: Level 19+, Spellcasting Feature)_",
    ),
    cl(
        "boon_of_spell_recall",
        "ability_score_increase",
        "_Ability Score Increase._ Increase your Intelligence, Wisdom, or Charisma score by 1, to a maximum of 30.",
    ),
    cl(
        "boon_of_spell_recall",
        "free_casting",
        "_Free Casting._ Whenever you cast a spell with a level 1–4 spell slot, roll 1d4. If the number you roll is the same as the slot's level, the slot isn't expended.",
    ),
    cl("boon_of_the_night_spirit", "category", EPIC_BOON_CATEGORY),
    cl("boon_of_the_night_spirit", "ability_score_increase", EPIC_ASI),
    cl(
        "boon_of_the_night_spirit",
        "merge_with_shadows",
        "_Merge with Shadows._ While within Dim Light or Darkness, you can give yourself the Invisible condition as a Bonus Action. The condition ends on you immediately after you take an action, a Bonus Action, or a Reaction.",
    ),
    cl(
        "boon_of_the_night_spirit",
        "shadowy_form",
        "_Shadowy Form._ While within Dim Light or Darkness, you have Resistance to all damage except Psychic and Radiant.",
    ),
    cl("boon_of_truesight", "category", EPIC_BOON_CATEGORY),
    cl("boon_of_truesight", "ability_score_increase", EPIC_ASI),
    cl(
        "boon_of_truesight",
        "truesight",
        "_Truesight._ You have Truesight with a range of 60 feet.",
    ),
)

#: (entry, leaf prefix): whole leaves that introduce the rules after them and
#: state none of their own.
FRAMING: tuple[tuple[str, str], ...] = (
    ("backgrounds", "A background includes the following parts."),
    ("species", "A species includes the following parts."),
    *(
        (s, f"As {'an' if label[0] in 'AEIOU' else 'a'} {label}, you have")
        for s, label in SPECIES_ENTRIES
    ),
    ("feat_descriptions", "The description of a feat contains the following parts"),
    *(
        (s, "You gain the following benefits.")
        for s in (
            "alert",
            "magic_initiate",
            "grappler",
            "boon_of_combat_prowess",
            "boon_of_dimensional_travel",
            "boon_of_fate",
            "boon_of_irresistible_offense",
            "boon_of_spell_recall",
            "boon_of_the_night_spirit",
            "boon_of_truesight",
        )
    ),
)

SUBSECTION_HEADING = "subsection heading: names a subsection and states no rule"

#: (entry, exact leaf contents, reason): whole leaves that only name a
#: subsection. The feat category headings name what each feat's own category
#: line states; only headings are excluded.
EXCLUDED: tuple[tuple[str, tuple[str, ...], str], ...] = (
    (
        "backgrounds",
        (
            "### Parts of a Background",
            "#### Ability Scores",
            "#### Feat",
            "#### Skill Proficiencies",
            "#### Tool Proficiency",
            "#### Equipment",
            "### Background Descriptions",
        ),
        SUBSECTION_HEADING,
    ),
    (
        "species",
        (
            "### Parts of a Species",
            "#### Creature Type",
            "#### Size",
            "#### Speed",
            "#### Special Traits",
            "### Species Descriptions",
        ),
        SUBSECTION_HEADING,
    ),
    (
        "feat_descriptions",
        (
            "### Parts of a Feat",
            "### Origin Feats",
            "### General Feats",
            "### Fighting Style Feats",
            "### Epic Boon Feats",
        ),
        SUBSECTION_HEADING,
    ),
)

# ---------------------------------------------------------------------------
# Representation proposed for the clauses above
# ---------------------------------------------------------------------------

C = EntryComponent


def origin(slug: str) -> Target:
    """A *Character Origins* record of this batch."""
    return (CHARACTER_ORIGINS, PLACEMENTS[slug].record_key)


def feat(slug: str) -> Target:
    """A *Feats* record of this batch."""
    return (FEATS, PLACEMENTS[slug].record_key)


BACKGROUNDS_RECORD = origin("backgrounds")
SPECIES_RECORD = origin("species")
FEAT_DESCRIPTIONS_RECORD = feat("feat_descriptions")


def spells(*names: str) -> tuple[tuple[str, Target], ...]:
    """Named spells a rule grants: *Spells* is not authored."""
    return tuple((n, (SPELLS, UNRESOLVED_TARGET)) for n in names)


def equipment(*names: str) -> tuple[tuple[str, Target], ...]:
    """Named equipment, tools, weapon properties and armor categories."""
    return tuple((n, (EQUIPMENT, UNRESOLVED_TARGET)) for n in names)


def classes(*names: str) -> tuple[tuple[str, Target], ...]:
    """Class spell lists and class-feature prerequisites."""
    return tuple((n, (CLASSES, UNRESOLVED_TARGET)) for n in names)


#: Accepted Rules Glossary entries a rule here depends on, by printed name,
#: longest first so "Fly Speed" is not also read as "Speed". A component
#: references each entry once, at its first printed name. "Short or Long Rest"
#: names both rests: it references the Short Rest by the whole phrase and
#: leaves "Long Rest" inside it free, so each printed text has one target.
GLOSSARY_TERMS: tuple[tuple[str, str], ...] = (
    ("Short or Long Rest", "short_rest"),
    ("Temporary Hit Points", "temporary_hit_points"),
    ("Hit Point maximum", "hit_points"),
    ("Hit Points?", "hit_points"),
    ("Long Rest", "long_rest"),
    ("Fly Speed", "fly_speed"),
    ("Speed", "speed"),
    ("[Cc]reature [Tt]ype", "creature_type"),
    ("[Dd]amage [Tt]ype", "damage_types"),
    ("Size", "size"),
    ("Darkvision", "darkvision"),
    ("Tremorsense", "tremorsense"),
    ("Truesight", "truesight"),
    ("Resistance", "resistance"),
    ("Poisoned", "poisoned"),
    ("Charmed", "charmed"),
    ("Frightened", "frightened"),
    ("Grappled", "grappled"),
    ("Prone", "prone"),
    ("Incapacitated", "incapacitated"),
    ("Invisible", "invisible"),
    ("Attack action", "attack"),
    ("Dash action", "dash"),
    ("Hide action", "hide"),
    ("Magic action", "magic"),
    ("Utilize action", "utilize"),
    ("Unarmed Strike", "unarmed_strike"),
    ("Initiative", "initiative"),
    ("attack rolls?", "attack_roll"),
    ("Armor Class", "armor_class"),
    ("carrying capacity", "carrying_capacity"),
    ("unoccupied space", "unoccupied_space"),
)
#: Phrases whose inner names stay readable as references of their own.
OPEN_PHRASES = frozenset({"short_rest"})


def glossary_refs(texts: tuple[str, ...]) -> tuple[tuple[str, Target], ...]:
    """Each accepted glossary entry *texts* print, once, at its first name."""
    found: list[tuple[int, int, str, str]] = []
    for n, text in enumerate(texts):
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


#: Explicit pointers and catalogue members, by component; accepted glossary
#: terms are added from each component's clauses by :func:`glossary_refs`.
EXPLICIT_REFS: dict[tuple[str, str], tuple[tuple[str, Target], ...]] = {
    # -- Character Backgrounds ------------------------------------------------
    ("backgrounds", "feat"): (("Feats", FEAT_DESCRIPTIONS_RECORD),),
    ("backgrounds", "tool_proficiency"): equipment("Artisan's Tools", "Equipment"),
    ("acolyte", "feat"): (("Feats", feat("magic_initiate")),),
    ("acolyte", "tool_proficiency"): equipment("Calligrapher's Supplies"),
    ("acolyte", "equipment"): equipment(
        "Calligrapher's Supplies", "Book", "Holy Symbol", "Parchment", "Robe"
    ),
    ("criminal", "feat"): (("Feats", feat("alert")),),
    ("criminal", "tool_proficiency"): equipment("Thieves' Tools"),
    ("criminal", "equipment"): equipment(
        "Daggers", "Thieves' Tools", "Crowbar", "Pouches", "Traveler's Clothes"
    ),
    ("sage", "feat"): (("Feats", feat("magic_initiate")),),
    ("sage", "tool_proficiency"): equipment("Calligrapher's Supplies"),
    ("sage", "equipment"): equipment(
        "Quarterstaff", "Calligrapher's Supplies", "Book", "Parchment", "Robe"
    ),
    ("soldier", "feat"): (("Feats", feat("savage_attacker")),),
    ("soldier", "tool_proficiency"): equipment("Gaming Set", "Equipment"),
    ("soldier", "equipment"): equipment(
        "Spear",
        "Shortbow",
        "Arrows",
        "Gaming Set",
        "Healer's Kit",
        "Quiver",
        "Traveler's Clothes",
    ),
    # -- Character Species ----------------------------------------------------
    # "Rules Glossary" names the entry the clause describes.
    ("species", "creature_type"): (("Rules Glossary", "creature_type"),),
    ("elf", "elven_lineage"): (
        *spells(
            "Dancing Lights",
            "Faerie Fire",
            "Darkness",
            "Prestidigitation",
            "Detect Magic",
            "Misty Step",
            "Druidcraft",
            "Longstrider",
            "Pass without Trace",
        ),
        *classes("Wizard spell list"),
    ),
    ("gnome", "gnomish_lineage"): spells(
        "Minor Illusion", "Speak with Animals", "Mending", "Prestidigitation"
    ),
    ("human", "versatile"): (("Feats", FEAT_DESCRIPTIONS_RECORD),),
    ("tiefling", "fiendish_legacy"): spells(
        "Poison Spray",
        "Ray of Sickness",
        "Hold Person",
        "Chill Touch",
        "False Life",
        "Ray of Enfeeblement",
        "Fire Bolt",
        "Hellish Rebuke",
        "Darkness",
    ),
    ("tiefling", "otherworldly_presence"): spells("Thaumaturgy"),
    # -- Feats ----------------------------------------------------------------
    ("magic_initiate", "two_cantrips"): classes("Cleric, Druid, or Wizard spell list"),
    **{
        (s, "category"): classes("Fighting Style Feature")
        for s in (
            "archery",
            "defense",
            "great_weapon_fighting",
            "two_weapon_fighting",
        )
    },
    ("boon_of_spell_recall", "category"): classes("Spellcasting Feature"),
    ("archery", "archery"): equipment("Ranged weapons"),
    ("defense", "defense"): equipment("Light, Medium, or Heavy armor"),
    ("great_weapon_fighting", "great_weapon_fighting"): equipment(
        "Melee weapon", "Two-Handed", "Versatile"
    ),
    ("two_weapon_fighting", "two_weapon_fighting"): equipment("Light property"),
}

#: Trait components whose applicability turns on fiction the projection cannot
#: enumerate.
CONTEXTUAL: frozenset[tuple[str, str]] = frozenset(
    {("dwarf", "stonecunning"), ("goliath", "large_form")}
)


def _components() -> tuple[EntryComponent, ...]:
    out = []
    for entry, key, _, texts in CLAUSES:
        explicit = EXPLICIT_REFS.get((entry, key), ())
        stated = {scoped(t) for _, t in explicit}
        refs = explicit + tuple(
            (printed, slug)
            for printed, slug in glossary_refs(texts)
            if scoped(slug) not in stated
        )
        reason = CTX if (entry, key) in CONTEXTUAL else NO_USE
        out.append(C(entry, key, P, reason, refs=refs))
    return tuple(out)


COMPONENTS: tuple[EntryComponent, ...] = _components()

#: (entry, text, component key or ``None`` for record-owned references).
SUPPORTING: tuple[tuple[str, str, str | None], ...] = (
    ("species", SPECIES_GENESIS, "species"),
    ("gnome", ROCK_GNOME_EXAMPLE, "gnomish_lineage"),
    ("human", SKILLED_ADVICE, "versatile"),
)

#: Record-owned references: (entry, printed text, target, texts of the spans the
#: pointer is read from). The Human's advice names a feat of this batch.
RECORD_REFERENCES: tuple[RecordReference, ...] = (
    ("human", "Skilled", feat("skilled"), (SKILLED_ADVICE,)),
)

#: Targets outside this batch that no accepted record defines and this batch
#: does not author. Each citation would be an expected unknown-target finding.
NEW_TARGETS: tuple[Target, ...] = ()


def accepted_context_targets() -> tuple[Target, ...]:
    """The accepted glossary entries this batch's components cite."""
    return tuple(
        sorted(
            {t for c in COMPONENTS for _, t in c.refs if isinstance(t, str)},
        )
    )


def batch() -> EntryBatch:
    """The tables above, read at call time so tests can mutate them."""
    return EntryBatch(
        origin=ORIGIN,
        proposal_origin=f"{ORIGIN} (CRD Issue 5d character-origins-feats batch; unaccepted)",
        unit_prefix="character-origins-feats",
        parent=PARENT,
        entries=ENTRIES,
        expected_leaves=208,
        clauses=CLAUSES,
        framing=FRAMING,
        components=COMPONENTS,
        supporting=SUPPORTING,
        record_references=RECORD_REFERENCES,
        placements=PLACEMENTS,
        excluded=EXCLUDED,
        members=MEMBERS,
    )


def build(session: Session) -> Built:
    """Derive the character-origins-feats proposal from the release *session* published."""
    return build_entry_batch(session, batch(), published_release_binding(session))


def unresolved() -> list[tuple[str, str]]:
    """Printed pointers whose destination has no record yet, as (scope, text).

    Each stays unresolved, alone and composed, until a reviewed resolution
    names it. A name printed by several components is each one's reference.
    """
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
#: Three accepted citations in ``character_creation.create_your_character``
#: print a part this batch authors and stay unresolved. A resolution may name
#: only an accepted destination, so each draft becomes applicable only once
#: its target is accepted, and then only by its own authorized
#: ``resolve_references`` action. Nothing here records or applies any.
#:
#: Each destination is the section its clause's wording names, not a
#: subsection picked for convenience, and each is the one record that owns
#: that section's own text. The entries the section prints are records of
#: their own and its ``CATALOGUE_MEMBER`` entries (``MEMBERS``): a consumer that
#: selects the destination reads the section with every member, and each
#: member keeps its own category, prerequisite and eligibility.
#:
#: ``choose_background``: "You can choose any of the backgrounds detailed in
#: "Character Origins"" -- the *Character Backgrounds* section.
CHOOSE_BACKGROUND_RESOLUTION_ID = "resolve-choose-background-character-origins-1"
#: The span the accepted citation's REFERENCE provenance cites.
CHOOSE_BACKGROUND_POINTER_SPAN = "9051aa97-c4d4-5640-9d82-6f011e776a15"
#: ``choose_species``: "The following species options are detailed in
#: "Character Origins": Dragonborn, ... Tiefling" -- the *Character Species*
#: section.
CHOOSE_SPECIES_RESOLUTION_ID = "resolve-choose-species-character-origins-1"
CHOOSE_SPECIES_POINTER_SPAN = "e0bfa3fa-8494-5b9e-a8da-a742ea5b6923"
#: ``background_feat``: "Feats are detailed in "Feats."" -- *Feat
#: Descriptions*, the part's only section, which defines what a feat's parts
#: and categories are.
BACKGROUND_FEAT_RESOLUTION_ID = "resolve-background-feat-feats-1"
BACKGROUND_FEAT_POINTER_SPAN = "d131ec53-eaef-593a-9bdf-47800204accd"

CREATE_YOUR_CHARACTER = "character_creation.create_your_character"


def _draft(
    resolution_id: str,
    component: str,
    text: str,
    target: Target,
    span: str,
    binding: ReleaseBinding,
) -> ReferenceResolution:
    scope, key = scoped(target)
    return ReferenceResolution(
        resolution_id=resolution_id,
        from_record_key=CREATE_YOUR_CHARACTER,
        from_component_key=component,
        source_text=text,
        scope_key=scope,
        target_record_key=key,
        release_binding=binding,
        provenance_span_ids=(span,),
    )


def draft_choose_background_resolution(binding: ReleaseBinding) -> ReferenceResolution:
    """The pending background resolution, drafted for review against *binding*."""
    return _draft(
        CHOOSE_BACKGROUND_RESOLUTION_ID,
        "choose_background",
        "Character Origins",
        BACKGROUNDS_RECORD,
        CHOOSE_BACKGROUND_POINTER_SPAN,
        binding,
    )


def draft_choose_species_resolution(binding: ReleaseBinding) -> ReferenceResolution:
    """The pending species resolution, drafted for review against *binding*."""
    return _draft(
        CHOOSE_SPECIES_RESOLUTION_ID,
        "choose_species",
        "Character Origins",
        SPECIES_RECORD,
        CHOOSE_SPECIES_POINTER_SPAN,
        binding,
    )


def draft_background_feat_resolution(binding: ReleaseBinding) -> ReferenceResolution:
    """The pending background-feat resolution, drafted for review against *binding*."""
    return _draft(
        BACKGROUND_FEAT_RESOLUTION_ID,
        "background_feat",
        "Feats",
        FEAT_DESCRIPTIONS_RECORD,
        BACKGROUND_FEAT_POINTER_SPAN,
        binding,
    )


def main(db: str) -> int:
    out = Path(__file__).resolve().parent / PROPOSAL_FILE
    return emit(db, build, out, expected_representation_findings())


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
