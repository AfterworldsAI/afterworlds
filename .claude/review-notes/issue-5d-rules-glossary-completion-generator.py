# ruff: noqa: E501  -- clause literals are verbatim source text, kept whole to be greppable
"""Author the **rules-glossary-completion** proposal: every Rules Glossary
definition no accepted batch has authored, one consolidated batch.

REVIEW MATERIAL for CRD Issue 5d (#137) over the qualified 5c release
``ebdd9333-eeed-5df1-b3e1-8b97c2f65f80`` / ``5.2.1-corpus.574662e9-0ef``. It
emits an *unaccepted* ``5d-proposal-2`` artifact. It accepts nothing, publishes
nothing, writes nothing under ``oracles/``, records no reference resolution,
and imports no earlier batch's content, identity or authority: every leaf is
read afresh from the release.

Scope, 133 leaves, 60 records, one review unit each: the sixty entries under
*Rules Definitions* (pp176-191 of the official PDF) that no accepted batch
authors, each whole, in printed order -- every entry the fourteen accepted
batches left, *Improvised Weapons* among them, which Equipment already cites.
The ninety-five accepted entries are inputs, not re-read. *Glossary
Conventions* (tags, "you", *See also*, obsolete terms, abbreviations) states
how the glossary is written, not a rule, and is not authored; nor is the
*Rules Definitions* heading or its one-line introduction. No spell, class,
monster or magic item is authored; each such name here is an example.

Record grain: one record per entry, each reading its whole unit in printed
order, one component per leaf a rule is printed in (*Improvised Weapons* its
definition and four run-in rules). Kinds: every record is ``glossary_rule``.

This file is literal review data only; the assembly is the committed shared
:mod:`afterworlds.ingestion.mechanical.authoring`. ``CLAUSES`` is the source
review; ``COMPONENTS`` is the representation proposed for it; expected rules
come from ``CLAUSES`` alone.

Authoring conventions (as the fourteen accepted batches):

* Every component is prose-bound: a definition states what a term means, and
  its numbers (a d20 roll's pair, three Attunements, 1d4 and 20/60 feet) are
  the lift path, not this batch, as the spellcasting batch left its own.
* The *Action* entry's uncaptioned, headless table is written as the release
  prints it (three rows of four); the official PDF prints the same twelve
  actions in columns.
* Examples stay inside the clause they illustrate; a *See also* is a
  supporting span of its record, as every accepted glossary batch.
* ``gamemaster_latitude`` is kept where the rule leaves the outcome to the GM
  (whether a D20 Test is warranted; an Ally or Enemy the GM designates; an
  improvised weapon's damage type and weapon equivalent);
  ``contextual_applicability`` where applying it turns on fiction the
  projection cannot enumerate (what is wielded contrary to its design; how an
  illusion in space seems to behave); everything else is
  ``no_identified_structured_use``. *Simultaneous Effects* hands the order to
  whoever's turn it is, player or GM, so it is not GM latitude.
* References:

  - every *See also*: a glossary entry to its record; "Playing the Game"
    ("X") to the accepted section ``X`` names, as the accepted glossary
    batches; "Equipment" ("Armor"/"Magic Items"/"Weapons") likewise to the
    accepted Equipment section; "NPC" to *Nonplayer Character*, the entry
    that defines the abbreviation ("A nonplayer character (NPC)") and the
    one *Glossary Conventions*' abbreviation list expands it to.
  - "Spells" and "Character Creation" name a whole part, and stay unresolved
    under its scope, as the accepted batches leave them: *Cantrip*, *Ritual*,
    *Spell*, *Character Sheet*, *Player Character*, and *Hit Point Dice*'s
    "as explained in "Character Creation."" A *Character Sheet* record exists
    in *Character Creation*; the pointer names the part, not it.
  - "Spells" ("Casting Spells") from *Spell Attack* and *Spellcasting Focus*
    stays unresolved under the Spells scope. In the official PDF *Casting
    Spells* (18 pt) contains *Casting Time* through *Combining Spell Effects*
    (14/12 pt), among them *Components* and *Attack Rolls*, which these
    entries' rules need; the release, and the accepted spellcasting batch
    after it, make those sections siblings, so ``spells.casting_spells`` is
    narrower than the section the pointer names. No record equals that
    target, and correcting the accepted structure is not this batch's.
  - each Rules Glossary term a rule here depends on (``GLOSSARY_TERMS``),
    accepted or authored here, by its printed name, once per component, from
    prose only, never an entry citing itself: a term printed capitalized as a
    rule name (D20 Test, Advantage, Hit Points, Short Rest, Blinded...), and
    the three rolls a D20 Test is -- "ability check", "attack roll", "saving
    throw" -- lowercase too, as the spellcasting batch cited "attack roll".
    Everyday words the glossary also defines (creature, object, target,
    weapon, spell, monster, skill, action, save, condition, curse, occupied)
    are not cited, and "Proficiency Bonus", which no glossary entry is, is
    not either. The *Action* entry's table is its explicit list of the actions
    it says are "defined elsewhere in this glossary", so each is cited from it.
  - the Equipment rules these definitions name by their printed names:
    "Simple"/"Martial" weapon to Weapon *Category*, "Ranged"/"Melee" weapon
    to *Melee or Ranged*, the "Thrown property" to *Thrown*, "Light, Medium,
    or Heavy armor" to Armor *Category* and "Shield" to the *Shield*, as the
    Equipment batch cites them; and *Spellcasting Focus*'s "Material
    components" to ``spells.components``.
  - examples (*Remove Curse*, *Greater Restoration*, *Polymorph*, Wild Shape,
    *Protection from Evil and Good*, *Dispel Evil and Good*, a Club) illustrate
    and are not references.

No resolution is drafted: Equipment's accepted "Improvised Weapons" citation
already names ``glossary.improvised_weapons``, which this batch defines, so it
closes by key.

Run: ``python issue-5d-rules-glossary-completion-generator.py <published afterworlds.db>``
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
from afterworlds.ingestion.mechanical.models import ComponentHandling
from afterworlds.ingestion.mechanical.representation import RecordKind

ORIGIN = "issue-5d-rules-glossary-completion-generator.py"
PROPOSAL_FILE = "issue-5d-rules-glossary-completion-REGEN-574662e9-PROPOSAL.json"
#: The entries are read under the Rules Glossary's definitions.
PARENT = ("Rules Glossary", "Rules Definitions")
#: The parts this batch's pointers name, formed from the release's own part
#: names under the ``<release-family>/<section-slug>`` convention.
PLAY = "srd-5.2.1/playing-the-game"
EQUIPMENT = "srd-5.2.1/equipment"
SPELLS = "srd-5.2.1/spells"
CHARACTER_CREATION = "srd-5.2.1/character-creation"
#: The target of a printed pointer whose destination has no record.
UNRESOLVED_TARGET = ""

GL = RecordKind.GLOSSARY_RULE

#: (record slug, printed label, record kind), in printed order.
ENTRIES: tuple[tuple[str, str, RecordKind], ...] = (
    ("ability_check", "Ability Check", GL),
    ("ability_score_and_modifier", "Ability Score and Modifier", GL),
    ("action", "Action", GL),
    ("advantage", "Advantage", GL),
    ("adventure", "Adventure", GL),
    ("ally", "Ally", GL),
    ("armor_training", "Armor Training", GL),
    ("attitude", "Attitude", GL),
    ("attunement", "Attunement", GL),
    ("bloodied", "Bloodied", GL),
    ("bonus_action", "Bonus Action", GL),
    ("bright_light", "Bright Light", GL),
    ("campaign", "Campaign", GL),
    ("cantrip", "Cantrip", GL),
    ("character_sheet", "Character Sheet", GL),
    ("creature", "Creature", GL),
    ("critical_hit", "Critical Hit", GL),
    ("curses", "Curses", GL),
    ("d20_test", "D20 Test", GL),
    ("darkness", "Darkness", GL),
    ("death_saving_throw", "Death Saving Throw", GL),
    ("difficulty_class", "Difficulty Class", GL),
    ("dim_light", "Dim Light", GL),
    ("disadvantage", "Disadvantage", GL),
    ("encounter", "Encounter", GL),
    ("enemy", "Enemy", GL),
    ("hazard", "Hazard", GL),
    ("healing", "Healing", GL),
    ("heavily_obscured", "Heavily Obscured", GL),
    ("heroic_inspiration", "Heroic Inspiration", GL),
    ("hit_point_dice", "Hit Point Dice", GL),
    ("illusions", "Illusions", GL),
    ("improvised_weapons", "Improvised Weapons", GL),
    ("knocking_out_a_creature", "Knocking Out a Creature", GL),
    ("lightly_obscured", "Lightly Obscured", GL),
    ("magical_effect", "Magical Effect", GL),
    ("monster", "Monster", GL),
    ("nonplayer_character", "Nonplayer Character", GL),
    ("object", "Object", GL),
    ("per_day", "Per Day", GL),
    ("player_character", "Player Character", GL),
    ("possession", "Possession", GL),
    ("proficiency", "Proficiency", GL),
    ("reaction", "Reaction", GL),
    ("ritual", "Ritual", GL),
    ("round_down", "Round Down", GL),
    ("save", "Save", GL),
    ("saving_throw", "Saving Throw", GL),
    ("shape_shifting", "Shape-Shifting", GL),
    ("simultaneous_effects", "Simultaneous Effects", GL),
    ("skill", "Skill", GL),
    ("spell", "Spell", GL),
    ("spell_attack", "Spell Attack", GL),
    ("spellcasting_focus", "Spellcasting Focus", GL),
    ("stable", "Stable", GL),
    ("target", "Target", GL),
    ("telepathy", "Telepathy", GL),
    ("teleportation", "Teleportation", GL),
    ("weapon", "Weapon", GL),
    ("weapon_attack", "Weapon Attack", GL),
)

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
#: The *Action* entry's twelve actions: no caption, no header row, three rows
#: of four cells, as the release prints them.
ACTIONS_TABLE = (
    "<table>\n  <tbody>\n"
    "    <tr>\n      <td>Attack</td>\n      <td>Dodge</td>\n      <td>Influence</td>\n      <td>Search</td>\n    </tr>\n"
    "    <tr>\n      <td>Dash</td>\n      <td>Help</td>\n      <td>Magic</td>\n      <td>Study</td>\n    </tr>\n"
    "    <tr>\n      <td>Disengage</td>\n      <td>Hide</td>\n      <td>Ready</td>\n      <td>Utilize</td>\n    </tr>\n"
    "  </tbody>\n</table>"
)

Clause = tuple[str, str, tuple[str | None, ...], tuple[str, ...]]


def cl(entry: str, key: str, *texts: str) -> Clause:
    """One clause row whose meaning is carried by governing prose."""
    return (entry, key, (PROSE,), texts)


#: Every covered leaf, in printed order, one row per rule. A *See also* is
#: not a clause: it is read below as a supporting span.
CLAUSES: tuple[Clause, ...] = (
    cl(
        "ability_check",
        "ability_check",
        "An ability check is a D20 Test that represents using one of the six abilities—or a specific skill associated with an ability—to overcome a challenge.",
    ),
    cl(
        "ability_score_and_modifier",
        "ability_score_and_modifier",
        "A creature has six ability scores—Strength, Dexterity, Constitution, Intelligence, Wisdom, and Charisma—each of which has a corresponding modifier. Add the modifier when you make a D20 Test with the corresponding ability or when a rule asks you to do so.",
    ),
    cl(
        "action",
        "action",
        "On your turn, you can take one action. Choose which action to take from those below or from the special actions provided by your features.",
        "These actions are defined elsewhere in this glossary:",
        ACTIONS_TABLE,
    ),
    cl(
        "advantage",
        "advantage",
        "If you have Advantage on a D20 Test, roll two d20s, and use the higher roll. A roll can't be affected by more than one Advantage, and Advantage and Disadvantage on the same roll cancel each other.",
    ),
    cl(
        "adventure",
        "adventure",
        "An adventure is a series of encounters. A story emerges through playing them.",
    ),
    cl(
        "ally",
        "ally",
        "A creature is your ally if it is a member of your adventuring party, your friend, on your side in combat, or a creature that the rules or the GM designates as your ally.",
    ),
    cl(
        "armor_training",
        "armor_training",
        "Armor training allows you to use armor of a certain category without the following drawbacks. If you wear Light, Medium, or Heavy armor and lack training with it, you have Disadvantage on any D20 Test that involves Strength or Dexterity, and you can't cast spells. If you use a Shield and lack training with it, you don't gain its AC bonus.",
    ),
    cl(
        "attitude",
        "attitude",
        "A monster has a starting attitude toward a player character: Friendly, Hostile, or Indifferent.",
    ),
    cl(
        "attunement",
        "attunement",
        "Some magic items require a creature to form a bond—called Attunement—with them before the creature can use an item's magical properties. A creature can have Attunement with no more than three magic items at a time.",
    ),
    cl(
        "bloodied",
        "bloodied",
        "A creature is Bloodied while it has half its Hit Points or fewer remaining.",
    ),
    cl(
        "bonus_action",
        "bonus_action",
        "A Bonus Action is a special action that you can take on the same turn that you take an action. You can't take more than one Bonus Action on a turn, and you have a Bonus Action to take only if a rule explicitly says so.",
    ),
    cl("bright_light", "bright_light", "Bright Light is normal illumination."),
    cl("campaign", "campaign", "A campaign is a series of adventures."),
    cl(
        "cantrip",
        "cantrip",
        "A cantrip is a level 0 spell, which is cast without a spell slot.",
    ),
    cl(
        "character_sheet",
        "character_sheet",
        "A character sheet is a paper or digital record that you use to track your character's information.",
    ),
    cl(
        "creature",
        "creature",
        "Any being in the game, including a player's character, is a creature.",
    ),
    cl(
        "critical_hit",
        "critical_hit",
        "If you roll a 20 on the d20 for an attack roll, you score a Critical Hit, and the attack hits regardless of any modifiers or the target's AC. A Critical Hit lets you roll extra dice for the attack's damage against the target. Roll all of the attack's damage dice twice and add them together. Then add any relevant modifiers.",
    ),
    cl(
        "curses",
        "curses",
        "Some game effects curse a creature or an object. The effect that confers a curse defines what the curse does. Curses can be removed by the _Remove Curse_ and _Greater Restoration_ spells or other magic that explicitly ends curses.",
    ),
    cl(
        "d20_test",
        "d20_test",
        "D20 Tests encompass the three main d20 rolls of the game: ability checks, attack rolls, and saving throws. If something in the game affects D20 Tests, it affects all three of these rolls. The GM determines whether a D20 Test is warranted in a given circumstance.",
    ),
    cl("darkness", "darkness", "An area of Darkness is Heavily Obscured."),
    cl(
        "death_saving_throw",
        "death_saving_throw",
        "A player character must make a Death Saving Throw (also called a Death Save) if they start their turn with 0 Hit Points.",
    ),
    cl(
        "difficulty_class",
        "difficulty_class",
        "A Difficulty Class (DC) is the target number for an ability check or a saving throw.",
    ),
    cl("dim_light", "dim_light", "An area with Dim Light is Lightly Obscured."),
    cl(
        "disadvantage",
        "disadvantage",
        "If you have Disadvantage on a D20 Test, roll two d20s and use the lower roll. A roll can't be affected by more than one Disadvantage, and Advantage and Disadvantage on the same roll cancel each other.",
    ),
    cl(
        "encounter",
        "encounter",
        "An encounter is a scene in an adventure that is part of at least one of the game's three pillars: social interaction, exploration, or combat.",
    ),
    cl(
        "enemy",
        "enemy",
        "A creature is your enemy if it fights against you in combat, actively works to harm you, or is designated as your enemy by the rules or GM.",
    ),
    cl("hazard", "hazard", "A hazard is an environmental danger."),
    cl("healing", "healing", "Healing is how you regain Hit Points."),
    cl(
        "heavily_obscured",
        "heavily_obscured",
        "You have the Blinded condition while trying to see something in a Heavily Obscured space.",
    ),
    cl(
        "heroic_inspiration",
        "heroic_inspiration",
        "If you (a player character) have Heroic Inspiration, you can expend it to reroll any die immediately after rolling it, and you must use the new roll.",
    ),
    cl(
        "heroic_inspiration",
        "gaining_it_again",
        "If you gain Heroic Inspiration but already have it, it's lost unless you give it to a player character who lacks it.",
    ),
    cl(
        "hit_point_dice",
        "hit_point_dice",
        'Hit Point Dice, or Hit Dice for short, help determine a player character\'s Hit Point maximum, as explained in "Character Creation." Most monsters also have Hit Dice. A creature can spend Hit Dice during a Short Rest to regain Hit Points.',
    ),
    cl(
        "illusions",
        "illusions",
        "Spells and other effects sometimes create magical illusions. Such an effect defines what the illusion does and which senses or mental faculties it deceives.",
    ),
    cl(
        "illusions",
        "illusions_in_space",
        "If an illusion manifests in space, the illusion is insubstantial and weightless, yet it seems to be affected by the environment as if the illusion were real unless the effect that created it specifies otherwise. For example, a visual illusion of a creature casts shadows and reflections, and wind appears to affect the illusory creature. Similarly, an audible illusion echoes in an echoey space.",
    ),
    cl(
        "improvised_weapons",
        "improvised_weapons",
        "An improvised weapon is an object wielded as a makeshift weapon, such as broken glass, a table leg, or a frying pan. A Simple or Martial weapon also counts as an improvised weapon if it's wielded in a way contrary to its design; if you use a Ranged weapon to make a melee attack or throw a Melee weapon that lacks the Thrown property, the weapon counts as an improvised weapon. An improvised weapon follows the rules below.",
    ),
    cl(
        "improvised_weapons",
        "proficiency",
        "_Proficiency._ Don't add your Proficiency Bonus to attack rolls with an improvised weapon.",
    ),
    cl(
        "improvised_weapons",
        "damage",
        "_Damage._ On a hit, the weapon deals 1d4 damage of a type the GM thinks is appropriate for the object.",
    ),
    cl(
        "improvised_weapons",
        "range",
        "_Range._ If you throw the weapon, it has a normal range of 20 feet and a long range of 60 feet.",
    ),
    cl(
        "improvised_weapons",
        "weapon_equivalents",
        "_Weapon Equivalents._ If an improvised weapon resembles a Simple or Martial weapon, the GM may say it functions as that weapon and uses that weapon's rules. For example, the GM could treat a table leg as a Club.",
    ),
    cl(
        "knocking_out_a_creature",
        "knocking_out",
        "When you would reduce a creature to 0 Hit Points with a melee attack, you can instead reduce the creature to 1 Hit Point. The creature then has the Unconscious condition and starts a Short Rest.",
    ),
    cl(
        "knocking_out_a_creature",
        "remaining_unconscious",
        "The creature remains Unconscious until it regains any Hit Points or until someone uses an action to administer first aid to it, which requires a successful DC 10 Wisdom (Medicine) check.",
    ),
    cl(
        "lightly_obscured",
        "lightly_obscured",
        "You have Disadvantage on Wisdom (Perception) checks to see something in a Lightly Obscured space.",
    ),
    cl(
        "magical_effect",
        "magical_effect",
        "An effect is magical if it is created by a spell, a magic item, or a phenomenon that a rule labels as magical.",
    ),
    cl(
        "monster",
        "monster",
        "A monster is a creature controlled by the GM, even if the creature is benevolent.",
    ),
    cl(
        "nonplayer_character",
        "nonplayer_character",
        "A nonplayer character (NPC) is a monster that has a personal name and a distinct personality.",
    ),
    cl(
        "object",
        "object",
        "An object is a nonliving, distinct thing. Composite things, like buildings, comprise more than one object.",
    ),
    cl(
        "per_day",
        "per_day",
        "If a rule says you can use something a certain number of times per day, that means you must finish a Long Rest to use it again after you run out of uses.",
    ),
    cl(
        "player_character",
        "player_character",
        "A player character is a character controlled by a player.",
    ),
    cl(
        "possession",
        "possession",
        "Some effects cause a creature to be possessed by another creature or entity. A possessing effect defines how the possession operates. Possession can be prevented by the _Protection from Evil and Good_ spell and ended by the _Dispel Evil and Good_ spell.",
    ),
    cl(
        "proficiency",
        "proficiency",
        "If you have proficiency with something, you can add your Proficiency Bonus to any D20 Test you make using that thing. A creature might have proficiency in a skill or saving throw or with a weapon or tool.",
    ),
    cl(
        "reaction",
        "reaction",
        "A Reaction is a special action taken in response to a trigger defined in the Reaction's description. You can take a Reaction on another creature's turn, and if you take it on your turn, you can do so even if you also take an action, a Bonus Action, or both. Once you take a Reaction, you can't take another one until the start of your next turn. The Opportunity Attack is a Reaction available to all creatures.",
    ),
    cl(
        "ritual",
        "ritual",
        "If you have a spell prepared that has the Ritual tag, you can cast that spell as a Ritual. The Ritual version of a spell takes 10 minutes longer to cast than normal. It also doesn't expend a spell slot, which means the ritual version of a spell can't be cast at a higher level.",
    ),
    cl(
        "round_down",
        "round_down",
        "Whenever you divide or multiply a number in the game, round down if you end up with a fraction, even if the fraction is one-half or greater. Some rules make an exception and tell you to round up.",
    ),
    cl("save", "save", "Save is another name for a saving throw."),
    cl(
        "saving_throw",
        "saving_throw",
        "A saving throw—also called a save—represents an attempt to avoid or resist a threat. You normally make a saving throw only when a rule requires you to do so, but you can decide to fail the save without rolling. The result of a save is detailed in the effect that allowed it. If a target is forced to make a save and lacks the ability score used by it, the target automatically fails.",
    ),
    cl(
        "shape_shifting",
        "shape_shifting",
        "If an effect, such as Wild Shape or the _Polymorph_ spell, lets you shape-shift, its description specifies what happens to you. Unless that description says otherwise, any ongoing effects on you—conditions, spells, curses, and the like—carry over from one form to the other. You revert to your true form if you die.",
    ),
    cl(
        "simultaneous_effects",
        "simultaneous_effects",
        "If two or more things happen at the same time on a turn, the person at the game table—player or GM—whose turn it is decides the order in which those things happen. For example, if two effects occur at the start of a player character's turn, the player decides which of the effects happens first.",
    ),
    cl(
        "skill",
        "skill",
        "A skill is an area of specialization associated with an ability check. If you have proficiency in a skill, you can add your Proficiency Bonus when you make an ability check associated with that skill.",
    ),
    cl(
        "spell",
        "spell",
        'A spell is a magical effect that has the characteristics described in "Spells."',
    ),
    cl(
        "spell_attack",
        "spell_attack",
        "A spell attack is an attack roll made as part of a spell or another magical effect.",
    ),
    cl(
        "spellcasting_focus",
        "spellcasting_focus",
        "A Spellcasting Focus is an object that certain creatures can use in place of a spell's Material components if those materials aren't consumed by the spell and don't have a cost specified. Some classes allow its members to use certain types of Spellcasting Focuses.",
    ),
    cl(
        "stable",
        "stable",
        "A creature is Stable if it has 0 Hit Points but isn't required to make Death Saving Throws.",
    ),
    cl(
        "target",
        "target",
        "A target is the creature or object targeted by an attack roll, forced to make a saving throw by an effect, or selected to receive the effects of a spell or another phenomenon.",
    ),
    cl(
        "telepathy",
        "telepathy",
        "Telepathy is a magical ability that allows a creature to communicate mentally with another creature within a specified range. Unless a rule states otherwise, the contacted creature doesn't need to share a language with the telepath to understand this communication, but the contacted creature must be able to understand at least one language or be telepathic itself to understand.",
    ),
    cl(
        "telepathy",
        "telepathic_contact",
        "A telepath doesn't need to see a contacted creature, and the telepath can start or end the telepathic contact at any time (no action required). Telepathic contact can't be initiated and is immediately broken if either the telepath or the other creature has the Incapacitated condition. Telepathic contact is also broken if the contacted creature is no longer within the telepathy's range or if the telepath contacts a different creature within range.",
    ),
    cl(
        "telepathy",
        "non_telepaths",
        "A creature without telepathy can receive telepathic messages but can't initiate a telepathic conversation. Once a telepathic conversation starts, the non-telepath can communicate mentally to the telepath until the telepathic connection ends.",
    ),
    cl(
        "teleportation",
        "teleportation",
        "Teleportation is a special kind of magical transportation. If you teleport, you disappear and reappear elsewhere instantly, without moving through the intervening space. This transportation doesn't expend movement unless a rule tells you otherwise, and teleportation never provokes Opportunity Attacks.",
    ),
    cl(
        "teleportation",
        "carried_equipment",
        "When you teleport, all the equipment you're wearing and carrying teleports with you. If you're touching another creature when you teleport, that creature doesn't teleport with you unless the teleportation effect says otherwise.",
    ),
    cl(
        "teleportation",
        "occupied_destination",
        "If the destination space of your teleportation is occupied by another creature or blocked by a solid obstacle, you instead appear in the nearest unoccupied space of your choice.",
    ),
    cl(
        "teleportation",
        "seeing_the_destination",
        "The description of a teleportation effect tells you if you must see the teleportation's destination.",
    ),
    cl(
        "weapon",
        "weapon",
        "A weapon is an object that is in the Simple or Martial weapon category.",
    ),
    cl(
        "weapon_attack",
        "weapon_attack",
        "A weapon attack is an attack roll made with a weapon.",
    ),
)

# ---------------------------------------------------------------------------
# Representation proposed for the clauses above
# ---------------------------------------------------------------------------

C = EntryComponent


def play(slug: str) -> Target:
    """An accepted *Playing the Game* section."""
    return (PLAY, f"play.{slug}")


def eq(key: str) -> Target:
    """An accepted Equipment record."""
    return (EQUIPMENT, f"equipment.{key}")


SPELLS_PART: Target = (SPELLS, UNRESOLVED_TARGET)
CHARACTER_CREATION_PART: Target = (CHARACTER_CREATION, UNRESOLVED_TARGET)
SPELL_COMPONENTS: Target = (SPELLS, "spells.components")

#: Rules Glossary terms a rule here depends on, by printed pattern. Matched as
#: one alternation, longest first, so a longer name is never read as a
#: shorter one inside it ("Death Saving Throw", not "Saving Throw"); a
#: ``None`` slug consumes a name no entry defines. An entry never cites itself.
#: "Hit Point maximum" is cited whole, as the character-origins-feats batch
#: cites it, never truncated to "Hit Point".
GLOSSARY_TERMS: tuple[tuple[str, str | None], ...] = (
    ("Hit Point maximum", "hit_points"),
    ("Death Saving Throws?", "death_saving_throw"),
    ("Death Saves?", "death_saving_throw"),
    ("Hit Point Dice", "hit_point_dice"),
    ("Hit Dice", "hit_point_dice"),
    ("Hit Points?", "hit_points"),
    ("Proficiency Bonus", None),
    ("Opportunity Attacks?", "opportunity_attacks"),
    ("Bonus Actions?", "bonus_action"),
    ("D20 Tests?", "d20_test"),
    ("Advantage", "advantage"),
    ("Disadvantage", "disadvantage"),
    ("Heavily Obscured", "heavily_obscured"),
    ("Lightly Obscured", "lightly_obscured"),
    ("Blinded", "blinded"),
    ("Unconscious", "unconscious"),
    ("Incapacitated", "incapacitated"),
    ("Long Rest", "long_rest"),
    ("Short Rest", "short_rest"),
    ("Friendly", "friendly"),
    ("Hostile", "hostile"),
    ("Indifferent", "indifferent"),
    ("ability checks?", "ability_check"),
    ("attack rolls?", "attack_roll"),
    ("saving throws?", "saving_throw"),
)
_TERMS = re.compile(
    "|".join(
        rf"\b(?:{p})\b" for p, _ in sorted(GLOSSARY_TERMS, key=lambda t: -len(t[0]))
    )
)
_SLUGS = {p: s for p, s in GLOSSARY_TERMS}


def _slug_of(printed: str) -> str | None:
    (slug,) = {s for p, s in _SLUGS.items() if re.fullmatch(p, printed)}
    return slug


def glossary_refs(entry: str, texts: tuple[str, ...]) -> tuple[tuple[str, str], ...]:
    """Each other glossary entry *texts*' prose prints, once, at its first name."""
    refs: dict[str, str] = {}
    for text in texts:
        if "<t" in text or "</t" in text:
            continue
        for m in _TERMS.finditer(text):
            slug = _slug_of(m.group())
            if slug is not None and slug != entry:
                refs.setdefault(slug, m.group())
    return tuple((printed, slug) for slug, printed in refs.items())


