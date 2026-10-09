# ruff: noqa: E501  -- clause literals are verbatim source text, kept whole to be greppable
"""Author the **checks-actions-rests** proposal: three whole sections, four entries.

REVIEW MATERIAL for CRD Issue 5d (#137) over the qualified 5c release
``9717e288-c099-5217-b2d2-f89aeabd7b73`` / ``5.2.1-corpus.883aabdf-462``. It
emits an *unaccepted* ``5d-proposal-2`` artifact. It accepts nothing, publishes
nothing, writes nothing under ``oracles/``, and imports no earlier batch's
content, identity or authority: every leaf is read afresh from the release.

Scope, 118 leaves, one review unit per record:

* *Playing the Game > D20 Tests* (55 leaves), ``play.d20_tests``, ``SECTION``,
  including the *Heroic Inspiration* sidebar the release places in it. The
  section prints its steps as 4, 5 and 6; the official PDF does too, so the
  numbering is reproduced, not repaired;
* *Playing the Game > Proficiency* (22), ``play.proficiency``, ``SECTION``;
* *Playing the Game > Actions* (15), ``play.actions``, ``SECTION``;
* *Rules Glossary > Damage Types* (3), *Dead* (3), *Long Rest* (12) and
  *Short Rest* (8), ``ENTRY`` each.

These close the five targets the accepted batches cite: ``play.actions``,
``glossary.short_rest``, ``glossary.long_rest``, ``glossary.damage_types`` and
``glossary.dead``. ``play.d20_tests`` is also the printed destination of the
accepted attack-roll pointer (``play.combat`` / ``attack_structure``,
``"Playing the Game"``). That pointer is **not** retargeted here: accepted
references are immutable, and a reference resolution can name only an
accepted destination, so the resolution is drafted for review, not emitted.

This file is literal review data only; the assembly is the committed shared
:mod:`afterworlds.ingestion.mechanical.authoring`. ``CLAUSES`` is the source
review; ``COMPONENTS`` is the representation proposed for it; expected rules
come from ``CLAUSES`` alone.

Authoring conventions (as the seven accepted batches):

* A typed fact is used only where it is true under the conditions the typed
  surface states. A condition the closed vocabulary cannot state stays in the
  same component's governing prose, beside the fact it conditions.
* One source statement, one typed copy. Where two sites print one rule, the
  site the family was designed from carries the fact and the other is prose
  with a reference to it: the D20 Tests *Proficiency Bonus* subsections
  restate the Proficiency section, which types them; the Actions table and
  *Exhaustion Reduced* restate accepted glossary records.
* Examples, list leads, sidebar titles and chapter pointers are supporting
  spans of the component they illustrate. Pointers into this batch's own
  record ("described later in "Playing the Game"" for Advantage, "see the
  sidebar below") name no reference.
* References: every explicit pointer and each accepted glossary term a rule
  depends on. A pointer to a part with no record yet ("Equipment", "Spells",
  "Character Creation") or to no single record (step 5's "Rules Glossary") is
  a reference in that part's scope with no target, reported unresolved until a
  real destination exists. Unaccepted glossary terms that are only mentioned
  (Advantage, Heroic Inspiration, Bonus Action, Reaction, Critical Hit, Hit
  Point Dice, Attunement) stay unreferenced.

Run: ``python issue-5d-checks-actions-rests-generator.py <published afterworlds.db>``
"""

from __future__ import annotations

import sys
from pathlib import Path

from sqlalchemy.orm import Session

