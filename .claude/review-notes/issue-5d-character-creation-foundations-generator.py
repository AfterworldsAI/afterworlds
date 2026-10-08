# ruff: noqa: E501  -- clause literals are verbatim source text, kept whole to be greppable
"""Author the **character-creation-foundations** proposal: the whole *Character
Creation* part and the five Rules Glossary foundations *Stat Block* cites.

REVIEW MATERIAL for CRD Issue 5d (#137) over the qualified 5c release
``9717e288-c099-5217-b2d2-f89aeabd7b73`` / ``5.2.1-corpus.883aabdf-462``. It
emits an *unaccepted* ``5d-proposal-2`` artifact. It accepts nothing, publishes
nothing, writes nothing under ``oracles/``, records no reference resolution,
and imports no earlier batch's content, identity or authority: every leaf is
read afresh from the release.

Scope, 179 leaves, eleven records, one review unit each:

* the six ``##`` sections of *Character Creation* (pp19-27), each one
  ``SECTION`` record keyed ``character_creation.<section>``: *Choose a
  Character Sheet* (2 leaves), *Create Your Character* (97: all five steps and
  their tables), *Level Advancement* (22: the Character Advancement table,
  Gaining a Level, Tiers of Play with each tier's level range), *Starting at Higher Levels* (9), *Multiclassing*
  (33, with the Multiclass Spellcaster table) and *Trinkets* (3, all 100 rows).
  The part title ``# Character Creation`` states no rule and belongs to no
  section, as ``# Playing the Game`` belongs to none;
* the Rules Glossary entries *Alignment* (2), *Creature Type* (4),
  *Experience Points* (2), *Passive Perception* (3) and *Size* (2), the five
  targets the accepted ``glossary.stat_block`` cites and no accepted record
  defines.

Kinds: a section about making a level 1 character is ``character_creation``;
*Level Advancement* and *Multiclassing*, which apply as a character gains
levels, are ``character_advancement``. *Starting at Higher Levels* combines
both but is a way of creating a character. *Trinkets* is rolled "when you make
your character"; that the GM may also use the table stays in its prose.

This file is literal review data only; the assembly is the committed shared
:mod:`afterworlds.ingestion.mechanical.authoring`. ``CLAUSES`` is the source
review; ``COMPONENTS`` is the representation proposed for it; expected rules
come from ``CLAUSES`` alone.

Authoring conventions (as the ten accepted batches):

* Every component is prose-bound. No closed family states an XP threshold, a
  point-buy cost, a background's ability adjustment, a derived score
  (Passive Perception, attack bonus, spell save DC), a class-keyed hit point
  value, a starting-equipment allowance, a multiclass prerequisite or a
  trinket. The Character Advancement table's Proficiency Bonus column restates
  the accepted ``play.proficiency`` bands and the Ability Scores and Modifiers
  table restates ``play.six_abilities``: one source statement, one typed copy.
* The Multiclass Spellcaster table stays prose. ``SpellSlotProgressionFact``
  indexes its row by *character level*; this table's row is the total of the
  multiclass spellcaster arithmetic (full levels plus half Paladin and Ranger
  levels, rounded up), not the character level, so the family would misstate
  the index. Faithful prose is the in-scope choice: no consumer requires
  typed multiclass slots, and no schema is added.
* A condition the closed vocabulary cannot state stays in the same
  component's governing prose, beside what it conditions: the Multiclassing
  *Spellcasting* scope ("Once you have the Spellcasting feature from more than
  one class, use the rules below") is one component with the prepared-spell,
  cantrip and spell-slot rules it governs; *Pact Magic* states its own
  condition and is its own component.
* Gamemaster latitude (``gamemaster_latitude``) is kept where the source
  delegates to the GM; the character-creation and advancement contexts are
  kept by record, never merged.
* Examples, sidebar titles and *See also* pointers are supporting spans of
  the component they illustrate or of the record.
* References: every explicit pointer. A pointer to a record of this batch
  names it. A pointer to a part this batch does not author ("Classes",
  "Character Origins", "Feats", "Equipment", "Playing the Game") is a
  reference in that part's scope with no target, reported unresolved. The
  Character Advancement table, named twice in *Multiclassing*, is the table of
  ``character_creation.level_advancement`` and is referenced there. Terms only
  mentioned (character-sheet fields, Death Saving Throws, Hit Point Dice,
  Temporary Hit Points, class features by name) stay unreferenced; the one
  accepted glossary term a rule here depends on, *Short Rest*, is referenced.

Two accepted citations print "Character Creation" and stay unresolved. This
part now makes each faithfully resolvable, so two unrecorded resolution drafts
are given below for the same Owner packet; nothing here records or applies
them, and the recorded attack-roll resolution is untouched.

Run: ``python issue-5d-character-creation-foundations-generator.py <published afterworlds.db>``
"""

from __future__ import annotations

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
from afterworlds.ingestion.mechanical.representation import RecordKind
from afterworlds.ingestion.mechanical.schema_lift import (
    SCHEMA_15_HASH,
    SCHEMA_15_VERSION,
)

ORIGIN = "issue-5d-character-creation-foundations-generator.py"
PROPOSAL_FILE = "issue-5d-character-creation-foundations-PROPOSAL.json"
PARENT = ("Rules Glossary", "Rules Definitions")
#: The parts this batch's records and pointers name, formed from the release's
#: own part names under the ``<release-family>/<section-slug>`` convention.
CHARACTER_CREATION = "srd-5.2.1/character-creation"
PLAY = "srd-5.2.1/playing-the-game"
CLASSES = "srd-5.2.1/classes"
CHARACTER_ORIGINS = "srd-5.2.1/character-origins"
FEATS = "srd-5.2.1/feats"
EQUIPMENT = "srd-5.2.1/equipment"
#: The target of a printed pointer whose destination has no record yet. It is
#: reported as ``unresolved reference`` until a reviewed resolution names one;
#: naming a key here would guess at a record nobody has authored.
UNRESOLVED_TARGET = ""

#: (record slug, printed container label, record kind), in printed order.
ENTRIES: tuple[tuple[str, str, RecordKind], ...] = (
    ("character_sheet", "Choose a Character Sheet", RecordKind.CHARACTER_CREATION),
    ("create_your_character", "Create Your Character", RecordKind.CHARACTER_CREATION),
    ("level_advancement", "Level Advancement", RecordKind.CHARACTER_ADVANCEMENT),
    (
        "starting_at_higher_levels",
        "Starting at Higher Levels",
        RecordKind.CHARACTER_CREATION,
    ),
    ("multiclassing", "Multiclassing", RecordKind.CHARACTER_ADVANCEMENT),
    ("trinkets", "Trinkets", RecordKind.CHARACTER_CREATION),
    ("alignment", "Alignment", RecordKind.GLOSSARY_RULE),
    ("creature_type", "Creature Type", RecordKind.GLOSSARY_RULE),
    ("experience_points", "Experience Points", RecordKind.GLOSSARY_RULE),
    ("passive_perception", "Passive Perception", RecordKind.GLOSSARY_RULE),
    ("size", "Size", RecordKind.GLOSSARY_RULE),
)

#: The six *Character Creation* sections, one record each.
PLACEMENTS: dict[str, Placement] = {
    slug: Placement(
        f"character_creation.{slug}",
        ("Character Creation", label),
        f"## {label}",
    )
    for slug, label, _ in ENTRIES[:6]
}

# ---------------------------------------------------------------------------
# Reason codes and handling
# ---------------------------------------------------------------------------
CTX = "contextual_applicability"
GM = "gamemaster_latitude"
NO_USE = "no_identified_structured_use"
P = ComponentHandling.PROSE_BOUND
PROSE = None

# ---------------------------------------------------------------------------
# Table leaves, written as their rows
# ---------------------------------------------------------------------------
CLASS_OVERVIEW_TABLE = html_table(
    "Class Overview",
    ("Class", "Likes ...", "Primary Ability", "Complexity"),
    [
        ("Barbarian", "Battle", "Strength", "Average"),
        ("Bard", "Performing", "Charisma", "High"),
        ("Cleric", "Gods", "Wisdom", "Average"),
        ("Druid", "Nature", "Wisdom", "High"),
        ("Fighter", "Weapons", "Strength or Dexterity", "Low"),
        ("Monk", "Unarmed combat", "Dexterity and Wisdom", "High"),
        ("Paladin", "Defense", "Strength and Charisma", "Average"),
        ("Ranger", "Survival", "Dexterity and Wisdom", "Average"),
        ("Rogue", "Stealth", "Dexterity", "Low"),
        ("Sorcerer", "Power", "Charisma", "High"),
        ("Warlock", "Occult lore", "Charisma", "High"),
        ("Wizard", "Spellbooks", "Intelligence", "Average"),
    ],
)

ABILITY_SCORES_AND_BACKGROUNDS_TABLE = html_table(
    "Ability Scores and Backgrounds",
    ("Ability", "Background"),
    [
        ("Strength", "Soldier"),
        ("Dexterity", "Soldier"),
        ("Constitution", "Soldier"),
        ("Intelligence", "Acolyte"),
        ("Wisdom", "Acolyte"),
        ("Charisma", "Acolyte"),
    ],
)

STANDARD_LANGUAGES_TABLE = html_table(
    "Standard Languages",
    ("1d12", "Language"),
    [
        ("—", "Common"),
        ("1", "Common Sign Language"),
        ("2", "Draconic"),
        ("3–4", "Dwarvish"),
        ("5–6", "Elvish"),
        ("7", "Giant"),
        ("8", "Gnomish"),
        ("9", "Goblin"),
        ("10–11", "Halfling"),
        ("12", "Orc"),
    ],
)