#: The twelve actions, as the *Action* entry's table prints them.
ACTIONS: tuple[tuple[str, str], ...] = tuple(
    (name, name.lower())
    for name in (
        "Attack",
        "Dodge",
        "Influence",
        "Search",
        "Dash",
        "Help",
        "Magic",
        "Study",
        "Disengage",
        "Hide",
        "Ready",
        "Utilize",
    )
)
WEAPON_CATEGORY: tuple[str, Target] = ("Simple", eq("weapons.category"))

#: Explicit pointers, by component; glossary terms are added from each
#: component's prose by :func:`glossary_refs`.
EXPLICIT_REFS: dict[tuple[str, str], tuple[tuple[str, Target], ...]] = {
    # The table is the entry's list of the actions "defined elsewhere".
    ("action", "action"): ACTIONS,
    ("armor_training", "armor_training"): (
        ("Light", eq("armor.category")),
        ("Shield", eq("armor.shield")),
    ),
    ("hit_point_dice", "hit_point_dice"): (
        ("Character Creation", CHARACTER_CREATION_PART),
    ),
    ("improvised_weapons", "improvised_weapons"): (
        WEAPON_CATEGORY,
        ("Ranged weapon", eq("weapons.melee_or_ranged")),
        ("Thrown property", eq("weapons.thrown")),
    ),
    ("improvised_weapons", "weapon_equivalents"): (WEAPON_CATEGORY,),
    ("spell", "spell"): (("Spells", SPELLS_PART),),
    ("spellcasting_focus", "spellcasting_focus"): (
        ("Material components", SPELL_COMPONENTS),
    ),
    ("weapon", "weapon"): (WEAPON_CATEGORY,),
}

