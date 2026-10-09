# ruff: noqa: E501  -- clause literals are verbatim source text, kept whole to be greppable
"""Author the **core-play-completion** proposal: four whole sections, three entries.

REVIEW MATERIAL for CRD Issue 5d (#137) over the qualified 5c release
``9717e288-c099-5217-b2d2-f89aeabd7b73`` / ``5.2.1-corpus.883aabdf-462``. It
emits an *unaccepted* ``5d-proposal-2`` artifact. It accepts nothing, publishes
nothing, writes nothing under ``oracles/``, and imports no earlier batch's
content, identity or authority: every leaf is read afresh from the release.

Scope, 85 leaves, one review unit per record:

* *Playing the Game > Rhythm of Play* (6 leaves), ``play.rhythm_of_play``;
* *Playing the Game > The Six Abilities* (11), ``play.six_abilities``,
  including the *Exceptions Supersede General Rules* and *Round Down* sidebars
  the release places in it;
* *Playing the Game > Social Interaction* (13), ``play.social_interaction``;
* *Playing the Game > Exploration* (46), ``play.exploration``, **less** its
  *Interacting with Objects > Breaking Objects* subsection (3 leaves), which the
  accepted ``play.exploration.breaking_objects`` already owns, Marching Order
  sidebar included. The subsection is left out by ``Placement.omit``, so no
  leaf has two owners;
* *Rules Glossary > Armor Class* (3), *Challenge Rating* (2) and *Expertise*
  (4), ``ENTRY`` each.

The three entries close the three targets the accepted batches cite and no
accepted record defines: ``glossary.armor_class`` (``play.d20_tests`` /
``compare_to_target``), ``glossary.challenge_rating`` (``play.proficiency`` /
``proficiency_bonus``) and ``glossary.expertise`` (``play.proficiency``). No
accepted reference with an empty target points into this batch's sections, so
no reference resolution is drafted.

The chapter title leaf ``# Playing the Game`` sits in the chapter container,
outside every section; it stays unowned (review packet §1).

This file is literal review data only; the assembly is the committed shared
:mod:`afterworlds.ingestion.mechanical.authoring`. ``CLAUSES`` is the source
review; ``COMPONENTS`` is the representation proposed for it; expected rules
come from ``CLAUSES`` alone.

Authoring conventions (as the eight accepted batches):

* A typed fact is used only where it is true under the conditions the typed
  surface states. A condition the closed vocabulary cannot state stays in the
  same component's governing prose, beside the fact it conditions. A lead that
  conditions a list ("Each travel pace has a game effect", "Rules Glossary
  defines the following hazards") is governing prose of the component that
  holds the list.
* One source statement, one typed copy. A restatement of an accepted rule is
  prose: the base AC here restates ``play.d20_tests``, the free object
  interaction restates ``play.combat``, the Expertise doubling sits under the
  multiplication limit ``play.proficiency`` types.
* Examples, sidebar titles and chapter pointers are supporting spans of the
  component they illustrate or of the record.
* References: every explicit pointer and each accepted glossary term a rule
  depends on. A pointer to a named glossary entry resolves to that entry's key
  whether or not it is accepted yet; one with no record yet reports an unknown
  target. A pointer to a part with no record ("Equipment", "Gameplay
  Toolbox") is a reference in that part's scope with no target, reported
  unresolved. Terms that are only mentioned (Dim Light, Darkness, Proficiency
  Bonus) and the "Tools" and "Adventuring Gear" sections of Equipment stay
  unreferenced.

Run: ``python issue-5d-core-play-completion-generator.py <published afterworlds.db>``
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
from afterworlds.ingestion.mechanical.models import ComponentHandling
from afterworlds.ingestion.mechanical.representation import (
    AbilityScore,
    AdvantageFact,
    AdvantageState,
    ComponentOption,
    ConditionEffectFact,
    ConditionEffectKind,
    ConditionKind,
    RecordKind,
    RollActor,
    RollContext,
    RollSpec,
    Skill,
)
from afterworlds.ingestion.mechanical.schema_lift import (
    SCHEMA_15_HASH,
    SCHEMA_15_VERSION,
)

ORIGIN = "issue-5d-core-play-completion-generator.py"
PROPOSAL_FILE = "issue-5d-core-play-completion-PROPOSAL.json"
PARENT = ("Rules Glossary", "Rules Definitions")
PLAY = "srd-5.2.1/playing-the-game"
#: The parts this batch's pointers name, formed from the release's own part
#: names under the ``<release-family>/<section-slug>`` convention ``PLAY`` uses.
EQUIPMENT = "srd-5.2.1/equipment"
GAMEPLAY_TOOLBOX = "srd-5.2.1/gameplay-toolbox"
#: The target of a printed pointer whose destination has no record yet. It is
#: reported as ``unresolved reference`` until a reviewed resolution names one;
#: naming a key here would guess at a record nobody has authored.
UNRESOLVED_TARGET = ""

#: (record slug, printed container label, record kind), in printed order.
ENTRIES: tuple[tuple[str, str, RecordKind], ...] = (
    ("rhythm_of_play", "Rhythm of Play", RecordKind.GENERAL_RULE),
    ("six_abilities", "The Six Abilities", RecordKind.GENERAL_RULE),
    ("social_interaction", "Social Interaction", RecordKind.GENERAL_RULE),
    ("exploration", "Exploration", RecordKind.GENERAL_RULE),
    ("armor_class", "Armor Class", RecordKind.GLOSSARY_RULE),
    ("challenge_rating", "Challenge Rating", RecordKind.GLOSSARY_RULE),
    ("expertise", "Expertise", RecordKind.GLOSSARY_RULE),
)

#: The four *Playing the Game* sections, keyed as the accepted sections are.
#: ``play.exploration`` is the section record the accepted
#: ``play.exploration.breaking_objects`` was keyed to stay clear of.
PLACEMENTS: dict[str, Placement] = {
    "rhythm_of_play": Placement(
        "play.rhythm_of_play",
        ("Playing the Game", "Rhythm of Play"),
        "## Rhythm of Play",
    ),
    "six_abilities": Placement(
        "play.six_abilities",
        ("Playing the Game", "The Six Abilities"),
        "## The Six Abilities",
    ),
    "social_interaction": Placement(
        "play.social_interaction",
        ("Playing the Game", "Social Interaction"),
        "## Social Interaction",
    ),
    "exploration": Placement(
        "play.exploration",
        ("Playing the Game", "Exploration"),
        "## Exploration",
        omit=(("Exploration", "Interacting with Objects", "Breaking Objects"),),
    ),
}

# ---------------------------------------------------------------------------
# Reason codes and handling
# ---------------------------------------------------------------------------
CTX = "contextual_applicability"
GM = "gamemaster_latitude"
NO_USE = "no_identified_structured_use"
S, M, P = (
    ComponentHandling.STRUCTURED,
    ComponentHandling.MIXED,
    ComponentHandling.PROSE_BOUND,
)
PROSE = None

# ---------------------------------------------------------------------------
# Table leaves, written as their rows
# ---------------------------------------------------------------------------
ABILITY_DESCRIPTIONS_TABLE = html_table(
    "Ability Descriptions",
    ("Ability", "Score Measures …"),
    [
        ("Strength", "Physical might"),
        ("Dexterity", "Agility, reflexes, and balance"),
        ("Constitution", "Health and stamina"),
        ("Intelligence", "Reasoning and memory"),
        ("Wisdom", "Perceptiveness and mental fortitude"),
        ("Charisma", "Confidence, poise, and charm"),
    ],
)
ABILITY_SCORES_TABLE = html_table(
    "Ability Scores",
    ("Score", "Meaning"),
    [
        (
            "1",
            "This is the lowest a score can normally go. If an effect reduces a score to 0, that effect explains what happens.",
        ),
        ("2–9", "This represents a weak capability."),
        ("10–11", "This represents the human average."),
        ("12–19", "This represents a strong capability."),
        (
            "20",
            "This is the highest an adventurer's score can go unless a feature says otherwise.",
        ),
        ("21–29", "This represents an extraordinary capability."),
        ("30", "This is the highest a score can go."),
    ],
)
#: The negative modifiers print U+2212 MINUS SIGN, not a hyphen.
ABILITY_MODIFIERS_TABLE = html_table(
    "Ability Modifiers",
    ("Score", "Modifier", "Score", "Modifier"),
    [
        ("1", "−5", "16–17", "+3"),
        ("2–3", "−4", "18–19", "+4"),
        ("4–5", "−3", "20–21", "+5"),
        ("6–7", "−2", "22–23", "+6"),
        ("8–9", "−1", "24–25", "+7"),
        ("10–11", "+0", "26–27", "+8"),
        ("12–13", "+1", "28–29", "+9"),
        ("14–15", "+2", "30", "+10"),
    ],
)
#: The corrected source prints the two header rows official p.12 does
#: (correction family K), which ``html_table``'s single header row cannot
#: name, so the leaf's text is written out.
TRAVEL_PACE_TABLE = (
    "**Travel Pace**\n\n<table>\n  <thead>\n    <tr>\n      <th></th>\n"
    '      <th colspan="3">Distance Traveled Per …</th>\n    </tr>\n'
    "    <tr>\n      <th>Pace</th>\n      <th>Minute</th>\n      <th>Hour</th>\n"
    "      <th>Day</th>\n    </tr>\n  </thead>\n  <tbody>\n"
    + "".join(
        f"    <tr>\n      <td>{pace}</td>\n      <td>{minute}</td>\n"
        f"      <td>{hour}</td>\n      <td>{day}</td>\n    </tr>\n"
        for pace, minute, hour, day in (
            ("Fast", "400 feet", "4 miles", "30 miles"),
            ("Normal", "300 feet", "3 miles", "24 miles"),
            ("Slow", "200 feet", "2 miles", "18 miles"),
        )
    )
    + "  </tbody>\n</table>"
)

# ---------------------------------------------------------------------------
# Source review: what each printed clause must be read as
# ---------------------------------------------------------------------------

PACE_LEAD = "Each travel pace has a game effect, as defined below."
FAST_PACE = "_Fast._ Traveling at a Fast pace imposes Disadvantage on a traveler's Wisdom (Perception or Survival) and Dexterity (Stealth) checks."
NORMAL_PACE = "_Normal._ Traveling at a Normal pace imposes Disadvantage on Dexterity (Stealth) checks."
SLOW_PACE = "_Slow._ Traveling at a Slow pace grants Advantage on Wisdom (Perception or Survival) checks."

#: (entry, component key, expected fact families + ``None`` for governing
#: prose, clause texts). Every rule-stating sentence of the batch is named here.
CLAUSES: tuple[tuple[str, str, tuple[str | None, ...], tuple[str, ...]], ...] = (
    # == Rhythm of Play (p5) ==================================================
    # The lead governs the three steps, so they are one component's prose.
    (
        "rhythm_of_play",
        "basic_pattern",
        (PROSE,),
        (
            "The three main pillars of D&D play are social interaction, exploration, and combat. Whichever one you're experiencing, the game unfolds according to this basic pattern:",
            "**1: The Game Master Describes a Scene.** The GM tells the players where their adventurers are and what's around them (how many doors lead out of a room, what's on a table, and so on).",
            "**2: The Players Describe What Their Characters Do.** Typically, the characters stick together as they travel through a dungeon or another environment. Sometimes different adventurers do different things: one adventurer might search a treasure chest while a second examines a mysterious symbol engraved on a wall and a third keeps watch for monsters. Outside combat, the GM ensures that every character has a chance to act and decides how to resolve their activity. In combat, the characters take turns.",
            "**3: The GM Narrates the Results of the Adventurers' Actions.** Sometimes resolving a task is easy. If an adventurer walks across a room and tries to open a door, the GM might say the door opens and describe what lies beyond. But the door might be locked, the floor might hide a trap, or some other circumstance might make it challenging for an adventurer to complete a task. In those cases, the GM might ask the player to roll a die to help determine what happens. Describing the results often leads to another decision point, which brings the game back to step 1.",
        ),
    ),
    (
        "rhythm_of_play",
        "every_session",
        (PROSE,),
        (
            "This pattern holds during every game session (each time you sit down to play D&D), whether the adventurers are talking to a noble, exploring a ruin, or fighting a dragon. In certain situations—particularly combat—the action is more structured, and everyone takes turns.",
        ),
    ),
    # == The Six Abilities (pp5-6) ============================================
    (
        "six_abilities",
        "six_abilities",
        (PROSE,),
        (
            "All creatures—characters and monsters—have six abilities that measure physical and mental characteristics, as shown on the Ability Descriptions table.",
            ABILITY_DESCRIPTIONS_TABLE,
        ),
    ),
    (
        "six_abilities",
        "ability_scores",
        (PROSE,),
        (
            "Each ability has a score from 1 to 20, although some monsters have a score as high as 30. The score represents the magnitude of an ability. The Ability Scores table summarizes what the scores mean.",
            ABILITY_SCORES_TABLE,
        ),
    ),
    (
        "six_abilities",
        "ability_modifiers",
        (PROSE,),
        (
            'Each ability has a modifier that you apply whenever you make a D20 Test with that ability (explained in "D20 Tests"). An ability modifier is derived from its score, as shown in the Ability Modifiers table.',
            ABILITY_MODIFIERS_TABLE,
        ),
    ),
    # The two sidebars the release places in Ability Modifiers. Each is one
    # blockquote leaf; each clause is an exact run of its text between the
    # ``>`` markers.
    (
        "six_abilities",
        "exceptions_supersede",
        (PROSE,),
        (
            "General rules govern each part of the game.",
            "That's a general rule, and a general rule is in effect as long as something in the game doesn't explicitly say otherwise.",
            "The game also includes elements—class features, feats, weapon properties, spells, magic items, monster abilities, and the like—that sometimes contradict a general rule. When an exception and a general rule disagree, the exception wins.",
        ),
    ),
    (
        "six_abilities",
        "round_down",
        (PROSE,),
        (
            "Whenever you divide or multiply a number in the game, round down if you end up with a fraction, even if the fraction is one-half or greater. Some rules make an exception and tell you to round up.",
        ),
    ),
    # == Social Interaction (pp10-11) =========================================
    (
        "social_interaction",
        "social_interaction",
        (PROSE,),
        (
            "During their adventures, player characters meet many different people and face some monsters that would rather talk than fight. In those situations, it's time for social interaction, which takes many forms.",
            "The Game Master assumes the roles of any nonplayer characters who are participating.",
        ),
    ),
    (
        "social_interaction",
        "attitudes",
        (PROSE,),
        (
            'An NPC\'s attitude toward your character is Friendly, Indifferent, or Hostile, as defined in "Rules Glossary." Friendly NPCs are predisposed to help, and Hostile ones are inclined to hinder.',
        ),
    ),
    (
        "social_interaction",
        "roleplaying",
        (PROSE,),
        (
            "Roleplaying is, literally, the act of playing out a role. In this case, it's you as a player determining how your character thinks, acts, and talks. Roleplaying is part of every aspect of the game, and it comes to the fore during social interactions.",
            "As you roleplay, consider whether you prefer an active approach or a descriptive approach.",
        ),
    ),
    (
        "social_interaction",
        "npc_reactions",
        (PROSE,),
        (
            "The GM uses an NPC's personality and your character's actions and attitudes to determine how an\nNPC reacts.",
        ),
    ),
    (
        "social_interaction",
        "influencing_npcs",
        (PROSE,),
        (
            "When interacting with an NPC, pay attention to the GM's portrayal of the NPC's personality. You might be able to learn an NPC's goals and then use that information to influence the NPC.",
            "If you offer NPCs something they want or play on their sympathies, fears, or goals, you can form friendships, ward off violence, or learn a key piece of information. On the other hand, if you insult a proud warrior or speak ill of a noble's allies, your efforts to convince or deceive will likely fail.",
        ),
    ),
    (
        "social_interaction",
        "social_checks",
        (PROSE,),
        (
            "Ability checks can be key in determining the outcome of a social interaction. Your roleplaying efforts can alter an NPC's attitude, but there might still be an element of chance if the GM wants dice to play a role in determining an NPC's response to you. In such situations, the GM will typically ask you to take the Influence action.",
        ),
    ),
    (
        "social_interaction",
        "skill_approach",
        (PROSE,),
        (
            "Pay attention to your skill proficiencies when thinking of how you will interact with an NPC; use an approach that relies on your group's skill proficiencies.",
        ),
    ),
    # == Exploration (pp11-12) ================================================
    (
        "exploration",
        "equipment_help",
        (PROSE,),
        ("As adventurers explore, their equipment can help them in many ways.",),
    ),
    (
        "exploration",
        "weapons_beyond_battle",
        (PROSE,),
        (
            'The weapons in "Equipment" can also be used for more than battle; you could use a Quarterstaff, for example, to push a sinister-looking button that you\'re reluctant to touch.',
        ),
    ),
    (
        "exploration",
        "lightly_obscured",
        ("advantage", PROSE),
        (
            "An area might be Lightly or Heavily Obscured. In a Lightly Obscured area—such as an area with Dim Light, patchy fog, or moderate foliage—you have Disadvantage on Wisdom (Perception) checks that rely on sight.",
        ),
    ),
    (
        "exploration",
        "heavily_obscured",
        ("condition_effect", PROSE),
        (
            'A Heavily Obscured area—such as an area with Darkness, heavy fog, or dense foliage—is opaque. You have the Blinded condition (see "Rules Glossary") when trying to see something there.',
        ),
    ),
    # The lead defines the categories the three paragraphs name.
    (
        "exploration",
        "light",
        (PROSE,),
        (
            "The presence or absence of light determines the category of illumination in an area, as defined below.",
            "**Bright Light.** Bright Light lets most creatures see normally. Even gloomy days provide Bright Light, as do torches, lanterns, fires, and other sources of illumination within a specific radius.",
            "**Dim Light.** Dim Light, also called shadows, creates a Lightly Obscured area. An area of Dim Light is usually a boundary between Bright Light and surrounding Darkness. The soft light of twilight and dawn also counts as Dim Light. A full moon might bathe the land in Dim Light.",
            "**Darkness.** Darkness creates a Heavily Obscured area. Characters face Darkness outdoors at night (even most moonlit nights), within the confines of an unlit dungeon, or in an area of magical Darkness.",
        ),
    ),
    (
        "exploration",
        "special_senses",
        (PROSE,),
        (
            'Some creatures have special senses that help them perceive things in certain situations. "Rules Glossary" defines the following special senses:',
            "- Blindsight\n- Darkvision\n- Tremorsense\n- Truesight",
        ),
    ),
    (
        "exploration",
        "hiding",
        (PROSE,),
        (
            "Adventurers and monsters often hide, whether to spy on one another, sneak past a guardian, or set an ambush. The Game Master decides when circumstances are appropriate for hiding. When you try to hide, you take the Hide action.",
        ),
    ),
    (
        "exploration",
        "interacting_with_objects",
        (PROSE,),
        (
            "Interacting with objects is often simple to resolve. The player tells the GM that their character is doing something, such as moving a lever or opening\na door, and the GM describes what happens. Sometimes, however, rules govern what you can do with an object, as detailed in the following sections.",
        ),
    ),
    (
        "exploration",
        "what_is_an_object",
        (PROSE,),
        (
            "For the purpose of the rules, an object is a discrete, inanimate item like a window, door, sword, book, table, chair, or stone. It isn't a building or a vehicle, which are composed of many objects.",
        ),
    ),
    (
        "exploration",
        "time_limited_interactions",
        (PROSE,),
        (
            'When time is short, such as in combat, interactions with objects are limited: one free interaction per turn. That interaction must occur during a creature\'s movement or action. Any additional interactions require the Utilize action, as explained in "Combat" later in "Playing the Game."',
        ),
    ),
    (
        "exploration",
        "finding_hidden_objects",
        (PROSE,),
        (
            "When your character searches for hidden things, such as a secret door or a trap, the GM typically asks you to make a Wisdom (Perception) check, provided you describe the character searching in the hidden object's vicinity. On a success, you find the object, other important details, or both.",
            "If you describe your character searching nowhere near a hidden object, a Wisdom (Perception) check won't reveal the object, no matter the check's total.",
        ),
    ),
    (
        "exploration",
        "carrying_objects",
        (PROSE,),
        (
            'You can usually carry your gear and treasure without worrying about the weight of those objects. If you try to haul an unusually heavy object or a massive number of lighter objects, the GM might require you to abide by the rules for carrying capacity in "Rules Glossary."',
        ),
    ),
    (
        "exploration",
        "hazards",
        (PROSE,),
        (
            'Monsters are the main perils characters face, but other dangers await. "Rules Glossary" defines the following hazards:',
            "- Burning\n- Dehydration\n- Falling\n- Malnutrition\n- Suffocation",
        ),
    ),
    (
        "exploration",
        "travel",
        (PROSE,),
        (
            "During an adventure, the characters might travel long distances on trips that could take hours or days. The GM can summarize this travel without calculating exact distances or travel times, or the GM might have you use the travel pace rules below.",
        ),
    ),
    (
        "exploration",
        "travel_pace",
        (PROSE,),
        (
            'While traveling outside combat, a group can move at a Fast, Normal, or Slow pace, as shown on the Travel Pace table. The table states how far the party can move in a period of time; if riding horses or other mounts, the group can move twice that distance for 1 hour, after which the mounts need a Short or Long Rest before they can move at that increased pace again (see "Equipment" for a selection of mounts for sale). "Gameplay Toolbox" has rules that affect which pace you can choose in certain types of terrain.',
            TRAVEL_PACE_TABLE,
        ),
    ),
    # The lead and the three effects are one component's governing prose, and
    # each pace is one option read from the lead and its own paragraph.
    (
        "exploration",
        "pace_effects",
        ("advantage", PROSE),
        (PACE_LEAD, FAST_PACE, NORMAL_PACE, SLOW_PACE),
    ),
    (
        "exploration",
        "vehicles",
        (PROSE,),
        (
            'Travelers in wagons, carriages, or other land vehicles choose a pace as normal. Characters in a waterborne vessel are limited to the speed of the vessel, and they don\'t choose a travel pace. Depending on the vessel and the size of the crew, ships might be able to travel for up to 24 hours per day. "Equipment" includes vehicles for sale.',
        ),
    ),
    # == Rules Glossary: Armor Class (p177) ===================================
    (
        "armor_class",
        "armor_class",
        (PROSE,),
        (
            "An Armor Class (AC) is the target number for an attack roll. AC represents how difficult it is to hit a target.",
        ),
    ),
    (
        "armor_class",
        "base_ac",
        (PROSE,),
        (
            "Your base AC calculation is 10 plus your Dexterity modifier. If a rule gives you another base AC calculation, you choose which calculation to use; you can't use more than one.",
        ),
    ),
    # == Rules Glossary: Challenge Rating (p178) ==============================
    (
        "challenge_rating",
        "challenge_rating",
        (PROSE,),
        (
            "Challenge Rating (CR) summarizes the threat a monster poses to a group of four player characters. Compare a monster's CR to the characters' level. If the CR is higher, the monster is likely a danger. If the CR is lower, the monster likely poses little threat. But circumstances and the number of player characters can significantly alter how threatening a monster is in actual play.",
        ),
    ),
    # == Rules Glossary: Expertise (p182) =====================================
    (
        "expertise",
        "expertise",
        (PROSE,),
        (
            "Expertise is a feature that enhances your use of a skill proficiency. When you make an ability check with a skill proficiency in which you have Expertise, your Proficiency Bonus is doubled for that check unless the bonus is doubled by another feature.",
        ),
    ),
    (
        "expertise",
        "gaining_expertise",
        (PROSE,),
        (
            "If you gain Expertise, you gain it in one skill in which you have proficiency. You can't have Expertise in the same skill proficiency more than once.",
        ),
    ),
)

#: (entry, leaf prefix): whole leaves that introduce the rules after them and
#: state none of their own.
FRAMING: tuple[tuple[str, str], ...] = (
    ("social_interaction", "Social interactions progress in two ways"),
    ("exploration", "Exploration involves delving"),
    ("exploration", "Some adventuring tasks"),
)

SUBSECTION_HEADING = "subsection heading: names a subsection and states no rule"

#: (entry, exact leaf contents, reason): whole leaves that only name a
#: subsection. Only headings are excluded; both Six Abilities sidebars are
#: authored. *Breaking Objects* is not listed: it is not this record's leaf.
EXCLUDED: tuple[tuple[str, tuple[str, ...], str], ...] = (
    (
        "six_abilities",
        ("### Ability Scores", "### Ability Modifiers"),
        SUBSECTION_HEADING,
    ),
    (
        "social_interaction",
        ("### Roleplaying", "### Ability Checks"),
        SUBSECTION_HEADING,
    ),
    (
        "exploration",
        (
            "### Adventuring Equipment",
            "### Vision and Light",
            "#### Obscured Areas",
            "#### Light",
            "#### Special Senses",
            "### Hiding",
            "### Interacting with Objects",
            "#### What Is an Object?",
            "#### Time-Limited Object Interactions",
            "#### Finding Hidden Objects",
            "#### Carrying Objects",
            "### Hazards",
            "### Travel",
            "#### Travel Pace",
            "#### Vehicles",
        ),
        SUBSECTION_HEADING,
    ),
)

# ---------------------------------------------------------------------------
# Representation proposed for the clauses above
# ---------------------------------------------------------------------------

C = EntryComponent


def check(state: AdvantageState, ability: AbilityScore, skill: Skill) -> AdvantageFact:
    """*state* on the subject's own *ability* (*skill*) checks."""
    return AdvantageFact(
        state, RollSpec(RollActor.SUBJECT, RollContext.ABILITY_CHECK, ability, skill)
    )