RARE_LANGUAGES_TABLE = html_table(
    "Rare Languages",
    ("Language", "Language"),
    [
        ("Abyssal", "Primordial*"),
        ("Celestial", "Sylvan"),
        ("Deep Speech", "Thieves' Cant"),
        ("Druidic", "Undercommon"),
        ("Infernal", ""),
    ],
)

ABILITY_SCORE_POINT_COSTS_TABLE = html_table(
    "Ability Score Point Costs",
    ("Score", "Cost", "Score", "Cost"),
    [
        ("8", "0", "12", "4"),
        ("9", "1", "13", "5"),
        ("10", "2", "14", "7"),
        ("11", "3", "15", "9"),
    ],
)

STANDARD_ARRAY_BY_CLASS_TABLE = html_table(
    "Standard Array by Class",
    ("Class", "Str.", "Dex.", "Con.", "Int.", "Wis.", "Cha."),
    [
        ("Barbarian", "15", "13", "14", "10", "12", "8"),
        ("Bard", "8", "14", "12", "13", "10", "15"),
        ("Cleric", "14", "8", "13", "10", "15", "12"),
        ("Druid", "8", "12", "14", "13", "15", "10"),
        ("Fighter", "15", "14", "13", "8", "10", "12"),
        ("Monk", "12", "15", "13", "10", "14", "8"),
        ("Paladin", "15", "10", "13", "8", "12", "14"),
        ("Ranger", "12", "15", "13", "8", "14", "10"),
        ("Rogue", "12", "15", "13", "14", "10", "8"),
        ("Sorcerer", "10", "13", "14", "8", "12", "15"),
        ("Warlock", "8", "14", "13", "12", "10", "15"),
        ("Wizard", "8", "12", "13", "15", "14", "10"),
    ],
)

ABILITY_SCORES_AND_MODIFIERS_TABLE = html_table(
    "Ability Scores and Modifiers",
    ("Score", "Modifier", "Score", "Modifier"),
    [
        ("3", "−4", "12–13", "+1"),
        ("4–5", "−3", "14–15", "+2"),
        ("6–7", "−2", "16–17", "+3"),
        ("8–9", "−1", "18–19", "+4"),
        ("10–11", "+0", "20", "+5"),
    ],
)

LEVEL_1_HIT_POINTS_BY_CLASS_TABLE = html_table(
    "Level 1 Hit Points by Class",
    ("Class", "Hit Point Maximum"),
    [
        ("Barbarian", "12 + Con. modifier"),
        ("Fighter, Paladin, or Ranger", "10 + Con. modifier"),
        ("Bard, Cleric, Druid, Monk, Rogue, or Warlock", "8 + Con. modifier"),
        ("Sorcerer or Wizard", "6 + Con. modifier"),
    ],
)

CHARACTER_ADVANCEMENT_TABLE = html_table(
    "Character Advancement",
    ("Level", "Experience Points", "Proficiency Bonus"),
    [
        ("1", "0", "+2"),
        ("2", "300", "+2"),
        ("3", "900", "+2"),
        ("4", "2,700", "+2"),
        ("5", "6,500", "+3"),
        ("6", "14,000", "+3"),
        ("7", "23,000", "+3"),
        ("8", "34,000", "+3"),
        ("9", "48,000", "+4"),
        ("10", "64,000", "+4"),
        ("11", "85,000", "+4"),
        ("12", "100,000", "+4"),
        ("13", "120,000", "+5"),
        ("14", "140,000", "+5"),
        ("15", "165,000", "+5"),
        ("16", "195,000", "+5"),
        ("17", "225,000", "+6"),
        ("18", "265,000", "+6"),
        ("19", "305,000", "+6"),
        ("20", "355,000", "+6"),
    ],
)

FIXED_HIT_POINTS_BY_CLASS_TABLE = html_table(
    "Fixed Hit Points by Class",
    ("Class", "Hit Points per Level"),
    [
        ("Barbarian", "7 + Con. modifier"),
        ("Fighter, Paladin, or Ranger", "6 + Con. modifier"),
        ("Bard, Cleric, Druid, Monk, Rogue, or Warlock", "5 + Con. modifier"),
        ("Sorcerer or Wizard", "4 + Con. modifier"),
    ],
)

STARTING_EQUIPMENT_AT_HIGHER_LEVELS_TABLE = html_table(
    "Starting Equipment at Higher Levels",
    ("Starting Level", "Equipment and Money", "Magic Items"),
    [
        ("2–4", "Normal starting equipment", "1 Common"),
        (
            "5–10",
            "500 GP plus 1d10 × 25 GP plus normal starting equipment",
            "1 Common, 1 Uncommon",
        ),
        (
            "11–16",
            "5,000 gp plus 1d10 × 250 GP plus normal starting equipment",
            "2 Common, 3 Uncommon, 1 Rare",
        ),
        (
            "17–20",
            "20,000 GP plus 1d10 × 250 GP plus normal starting equipment",
            "2 Common, 4 Uncommon, 3 Rare, 1 Very Rare",
        ),
    ],
)

MULTICLASS_SPELLCASTER_TABLE = html_table(
    "Multiclass Spellcaster: Spell Slots per Spell Level",
    ("Level", "1", "2", "3", "4", "5", "6", "7", "8", "9"),
    [
        ("1", "2", "—", "—", "—", "—", "—", "—", "—", "—"),
        ("2", "3", "—", "—", "—", "—", "—", "—", "—", "—"),
        ("3", "4", "2", "—", "—", "—", "—", "—", "—", "—"),
        ("4", "4", "3", "—", "—", "—", "—", "—", "—", "—"),
        ("5", "4", "3", "2", "—", "—", "—", "—", "—", "—"),
        ("6", "4", "3", "3", "—", "—", "—", "—", "—", "—"),
        ("7", "4", "3", "3", "1", "—", "—", "—", "—", "—"),
        ("8", "4", "3", "3", "2", "—", "—", "—", "—", "—"),
        ("9", "4", "3", "3", "3", "1", "—", "—", "—", "—"),
        ("10", "4", "3", "3", "3", "2", "—", "—", "—", "—"),
        ("11", "4", "3", "3", "3", "2", "1", "—", "—", "—"),
        ("12", "4", "3", "3", "3", "2", "1", "—", "—", "—"),
        ("13", "4", "3", "3", "3", "2", "1", "1", "—", "—"),
        ("14", "4", "3", "3", "3", "2", "1", "1", "—", "—"),
        ("15", "4", "3", "3", "3", "2", "1", "1", "1", "—"),
        ("16", "4", "3", "3", "3", "2", "1", "1", "1", "—"),
        ("17", "4", "3", "3", "3", "2", "1", "1", "1", "1"),
        ("18", "4", "3", "3", "3", "3", "1", "1", "1", "1"),
        ("19", "4", "3", "3", "3", "3", "2", "1", "1", "1"),
        ("20", "4", "3", "3", "3", "3", "2", "2", "1", "1"),
    ],
)