#: Components whose outcome the rule leaves to the GM.
GM_LATITUDE: frozenset[tuple[str, str]] = frozenset(
    {
        ("ally", "ally"),
        ("d20_test", "d20_test"),
        ("enemy", "enemy"),
        ("improvised_weapons", "damage"),
        ("improvised_weapons", "weapon_equivalents"),
    }
)
#: Rules whose applicability turns on fiction the projection cannot enumerate.
CONTEXTUAL: frozenset[tuple[str, str]] = frozenset(
    {
        ("illusions", "illusions_in_space"),
        ("improvised_weapons", "improvised_weapons"),
    }
)


def _components() -> tuple[EntryComponent, ...]:
    out = []
    for entry, key, _, texts in CLAUSES:
        explicit = EXPLICIT_REFS.get((entry, key), ())
        printed = {text for text, _ in explicit}
        refs = explicit + tuple(
            (text, slug)
            for text, slug in glossary_refs(entry, texts)
            if text not in printed
            and scoped(slug) not in {scoped(t) for _, t in explicit}
        )
        reason = (
            GM
            if (entry, key) in GM_LATITUDE
            else CTX if (entry, key) in CONTEXTUAL else NO_USE
        )
        out.append(C(entry, key, P, reason, refs=refs))
    return tuple(out)