DIS, ADV = AdvantageState.DISADVANTAGE, AdvantageState.ADVANTAGE
WIS, DEX = AbilityScore.WISDOM, AbilityScore.DEXTERITY

#: The accepted *Playing the Game* destinations this batch cites.
PLAY_COMBAT = (PLAY, "play.combat")
PLAY_D20_TESTS = (PLAY, "play.d20_tests")
PLAY_PROFICIENCY = (PLAY, "play.proficiency")
EQUIPMENT_UNRESOLVED = (EQUIPMENT, UNRESOLVED_TARGET)
GAMEPLAY_TOOLBOX_UNRESOLVED = (GAMEPLAY_TOOLBOX, UNRESOLVED_TARGET)

#: The four special senses and five hazards the two lists name, each its own
#: Rules Glossary entry; only Falling is accepted.
SENSE_REFS: tuple[tuple[str, Target], ...] = tuple(
    (name, name.lower())
    for name in ("Blindsight", "Darkvision", "Tremorsense", "Truesight")
)
HAZARD_REFS: tuple[tuple[str, Target], ...] = tuple(
    (name, name.lower())
    for name in ("Burning", "Dehydration", "Falling", "Malnutrition", "Suffocation")
)

COMPONENTS: tuple[EntryComponent, ...] = (
    # == Rhythm of Play =======================================================
    C("rhythm_of_play", "basic_pattern", P, GM),
    C("rhythm_of_play", "every_session", P, CTX),
    # == The Six Abilities ====================================================
    C("six_abilities", "six_abilities", P, NO_USE),
    # "normally", "unless a feature says otherwise": the table is a guide.
    C("six_abilities", "ability_scores", P, CTX),
    # No family states the score-to-modifier derivation; the table is the
    # printed canon and the arithmetic is left to its consumer.
    C(
        "six_abilities",
        "ability_modifiers",
        P,
        NO_USE,
        refs=(("D20 Tests", PLAY_D20_TESTS),),
    ),
    C("six_abilities", "exceptions_supersede", P, CTX),
    # Rounding is arithmetic every consumer performs; no family states it.
    C("six_abilities", "round_down", P, NO_USE),
    # == Social Interaction ===================================================
    C("social_interaction", "social_interaction", P, GM),
    # Restates the three accepted attitude records, which type them.
    C(
        "social_interaction",
        "attitudes",
        P,
        NO_USE,
        refs=(
            ("Friendly", "friendly"),
            ("Indifferent", "indifferent"),
            ("Hostile", "hostile"),
        ),
    ),
    C("social_interaction", "roleplaying", P, NO_USE),
    C("social_interaction", "npc_reactions", P, GM),
    C("social_interaction", "influencing_npcs", P, GM),
    C(
        "social_interaction",
        "social_checks",
        P,
        GM,
        refs=(("Influence", "influence"),),
    ),
    C("social_interaction", "skill_approach", P, NO_USE),
    # == Exploration ==========================================================
    C("exploration", "equipment_help", P, NO_USE),
    C(
        "exploration",
        "weapons_beyond_battle",
        P,
        GM,
        refs=(("Equipment", EQUIPMENT_UNRESOLVED),),
    ),
    # "that rely on sight" stays the prose; no Applicability names Lightly
    # Obscured.
    C(
        "exploration",
        "lightly_obscured",
        M,
        CTX,
        facts=(check(DIS, WIS, Skill.PERCEPTION),),
    ),
    # "when trying to see something there": the area is what is seen, not
    # where the subject stands, so OBSCUREMENT (the subject's own state, as
    # Hide uses it) would state a different rule. The condition stays prose.
    C(
        "exploration",
        "heavily_obscured",
        M,
        CTX,
        facts=(
            ConditionEffectFact(ConditionKind.BLINDED, ConditionEffectKind.APPLIES),
        ),
        refs=(("Blinded", "blinded"),),
    ),
    C("exploration", "light", P, CTX),
    C("exploration", "special_senses", P, NO_USE, refs=SENSE_REFS),
    C("exploration", "hiding", P, GM, refs=(("Hide", "hide"),)),
    C("exploration", "interacting_with_objects", P, GM),
    C("exploration", "what_is_an_object", P, NO_USE),
    # Restates the free object interaction accepted, as prose, in Combat.
    C(
        "exploration",
        "time_limited_interactions",
        P,
        CTX,
        refs=(("Utilize", "utilize"), ("Combat", PLAY_COMBAT)),
    ),
    # "the GM typically asks"; the vicinity proviso governs the check.
    C("exploration", "finding_hidden_objects", P, GM),
    C(
        "exploration",
        "carrying_objects",
        P,
        GM,
        refs=(("carrying capacity", "carrying_capacity"),),
    ),
    C("exploration", "hazards", P, NO_USE, refs=HAZARD_REFS),
    C("exploration", "travel", P, GM),
    # No family states a travel distance or the mounts' doubled hour.
    C(
        "exploration",
        "travel_pace",
        P,
        CTX,
        refs=(
            ("Short or Long Rest", "short_rest"),
            ("Long Rest", "long_rest"),
            ("Equipment", EQUIPMENT_UNRESOLVED),
            ("Gameplay Toolbox", GAMEPLAY_TOOLBOX_UNRESOLVED),
        ),
    ),
    # A group chooses one pace; each option holds only its own pace's facts,
    # so Perception's Disadvantage (Fast) and Advantage (Slow) never meet.
    C(
        "exploration",
        "pace_effects",
        M,
        CTX,
        options=(
            ComponentOption(
                "fast",
                (
                    check(DIS, WIS, Skill.PERCEPTION),
                    check(DIS, WIS, Skill.SURVIVAL),
                    check(DIS, DEX, Skill.STEALTH),
                ),
            ),
            ComponentOption("normal", (check(DIS, DEX, Skill.STEALTH),)),
            ComponentOption(
                "slow",
                (check(ADV, WIS, Skill.PERCEPTION), check(ADV, WIS, Skill.SURVIVAL)),
            ),
        ),
        option_sources=(
            ("fast", (PACE_LEAD, FAST_PACE)),
            ("normal", (PACE_LEAD, NORMAL_PACE)),
            ("slow", (PACE_LEAD, SLOW_PACE)),
        ),
    ),
    C(
        "exploration",
        "vehicles",
        P,
        CTX,
        refs=(("Equipment", EQUIPMENT_UNRESOLVED),),
    ),
    # == Rules Glossary: Armor Class ==========================================
    C("armor_class", "armor_class", P, NO_USE),
    # Restates ``play.d20_tests`` Calculating AC and Only One Base AC, both
    # prose there; no family states a base AC formula.
    C("armor_class", "base_ac", P, CTX),
    # == Rules Glossary: Challenge Rating =====================================
    C("challenge_rating", "challenge_rating", P, GM),
    # == Rules Glossary: Expertise ============================================
    # No family states a doubled bonus; the once-only multiplication it relies
    # on is ``play.proficiency`` / ``bonus_operation_limits``.
    C("expertise", "expertise", P, NO_USE),
    C("expertise", "gaining_expertise", P, NO_USE),
)