TRINKETS_TABLE = html_table(
    "Trinkets",
    ("1d100", "Trinket"),
    [
        ("01", "A mummified goblin hand"),
        ("02", "A crystal that faintly glows in moonlight"),
        ("03", "A gold coin minted in an unknown land"),
        ("04", "A diary written in a language you don't know"),
        ("05", "A brass ring that never tarnishes"),
        ("06", "An old chess piece made from glass"),
        (
            "07",
            "A pair of knucklebone dice, each with a skull symbol on the side that would normally show six pips",
        ),
        (
            "08",
            "A small idol depicting a nightmarish creature that gives you unsettling dreams when you sleep near it",
        ),
        ("09", "A lock of someone's hair"),
        ("10", "The deed for a parcel of land in a realm unknown to you"),
        ("11", "A 1-ounce block made from an unknown material"),
        ("12", "A small cloth doll skewered with needles"),
        ("13", "A tooth from an unknown beast"),
        ("14", "An enormous scale, perhaps from a dragon"),
        ("15", "A bright-green feather"),
        ("16", "An old divination card bearing your likeness"),
        ("17", "A glass orb filled with moving smoke"),
        ("18", "A 1-pound egg with a bright-red shell"),
        ("19", "A pipe that blows bubbles"),
        ("20", "A glass jar containing a bit of flesh floating in pickling fluid"),
        (
            "21",
            "A gnome-crafted music box that plays a song you dimly remember from your childhood",
        ),
        ("22", "A wooden statuette of a smug halfling"),
        ("23", "A brass orb etched with strange runes"),
        ("24", "A multicolored stone disk"),
        ("25", "A silver icon of a raven"),
        ("26", "A bag containing forty-seven teeth, one of which is rotten"),
        ("27", "A shard of obsidian that always feels warm to the touch"),
        ("28", "A dragon's talon strung on a leather necklace"),
        ("29", "A pair of old socks"),
        (
            "30",
            "A blank book whose pages refuse to hold ink, chalk, graphite, or any other marking",
        ),
        ("31", "A silver badge that is a five-pointed star"),
        ("32", "A knife that belonged to a relative"),
        ("33", "A glass vial filled with nail clippings"),
        (
            "34",
            "A rectangular metal device with two tiny metal cups on one end that throws sparks when wet",
        ),
        ("35", "A white, sequined glove sized for a human"),
        ("36", "A vest with one hundred tiny pockets"),
        ("37", "A weightless stone"),
        ("38", "A sketch of a goblin"),
        ("39", "An empty glass vial that smells of perfume"),
        (
            "40",
            "A gemstone that looks like a lump of coal when examined by anyone but you",
        ),
        ("41", "A scrap of cloth from an old banner"),
        ("42", "A rank insignia from a lost legionnaire"),
        ("43", "A silver bell without a clapper"),
        ("44", "A mechanical canary inside a lamp"),
        (
            "45",
            "A miniature chest carved to look like it has numerous feet on the bottom",
        ),
        ("46", "A dead sprite inside a clear glass bottle"),
        (
            "47",
            "A metal can that has no opening but sounds as if it is filled with liquid, sand, spiders, or broken glass (your choice)",
        ),
        ("48", "A glass orb filled with water, in which swims a clockwork goldfish"),
        ("49", "A silver spoon with an M engraved on the handle"),
        ("50", "A whistle made from gold-colored wood"),
        ("51", "A dead scarab beetle the size of your hand"),
        ("52", "Two toy soldiers, one missing a head"),
        ("53", "A small box filled with different-sized buttons"),
        ("54", "A candle that can't be lit"),
        ("55", "A miniature cage with no door"),
        ("56", "An old key"),
        ("57", "An indecipherable treasure map"),
        ("58", "A hilt from a broken sword"),
        ("59", "A rabbit's foot"),
        ("60", "A glass eye"),
        ("61", "A cameo of a hideous person"),
        ("62", "A silver skull the size of a coin"),
        ("63", "An alabaster mask"),
        ("64", "A cone of sticky black incense that stinks"),
        ("65", "A nightcap that gives you pleasant dreams when you wear it"),
        ("66", "A single caltrop made from bone"),
        ("67", "A gold monocle frame without the lens"),
        ("68", "A 1-inch cube, each side a different color"),
        ("69", "A crystal doorknob"),
        ("70", "A packet filled with pink dust"),
        (
            "71",
            "A fragment of a beautiful song, written as musical notes on two pieces of parchment",
        ),
        ("72", "A silver teardrop earring containing a real teardrop"),
        ("73", "An eggshell painted with scenes of misery in disturbing detail"),
        ("74", "A fan that, when unfolded, shows a sleepy cat"),
        ("75", "A set of bone pipes"),
        (
            "76",
            "A four-leaf clover pressed inside a book discussing manners and etiquette",
        ),
        ("77", "A sheet of parchment upon which is drawn a mechanical contraption"),
        ("78", "An ornate scabbard that fits no blade you have found"),
        ("79", "An invitation to a party where a murder happened"),
        ("80", "A bronze pentacle with an etching of a rat's head in its center"),
        ("81", "A purple handkerchief embroidered with the name of an archmage"),
        ("82", "Half a floor plan for a temple, a castle, or another structure"),
        ("83", "A bit of folded cloth that, when unfolded, turns into a stylish cap"),
        ("84", "A receipt of deposit at a bank in a far-off city"),
        ("85", "A diary with seven missing pages"),
        ("86", 'An empty silver snuffbox bearing the inscription "dreams" on its lid'),
        ("87", "An iron holy symbol devoted to an unknown god"),
        (
            "88",
            "A book about a legendary hero's rise and fall, with the last chapter missing",
        ),
        ("89", "A vial of dragon blood"),
        ("90", "An ancient arrow of elven design"),
        ("91", "A needle that never bends"),
        ("92", "An ornate brooch of dwarven design"),
        (
            "93",
            'An empty wine bottle bearing a pretty label that says, "The Wizard of Wines Winery, Red Dragon Crush, 331422-W"',
        ),
        ("94", "A mosaic tile with a multicolored, glazed surface"),
        ("95", "A petrified mouse"),
        ("96", "A black pirate flag adorned with a dragon's skull and crossbones"),
        (
            "97",
            "A tiny mechanical crab or spider that moves about when it's not being observed",
        ),
        ("98", 'A glass jar containing lard with a label that reads, "Griffon Grease"'),
        (
            "99",
            "A wooden box with a ceramic bottom that holds a living worm with a head on each end of its body",
        ),
        ("00", "A metal urn containing the ashes of a hero"),
    ],
)

CREATURE_TYPE_TABLE = "<table>\n  <tbody>\n    <tr>\n      <td>Aberration</td>\n      <td>Elemental</td>\n      <td>Monstrosity</td>\n    </tr>\n    <tr>\n      <td>Beast</td>\n      <td>Fey</td>\n      <td>Ooze</td>\n    </tr>\n    <tr>\n      <td>Celestial</td>\n      <td>Fiend</td>\n      <td>Plant</td>\n    </tr>\n    <tr>\n      <td>Construct</td>\n      <td>Giant</td>\n      <td>Undead</td>\n    </tr>\n    <tr>\n      <td>Dragon</td>\n      <td>Humanoid</td>\n      <td></td>\n    </tr>\n  </tbody>\n</table>"
RARE_LANGUAGES_FOOTNOTE = "\\*Primordial includes the Aquan, Auran, Ignan, and Terran dialects. Creatures that know one of these dialects can communicate with those that know a different one."