COMPONENTS: tuple[EntryComponent, ...] = _components()

#: No leaf frames or is excluded beyond each entry's own heading.
FRAMING: tuple[tuple[str, str], ...] = ()

#: Every *See also*: (entry, exact text, the pointers it prints, in order).
SEE_ALSO: tuple[tuple[str, str, tuple[tuple[str, Target], ...]], ...] = (
    (
        "ability_check",
        '_See also_ "Playing the Game" ("D20 Tests" and "Proficiency").',
        (("D20 Tests", play("d20_tests")), ("Proficiency", play("proficiency"))),
    ),
    (
        "ability_score_and_modifier",
        '_See also_ "Playing the Game" ("The Six Abilities").',
        (("The Six Abilities", play("six_abilities")),),
    ),
    (
        "action",
        '_See also_ "Playing the Game" ("Actions").',
        (("Actions", play("actions")),),
    ),
    (
        "advantage",
        '_See also_ "Playing the Game" ("D20 Tests").',
        (("D20 Tests", play("d20_tests")),),
    ),
    ("adventure", '_See also_ "Encounter."', (("Encounter", "encounter"),)),
    (
        "armor_training",
        '_See also_ "Disadvantage" and "Equipment" ("Armor").',
        (("Disadvantage", "disadvantage"), ("Armor", eq("armor"))),
    ),
    (
        "attitude",
        '_See also_ "Friendly," "Hostile," "Indifferent," and "Influence."',
        (
            ("Friendly", "friendly"),
            ("Hostile", "hostile"),
            ("Indifferent", "indifferent"),
            ("Influence", "influence"),
        ),
    ),
    (
        "attunement",
        '_See also_ "Equipment" ("Magic Items").',
        (("Magic Items", eq("magic_items")),),
    ),
    (
        "bonus_action",
        '_See also_ "Playing the Game" ("Actions").',
        (("Actions", play("actions")),),
    ),
    (
        "bright_light",
        '_See also_ "Playing the Game" ("Exploration").',
        (("Exploration", play("exploration")),),
    ),
    ("campaign", '_See also_ "Adventure."', (("Adventure", "adventure"),)),
    ("cantrip", '_See also_ "Spells."', (("Spells", SPELLS_PART),)),
    (
        "character_sheet",
        '_See also_ "Character Creation."',
        (("Character Creation", CHARACTER_CREATION_PART),),
    ),
    ("creature", '_See also_ "Creature Type."', (("Creature Type", "creature_type"),)),
    (
        "critical_hit",
        '_See also_ "Playing the Game" ("Damage and Healing").',
        (("Damage and Healing", play("damage_and_healing")),),
    ),
    (
        "d20_test",
        '_See also_ "Playing the Game" ("D20 Tests").',
        (("D20 Tests", play("d20_tests")),),
    ),
    (
        "darkness",
        '_See also_ "Heavily Obscured" and "Playing the Game" ("Exploration").',
        (
            ("Heavily Obscured", "heavily_obscured"),
            ("Exploration", play("exploration")),
        ),
    ),
    (
        "death_saving_throw",
        '_See also_ "Playing the Game" ("Damage and Healing").',
        (("Damage and Healing", play("damage_and_healing")),),
    ),
    (
        "difficulty_class",
        '_See also_ "Playing the Game" ("D20 Tests").',
        (("D20 Tests", play("d20_tests")),),
    ),
    (
        "dim_light",
        '_See also_ "Lightly Obscured" and "Playing the Game" ("Exploration").',
        (
            ("Lightly Obscured", "lightly_obscured"),
            ("Exploration", play("exploration")),
        ),
    ),
    (
        "disadvantage",
        '_See also_ "Playing the Game" ("D20 Tests").',
        (("D20 Tests", play("d20_tests")),),
    ),
    (
        "encounter",
        '_See also_ "Playing the Game" ("Social Interaction," "Exploration," and "Combat").',
        (
            ("Social Interaction", play("social_interaction")),
            ("Exploration", play("exploration")),
            ("Combat", play("combat")),
        ),
    ),
    (
        "hazard",
        '_See also_ "Burning," "Dehydration," "Falling," "Malnutrition," and "Suffocation."',
        (
            ("Burning", "burning"),
            ("Dehydration", "dehydration"),
            ("Falling", "falling"),
            ("Malnutrition", "malnutrition"),
            ("Suffocation", "suffocation"),
        ),
    ),
    (
        "healing",
        '_See also_ "Playing the Game" ("Damage and Healing").',
        (("Damage and Healing", play("damage_and_healing")),),
    ),
    (
        "heavily_obscured",
        '_See also_ "Blinded," "Darkness," and "Playing the Game" ("Exploration").',
        (
            ("Blinded", "blinded"),
            ("Darkness", "darkness"),
            ("Exploration", play("exploration")),
        ),
    ),
    ("hit_point_dice", '_See also_ "Short Rest."', (("Short Rest", "short_rest"),)),
    (
        "lightly_obscured",
        '_See also_ "Dim Light" and "Playing the Game" ("Exploration").',
        (("Dim Light", "dim_light"), ("Exploration", play("exploration"))),
    ),
    (
        "monster",
        '_See also_ "Creature" and "NPC."',
        (("Creature", "creature"), ("NPC", "nonplayer_character")),
    ),
    ("nonplayer_character", '_See also_ "Monster."', (("Monster", "monster"),)),
    (
        "object",
        '_See also_ "Breaking Objects."',
        (("Breaking Objects", "breaking_objects"),),
    ),
    (
        "player_character",
        '_See also_ "Character Creation."',
        (("Character Creation", CHARACTER_CREATION_PART),),
    ),
    (
        "proficiency",
        '_See also_ "Playing the Game" ("Proficiency").',
        (("Proficiency", play("proficiency")),),
    ),
    (
        "reaction",
        '_See also_ "Opportunity Attacks" and "Playing the Game" ("Actions").',
        (
            ("Opportunity Attacks", "opportunity_attacks"),
            ("Actions", play("actions")),
        ),
    ),
    ("ritual", '_See also_ "Spells."', (("Spells", SPELLS_PART),)),
    ("save", '_See also_ "Saving Throw."', (("Saving Throw", "saving_throw"),)),
    (
        "saving_throw",
        '_See also_ "Playing the Game" ("D20 Tests").',
        (("D20 Tests", play("d20_tests")),),
    ),
    (
        "skill",
        '_See also_ "Playing the Game" ("Proficiency").',
        (("Proficiency", play("proficiency")),),
    ),
    (
        "spell_attack",
        '_See also_ "Spells" ("Casting Spells").',
        (("Casting Spells", SPELLS_PART),),
    ),
    (
        "spellcasting_focus",
        '_See also_ "Spells" ("Casting Spells").',
        (("Casting Spells", SPELLS_PART),),
    ),
    (
        "stable",
        '_See also_ "Playing the Game" ("Damage and Healing").',
        (("Damage and Healing", play("damage_and_healing")),),
    ),
    (
        "weapon",
        '_See also_ "Equipment" ("Weapons").',
        (("Weapons", eq("weapons")),),
    ),
    ("weapon_attack", '_See also_ "Weapon."', (("Weapon", "weapon"),)),
)