EQUIPMENT_POINTER = 'See "Equipment" for rules on many items that are useful on adventures. The items in the "Tools" and "Adventuring Gear" sections are especially useful.'
TRAVEL_COMBAT_POINTER = 'If you need to know how fast you can move when every second matters, see the movement rules in "Combat" later in "Playing the Game."'
ATTACK_ROLL_SEE_ALSO = '_See also_ "Attack Roll."'
COMBAT_ENCOUNTERS_POINTER = '"Gameplay Toolbox" ("Combat Encounters") provides guidance to the GM on using CR while planning potential combat encounters.'
STAT_BLOCK_SEE_ALSO = '_See also_ "Stat Block."'
PROFICIENCY_SEE_ALSO = '_See also_ "Playing the Game" ("Proficiency").'

#: Supporting spans: (entry, text, component supported or ``None`` for the
#: record). Examples illustrate; sidebar titles and chapter pointers identify
#: or scope.
SUPPORTING: tuple[tuple[str, str, str | None], ...] = (
    # -- The Six Abilities ----------------------------------------------------
    ("six_abilities", "**EXCEPTIONS SUPERSEDE GENERAL RULES**", "exceptions_supersede"),
    (
        "six_abilities",
        "For example, the combat rules tell you that melee attacks use Strength and ranged attacks use Dexterity.",
        "exceptions_supersede",
    ),
    (
        "six_abilities",
        "For example, if a feature says you can make melee attacks using your Charisma, you can do so, even though that statement disagrees with the general rule.",
        "exceptions_supersede",
    ),
    ("six_abilities", "**ROUND DOWN**", "round_down"),
    # -- Social Interaction ---------------------------------------------------
    (
        "social_interaction",
        "For example, you might try to convince a burglar to confess to wrongdoing or try to flatter a guard.",
        "social_interaction",
    ),
    (
        "social_interaction",
        "A cowardly bandit might buckle under threats of imprisonment. A stubborn merchant refuses to help if the characters badger her. A vain dragon laps up flattery.",
        "npc_reactions",
    ),
    (
        "social_interaction",
        "For example, if the group needs to trick a guard into letting them into a castle, the Rogue who is proficient in Deception should lead the discussion.",
        "skill_approach",
    ),
    # -- Exploration ----------------------------------------------------------
    (
        "exploration",
        "For example, they can reach out-of-the-way places with a Ladder, perceive things they wouldn't otherwise notice with a Torch or another light source, bypass locked doors and containers with Thieves' Tools, and create obstacles for pursuers with Caltrops.",
        "equipment_help",
    ),
    ("exploration", EQUIPMENT_POINTER, None),
    ("exploration", TRAVEL_COMBAT_POINTER, None),
    # -- Rules Glossary -------------------------------------------------------
    ("armor_class", ATTACK_ROLL_SEE_ALSO, None),
    ("challenge_rating", COMBAT_ENCOUNTERS_POINTER, None),
    ("challenge_rating", STAT_BLOCK_SEE_ALSO, None),
    ("expertise", PROFICIENCY_SEE_ALSO, None),
)