#: (entry, component key, expected fact families + ``None`` for governing
#: prose, clause texts). Every rule-stating sentence of the batch is named here.
CLAUSES: tuple[tuple[str, str, tuple[str | None, ...], tuple[str, ...]], ...] = (
    # == Choose a Character Sheet (p19) =======================================
    (
        "character_sheet",
        "character_sheet",
        (PROSE,),
        (
            "You'll record the main details of your character on a character sheet. Throughout this chapter, we use the term \"character sheet\" to mean whatever you use to track your character's details, whether it's a printed character sheet, a digital character sheet, or plain paper. Choose whichever style of sheet works for you, and then embark on creating a character!",
        ),
    ),
    # == Create Your Character (pp19-23) ======================================
    (
        "create_your_character",
        "creation_steps",
        (PROSE,),
        (
            "1. **Choose a Class.** Every adventurer is a member of a class. A class broadly describes a character's vocation, special talents, and favored tactics.\n2. **Determine Origin.** A character's origin includes two elements: background and species. How did the character spend the years leading up to a life of adventure? Who are the character's ancestors? You can also choose your character's languages.\n3. **Determine Ability Scores.** Much of what your character does in the game depends on the character's six abilities.\n4. **Choose an Alignment.** Alignment is a shorthand for your character's moral compass.\n5. **Fill in Details.** Using the choices you've made, fill in the remaining details on your character sheet.",
        ),
    ),
    # -- Step 1: Choose Class --------------------------------------------------
    (
        "create_your_character",
        "choose_class",
        (PROSE,),
        (
            'Choose a class, and write it on your character sheet. The Class Overview table summarizes the classes. See "Classes" for the classes\' details.',
            CLASS_OVERVIEW_TABLE,
        ),
    ),
    (
        "create_your_character",
        "write_level",
        (PROSE,),
        (
            "Write your character's level on your character sheet. Typically, a character starts at level 1 and advances in level by adventuring and gaining Experience Points (XP).",
        ),
    ),
    (
        "create_your_character",
        "write_xp",
        (PROSE,),
        (
            "_Write Your XP._ Also record your Experience Points. A level 1 character has 0 XP.",
        ),
    ),
    (
        "create_your_character",
        "starting_at_a_higher_level",
        (PROSE,),
        (
            '_Starting at a Higher Level._ Your GM might start you at a higher level. If you start at level 3 or higher, write your chosen subclass on your character sheet. See the "Starting at Higher Levels" section later in "Character Creation" for more information.',
        ),
    ),
    (
        "create_your_character",
        "armor_training",
        (PROSE,),
        (
            'Your class might give you training with certain categories of armor. Note your armor training on your character sheet. Armor training with a kind of armor means you can wear that armor effectively, gaining defensive bonuses from it. The categories of armor are described in "Equipment."',
        ),
    ),
    # -- Step 2: Character Origin ----------------------------------------------
    (
        "create_your_character",
        "origin",
        (PROSE,),
        (
            "Determining your character's origin involves choosing a background, a species, and two languages.",
            "A character's background represents the place and occupation that were most formative for the character. The combination of background, species, and languages provides fertile soil for your imagination as you ponder your character's earliest days.",
        ),
    ),
    (
        "create_your_character",
        "choose_background",
        (PROSE,),
        (
            'Choose your character\'s background, and write it on your character sheet. You can choose any of the backgrounds detailed in "Character Origins," and your GM might offer additional backgrounds as options.',
        ),
    ),
    (
        "create_your_character",
        "background_ability_scores",
        (PROSE,),
        (
            "The background you choose influences step 3, when you determine your character's ability scores. If you're having trouble choosing, the Ability Scores and Backgrounds table shows which backgrounds benefit which ability scores. Look for your class's primary ability there.",
            ABILITY_SCORES_AND_BACKGROUNDS_TABLE,
        ),
    ),
    (
        "create_your_character",
        "background_feat",
        (PROSE,),
        (
            '_Record Your Feat._ A background gives you a feat, which grants your character particular capabilities. Feats are detailed in "Feats." Write the feat on your character sheet.',
        ),
    ),
    (
        "create_your_character",
        "background_proficiencies",
        (PROSE,),
        (
            "_Note Proficiencies._ Your background gives proficiency in two skills and with one tool. Record this information on your character sheet.",
        ),
    ),
    (
        "create_your_character",
        "class_proficiencies",
        (PROSE,),
        (
            'Your class also gives proficiencies. Check your class description in "Classes" and note the proficiencies on your character sheet.',
        ),
    ),
    (
        "create_your_character",
        "starting_proficiency_bonus",
        (PROSE,),
        (
            'The features table in your class description shows your Proficiency Bonus (described in "Playing the Game"), which is +2 for a level 1 character. Note this number on your character sheet. You\'ll fill in other numbers connected to these proficiencies in step 5.',
        ),
    ),
    (
        "create_your_character",
        "starting_equipment",
        (PROSE,),
        (
            'Your background and class both provide starting equipment. Any coins that you gain at this step can be immediately spent on equipment from "Equipment."',
            'Record your chosen equipment on your character sheet. Equipment is described in "Equipment," but for now you can just write it all down and look up the specifics in "Equipment" later. Note any coins you have left after purchasing your equipment.',
        ),
    ),
    (
        "create_your_character",
        "choose_species",
        (PROSE,),
        (
            "Choose a species for your character. The following species options are detailed in \"Character Origins\": Dragonborn, Dwarf, Elf, Gnome, Goliath, Halfling, Human, Orc, and Tiefling. Once you've chosen a species, write it on your character sheet. Then record your species' traits.",
            "Your character's size and Speed are determined by the character's species; record these in the appropriate places on your character sheet as well (you may write just the first letter of your size).",
        ),
    ),
    (
        "create_your_character",
        "past_and_present",
        (PROSE,),
        (
            "Let your character's background and species inspire how you imagine their past. That past fed into the character's present. With that in mind, consider answers to the following questions as your character:",
            "- Who raised you?\n- Who was your dearest childhood friend?\n- Did you grow up with a pet?\n- Have you fallen in love? If so, with whom?\n- Did you join an organization, such as a guild or religion? If so, are you still a member of it?\n- What elements of your past inspire you to go on adventures now?",
        ),
    ),
    (
        "create_your_character",
        "languages",
        (PROSE,),
        (
            "Your character knows at least three languages: Common plus two languages you roll or choose from the Standard Languages table. Knowledge of a language means your character can communicate in it, read it, and write it. Your class and other features might also give you languages.",
        ),
    ),
    (
        "create_your_character",
        "standard_languages",
        (PROSE,),
        (
            "The Standard Languages table lists languages that are widespread in the setting. Every player character knows Common. The other standard languages originated with the first members of the most prominent species in the setting and have since spread widely.",
            STANDARD_LANGUAGES_TABLE,
        ),
    ),
    # The footnote is printed under the table in the same leaf and qualifies
    # its Primordial row, so it is a clause of the same component.
    (
        "create_your_character",
        "rare_languages",
        (PROSE,),
        (
            "The Rare Languages table lists languages that are either secret or derived from other planes of existence and thus less widespread in the worlds of the Material Plane. Some features let a character learn a rare language.",
            RARE_LANGUAGES_TABLE,
            RARE_LANGUAGES_FOOTNOTE,
        ),
    ),
    # -- Step 3: Ability Scores ------------------------------------------------
    (
        "create_your_character",
        "determine_ability_scores",
        (PROSE,),
        (
            'To determine your character\'s ability scores, you first generate a set of six numbers using the instructions below and then assign them to your six abilities. "Playing the Game" explains what each ability means.',
        ),
    ),
    # The lead governs the three methods, so they are one component's prose.
    (
        "create_your_character",
        "generate_scores",
        (PROSE,),
        (
            "Determine your ability scores by using one of the following three methods. Your GM might prefer you to use a particular one.",
            "_Standard Array._ Use the following six scores for your abilities: 15, 14, 13, 12, 10, 8.",
            "_Random Generation._ Roll four d6s and record the total of the highest three dice. Do this five more times, so you have six numbers.",
            "_Point Cost._ You have 27 points to spend on your ability scores. The cost of each score is shown on the Ability Score Point Costs table.",
            ABILITY_SCORE_POINT_COSTS_TABLE,
        ),
    ),
    (
        "create_your_character",
        "assign_scores",
        (PROSE,),
        (
            "Once you've generated six scores, assign them to Strength, Dexterity, Constitution, Intelligence, Wisdom, and Charisma, keeping in mind your class's primary ability. Fill in the ability modifiers as well.",
        ),
    ),
    (
        "create_your_character",
        "standard_array_by_class",
        (PROSE,),
        (
            "If you're using the Standard Array option, consult the Standard Array by Class table for suggestions on where to assign scores for your character's class. The table puts the highest scores in a class's main abilities. If you used a different method to generate the scores, you may still use this table to guide where you place your highest and lowest scores.",
            STANDARD_ARRAY_BY_CLASS_TABLE,
        ),
    ),
    (
        "create_your_character",
        "adjust_scores",
        (PROSE,),
        (
            "After assigning your ability scores, adjust them according to your background. Your background lists three abilities; increase one of those scores by 2 and a different one by 1, or increase all three by 1. None of these increases can raise a score above 20.",
        ),
    ),
    (
        "create_your_character",
        "ability_modifiers",
        (PROSE,),
        (
            "Finally, determine your ability modifiers using the Ability Scores and Modifiers table. Write the modifier next to each of your scores.",
            ABILITY_SCORES_AND_MODIFIERS_TABLE,
        ),
    ),
    # -- Step 4: Alignment -----------------------------------------------------
    (
        "create_your_character",
        "choose_alignment",
        (PROSE,),
        (
            "Choose your character's alignment from the options below, and note it on your character sheet.",
            "The game assumes that player characters aren't of an evil alignment. Check with your GM before making an evil character.",
        ),
    ),
    # The qualifier ("typical behavior ... individuals can vary") governs all
    # nine summaries, so they are one component's prose.
    (
        "create_your_character",
        "nine_alignments",
        (PROSE,),
        (
            "A creature's alignment broadly describes its ethical attitudes and ideals. Alignment is a combination of two factors: one identifies morality (good, evil, or neutral), and the other describes attitudes toward order (lawful, chaotic, or neutral).",
            "The summaries of the alignments below describe the typical behavior of a creature with that alignment; individuals can vary from that behavior.",
            "_Lawful Good (LG)._ Lawful Good creatures endeavor to do the right thing as expected by society. Someone who fights injustice and protects the innocent without hesitation is probably Lawful Good.",
            "_Neutral Good (NG)._ Neutral Good creatures do the best they can, working within rules but not feeling bound by them. A kindly person who helps others according to their needs is probably Neutral Good.",
            "_Chaotic Good (CG)._ Chaotic Good creatures act as their conscience directs with little regard for what others expect. A rebel who waylays a cruel baron's tax collectors and uses the stolen money to help the poor is probably Chaotic Good.",
            "_Lawful Neutral (LN)._ Lawful Neutral individuals act in accordance with law, tradition, or personal codes. Someone who follows a disciplined rule of life—and isn't swayed either by the demands of those in need or by the temptations of evil—is probably Lawful Neutral.",
            "_Neutral (N)._ Neutral is the alignment of those who prefer to avoid moral questions and don't take sides, doing what seems best at the time. Someone who's bored by moral debate is probably Neutral.",
            "_Chaotic Neutral (CN)._ Chaotic Neutral creatures follow their whims, valuing their personal freedom above all else. A scoundrel who wanders the land living by their wits is probably Chaotic Neutral.",
            "_Lawful Evil (LE)._ Lawful Evil creatures methodically take what they want within the limits of a code of tradition, loyalty, or order. An aristocrat exploiting citizens while scheming for power is probably Lawful Evil.",
            "_Neutral Evil (NE)._ Neutral Evil is the alignment of those who are untroubled by the harm they cause as they pursue their desires. A criminal who robs and murders as they please is probably Neutral Evil.",
            "_Chaotic Evil (CE)._ Chaotic Evil creatures act with arbitrary violence, spurred by their hatred or bloodlust. A villain pursuing schemes of vengeance and havoc is probably Chaotic Evil.",
        ),
    ),
    # The sidebar the release prints among the nine; its clause is an exact run
    # of its text between the ``>`` markers.
    (
        "create_your_character",
        "unaligned_creatures",
        (PROSE,),
        (
            "Most creatures that lack the capacity for rational thought don't have alignments; they are unaligned.",
        ),
    ),
    # -- Step 5: Character Creation Details -------------------------------------
    (
        "create_your_character",
        "class_features",
        (PROSE,),
        (
            'Look at your class\'s feature table in "Classes," and write down the level 1 features. The class features are detailed there too.',
            "Some class features offer choices. Make sure to read all your features and make any offered choices.",
        ),
    ),
    (
        "create_your_character",
        "saving_throws",
        (PROSE,),
        (
            "_Saving Throws_. For the saving throws you have proficiency in, add your Proficiency Bonus to the appropriate ability modifier and note the total. Some players also like to note the modifier for saving throws they're not proficient in, which is just the relevant ability modifier.",
        ),
    ),
    (
        "create_your_character",
        "skills",
        (PROSE,),
        (
            "_Skills_. For skills you have proficiency in, add your Proficiency Bonus to the ability modifier associated with that skill, and note the total. You might also wish to note the modifier for skills you're not proficient in, which is just the relevant ability modifier.",
        ),
    ),
    (
        "create_your_character",
        "passive_perception",
        (PROSE,),
        (
            "_Passive Perception_. Sometimes your GM will determine whether your character notices something without asking you to make a Wisdom (Perception) check; the GM uses your Passive Perception instead. Passive Perception is a score that reflects a general awareness of your surroundings when you're not actively looking for something. Use this formula to determine your Passive Perception score:",
            "Passive Perception = 10 + Wisdom (Perception) check modifier",
            "Include all modifiers that apply to your Wisdom (Perception) checks.",
        ),
    ),
    (
        "create_your_character",
        "hit_points",
        (PROSE,),
        (
            "_Hit Points_. Your class and Constitution modifier determine your Hit Point maximum at level 1, as shown on the Level 1 Hit Points by Class table.",
            LEVEL_1_HIT_POINTS_BY_CLASS_TABLE,
            "The character sheet includes room to note your current Hit Points when you take damage, as well as any Temporary Hit Points you might gain. There's also space to track Death Saving Throws.",
        ),
    ),
    (
        "create_your_character",
        "hit_point_dice",
        (PROSE,),
        (
            "_Hit Point Dice_. Your class's description tells you the die type of your character's Hit Point Dice (or Hit Dice for short); write this on your character sheet. At level 1, your character has 1 Hit Die. You can spend Hit Dice during a Short Rest to recover Hit Points. Your character sheet also includes space to note how many Hit Dice you've spent.",
        ),
    ),
    (
        "create_your_character",
        "initiative",
        (PROSE,),
        (
            "_Initiative_. Write your Dexterity modifier in the space for Initiative on your character sheet.",
        ),
    ),
    (
        "create_your_character",
        "armor_class",
        (PROSE,),
        (
            '_Armor Class_. Without armor or a shield, your base Armor Class is 10 plus your Dexterity modifier. If your starting equipment includes armor or a Shield (or both), calculate your AC using the rules in "Equipment." A class feature might give you a different way to calculate your AC.',
        ),
    ),
    # The lead's "unless a weapon's property says otherwise" governs both
    # formulas, so lead and formulas are one component's prose.
    (
        "create_your_character",
        "attacks",
        (PROSE,),
        (
            "_Attacks_. In the Weapons & Damage Cantrips section of the character sheet, write your starting weapons. The attack roll bonus for a weapon with which you have proficiency is one of the following unless a weapon's property says otherwise:",
            "Melee attack bonus = Strength modifier + Proficiency Bonus\nRanged attack bonus = Dexterity modifier + Proficiency Bonus",
            'Look up the damage and properties of your weapons in "Equipment." You add the same ability modifier you use for attacks with a weapon to your damage rolls with that weapon.',
        ),
    ),
    (
        "create_your_character",
        "spellcasting",
        (PROSE,),
        (
            "_Spellcasting_. Note both the saving throw DC for your spells and the attack bonus for attacks you make with them, using these formulas:\n**Spell save DC** = 8 + spellcasting ability modifier + Proficiency Bonus",
            "**Spell attack bonus** = spellcasting ability modifier + Proficiency Bonus",
            "Your spellcasting ability modifier for a spell is determined by whatever feature gives you the ability to cast the spell.",
        ),
    ),
    (
        "create_your_character",
        "spell_slots_cantrips_prepared",
        (PROSE,),
        (
            "_Spell Slots, Cantrips, and Prepared Spells._ If your class gives you the Spellcasting or Pact Magic feature, your class features table shows the number of spell slots you have available, how many cantrips you know, and how many spells you can prepare. Choose your cantrips and prepared spells, and note them—along with your number of spell slots—on your character sheet.",
        ),
    ),
    # == Level Advancement (pp23-24) ==========================================
    (
        "level_advancement",
        "character_advancement",
        (PROSE,),
        (
            "While going on adventures, your character gains experience, represented by Experience Points (XP). A character who reaches a specified Experience Point total advances in capability. This advancement is called gaining a level.",
            "The Character Advancement table lists the XP you need to advance to a level and the Proficiency Bonus for a character of that level. When your XP total equals or exceeds a number in the Experience Points column, you reach the corresponding level.",
            CHARACTER_ADVANCEMENT_TABLE,
        ),
    ),
    (
        "level_advancement",
        "choose_class",
        (PROSE,),
        (
            '**1: Choose a Class.** Most characters advance in the same class. However, you might decide to gain a level in another class using the rules in the "Multiclassing" section.',
        ),
    ),
    (
        "level_advancement",
        "hit_points_and_hit_point_dice",
        (PROSE,),
        (
            "**2: Adjust Hit Points and Hit Point Dice.** Each time you gain a level, you gain an additional Hit Die. Roll that die, add your Constitution modifier to the roll, and add the total (minimum of 1) to your Hit Point maximum. Instead of rolling, you can use the fixed value shown in the Fixed Hit Points by Class table.",
            FIXED_HIT_POINTS_BY_CLASS_TABLE,
        ),
    ),
    (
        "level_advancement",
        "class_features",
        (PROSE,),
        (
            '**3: Record New Class Features.** Look at your class features table in "Classes," and note the features you gain at your new level in that class. Make any choices offered by a new feature.',
        ),
    ),
    (
        "level_advancement",
        "proficiency_bonus",
        (PROSE,),
        (
            '**4: Adjust Proficiency Bonus.** A character\'s Proficiency Bonus increases at certain levels, as shown in the Character Advancement table and your class features table in "Classes." When your Proficiency Bonus increases, increase all the numbers on your character sheet that include your Proficiency Bonus.',
        ),
    ),
    (
        "level_advancement",
        "ability_modifiers",
        (PROSE,),
        (
            "**5: Adjust Ability Modifiers.** If you choose a feat that increases one or more of your ability scores, your ability modifier also changes if the new score is an even number. When that happens, adjust all the numbers on your character sheet that use that ability modifier. When your Constitution modifier increases by 1, your Hit Point maximum increases by 1 for each level you have attained.",
        ),
    ),
    # "These tiers don't have any rules associated with them": kept whole as
    # faithful descriptive prose, never as a rule. Each tier's level range is
    # printed only in its heading, so the four headings are governing prose
    # beside the descriptions they label, not excluded headings.
    (
        "level_advancement",
        "tiers_of_play",
        (PROSE,),
        (
            "With each new level, characters acquire new capabilities that equip them to handle greater challenges. As characters advance in level, the tone of the game also changes, and the stakes of the campaign get higher. It's helpful to think of a character's (and a campaign's) arc in terms of four tiers of play,\ndescribing the journey from a level 1 character just beginning an adventuring career to the epic heights of level 20. These tiers don't have any rules associated with them; they point to the fact that the play experience evolves as characters gain levels.",
            "#### Tier 1 (Levels 1–4)",
            "In tier 1, characters are apprentice adventurers, though they are already set apart from the broader populace by virtue of their extraordinary abilities. They learn their starting class features and choose a subclass. The threats they face usually pose a danger to local farmsteads or villages.",
            "#### Tier 2 (Levels 5–10)",
            "In tier 2, characters are full-fledged adventurers. Spellcasters gain iconic spells such as _Fireball_, _Lightning Bolt_, and _Raise Dead_. Most weapon-focused classes gain the ability to make multiple attacks in a round. The characters now face dangers that threaten cities and kingdoms.",
            "#### Tier 3 (Levels 11–16)",
            "In tier 3, characters have reached a level of power that makes them special among adventurers. At level 11, many spellcasters learn reality-altering spells. Other characters gain features that allow them to make more attacks or to do more impressive things with those attacks. These adventurers often confront threats to whole regions.",
            "#### Tier 4 (Levels 17–20)",
            "At tier 4, characters achieve the pinnacle of their class features, becoming heroic archetypes. The fate of the world or even the order of the multiverse might hang in the balance during their adventures.",
        ),
    ),
    # == Starting at Higher Levels (p24) ======================================
    (
        "starting_at_higher_levels",
        "higher_starting_level",
        (PROSE,),
        (
            "Your GM might start your group's characters at a level higher than 1. It is particularly recommended to start at level 3 if your group is composed of seasoned D&D players.",
        ),
    ),
    (
        "starting_at_higher_levels",
        "creating_your_character",
        (PROSE,),
        (
            'Creating a higher-level character uses the same character-creation steps outlined in this chapter and the rules for advancing beyond level 1 provided in the "Level Advancement" section. You begin with the minimum amount of XP required to reach your starting level.',
        ),
    ),
    # A GM's optional advancement past level 20, not a creation rule.
    (
        "starting_at_higher_levels",
        "bonus_feats_at_level_20",
        (PROSE,),
        (
            "A GM can use feats as a form of advancement after characters reach level 20 to provide greater power to characters who have no more levels to gain. With this approach, each character gains one feat of their choice for every 30,000 XP the character earns above 355,000 XP. Epic Boon feats are especially appropriate for these bonus feats, but a player can choose any feat for which their level 20 character qualifies.",
        ),
    ),
    (
        "starting_at_higher_levels",
        "starting_equipment",
        (PROSE,),
        (
            "The GM decides whether your character starts with more than the standard equipment for a level 1 character, possibly even one or more magic items. The Starting Equipment at Higher Levels table is a guide for the GM.",
            'Also, check with your GM about what equipment is available for you to buy with your starting money. For example, the firearms described in "Equipment" are too expensive for level 1 characters, but they might be available for purchase if your GM allows them.',
            STARTING_EQUIPMENT_AT_HIGHER_LEVELS_TABLE,
        ),
    ),
    # == Multiclassing (pp24-26) ==============================================
    (
        "multiclassing",
        "multiclassing",
        (PROSE,),
        (
            "Multiclassing allows you to gain levels in multiple classes. With this rule, you have the option of gaining a level in a new class whenever you advance in level instead of gaining a level in your current class. Doing so lets you mix the abilities of those classes to realize a character concept that might not be reflected in a single class.",
        ),
    ),
    (
        "multiclassing",
        "prerequisites",
        (PROSE,),
        (
            "To qualify for a new class, you must have a score of at least 13 in the primary ability of the new class and your current classes.",
        ),
    ),
    (
        "multiclassing",
        "experience_points",
        (PROSE,),
        (
            'The Experience Point cost to gain a level is based on your total character level, not your level in a particular class, as shown in the Character Advancement table in "Character Creation."',
        ),
    ),
    (
        "multiclassing",
        "hit_points",
        (PROSE,),
        (
            "You gain the Hit Points from your new class as described for levels after 1. You gain the level 1 Hit Points for a class only when your total character level is 1.",
        ),
    ),
    (
        "multiclassing",
        "hit_point_dice",
        (PROSE,),
        (
            "Add together the Hit Dice granted by all your classes to form your pool of Hit Dice. If these dice are the same die type, you can pool them together.",
            "If your classes give you Hit Dice of different types, track them separately.",
        ),
    ),
    (
        "multiclassing",
        "proficiency_bonus",
        (PROSE,),
        (
            "Your Proficiency Bonus is based on your total character level, not your level in a particular class, as shown in the Character Advancement table.",
        ),
    ),
    (
        "multiclassing",
        "proficiencies",
        (PROSE,),
        (
            "When you gain your first level in a class other than your initial class, you gain only some of the new class's starting proficiencies, as detailed in each class's description in \"Classes.\"",
        ),
    ),
    (
        "multiclassing",
        "class_features",
        (PROSE,),
        (
            "When you gain a new level in a class, you get its features for that level. A few features have additional rules when you're multiclassing. Check the information about multiclassing included in each of your classes' descriptions.",
            "Special rules apply to Extra Attack, Spellcasting, and features (such as Unarmored Defense) that give you alternative ways to calculate your Armor Class.",
        ),
    ),
    (
        "multiclassing",
        "armor_class",
        (PROSE,),
        (
            "If you have multiple ways to calculate your Armor Class, you can benefit from only one at a time.",
        ),
    ),
    (
        "multiclassing",
        "extra_attack",
        (PROSE,),
        (
            "If you gain the Extra Attack feature from more than one class, the features don't stack. You can't make more than two attacks with this feature unless you have a feature that says you can (such as the Fighter's Two Extra Attacks feature).",
            "Similarly, the Warlock's Thirsting Blade invocation, which grants you the Extra Attack feature with your pact weapon, doesn't give you additional attacks if you also have Extra Attack.",
        ),
    ),
    # The scope sentence ("Once you have the Spellcasting feature from more than
    # one class, use the rules below") governs prepared spells, cantrips and
    # spell slots alike, so it and they are one component's prose, the table
    # with them.
    (
        "multiclassing",
        "spellcasting",
        (PROSE,),
        (
            "Your capacity for spellcasting depends partly on your combined levels in all your spellcasting classes and partly on your individual levels in those classes. Once you have the Spellcasting feature from more than one class, use the rules below. If you multiclass but have the Spellcasting feature from only one class, follow the rules for that class.",
            "_Spells Prepared_. You determine what spells you can prepare for each class individually, as if you were a single-classed member of that class.",
            "Each spell you prepare is associated with one of your classes, and you use the spellcasting ability of that class when you cast the spell.",
            "_Cantrips_. If a cantrip of yours increases in power at higher levels, the increase is based on your total character level, not your level in a particular class, unless the spell says otherwise.",
            "_Spell Slots_. You determine your available spell slots by adding together the following:",
            "- All your levels in the Bard, Cleric, Druid, Sorcerer, and Wizard classes\n- Half your levels (round up) in the Paladin and Ranger classes",
            "Then look up this total level in the Level column of the Multiclass Spellcaster table. You use the slots for that level to cast spells of an appropriate level from any class whose Spellcasting feature you have.",
            "This table might give you spell slots of a higher level than the spells you prepare. You can use those slots but only to cast your lower-level spells. If a lower-level spell that you cast, like _Burning Hands_, has an enhanced effect when cast at a higher level, you can use the enhanced effect as normal.",
            MULTICLASS_SPELLCASTER_TABLE,
        ),
    ),
    (
        "multiclassing",
        "pact_magic",
        (PROSE,),
        (
            "_Pact Magic._ If you have the Pact Magic feature from the Warlock class and the Spellcasting feature, you can use the spell slots you gain from Pact Magic to cast spells you have prepared from classes with the Spellcasting feature, and you can use the spell slots you gain from the Spellcasting feature to cast Warlock spells you have prepared.",
        ),
    ),
    # == Trinkets (pp26-28) ===================================================
    (
        "trinkets",
        "trinkets",
        (PROSE,),
        (
            "When you make your character, you can roll once on the Trinkets table to gain a Tiny trinket, a simple item lightly touched by mystery. The GM might also use this table. It can help stock a room in a dungeon or fill a creature's pockets.",
            TRINKETS_TABLE,
        ),
    ),
    # == Rules Glossary =======================================================
    (
        "alignment",
        "alignment",
        (PROSE,),
        (
            "A creature's alignment broadly describes its ethical attitudes and ideals. Alignment is a combination of two factors: one identifies morality (good, evil, or neutral), and the other describes attitudes toward order (lawful, chaotic, or neutral). These factors allow for nine possible combinations, such as Lawful Good and Neutral Evil.",
        ),
    ),
    (
        "creature_type",
        "creature_type",
        (PROSE,),
        (
            "Every creature, including every player character, has a tag in the rules that identifies the type of creature it is. Most player characters are of the Humanoid type. These are the game's creature types:",
            CREATURE_TYPE_TABLE,
            "The types don't have rules themselves, but some rules in the game affect creatures of certain types in different ways.",
        ),
    ),
    (
        "experience_points",
        "experience_points",
        (PROSE,),
        (
            "As they overcome challenges and complete adventures, characters earn Experience Points (XP), which are awarded by the Game Master. When a character's XP total crosses certain thresholds, the character's level increases.",
        ),
    ),
    (
        "passive_perception",
        "passive_perception",
        (PROSE,),
        (
            "Passive Perception is a score that reflects a creature's general awareness of its surroundings. The GM uses this score when determining whether a creature notices something without consciously making a Wisdom (Perception) check.",
            "A creature's Passive Perception equals 10 plus the creature's Wisdom (Perception) check bonus. If the creature has Advantage on such checks, increase the score by 5. If the creature has Disadvantage on them, decrease the score by 5.",
        ),
    ),
    (
        "size",
        "size",
        (PROSE,),
        (
            "A creature or an object belongs to a size category: Tiny, Small, Medium, Large, Huge, or Gargantuan. A creature's size determines how much space the creature occupies in combat. An object's size affects its Hit Points.",
        ),
    ),
)