#: Supporting spans: (entry, text, component supported or ``None`` for the
#: record). *See also* pointers identify.
SUPPORTING: tuple[tuple[str, str, str | None], ...] = tuple(
    (entry, text, None) for entry, text, _ in SEE_ALSO
)
#: Record-owned references: (entry, printed text, target, texts of the spans the
#: pointer is read from).
RECORD_REFERENCES: tuple[RecordReference, ...] = tuple(
    (entry, printed, target, (text,))
    for entry, text, pointers in SEE_ALSO
    for printed, target in pointers
)

IN_BATCH: frozenset[str] = frozenset(s for s, _, _ in ENTRIES)


def _pointers() -> list[tuple[str, Target]]:
    """Every reference the batch drafts, as (printed text, target): each
    component's own, and a record's only where no component of it states it.
    """
    stated = [(c.entry, text, t) for c in COMPONENTS for text, t in c.refs]
    owned = {
        (e, text, t)
        for e, text, t, _ in RECORD_REFERENCES
        if (e, text, t) not in stated
    }
    return [(text, t) for _, text, t in (*stated, *owned)]


def accepted_context_targets() -> tuple[Target, ...]:
    """The accepted records this batch's references cite."""
    return tuple(
        sorted(
            {
                t
                for _, t in _pointers()
                if scoped(t)[1] != UNRESOLVED_TARGET
                and not (isinstance(t, str) and t in IN_BATCH)
            },
            key=scoped,
        )
    )