#: Record-owned references: (entry, printed text, target, texts of the spans the
#: pointer is read from).
RECORD_REFERENCES: tuple[RecordReference, ...] = (
    ("exploration", "Equipment", EQUIPMENT_UNRESOLVED, (EQUIPMENT_POINTER,)),
    ("exploration", "Combat", PLAY_COMBAT, (TRAVEL_COMBAT_POINTER,)),
    ("armor_class", "Attack Roll", "attack_roll", (ATTACK_ROLL_SEE_ALSO,)),
    (
        "challenge_rating",
        "Combat Encounters",
        GAMEPLAY_TOOLBOX_UNRESOLVED,
        (COMBAT_ENCOUNTERS_POINTER,),
    ),
    ("challenge_rating", "Stat Block", "stat_block", (STAT_BLOCK_SEE_ALSO,)),
    ("expertise", "Proficiency", PLAY_PROFICIENCY, (PROFICIENCY_SEE_ALSO,)),
)

#: Targets outside this batch that no accepted record defines and this batch
#: does not author. Each citation is an expected unknown-target finding.
NEW_TARGETS: tuple[Target, ...] = (
    "attack_roll",
    "blindsight",
    "burning",
    "carrying_capacity",
    "darkvision",
    "dehydration",
    "malnutrition",
    "stat_block",
    "suffocation",
    "tremorsense",
    "truesight",
)
#: Targets outside this batch that the accepted inputs define.
ACCEPTED_CONTEXT_TARGETS: tuple[Target, ...] = (
    PLAY_COMBAT,
    PLAY_D20_TESTS,
    PLAY_PROFICIENCY,
    "blinded",
    "falling",
    "friendly",
    "hide",
    "hostile",
    "indifferent",
    "influence",
    "long_rest",
    "short_rest",
    "utilize",
)