#: (entry, leaf prefix): whole leaves that introduce the rules after them and
#: state none of their own.
FRAMING: tuple[tuple[str, str], ...] = (
    ("create_your_character", "Here are the steps to make a character"),
    ("create_your_character", "Now fill in the rest of your character sheet."),
    ("create_your_character", "Note these numbers on your character sheet."),
    ("level_advancement", "When you gain a level, follow these steps:"),
)

SUBSECTION_HEADING = "subsection heading: names a subsection and states no rule"

#: (entry, exact leaf contents, reason): whole leaves that only name a
#: subsection. Only headings are excluded; every sidebar is authored.
EXCLUDED: tuple[tuple[str, tuple[str, ...], str], ...] = (
    (
        "create_your_character",
        (
            "### Step 1: Choose Class",
            "#### Write Your Level",
            "#### Note Armor Training",
            "### Step 2: Character Origin",
            "#### Choose a Background",
            "#### Choose Starting Equipment",
            "#### Choose a Species",
            "#### Imagine Your Past and Present",
            "#### Choose Languages",
            "### Step 3: Ability Scores",
            "#### Generate Your Scores",
            "#### Assign Ability Scores",
            "#### Adjust Ability Scores",
            "#### Determine Ability Modifiers",
            "### Step 4: Alignment",
            "#### The Nine Alignments",
            "### Step 5: Character Creation Details",
            "#### Record Class Features",
            "#### Fill In Numbers",
        ),
        SUBSECTION_HEADING,
    ),
    (
        "level_advancement",
        (
            "### Gaining a Level",
            "### Tiers of Play",
        ),
        SUBSECTION_HEADING,
    ),
    (
        "starting_at_higher_levels",
        ("### Creating Your Character", "### Starting Equipment"),
        SUBSECTION_HEADING,
    ),
    (
        "multiclassing",
        (
            "### Prerequisites",
            "### Experience Points",
            "### Hit Points and Hit Point Dice",
            "### Proficiency Bonus",
            "### Proficiencies",
            "### Class Features",
            "#### Armor Class",
            "#### Extra Attack",
            "#### Spellcasting",
        ),
        SUBSECTION_HEADING,
    ),
)