def batch() -> EntryBatch:
    """The tables above, read at call time so tests can mutate them."""
    return EntryBatch(
        origin=ORIGIN,
        proposal_origin=f"{ORIGIN} (CRD Issue 5d rules-glossary-completion batch; unaccepted)",
        unit_prefix="rules-glossary-completion",
        parent=PARENT,
        entries=ENTRIES,
        expected_leaves=133,
        clauses=CLAUSES,
        framing=FRAMING,
        components=COMPONENTS,
        supporting=SUPPORTING,
        record_references=RECORD_REFERENCES,
    )


def build(session: Session) -> Built:
    """Derive the rules-glossary-completion proposal from the release *session* published."""
    return build_entry_batch(session, batch(), published_release_binding(session))


def unresolved() -> list[tuple[str, str]]:
    """Printed pointers whose destination has no record, as (scope, text)."""
    return sorted(
        (scope, text)
        for text, t in _pointers()
        for scope, key in (scoped(t),)
        if key == UNRESOLVED_TARGET
    )


def expected_representation_findings() -> list[str]:
    """Every out-of-batch target: the accepted ones stay unknown to the batch alone."""
    return sorted(
        [
            *unknown_target_findings(
                RECORD_REFERENCES, COMPONENTS, accepted_context_targets()
            ),
            *(f"reference {s}:{t!r}: unresolved reference" for s, t in unresolved()),
        ]
    )


def main(db: str) -> int:
    out = Path(__file__).resolve().parent / PROPOSAL_FILE
    return emit(db, build, out, expected_representation_findings())


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