from afterworlds.ingestion.mechanical.authoring import (
    GLOSSARY_SCOPE,
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
from afterworlds.ingestion.mechanical.representation import (
    ActionAllowanceFact,
    ActionCost,
    AdvantageFact,
    AdvantageState,
    AllowanceScope,
    ConditionEffectFact,
    ConditionEffectKind,
    ConditionKind,
    ConditionLevelFact,
    HealingFact,
    LevelDirection,
    ProficiencyApplicationFact,
    ProficiencyBonusBandFact,
    ProficiencyBonusOperation,
    ProficiencyBonusOperationLimitFact,
    ProficiencyBonusUse,
    ProficiencyBonusUseFact,
    ProficiencyKind,
    RecordKind,
    RetryRestrictionFact,
    RollActor,
    RollContext,
    RollSpec,
    TimeUnit,
)
from afterworlds.ingestion.mechanical.schema_lift import (
    SCHEMA_15_HASH,
    SCHEMA_15_VERSION,
)

ORIGIN = "issue-5d-checks-actions-rests-generator.py"
PROPOSAL_FILE = "issue-5d-checks-actions-rests-PROPOSAL.json"
PARENT = ("Rules Glossary", "Rules Definitions")
PLAY = "srd-5.2.1/playing-the-game"
#: The parts this batch's pointers name, formed from the release's own part
#: names under the ``<release-family>/<section-slug>`` convention ``PLAY`` uses.
EQUIPMENT = "srd-5.2.1/equipment"
SPELLS = "srd-5.2.1/spells"
CHARACTER_CREATION = "srd-5.2.1/character-creation"
#: The target of a printed pointer whose destination has no record yet. It is
#: reported as ``unresolved reference`` until a reviewed resolution names one;
#: naming a key here would guess at a record nobody has authored.
UNRESOLVED_TARGET = ""

#: (record slug, printed container label, record kind), in printed order.
ENTRIES: tuple[tuple[str, str, RecordKind], ...] = (
    ("d20_tests", "D20 Tests", RecordKind.GENERAL_RULE),
    ("proficiency", "Proficiency", RecordKind.GENERAL_RULE),
    ("actions", "Actions", RecordKind.GENERAL_RULE),
    ("damage_types", "Damage Types", RecordKind.GLOSSARY_RULE),
    ("dead", "Dead", RecordKind.GLOSSARY_RULE),
    ("long_rest", "Long Rest", RecordKind.GLOSSARY_RULE),
    ("short_rest", "Short Rest", RecordKind.GLOSSARY_RULE),
)

#: The three *Playing the Game* sections, keyed as the accepted
#: ``play.combat`` and ``play.damage_and_healing`` are. ``play.actions`` is the
#: key the accepted Combat section already cites.
PLACEMENTS: dict[str, Placement] = {
    "d20_tests": Placement(
        "play.d20_tests", ("Playing the Game", "D20 Tests"), "## D20 Tests"
    ),
    "proficiency": Placement(
        "play.proficiency", ("Playing the Game", "Proficiency"), "## Proficiency"
    ),
    "actions": Placement("play.actions", ("Playing the Game", "Actions"), "## Actions"),
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
ABILITY_CHECK_EXAMPLES_TABLE = html_table(
    "Ability Check Examples",
    ("Ability", "Make a Check To …"),
    [
        ("Strength", "Lift, push, pull, or break something"),
        ("Dexterity", "Move nimbly, quickly, or quietly"),
        ("Constitution", "Push your body beyond normal limits"),
        ("Intelligence", "Reason or remember"),
        ("Wisdom", "Notice things in the environment or in creatures' behavior"),
        ("Charisma", "Influence, entertain, or deceive"),
    ],
)
#: Written out rather than through ``html_table``: its third row prints two
#: empty cells and its last one ``colspan`` cell, which the row helper does
#: not render.
TYPICAL_DC_TABLE = (
    "**Typical Difficulty Classes**\n\n<table>\n  <thead>\n    <tr>\n"
    "      <th>Task Difficulty</th>\n      <th>DC</th>\n"
    "      <th>Task Difficulty</th>\n      <th>DC</th>\n    </tr>\n  </thead>\n"
    "  <tbody>\n"
    "    <tr>\n      <td>Very easy</td>\n      <td>5</td>\n"
    "      <td>Very hard</td>\n      <td>25</td>\n    </tr>\n"
    "    <tr>\n      <td>Easy</td>\n      <td>10</td>\n"
    "      <td>Nearly impossible</td>\n      <td>30</td>\n    </tr>\n"
    "    <tr>\n      <td>Medium</td>\n      <td>15</td>\n"
    "      <td></td>\n      <td></td>\n    </tr>\n"
    '    <tr>\n      <td>Hard</td>\n      <td>20</td>\n      <td colspan="2"></td>\n'
    "    </tr>\n  </tbody>\n</table>"
)
SAVING_THROW_EXAMPLES_TABLE = html_table(
    "Saving Throw Examples",
    ("Ability", "Make a Save To …"),
    [
        ("Strength", "Physically resist direct force"),
        ("Dexterity", "Dodge out of harm's way"),
        ("Constitution", "Endure a toxic hazard"),
        ("Intelligence", "Recognize an illusion as fake"),
        ("Wisdom", "Resist a mental assault"),
        ("Charisma", "Assert your identity"),
    ],
)
ATTACK_ROLL_ABILITIES_TABLE = html_table(
    "Attack Roll Abilities",
    ("Ability", "Attack Type"),
    [
        (
            "Strength",
            "Melee attack with a weapon or an Unarmed Strike (see Rules Glossary)",
        ),
        ("Dexterity", "Ranged attack with a weapon"),
        (
            "Varies",
            "Spell attack (the ability used is determined by the spellcaster's spellcasting feature, as explained in Spells)",
        ),
    ],
)
PROFICIENCY_BONUS_TABLE = html_table(
    "Proficiency Bonus",
    ("Level or CR", "Bonus", "Level or CR", "Bonus"),
    [
        ("Up to 4", "+2", "17–20", "+6"),
        ("5–8", "+3", "21–24", "+7"),
        ("9–12", "+4", "25–28", "+8"),
        ("13–16", "+5", "29–30", "+9"),
    ],
)
SKILLS_TABLE = html_table(
    "Skills",
    ("Skill", "Ability", "Example Uses"),
    [
        (
            "Acrobatics",
            "Dexterity",
            "Stay on your feet in a tricky situation, or perform an acrobatic stunt.",
        ),
        (
            "Animal Handling",
            "Wisdom",
            "Calm or train an animal, or get an animal to behave in a certain way.",
        ),
        (
            "Arcana",
            "Intelligence",
            "Recall lore about spells, magic items, and the planes of existence.",
        ),
        (
            "Athletics",
            "Strength",
            "Jump farther than normal, stay afloat in rough water, or break something.",
        ),
        (
            "Deception",
            "Charisma",
            "Tell a convincing lie, or wear a disguise convincingly.",
        ),
        (
            "History",
            "Intelligence",
            "Recall lore about historical events, people, nations, and cultures.",
        ),
        ("Insight", "Wisdom", "Discern a person's mood and intentions."),
        (
            "Intimidation",
            "Charisma",
            "Awe or threaten someone into doing what you want.",
        ),
        (
            "Investigation",
            "Intelligence",
            "Find obscure information in books, or deduce how something works.",
        ),
        (
            "Medicine",
            "Wisdom",
            "Diagnose an illness, or determine what killed the recently slain.",
        ),
        (
            "Nature",
            "Intelligence",
            "Recall lore about terrain, plants, animals, and weather.",
        ),
        (
            "Perception",
            "Wisdom",
            "Using a combination of senses, notice something that's easy to miss.",
        ),
        ("Performance", "Charisma", "Act, tell a story, perform music, or dance."),
        (
            "Persuasion",
            "Charisma",
            "Honestly and graciously convince someone of something.",
        ),
        (
            "Religion",
            "Intelligence",
            "Recall lore about gods, religious rituals, and holy symbols.",
        ),
        (
            "Sleight of Hand",
            "Dexterity",
            "Pick a pocket, conceal a handheld object, or perform legerdemain.",
        ),
        (
            "Stealth",
            "Dexterity",
            "Escape notice by moving quietly and hiding behind things.",
        ),
        (
            "Survival",
            "Wisdom",
            "Follow tracks, forage, find a trail, or avoid natural hazards.",
        ),
    ],
)
ACTIONS_TABLE = html_table(
    "Actions",
    ("Action", "Summary"),
    [
        ("Attack", "Attack with a weapon or an Unarmed Strike."),
        (
            "Dash",
            "For the rest of the turn, give yourself extra movement equal to your Speed.",
        ),
        (
            "Disengage",
            "Your movement doesn't provoke Opportunity Attacks for the rest of the turn.",
        ),
        (
            "Dodge",
            "Until the start of your next turn, attack rolls against you have Disadvantage, and you make Dexterity saving throws with Advantage. You lose this benefit if you have the Incapacitated condition or if your Speed is 0.",
        ),
        (
            "Help",
            "Help another creature's ability check or attack roll, or administer first aid.",
        ),
        ("Hide", "Make a Dexterity (Stealth) check."),
        (
            "Influence",
            "Make a Charisma (Deception, Intimidation, Performance, or Persuasion) or Wisdom (Animal Handling) check to alter a creature's attitude.",
        ),
        ("Magic", "Cast a spell, use a magic item, or use a magical feature."),
        ("Ready", "Prepare to take an action in response to a trigger you define."),
        ("Search", "Make a Wisdom (Insight, Medicine, Perception, or Survival) check."),
        (
            "Study",
            "Make an Intelligence (Arcana, History, Investigation, Nature, or Religion) check.",
        ),
        ("Utilize", "Use a nonmagical object."),
    ],
)
DAMAGE_TYPES_TABLE = html_table(
    "Damage Types",
    ("Type", "Examples"),
    [
        ("Acid", "Corrosive liquids, digestive enzymes"),
        ("Bludgeoning", "Blunt objects, constriction, falling"),
        ("Cold", "Freezing water, icy blasts"),
        ("Fire", "Flames, unbearable heat"),
        ("Force", "Pure magical energy"),
        ("Lightning", "Electricity"),
        ("Necrotic", "Life-draining energy"),
        ("Piercing", "Fangs, puncturing objects"),
        ("Poison", "Toxic gas, venom"),
        ("Psychic", "Mind-rending energy"),
        ("Radiant", "Holy energy, searing radiation"),
        ("Slashing", "Claws, cutting objects"),
        ("Thunder", "Concussive sound"),
    ],
)

# ---------------------------------------------------------------------------
# Source review: what each printed clause must be read as
# ---------------------------------------------------------------------------

#: The Heroic Inspiration sidebar is one blockquote leaf; each clause below is
#: an exact run of its text between the ``>`` markers.
HEROIC_INSPIRATION_USE = "Sometimes the GM or a rule gives you Heroic Inspiration. If you have Heroic Inspiration, you can expend it to reroll any die immediately after rolling it, and you must use the new roll."

#: (entry, component key, expected fact families + ``None`` for governing
#: prose, clause texts). Every rule-stating sentence of the batch is named here.
CLAUSES: tuple[tuple[str, str, tuple[str | None, ...], tuple[str, ...]], ...] = (
    # == D20 Tests (pp6-8) ====================================================
    (
        "d20_tests",
        "d20_tests",
        (PROSE,),
        (
            "When the outcome of an action is uncertain, the game uses a d20 roll to determine success or failure. These rolls are called D20 Tests, and they come in three kinds: ability checks, saving throws, and attack rolls.",
        ),
    ),
    (
        "d20_tests",
        "roll_1d20",
        (PROSE,),
        (
            '**4: Roll 1d20.** You always want to roll high. If the roll has Advantage or Disadvantage (described later in "Playing the Game"), you roll two d20s, but you use the number from only one of them—the higher one if you have Advantage or the lower one if you have Disadvantage.',
        ),
    ),
    (
        "d20_tests",
        "add_modifiers",
        (PROSE,),
        (
            "**5: Add Modifiers.** Add these modifiers to the number rolled on the d20:",
            '- **The Relevant Ability Modifier.** "Playing the Game" and "Rules Glossary" explain which ability modifiers to use for various D20 Tests.',
            '- **Your Proficiency Bonus If Relevant.** Each creature has a Proficiency Bonus, a number added when making a D20 Test that uses something, such as a skill, in which the creature has proficiency. See "Proficiency" later in "Playing the Game."',
            "- **Circumstantial Bonuses and Penalties.** A class feature, a spell, or another rule might give a bonus or penalty to the die roll.",
        ),
    ),
    (
        "d20_tests",
        "compare_to_target",
        (PROSE,),
        (
            '**6: Compare the Total to a Target Number.** If the total of the d20 and its modifiers equals or exceeds the target number, the D20 Test succeeds. Otherwise, it fails. The Game Master determines target numbers and tells players whether their rolls are successful. The target number for an ability check or a saving throw is called a Difficulty Class (DC). The target number for an attack roll is called an Armor Class (AC), which appears on a character sheet or in a stat block (see "Rules Glossary").',
        ),
    ),
    # -- Ability Checks -------------------------------------------------------
    (
        "d20_tests",
        "ability_checks",
        (PROSE,),
        (
            "An ability check represents a creature using talent and training to try to overcome a challenge, such as forcing open a stuck door, picking a lock, entertaining a crowd, or deciphering a cipher. The GM and the rules often call for an ability check when a creature attempts something other than an attack that has a chance of meaningful failure. When the outcome is uncertain and narratively interesting, the dice determine the result.",
        ),
    ),
    (
        "d20_tests",
        "check_ability_modifier",
        (PROSE,),
        (
            "An ability check is named for the ability modifier it uses: a Strength check, an Intelligence check, and so on. Different ability checks are called for in different situations, depending on which ability is most relevant.",
        ),
    ),
    (
        "d20_tests",
        "check_proficiency",
        (PROSE,),
        (
            "Add your Proficiency Bonus to an ability check when the GM determines that a skill or tool proficiency is relevant to the check and you have that proficiency.",
        ),
    ),
    (
        "d20_tests",
        "check_dc",
        (PROSE,),
        (
            "The Difficulty Class of an ability check represents the task's difficulty. The more difficult the task, the higher its DC. The rules provide DCs for certain checks, but the GM ultimately sets them.",
        ),
    ),
    (
        "d20_tests",
        "typical_dcs",
        (PROSE,),
        (
            "The Typical Difficulty Classes table presents a range of possible DCs for ability checks.",
            TYPICAL_DC_TABLE,
        ),
    ),
    # -- Saving Throws --------------------------------------------------------
    (
        "d20_tests",
        "saving_throws",
        (PROSE,),
        (
            "A saving throw—also called a save—represents an attempt to evade or resist a threat, such as a fiery explosion, a blast of poisonous gas, or a spell trying to invade your mind. You don't normally choose to make a save; you must make one because your character or a monster (if you're the GM) is at risk. A save's result is detailed in the effect that caused it.",
        ),
    ),
    (
        "d20_tests",
        "choosing_to_fail",
        (PROSE,),
        (
            "If you don't want to resist the effect, you can choose to fail the save without rolling.",
        ),
    ),
    (
        "d20_tests",
        "save_ability_modifier",
        (PROSE,),
        (
            "Saving throws are named for the ability modifiers they use: a Constitution saving throw, a Wisdom saving throw, and so on. Different saving throws are used to resist different kinds of effects, as shown on the Saving Throw Examples table.",
        ),
    ),
    (
        "d20_tests",
        "save_proficiency",
        (PROSE,),
        (
            'You add your Proficiency Bonus to your saving throw if you have proficiency in that kind of save. See "Proficiency" later in "Playing the Game."',
        ),
    ),
    (
        "d20_tests",
        "save_dc",
        (PROSE,),
        (
            "The Difficulty Class for a saving throw is determined by the effect that causes it or by the GM.",
            "Monster abilities that call for saves specify the DC.",
        ),
    ),
    # -- Attack Rolls ---------------------------------------------------------
    (
        "d20_tests",
        "attack_rolls",
        (PROSE,),
        (
            'An attack roll determines whether an attack hits a target. An attack roll hits if the roll equals or exceeds the target\'s Armor Class. Attack rolls usually occur in battle, described in "Combat" later in "Playing the Game," but the GM might also ask for an attack roll in other situations, such as an archery competition.',
        ),
    ),
    (
        "d20_tests",
        "attack_ability_modifier",
        (PROSE,),
        (
            "The Attack Roll Abilities table shows which ability modifier to use for different types of attack rolls.",
            ATTACK_ROLL_ABILITIES_TABLE,
        ),
    ),
    (
        "d20_tests",
        "other_ability_modifiers",
        (PROSE,),
        ("Some features let you use different ability modifiers from those listed.",),
    ),
    (
        "d20_tests",
        "attack_proficiency",
        (PROSE,),
        (
            "You add your Proficiency Bonus to your attack roll when you attack using a weapon you have proficiency with, as well as when you attack with a spell.",
        ),
    ),
    (
        "d20_tests",
        "armor_class",
        (PROSE,),
        (
            'A creature\'s Armor Class represents how well the creature avoids being wounded in combat. The AC of a character is determined at character creation (see "Character Creation"), whereas the AC of a monster appears in its stat block.',
        ),
    ),
    (
        "d20_tests",
        "base_ac",
        (PROSE,),
        (
            "_Calculating AC._ All creatures start with the same base AC calculation:",
            "**Base AC** = 10 + the creature's Dexterity modifier",
            "A creature's AC can then be modified by armor, magic items, spells, and more.",
        ),
    ),
    (
        "d20_tests",
        "only_one_base_ac",
        (PROSE,),
        (
            "_Only One Base AC._ Some spells and class features give characters a different way to calculate their AC. A character with multiple features that give different ways to calculate AC must choose which one to use; only one base calculation can be in effect for a creature.",
        ),
    ),
    (
        "d20_tests",
        "natural_20",
        (PROSE,),
        (
            'If you roll a 20 on the d20 (called a "natural 20") for an attack roll, the attack hits regardless of any modifiers or the target\'s AC. This is called a Critical Hit (see "Combat" later in "Playing the Game").',
        ),
    ),
    (
        "d20_tests",
        "natural_1",
        (PROSE,),
        (
            'If you roll a 1 on the d20 (a "natural 1") for an attack roll, the attack misses regardless of any modifiers or the target\'s AC.',
        ),
    ),
    # -- Advantage/Disadvantage -----------------------------------------------
    (
        "d20_tests",
        "advantage_disadvantage",
        (PROSE,),
        (
            "Sometimes a D20 Test is modified by Advantage or Disadvantage. Advantage reflects the positive circumstances surrounding a d20 roll, while Disadvantage reflects negative circumstances.",
            "You usually acquire Advantage or Disadvantage through the use of special abilities and actions. The GM can also decide that circumstances grant Advantage or impose Disadvantage.",
        ),
    ),
    (
        "d20_tests",
        "roll_two_d20s",
        (PROSE,),
        (
            "When a roll has either Advantage or Disadvantage, roll a second d20 when you make the roll. Use the higher of the two rolls if you have Advantage, and use the lower roll if you have Disadvantage.",
        ),
    ),
    (
        "d20_tests",
        "no_stacking",
        (PROSE,),
        (
            "If multiple situations affect a roll and they all grant Advantage on it, you still roll only two d20s. Similarly, if multiple situations impose Disadvantage on a roll, you roll only two d20s.",
            "If circumstances cause a roll to have both Advantage and Disadvantage, the roll has neither of them, and you roll one d20. This is true even if multiple circumstances impose Disadvantage and only one grants Advantage or vice versa. In such a situation, you have neither Advantage nor Disadvantage.",
        ),
    ),
    (
        "d20_tests",
        "rerolls",
        (PROSE,),
        (
            "When you have Advantage or Disadvantage and something in the game lets you reroll or replace the d20, you can reroll or replace only one die, not both. You choose which one.",
        ),
    ),
    # The Heroic Inspiration sidebar, which the release places in this section.
    (
        "d20_tests",
        "heroic_inspiration",
        (PROSE,),
        (HEROIC_INSPIRATION_USE,),
    ),
    (
        "d20_tests",
        "only_one_heroic_inspiration",
        (PROSE,),
        (
            "_Only One at a Time._ You can never have more than one instance of Heroic Inspiration. If something gives you Heroic Inspiration and you already have it, you can give it to a player character in your group who lacks it.",
        ),
    ),
    (
        "d20_tests",
        "gaining_heroic_inspiration",
        (PROSE,),
        (
            "_Gaining Heroic Inspiration._ Your GM can give you Heroic Inspiration for a variety of reasons. Typically, GMs award it when you do something particularly heroic, in character, or entertaining. It's a reward for making the game more fun for everyone playing.",
            "Other rules might allow your character to gain Heroic Inspiration independent of the GM's decision.",
        ),
    ),
    # == Proficiency (pp8-10) =================================================
    (
        "proficiency",
        "proficiency_bonus",
        (PROSE,),
        (
            'All creatures have a Proficiency Bonus, which reflects the impact that training has on the creature\'s capabilities. A character\'s Proficiency Bonus increases as the character gains levels (described in "Character Creation"). A monster\'s Proficiency Bonus is based on its Challenge Rating (see "Rules Glossary").',
        ),
    ),
    (
        "proficiency",
        "proficiency_bonus_bands",
        ("proficiency_bonus_band",),
        (PROFICIENCY_BONUS_TABLE,),
    ),
    (
        "proficiency",
        "d20_test_application",
        (PROSE,),
        (
            "This bonus is applied to a D20 Test when the creature has proficiency in a skill, in a saving throw, or with an item that the creature uses to make the D20 Test.",
        ),
    ),
    (
        "proficiency",
        "spell_uses",
        ("proficiency_bonus_use",),
        (
            "The bonus is also used for spell attacks and for calculating the DC of saving throws for spells.",
        ),
    ),
    (
        "proficiency",
        "bonus_operation_limits",
        ("proficiency_bonus_operation_limit",),
        (
            "Your Proficiency Bonus can't be added to a die roll or another number more than once.",
            "Occasionally, a Proficiency Bonus might be multiplied or divided (doubled or halved, for example) before being added.",
            "Whenever the bonus is used, it can be multiplied only once and divided only once.",
        ),
    ),
    (
        "proficiency",
        "skills",
        (PROSE,),
        (
            'Most ability checks involve using a skill, which represents a category of things creatures try to do with an ability check. The descriptions of the actions you take (see "Actions" later in "Playing the Game") specify which skill applies if you make an ability check for that action, and many other rules note when a skill is relevant. The GM has the ultimate say on whether a skill is relevant in a situation.',
        ),
    ),
    (
        "proficiency",
        "skill_proficiency",
        ("proficiency_application", PROSE),
        (
            "If a creature is proficient in a skill, the creature applies its Proficiency Bonus to ability checks involving that skill. Without proficiency in a skill, a creature can still make ability checks involving that skill but doesn't add its Proficiency Bonus.",
        ),
    ),
    (
        "proficiency",
        "skill_list",
        (PROSE,),
        (
            SKILLS_TABLE,
            "The skills are shown on the Skills table, which notes example uses for each skill proficiency as well as the ability check the skill most often applies to.",
        ),
    ),
    (
        "proficiency",
        "determining_skills",
        (PROSE,),
        (
            "A character's starting skill proficiencies are determined at character creation, and a monster's skill proficiencies appear in its stat block.",
        ),
    ),
    (
        "proficiency",
        "saving_throw_proficiency",
        ("proficiency_application", PROSE),
        (
            "Proficiency in a saving throw lets a character add their Proficiency Bonus to saves that use a particular ability.",
            "Some monsters also have saving throw proficiencies, as noted in their stat blocks.",
        ),
    ),
    (
        "proficiency",
        "class_saving_throws",
        (PROSE,),
        (
            "Each class gives proficiency in at least two saving throws, representing that class's training in evading or resisting certain threats.",
        ),
    ),
    (
        "proficiency",
        "equipment_proficiency",
        (PROSE,),
        (
            "A character gains proficiency with various weapons and tools from their class and background.",
        ),
    ),
    (
        "proficiency",
        "weapon_proficiency",
        ("proficiency_application", PROSE),
        (
            "**Weapons.** Anyone can wield a weapon, but proficiency makes you better at wielding it. If you have proficiency with a weapon, you add your Proficiency Bonus to attack rolls you make with it.",
        ),
    ),
    (
        "proficiency",
        "tool_proficiency",
        ("proficiency_application", "advantage", PROSE),
        (
            "**Tools.** If you have proficiency with a tool, you can add your Proficiency Bonus to any ability check you make that uses the tool. If you have proficiency in the skill that's also used with that check, you have Advantage on the check too.",
        ),
    ),
    # == Actions (pp10-11) ====================================================
    (
        "actions",
        "main_actions",
        (PROSE,),
        (
            'When you do something other than moving or communicating, you typically take an action. The Action table lists the game\'s main actions, which are defined in more detail in "Rules Glossary."',
            ACTIONS_TABLE,
        ),
    ),
    (
        "actions",
        "improvised_actions",
        (PROSE,),
        (
            "Player characters and monsters can also do things not covered by these actions. Many class features and other abilities provide additional action options, and you can improvise other actions. When you describe an action not detailed elsewhere in the rules, the Game Master tells you whether that action is possible and what kind of D20 Test you need to make, if any.",
        ),
    ),
    (
        "actions",
        "one_thing_at_a_time",
        (PROSE,),
        (
            'The game uses actions to govern how much you can do at one time. You can take only one action at a time. This principle is most important in combat, as explained in "Combat" later in "Playing the Game."',
        ),
    ),
    (
        "actions",
        "bonus_actions",
        (PROSE,),
        (
            "Various class features, spells, and other abilities let you take an additional action on your turn called a Bonus Action.",
            "You can take a Bonus Action only when a special ability, a spell, or another feature of the game states that you can do something as a Bonus Action. You otherwise don't have a Bonus Action to take.",
        ),
    ),
    (
        "actions",
        "one_bonus_action",
        ("action_allowance", PROSE),
        (
            "You can take only one Bonus Action on your turn, so you must choose which Bonus Action to use if you have more than one available.",
        ),
    ),
    (
        "actions",
        "bonus_action_timing",
        (PROSE,),
        (
            "You choose when to take a Bonus Action during your turn unless the Bonus Action's timing is specified. Anything that deprives you of your ability to take actions also prevents you from taking a Bonus Action.",
        ),
    ),
    (
        "actions",
        "reactions",
        (PROSE,),
        (
            "Certain special abilities, spells, and situations allow you to take a special action called a Reaction. A Reaction is an instant response to a trigger of some kind, which can occur on your turn or on someone else's.",
        ),
    ),
    (
        "actions",
        "one_reaction",
        (PROSE,),
        (
            "When you take a Reaction, you can't take another one until the start of your next turn. If the reaction interrupts another creature's turn, that creature can continue its turn right after the Reaction.",
        ),
    ),
    (
        "actions",
        "reaction_timing",
        (PROSE,),
        (
            "In terms of timing, a Reaction takes place immediately after its trigger unless the Reaction's description says otherwise.",
        ),
    ),
    # == Rules Glossary: Damage Types (p180) ==================================
    (
        "damage_types",
        "damage_types",
        (PROSE,),
        (
            "Attacks and other harmful effects deal different types of damage. Damage types have no rules of their own, but other rules, such as Resistance, rely on the types.",
        ),
    ),
    (
        "damage_types",
        "damage_type_examples",
        (PROSE,),
        (
            "The Damage Types table offers examples to help a GM assign a type to a new effect.",
            DAMAGE_TYPES_TABLE,
        ),
    ),
    # == Rules Glossary: Dead (p180) ==========================================
    (
        "dead",
        "dead",
        (PROSE,),
        (
            "A dead creature has no Hit Points and can't regain them unless it is first revived by magic such as the _Raise Dead_ or _Revivify_ spell. When such a spell is cast, the spirit knows who is casting it and can refuse. The spirit of a dead creature has left the body and departed for the Outer Planes, and reviving the creature requires calling the spirit back.",
        ),
    ),
    (
        "dead",
        "returning_to_life",
        (PROSE,),
        (
            "If the creature returns to life, the revival effect determines the creature's current Hit Points. Unless otherwise stated, the creature returns to life with any conditions, magical contagions, or curses that were affecting it at death if the durations of those effects are still ongoing.",
            "If the creature had Attunement to one or more magic items, it is no longer attuned to them.",
        ),
    ),
    (
        "dead",
        "exhaustion_on_revival",
        ("condition_level", PROSE),
        (
            "If the creature died with any Exhaustion levels, it returns with 1 fewer level.",
        ),
    ),
    # == Rules Glossary: Long Rest (p185) =====================================
    (
        "long_rest",
        "long_rest",
        (PROSE,),
        (
            "A Long Rest is a period of extended downtime—at least 8 hours—available to any creature. During a Long Rest, you sleep for at least 6 hours and perform no more than 2 hours of light activity, such as reading, talking, eating, or standing watch.",
        ),
    ),
    (
        "long_rest",
        "sleep",
        ("condition_effect", PROSE),
        ("During sleep, you have the Unconscious condition.",),
    ),
    (
        "long_rest",
        "frequency",
        ("retry_restriction", PROSE),
        (
            "After you finish a Long Rest, you must wait at least 16 hours before starting another one.",
        ),
    ),
    (
        "long_rest",
        "starting",
        (PROSE,),
        ("To start a Long Rest, you must have at least 1 Hit Point.",),
    ),
    # Each benefit is granted only by the lead's "When you finish the rest",
    # so the lead and the benefits are one component's governing prose.
    (
        "long_rest",
        "benefits",
        ("healing", PROSE),
        (
            "When you finish the rest, you gain the following benefits:",
            "**Regain All HP.** You regain all lost Hit Points and all spent Hit Point Dice. If your Hit Point maximum was reduced, it returns to normal.",
            "**Ability Scores Restored.** If any of your ability scores were reduced, they return to normal.",
            "**Exhaustion Reduced.** If you have the Exhaustion condition, its level decreases by 1.",
            "**Special Feature.** Some features are recharged by a Long Rest. If you have such a feature, it recharges in the way specified in its description.",
        ),
    ),
    (
        "long_rest",
        "interruptions",
        (PROSE,),
        (
            "_Interrupting the Rest._ A Long Rest is stopped by the following interruptions:",
            "- Rolling Initiative\n- Casting a spell other than a cantrip\n- Taking any damage\n- 1 hour of walking or other physical exertion",
            "If you rested at least 1 hour before the interruption, you gain the benefits of a Short Rest.",
        ),
    ),
    (
        "long_rest",
        "resuming",
        (PROSE,),
        (
            "You can resume a Long Rest immediately after an interruption. If you do so, the rest requires 1 additional hour per interruption to finish.",
        ),
    ),
    # == Rules Glossary: Short Rest (p187) ====================================
    (
        "short_rest",
        "short_rest",
        (PROSE,),
        (
            "A Short Rest is a 1-hour period of downtime, during which a creature does nothing more strenuous than reading, talking, eating, or standing watch.",
        ),
    ),
    (
        "short_rest",
        "starting",
        (PROSE,),
        ("To start a Short Rest, you must have at least 1 Hit Point.",),
    ),
    (
        "short_rest",
        "benefits",
        (PROSE,),
        (
            "_Benefits of the Rest._ When you finish the rest, you gain the following benefits:",
            "**Spend Hit Point Dice.** You can spend one or more of your Hit Point Dice to regain Hit Points. For each Hit Point Die you spend in this way, roll the die and add your Constitution modifier to it. You regain Hit Points equal to the total (minimum of 1 Hit Point). You can decide to spend an additional Hit Point Die after each roll.",
            "**Special Feature.** Some features are recharged by a Short Rest. If you have such a feature, it recharges in the way specified in its description.",
        ),
    ),
    (
        "short_rest",
        "interruptions",
        (PROSE,),
        (
            "_Interrupting the Rest._ A Short Rest is stopped by the following interruptions:",
            "- Rolling Initiative\n- Casting a spell other than a cantrip\n- Taking any damage",
            "An interrupted Short Rest confers no benefits.",
        ),
    ),
)

#: (entry, leaf prefix): whole leaves that introduce the rules after them and
#: state none of their own. This batch has none: every lead-in shares a leaf
#: with a rule or is a supporting span.
FRAMING: tuple[tuple[str, str], ...] = ()

SUBSECTION_HEADING = "subsection heading: names a subsection and states no rule"

#: (entry, exact leaf contents, reason): whole leaves that only name a
#: subsection. D20 Tests prints "Ability Modifier", "Proficiency Bonus" and
#: "Difficulty Class" under more than one kind of test; each printing is listed
#: where it falls. Only headings are excluded; the Heroic Inspiration sidebar is
#: authored.
EXCLUDED: tuple[tuple[str, tuple[str, ...], str], ...] = (
    (
        "d20_tests",
        (
            "### Ability Checks",
            "#### Ability Modifier",
            "#### Proficiency Bonus",
            "#### Difficulty Class",
            "### Saving Throws",
            "#### Ability Modifier",
            "#### Proficiency Bonus",
            "#### Difficulty Class",
            "### Attack Rolls",
            "#### Ability Modifier",
            "#### Proficiency Bonus",
            "#### Armor Class",
            "#### Rolling 20 or 1",
            "### Advantage/Disadvantage",
            "#### Roll Two D20s",
            "#### They Don't Stack",
            "#### Interactions with Rerolls",
        ),
        SUBSECTION_HEADING,
    ),
    (
        "proficiency",
        (
            "### The Bonus Doesn't Stack",
            "### Skill Proficiencies",
            "#### Skill List",
            "#### Determining Skills",
            "### Saving Throw Proficiencies",
            "### Equipment Proficiencies",
        ),
        SUBSECTION_HEADING,
    ),
    (
        "actions",
        ("### One Thing at a Time", "### Bonus Actions", "### Reactions"),
        SUBSECTION_HEADING,
    ),
)

# ---------------------------------------------------------------------------
# Representation proposed for the clauses above
# ---------------------------------------------------------------------------

C = EntryComponent


def own(context: RollContext) -> RollSpec:
    return RollSpec(RollActor.SUBJECT, context)


def applies(kind: ProficiencyKind, context: RollContext) -> ProficiencyApplicationFact:
    return ProficiencyApplicationFact(kind, own(context))


#: The in-batch and accepted *Playing the Game* destinations this batch cites.
PLAY_COMBAT = (PLAY, "play.combat")
PLAY_PROFICIENCY = (PLAY, "play.proficiency")
PLAY_ACTIONS = (PLAY, "play.actions")

#: The twelve actions the Actions table names, each an accepted glossary record.
ACTION_REFS: tuple[tuple[str, Target], ...] = tuple(
    (name, name.lower())
    for name in (
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
)

COMPONENTS: tuple[EntryComponent, ...] = (
    # == D20 Tests ===========================================================
    C("d20_tests", "d20_tests", P, NO_USE),
    # Dice generation and the kept die are code-owned rails; the rule's
    # meaning stays its prose. Advantage is explained later in this record.
    C("d20_tests", "roll_1d20", P, NO_USE),
    # "Playing the Game" is this record's own Ability Modifier subsections;
    # "Rules Glossary" names no entry and is left unresolved (packet §6).
    C(
        "d20_tests",
        "add_modifiers",
        P,
        CTX,
        refs=(
            ("Rules Glossary", (GLOSSARY_SCOPE, UNRESOLVED_TARGET)),
            ("Proficiency", PLAY_PROFICIENCY),
        ),
    ),
    C(
        "d20_tests",
        "compare_to_target",
        P,
        GM,
        refs=(("Armor Class", "armor_class"),),
    ),
    C("d20_tests", "ability_checks", P, GM),
    C("d20_tests", "check_ability_modifier", P, CTX),
    # Restates the skill and tool rules the Proficiency section types.
    C("d20_tests", "check_proficiency", P, GM),
    C("d20_tests", "check_dc", P, GM),
    # The table "presents a range of possible DCs"; the GM sets them.
    C("d20_tests", "typical_dcs", P, GM),
    C("d20_tests", "saving_throws", P, CTX),
    # An election, not an outcome: AutomaticOutcomeFact would state the save
    # always fails.
    C("d20_tests", "choosing_to_fail", P, NO_USE),
    C("d20_tests", "save_ability_modifier", P, CTX),
    # Restates the saving-throw rule the Proficiency section types.
    C(
        "d20_tests",
        "save_proficiency",
        P,
        NO_USE,
        refs=(("Proficiency", PLAY_PROFICIENCY),),
    ),
    C("d20_tests", "save_dc", P, GM),
    C("d20_tests", "attack_rolls", P, GM, refs=(("Combat", PLAY_COMBAT),)),
    C(
        "d20_tests",
        "attack_ability_modifier",
        P,
        NO_USE,
        refs=(
            ("Unarmed Strike", "unarmed_strike"),
            ("Spells", (SPELLS, UNRESOLVED_TARGET)),
        ),
    ),
    C("d20_tests", "other_ability_modifiers", P, CTX),
    # Restates the weapon rule and the spell-attack use the Proficiency
    # section types.
    C("d20_tests", "attack_proficiency", P, NO_USE),
    C(
        "d20_tests",
        "armor_class",
        P,
        NO_USE,
        refs=(("Character Creation", (CHARACTER_CREATION, UNRESOLVED_TARGET)),),
    ),
    # No family states a base Armor Class formula.
    C("d20_tests", "base_ac", P, NO_USE),
    C("d20_tests", "only_one_base_ac", P, CTX),
    # CriticalHitRuleFact states a *change* to when a Critical Hit is scored;
    # the ordinary natural-20 and natural-1 rules have no family.
    C("d20_tests", "natural_20", P, NO_USE, refs=(("Combat", PLAY_COMBAT),)),
    C("d20_tests", "natural_1", P, NO_USE),
    C("d20_tests", "advantage_disadvantage", P, GM),
    C("d20_tests", "roll_two_d20s", P, NO_USE),
    C("d20_tests", "no_stacking", P, NO_USE),
    C("d20_tests", "rerolls", P, NO_USE),
    C("d20_tests", "heroic_inspiration", P, NO_USE),
    C("d20_tests", "only_one_heroic_inspiration", P, NO_USE),
    C("d20_tests", "gaining_heroic_inspiration", P, GM),
    # == Proficiency =========================================================
    C(
        "proficiency",
        "proficiency_bonus",
        P,
        NO_USE,
        refs=(
            ("Character Creation", (CHARACTER_CREATION, UNRESOLVED_TARGET)),
            ("Challenge Rating", "challenge_rating"),
        ),
    ),
    # One band per printed cell pair; "Up to 4" prints no lower bound.
    C(
        "proficiency",
        "proficiency_bonus_bands",
        S,
        None,
        facts=(
            ProficiencyBonusBandFact(2, 4, None),
            ProficiencyBonusBandFact(3, 8, 5),
            ProficiencyBonusBandFact(4, 12, 9),
            ProficiencyBonusBandFact(5, 16, 13),
            ProficiencyBonusBandFact(6, 20, 17),
            ProficiencyBonusBandFact(7, 24, 21),
            ProficiencyBonusBandFact(8, 28, 25),
            ProficiencyBonusBandFact(9, 30, 29),
        ),
    ),
    # The umbrella sentence is four rules, typed below per kind.
    C("proficiency", "d20_test_application", P, NO_USE),
    C(
        "proficiency",
        "spell_uses",
        S,
        None,
        facts=(
            ProficiencyBonusUseFact(ProficiencyBonusUse.SPELL_ATTACK),
            ProficiencyBonusUseFact(ProficiencyBonusUse.SPELL_SAVE_DC),
        ),
    ),
    C(
        "proficiency",
        "bonus_operation_limits",
        S,
        None,
        facts=(
            ProficiencyBonusOperationLimitFact(ProficiencyBonusOperation.ADD, 1, None),
            ProficiencyBonusOperationLimitFact(
                ProficiencyBonusOperation.MULTIPLY, 1, ProficiencyBonusOperation.ADD
            ),
            ProficiencyBonusOperationLimitFact(
                ProficiencyBonusOperation.DIVIDE, 1, ProficiencyBonusOperation.ADD
            ),
        ),
    ),
    C("proficiency", "skills", P, GM, refs=(("Actions", PLAY_ACTIONS),)),
    # Which skill a creature has is sheet state; the no-proficiency case stays
    # the prose beside the fact.
    C(
        "proficiency",
        "skill_proficiency",
        M,
        NO_USE,
        facts=(applies(ProficiencyKind.SKILL, RollContext.ABILITY_CHECK),),
    ),
    # "most often applies to": the pairing is typical, not fixed.
    C("proficiency", "skill_list", P, CTX),
    C("proficiency", "determining_skills", P, NO_USE),
    C(
        "proficiency",
        "saving_throw_proficiency",
        M,
        NO_USE,
        facts=(applies(ProficiencyKind.SAVING_THROW, RollContext.SAVING_THROW),),
    ),
    C("proficiency", "class_saving_throws", P, NO_USE),
    C("proficiency", "equipment_proficiency", P, NO_USE),
    C(
        "proficiency",
        "weapon_proficiency",
        M,
        NO_USE,
        facts=(applies(ProficiencyKind.WEAPON, RollContext.ATTACK_ROLL),),
    ),
    # The bonus, and Advantage when the skill proficiency is held too; "that
    # uses the tool" stays the prose.
    C(
        "proficiency",
        "tool_proficiency",
        M,
        CTX,
        facts=(
            applies(ProficiencyKind.TOOL, RollContext.ABILITY_CHECK),
            AdvantageFact(
                AdvantageState.ADVANTAGE,
                own(RollContext.ABILITY_CHECK),
                requires_proficiencies=(ProficiencyKind.SKILL, ProficiencyKind.TOOL),
            ),
        ),
    ),
    # == Actions =============================================================
    # Restates the twelve accepted action records, which type them.
    C("actions", "main_actions", P, NO_USE, refs=ACTION_REFS),
    C("actions", "improvised_actions", P, GM),
    C(
        "actions",
        "one_thing_at_a_time",
        P,
        CTX,
        refs=(("Combat", PLAY_COMBAT),),
    ),
    C("actions", "bonus_actions", P, NO_USE),
    # One Bonus Action per turn is typed; the choice among several stays prose.
    C(
        "actions",
        "one_bonus_action",
        M,
        NO_USE,
        facts=(ActionAllowanceFact(1, AllowanceScope.TURN, ActionCost.BONUS_ACTION),),
    ),
    C("actions", "bonus_action_timing", P, NO_USE),
    C("actions", "reactions", P, NO_USE),
    # "until the start of your next turn" spans other creatures' turns, so a
    # per-turn allowance would be false.
    C("actions", "one_reaction", P, NO_USE),
    C("actions", "reaction_timing", P, NO_USE),
    # == Rules Glossary: Damage Types ========================================
    C(
        "damage_types",
        "damage_types",
        P,
        NO_USE,
        refs=(("Resistance", "resistance"),),
    ),
    # "offers examples to help a GM assign a type".
    C("damage_types", "damage_type_examples", P, GM),
    # == Rules Glossary: Dead ================================================
    C("dead", "dead", P, NO_USE, refs=(("Hit Points", "hit_points"),)),
    C(
        "dead",
        "returning_to_life",
        P,
        CTX,
        refs=(("Hit Points", "hit_points"),),
    ),
    # One level removed is typed; "died with any Exhaustion levels" and the
    # return to life stay the prose.
    C(
        "dead",
        "exhaustion_on_revival",
        M,
        NO_USE,
        facts=(
            ConditionLevelFact(
                ConditionKind.EXHAUSTION, LevelDirection.REMOVE, amount=1
            ),
        ),
        refs=(("Exhaustion", "exhaustion"),),
    ),
    # == Rules Glossary: Long Rest ===========================================
    C("long_rest", "long_rest", P, CTX),
    C(
        "long_rest",
        "sleep",
        M,
        NO_USE,
        facts=(
            ConditionEffectFact(ConditionKind.UNCONSCIOUS, ConditionEffectKind.APPLIES),
        ),
        refs=(("Unconscious", "unconscious"),),
    ),
    # The clock runs from finishing a Long Rest; that anchor stays the prose.
    C(
        "long_rest",
        "frequency",
        M,
        NO_USE,
        facts=(RetryRestrictionFact(16, TimeUnit.HOUR, False),),
    ),
    C("long_rest", "starting", P, NO_USE, refs=(("Hit Point", "hit_points"),)),
    # Full restoration is typed, under the "When you finish the rest" lead that
    # is this component's own prose; Hit Point Dice, the maximum, ability
    # scores and recharges stay prose. Exhaustion Reduced restates the
    # accepted Exhaustion removal, which is typed there.
    C(
        "long_rest",
        "benefits",
        M,
        NO_USE,
        facts=(HealingFact(restores_all_hit_points=True),),
        refs=(("Hit Points", "hit_points"), ("Exhaustion", "exhaustion")),
    ),
    # What stops the rest, and what an interrupted rest still grants.
    C(
        "long_rest",
        "interruptions",
        P,
        CTX,
        refs=(
            ("Initiative", "initiative"),
            ("damage", "damage"),
            ("Short Rest", "short_rest"),
        ),
    ),
    C("long_rest", "resuming", P, NO_USE),
    # == Rules Glossary: Short Rest ==========================================
    C("short_rest", "short_rest", P, CTX),
    C("short_rest", "starting", P, NO_USE, refs=(("Hit Point", "hit_points"),)),
    # Granted on finishing the rest. The healing depends on each Hit Point Die
    # rolled; no family states it.
    C(
        "short_rest",
        "benefits",
        P,
        NO_USE,
        refs=(("Hit Points", "hit_points"),),
    ),
    C(
        "short_rest",
        "interruptions",
        P,
        CTX,
        refs=(("Initiative", "initiative"), ("damage", "damage")),
    ),
)

CHECK_PROFICIENCY_POINTER = 'See "Proficiency" later in "Playing the Game" for more information about skill and tool proficiencies.'
ATTACK_PROFICIENCY_POINTER = 'See "Proficiency" later in "Playing the Game" for more information about weapon proficiencies.'
FINESSE_EXAMPLE = 'For example, the Finesse property (see "Equipment") lets you use Strength or Dexterity with a weapon that has that property.'
EXPERTISE_EXAMPLE = 'For example, the Expertise feature (see "Rules Glossary") doubles the Proficiency Bonus for certain ability checks.'
OPPORTUNITY_ATTACK_POINTER = 'The Opportunity Attack, described later in "Playing the Game," is the most common type of Reaction.'
SHORT_REST_SEE_ALSO = '_See also_ "Short Rest."'

#: Supporting spans: (entry, text, component supported or ``None`` for the
#: record). Examples illustrate; leads, sidebar titles and chapter pointers
#: identify or scope.
SUPPORTING: tuple[tuple[str, str, str | None], ...] = (
    # -- D20 Tests ------------------------------------------------------------
    ("d20_tests", "They follow these steps:", "d20_tests"),
    (
        "d20_tests",
        "See the Ability Check Examples table for examples of each check's use.",
        "check_ability_modifier",
    ),
    ("d20_tests", ABILITY_CHECK_EXAMPLES_TABLE, "check_ability_modifier"),
    (
        "d20_tests",
        "For example, if a rule refers to a Strength (Acrobatics or Athletics) check, you can add your Proficiency Bonus to the check if you have proficiency in the Acrobatics or Athletics skill.",
        "check_proficiency",
    ),
    ("d20_tests", CHECK_PROFICIENCY_POINTER, "check_proficiency"),
    ("d20_tests", SAVING_THROW_EXAMPLES_TABLE, "save_ability_modifier"),
    (
        "d20_tests",
        "For example, if a spell forces you to make a save, the DC is determined by the caster's spellcasting ability and Proficiency Bonus.",
        "save_dc",
    ),
    ("d20_tests", FINESSE_EXAMPLE, "other_ability_modifiers"),
    ("d20_tests", ATTACK_PROFICIENCY_POINTER, "attack_proficiency"),
    (
        "d20_tests",
        "For example, if you have Disadvantage and roll an 18 and a 3, use the 3. If you instead have Advantage and roll those numbers, use the 18.",
        "roll_two_d20s",
    ),
    (
        "d20_tests",
        "For example, if you have Heroic Inspiration (see the sidebar below) and roll a 3 and an 18 on an ability check that has Advantage or Disadvantage, you could expend your Heroic Inspiration to reroll one of those dice, not both of them.",
        "rerolls",
    ),
    ("d20_tests", "**Heroic Inspiration**", "heroic_inspiration"),
    (
        "d20_tests",
        "For example, Human characters start each day with Heroic Inspiration.",
        "gaining_heroic_inspiration",
    ),
    # -- Proficiency ----------------------------------------------------------
    (
        "proficiency",
        "Characters and monsters are good at various things. Some are skilled with many weapons, while others can use only a few. Some are better at understanding people's motives, and others are better at unlocking the secrets of the multiverse.",
        "proficiency_bonus",
    ),
    (
        "proficiency",
        "The Proficiency Bonus table shows how the bonus is determined.",
        "proficiency_bonus_bands",
    ),
    (
        "proficiency",
        "For example, if a rule allows you to make a Charisma (Deception or Persuasion) check, you add your Proficiency Bonus if you're proficient in either skill, but you don't add it twice if you're proficient in both skills.",
        "bonus_operation_limits",
    ),
    ("proficiency", EXPERTISE_EXAMPLE, "bonus_operation_limits"),
    (
        "proficiency",
        "For example, if a character tries to climb a cliff, the GM might ask for a Strength (Athletics) check. If the character has Athletics proficiency, the character adds their Proficiency Bonus to the Strength check. If the character lacks that proficiency, they make the check without adding their Proficiency Bonus.",
        "skill_proficiency",
    ),
    (
        "proficiency",
        "For example, proficiency in Wisdom saves lets you add your Proficiency Bonus to your Wisdom saves.",
        "saving_throw_proficiency",
    ),
    (
        "proficiency",
        "Wizards, for example, are proficient in Intelligence and Wisdom saves; they train to resist mental assault.",
        "class_saving_throws",
    ),
    (
        "proficiency",
        "There are two categories of equipment proficiency:",
        "equipment_proficiency",
    ),
    (
        "proficiency",
        "This means you can benefit from both skill proficiency and tool proficiency on the same ability check.",
        "tool_proficiency",
    ),
    # -- Actions --------------------------------------------------------------
    (
        "actions",
        "Actions can come up in other situations, too: in a social interaction, you can try to Influence a creature or use the Search action to read the creature's body language, but you can't do both at the same time. And when you're exploring a dungeon, you can't simultaneously use the Search action to look for traps and use the Help action to aid another character who's trying to open a stuck door (with the Utilize action).",
        "one_thing_at_a_time",
    ),
    (
        "actions",
        "The Cunning Action feature, for example, allows a Rogue to take a Bonus Action.",
        "bonus_actions",
    ),
    ("actions", OPPORTUNITY_ATTACK_POINTER, "reactions"),
    # -- Rules Glossary -------------------------------------------------------
    ("long_rest", "_Benefits of the Rest._", "benefits"),
    ("long_rest", SHORT_REST_SEE_ALSO, None),
)

#: Record-owned references: (entry, printed text, target, texts of the spans the
#: pointer is read from).
RECORD_REFERENCES: tuple[RecordReference, ...] = (
    ("d20_tests", "Proficiency", PLAY_PROFICIENCY, (CHECK_PROFICIENCY_POINTER,)),
    ("d20_tests", "Proficiency", PLAY_PROFICIENCY, (ATTACK_PROFICIENCY_POINTER,)),
    ("d20_tests", "Equipment", (EQUIPMENT, UNRESOLVED_TARGET), (FINESSE_EXAMPLE,)),
    ("proficiency", "Expertise", "expertise", (EXPERTISE_EXAMPLE,)),
    ("actions", "Opportunity Attack", PLAY_COMBAT, (OPPORTUNITY_ATTACK_POINTER,)),
    ("long_rest", "Short Rest", "short_rest", (SHORT_REST_SEE_ALSO,)),
)

#: Targets outside this batch that no accepted record defines and this batch
#: does not author. Each citation is an expected unresolved-reference finding.
NEW_TARGETS: tuple[Target, ...] = ("armor_class", "challenge_rating", "expertise")
#: Targets outside this batch that the accepted inputs define.
ACCEPTED_CONTEXT_TARGETS: tuple[Target, ...] = (
    *(t for _, t in ACTION_REFS),
    PLAY_COMBAT,
    "damage",
    "exhaustion",
    "hit_points",
    "initiative",
    "resistance",
    "unarmed_strike",
    "unconscious",
)


def batch() -> EntryBatch:
    """The tables above, read at call time so tests can mutate them."""
    return EntryBatch(
        origin=ORIGIN,
        schema=(SCHEMA_15_VERSION, SCHEMA_15_HASH),
        proposal_origin=f"{ORIGIN} (CRD Issue 5d checks, actions and rests batch; unaccepted)",
        unit_prefix="checks-actions-rests",
        parent=PARENT,
        entries=ENTRIES,
        expected_leaves=118,
        clauses=CLAUSES,
        framing=FRAMING,
        components=COMPONENTS,
        supporting=SUPPORTING,
        record_references=RECORD_REFERENCES,
        placements=PLACEMENTS,
        excluded=EXCLUDED,
    )


def build(session: Session) -> Built:
    """Derive the checks-actions-rests proposal from the release *session* published."""
    return build_entry_batch(session, batch(), published_release_binding(session))


#: Printed pointers whose destination has no record yet, as (scope, text). Each
#: stays unresolved, alone and composed, until a reviewed resolution names it.
#: "Character Creation" is printed by two components (Armor Class and the
#: Proficiency Bonus), each its own reference.
UNRESOLVED: tuple[tuple[str, str], ...] = (
    (CHARACTER_CREATION, "Character Creation"),
    (CHARACTER_CREATION, "Character Creation"),
    (EQUIPMENT, "Equipment"),
    (GLOSSARY_SCOPE, "Rules Glossary"),
    (SPELLS, "Spells"),
)


#: The accepted citation this batch's D20 Tests section is the printed
#: destination of: *Combat*'s "as detailed earlier in "Playing the Game."" It
#: stays unresolved. A resolution may name only an accepted destination, so this
#: draft becomes applicable only once ``play.d20_tests`` is accepted, and then
#: only by its own authorized ``resolve_references`` action. Nothing here
#: records or applies it.
ATTACK_ROLL_RESOLUTION_ID = "resolve-attack-roll-playing-the-game-1"
#: The span the accepted citation's REFERENCE provenance cites.
ATTACK_ROLL_POINTER_SPAN = "aeefa376-825e-5b97-a815-7409beee2672"


def draft_attack_roll_resolution(binding: ReleaseBinding) -> ReferenceResolution:
    """The pending resolution, drafted for review against *binding*."""
    return ReferenceResolution(
        resolution_id=ATTACK_ROLL_RESOLUTION_ID,
        from_record_key="play.combat",
        from_component_key="attack_structure",
        source_text="Playing the Game",
        scope_key=PLAY,
        target_record_key="play.d20_tests",
        release_binding=binding,
        provenance_span_ids=(ATTACK_ROLL_POINTER_SPAN,),
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