# ---------------------------------------------------------------------------
# Representation proposed for the clauses above
# ---------------------------------------------------------------------------

C = EntryComponent


def here(slug: str) -> Target:
    """A *Character Creation* section of this batch."""
    return (CHARACTER_CREATION, f"character_creation.{slug}")


STARTING_AT_HIGHER_LEVELS = here("starting_at_higher_levels")
CREATE_YOUR_CHARACTER = here("create_your_character")
LEVEL_ADVANCEMENT = here("level_advancement")
MULTICLASSING = here("multiclassing")
#: The accepted destinations this batch cites.
PLAY_COMBAT = (PLAY, "play.combat")
#: Parts this batch does not author: each pointer stays unresolved.
PLAY_UNRESOLVED = (PLAY, UNRESOLVED_TARGET)
CLASSES_UNRESOLVED = (CLASSES, UNRESOLVED_TARGET)
CHARACTER_ORIGINS_UNRESOLVED = (CHARACTER_ORIGINS, UNRESOLVED_TARGET)
FEATS_UNRESOLVED = (FEATS, UNRESOLVED_TARGET)
EQUIPMENT_UNRESOLVED = (EQUIPMENT, UNRESOLVED_TARGET)

CLASSES_REF = (("Classes", CLASSES_UNRESOLVED),)
EQUIPMENT_REF = (("Equipment", EQUIPMENT_UNRESOLVED),)
ORIGINS_REF = (("Character Origins", CHARACTER_ORIGINS_UNRESOLVED),)
#: The table is ``character_creation.level_advancement``'s own; the part name
#: printed after it in *Multiclassing* ("in "Character Creation."") only
#: locates that table, so it is not a separate, broader pointer.
ADVANCEMENT_TABLE_REF = (("Character Advancement table", LEVEL_ADVANCEMENT),)