def batch() -> EntryBatch:
    """The tables above, read at call time so tests can mutate them."""
    return EntryBatch(
        origin=ORIGIN,
        schema=(SCHEMA_15_VERSION, SCHEMA_15_HASH),
        proposal_origin=f"{ORIGIN} (CRD Issue 5d core-play completion batch; unaccepted)",
        unit_prefix="core-play-completion",
        parent=PARENT,
        entries=ENTRIES,
        expected_leaves=85,
        clauses=CLAUSES,
        framing=FRAMING,
        components=COMPONENTS,
        supporting=SUPPORTING,
        record_references=RECORD_REFERENCES,
        placements=PLACEMENTS,
        excluded=EXCLUDED,
    )


def build(session: Session) -> Built:
    """Derive the core-play-completion proposal from the release *session* published."""
    return build_entry_batch(session, batch(), published_release_binding(session))


#: Printed pointers whose destination has no record yet, as (scope, text). Each
#: stays unresolved, alone and composed, until a reviewed resolution names it.
#: "Equipment" is printed four times in Exploration: three components' own
#: references, and the record's "See "Equipment"" pointer, which cites the
#: first of them (the shared fold every accepted batch uses).
UNRESOLVED: tuple[tuple[str, str], ...] = (
    (EQUIPMENT, "Equipment"),
    (EQUIPMENT, "Equipment"),
    (EQUIPMENT, "Equipment"),
    (GAMEPLAY_TOOLBOX, "Combat Encounters"),
    (GAMEPLAY_TOOLBOX, "Gameplay Toolbox"),
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


def main(db: str) -> int:
    out = Path(__file__).resolve().parent / PROPOSAL_FILE
    return emit(db, build, out, expected_representation_findings())


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