COMPONENTS: tuple[EntryComponent, ...] = (
    # == Choose a Character Sheet =============================================
    C("character_sheet", "character_sheet", P, NO_USE),
    # == Create Your Character ================================================
    C("create_your_character", "creation_steps", P, NO_USE),
    # Class-keyed tables stay prose: "Classes" is not authored, so no class
    # identity exists to key a fact to.
    C("create_your_character", "choose_class", P, NO_USE, refs=CLASSES_REF),
    # "Typically": a GM may start higher.
    C("create_your_character", "write_level", P, CTX),
    C("create_your_character", "write_xp", P, NO_USE),
    C(
        "create_your_character",
        "starting_at_a_higher_level",
        P,
        GM,
        refs=(("Starting at Higher Levels", STARTING_AT_HIGHER_LEVELS),),
    ),
    C("create_your_character", "armor_training", P, NO_USE, refs=EQUIPMENT_REF),
    C("create_your_character", "origin", P, NO_USE),
    C("create_your_character", "choose_background", P, GM, refs=ORIGINS_REF),
    C("create_your_character", "background_ability_scores", P, NO_USE),
    C(
        "create_your_character",
        "background_feat",
        P,
        NO_USE,
        refs=(("Feats", FEATS_UNRESOLVED),),
    ),
    C("create_your_character", "background_proficiencies", P, NO_USE),
    C("create_your_character", "class_proficiencies", P, NO_USE, refs=CLASSES_REF),
    # +2 at level 1 restates the accepted ``play.proficiency`` bands.
    C(
        "create_your_character",
        "starting_proficiency_bonus",
        P,
        NO_USE,
        refs=(("Playing the Game", PLAY_UNRESOLVED),),
    ),
    C("create_your_character", "starting_equipment", P, NO_USE, refs=EQUIPMENT_REF),
    C("create_your_character", "choose_species", P, NO_USE, refs=ORIGINS_REF),
    C("create_your_character", "past_and_present", P, NO_USE),
    # "might also give you languages": features outside this part add more.
    C("create_your_character", "languages", P, CTX),
    C("create_your_character", "standard_languages", P, NO_USE),
    C("create_your_character", "rare_languages", P, NO_USE),
    C(
        "create_your_character",
        "determine_ability_scores",
        P,
        NO_USE,
        refs=(("Playing the Game", PLAY_UNRESOLVED),),
    ),
    # Three alternative methods; "Your GM might prefer" one of them.
    C("create_your_character", "generate_scores", P, GM),
    C("create_your_character", "assign_scores", P, NO_USE),
    C("create_your_character", "standard_array_by_class", P, NO_USE),
    C("create_your_character", "adjust_scores", P, NO_USE),
    # Restates ``play.six_abilities`` / ``ability_modifiers``, prose there.
    C("create_your_character", "ability_modifiers", P, NO_USE),
    # "Check with your GM before making an evil character."
    C("create_your_character", "choose_alignment", P, GM),
    C("create_your_character", "nine_alignments", P, NO_USE),
    C("create_your_character", "unaligned_creatures", P, NO_USE),
    C("create_your_character", "class_features", P, NO_USE, refs=CLASSES_REF),
    C("create_your_character", "saving_throws", P, NO_USE),
    C("create_your_character", "skills", P, NO_USE),
    # No family states a derived score; the GM decides when it is used.
    C("create_your_character", "passive_perception", P, GM),
    C("create_your_character", "hit_points", P, NO_USE),
    C(
        "create_your_character",
        "hit_point_dice",
        P,
        NO_USE,
        refs=(("Short Rest", "short_rest"),),
    ),
    C("create_your_character", "initiative", P, NO_USE),
    # "A class feature might give you a different way to calculate your AC."
    C("create_your_character", "armor_class", P, CTX, refs=EQUIPMENT_REF),
    # "unless a weapon's property says otherwise".
    C("create_your_character", "attacks", P, CTX, refs=EQUIPMENT_REF),
    C("create_your_character", "spellcasting", P, NO_USE),
    # "If your class gives you the Spellcasting or Pact Magic feature".
    C("create_your_character", "spell_slots_cantrips_prepared", P, CTX),
    # == Level Advancement ====================================================
    # No family states an XP threshold; the Proficiency Bonus column restates
    # the accepted ``play.proficiency`` bands.
    C("level_advancement", "character_advancement", P, NO_USE),
    C(
        "level_advancement",
        "choose_class",
        P,
        CTX,
        refs=(("Multiclassing", MULTICLASSING),),
    ),
    C("level_advancement", "hit_points_and_hit_point_dice", P, NO_USE),
    C("level_advancement", "class_features", P, NO_USE, refs=CLASSES_REF),
    C("level_advancement", "proficiency_bonus", P, NO_USE, refs=CLASSES_REF),
    C("level_advancement", "ability_modifiers", P, NO_USE),
    C("level_advancement", "tiers_of_play", P, NO_USE),
    # == Starting at Higher Levels ============================================
    C("starting_at_higher_levels", "higher_starting_level", P, GM),
    C(
        "starting_at_higher_levels",
        "creating_your_character",
        P,
        NO_USE,
        refs=(("Level Advancement", LEVEL_ADVANCEMENT),),
    ),
    C("starting_at_higher_levels", "bonus_feats_at_level_20", P, GM),
    C("starting_at_higher_levels", "starting_equipment", P, GM, refs=EQUIPMENT_REF),
    # == Multiclassing ========================================================
    # An option a player takes when advancing, "With this rule".
    C("multiclassing", "multiclassing", P, CTX),
    C("multiclassing", "prerequisites", P, NO_USE),
    C(
        "multiclassing",
        "experience_points",
        P,
        NO_USE,
        refs=ADVANCEMENT_TABLE_REF,
    ),
    C("multiclassing", "hit_points", P, NO_USE),
    C("multiclassing", "hit_point_dice", P, NO_USE),
    C(
        "multiclassing",
        "proficiency_bonus",
        P,
        NO_USE,
        refs=ADVANCEMENT_TABLE_REF,
    ),
    C("multiclassing", "proficiencies", P, NO_USE, refs=CLASSES_REF),
    C("multiclassing", "class_features", P, NO_USE),
    C("multiclassing", "armor_class", P, NO_USE),
    C("multiclassing", "extra_attack", P, NO_USE),
    # ``SpellSlotProgressionFact`` rows are character levels; this table's
    # rows are the multiclass spellcaster total, so the family would misstate
    # the index. Kept whole, with its scope, arithmetic and rounding.
    C("multiclassing", "spellcasting", P, CTX),
    C("multiclassing", "pact_magic", P, CTX),
    # == Trinkets =============================================================
    C("trinkets", "trinkets", P, GM),
    # == Rules Glossary =======================================================
    C("alignment", "alignment", P, NO_USE),
    C("creature_type", "creature_type", P, NO_USE),
    C("experience_points", "experience_points", P, GM),
    # Restated by Create Your Character Step 5; no family states a derived score.
    C("passive_perception", "passive_perception", P, GM),
    C("size", "size", P, NO_USE),
)

ALIGNMENT_SEE_ALSO = '_See also_ "Character Creation" ("Create Your Character").'
EXPERIENCE_POINTS_SEE_ALSO = '_See also_ "Level Advancement."'
SIZE_SEE_ALSO = '_See also_ "Breaking Objects" and "Playing the Game" ("Combat").'

#: (entry, text, component key or ``None`` for record-owned references).
SUPPORTING: tuple[tuple[str, str, str | None], ...] = (
    # -- Create Your Character ------------------------------------------------
    (
        "create_your_character",
        "For example, a score of 14 costs 7 of your 27 points.",
        "generate_scores",
    ),
    (
        "create_your_character",
        "Some players like to increase their class's primary ability, while others prefer to increase a low score.",
        "adjust_scores",
    ),
    ("create_your_character", "**Unaligned Creatures**", "unaligned_creatures"),
    (
        "create_your_character",
        "Sharks are savage predators, for example, but they aren't evil; they are unaligned.",
        "unaligned_creatures",
    ),
    (
        "create_your_character",
        "For example, if your character has a Wisdom of 15 and proficiency in the Perception skill, you have a Passive Perception of 14 (10 + 2 for your Wisdom modifier + 2 for proficiency).",
        "passive_perception",
    ),
    # -- Level Advancement ----------------------------------------------------
    (
        "level_advancement",
        "For example, if a character reaches level 8 and increases their Constitution score from 17 to 18, the Constitution modifier increases to +4. The character's Hit Point maximum then increases by 8, in addition to the Hit Points gained for reaching level 8.",
        "ability_modifiers",
    ),
    # -- Starting at Higher Levels --------------------------------------------
    (
        "starting_at_higher_levels",
        "For example, if the GM starts you at level 10, you have 64,000 XP.",
        "creating_your_character",
    ),
    (
        "starting_at_higher_levels",
        "**Bonus Feats at Level 20**",
        "bonus_feats_at_level_20",
    ),
    # -- Multiclassing ----------------------------------------------------------
    (
        "multiclassing",
        "For example, a Barbarian who decides to multiclass into the Druid class must have Strength and Wisdom scores of 13 or higher, since Strength is the primary ability for Barbarians and Wisdom is the primary ability for Druids.",
        "prerequisites",
    ),
    (
        "multiclassing",
        "For example, if you are a level 6 Cleric / level 1 Fighter, you must gain enough XP to reach level 8 before you can take your second level as a Fighter or your seventh level as a Cleric.",
        "experience_points",
    ),
    (
        "multiclassing",
        "For example, both the Fighter and the Paladin have a d10 Hit Die, so if you are a level 5 Fighter / level 5 Paladin, you have ten d10 Hit Dice.",
        "hit_point_dice",
    ),
    (
        "multiclassing",
        "If you are a level 5 Cleric / level 5 Paladin, for example, you have five d8 Hit Dice and five d10 Hit Dice.",
        "hit_point_dice",
    ),
    (
        "multiclassing",
        "For example, if you are a level 3 Fighter / level 2 Rogue, you have the Proficiency Bonus of a level 5 character, which is +3.",
        "proficiency_bonus",
    ),
    (
        "multiclassing",
        "For example, a Monk/Sorcerer with a Monk's Unarmored Defense feature and a Sorcerer's Draconic Resilience feature must choose only one of those features as a way to calculate Armor Class.",
        "armor_class",
    ),
    (
        "multiclassing",
        "If you are a level 4 Ranger / level 3 Sorcerer, for example, you can prepare five level 1 Ranger spells, and you can prepare six Sorcerer spells of level 1 or 2 (as well as four Sorcerer cantrips).",
        "spellcasting",
    ),
    (
        "multiclassing",
        "For example, if you are a level 4 Ranger / level 3 Sorcerer, you count as a level 5 character when determining your spell slots, counting all your levels as a Sorcerer and half your Ranger levels. As shown\nin the Multiclass Spellcaster table, you have four level 1 spell slots, three level 2 slots, and two level 3 slots. However, you can't prepare any level 3 spells, nor can you prepare any level 2 Ranger spells. You can use the spell slots of those levels to cast the spells you do prepare—and potentially enhance their effects.",
        "spellcasting",
    ),
    # -- Rules Glossary ---------------------------------------------------------
    ("alignment", ALIGNMENT_SEE_ALSO, None),
    ("experience_points", EXPERIENCE_POINTS_SEE_ALSO, None),
    (
        "passive_perception",
        "For example, a level 1 character with a Wisdom of 15 and proficiency in Perception has a Passive Perception of 14 (10 + 2 + 2). If that character has Advantage on Wisdom (Perception) checks, the score becomes 19.",
        "passive_perception",
    ),
    ("size", SIZE_SEE_ALSO, None),
)

#: Record-owned references: (entry, printed text, target, texts of the spans the
#: pointer is read from). Alignment's pointer names the part and then its
#: section; the section is the precise destination.
RECORD_REFERENCES: tuple[RecordReference, ...] = (
    (
        "alignment",
        "Create Your Character",
        CREATE_YOUR_CHARACTER,
        (ALIGNMENT_SEE_ALSO,),
    ),
    (
        "experience_points",
        "Level Advancement",
        LEVEL_ADVANCEMENT,
        (EXPERIENCE_POINTS_SEE_ALSO,),
    ),
    ("size", "Breaking Objects", "breaking_objects", (SIZE_SEE_ALSO,)),
    ("size", "Combat", PLAY_COMBAT, (SIZE_SEE_ALSO,)),
)

#: Targets outside this batch that no accepted record defines and this batch
#: does not author. Each citation would be an expected unknown-target finding.
NEW_TARGETS: tuple[Target, ...] = ()
#: Targets outside this batch that the accepted inputs define.
ACCEPTED_CONTEXT_TARGETS: tuple[Target, ...] = (
    PLAY_COMBAT,
    "breaking_objects",
    "short_rest",
)


def batch() -> EntryBatch:
    """The tables above, read at call time so tests can mutate them."""
    return EntryBatch(
        origin=ORIGIN,
        schema=(SCHEMA_15_VERSION, SCHEMA_15_HASH),
        proposal_origin=f"{ORIGIN} (CRD Issue 5d character-creation foundations batch; unaccepted)",
        unit_prefix="character-creation-foundations",
        parent=PARENT,
        entries=ENTRIES,
        expected_leaves=179,
        clauses=CLAUSES,
        framing=FRAMING,
        components=COMPONENTS,
        supporting=SUPPORTING,
        record_references=RECORD_REFERENCES,
        placements=PLACEMENTS,
        excluded=EXCLUDED,
    )


def build(session: Session) -> Built:
    """Derive the character-creation-foundations proposal from the release *session* published."""
    return build_entry_batch(session, batch(), published_release_binding(session))


#: Printed pointers whose destination has no record yet, as (scope, text). Each
#: stays unresolved, alone and composed, until a reviewed resolution names it.
#: A part printed by several components is each component's own reference.
UNRESOLVED: tuple[tuple[str, str], ...] = (
    *((CHARACTER_ORIGINS, "Character Origins"),) * 2,
    *((CLASSES, "Classes"),) * 6,
    *((EQUIPMENT, "Equipment"),) * 5,
    (FEATS, "Feats"),
    *((PLAY, "Playing the Game"),) * 2,
)


def expected_representation_findings() -> list[str]:
    """Every out-of-batch target: the accepted ones stay unknown to the batch alone."""
    return sorted(
        [
            *unknown_target_findings(
                RECORD_REFERENCES,
                COMPONENTS,
                (*NEW_TARGETS, *ACCEPTED_CONTEXT_TARGETS),
            ),
            *(f"reference {s}:{t!r}: unresolved reference" for s, t in UNRESOLVED),
        ]
    )


# ---------------------------------------------------------------------------
# Unrecorded resolution drafts for the same Owner packet
# ---------------------------------------------------------------------------
#: Two accepted citations print "Character Creation" and stay unresolved. A
#: resolution may name only an accepted destination, so each draft becomes
#: applicable only once its target is accepted, and then only by its own
#: authorized ``resolve_references`` action. Nothing here records or applies
#: either.
#:
#: ``play.d20_tests`` / ``armor_class``: "The AC of a character is determined
#: at character creation (see "Character Creation")". Character creation
#: determines AC in *Create Your Character*, Step 5, *Armor Class*; the
#: *Multiclassing* Armor Class rule is advancement and a different rule.
ARMOR_CLASS_RESOLUTION_ID = "resolve-armor-class-character-creation-1"
#: The span the accepted citation's REFERENCE provenance cites.
ARMOR_CLASS_POINTER_SPAN = "4e1f6ecf-d4c1-5b6d-a24c-c8676b1b7506"
#: ``play.proficiency`` / ``proficiency_bonus``: "A character's Proficiency
#: Bonus increases as the character gains levels (described in "Character
#: Creation")". That increase is *Level Advancement*: the Character
#: Advancement table's Proficiency Bonus column and Gaining a Level step 4.
PROFICIENCY_BONUS_RESOLUTION_ID = "resolve-proficiency-bonus-character-creation-1"
PROFICIENCY_BONUS_POINTER_SPAN = "6b8bbca6-0f41-549a-8b8e-bc750f6e3bf6"


def draft_armor_class_resolution(binding: ReleaseBinding) -> ReferenceResolution:
    """The pending Armor Class resolution, drafted for review against *binding*."""
    return ReferenceResolution(
        resolution_id=ARMOR_CLASS_RESOLUTION_ID,
        from_record_key="play.d20_tests",
        from_component_key="armor_class",
        source_text="Character Creation",
        scope_key=CHARACTER_CREATION,
        target_record_key=CREATE_YOUR_CHARACTER[1],
        release_binding=binding,
        provenance_span_ids=(ARMOR_CLASS_POINTER_SPAN,),
    )


def draft_proficiency_bonus_resolution(binding: ReleaseBinding) -> ReferenceResolution:
    """The pending Proficiency Bonus resolution, drafted for review against *binding*."""
    return ReferenceResolution(
        resolution_id=PROFICIENCY_BONUS_RESOLUTION_ID,
        from_record_key="play.proficiency",
        from_component_key="proficiency_bonus",
        source_text="Character Creation",
        scope_key=CHARACTER_CREATION,
        target_record_key=LEVEL_ADVANCEMENT[1],
        release_binding=binding,
        provenance_span_ids=(PROFICIENCY_BONUS_POINTER_SPAN,),
    )


def main(db: str) -> int:
    out = Path(__file__).resolve().parent / PROPOSAL_FILE
    return emit(db, build, out, expected_representation_findings())


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
